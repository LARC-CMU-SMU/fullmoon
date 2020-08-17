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

SERVICE_NAME = "RECORD"


# temp fix before updating rpi to lux library
def modify_lux_reply_from_rpi(rpi_lux_reply):
    logger.info("modifying rpi lux reply {}".format(str(rpi_lux_reply)))
    hr = rpi_lux_reply.get('hr')
    if hr is not None:
        return {"tsl_9": hr}
    return rpi_lux_reply


def get_lux_from_device(url):
    logger.info("getting lux for url {}".format(url))
    rpi_lux_json = None
    try:
        res = requests.get(url)
        if res.status_code == 200:
            rpi_lux_json = modify_lux_reply_from_rpi(res.json())
        else:
            logger.error(res.text)
    except Exception as e:
        logger.error(str(e))
    finally:
        return rpi_lux_json


def get_dc_from_device(url, pin):
    logger.info("getting dc for url {} pin {}".format(url, pin))
    dc = -1
    try:
        res = requests.get(url, params={'pin': pin})
        if res.status_code == 200:
            logger.debug(res.json())
            dc = res.json().get(str(pin))
        else:
            logger.error(res.text)
    except Exception as e:
        logger.error(str(e))
    finally:
        return dc


# def set_dc_in_device(url, pin, dc, freq):
#     logger.info("setting dc at url {} with pin {} dc {} freq {}".format(url, pin, dc, freq))
#     res = requests.post(url, json={'dc': dc, 'pin': pin, 'freq': freq})
#     try:
#         if res.status_code == 200:
#             return 0
#         else:
#             logger.error(res.text)
#     except Exception as e:
#         logger.error(str(e))
#     return -1


def get_time():
    return int(time.time())


# def update_and_confirm_dc_in_device(label, pin, dc, freq):
#     timestamp = get_time()
#     url = config.DEVICES.get(label).get('url') + 'dc'
#     logger.info("setting dc at url {} with pin {} dc {} freq {} at time {}".format(url, pin, dc, freq, timestamp))
#     ret = set_dc_in_device(url, pin, dc, freq)
#     if ret == 0:
#         ret_dc = get_dc_from_device(url, pin)
#         if dc == ret_dc:
#             db.execute_sql(QUERY_DC_INSERT, (timestamp, label, dc), logger)
#             return 0
#         logger.error("requested dc {} while updated dc {}".format(dc, ret_dc))
#     return -1


def collect_lux_values():
    logger.info("lux collection thread started")
    while 1:
        for label in config.DEVICES.keys():
            url = config.DEVICES.get(label).get('url') + 'lux'
            timestamp = time.time()
            lux = get_lux_from_device(url)
            if lux is not None:
                logger.info("lux reply from rpi {}".format(str(lux)))
                for k, v in lux.items():
                    db.execute_sql(QUERY_LUX_INSERT, (timestamp, label, v, k), logger)
            else:
                logger.error("rpi {} with url {} returned None for lux".format(label, url))
        time.sleep(config.general.get("collect_lux_thread_sleep_time"))


def collect_dc_values():
    logger.info("dc collection thread started")
    while 1:
        for label in config.DEVICES.keys():
            url = config.DEVICES.get(label).get('url') + 'dc'
            timestamp = time.time()
            for pin in config.DEVICES.get(label).get('dc_pins'):
                lux = get_dc_from_device(url, pin)
                db.execute_sql(QUERY_DC_INSERT, (timestamp, label, pin, lux), logger)
        time.sleep(config.general.get("collect_dc_thread_sleep_time"))


def main():
    wait_time_for_db = config.general["wait_time_for_db"]
    logger.info("Waiting [%s] seconds for DB to come up", wait_time_for_db)
    time.sleep(wait_time_for_db)
    threading.Thread(target=collect_lux_values).start()
    threading.Thread(target=collect_dc_values).start()
    logger.info("init finished[{}]".format(SERVICE_NAME))


if __name__ == '__main__':
    main()
