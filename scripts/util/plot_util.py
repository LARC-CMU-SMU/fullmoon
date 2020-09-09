import plotly.graph_objects as go


def get_plot(data_dict, mode='lines+markers'):
    fig = go.Figure()
    x_dict=data_dict['x']
    y_dict=data_dict['y']
    for k, v in y_dict.items():
        fig.add_trace(go.Scatter(x=x_dict['data'],
                                 y=v,
                                 mode=mode,
                                 name=k))

    return fig


def get_plots(data_dict_list):
    fig = go.Figure()
    for data_dict in data_dict_list:
        x_dict = data_dict['x']
        y_dict = data_dict['y']
        for k, v in y_dict.items():
            fig.add_trace(go.Scatter(x=x_dict['data'],
                                     y=v,
                                     mode='lines+markers',
                                     name=k))

    return fig


def show_plot(plot):
    plot.show()


def write_plot(plot, file_name):
    plot.write_html(file_name)
