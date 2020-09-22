

from scripts.m_util import *
from scripts.util.data_util import *
from scripts.util.file_util import *

CSV_DIR = "/Users/kasun/working_data/sept14/"
LUX_FILE_NAME = "{}lux_exp1.csv".format(CSV_DIR)
# SENSOR_TAG_LUX_FILE_NAME = "{}st_lux.csv".format(CSV_DIR)
PIXEL_FILE_NAME = "{}pixel_lux_exp1.csv".format(CSV_DIR)

FINGER_PRINTS = {}
FLOAT_DATA_HEADERS = ["pixel", 'lux', 'light']
INT_DATA_HEADERS = ['timestamp', ]
TIME_DATA_HEADERS = []


load_finger_prints()

pixel_data = get_data_dictionary_from_csv(PIXEL_FILE_NAME)
pixel_data = fix_data_types(pixel_data, FLOAT_DATA_HEADERS, INT_DATA_HEADERS, TIME_DATA_HEADERS)

lux_data = get_data_dictionary_from_csv(LUX_FILE_NAME)
lux_data = fix_data_types(lux_data, FLOAT_DATA_HEADERS, INT_DATA_HEADERS, TIME_DATA_HEADERS)


print("that's all folks")