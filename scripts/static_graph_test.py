import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque
import psycopg2
import psycopg2.extras
from plotly.subplots import make_subplots

from scripts.util.data_util import convert_str_list_to_time

TRUE_LUX_QUERY = "SELECT * FROM lux WHERE timestamp > 1600096083 and timestamp < 1600101372 ORDER BY timestamp;-- DESC LIMIT 1000"
PSUDO_LUX_QUERY = "SELECT * FROM pixel_lux WHERE timestamp > 1600096083 and timestamp < 1600101372 ORDER BY timestamp; --ORDER BY timestamp DESC LIMIT 100000"
FP_QUERY = "select * from fp where lux_label = %s order by pearson_corr desc limit 1"

# X = deque(maxlen=20)
# X.append(1)
# Y = deque(maxlen=20)
# Y.append(1)

LUX_DATA={}
P_LUX_DATA={}


def get_highest_correlation(lux_label):
    from_db = execute_sql_for_dict(FP_QUERY, [lux_label,])
    return from_db[0]


def get_true_lux():
    ret={}
    from_db=execute_sql_for_dict(TRUE_LUX_QUERY,[])
    for row in from_db:
        ts=row.get('timestamp')
        label=row.get('label')
        lux=row.get('lux')
        pin=row.get('pin')
        composit_key="{}_{}".format(label,pin)
        if composit_key not in ret.keys():
            ret[composit_key]={'ts':[],'lux':[]}
        ret[composit_key]['ts'].append(ts)
        ret[composit_key]['lux'].append(lux)
    return ret


def get_psudo_lux():
    ret = {}
    from_db = execute_sql_for_dict(PSUDO_LUX_QUERY, [])
    for row in from_db:
        ts = row.get('timestamp')
        patch_label = row.get('patch_label')
        lux_sensor_label = row.get('lux_label')
        lux = row.get('lux')
        pixel = row.get('pixel')
        composit_key = "{}_{}".format(patch_label, lux_sensor_label)
        if composit_key not in ret.keys():
            ret[composit_key] = {'ts': [], 'lux': [], 'pixel':[]}
        ret[composit_key]['ts'].append(ts)
        ret[composit_key]['lux'].append(lux)
        ret[composit_key]['pixel'].append(pixel)

    return ret


def update_data():
    global LUX_DATA, P_LUX_DATA
    LUX_DATA=get_true_lux()
    P_LUX_DATA=get_psudo_lux()


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


def update_graph_scatter():
    sensor='b_tsl_2'


    update_data()
    #
    fig = go.Figure()
    #
    labels = LUX_DATA.keys()
    sorted(labels)
    for i,label in enumerate(labels):
        if not sensor in label:
            continue
        data = LUX_DATA.get(label)
        fig.add_trace(go.Scatter(x=convert_str_list_to_time(data.get('ts')),
                                 y=data.get('lux'),
                                 mode='lines+markers',
                                 name=label))

    labels = P_LUX_DATA.keys()
    sorted(labels)
    for i, label in enumerate(labels):
        if not sensor in label:
            continue
        highest_pcorr = get_highest_correlation(sensor)
        # highest_pcorr_patch_label = highest_pcorr.get('patch_label')
        highest_pcorr_patch_label = "B10"


        if highest_pcorr_patch_label not in label:
            continue
        data = P_LUX_DATA.get(label)
        fig.add_trace(go.Scatter(x=convert_str_list_to_time(data.get('ts')),
                                 y=data.get('lux'),
                                 mode='lines',
                                 name="p_lux_{}".format(label)))
        fig.add_trace(go.Scatter(x=convert_str_list_to_time(data.get('ts')),
                                 y=data.get('pixel'),
                                 mode='lines',
                                 name="p_pixel_{}".format(label)))

    fig.show()


if __name__ == '__main__':
    update_graph_scatter()

