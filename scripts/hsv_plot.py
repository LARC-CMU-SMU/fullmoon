import plotly.graph_objs as go
import psycopg2
import psycopg2.extras

from scripts.util.data_util import convert_str_list_to_time

# start_ts = 1600096083
# end_ts = 1600101372

start_ts = 1601055543
end_ts = 1601063476

PIXEL_STAT_QUERY = "SELECT * FROM pixel_lux WHERE timestamp > {} and timestamp < {} and patch_label={} and lux_label={} ORDER BY timestamp;".format(start_ts, end_ts,"'D4'","'c_tsl_2'")

# X = deque(maxlen=20)
# X.append(1)
# Y = deque(maxlen=20)
# Y.append(1)

# LUX_DATA={}
P_LUX_DATA={}


def get_pixel_stat():
    ret = {}
    from_db = execute_sql_for_dict(PIXEL_STAT_QUERY, [])
    for row in from_db:
        if row["v_mean"] > 0:
            for key in row.keys():
                if key not in ret.keys():
                    ret[key] = []
                ret[key].append(row[key])
    return ret


def update_data():
    global P_LUX_DATA
    P_LUX_DATA=get_pixel_stat()


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
    update_data()
    fig = go.Figure()

    for header,values in P_LUX_DATA.items():
        fig.add_trace(go.Scatter(x=list(range(len(values))),
                                 y=values,
                                 mode='markers',
                                 name=header))

    fig.show()


if __name__ == '__main__':
    update_graph_scatter()

