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

mail_count = 1
count_reset_time = time.time()

DEVICES = {
    'a': {'url': 'http://192.168.1.11:8000/', 'dc_pins': [13, ]},
    'b': {'url': 'http://192.168.1.10:8000/', 'dc_pins': [13, ]},
    'c': {'url': 'http://192.168.1.14:8000/', 'dc_pins': [13, ]},
    'd': {'url': 'http://192.168.1.15:8000/', 'dc_pins': [13, ]},
}
QUERY_LUX_INSERT = "INSERT INTO lux(timestamp,label,lux) VALUES (%s, %s, %s)"
QUERY_DC_INSERT = "INSERT INTO dc(timestamp,label,pin, dc) VALUES (%s, %s, %s, %s)"


# temp fix before updating rpi to lux library
def modify_lux_reply_from_rpi(rpi_lux_reply):
    logger.info("modifying rpi lux reply {}".format(str(rpi_lux_reply)))
    hr = rpi_lux_reply.get('hr')
    if hr is not None:
       return {"tsl_9" :hr}
    return rpi_lux_reply


def get_lux_from_device(url):
    logger.info("getting lux for url {}".format(url))
    res = requests.get(url)
    hr = -1
    if res.status_code == 200:
        rpi_lux_json = modify_lux_reply_from_rpi(res.json())
        logger.debug(rpi_lux_json)
    else:
        logger.error(res.text)
    return rpi_lux_json


def get_dc_from_device(url, pin):
    logger.info("getting dc for url {} pin {}".format(url, pin))
    res = requests.get(url, params={'pin': pin})
    dc = -1
    if res.status_code == 200:
        logger.debug(res.json())
        dc = res.json().get(str(pin))
    else:
        logger.error(res.text)
    return dc


def set_dc_in_device(url, pin, dc, freq):
    logger.info("setting dc at url {} with pin {} dc {} freq {}".format(url, pin, dc, freq))
    res = requests.post(url, json={'dc': dc, 'pin': pin, 'freq': freq})
    if res.status_code == 200:
        return 0
    logger.error(res.text)
    return -1


def get_time():
    return int(time.time())


def update_and_confirm_dc_in_device(label, pin, dc, freq):
    timestamp = get_time()
    url = DEVICES.get(label).get('url') + 'dc'
    logger.info("setting dc at url {} with pin {} dc {} freq {} at time {}".format(url, pin, dc, freq, timestamp))
    ret = set_dc_in_device(url, pin, dc, freq)
    if ret == 0:
        ret_dc = get_dc_from_device(url, pin)
        if dc == ret_dc:
            db.execute_sql(QUERY_DC_INSERT, (timestamp, label, dc), logger)
            return 0
        logger.error("requested dc {} while updated dc {}".format(dc, ret_dc))
    return -1


def collect_lux_values():
    logger.info("lux collection thread started")
    while 1:
        for label in DEVICES.keys():
            url = DEVICES.get(label).get('url') + 'lux'
            timestamp = time.time()
            lux = get_lux_from_device(url)
            logger.info("lux reply from rpi {}".format(str(lux)))
            for k,v in lux.items():
                db_label = "{}_{}".format(label,k)
	        db.execute_sql(QUERY_LUX_INSERT, (timestamp, db_label, lux), logger)
        time.sleep(5)


def collect_dc_values():
    logger.info("dc collection thread started")
    while 1:
        for label in DEVICES.keys():
            url = DEVICES.get(label).get('url')+'dc'
            timestamp = time.time()
            for pin in DEVICES.get(label).get('dc_pins'):
                lux = get_dc_from_device(url, pin)
                db.execute_sql(QUERY_DC_INSERT, (timestamp, label, pin, lux), logger)
        time.sleep(5)


def main():
    wait_time_for_db = config.general["wait_time_for_db"]
    logger.info("Waiting [%s] seconds for DB to come up", wait_time_for_db)
    time.sleep(wait_time_for_db)
    threading.Thread(target=collect_lux_values).start()
    threading.Thread(target=collect_dc_values).start()
    logger.info("init finished")


if __name__ == '__main__':
    main()
