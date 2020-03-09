#!/usr/bin/python3
import datetime
import sys

import dash
import dash_core_components as dcc
import dash_html_components as html
import networkx as nx
import plotly
import plotly.graph_objects as go
from dash.dependencies import Input, Output

from core import Api

try:
    api = Api(sys.argv[1])
except:
    print("Specify ip of one node.")
    print("python3 app.py http://127.0.0.1:3030")
    exit(1)

app = dash.Dash(__name__)
app.layout = html.Div(
    html.Div([
        html.H1('Near Network | Dashboard'),
        html.Div(id='general-info'),
        dcc.Graph(id='network-layout'),
        dcc.Graph(id='heatmap-info'),
        dcc.Graph(id='received-type'),
        dcc.Graph(id='received-peer'),
        dcc.Graph(id='summary'),
        dcc.Interval(
            id='interval-component',
            interval=5*1000,  # in milliseconds
            n_intervals=0
        )
    ])
)


@app.callback(Output('general-info', 'children'), [Input('interval-component', 'n_intervals')])
def update_general_info(n):
    style = {'padding': '5px', 'fontSize': '16px'}
    return [
        html.Span(f'Number of nodes: {api.num_nodes()}', style=style),
        html.Span(f'Diameter: {api.diameter()}', style=style),
    ]


@app.callback(Output('network-layout', 'figure'), [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    G = api.get_graph()

    # G = nx.random_geometric_graph(200, 0.125)

    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append('# of connections: '+str(len(adjacencies[1])))

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                    title='Network Layout',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    annotations=[dict(
                        text="",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002)],
                    xaxis=dict(showgrid=False, zeroline=False,
                               showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )

    return fig


@app.callback(Output('heatmap-info', 'figure'), [Input('interval-component', 'n_intervals')])
def update_graph_live(n):
    fig = plotly.subplots.make_subplots(
        rows=1, cols=3, subplot_titles=("Latency", "Bytes", "Total"))

    fig.add_heatmap(z=api.get_latency_heatmap(), row=1,
                    col=1, showscale=False, colorscale='MAGMA_r')
    fig.add_heatmap(z=api.get_transfer_bytes_heatmap(),
                    row=1, col=2, showscale=False, colorscale='MAGMA_r')
    fig.add_heatmap(z=api.get_transfer_count_heatmap() * 100,
                    row=1, col=3, showscale=False, colorscale='MAGMA_r')

    return fig


@app.callback(Output('received-type', 'figure'), [Input('interval-component', 'n_intervals')])
def update_received_type(n):
    fig = plotly.subplots.make_subplots(
        rows=1, cols=2, subplot_titles=["Bytes", "Total"], specs=[[{'type': 'domain'}, {'type': 'domain'}]])
    size, total, labels = api.get_received_type()
    fig.add_trace(go.Pie(labels=labels, values=size), 1, 1)
    fig.add_trace(go.Pie(labels=labels, values=total), 1, 2)
    return fig


@app.callback(Output('received-peer', 'figure'), [Input('interval-component', 'n_intervals')])
def update_received_peer(n):
    fig = plotly.subplots.make_subplots(
        rows=1, cols=2, subplot_titles=["Bytes", "Total"], specs=[[{'type': 'domain'}, {'type': 'domain'}]])
    size, total, labels = api.get_received_peer()
    fig.add_trace(go.Pie(labels=labels, values=size), 1, 1)
    fig.add_trace(go.Pie(labels=labels, values=total), 1, 2)
    return fig


@app.callback(Output('summary', 'figure'), [Input('interval-component', 'n_intervals')])
def update_received_peer(n):
    header, values = api.summary()
    fig = go.Figure(data=[go.Table(header=dict(values=header),
                                   cells=dict(values=values))
                          ])
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
