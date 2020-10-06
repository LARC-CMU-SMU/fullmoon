import plotly.graph_objs as go
import time

from scripts.m_util import execute_sql_for_dict
from scripts.util.data_util import convert_str_list_to_time

TIME_WINDOW_SIZE = 10*60

CAM_LABEL = 'b'

TRUE_LUX_QUERY = "SELECT * FROM lux WHERE timestamp > %s and timestamp < %s ORDER BY timestamp;"
DC_QUERY = "SELECT * FROM dc WHERE timestamp > %s and timestamp < %s ORDER BY timestamp;"
OCCUPANCY_QUERY = "SELECT * FROM occupancy WHERE timestamp > %s and timestamp < %s ORDER BY timestamp;"


def get_now():
    return int(time.time())


def get_plot_ready_data(list_of_dicts):
    ret = {}
    for row in list_of_dicts:
        for key in row.keys():
            if key not in ret.keys():
                ret[key] = []
            ret[key].append(row[key])
    return ret


def get_lux(start_ts, end_ts):
    ret = {}
    from_db=execute_sql_for_dict(TRUE_LUX_QUERY,[start_ts,end_ts])
    inter_ret = get_plot_ready_data(from_db)
    for i in range(len(inter_ret['timestamp'])):
        ts = inter_ret['timestamp'][i]
        label = inter_ret['label'][i]
        lux = inter_ret['lux'][i]
        pin = inter_ret['pin'][i]
        new_label = "{}_{}".format(label, pin)
        if new_label not in ret.keys():
            ret[new_label]={'ts':[],'lux':[]}
        ret[new_label]['ts'].append(ts)
        ret[new_label]['lux'].append(lux)

    return ret


def get_dc(start_ts, end_ts):
    ret = {}
    from_db=execute_sql_for_dict(DC_QUERY,[start_ts,end_ts])
    inter_ret = get_plot_ready_data(from_db)
    for i in range(len(inter_ret['timestamp'])):
        ts = inter_ret['timestamp'][i]
        label = inter_ret['label'][i]
        dc = inter_ret['dc'][i]/10000
        pin = inter_ret['pin'][i]
        new_label = "{}_{}".format(label, pin)
        if new_label not in ret.keys():
            ret[new_label]={'ts':[],'dc':[]}
        ret[new_label]['ts'].append(ts)
        ret[new_label]['dc'].append(dc)
    return ret




def plot():
    fig = go.Figure()
    end_ts=get_now()
    start_ts = end_ts - TIME_WINDOW_SIZE
    lux_data=get_lux(start_ts, end_ts)
    for label, data in lux_data.items():
        fig.add_trace(go.Scatter(x=convert_str_list_to_time(data.get('ts')),
                                 y=data.get('lux'),
                                 mode='markers+lines',
                                 name="lux {}".format(label)))
    # occupancy_data = get_occupancy(start_ts, end_ts)
    dc_data = get_dc(start_ts, end_ts)
    for label, data in dc_data.items():
        fig.add_trace(go.Scatter(x=convert_str_list_to_time(data.get('ts')),
                                 y=data.get('dc'),
                                 mode='markers+lines',
                                 name="dc {}".format(label)))

    fig.show()


if __name__ == '__main__':
    plot()

