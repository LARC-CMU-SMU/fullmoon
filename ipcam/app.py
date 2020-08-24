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

QUERY_PIXEL_LUX_INSERT = "INSERT INTO pixel_lux(timestamp,cam_label,patch_label,lux) VALUES (%s, %s, %s, %s)"

SERVICE_NAME = "IPCAM"


def write_lux_values_to_db(lux_values, camera_label, timestamp):
    logger.debug("write_lux_values_to_db with ts {} cam_label {} lux {}".format(timestamp, camera_label, lux_values))
    to_db = []
    for patch_label, lux in lux_values.items():
        to_db.append((timestamp, camera_label, patch_label, lux))
    db.executemany_sql(QUERY_PIXEL_LUX_INSERT, to_db, logger)


def get_time():
    return int(time.time())


def get_lux_value_for_pixel_value(cam_label, patch_label, pixel_value):
    # todo : retrieve the regressor formula and do the real transfer
    return pixel_value


def get_pixel_value_for_patch(image, mask):
    logger.debug("get_lux_value_for_patch with coordinates")
    pixel_values = get_pixel_statics_for_rgb_image(image, mask)
    return pixel_values['mean']


def calculate_lux_values_from_image(ip_cam_label, image):
    logger.debug("calculate_lux_values_from_image with label {}".format(ip_cam_label))
    patch_coordinates_file = config.IP_CAM_DEVICES.get(ip_cam_label).get('patch_coordinate_file')
    coordinates = get_coords_from_labelimg_xml(patch_coordinates_file)
    logger.debug("coordinates :{}".format(coordinates))
    mask_size = image.shape[:2]
    lux_values = {}
    for coordinate_label, points in coordinates.items():
        mask = get_mask(points, mask_size)
        pixel_value = get_pixel_value_for_patch(image, mask)
        logger.debug("pixel value :{}".format(pixel_value))
        lux_value = get_lux_value_for_pixel_value(ip_cam_label, coordinate_label, pixel_value)
        lux_values[coordinate_label] = lux_value
    return lux_values


def handle_ip_cam_thread(label, ip_cam_url):
    logger.debug("starting handle_ip_cam_thread for ip cam {} with url {}".format(label, ip_cam_url))
    # vcap = cv2.VideoCapture(ip_cam_url)
    while 1:
        vcap = cv2.VideoCapture(ip_cam_url)
        if vcap.isOpened():
            try:
                ret, frame = vcap.read()
                if ret:
                    timestamp = get_time()
                    lux_values = calculate_lux_values_from_image(label, frame)
                    write_lux_values_to_db(lux_values, label, timestamp)
                    if config.general.get("write_image"):
                        image_path = join(config.general.get("image_dir"), "{}_{}.jpg".format(timestamp, label))
                        logger.debug("writing image to {}".format(image_path))
                        cv2.imwrite(image_path, frame)
                else:
                    logger.warn("read status false for {}".format(ip_cam_url))
                    # vcap = cv2.VideoCapture(ip_cam_url)
            except Exception as e:
                logger.error("cam reading error :{}".format(str(e)))
        else:
            logger.warn("cam {} closed, re initiating".format(ip_cam_url))
            # vcap = cv2.VideoCapture(ip_cam_url)
        time.sleep(config.general.get("handle_ip_cam_thread_sleep_time"))


def main():
    wait_time_for_db = config.general["wait_time_for_db"]
    logger.info("Waiting [%s] seconds for DB to come up", wait_time_for_db)
    time.sleep(wait_time_for_db)
    cam_user = config.ip_cam_meta.get("username")
    cam_pass = config.ip_cam_meta.get("password")
    cam_port = config.ip_cam_meta.get("port")
    for cam_label, cam_data in config.IP_CAM_DEVICES.items():
        cam_ip = cam_data.get("ip")
        cam_url = "rtsp://{}:{}@{}:{}".format(cam_user, cam_pass, cam_ip, cam_port)
        threading.Thread(target=handle_ip_cam_thread, args=(cam_label, cam_url)).start()
    logger.info("init finished[{}]".format(SERVICE_NAME))


if __name__ == '__main__':
    main()
