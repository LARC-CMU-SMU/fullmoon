from scripts.util.data_util import *
from scripts.util.file_util import *
import plotly.graph_objects as go

CSV_DIR = "/Users/kasun/working_data/sep11/"
LUX_FILE_NAME = "{}lux.csv".format(CSV_DIR)
# SENSOR_TAG_LUX_FILE_NAME = "{}st_lux.csv".format(CSV_DIR)
PIXEL_FILE_NAME = "{}pixel_lux.csv".format(CSV_DIR)
OUT_CSV = '{}correlation_pt3.csv'.format(CSV_DIR)

FLOAT_DATA_HEADERS = ["pixel", 'lux', 'light']
INT_DATA_HEADERS = ['timestamp', ]
TIME_DATA_HEADERS = []

pixel_data = get_data_dictionary_from_csv(PIXEL_FILE_NAME)
pixel_data = fix_data_types(pixel_data, FLOAT_DATA_HEADERS, INT_DATA_HEADERS, TIME_DATA_HEADERS)

lux_data = get_data_dictionary_from_csv(LUX_FILE_NAME)
lux_data = fix_data_types(lux_data, FLOAT_DATA_HEADERS, INT_DATA_HEADERS, TIME_DATA_HEADERS)

# st_lux_data = get_data_dictionary_from_csv(SENSOR_TAG_LUX_FILE_NAME)
# st_lux_data = fix_data_types(st_lux_data, FLOAT_DATA_HEADERS, INT_DATA_HEADERS, TIME_DATA_HEADERS)


def get_shifted_sensor_tag_time_line(m_ts_list, delta):
    ret_list = [x + delta for x in m_ts_list]
    return ret_list


def align_ts(m_ts_list, delta=5):
    return [delta * round(x / delta) for x in m_ts_list]


def process_wired_lux_dict(lux_dict):
    inter_dict = {}
    for i in range(len(lux_dict['timestamp'])):
        ts = lux_dict['aligned_ts'][i]
        label = lux_dict['label'][i]
        pin = lux_dict['pin'][i]
        lux = lux_dict['lux'][i]
        new_label = "{}_{}".format(label, pin)
        if new_label not in inter_dict:
            inter_dict[new_label] = []
        inter_dict[new_label].append((ts, lux))
    ret_dict = {}
    for k, v in inter_dict.items():
        label_dict = {}
        for tup in v:
            label_dict[tup[0]] = float(tup[1])
        ret_dict[k] = label_dict
    return ret_dict


def process_pixel_lux_dict(lux_dict):
    inter_dict = {}
    for i in range(len(lux_dict['timestamp'])):
        ts = lux_dict['aligned_ts'][i]
        m_pixel_label = lux_dict['patch_label'][i]
        cam_label = lux_dict['cam_label'][i]
        pixel = lux_dict['pixel'][i]
        new_label = "{}_{}".format(cam_label, m_pixel_label)
        if new_label not in inter_dict:
            inter_dict[new_label] = []
        inter_dict[new_label].append((ts, pixel))
    ret_dict = {}
    for k, v in inter_dict.items():
        label_dict = {}
        for tup in v:
            label_dict[tup[0]] = float(tup[1])
        ret_dict[k] = label_dict
    return ret_dict


def process_sensor_tag_lux_dict(st_lux_dict):
    inter_dict = {}
    for i in range(len(st_lux_dict['timestamp'])):
        ts = st_lux_dict['aligned_ts'][i]
        label = st_lux_dict['label'][i]
        pin = 'sensor_tag'
        lux = st_lux_dict['light'][i]
        new_label = "{}_{}".format(label, pin)
        if new_label not in inter_dict:
            inter_dict[new_label] = []
        inter_dict[new_label].append((ts, lux))
    ret_dict = {}
    for k, v in inter_dict.items():
        label_dict = {}
        for tup in v:
            label_dict[tup[0]] = float(tup[1])
        ret_dict[k] = label_dict
    return ret_dict


def process_pixel_dict(pixel_dict):
    inter_dict = {}
    m_ts_list = pixel_dict['aligned_ts']
    for k, v in pixel_dict.items():
        inter_dict[k] = list(zip(m_ts_list, v))
    ret_dict = {}
    for k, v in inter_dict.items():
        label_dict = {}
        for tup in v:
            label_dict[tup[0]] = float(tup[1])
        ret_dict[k] = label_dict
    del ret_dict['timestamp']
    del ret_dict['aligned_ts']

    return ret_dict


