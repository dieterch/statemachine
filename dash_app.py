import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input, State

import pandas as pd; pd.options.mode.chained_assignment = None
import numpy as np
from datetime import datetime
import warnings; warnings.simplefilter(action='ignore', category=UserWarning)

from dmyplant2 import (
    cred, MyPlant, Engine, 
    FSMOperator, filterFSM, FSMPlot_Start, 
    bokeh_show, dbokeh_chart, add_dbokeh_vlines, get_cycle_data2, 
    disp_result, alarms_pareto, warnings_pareto, states_lines,
    detect_edge_right, detect_edge_left)

cred()
mp = MyPlant(3600)

mval = {'fleet': pd.DataFrame([])}

data = pd.read_csv("avocado.csv")
data["Date"] = pd.to_datetime(data["Date"], format="%Y-%m-%d")
data.sort_values("Date", inplace=True)

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "MyPlant Engine Start Analytics"

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1(
                    children="Engine Analytics", className="header-title"
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Installed Fleet Query", className="menu-title"),
                        dcc.Input(
                            id="query-input",
                            type='text',
                            placeholder="query ...",
                            value='Forsa Hartmoor',
                            debounce=True,
                            className="form-control"
                        )
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Engine", className="menu-title"),
                        dcc.Dropdown(
                            id="type-filter",
                            value=0,
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range", className="menu-title"
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=data.Date.min().date(),
                            max_date_allowed=data.Date.max().date(),
                            start_date=data.Date.min().date(),
                            end_date=data.Date.max().date(),
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Run FSM 1", 
                            className="menu-title"
                        ),
                        html.Button(
                            'Submit',
                            id="run-fsm1",
                            n_clicks=0
                        ),
                    ]                    
                )
            ],
            className="menu",
        ),
        # dcc.Loading(
        #     id = "loading-1",
        #     type = "default",
        #     children = html.Div(
        #             id="loading-output-1",
        #             className="wrapper"
        #         )
        # ),
        html.Div(
            children=[
                html.P(
                    id='selected-engine',
                ),
                dcc.Tabs(id="tabs-example-graph", value='tab-1-example-graph',
                    children= [
                        dcc.Tab(label='Tab One', value='tab-1-example-graph'),
                        dcc.Tab(label='Tab Two', value='tab-2-example-graph'),
                    ]
                ),
                html.Div(id='tabs-content-example-graph',
                         className="card",
                         ),
            ],
            className="wrapper",
        ),
    ]
)

@app.callback(
    Output("selected-engine", "children"),
    Input("run-fsm1", "n_clicks"),
    #State("query-input", 'value'),
    State("type-filter", 'value'))
def update_output(n_clicks, engine):
#def update_output(n_clicks, query, engine):
    global mval
    if not mval['fleet'].empty:
        return f"Selected Engine:   {mval['fleet']['Engine'].iloc[engine]:>50}"
    else:
        return ""

#modes = ['???','OFF','MANUAL','AUTO']
#success = [True,False]

@app.callback(
    [
        #Output("price-chart", "figure"),
        Output('tabs-content-example-graph', 'children'),    
        Output("type-filter", "options") ,
        Output("selected-engine", "children")
    ], #,Output("volume-chart", "figure")
    [
        Input("query-input", "value"),
        #Input("type-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("tabs-example-graph", 'value')
    ],
)
def update_charts(query, start_date, end_date, tab):
#def update_charts(query, engine, start_date, end_date, tab):

    global mval
    mask = (
        (data.region == "Albany")
        & (data.type == "organic")
        & (data.Date >= start_date)
        & (data.Date <= end_date)
    )
    filtered_data = data.loc[mask, :]
    price_chart_figure = {
        "data": [
            {
                "x": filtered_data["Date"],
                "y": filtered_data["AveragePrice"],
                "type": "lines",
                "hovertemplate": "$%{y:.2f}<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Average Price of Avocados",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True},
            "colorway": ["#17B897"],
        },
    }
    
    volume_chart_figure = {
        "data": [
            {
                "x": filtered_data["Date"],
                "y": filtered_data["Total Volume"],
                "type": "lines",
            },
        ],
        "layout": {
            "title": {"text": "Avocados Sold", "x": 0.05, "xanchor": "left"},
            "xaxis": {"fixedrange": True},
            "yaxis": {"fixedrange": True},
            "colorway": ["#E12D39"],
        },
    }

    fleet = mp.search_installed_fleet_by_contains_name(query)
    fleet['Engine'] = fleet.apply(lambda x: f"{x['serialNumber']} - {x['IB Site Name']} {x['Engine ID']}", axis=1)
    mval['fleet'] = fleet

    engineoptions = [
        {"label": engine, "value": i}
        for i, engine in enumerate(fleet['Engine'])
        #for avocado_type in data.type.unique()
    ]

    #motor = fleet.iloc[engine]
    #mval['motor'] = motor

    comment = f"{len(fleet)} Engines found." #, selected: {fleet['Engine'].iloc[engine]}"

    #e=Engine.from_fleet(mp,motor)
    #fsm = FSMOperator(e, p_from=e['Commissioning Date'], p_to=datetime.now(), successtime=300)

    if tab == 'tab-1-example-graph':
        tabret = dcc.Graph(
                    id="price-chart",
                    figure=price_chart_figure,
                    config={"displayModeBar": False},
                )
    elif tab =='tab-2-example-graph':
        tabret = dcc.Graph(
                    id="volume-chart",
                    figure=volume_chart_figure,
                    config={"displayModeBar": False},
                )

    return tabret, engineoptions, comment #, volume_chart_figure


if __name__ == "__main__":
    app.run_server(debug=True)
