
from scripts.m_util import *
from scripts.util.data_util import *
from scripts.util.file_util import *
import plotly.graph_objects as go

CSV_DIR = "/Users/kasun/working_data/sep15/"
LUX_FILE_NAME = "{}lux1.csv".format(CSV_DIR)
# LUX_FILE_NAME2 = "{}lux2.csv".format(CSV_DIR)

# SENSOR_TAG_LUX_FILE_NAME = "{}st_lux.csv".format(CSV_DIR)
PIXEL_FILE_NAME = "{}pixel_lux1.csv".format(CSV_DIR)
# PIXEL_FILE_NAME2 = "{}pixel_lux_exp2.csv".format(CSV_DIR)

OUT_CSV = '{}correlation.csv'.format(CSV_DIR)

FLOAT_DATA_HEADERS = ["pixel", 'lux', 'light']
INT_DATA_HEADERS = ['timestamp', ]
TIME_DATA_HEADERS = []

pixel_data = get_data_dictionary_from_csv(PIXEL_FILE_NAME)
pixel_data = fix_data_types(pixel_data, FLOAT_DATA_HEADERS, INT_DATA_HEADERS, TIME_DATA_HEADERS)

# pixel_data2 = get_data_dictionary_from_csv(PIXEL_FILE_NAME2)
# pixel_data2 = fix_data_types(pixel_data2, FLOAT_DATA_HEADERS, INT_DATA_HEADERS, TIME_DATA_HEADERS)

lux_data = get_data_dictionary_from_csv(LUX_FILE_NAME)
lux_data = fix_data_types(lux_data, FLOAT_DATA_HEADERS, INT_DATA_HEADERS, TIME_DATA_HEADERS)
# lux_data2 = get_data_dictionary_from_csv(LUX_FILE_NAME2)
# lux_data2 = fix_data_types(lux_data2, FLOAT_DATA_HEADERS, INT_DATA_HEADERS, TIME_DATA_HEADERS)

# st_lux_data = get_data_dictionary_from_csv(SENSOR_TAG_LUX_FILE_NAME)
# st_lux_data = fix_data_types(st_lux_data, FLOAT_DATA_HEADERS, INT_DATA_HEADERS, TIME_DATA_HEADERS)


def get_shifted_sensor_tag_time_line(m_ts_list, delta):
    ret_list = [x + delta for x in m_ts_list]
    return ret_list



# correct the time diff on PC and rpi used to collect the sensor tag data
# st_lux_data['timestamp'] = get_shifted_sensor_tag_time_line(st_lux_data['timestamp'], 3360)


# rearrange the data to make it easier to calculate correlation
processed_lux = get_processed_lux_dict(lux_data)
# processed_lux2 = process_wired_lux_dict(lux_data2)

processed_pixel = get_processed_gray_dict_and_hue_dict(pixel_data)
# processed_pixel2 = process_pixel_lux_dict(pixel_data2)
# processed_st_lux = process_sensor_tag_lux_dict(st_lux_data)

# combine the wired lux and sensor tag lux together
processed_lux_all = {}
processed_lux_all.update(processed_lux)
# processed_lux_all2 = {}
# processed_lux_all2.update(processed_lux2)
# processed_lux_all.update(processed_st_lux)

to_csv_dict_list = []

for_testing_coeff = {}

# for pixel_label in processed_pixel.keys():
#     for lux_label in processed_lux_all.keys():
#         current_pixel_dict = processed_pixel[pixel_label]
#         current_lux_dict = processed_lux_all[lux_label]
#
#         ts_list, lux_list, pixel_list = get_synced_pixel_lux_lists(current_pixel_dict, current_lux_dict)
#
#         lux_list = np.asarray(lux_list)
#         pixel_list = np.asarray(pixel_list)
#         if len(ts_list) > 0:
#             fit = np.polyfit(pixel_list,lux_list, 2)  # all prev lines are there, in order for us to do this !!!!
#             corr = get_pearson_correlation_coefficient(pixel_list, lux_list)
#
#             current_dict = {
#                 'patch_label': pixel_label,
#                 'lux_label': lux_label,
#                 'tuple_len': len(ts_list),
#                 'pearson_corr': corr,
#                 'x2': fit[0],
#                 'x1': fit[1],
#                 'x0': fit[2]
#             }
#             # calc_lux_list
#             to_csv_dict_list.append(current_dict)

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

# write_dictionary_to_csv_file(to_csv_dict_list, OUT_CSV)

FP=load_finger_prints()
fig = go.Figure()

### testing
for pixel_label in processed_pixel.keys():
    for lux_label in processed_lux_all.keys():
        current_pixel_dict = processed_pixel[pixel_label]
        current_lux_dict = processed_lux_all[lux_label]

        ts_list, lux_list, pixel_list = get_synced_pixel_lux_lists(current_pixel_dict, current_lux_dict)

        lux_list = np.asarray(lux_list)
        pixel_list = np.asarray(pixel_list)
        calculated_coefficients = FP.get(pixel_label).get(lux_label)
        if len(ts_list) > 0:
            if calculated_coefficients['pearson_corr'] > .97:
                if 'b' in lux_label:
                    print(lux_label)
                    x2=calculated_coefficients['x2']
                    x1=calculated_coefficients['x1']
                    x0=calculated_coefficients['x0']

                    calc_lux_list2=[x2 * x * x + x1 * x + x0 for x in pixel_list]
                    # import matplotlib.pyplot as plt
                    # _,(a1,a2) = plt.subplots(1,2)
                    # a1.scatter(pixel_list2, lux_list2)
                    # sorted_pixel_list_for_plot = pixel_list2.copy()
                    # sorted_pixel_list_for_plot.sort()
                    # a2.scatter(lux_list2,calc_lux_list2)
                    # a2.plot(lux_list2,lux_list2)
                    # plt.title("pixel {} vs lux {}".format(pixel_label, lux_label))
                    # plt.show()

                    fig.add_trace(go.Scatter(x=convert_str_list_to_time(ts_list),
                                             y=lux_list,
                                             mode='lines',
                                             name="lux_{}".format(lux_label)))
                    fig.add_trace(go.Scatter(x=convert_str_list_to_time(ts_list),
                                             y=calc_lux_list2,
                                             mode='lines',
                                             name="calc_lux_{} <- {}".format(lux_label, pixel_label)))
            #
                    # print("corr is higher than .97")

fig.show()

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
