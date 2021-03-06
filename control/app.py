import json
import logging
import sys
import threading
import time
import requests
from logging.handlers import TimedRotatingFileHandler
import xml.etree.ElementTree as ET

import config
import db
import optimizer

from m_lux import m_get_current_pseudo_lux

logger = logging.getLogger(__name__)

log_level = logging.getLevelName(config.general['log_level'])

handler = logging.handlers.RotatingFileHandler(config.general['log_file_name'],
                                               maxBytes=config.general["max_log_size"],
                                               backupCount=config.general["max_log_file_count"])

syserr_handler = logging.StreamHandler(sys.stderr)
logger.addHandler(syserr_handler)

logger.setLevel(log_level)

formatter = logging.Formatter('%(asctime)s: %(levelname)-8s: %(threadName)-12s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

QUERY_LUX_INSERT = "INSERT INTO lux(timestamp,label,lux,pin) VALUES (%s, %s, %s, %s)"
QUERY_DC_INSERT = "INSERT INTO dc(timestamp,label,pin, dc) VALUES (%s, %s, %s, %s)"

SERVICE_NAME = "CONTROL"
# COMFORT_DC = 60 * 10000
# DELTA_DC = 10 * 10000
WEIGHTS_DICT = None
WEIGHT_MATRIX = None
OPTIMIZED_DC = None
DC_THRESHOLD = 1 * 10000
LUX_THRESHOLD = 5
DC_LOWER_BOUND = 0
DC_UPPER_BOUND = 100 * 10000
MIN_SAFETY_LUX = 10
COMFORT_LUX = 20
PATCH_COORDINATES = None


def set_dc_in_device(url, pin, dc, freq):
    logger.info("setting dc at url {} with pin {} dc {} freq {}".format(url, pin, dc, freq))
    try:
        res = requests.post(url, json={'dc': dc, 'pin': pin, 'freq': freq})
        if res.status_code == 202:
            return 0
        else:
            logger.error(res.text)
    except Exception as e:
        logger.error(str(e))
    logger.error("setting dc failed")
    return -1


def get_time():
    return int(time.time())


def validate_dc(dc):
    logger.debug("validating dc {}".format(dc))
    if dc < DC_LOWER_BOUND:
        return DC_LOWER_BOUND
    if dc > DC_UPPER_BOUND:
        return DC_UPPER_BOUND
    return int(dc)


def set_dc_in_section(section, dc):
    logger.debug("setting lux {} in section {}".format(dc, section))
    dc = validate_dc(dc)
    url = "{}dc".format(config.DEVICES.get(section).get('url'))
    dc_pin = config.DEVICES.get(section).get('dc_pin')
    ret = set_dc_in_device(url, dc_pin, dc, config.general.get("dc_freq"))
    if ret < 0:
        logger.error("setting lux failed")


def get_weight_matrix_dict():
    # todo : load the matrix from db
    return {'a': {'a': 53.3, 'b': 0.8, 'c': 0.4, 'd': 0, 'e': 9.6, 'f': 1.7},
            'b': {'a': 0.4, 'b': 15.4, 'c': 0, 'd': 1.7, 'e': 0, 'f': 12.1},
            'c': {'a': 1.25, 'b': 0, 'c': 31.7, 'd': 10, 'e': 6.25, 'f': 4.2},
            'd': {'a': 0.4, 'b': 0.8, 'c': 8.75, 'd': 37.1, 'e': 0.4, 'f': 11.25}
            }


# this is borrowed from util file
def get_coords_from_labelimg_xml(file_name):
    tree = ET.parse(file_name)
    root = tree.getroot()
    boxes = {}
    for obj in root.iter("object"):
        name = obj.find('name').text
        bndbox = obj.find('bndbox')
        xmin = int(bndbox.find('xmin').text)
        xmax = int(bndbox.find('xmax').text)
        ymin = int(bndbox.find('ymin').text)
        ymax = int(bndbox.find('ymax').text)
        boxes[name] = ((xmin, ymin), (xmax, ymax))
    return boxes


def init_weights():
    global WEIGHTS_DICT, WEIGHT_MATRIX
    WEIGHTS_DICT = get_weight_matrix_dict()
    logger.debug("weights dict :{}".format(WEIGHTS_DICT))
    WEIGHT_MATRIX = get_matrix_from_weight_dict(WEIGHTS_DICT)
    logger.debug("weights matrix :{}".format(WEIGHT_MATRIX))


# instantly light up newly occupied sections
# def handle_newly_occupied_thread():
#     logger.debug("starting handle_newly_occupied thread")
#     prev_occupancy_dict = get_current_occupancy()
#     while 1:
#         now_occupancy_dict = get_current_occupancy()
#         for section in prev_occupancy_dict.keys():
#             prev_occupied = prev_occupancy_dict.get(section)
#             now_occupied = now_occupancy_dict.get(section)
#             if prev_occupied is not now_occupied:
#                 logger.info("prev {} -> now {}".format(prev_occupied, now_occupied))
#                 if now_occupied and not prev_occupied:
#                     set_dc_in_section(section, COMFORT_DC)
#
#         prev_occupancy_dict = now_occupancy_dict
#         sleep_time = config.general.get("handle_newly_occupied_thread_sleep_time")
#         time.sleep(sleep_time)


# returns the should be lux levels for the sections based on occupancy
def get_should_be_lux_vector_for_occupancy_vector(occupancy_vector):
    optimum_lux_vector = {}
    for section, occupied in occupancy_vector.items():
        optimum_lux = MIN_SAFETY_LUX
        if occupied:
            optimum_lux = COMFORT_LUX
        optimum_lux_vector[section] = optimum_lux
    # round the lux values to nearest 10
    optimum_lux_vector = get_rounded_values_dict(optimum_lux_vector)
    return optimum_lux_vector


def get_lux_already_added_by_system(weight_dict, dc_vector):
    ret = {}
    for cubical_sensor, weights in weight_dict.items():
        tot_lux = 0
        for light_source, val in weights.items():
            lux = val * dc_vector.get(light_source) / 1000000
            tot_lux += lux
        ret[cubical_sensor] = tot_lux
    return get_rounded_values_dict(ret)


# make sure the deficit vector have only positive values
def validate_deficit_lux_vector(lux_dict):
    ret = {}
    for k, v in lux_dict.items():
        if v < 0:
            v = 0
        ret[k] = v
    return ret


# returns the optimum dc values that should to be set to fill the deficit lux levels
def get_should_be_dc_vector(deficit_lux_vector, weight_matrix, weight_dict):
    dc_vector, sum = optimizer.opt_get_optimized_dc_dict(weight_matrix, weight_dict, deficit_lux_vector, logger)
    logger.debug("get_dc_vector[{}] with cost [{}]".format(dc_vector, sum))
    return dc_vector


def get_rounded_values_dict(m_dict):
    ret = {}
    for k, v in m_dict.items():
        ret[k] = round_to_base(v)
    return ret


def round_to_base(x, base=10):
    return base * round(x / base)


def subtract_dict(dict_1, dict_2):
    ret = {}
    for k in dict_1.keys():
        ret[k] = dict_1[k] - dict_2[k]
    return ret


def add_dict(dict_1, dict_2):
    ret = {}
    for k in dict_1.keys():
        ret[k] = dict_1[k] + dict_2[k]
    return ret


def need_to_add_more_lux_to_system(deficit_lux_dict):
    for deficit_lux_val in deficit_lux_dict.values():
        if deficit_lux_val > LUX_THRESHOLD:
            return True
    return False


def get_empty_dc_dict(light_source_keys):
    ret={}
    for k in light_source_keys:
        ret[k]=0
    return ret


def get_optimized_dc_dict():
    occupancy_dict = get_current_occupancy()
    occuapant_coordinates = get_current_occupants_coordinates()

    should_be_lux_dict = get_should_be_lux_vector_for_occupancy_vector(occupancy_dict)  # rounded to base 10
    logger.info("should_be_lux_dict {}".format(should_be_lux_dict))

    current_dc_dict = get_current_dc()
    logger.info("current_dc_dict {}".format(current_dc_dict))

    already_added_lux_dict = get_lux_already_added_by_system(WEIGHTS_DICT, current_dc_dict)  # rounded to base 10
    logger.info("already_added_lux_dict {}".format(already_added_lux_dict))

    # current_lux_dict = get_current_real_lux()  # rounded to base 10
    current_lux_dict = get_current_pseudo_lux("b", occuapant_coordinates, PATCH_COORDINATES)  # rounded to base 10
    logger.info("current_lux_dict {}".format(current_lux_dict))

    natural_lux_dict = subtract_dict(current_lux_dict, already_added_lux_dict)
    logger.info("natural_lux_dict {}".format(natural_lux_dict))

    deficit_lux_dict = validate_deficit_lux_vector(subtract_dict(should_be_lux_dict, natural_lux_dict))
    logger.info("deficit_lux_dict {}".format(deficit_lux_dict))

    if need_to_add_more_lux_to_system(deficit_lux_dict):
        optimized_dc_dict = get_should_be_dc_vector(deficit_lux_dict, WEIGHT_MATRIX, WEIGHTS_DICT)
    else:
        logger.info("no need to add more lux")
        optimized_dc_dict = get_empty_dc_dict(current_dc_dict.keys())

    logger.info("optimized_dc_dict {}".format(optimized_dc_dict))
    return optimized_dc_dict


def get_matrix_from_weight_dict(weight_dict):
    ret = []
    sorted(weight_dict)
    for section_label, section_weights in weight_dict.items():
        current_row = []
        sorted(section_weights)
        for light_source_id, light_source_weight in section_weights.items():
            current_row.append(light_source_weight)
        ret.append(current_row)
    return ret


def calculate_optimized_lux_thread():
    logger.debug("starting calculate_optimized_brightness thread")
    global OPTIMIZED_DC
    while 1:
        calculated_dc_vector = get_optimized_dc_dict()
        if calculated_dc_vector:  # only update if system returned a optimized dc vector
            logger.debug("old dc dict {}".format(OPTIMIZED_DC))
            OPTIMIZED_DC = calculated_dc_vector
            logger.debug("updated dc dict {}".format(OPTIMIZED_DC))
        sleep_time = config.general.get("calculate_optimized_lux_thread_sleep_time")
        time.sleep(sleep_time)


def get_current_real_lux():
    # todo : optimize below code
    # logger.debug("querying the lux from db")
    query = "SELECT lux FROM lux WHERE label=%s AND pin=%s ORDER BY timestamp DESC LIMIT 1"
    a = db.execute_sql(query, ('a', 'tsl_0'), logger, True)[0][0]
    b = db.execute_sql(query, ('b', 'tsl_3'), logger, True)[0][0]
    c = db.execute_sql(query, ('c', 'tsl_0'), logger, True)[0][0]
    d = db.execute_sql(query, ('d', 'tsl_0'), logger, True)[0][0]
    logger.info("lux :a {}, b {}, c {}, d {}".format(a, b, c, d))
    ret = {'a': a, 'b': b, 'c': c, 'd': d}
    return get_rounded_values_dict(ret)


def get_current_pseudo_lux(cam_label, occupancy_list, patch_coordinates_dict):
    ret = {}
    lux_sensor_labels = ["a_tsl_0", "b_tsl_3", "c_tsl_0", "d_tsl_0"]
    inter_ret = m_get_current_pseudo_lux(cam_label, lux_sensor_labels, occupancy_list, patch_coordinates_dict)
    ret['a']=inter_ret["a_tsl_0"]
    ret['b']=inter_ret["b_tsl_3"]
    ret['c']=inter_ret["c_tsl_0"]
    ret['d']=inter_ret["d_tsl_0"]
    return get_rounded_values_dict(ret)


def get_current_occupancy():
    # todo : optimize
    # logger.debug("querying the occupancy from db")
    query = "SELECT occupancy FROM occupancy_cache WHERE cubical_label=%s ORDER BY timestamp DESC LIMIT 1"
    a = db.execute_sql(query, ('a',), logger, True)[0][0]
    b = db.execute_sql(query, ('b',), logger, True)[0][0]
    c = db.execute_sql(query, ('c',), logger, True)[0][0]
    d = db.execute_sql(query, ('d',), logger, True)[0][0]
    # logger.info("occupancy : a {}, b {}, c {}, d {}".format(a, b, c, d))
    return {'a': a, 'b': b, 'c': c, 'd': d}


def get_current_occupants_coordinates():
    # todo : optimize
    # logger.debug("querying the occupant coordinates from db")
    ret = []
    query = "SELECT occupant_coordinates FROM occupancy_cache WHERE cubical_label=%s ORDER BY timestamp DESC LIMIT 1"
    a = db.execute_sql(query, ('a',), logger, True)[0][0]
    if a and len(a) > 0:
        ret += (json.loads(a))
    b = db.execute_sql(query, ('b',), logger, True)[0][0]
    if b and len(b) > 0:
        ret += (json.loads(b))
    c = db.execute_sql(query, ('c',), logger, True)[0][0]
    if c and len(c) > 0:
        ret += (json.loads(c))
    d = db.execute_sql(query, ('d',), logger, True)[0][0]
    if d and len(d) > 0:
        ret += (json.loads(d))
    logger.info("occupant coordinates : {}".format(ret))
    return ret


def get_current_dc():
    # todo : optimize
    # logger.debug("querying the dc from db")
    query = "SELECT dc FROM dc WHERE label=%s ORDER BY timestamp DESC LIMIT 1"
    a = db.execute_sql(query, ('a',), logger, True)[0][0]
    b = db.execute_sql(query, ('b',), logger, True)[0][0]
    c = db.execute_sql(query, ('c',), logger, True)[0][0]
    d = db.execute_sql(query, ('d',), logger, True)[0][0]
    e = db.execute_sql(query, ('e',), logger, True)[0][0]
    f = db.execute_sql(query, ('f',), logger, True)[0][0]
    # logger.info("dc : a {}, b {}, c {}, d {}, e {}, f {}".format(a, b, c, d, e, f))
    ret = {'a': a, 'b': b, 'c': c, 'd': d, 'e': e, 'f': f}
    return ret


def set_optimized_dc():
    logger.debug("starting set_optimized_brightness thread")
    while 1:
        old_dc_dict = get_current_dc()
        for section, old_dc in old_dc_dict.items():
            if not OPTIMIZED_DC:  # fail safe
                continue
            new_dc = OPTIMIZED_DC.get(section)
            abs_diff = abs(new_dc - old_dc)
            if abs_diff > DC_THRESHOLD:
                logger.debug("section [{}] changing the dc in {}->{}".format(section, old_dc, new_dc))
                #  bypass the gradual increase for now.
                set_dc_in_section(section, new_dc)
            #     if new_dc > old_dc:
            #         logger.info("old dc {} -> new dc {} delta dc +{}"
            #                      .format(old_dc, new_dc, DELTA_DC))
            #         set_dc_in_section(section, old_dc + DELTA_DC)
            #     if new_dc < old_dc:
            #         logger.info("old dc {} -> new dc {} delta dc -{}"
            #                      .format(old_dc, new_dc, DELTA_DC))
            #         set_dc_in_section(section, old_dc - DELTA_DC)
            else:
                logger.debug("section [{}] DC delta {} < DC_THRESHOLD {}, not doing anything"
                             .format(section, abs_diff, DC_THRESHOLD))

        sleep_time = config.general.get("set_optimized_dc_in_device_thread_sleep_time")
        time.sleep(sleep_time)


def main():
    wait_time_for_db = config.general["wait_time_for_db"]
    logger.info("Waiting [%s] seconds for DB to come up", wait_time_for_db)
    time.sleep(wait_time_for_db)
    init_weights()
    logger.info("weight_matrix_loaded")
    # todo : ideally this should be loaded from config value
    global PATCH_COORDINATES
    PATCH_COORDINATES = get_coords_from_labelimg_xml("patch_coordinates/B_20201019_132337.xml")
    # todo : uncomment this
    # threading.Thread(target=handle_newly_occupied).start()
    threading.Thread(target=calculate_optimized_lux_thread).start()
    time.sleep(config.general['wait_between_optimize_and_control'])
    threading.Thread(target=set_optimized_dc).start()
    logger.info("init finished[{}]".format(SERVICE_NAME))


if __name__ == '__main__':
    main()
