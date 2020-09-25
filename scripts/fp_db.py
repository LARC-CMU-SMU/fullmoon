
from scripts.m_util import *
from scripts.util.data_util import *
from scripts.util.file_util import *
import plotly.graph_objects as go

CSV_DIR = "/Users/kasun/working_data/sep25/"
START_TS = 1600956015
END_TS = 1600963950

OUT_CSV = '{}correlation.csv'.format(CSV_DIR)
LUX_QUERY = "SELECT * FROM lux WHERE timestamp > {} and timestamp < {} ORDER BY timestamp".format(START_TS, END_TS)
PIXEL_QUERY = "SELECT * FROM pixel_lux WHERE timestamp > {} and timestamp < {} ORDER BY timestamp".format(START_TS, END_TS)


def get_true_lux():
    ret={'timestamp':[], 'label':[], 'lux':[], 'pin':[]}
    from_db=execute_sql_for_dict(LUX_QUERY, [])
    for row in from_db:
        ts=row.get('timestamp')
        label=row.get('label')
        lux=row.get('lux')
        pin=row.get('pin')
        ret.get('timestamp').append(ts)
        ret.get('label').append(label)
        ret.get('lux').append(lux)
        ret.get('pin').append(pin)
    return ret


def get_true_pixel():
    ret={'timestamp':[],'cam_label':[],'patch_label':[],'pixel':[],'h_mean':[],'s_mean':[],'v_mean':[]}
    from_db=execute_sql_for_dict(PIXEL_QUERY, [])
    for row in from_db:
        ts=row.get('timestamp')
        cam_label=row.get('cam_label')
        patch_label = row.get('patch_label')
        pixel=row.get('gray_mean')
        h_mean = row.get('h_mean')
        s_mean = row.get('s_mean')
        v_mean = row.get('v_mean')
        ret.get('timestamp').append(ts)
        ret.get('cam_label').append(cam_label)
        ret.get('patch_label').append(patch_label)
        ret.get('pixel').append(pixel)
        ret.get('h_mean').append(h_mean)
        ret.get('s_mean').append(s_mean)
        ret.get('v_mean').append(v_mean)
    return ret


def get_hsv_ranges(m_pixel_dict):
    inter_dict = {}
    # smooth the timestamps
    # pixel_lux_dict['aligned_ts'] = align_ts(pixel_lux_dict['timestamp'])
    for i in range(len(m_pixel_dict['timestamp'])):
        ts = m_pixel_dict['aligned_ts'][i]
        m_pixel_label = m_pixel_dict['patch_label'][i]
        cam_label = m_pixel_dict['cam_label'][i]
        pixel = m_pixel_dict['pixel'][i]
        h_mean = m_pixel_dict['h_mean'][i]
        s_mean = m_pixel_dict['s_mean'][i]
        v_mean = m_pixel_dict['v_mean'][i]
        composite_label = "{}_{}".format(cam_label, m_pixel_label)
        if composite_label not in inter_dict:
            inter_dict[composite_label] = {'h':[],'s':[],'v':[]}
        inter_dict[composite_label]['h'].append(h_mean)
        inter_dict[composite_label]['s'].append(s_mean)
        inter_dict[composite_label]['v'].append(v_mean)

    ret_dict = {}
    for label, hsv_value_lists in inter_dict.items():
        h_min = min(hsv_value_lists['h'])
        h_max = max(hsv_value_lists['h'])
        s_min = min(hsv_value_lists['s'])
        s_max = max(hsv_value_lists['s'])
        v_min = min(hsv_value_lists['v'])
        v_max = max(hsv_value_lists['v'])
        ret_dict[label]={'h_min':h_min, 'h_max':h_max, 's_min':s_min, 's_max':s_max, 'v_min':v_min, 'v_max':v_max}
    return ret_dict


lux_data = get_true_lux()
pixel_data = get_true_pixel()


# rearrange the data to make it easier to calculate correlation
processed_lux = process_wired_lux_dict(lux_data)

processed_pixel = process_pixel_lux_dict(pixel_data)

hsv_ranges = get_hsv_ranges(pixel_data)

to_csv_dict_list = []

for_testing_coeff = {}

