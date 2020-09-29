import logging
import sys
import threading
import time
from logging.handlers import TimedRotatingFileHandler
from os.path import join

import cv2

import config
import db
from util import *

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

QUERY_PIXEL_LUX_INSERT = "INSERT INTO pixel_lux(timestamp,cam_label,patch_label,lux_label,lux,gray_mean,gray_stddev,h_mean,s_mean,v_mean,h_stddev,s_stddev,v_stddev) " \
                         "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
QUERY_FP_SELECT = "SELECT * FROM fp"

SERVICE_NAME = "IPCAM"
FINGER_PRINTS = {}
PEARSON_CORR_THRESH = 0.8


def load_finger_prints():
    fp_dict_list = db.execute_sql_for_dict(QUERY_FP_SELECT,[],logger)
    num_of_finger_prints = len(fp_dict_list)
    for fp in fp_dict_list:
        patch_label = fp['patch_label']
        if not FINGER_PRINTS.get(patch_label):
            FINGER_PRINTS[patch_label] = {}
        lux_label = fp['lux_label']
        FINGER_PRINTS[patch_label][lux_label] = {'x2': float(fp['x2']),
                                                 'x1': float(fp['x1']),
                                                 'x0': float(fp['x0']),
                                                 'pearson_corr': float(fp['pearson_corr'])}
    logger.info('done loading {} finger prints for {} patches'.format(num_of_finger_prints), len(FINGER_PRINTS.keys()))


def write_lux_values_to_db(lux_data_and_pixel_stat_dict, camera_label, timestamp):
    logger.debug("write_lux_values_to_db with ts {} cam_label {}".
                 format(timestamp, camera_label))
    to_db = []
    # preserve the pixel stats in DB for patch even there is no lux value calculated
    for patch_label, lux_data_and_pixel_stat in lux_data_and_pixel_stat_dict.items():
        lux_values = lux_data_and_pixel_stat.get('lux')
        if len(lux_values.keys()) == 0:
            logger.debug("write_lux_values_to_db with cam_label [{}] patch_label [{}] when no lux value is calculated".
                         format(camera_label, patch_label))
            to_db.append((timestamp,
                          camera_label,
                          patch_label,
                          "None",
                          -1,
                          lux_data_and_pixel_stat.get('gray_mean'),
                          lux_data_and_pixel_stat.get('gray_stddev'),
                          lux_data_and_pixel_stat.get('h_mean'),
                          lux_data_and_pixel_stat.get('s_mean'),
                          lux_data_and_pixel_stat.get('v_mean'),
                          lux_data_and_pixel_stat.get('h_stddev'),
                          lux_data_and_pixel_stat.get('s_stddev'),
                          lux_data_and_pixel_stat.get('v_stddev'),
                          ))
        for lux_label, lux_val in lux_values.items():
            to_db.append((timestamp,
                          camera_label,
                          patch_label,
                          lux_label,
                          lux_val,
                          lux_data_and_pixel_stat.get('gray_mean'),
                          lux_data_and_pixel_stat.get('gray_stddev'),
                          lux_data_and_pixel_stat.get('h_mean'),
                          lux_data_and_pixel_stat.get('s_mean'),
                          lux_data_and_pixel_stat.get('v_mean'),
                          lux_data_and_pixel_stat.get('h_stddev'),
                          lux_data_and_pixel_stat.get('s_stddev'),
                          lux_data_and_pixel_stat.get('v_stddev'),
                          ))
    db.executemany_sql(QUERY_PIXEL_LUX_INSERT, to_db, logger)


def get_time_in_full_seconds():
    return int(time.time())


def get_time_in_frac_seconds():
    return time.time()


def get_lux_values_for_pixel_value(cam_label, patch_label, pixel_value):
    # logger.debug("get_lux_value_for_pixel_value cam_label {} patch_label {}".format(
    #     cam_label, patch_label))
    fp = FINGER_PRINTS.get(patch_label)
    ret_dict = {}
    if not fp:
        logger.error("no finger print found for {}".format(patch_label))
        return ret_dict
    for lux_label, coefficient_data in fp.items():
        pearson_corr = coefficient_data.get('pearson_corr')
        # logger.debug("pearson corr {}".format(pearson_corr))
        if pearson_corr > PEARSON_CORR_THRESH:
            x2 = coefficient_data.get('x2')
            x1 = coefficient_data.get('x1')
            x0 = coefficient_data.get('x0')
            calc_lux_val = (pixel_value*pixel_value*x2) + (pixel_value*x1) + x0
            # logger.debug("pixel val {} x2 {} x1 {} x0 {} lux label {} calc lux val {}".format(
            #     pixel_value, x2, x1, x0, lux_label, calc_lux_val))

            ret_dict[lux_label] = calc_lux_val
    return ret_dict


