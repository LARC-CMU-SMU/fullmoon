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
QUERY_DC_CACHE_UPSERT = "INSERT INTO dc_cache(timestamp,label,pin, dc) VALUES (%s, %s, %s, %s)" \
                        "ON CONFLICT (label,pin) DO UPDATE SET timestamp = excluded.timestamp, dc = excluded.dc;"

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


def get_time():
    return int(time.time())


def collect_lux_values_via_hardware_sensors():
    logger.info("collect_lux_values_via_hardware_sensors thread started")
    while 1:
        for label in config.RPI_DEVICES.keys():
            url = config.RPI_DEVICES.get(label).get('url') + 'lux'
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
        for label in config.RPI_DEVICES.keys():
            url = config.RPI_DEVICES.get(label).get('url') + 'dc'
            timestamp = time.time()
            for pin in config.RPI_DEVICES.get(label).get('dc_pins'):
                dc = get_dc_from_device(url, pin)
                db.execute_sql(QUERY_DC_INSERT, (timestamp, label, pin, dc), logger)
                db.execute_sql(QUERY_DC_CACHE_UPSERT, (timestamp, label, pin, dc), logger)
        time.sleep(config.general.get("collect_dc_thread_sleep_time"))


def main():
    wait_time_for_db = config.general["wait_time_for_db"]
    logger.info("Waiting [%s] seconds for DB to come up", wait_time_for_db)
    time.sleep(wait_time_for_db)
    threading.Thread(target=collect_lux_values_via_hardware_sensors).start()
    threading.Thread(target=collect_dc_values).start()
    logger.info("init finished[{}]".format(SERVICE_NAME))


if __name__ == '__main__':
    main()
