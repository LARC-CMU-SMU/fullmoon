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


TRUE_LUX_QUERY = "SELECT * FROM lux ORDER BY timestamp DESC LIMIT 500"

# X = deque(maxlen=20)
# X.append(1)
# Y = deque(maxlen=20)
# Y.append(1)

LUX_DATA={}


app = dash.Dash(__name__)
app.layout = html.Div(
    [
        dcc.Graph(id='live-graph', animate=True),
        dcc.Interval(
            id='graph-update',
            interval=1*1000
        ),
    ]
)


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


def update_data():
    global LUX_DATA
    LUX_DATA=get_true_lux()


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


@app.callback(Output('live-graph', 'figure'),
              [Input('graph-update', 'n_intervals')])
def update_graph_scatter(input_data):
    # X.append(X[-1]+1)
    # Y.append(Y[-1]+Y[-1]*random.uniform(-0.1,0.1))
    update_data()
    x_data = LUX_DATA.get('a_tsl_9').get('ts')
    y_data = LUX_DATA.get('a_tsl_9').get('lux')
    # data = plotly.graph_objs.Scatter(
    #     x=list(x_data),
    #     y=list(y_data),
    #     name='Scatter',
    #     mode='lines+markers'
    # )
    #
    # return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(x_data), max(x_data)]),
    #                                             yaxis=dict(range=[min(y_data), max(y_data)]), )}
    fig = make_subplots(rows=8, cols=1)
    # fig['layout']['margin'] = {
    #     'l': 30, 'r': 10, 'b': 30, 't': 10
    # }
    # fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
    labels = LUX_DATA.keys()
    sorted(labels)
    for i,label in enumerate(labels):
        data = LUX_DATA.get(label)
        fig.add_trace(go.Scatter(x=data.get('ts'),
                                 y=data.get('lux'),
                                 mode='lines',
                                 name=label),
                      row=i+1,
                      col=1)
    fig.update_layout(height=1000, width=2000, title_text="Stacked Subplots")
    # fig['layout']=go.Layout(xaxis=dict(range=[min(data.get('ts')),max(data.get('ts'))]),yaxis=dict(range=[min(data.get('lux')),max(data.get('lux'))]),)
    return fig


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True)