def get_synced_pixel_lux_lists(pixel_label_dict, lux_label_dict):
    lux_ts_list = lux_label_dict.keys()
    sorted(lux_ts_list)
    m_lux_list = []
    m_pixel_list = []
    ret_ts_list = []
    for ts in lux_ts_list:
        lux_val = lux_label_dict.get(ts)
        if lux_val > 3:  # remove the sub 3 lux data points to avoid the strong correlation resulting from 0,0 points
            pixel_val = pixel_label_dict.get(ts)
            if pixel_val is not None:
                m_lux_list.append(lux_val)
                m_pixel_list.append(pixel_val)
                ret_ts_list.append(ts)
    return ret_ts_list, m_lux_list, m_pixel_list


# correct the time diff on PC and rpi used to collect the sensor tag data
# st_lux_data['timestamp'] = get_shifted_sensor_tag_time_line(st_lux_data['timestamp'], 3360)

# smooth the timestamps
lux_data['aligned_ts'] = align_ts(lux_data['timestamp'])
pixel_data['aligned_ts'] = align_ts(pixel_data['timestamp'])
# st_lux_data['aligned_ts'] = align_ts(st_lux_data['timestamp'])

# rearrange the data to make it easier to calculate correlation
processed_lux = process_wired_lux_dict(lux_data)
processed_pixel = process_pixel_lux_dict(pixel_data)
# processed_st_lux = process_sensor_tag_lux_dict(st_lux_data)

# combine the wired lux and sensor tag lux together
processed_lux_all = {}
processed_lux_all.update(processed_lux)
# processed_lux_all.update(processed_st_lux)

to_csv_dict_list = []

for pixel_label in processed_pixel.keys():
    for lux_label in processed_lux_all.keys():
        current_pixel_dict = processed_pixel[pixel_label]
        current_lux_dict = processed_lux_all[lux_label]

        ts_list, lux_list, pixel_list = get_synced_pixel_lux_lists(current_pixel_dict, current_lux_dict)

        lux_list = np.asarray(lux_list)
        pixel_list = np.asarray(pixel_list)
        if len(ts_list) > 0:
            fit = np.polyfit(lux_list, pixel_list, 2)  # all prev lines are there so we can do this !!!!
            corr = get_pearson_correlation_coefficient(lux_list, pixel_list)

            current_dict = {
                'patch_label': pixel_label,
                'lux_label': lux_label,
                'tuple_len': len(ts_list),
                'pearson_corr': corr,
                'x2': fit[0],
                'x1': fit[1],
                'x0': fit[2]
            }
            to_csv_dict_list.append(current_dict)

write_dictionary_to_csv_file(to_csv_dict_list, OUT_CSV)

# ts_list, lux_list, pixel_list = get_synced_pixel_lux_lists(processed_pixel,processed_st_lux,PIXEL_LABEL,LUX_LABLE)


# fig = go.Figure()
# fig.add_trace(go.Scatter(x=list(processed_st_lux['f_sensor_tag'].keys()),
#                              y=list(processed_st_lux['f_sensor_tag'].values()),
#                              mode='lines',
#                              name='lux'))
# fig.add_trace(go.Scatter(x=list(processed_pixel['A2'].keys()),
#                              y=list(processed_pixel['A2'].values()),
#                              mode='lines',
#                              name='pixel'))

# fig.add_trace(go.Scatter(x=ts_list,
#                              y=lux_list,
#                              mode='lines',
#                              name='lux'))
# fig.add_trace(go.Scatter(x=ts_list,
#                              y=pixel_list,
#                              mode='lines',
#                              name='pixel'))
#
#
#
# fig.show()


# import matplotlib.pyplot as plt
#
# plt.scatter(lux_list, pixel_list)
#
# sorted_lux_for_plot = lux_list.copy()
# sorted_lux_for_plot.sort()
# plt.plot(sorted_lux_for_plot,
#          fit[0] * sorted_lux_for_plot * sorted_lux_for_plot + fit[1] * sorted_lux_for_plot + fit[2], color='darkblue',
#          linewidth=2)
#
# plt.text(10, 35, 'y={:.2f}x^2+{:.2f}x+{:.2f}'.format(fit[0], fit[1], fit[2]), color='darkblue', size=12)
#
# plt.title('polynomial regression {} vs {} '.format(LUX_LABEL, PIXEL_LABEL), size=18)
# plt.xlabel('lux %', size=12)
# plt.ylabel('pixel', size=12)
# #
# plt.show()

#
# get_r2_score_and_stuff(dc1_list, lux_list)


print("that's all folks")
