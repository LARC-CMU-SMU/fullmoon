
from scripts.m_util import *
from scripts.util.data_util import *
from scripts.util.file_util import *
import plotly.graph_objects as go

# pulls the pixel values and lux values from the DB and find the correlations among them
# result will be written to OUT_CSV
# resulting csv file can be imported to DB(fp table) directly

CSV_DIR = "/Users/kasun/working_data/sep26/"
OUT_CSV = '{}correlation.csv'.format(CSV_DIR)
CAM_LABEL = 'b'

START_TS = 1601040358
END_TS = 1601048295

# for the h range, only consider the data points where v channel value is above this threshold.
# because once the v channel value drops after certain value h value doesn't stay constant.
# (this is the reason why every cat is gray in the dark)
V_CHANNEL_THRESHOLD = 20

LUX_QUERY = "SELECT * FROM lux WHERE timestamp > %s and timestamp < %s ORDER BY timestamp"
PIXEL_QUERY = "SELECT * FROM pixel_lux WHERE cam_label=%s and timestamp > %s and timestamp < %s ORDER BY timestamp"


def get_lux_from_db():
    print("loading lux values")
    ret={'timestamp':[], 'label':[], 'lux':[], 'pin':[]}
    from_db=execute_sql_for_dict(LUX_QUERY, [START_TS, END_TS])
    for row in from_db:
        ret.get('timestamp').append(row.get('timestamp'))
        ret.get('label').append(row.get('label'))
        ret.get('lux').append(row.get('lux'))
        ret.get('pin').append(row.get('pin'))
    return ret


def get_pixel_from_db():
    print("loading pixel values")
    ret={'timestamp':[],'cam_label':[],'patch_label':[],'pixel':[],'h_mean':[],'s_mean':[],'v_mean':[]}
    from_db=execute_sql_for_dict(PIXEL_QUERY, [CAM_LABEL, START_TS, END_TS])
    for row in from_db:
        ret.get('timestamp').append(row.get('timestamp'))
        ret.get('cam_label').append(row.get('cam_label'))
        ret.get('patch_label').append(row.get('patch_label'))
        ret.get('pixel').append(row.get('gray_mean'))
        ret.get('h_mean').append(row.get('h_mean'))
        ret.get('s_mean').append(row.get('s_mean'))
        ret.get('v_mean').append(row.get('v_mean'))
    return ret


def get_min_and_max(m_list):
    if len(m_list):
        return min(m_list), max(m_list)
    else:
        return -1,-1


def get_hsv_ranges(m_pixel_dict):
    print("calculating hsv ranges")
    inter_dict = {}
    for i in range(len(m_pixel_dict['timestamp'])):
        m_pixel_label = m_pixel_dict['patch_label'][i]
        cam_label = m_pixel_dict['cam_label'][i]
        h_mean = m_pixel_dict['h_mean'][i]
        s_mean = m_pixel_dict['s_mean'][i]
        v_mean = m_pixel_dict['v_mean'][i]
        # composite_label = "{}_{}".format(cam_label, m_pixel_label)
        if m_pixel_label not in inter_dict:
            inter_dict[m_pixel_label] = {'h': [], 's': [], 'v': []}
        if v_mean > 20 :
            inter_dict[m_pixel_label]['h'].append(h_mean)
            inter_dict[m_pixel_label]['s'].append(s_mean)
            inter_dict[m_pixel_label]['v'].append(v_mean)

    ret_dict = {}
    for label, hsv_value_lists in inter_dict.items():
        h_min , h_max = get_min_and_max(hsv_value_lists['h'])
        s_min, s_max = get_min_and_max(hsv_value_lists['s'])
        v_min, v_max = get_min_and_max(hsv_value_lists['v'])
        ret_dict[label]={'h_min':h_min, 'h_max':h_max, 's_min':s_min, 's_max':s_max, 'v_min':v_min, 'v_max':v_max}
    return ret_dict


lux_data = get_lux_from_db()
pixel_data = get_pixel_from_db()

# rearrange the data to make it easier to calculate correlation
print("processing lux data")
processed_lux = process_wired_lux_dict(lux_data)
print("processing pixel data")
processed_pixel = process_pixel_lux_dict(pixel_data)

hsv_ranges = get_hsv_ranges(pixel_data)

to_csv_dict_list = []

print("calculating finger prints")
for pixel_label in processed_pixel.keys():  # iterate over the patches
    for lux_label in processed_lux.keys():  # iterate over the lux sensors
        # we are building coefficients for all the patch, lux sensor combinations
        current_pixel_dict = processed_pixel[pixel_label]
        current_lux_dict = processed_lux[lux_label]

        # smooth the pixel and lux tuples to a same time points
        ts_list, lux_list, pixel_list = get_synced_pixel_lux_lists(current_pixel_dict, current_lux_dict)

        lux_list = np.asarray(lux_list)
        pixel_list = np.asarray(pixel_list)
        if len(ts_list) > 0:
            # finally after all the courting ...
            fit = np.polyfit(pixel_list,lux_list, 2)
            corr = get_pearson_correlation_coefficient(pixel_list, lux_list)
            hsv_values = hsv_ranges.get(pixel_label)
            h_min= hsv_values.get('h_min')
            h_max= hsv_values.get('h_max')
            s_min= hsv_values.get('s_min')
            s_max= hsv_values.get('s_max')
            v_min= hsv_values.get('v_min')
            v_max= hsv_values.get('v_max')
            current_dict = {
                'cam_label':CAM_LABEL,
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
            to_csv_dict_list.append(current_dict)
        else:
            print("not enough data points {},{}".format(pixel_label, lux_label))

write_dictionary_to_csv_file(to_csv_dict_list, OUT_CSV)

print("that's all folks")
