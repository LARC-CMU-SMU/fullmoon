import psycopg2
import psycopg2.extras


def align_ts(m_ts_list, delta=5):
    return [delta * round(x / delta) for x in m_ts_list]


def process_wired_lux_dict(lux_dict):
    inter_dict = {}
    # smooth the timestamps
    lux_dict['aligned_ts']=align_ts(lux_dict['timestamp'])
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


def process_pixel_lux_dict(pixel_lux_dict):
    inter_dict = {}
    # smooth the timestamps
    pixel_lux_dict['aligned_ts']=align_ts(pixel_lux_dict['timestamp'])
    for i in range(len(pixel_lux_dict['timestamp'])):
        ts = pixel_lux_dict['aligned_ts'][i]
        m_pixel_label = pixel_lux_dict['patch_label'][i]
        cam_label = pixel_lux_dict['cam_label'][i]
        pixel = pixel_lux_dict['pixel'][i]
        # composite_label = "{}_{}".format(cam_label, m_pixel_label)
        if m_pixel_label not in inter_dict:
            inter_dict[m_pixel_label] = []
        inter_dict[m_pixel_label].append((ts, pixel))
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

def execute_sql_for_dict(query, values):
    con = None
    ret = None
    try:
        con = psycopg2.connect(database="fullmoon",
                               user="fullmoon",
                               password="fullmoon",
                               host="10.4.8.225",
                               port=5432)
        cursor = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute(query, values)
        inter_ret = cursor.fetchall()
        ret = [dict(row) for row in inter_ret]
    except Exception as e:
        print(str(e))
        if con:
            con.rollback()
    finally:
        if con:
            con.close()
        return ret


def load_finger_prints():
    QUERY_FP_SELECT = "SELECT * FROM fp"
    ret_dict ={}
    fp_dict_list = execute_sql_for_dict(QUERY_FP_SELECT,[])
    for fp in fp_dict_list:
        patch_label = fp['patch_label']
        if not ret_dict.get(patch_label):
            ret_dict[patch_label]={}
        lux_label = fp['lux_label']
        ret_dict[patch_label][lux_label]={'x2':float(fp['x2']),
                                               'x1':float(fp['x1']),
                                               'x0':float(fp['x0']),
                                               'pearson_corr':float(fp['pearson_corr'])}
    return ret_dict


def load_finger_prints_from_list(fp_dict_list):
    ret_dict={}
    for fp in fp_dict_list:
        patch_label = fp['patch_label']
        if not ret_dict.get(patch_label):
            ret_dict[patch_label]={}
        lux_label = fp['lux_label']
        ret_dict[patch_label][lux_label]={'x2':float(fp['x2']),
                                               'x1':float(fp['x1']),
                                               'x0':float(fp['x0']),
                                               'pearson_corr':float(fp['pearson_corr'])}

    return ret_dict
