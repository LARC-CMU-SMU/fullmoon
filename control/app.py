import logging
import sys
import threading
import time
from logging.handlers import TimedRotatingFileHandler

import requests

import config
import db

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
COMFORT_VALUE = 50
DELTA_DC = 5 * 10000
WEIGHT_MATRIX = None
OPTIMIZED_LUX = None
BRIGHTNESS_THRESHOLD = 2


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


def get_occupancy():
    occupancy = get_occupancy_from_db()
    logger.debug("latest occupancy stat {}".format(occupancy))
    return occupancy


def get_weight_matrix_from_db():
    # todo : implement the actual feature
    return [[.9, .4, .3, .1],
            [.4, .9, .3, .3],
            [.4, .2, .8, .4],
            [.2, .3, .4, .7]]


def init_weight_matrix():
    global WEIGHT_MATRIX
    WEIGHT_MATRIX = get_weight_matrix_from_db()


def get_dc_for_lux(lux):
    # todo
    logger.info("converting lux {} to dc".format(lux))
    return int(lux)  # magic


def set_lux_in_section(section, lux):
    logger.info("setting lux {} in section {}".format(lux, section))
    dc = get_dc_for_lux(lux)
    url = "{}dc".format(config.DEVICES.get(section).get('url'))
    dc_pin = config.DEVICES.get(section).get('dc_pin')
    ret = set_dc_in_device(url, dc_pin, dc, config.general.get("dc_freq"))
    if ret < 0:
        logger.error("setting lux failed")


def handle_newly_occupied():
    logger.info("starting handle_newly_occupied thread")
    prev_occupancy_dict = get_occupancy()
    while 1:
        now_occupancy_dict = get_occupancy()
        for section in prev_occupancy_dict.keys():
            prev_occupied = prev_occupancy_dict.get(section)
            now_occupied = now_occupancy_dict.get(section)
            if prev_occupied is not now_occupied:
                logger.debug("prev {} -> now {}".format(prev_occupied, now_occupied))
                if now_occupied and not prev_occupied:
                    set_lux_in_section(section, COMFORT_VALUE)

        prev_occupancy_dict = now_occupancy_dict
        sleep_time = config.general.get("handle_newly_occupied_thread_sleep_time")
        time.sleep(sleep_time)


def get_calculated_optimized_lux():
    # todo
    # for now it's magic
    # return {'a': 29, 'b': 53, 'c': 53, 'd': 20}
    return {'b': 70, }


def calculate_optimized_lux_thread():
    logger.info("starting calculate_optimized_brightness thread")
    global OPTIMIZED_LUX
    while 1:
        OPTIMIZED_LUX = get_calculated_optimized_lux()
        sleep_time = config.general.get("calculate_optimized_lux_thread_sleep_time")
        time.sleep(sleep_time)


def get_current_lux_from_db():
    # todo : optimize below code
    logger.debug("querying the lux from db")
    query = "SELECT lux FROM lux WHERE label=%s AND pin=%s ORDER BY timestamp DESC LIMIT 1"
    # a = db.execute_sql(query, ('a', 'tsl_9'), logger, True)[0][0]
    b = db.execute_sql(query, ('b', 'tsl_2'), logger, True)[0][0]
    # c = db.execute_sql(query, ('c', 'tsl_9'), logger, True)[0][0]
    # d = db.execute_sql(query, ('d', 'tsl_9'), logger, True)[0][0]
    # logger.debug("a {}, b {}, c {}, d {}".format(a, b, c, d))
    # return {'a': a, 'b': b, 'c': c, 'd': d}
    return {'b': b, }


def get_occupancy_from_db():
    # todo : optimize
    logger.debug("querying the occupancy from db")
    query = "SELECT occupancy FROM occupancy WHERE label=%s ORDER BY timestamp DESC LIMIT 1"
    # a = db.execute_sql(query, ('a',), logger, True)[0][0]
    b = db.execute_sql(query, ('b',), logger, True)[0][0]
    # c = db.execute_sql(query, ('c',), logger, True)[0][0]
    # d = db.execute_sql(query, ('d',), logger, True)[0][0]
    # logger.debug("a {}, b {}, c {}, d {}".format(a, b, c, d))
    # return {'a': a, 'b': b, 'c': c, 'd': d}
    return {'b': b, }


def get_dc_from_db():
    # todo : optimize
    logger.debug("querying the dc from db")
    query = "SELECT dc FROM dc WHERE label=%s ORDER BY timestamp DESC LIMIT 1"
    # a = db.execute_sql(query, ('a',), logger, True)[0][0]
    b = db.execute_sql(query, ('b',), logger, True)[0][0]
    # c = db.execute_sql(query, ('c',), logger, True)[0][0]
    # d = db.execute_sql(query, ('d',), logger, True)[0][0]
    # logger.debug("a {}, b {}, c {}, d {}".format(a, b, c, d))
    # return {'a': a, 'b': b, 'c': c, 'd': d}
    return {'b': b, }


def set_optimized_lux_in_device():
    logger.info("starting set_optimized_brightness thread")
    old_lux_dict = get_current_lux_from_db()
    dc_dict = get_dc_from_db()
    while 1:
        for section, old_lux in old_lux_dict.items():
            new_lux = OPTIMIZED_LUX.get(section)
            logger.debug("new lux {}, old lux {} delta {}"
                         .format(new_lux, old_lux, DELTA_DC))
            if abs(new_lux - old_lux) > BRIGHTNESS_THRESHOLD:
                dc = dc_dict.get(section)
                if new_lux > old_lux:
                    logger.debug("old lux {} -> new lux {} old dc {} delta dc +{}"
                                 .format(old_lux, new_lux, dc, DELTA_DC))
                    set_lux_in_section(section, dc + DELTA_DC)
                if new_lux < old_lux:
                    logger.debug("old lux {} -> new lux {} old dc {} delta dc -{}"
                                 .format(old_lux, new_lux, dc, DELTA_DC))
                    set_lux_in_section(section, dc - DELTA_DC)
            else:
                logger.debug("new lux {}, old lux {} delta {}, not doing anything"
                             .format(new_lux, old_lux, DELTA_DC))

        sleep_time = config.general.get("set_optimized_lux_in_device_thread_sleep_time")
        time.sleep(sleep_time)


def main():
    wait_time_for_db = config.general["wait_time_for_db"]
    logger.info("Waiting [%s] seconds for DB to come up", wait_time_for_db)
    time.sleep(wait_time_for_db)
    threading.Thread(target=handle_newly_occupied).start()
    threading.Thread(target=calculate_optimized_lux_thread).start()
    time.sleep(config.general['wait_between_optimize_and_control'])
    threading.Thread(target=set_optimized_lux_in_device).start()
    logger.debug("init finished[{}]".format(SERVICE_NAME))


if __name__ == '__main__':
    main()
