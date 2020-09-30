import plotly.graph_objs as go
import psycopg2
import psycopg2.extras

from scripts.util.data_util import convert_str_list_to_time

START_TS = 1601417642
END_TS = 1601417642 + (3600*4)
# START_TS = 1601063536
# END_TS = 1601071469

SENSOR_LABEL = 'a'
SENSOR_PIN = 'tsl_2'
CAM_LABEL = 'b'

TRUE_LUX_QUERY = "SELECT * FROM lux WHERE label=%s and pin =%s and timestamp > %s and timestamp < %s ORDER BY timestamp;"
PSUDO_LUX_QUERY = "SELECT * FROM pixel_lux WHERE lux_label=%s and cam_label=%s and patch_label=%s and timestamp > %s and timestamp < %s ORDER BY timestamp;"
FP_QUERY = "select * from fp where lux_label = %s order by pearson_corr desc limit 1"


def get_highest_correlation(lux_label):
    from_db = execute_sql_for_dict(FP_QUERY, [lux_label,])
    return from_db[0]


def get_true_lux(label, pin, start_ts, end_ts):
    ret ={}
    from_db=execute_sql_for_dict(TRUE_LUX_QUERY,[label,pin,start_ts,end_ts])
    for row in from_db:
        for key in row.keys():
            if key not in ret.keys():
                ret[key]=[]
            ret[key].append(row[key])
    return ret


def get_psudo_lux(comp_lux_label,cam_label,patch_label,start_ts,end_ts):
    ret = {}
    from_db = execute_sql_for_dict(PSUDO_LUX_QUERY, [comp_lux_label,cam_label,patch_label,start_ts,end_ts])
    for row in from_db:
        for key in row.keys():
            if key not in ret.keys():
                ret[key] = []
            ret[key].append(row[key])
    return ret


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


def plot():
    fig = go.Figure()
    comp_key = "{}_{}".format(SENSOR_LABEL, SENSOR_PIN)
    lux_data=get_true_lux(SENSOR_LABEL, SENSOR_PIN, START_TS, END_TS)

    highest_pcorr = get_highest_correlation(comp_key)
    patch_label = highest_pcorr.get('patch_label')

    print(comp_key, patch_label, highest_pcorr.get('pearson_corr'))

    p_lux_data = get_psudo_lux(comp_key, CAM_LABEL, patch_label, START_TS, END_TS)

    fig.add_trace(go.Scatter(x=convert_str_list_to_time(lux_data.get('timestamp')),
                             y=lux_data.get('lux'),
                             mode='lines+markers',
                             name='true lux'))

    fig.add_trace(go.Scatter(x=convert_str_list_to_time(p_lux_data.get('timestamp')),
                             y=p_lux_data.get('lux'),
                             mode='lines',
                             name="pseudo lux"))
    fig.add_trace(go.Scatter(x=convert_str_list_to_time(p_lux_data.get('timestamp')),
                             y=p_lux_data.get('gray_mean'),
                             mode='lines',
                             name="pixel"))

    fig.show()


if __name__ == '__main__':
    plot()