for pixel_label in processed_pixel.keys():
    for lux_label in processed_lux.keys():
        current_pixel_dict = processed_pixel[pixel_label]
        current_lux_dict = processed_lux[lux_label]

        ts_list, lux_list, pixel_list = get_synced_pixel_lux_lists(current_pixel_dict, current_lux_dict)

        lux_list = np.asarray(lux_list)
        pixel_list = np.asarray(pixel_list)
        if len(ts_list) > 0:
            fit = np.polyfit(pixel_list,lux_list, 2)  # all prev lines are there, in order for us to do this !!!!
            corr = get_pearson_correlation_coefficient(pixel_list, lux_list)
            hsv_values = hsv_ranges.get(pixel_label)
            h_min = hsv_values['h_min']
            h_max = hsv_values['h_max']
            s_min = hsv_values['s_min']
            s_max = hsv_values['s_max']
            v_min = hsv_values['v_min']
            v_max = hsv_values['v_max']

            current_dict = {
                'patch_label': pixel_label,
                'lux_label': lux_label,
                'tuple_len': len(ts_list),
                'pearson_corr': corr,
                'x2': fit[0],
                'x1': fit[1],
                'x0': fit[2],
                'h_min':h_min,
                'h_max':h_max,
                's_min':s_min,
                's_max':s_max,
                'v_min':v_min,
                'v_max':v_max
            }
            # calc_lux_list
            to_csv_dict_list.append(current_dict)

            # if corr > .97:
            #     calc_lux_list=[fit[0] * x * x + fit[1] * x + fit[2] for x in pixel_list]
            #     import matplotlib.pyplot as plt
            #     fig,(a1,a2) = plt.subplots(1,2)
            #     a1.scatter(pixel_list, lux_list)
            #     sorted_pixel_list_for_plot = pixel_list.copy()
            #     sorted_pixel_list_for_plot.sort()
            #     a1.plot(sorted_pixel_list_for_plot,
            #              fit[0] * sorted_pixel_list_for_plot * sorted_pixel_list_for_plot + fit[1] * sorted_pixel_list_for_plot + fit[2])
            #     a2.scatter(lux_list,calc_lux_list)
            #     a2.plot(lux_list,lux_list)
            #     plt.title("pixel {} vs lux {}".format(pixel_label, lux_label))
            #     plt.show()
            #
            #     print("corr is higher than .97")

write_dictionary_to_csv_file(to_csv_dict_list, OUT_CSV)



### testing
# FP=load_finger_prints()
# fig = go.Figure()
# for pixel_label in processed_pixel.keys():
#     for lux_label in processed_lux_all.keys():
#         current_pixel_dict = processed_pixel[pixel_label]
#         current_lux_dict = processed_lux_all[lux_label]
#
#         ts_list, lux_list, pixel_list = get_synced_pixel_lux_lists(current_pixel_dict, current_lux_dict)
#
#         lux_list = np.asarray(lux_list)
#         pixel_list = np.asarray(pixel_list)
#         calculated_coefficients = FP.get(pixel_label).get(lux_label)
#         if len(ts_list) > 0:
#             if calculated_coefficients['pearson_corr'] > .97:
#                 if 'b' in lux_label:
#                     print(lux_label)
#                     x2=calculated_coefficients['x2']
#                     x1=calculated_coefficients['x1']
#                     x0=calculated_coefficients['x0']
#
#                     calc_lux_list2=[x2 * x * x + x1 * x + x0 for x in pixel_list]
#                     # import matplotlib.pyplot as plt
#                     # _,(a1,a2) = plt.subplots(1,2)
#                     # a1.scatter(pixel_list2, lux_list2)
#                     # sorted_pixel_list_for_plot = pixel_list2.copy()
#                     # sorted_pixel_list_for_plot.sort()
#                     # a2.scatter(lux_list2,calc_lux_list2)
#                     # a2.plot(lux_list2,lux_list2)
#                     # plt.title("pixel {} vs lux {}".format(pixel_label, lux_label))
#                     # plt.show()
#
#                     fig.add_trace(go.Scatter(x=convert_str_list_to_time(ts_list),
#                                              y=lux_list,
#                                              mode='lines',
#                                              name="lux_{}".format(lux_label)))
#                     fig.add_trace(go.Scatter(x=convert_str_list_to_time(ts_list),
#                                              y=calc_lux_list2,
#                                              mode='lines',
#                                              name="calc_lux_{} <- {}".format(lux_label, pixel_label)))
#             #
#                     # print("corr is higher than .97")
#
# fig.show()



print("that's all folks")