def get_pixel_stats_for_patch(image, mask):
    # logger.debug("get_lux_value_for_patch with coordinates")
    pixel_stat = get_pixel_statics_for_bgr_image(image, mask)
    return pixel_stat


def calculate_lux_values_from_image(ip_cam_label, image):
    logger.debug("calculate_lux_values_from_image with label {}".format(ip_cam_label))
    # todo : load this at the beginning and save it in memory
    patch_coordinates_file = config.IP_CAM_DEVICES.get(ip_cam_label).get('patch_coordinate_file')
    coordinates = get_coords_from_labelimg_xml(patch_coordinates_file)
    mask_size = image.shape[:2]
    lux_and_pixel_stats = {}
    for coordinate_label, points in coordinates.items():
        mask = get_mask(points, mask_size)
        pixel_stat = get_pixel_stats_for_patch(image, mask)
        gray_pixel_mean = pixel_stat['mean']
        # logger.debug("pixel value :{}".format(pixel_value))
        lux_values = get_lux_values_for_pixel_value(ip_cam_label, coordinate_label, gray_pixel_mean)
        lux_and_pixel_stats[coordinate_label] = {
            'lux': lux_values,
            'gray_mean': gray_pixel_mean,
            'gray_stddev': pixel_stat['stddev'],
            'h_mean': pixel_stat['h_mean'],
            's_mean': pixel_stat['s_mean'],
            'v_mean': pixel_stat['v_mean'],
            'h_stddev': pixel_stat['h_stddev'],
            's_stddev': pixel_stat['s_stddev'],
            'v_stddev': pixel_stat['v_stddev'],
        }
    return lux_and_pixel_stats


def handle_ip_cam_thread(cam_label, ip_cam_url):
    logger.debug("starting handle_ip_cam_thread for ip cam {} with url {}".format(cam_label, ip_cam_url))
    while 1:
        start_time = get_time_in_frac_seconds()
        vcap = cv2.VideoCapture(ip_cam_url)
        if vcap.isOpened():
            ret = False
            try:
                ret, frame = vcap.read()
            except Exception as e:
                logger.error("cam reading error :{}".format(str(e)))

            if ret:
                timestamp = get_time_in_full_seconds()
                lux_values_and_pixel_stat = calculate_lux_values_from_image(cam_label, frame)
                write_lux_values_to_db(lux_values_and_pixel_stat, cam_label, timestamp)
                if config.general.get("write_image"):
                    image_path = join(config.general.get("image_dir"), "{}_{}.jpg".format(timestamp, cam_label))
                    logger.debug("writing image to {}".format(image_path))
                    cv2.imwrite(image_path, frame)
            else:
                logger.warn("read status false for {}".format(ip_cam_url))
        else:
            logger.warn("cam {} closed".format(ip_cam_url))
        time_passed = get_time_in_frac_seconds() - start_time
        sleep_time = config.general.get("handle_ip_cam_thread_sleep_time") - time_passed
        logger.debug("going to sleep for {} seconds".format(sleep_time))
        if sleep_time > 0:
            time.sleep(sleep_time)


def main():
    wait_time_for_db = config.general["wait_time_for_db"]
    logger.info("Waiting [%s] seconds for DB to come up", wait_time_for_db)
    time.sleep(wait_time_for_db)
    cam_user = config.ip_cam_meta.get("username")
    cam_pass = config.ip_cam_meta.get("password")
    cam_port = config.ip_cam_meta.get("port")
    load_finger_prints()
    for cam_label, cam_data in config.IP_CAM_DEVICES.items():
        cam_ip = cam_data.get("ip")
        patch_coord_file = cam_data.get("patch_coordinate_file")
        logger.info("cam [{}] -> file [{}]".format(cam_label, patch_coord_file))
        cam_url = "rtsp://{}:{}@{}:{}".format(cam_user, cam_pass, cam_ip, cam_port)
        threading.Thread(target=handle_ip_cam_thread, args=(cam_label, cam_url)).start()
    logger.info("init finished[{}]".format(SERVICE_NAME))


if __name__ == '__main__':
    main()
