#import things
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_table
import plotly.graph_objs as go
import pandas_datareader.data as web
import pandas as pd
import numpy as np
import base64
import fred
from fredapi import Fred
import fred as fred2
from datetime import datetime, date, time
from collections import OrderedDict
import io
import flask
import json
import os
import sys
from itertools import product
import ast
import urllib
import urllib.parse
from urllib.parse import quote, urlparse, parse_qsl, urlencode
from base64 import urlsafe_b64decode, urlsafe_b64encode
import statsmodels.api as sm
import statsmodels.formula.api as smf
from functools import partial
import re
import dash_daq as daq
from pyshorteners import Shortener
import patsy
from Dash.SocialMedia import SocialMedia
from scipy.optimize import curve_fit
import random

import plotly.io as pio

fred = Fred(api_key='51162ee18f52f0caa348af89a09c0af4')
fred2.key('51162ee18f52f0caa348af89a09c0af4')


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

url_base = '/dash/app/'
#Set an upload directory where uploaded files are stored
UPLOAD_DIRECTORY = "/Users/isaac/Desktop/Flask Blog w FRED Dash 1 Jul/flaskblog/static/dash_data"
UPLOAD_DIRECTORY_POST = "/Users/isaac/Desktop/Flask Blog w FRED Dash 1 Jul/flaskblog/static/post_images"

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

units_options = {'No Transformation': 'lin',
                 'Change': 'chg',
                 'Change from Year Ago': 'ch1',
                 '% Change': 'pch',
                 '% Change from Year Ago': 'pc1',
                 'Compounded Annual Rate of Change': 'pca',
                 'Continuously Compounded Rate of Change': 'cch',
                 'Continuously Compounded Annnual Rate of Change': 'cca',
                 'Natural Log': 'log'}

def id_to_title(id):
    info = fred.get_series_info(id)
    title = info['title']
    return title

def parse_contents(contents):
    content_string = contents.split(',')[1]

    decoded = base64.b64decode(content_string)
    try:
        return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    except Exception:
        return html.Div([
            'There was an error processing this file.'
        ])

def parse_state(url):
    parse_result = urlparse(url)
    query_string = parse_qsl(parse_result.query)
    if query_string:
        encoded_state = query_string[0][1]
        state = dict(json.loads(urlsafe_b64decode(encoded_state)))
    else:
        state = dict()
    return state

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-layout')
])


def apply_default_value(params):
    def wrapper(func):
        def apply_value(*args, **kwargs):
            if 'id' in kwargs and kwargs['id'] in params:
                kwargs[params[kwargs['id']][0]] = params[kwargs['id']][1]
                #kwargs['value'] = params[kwargs['id']][1]
            return func(*args, **kwargs)
        return apply_value
    return wrapper


def build_layout(params):
    layout = [
        dcc.Store(id = 'upload-csv-store'),
        dcc.Store(id = 'df-store'),
        dcc.Store(id = 'store-line-format'),
        dcc.Store(id = 'regression-store'),
        dcc.Store(id = 'regression-table-store'),
        dcc.Store(id = 'annotation-store'),
        html.Div(
            [
                html.Div(
                    [
                        html.H1("Economic Data")
                    ], 
                    style = dict(
                        width = '30%',
                        display = 'table-cell',
                        verticalAlign = "middle"
                    ),
                ),
                html.Div(
                    [   html.A(html.Button('Back to Blog', id='postButton'),href='http://127.0.0.1:5000/'),
                        dcc.Upload(
                            id='upload-local-data',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select CSVs')
                            ]),
                            style={
                                'width': '95%',
                                'height': '60px',
                                'lineHeight': '60px',
                                'borderWidth': '1px',
                                'borderStyle': 'dashed',
                                'borderRadius': '5px',
                                'textAlign': 'center',
                                'margin': '10px'
                            },
                        )
                    ],
                    style = dict(
                        width = '30%',
                        display = 'table-cell',
                        verticalAlign = "middle"
                    ),
                ),
                html.Div(
                    [
                        html.Div([html.Button('Generate Tiny URL', id='tinyurl-button', style = {'width': '100%'})]),
                        html.Div([dcc.Input(id='tiny_url', style = {'width': '100%', 'height': '10%'})])                       
                    ],
                    style = dict(
                        width = '0.01%',
                        display = 'table-cell',
                        verticalAlign = "middle"
                    ),                   
                )
            ],
            style = dict(
                height = '2px',
                width = '100%',
                display = 'table',
                verticalAlign = "middle"
            ),
        ),
        html.Div(
            [
                html.Div(
                    [   
                        html.Div(
                            [
                                dcc.Input(id = 'input', type='text', value='', placeholder = 'Search FRED...', style = dict(height = '36px'))
                            ],
                            style = dict(
                                height = '2px', 
                                width = '10%',
                                display = 'table-cell',
                                verticalAlign = "middle"
                            ),
                        ),    
                        html.Div(
                            [
                                dcc.Dropdown(id = 'dropdown', style = dict(height = '35px'))
                            ],
                            style = dict(
                                height = '2px',
                                width = '90%',
                                display = 'table-cell',
                                verticalAlign = "middle"
                            ),
                        )
                    ],
                    style = dict(
                        height = '2px',
                        width = '100%',
                        display = 'table',
                        verticalAlign = "middle"
                    ),
                ),
                apply_default_value(params)(dash_table.DataTable)(
                    id='table-dropdown',
                    columns=[
                        {'id': 'Variable ID', 'name': 'Variable ID'},
                        {'id': 'Variable', 'name': 'Variable'},
                        {'id': 'Units', 'name': 'Units', 'presentation': 'dropdown'},
                        {'id': 'Frequency', 'name': 'Frequency', 'presentation': 'dropdown'},
                        {'id': 'Y-axis Position', 'name': 'Y-axis Position', 'presentation': 'dropdown'}
                    ],
                    data = [],
                    column_static_dropdown=[
                        {
                            'id': 'Units',
                            'dropdown': [
                                {'label': key, 'value': value}
                                for key, value in units_options.items()
                            ]
                        },
                        {
                            'id': 'Frequency',
                            'dropdown': [
                                {'label': 'Annual', 'value': 'a'},
                                {'label': 'Semiannual', 'value': 'sa'},
                                {'label': 'Quarterly', 'value': 'q'},
                                {'label': 'Monthly', 'value': 'm'},
                                {'label': 'Biweekly', 'value': 'bw'},
                                {'label': 'Weekly', 'value': 'w'},
                                {'label': 'Daily', 'value': 'd'}]

                        },                        
                        { 'id': 'Y-axis Position',
                         'dropdown': [
                                 {'label': 'Left', 'value': 'Left'},
                                 {'label': 'Right', 'value': 'Right'}]
                                }
                    ],
                    editable=True,
                    sorting=True,
                    sorting_type='multi',
                    row_selectable='multi',
                    row_deletable=True,
                    selected_rows=[],                    
                ),
                apply_default_value(params)(dash_table.DataTable)(
                    id='regression-table',
                    columns=[
                        {'id': 'Name', 'name': 'Customized Variable'},
                        {'id': 'Formula', 'name': 'Formula'},
                        {'id': 'Model', 'name': 'Model'},
                        {'id': 'Y-axis Position_reg', 'name': 'Y-axis Position', 'presentation': 'dropdown'}
                    ],
                    data = [],
                    column_static_dropdown=[                        
                        { 'id': 'Y-axis Position_reg',
                         'dropdown': [
                                 {'label': 'Left', 'value': 'Left'},
                                 {'label': 'Right', 'value': 'Right'}]
                                }
                    ],
                    editable=True,
                    sorting=True,
                    sorting_type='multi',
                    row_selectable='multi',
                    row_deletable=True,
                    selected_rows=[],                    
                ),
                html.Div(    
                    [
                        html.Div(
                            [
                                apply_default_value(params)(dcc.DatePickerRange)(
                                    id='datepicker',
                                    start_date= datetime(1947, 1, 1),
                                    end_date= datetime(2019, 1, 1)
                                )
                            ],
                            style = dict(
                                height = '2px',
                                width = '30%',
                                display = 'table-cell',
                                verticalAlign = "middle"
                            ),
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(['Formatting'], style=dict(display = 'inline-block', verticalAlign = "middle")),
                                        daq.BooleanSwitch(
                                            id='toggle',
                                            on=False,
                                            style = {'display':'inline-block', 'padding': '20px', 'verticalAlign': 'middle'}
                                        )
                                    ]
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(['Format Graph:'], style={'width':'100px', 'display' : 'inline-block', 'verticalAlign':"middle", 'padding-right':'5px'}),
                                                dcc.Dropdown(
                                                    id='graph-type',
                                                    options=[
                                                        {'label': 'Line', 'value':'lines'},
                                                        {'label': 'Area', 'value':'tonexty'},
                                                        ],
                                                    value='lines',
                                                    style ={'width':'100px', 'display':'inline-block', 'verticalAlign': 'middle'}
                                                ),
                                                dcc.Input(id='width', type='number', placeholder='width', min=100, step=100, style = {'width':'100px','display':'inline-block', 'verticalAlign': 'middle'}),
                                                dcc.Input(id='height', type='number', placeholder='height', min=100, step=100, style ={'width':'100px', 'display':'inline-block', 'verticalAlign': 'middle'}),
                                                
                                            ]
                                        ),

                                        #line formatting

                                        html.Div(
                                            [
                                                html.Div(['Format Line:'], style={'width':'100px', 'display':'inline-block','verticalAlign':'middle', 'padding-right':'5px'}),
                                                dcc.Dropdown(
                                                    id='select-line-dropdown',
                                                    options = [],
                                                    placeholder = 'Select Line',
                                                    style = {'width':'100px', 'display':'inline-block','verticalAlign':'middle'}),
                                                dcc.Dropdown(
                                                    id='line-style',
                                                    options=[
                                                        {'label': 'Solid', 'value': 'lines'},
                                                        {'label': 'Line+Marker', 'value': 'lines+markers'},
                                                        {'label': 'Dot', 'value': 'dot'},
                                                        {'label': 'Dash', 'value': 'dash'},
                                                        {'label': 'Dashdot', 'value': 'dashdot'},
                                                    ],
                                                    value='lines',
                                                    style= {'width': '100px', 'display':'inline-block','verticalAlign':'middle'}
                                                ),
                                                dcc.Dropdown(
                                                    id='line-width',
                                                    options = [
                                                        {'label':'1', 'value': 1},
                                                        {'label':'2', 'value': 2},
                                                        {'label':'3', 'value': 3},
                                                        {'label':'4', 'value': 4},
                                                        {'label':'5', 'value': 5}
                                                        ],
                                                    value=2,
                                                    style = {'width': '100px', 'display':'inline-block','verticalAlign':'middle'}
                                                ),
                                                dcc.Dropdown(
                                                    id = 'line-color',
                                                    options = [
                                                        {'label':'red', 'value': ('rgb(255, 85, 94)')},
                                                        {'label':'orange', 'value': ('rgb(255, 134, 80)')},
                                                        {'label':'yellow', 'value': ('rgb(255, 233, 129)')},
                                                        {'label':'green', 'value': ('rgb(139, 241, 139)')},
                                                        {'label':'blue', 'value': ('rgb(131, 178, 255)')},
                                                        {'label':'purple', 'value': ('rgb(155, 110, 243)')}
                                                       
                                                    ],
                                                    placeholder = 'Select Color',
                                                    style = {'width': '105px', 'display':'inline-block','verticalAlign':'middle'}
                                                )
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Div(['Annotations:'],style={'width':'100px', 'display' : 'inline-block', 'verticalAlign':"middle", 'padding-right':'5px'}),
                                                dcc.Input(id='text-input', type='text', placeholder="Click points from graph", value='',style = {'width':'255px','display':'inline-block', 'verticalAlign': 'middle'}),
                                                html.Button(id='add-button', children="Add", style = {'verticalAlign': 'middle'}),
                                                html.Button(id='remove-button', children="Remove", style = {'verticalAlign': 'middle'}), ], className="row"),
                                        html.Div(
                                            [
                                                html.Div(['Recession:'], style=dict(display = 'inline-block', verticalAlign= 'middle')),
                                                daq.BooleanSwitch(
                                                    id='toggle2',
                                                    on=False,
                                                    style = {'display':'inline-block', 'padding': '20px', 'verticalAlign': 'middle'})]),
                                    ], 
                                    id='controls-container', style={'display':'none'}
                                ),
                            ], 
                            style = dict(
                                height = '2px', 
                                width = '50%',
                                display = 'table-cell',
                                verticalAlign = "middle",
                            ),                            
                        ),
                        html.Div(
                            [
                                html.A(
                                    "Download",
                                    id="download-link",
                                    download="data.csv",
                                    href="#",
                                    className="btn btn-primary btn-block",
                                    target="_blank",
                                    style = dict(height = '36px')
                                )
                            ],
                            style = dict(
                                height = '2px', 
                                width = '0.01%',
                                display = 'table-cell',
                                verticalAlign = "middle",
                            ),
                        ),
                    ],
                    style = dict(
                        height = '2px',
                        width = '100%',
                        display = 'table',
                        verticalAlign = "middle"
                    ),
                ),
            ],
        ),
        dcc.Graph(id = 'graph'),                
        html.Div(
            [
                apply_default_value(params)(dcc.Textarea)(
                    id = 'regressionBox',
                    placeholder='Enter a value...',
                    value='',
                    style={'width': '100%'}
                ),
                html.Button('Run', id='runButton'),
                html.Button('Clear', id='clearButton'),
            ],
            className = 'row',
            style={'width': '90%','padding-left':'5%', 'padding-right':'5%'}             
        ),    
        html.Div(
            [
                html.Br(id = 'regression_output0_Br', style = {'display':'none'}),
                html.Div(id = 'regression_output0a'),
                html.Div(id = 'regression_output0b'),
                html.Br(id = 'regression_output1_Br', style = {'display':'none'}),
                html.Div(id = 'regression_output1a'),
                html.Div(id = 'regression_output1b'),
                html.Br(id = 'regression_output2_Br', style = {'display':'none'}),
                html.Div(id = 'regression_output2a'),
                html.Div(id = 'regression_output2b')
            ],
            className = 'row',
            style={'width': '90%','padding-left':'5%', 'padding-right':'5%'}             
        ),
        html.Br(),
        #Markdown text area
        html.Div(
            [
                apply_default_value(params)(dcc.Textarea)(
                    id = 'markdownBox',
                    placeholder='Enter your story...',
                    value='',
                    style={'width': '100%'}
                )
            ],
            className = 'row',
            style={'width': '90%','padding-left':'5%', 'padding-right':'5%'}
            ),
        html.Div(
            [
                dcc.Textarea(
                    id = 'outputBox',
                    placeholder='Output...',
                    value='',
                    style={'width': '100%'}
                ),
                html.Div(
                        html.A(html.Button('Post', id='postButton'),href='http://127.0.0.1:5000/post/post_from_dash', target="_blank"),
                        html.Div([html.Button('Clear', id='clearButton2', n_clicks=0)], style=dict(height = '2px', width = '30%', display = 'table-cell', verticalAlign = "middle")),
                        html.Div(
                            [
                                html.A([html.Img(src=app.get_asset_url('facebook.jpg'), style=dict(height = '50px',width = '50px', verticalAlign = "middle"))], id = 'facebook', target="_blank"),
                            ], id='social-media-icons', style=dict(height = '2px', width = '0.01%', display = 'table-cell', verticalAlign = "middle")
                        ),
                        html.Div(
                            [
                                html.A([html.Img(src=app.get_asset_url('twitter.jpg'), style=dict(height = '50px',width = '50px', verticalAlign = "middle"))], id = 'twitter', target="_blank"),
                            ], id='social-media-icons', style=dict(height = '2px', width = '0.01%', display = 'table-cell', verticalAlign = "middle")
                        ),
                    style = dict(
                        height = '2px',
                        width = '100%',
                        display = 'table',
                        verticalAlign = "middle"
                    ),
                ),
            ],
            className = 'row',
            style={'width': '90%','padding-left':'5%', 'padding-right':'5%'}
        ),
        html.Br(),
        html.Div(id = 'meta0', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta1', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta2', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta3', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta4', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta5', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta6', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta7', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta8', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta9', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta10', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta11', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta12', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta13', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta14', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta15', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta16', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta17', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta18', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta19', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta20', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta21', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta22', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta23', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta24', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta25', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta26', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta27', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta28', style = dict(display='none', padding = 10)),
        html.Div(id = 'meta29', style = dict(display='none', padding = 10)),
        html.Div(id="hidden-div1", style={"display": "none"}),
        html.Div(id="hidden-div2", style={"display": "none"})
    ]

    return layout

sm = SocialMedia()
def socialmediaurls(url, socialmediasite):
    socialmediaurls = sm.GetSocialMediaSiteLinks_WithShareLinks({
        'url': url,
        'title': 'Dash App for FRED Data',
    })
    url_desired = socialmediaurls[socialmediasite]
    return url_desired



def register_callbacks(app):

    @app.callback(Output('page-layout', 'children'),
                    inputs=[Input('url', 'href')])
    def page_load(href):
        if not href:
            return []
        state = parse_state(href)
        return build_layout(state)

    #Returns Facebook link to the Dash app
    @app.callback(Output('facebook', 'href'),
                [Input('url', 'search')])
    def facebook_link(state):
        if not state:
            pass
        if state:
            # shortener = Shortener('Tinyurl')
            # shorter_url = shortener.short('http://127.0.0.1:8050' + state)
            state = 'http://127.0.0.1:8050' + state
            return '{}'.format(socialmediaurls(state, 'facebook'))

    #Returns Twitter link to the Dash app
    @app.callback(Output('twitter', 'href'),
                [Input('url', 'search')])
    def twitter_link(state):
        if not state:
            pass
        if state:
            shortener = Shortener('Tinyurl')
            shorter_url = shortener.short('http://127.0.0.1:8050' + state)
            return '{}'.format(socialmediaurls(shorter_url, 'twitter'))

    

    component_ids = {'datepicker': 'start_date',
                    'datepicker': 'end_date',
                    'table-dropdown': 'data',
                    'regression-table': 'data',
                    'regressionBox': 'value',
                    'markdownBox': 'value'
                    }

    #Encode saved presets into a URL
    @app.callback(Output('url', 'search'),
                inputs=[Input(id, param) for id, param in component_ids.items()])
    def update_url_state(*values):
        state = dict(zip(list(component_ids.keys()), list(zip(component_ids.values(), values))))
        encoded = urlsafe_b64encode(json.dumps(state).encode())
        params = urlencode(dict(params=encoded))
        return f'?{params}'

    #Return tinyurl whenever tinyurl button is clicked
    @app.callback(Output('tiny_url', 'value'),
                [Input('tinyurl-button', 'n_clicks')],
                [State('url', 'search')])
    def generate_tiny_url(n_clicks, state):
        if not state:
            return "No url to shorten"
        if n_clicks > 0 and state:
            shortener = Shortener('Tinyurl')
            return shortener.short('http://127.0.0.1:8050' + state)

    #click data on annotations
    @app.callback(
        Output('text-input','placeholder'),
        [Input('graph', 'clickData'),
        Input('df-store', 'data')])

    def display_click_data(clickData,data):
        df = pd.read_json(data)
        json_str=json.dumps(clickData)
        resp = json.loads(json_str)
        linenumber = int(resp['points'][0]['curveNumber'])
        return (resp['points'][0]['x'] + ' ' + df.columns.values[linenumber])

    #select each line formatting
    @app.callback(
        Output('select-line-dropdown','options'),
        [Input('table-dropdown','data'),
        Input('table-dropdown','selected_rows'),
        Input('regression-table', 'data'),
        Input('regression-table', 'selected_rows')])
    def format_line(rows_df, selected_rows_index_df, rows_regression, selected_rows_index_regression):
        data_df = []
        for row in rows_df:
            data_df.append(row['Variable ID'])

        data_df = [data_df[index] for index in selected_rows_index_df]

        data_regression = []
        for row in rows_regression:
            data_regression.append(row['Name'])

        data_regression = [data_regression[index] for index in selected_rows_index_regression]
        data = data_df + data_regression

        return [{'label': i, 'value': i} for i in data]

    format_dict = {}
    #store line format
    @app.callback(
        Output('store-line-format', 'data'),
        [Input('select-line-dropdown','value'),
        Input('line-style', 'value'),
        Input('line-width', 'value'),
        Input('line-color','value')
        ])
    def line_format(selected_line, line_style, line_width, line_color):

        if line_style == 'lines' or line_style == 'lines+markers':  # line
            line_variable = line_style
            dash_variable = 'solid'
        else:  # line_style == 'dash' or 'dot' or 'dashdot':
            line_variable = 'lines'
            dash_variable = line_style

        if selected_line is not None:
            format_dict[selected_line] = [line_variable, dash_variable, line_width, line_color]

            return format_dict
        else:
            raise PreventUpdate



    #formatting toggle
    @app.callback(Output('controls-container','style'),
                [Input('toggle','on')])
    def toggle_container(toggle_value):
        if toggle_value == False:
            return {'display': 'none'}
        else:
            return {'display': 'block'}


    @app.callback(
            Output('markdownBox', 'value'),
            [Input('clearButton2', 'n_clicks'),
            Input('graph', 'clickData')],
            [State('markdownBox', 'value'),
            State('df-store', 'data'),
            State('regression-store', 'data'),
            State('table-dropdown', 'data')])
    def update_markdown_values(n_clicks2, clickdata, 
                            string, data, data_reg, rows):
        
        if string is None:
            string = ''
        
        #Getting df-store data
        df = pd.read_json(data)
        df.index = pd.to_datetime(df.index, unit = 'ms')
        df = df.sort_index()
        
        ctx = dash.callback_context    
        button_pressed = ctx.triggered[0]['prop_id']
            
        #Case 2: Clear button pressed    
        if button_pressed == 'clearButton2.n_clicks': 
            return ''
            
        #Case 3: Click on graph   
        elif button_pressed == 'graph.clickData':
            #Linenumber is the column where the data is gotten from
            linenumber = int(clickdata['points'][0]['curveNumber'])
            
            #Finding out if the line is a prediction
            if len(df.columns) <= linenumber:
                linenumber = linenumber - len(df.columns)
                
                #Getting regression store data
                df_reg = pd.read_json(data_reg)
                df_reg.index = pd.to_datetime(df_reg.index, unit = 'ms')
                df_reg = df_reg.sort_index()
                
                out = clickdata['points'][0]['x'] + ' ' + clickdata['points'][0]['text']         
        
            #If not a prediction - normal data value
            else:
                #Get units from the dropdown-data
                units = [row['Units'] for row in rows if row['Variable ID'] == df.columns.values[linenumber]][0]
                    
                out = clickdata['points'][0]['x'] +' '+ clickdata['points'][0]['text'] + ' ' + units
            
            return (string + '{{' + out + '}}')

    @app.callback(
            Output('outputBox', 'value'),
            [Input('markdownBox', 'value'),
            Input('df-store', 'data'),
            Input('regression-store', 'data')])
    def update_output_values(string, data, data_reg):
        
        #Find all matches with {{ }} format
        matches = re.findall('(\{{.*?\}})', string, flags = 0)
        #Strip {{ }} from each match 
        matches2 = [e[2:-2] for e in matches]
        #Get the units value if not empty - by default it will follow the lin
        def get_units(e):
            units = 'lin'
            if len(e.split(' ')) == 3:
                units = e.split(' ')[2]
            return units
            
        #Split into series and value
        matches3 = [(e.split(' ')[0], e.split(' ')[1], get_units(e)) for e in matches2]
        #Find values from DF
        values = []
        for date, series, units in matches3:
            try:
                value = [str(fred.get_series(series, date, date, units = units)[0])]
            except ValueError:
                try:
                    df_reg = pd.read_json(data_reg)
                    df_reg.index = pd.to_datetime(df_reg.index, unit = 'ms')
                    df_reg = df_reg.sort_index()        
                    value = [str(df_reg.loc[date, '{}'.format(series)])]
                except KeyError:
                    df = pd.read_json(data)
                    df.index = pd.to_datetime(df.index, unit = 'ms')
                    for index in df.index:
                        index = index.date()
                    df = df.sort_index()
                    value = [str(df.loc[date, '{}'.format(series)])]
            values = values + value
        #Create tuple of matches and replacements
        match_replacement = [e for e in zip(matches, values)]
        #Make replacements to string
        out = string
        for match, value in match_replacement:
            out = out.replace(match, value)
            
        return out


    #Adds regressions to the regression table
    #Checks for legality of the regression formula - prevents repeats and variables not in datatable
    @app.callback(Output('regression-table', 'data'),
                [Input('runButton', 'n_clicks'),
                Input('table-dropdown', 'data')],
                [State('regression-table', 'data'),
                State('regressionBox', 'value'),
                State('df-store','data')])

    def update_regression_table(n_clicks, rows, regression_table_data, value, df_store):
        
        ctx = dash.callback_context
        button_pressed = ctx.triggered[0]['prop_id']
        
        if button_pressed == 'runButton.n_clicks': 
            #Read regressionBox value and put it in regression_table_data
            value_inputs = []
            regression_table_data_filtered = []
            if value.count('"') > 2:
                #Only works for more than one string
                value_inputs = ast.literal_eval(value)
            elif value.count('"') == 2:
                value_inputs = [value[1: -1]]
            #Detect regression formula for each string and add to line
            formulas = [e for e in value_inputs if '~' in e]
            
            #Split the regression formula into target and explanatory variables
            for formula_all in formulas:
                start = formula_all.find('(') + 1
                end = formula_all.find(')', start)
                formula = formula_all[start:end]

                if '=' not in formula:
                    predicted_value_name = 'reg{}'.format("%04d" % random.randint(1111,9999))
                if '=' in formula:
                    user_choosed_name = formula.split('=')[0]
                    formula = formula.split('=')[1]
                    predicted_value_name = '{}'.format(user_choosed_name) 

                model = formula_all.split('(')[0]
                x_vars_temp = formula.split('~')[1].split('+')
                #x_vars to be stored in the datatable behind the scenes
                x_vars = [e.strip() for e in x_vars_temp]
                y_var = formula.split('~')[0].strip()
                
                #Check if regression formula_ols (tuple of y_vars and x_vars) is repeated
                try:
                    formulas_in_reg_table = [(e['Formula'], e['Model']) for e in regression_table_data]

                    #Only if all the regression variables are in the datatable, AND the regression formula_ols
                    #is not repeated, will the function allow the regression to be added to regression table
                    if (formula, model) not in formulas_in_reg_table:
                        regression_table_data.append({'Name': predicted_value_name, 
                                                    'Formula': formula,
                                                    'Model': model,
                                                    'Target': y_var, 'Explanatory': ', '.join(x_vars), 
                                                    'x_vars': x_vars,
                                                    'Y-axis Position_reg': 'Left'})

                except TypeError:
                    # keys = ['Name', 'Formula', 'Target', 'Explanatory', 'x_vars']
                    # values = [predicted_value_name, formula, y_var, ', '.join(x_vars), x_vars]
                    # regression_table_data = [{k: v} for k, v in zip(keys, values)]
                    # regression_table_data = [e for e in dict(zip(keys, values))]
                    predicted_value_name = [predicted_value_name]
                    formula = [formula]
                    regression_table_data = [{'Name': '{}'.format(predicted_value_name), 
                                            'Formula': '{}'.format(formula),
                                            'Model': model,
                                            'Target': '{}'.format(y_var), 'Explanatory': ', '.join(x_vars), 
                                            'x_vars': '{}'.format(x_vars)} for predicted_value_name, formula, model, y_var, x_vars in zip(predicted_value_name, formula, model, y_var, x_vars)]
            
            for regression in regression_table_data:
                df_datatable_vars = [e['Variable ID'] for e in rows]
                regression_datatable_vars = [e['Name'] for e in regression_table_data]
                datatable_vars = df_datatable_vars + regression_datatable_vars
                try:
                    all_vars = regression['x_vars'] + [regression['Target']]
                except TypeError:
                    all_vars = [regression['x_vars']] + [regression['Target']]
                reg_vars_in_datatable = [e for e in all_vars if e in datatable_vars]
                if len(reg_vars_in_datatable) == len(all_vars):
                    regression_table_data_filtered.append(regression)

    
            formulas_add = [e for e in value_inputs if 'add' in e]

            for add_formula in formulas_add:
                start = add_formula.find('add(') + 4
                end = add_formula.find(')', start)
                add_formula = add_formula[start:end]
                
                if '=' not in add_formula:
                    add_value_name = 'var{}'.format("%04d" % random.randint(1111,9999))
                elif '=' in add_formula:
                    user_choosed_name = add_formula.split('=')[0]
                    add_formula = add_formula.split('=')[1]
                    add_value_name = '{}'.format(user_choosed_name)

                    # Check if regression formula (tuple of y_vars and x_vars) is repeated
                try:
                    formulas_in_reg_table = [(e['Formula']) for e in regression_table_data]

                    # Only if all the regression variables are in the datatable, AND the regression formula
                    # is not repeated, will the function allow the regression to be added to regression table
                    if add_formula not in formulas_in_reg_table:
                        regression_table_data.append({'Name': '{}'.format(add_value_name),
                                                    'Formula': '{}'.format(add_formula),
                                                    'Model': 'NA',
                                                    'Target': None, 'Explanatory': None,
                                                    'x_vars': None,
                                                    'Y-axis Position_reg': 'Left'})
                except TypeError:
                    add_value_name = [add_value_name]
                    add_formula = [add_formula]
                    regression_table_data = [{'Name': '{}'.format(add_value_name),
                                            'Formula': '{}'.format(add_formula),
                                            'Model': 'NA',
                                            'Target': None, 'Explanatory': None,
                                            'x_vars': None} for
                                            add_value_name, add_formula in
                                            zip(add_value_name, add_formula)]

            #For all regressions in regression table, Check if all variables are in the datatable 
            #(and hence in the df), and remove variable if it does not fulfil the rule

            for regression in regression_table_data:
                if regression['x_vars'] == None:
                    try:
                        df = pd.read_json(df_store)
                        df.index = pd.to_datetime(df.index, unit = 'ms')
                        df = df.sort_index()
                        df.eval('C={}'.format(regression['Formula']))
                        regression_table_data_filtered.append(regression)
                    except pd.core.computation.ops.UndefinedVariableError:
                        pass

        return regression_table_data_filtered


    #Input: regression model fit object
    #Output: dictionary of metrics and their values
    def regression_metrics(res):
        summary = res.summary()

        dfs = {}        
        for item in summary.tables[0].data:
            dfs[item[0].strip()] = item[1].strip()
            dfs[item[2].strip()] = item[3].strip()
                
        dfs = dict((key[:-1], value) for key, value in dfs.items())
            
        reg_metrics = dict((key, value) for key, value in dfs.items() if key in ['Dep. Variable', 
                    'No. Observations', 'Model', 'R-squared', 'Adj. R-squared', 'F-statistic',
                    'Prob (F-statistic)', 'Log-Likelihood', 'AIC', 'BIC'])
                        
        return reg_metrics

    #Input: regression model fit object
    #Output: dictionary of coefficients and their p-values
    def regression_coefs(res):
        summary = res.summary()
        
        res_html = summary.tables[1].as_html()
        reg_coefs = pd.read_html(res_html, header=0, index_col=0)[0].reset_index()
        
        return reg_coefs.to_dict()


    @app.callback([Output('regression-store', 'data'),
                Output('regression-table-store', 'data')],
                [Input('regression-table', 'data'),
                Input('regression-table', 'selected_rows'),
                Input('df-store', 'data')],
                [State('regression-store', 'data')])

    def run_regression(reg_table_data, reg_table_selected_rows, df_store_data, regression_store_data):
        
        #Parse data from df-store (JSON -> dataframe)
        df = pd.read_json(df_store_data)
        df.index = pd.to_datetime(df.index, unit = 'ms')
        df = df.sort_index()

        try:
            df_regression = pd.read_json(regression_store_data)
            df_regression.index = pd.to_datetime(df_regression.index, unit = 'ms')
            df_regression = df_regression.sort_index()
            df.index.name = 'index'
            df_regression.index.name = 'index'
            df = pd.merge(df, df_regression, on = 'index', how = 'outer').sort_index()
        except ValueError:
            pass
        
        #Takes in one formula (row in regression-table), and df_store data
        def run_regression_inner(row, data):
            #Run regression
            if row['Model'] == 'ols':
                model = smf.ols(formula = row['Formula'], data = data)
            if row['Model'] == 'glm':
                model = smf.glm(formula = row['Formula'], data = data)
            res = model.fit()
            #Index explanatory variables from dataframe
            x_vars = row['x_vars']
            X = data[x_vars]
            #Get fitted values
            prediction = res.predict(X).rename(row['Name'])
            
            #Get regression metrics (dict) and coefs (df)
            reg_metrics = regression_metrics(res)
            reg_coefs = regression_coefs(res)
            
            return prediction, reg_metrics, reg_coefs
        
        #Output is 
        #prediction: fitted values (in a pandas series)
        #reg_metrics: dictionary
        #reg_coefs: dictionary

        #regression results = metrics + coefs
        reg_df = pd.DataFrame()
        reg_results = []
        reg_table_data_selected = [reg_table_data[index] for index in reg_table_selected_rows]
        #For every regression formula in the regression table, run the regression formula, and add
        #fitted values to reg_df and regression results to reg_results
        for row in reg_table_data:
            try:
                fitted_values, reg_metrics, reg_coefs = run_regression_inner(row, df)
                fitted_values = fitted_values.reset_index()
                fitted_values.columns = ['index', row['Name']]
                reg_df = reg_df.reset_index()
                reg_df = pd.merge(reg_df, fitted_values, on = 'index', how = 'outer').set_index('index').sort_index()
            except UnboundLocalError:
                df = df.eval('{}={}'.format(row['Name'], row['Formula']))
                trans_var = df['{}'.format(row['Name'])]
                trans_var.columns = ['index', row['Name']]
                reg_df = reg_df.reset_index()
                reg_df = pd.merge(reg_df, trans_var, on = 'index', how = 'outer').set_index('index').sort_index()
                
        for row in reg_table_data_selected:
            try:
                fitted_values, reg_metrics, reg_coefs = run_regression_inner(row, df)
                reg_results.append({'Name': row['Name'], 'Metrics': reg_metrics, 'Coefs': reg_coefs})
            except patsy.PatsyError:
                pass
        
        return reg_df.to_json(), json.dumps(reg_results)

    #Show the regression output tables (multiple if necessary)

    def draw_regression_table(data, i):
        
        reg_results = json.loads(data)

        #List of dicts containing the metrics and coefs for each result
        reg_metrics = [e['Metrics'] for e in reg_results]
        reg_coefs = [e['Coefs'] for e in reg_results]
        
        try:
            #Get the metrics (as dict) and coefs (as df) as a df for 1st result
            reg_metrics_i = reg_metrics[i]
            reg_coefs_i = pd.DataFrame(reg_coefs[i])
        
            #For metrics datatable
            reg_metrics_table = dash_table.DataTable(id = 'regression_table1',
                                                    columns = [{'name': key, 'id': key} for key in reg_metrics_i.keys()],
                                                    data = [reg_metrics_i])
            #For coefs datatable
            reg_coefs_table = dash_table.DataTable(id = 'regression_table2',
                                                columns = [{'name': i, 'id': i} for i in reg_coefs_i.columns],
                                                data = reg_coefs_i.to_dict('records'))
            
            #{} for regression_output0_Br is to display the datatable (i.e. replace display=None with nothing)
            return reg_metrics_table, reg_coefs_table, {}, {}, {}
        
        #If there aren't 2/3 regressions - then don't show any results
        except IndexError:
            return [], [], {'display': 'none'}, {'display': 'none'}, {'display': 'none'}

    for i in range(0,3):
        app.callback([Output("regression_output{}a".format(i), "children"),
                    Output('regression_output{}b'.format(i), 'children'),
                    Output("regression_output{}a".format(i), "style"),
                    Output("regression_output{}b".format(i), "style"),
                    Output("regression_output{}_Br".format(i), "style")],
                    [Input('regression-table-store', 'data')])(partial(draw_regression_table, i=i))


    #If user uploads local data, 
    @app.callback(
            Output('upload-csv-store', 'data'),
            [Input('upload-local-data', 'contents')])

    def store_uploaded_local_data(settings_to_load):
        if settings_to_load != None:
            df = parse_contents(settings_to_load)
            return df.to_json()
            

    @app.callback(
            Output('regressionBox', 'value'),
            [Input('clearButton', 'n_clicks')],
            [State('regressionBox', 'value')])
    def reset_regression(n_clicks, string):
        
        if string is None:
            string = ''

        ctx = dash.callback_context    
        button_pressed = ctx.triggered[0]['prop_id']
                
        if button_pressed == 'clearButton.n_clicks': 
            string = ''
        
        return string


    @app.callback(
        [Output('table-dropdown', 'data'),
        Output('datepicker', 'start_date'),
        Output('datepicker', 'end_date')],
        [Input("upload-csv-store", "data"),
        Input('dropdown', 'value')],
        [State('table-dropdown', 'data'),
        State('regressionBox', 'value'),
        State('datepicker', 'start_date'),
        State('datepicker', 'end_date')]
    )
    def update_datatable_variables(settings_to_load_csv, value, rows, text, start, end): 
        all_frequency_options = OrderedDict(
            [('Annual', 'a'), ('Semiannual', 'sa'), ('Quarterly', 'q'), ('Monthly', 'm'), ('Biweekly', 'bw'),
            ('Weekly', 'w'), ('Daily', 'd')])

        ctx = dash.callback_context

        #Case 1: Uploaded local data
        if ctx.triggered[0]['prop_id'] == 'upload-csv-store.data':
            df_csv = pd.read_json(settings_to_load_csv)
            df_csv = df_csv.sort_index()
            df_csv = pd.DataFrame(df_csv)
            df_vars = df_csv.columns[1:]
            start = df_csv.loc[1,'Date'].date()
            end = df_csv['Date'][df_csv.index[-1]].date()
            for var in df_vars:
                contents = {'Variable ID': '{}_lcl'.format(var), 'Variable': var, 'Units': 'lin',
                            'Frequency': all_frequency_options,
                            'Y-axis Position': 'Left'}
                if var != None:
                    rows.append(contents)
            return rows, '{}'.format(start), '{}'.format(end)    
        
        #Case 3: User selects a variable from dropdown - add the datatable
        else:
            fred = Fred(api_key='51162ee18f52f0caa348af89a09c0af4')
            info = fred.get_series_info(value)

            contents = {'Variable ID': value, 'Variable': info['title'], 'Units': 'lin',
                        'Frequency': all_frequency_options[info['frequency']],
                        'Y-axis Position': 'Left'}

            if value != None:
                rows.append(contents)

            return rows, '{}'.format(start), '{}'.format(end)

    @app.callback(
        Output("save-settings-button", "href"),
        [Input('table-dropdown', 'data'),
        Input('regressionBox', 'value'),
        Input('markdownBox', 'value'),
        Input('datepicker', 'start_date'),
        Input('datepicker', 'end_date')]
    )
    def save_combination(rows, text, markdown, start, end):

        data = pd.DataFrame({'text': [text], 'start': [start], 'end': [end], 'markdown': [markdown]})
        rows = pd.DataFrame(rows).reset_index()
        df = pd.merge(rows, data, how = 'outer', left_index=True, right_index=True)
        
        csv_string = df.to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)

        return csv_string


    @app.callback(Output('df-store', 'data'),
                [Input('table-dropdown', 'data'),
                Input('datepicker', 'start_date'),
                Input('datepicker', 'end_date'),
                Input('upload-csv-store', 'data')])

    def store_datatable_var(rows, start_date, end_date, df_csv):

        #Input: Datepicker
        #Get start and end date from datepicker
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        start = datetime(start_date.year, start_date.month, start_date.day)
        end = datetime(end_date.year, end_date.month, end_date.day)
        
        if df_csv != None:
            df_csv = pd.read_json(df_csv)
            df_csv = df_csv.sort_index()
            df_csv.columns = [str(col) + '_lcl' for col in df_csv.columns]
            df_csv = df_csv.rename(columns=({'Date_lcl':'index'}))
            for element in df_csv['index']:
                element = element.date()
        
            #data is a list of series to pull from FRED
            #data is a list of dict - series: GDP, units: lin, y-axis_position: left
            data = []
            num = len(df_csv.columns) - 1
            
            #Input: table-dropdown data
            #Get series to pull from FRED from current rows in datatable
            if len(rows) > num:
                for row in rows:
                    keys = ['series', 'units', 'frequency', 'y-axis_position']
                    values = [row['Variable ID'], row['Units'], row['Frequency'], row['Y-axis Position']]
                    data.append(dict(zip(keys, values)))
            
                df_total = pd.DataFrame()
                
                #Input: data
                #For each variable in data, Pull data from FRED and store in df_total
                for e in data:
                    try:
                        e_series = fred.get_series(e['series'], start, end, units=e['units'], frequency=e['frequency']).reset_index()
                        e_series.columns = ['index', e['series']]
                        df_total = df_total.reset_index()
                        df_total = pd.merge(df_total, e_series, on='index', how='outer').set_index('index').sort_values(by='index')
                    except ValueError:
                        pass

                df_total = pd.merge(df_csv, df_total, on='index', how='outer').set_index('index').sort_values(by='index')
                
                return df_total.to_json()
            else:
                df_csv = df_csv.set_index('index').sort_values(by='index')
                return df_csv.to_json()

        if df_csv == None:
            #data is a list of series to pull from FRED
            #data is a list of dict - series: GDP, units: lin, y-axis_position: left
            data = []
            
            #Input: table-dropdown data
            #Get series to pull from FRED from current rows in datatable
            for row in rows:
                keys = ['series', 'units', 'frequency', 'y-axis_position']
                values = [row['Variable ID'], row['Units'], row['Frequency'], row['Y-axis Position']]
                data.append(dict(zip(keys, values)))
                    
            df_total = pd.DataFrame()
            
            #Input: data
            #For each variable in data, Pull data from FRED and store in df_total
            for e in data:
                e_series = fred.get_series(e['series'], start, end, units=e['units'], frequency=e['frequency']).reset_index()
                e_series.columns = ['index', e['series']]
                df_total = df_total.reset_index()
                df_total = pd.merge(df_total, e_series, on='index', how='outer').set_index('index').sort_values(by='index')
            
            return df_total.to_json()        


    #Plots graph with selected variables in datatable and runs a regression with the formula 
    #in regressionBox
    @app.callback([Output('graph', 'figure'),
                Output('annotation-store','data')],
                [Input('table-dropdown', 'data'),
                Input('table-dropdown', 'selected_rows'),
                Input('df-store', 'data'),
                Input('graph-type', 'value'),
                Input('store-line-format','data'),
                Input('toggle2','on'),
                Input('regression-table', 'data'),
                Input('regression-table', 'selected_rows'),
                Input('regression-store', 'data'),
                Input('graph', 'clickData'),
                Input('text-input', 'value'),
                Input('add-button', 'n_clicks'),
                Input('remove-button','n_clicks'),
                Input('width', 'value'),
                Input('height', 'value')],
                [State('annotation-store','data')])

    def draw_graph(rows_df, selected_rows_index_df, data_df, graph_type, store_line_data, toggle_value, rows_reg, selected_rows_index_reg, data_reg, clickData, text_value, add_button, remove_button, width, height,annotation_data):
            

            
        #Input: table-dropdown selected_rows
        #Filter the rows that are selected in datatable - only draw those rows
        df_total = pd.read_json(data_df)
        df_total.index = pd.to_datetime(df_total.index, unit = 'ms')
        df_total = df_total.sort_index()
        df_total = df_total.reset_index()
        df_total = pd.DataFrame(df_total)
        
        data = []
        #Input: table-dropdown data
        #Get series to pull from FRED from current rows in datatable
        for row in rows_df:
            keys = ['series', 'units', 'frequency', 'y-axis_position']
            values = [row['Variable ID'], row['Units'], row['Frequency'], row['Y-axis Position']]
            data.append(dict(zip(keys, values)))
        
        data_selected = [data[index] for index in selected_rows_index_df]

        
        df_selected = pd.DataFrame()
        left_axis = []
        right_axis = []
        
        for e in data_selected:
            e_series = df_total.loc[:, ['index','{}'.format(e['series'])]]
            df_selected = df_selected.reset_index()
            df_selected = pd.merge(df_selected, e_series, on = 'index', how = 'outer').set_index('index').sort_values(by = 'index')

            if e['y-axis_position'] == 'Left':
                left_axis.append(e['series'] + ' (' + e['units'] + ')')
            else:
                right_axis.append(e['series'] + ' (' + e['units'] + ')')
        
        #Graph regression results
        #Input: regression-table selected_rows

        #This solves problem that selected_rows does not remove index of a deleted row, hence causing IndexErrors
        #Need to manually remove deleted row index
        #Currently a lazy solution is implemented that cuts off indexes above len(rows_reg). But this leads to a bug
        #if e.g. the 1st regression is removed. Issue isn't that big or noticeable so ignoring it for now 
        selected_rows_index_reg_filtered = [e for e in selected_rows_index_reg if e < len(rows_reg)]

        
        reg_selected = [rows_reg[index] for index in selected_rows_index_reg_filtered]

        data_reg = pd.read_json(data_reg)
        data_reg.index = pd.to_datetime(data_reg.index, unit = 'ms')
        data_reg = data_reg.sort_index()
        
        for e in reg_selected:
            reg_series = data_reg.loc[:, '{}'.format(e['Name'])].reset_index()
            df_selected = df_selected.reset_index()
            df_selected = pd.merge(df_selected, reg_series, on = 'index', how = 'outer').set_index('index').sort_values(by = 'index')

            if e['Y-axis Position_reg'] == 'Left':
                left_axis.append(e['Name'])
            else:
                right_axis.append(e['Name'])

        traces = []

        if graph_type == 'tonexty':
            fill_variable = 'tonexty'
        else:
            fill_variable = 'none'

        for i in range(len(df_selected.columns)):
            dff = df_selected.iloc[:, i].dropna()
            
            #Setting y-axis position for each variable 
            yaxis_position = ''
            if df_selected.columns[i] in [e['series'] for e in data]:
                for e in data:
                    if e['series'] == df_selected.columns[i]:
                        yaxis_position = e['y-axis_position']
            if df_selected.columns[i] in [e['Name'] for e in reg_selected]:
                for e in reg_selected:
                    if e['Name'] == df_selected.columns[i]:
                        yaxis_position = e['Y-axis Position_reg']
            
            #For regression, make fitted line on same y-axis position as target variable
            df_selected.columns[i]
                    
            if yaxis_position == 'Right':
                yaxis_pos = 'y2'
            else:
                yaxis_pos = 'y1'

            if store_line_data is not None and df_selected.columns.values[i] in store_line_data.keys():
                z = go.Scatter(
                    x=dff.index,
                    y=dff,
                    name=df_selected.columns[i],
                    text=[df_selected.columns[i]]*len(dff),
                    fill = fill_variable,
                    mode=store_line_data[df_selected.columns.values[i]][0],
                    line=dict(dash=store_line_data[df_selected.columns.values[i]][1], 
                            width=store_line_data[df_selected.columns.values[i]][2], color=store_line_data[df_selected.columns.values[i]][3]),
                    yaxis=yaxis_pos
                    )

            else:
                z = go.Scatter(
                    x = dff.index,
                    y = dff,
                    name = df_selected.columns[i],
                    text=[df_selected.columns[i]]*len(dff),
                    fill = fill_variable,
                    mode = 'lines',
                    yaxis = yaxis_pos

                )

            traces.append(z)


        layout = go.Layout(
            legend=dict(x=-.1, y=1.2),
            height=height,
            width=width,
            hovermode = 'closest',
            yaxis = dict(
                title = ', '.join(left_axis)
                ),
            yaxis2 = dict(
                title = ', '.join(right_axis),
                side = 'right',
                overlaying = 'y'
                )        
        )
        # annotation
        ctx = dash.callback_context

        new_anno_dict_list = []
        if ctx.triggered[0]['prop_id'].split('.')[0] == 'add-button':
            resp = clickData
            cur_annotation_dict = {'x': datetime.strptime(resp['points'][0]['x'], '%Y-%m-%d'),
                                'y': float(resp['points'][0]['y']),
                                'xref': 'x', 'yref': 'y', 'text': text_value, 'showarrow': True,
                                'font': dict(color="black", size=20),
                                'align': 'center'}
            new_anno_dict_list = [cur_annotation_dict]

        if annotation_data is not None:
            new_anno_dict_list.extend(annotation_data)

        # if new_anno_dict_list is not empty, we either receive a click, or have previous saved click data, process to update graph
        if new_anno_dict_list and ctx.triggered[0]['prop_id'].split('.')[0] != 'remove-button':
            annotation_data = new_anno_dict_list
            layout.update({"annotations": annotation_data})

        if ctx.triggered[0]['prop_id'].split('.')[0] == 'remove-button':
            min_x = []
            annotation_data = annotation_data.copy()
            min_diff_y = 1000
            min_diff_x = abs(datetime.strptime("01/01/1947", "%d/%m/%Y") - datetime.strptime("30/01/2019", "%d/%m/%Y"))
            for value in annotation_data:
                if abs(datetime.strptime(value['x'], '%Y-%m-%d') - datetime.strptime(clickData['points'][0]['x'], '%Y-%m-%d')) < min_diff_x:
                    min_point = value
                    min_diff_x = abs(datetime.strptime(value['x'], '%Y-%m-%d') - datetime.strptime(clickData['points'][0]['x'], '%Y-%m-%d'))
                    remove = value
                    if min_diff_x < abs(datetime.strptime("01/01/2018", "%d/%m/%Y") - datetime.strptime("01/02/2019", "%d/%m/%Y")):
                        min_x.append(value)
                    for value in min_x:
                        if abs(float(value['y']-float(clickData['points'][0]['y']))) < min_diff_y:
                            min_point_y = value
                            min_diff_y = abs(float(value['y'] - float(clickData['points'][0]['y'])))
                            remove = value
            annotation_data.remove(remove)
            layout.update({"annotations": annotation_data})

        if toggle_value == True:
                shading = [
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1857-06-01',
                        'y0': 0,
                        'x1': '1858-12-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1860-10-01',
                        'y0': 0,
                        'x1': '1861-06-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1865-04-01',
                        'y0': 0,
                        'x1': '1867-12-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1869-06-01',
                        'y0': 0,
                        'x1': '1870-12-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1873-10-01',
                        'y0': 0,
                        'x1': '1879-03-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1882-03-01',
                        'y0': 0,
                        'x1': '1885-05-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1887-03-01',
                        'y0': 0,
                        'x1': '1888-04-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1890-07-01',
                        'y0': 0,
                        'x1': '1891-05-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1893-01-01',
                        'y0': 0,
                        'x1': '1894-06-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1895-12-01',
                        'y0': 0,
                        'x1': '1897-06-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1899-06-01',
                        'y0': 0,
                        'x1': '1900-12-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1902-09-01',
                        'y0': 0,
                        'x1': '1904-08-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1907-05-01',
                        'y0': 0,
                        'x1': '1908-06-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1910-01-01',
                        'y0': 0,
                        'x1': '1912-01-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1913-01-01',
                        'y0': 0,
                        'x1': '1914-12-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1918-08-01',
                        'y0': 0,
                        'x1': '1919-03-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1920-01-01',
                        'y0': 0,
                        'x1': '1921-07-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1923-05-01',
                        'y0': 0,
                        'x1': '1924-07-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1926-10-01',
                        'y0': 0,
                        'x1': '1927-11-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1929-08-01',
                        'y0': 0,
                        'x1': '1933-03-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1937-05-01',
                        'y0': 0,
                        'x1': '1938-06-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1945-02-01',
                        'y0': 0,
                        'x1': '1945-10-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1948-11-01',
                        'y0': 0,
                        'x1': '1949-10-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1953-07-01',
                        'y0': 0,
                        'x1': '1954-05-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1957-08-01',
                        'y0': 0,
                        'x1': '1958-04-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1960-04-01',
                        'y0': 0,
                        'x1': '1961-02-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1969-12-01',
                        'y0': 0,
                        'x1': '1970-11-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1973-11-01',
                        'y0': 0,
                        'x1': '1975-03-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1980-01-01',
                        'y0': 0,
                        'x1': '1980-07-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1981-07-01',
                        'y0': 0,
                        'x1': '1982-11-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '1990-07-01',
                        'y0': 0,
                        'x1': '1991-03-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '2001-03-01',
                        'y0': 0,
                        'x1': '2001-11-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    },
                    {
                        'type': 'rect',
                        'xref': 'x',
                        'yref': 'paper',
                        'x0': '2007-12-01',
                        'y0': 0,
                        'x1': '2009-06-01',
                        'y1': 1,
                        'fillcolor': '#d3d3d3',
                        'opacity': 0.5,
                        'line': {
                            'width': 0,
                        }
                    }
                ]
                shading_final = shading.copy()
                for i in shading:
                    if datetime.strptime(i['x0'], '%Y-%m-%d') < df_total["index"].iloc[0] or datetime.strptime(i['x1'], '%Y-%m-%d') > df_total["index"].iloc[-1]:
                        shading_final.remove(i)
                        shading = shading_final
                shading = shading_final
                layout.update({'shapes': shading})

        return {'data': traces, 'layout': layout}, annotation_data


    #When the data changes, update the download link href
    @app.callback(
        Output("download-link", "href"),
        [Input('df-store', 'data'),
        Input('regression-store', 'data')])

    def update_download_link(data_df, data_regression):
        df = pd.read_json(data_df)
        df.index = pd.to_datetime(df.index, unit = 'ms')
        df = df.sort_index()

        try:
            df_regression = pd.read_json(data_regression)
            df_regression.index = pd.to_datetime(df_regression.index, unit = 'ms')
            df_regression = df_regression.sort_index()
            df.index.name = 'index'
            df_regression.index.name = 'index'
            df = pd.merge(df, df_regression, on = 'index', how = 'outer').sort_index()
        except ValueError:
            pass

        csv_string = df.to_csv(index=True, encoding='utf-8', index_label='Date')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)

        return csv_string

    #Input text -> Dropdown options change
    @app.callback(
        Output('dropdown', 'options'),
        [Input('input', 'value')])
    def set_dropdown_options(input):
        
        ##Search FRED
        #Gets top 100 results from passing input into Fred Search
        search = fred2.search(input)['seriess'][:100]
        #Get series IDs of top 100 results
        search_titles = [e['title'] for e in search]
        search_frequency = [e['frequency'] for e in search]
        search_units = [e['units'] for e in search]
        search_seasonal_adjustment = [e['seasonal_adjustment'] for e in search]
        search_IDs = [e['id'] for e in search]
        search_observation_start = [e['observation_start'] for e in search]
        search_observation_end = [e['observation_end'] for e in search]

        
        #Return list of options
        out_dict = [
            {
                'label': '{}, {}, {}, {}, {}, {} to {}'.format(title, frequency, units, seasonal_adjustment, id, observation_start, observation_end), 'value': id
            } for title, frequency, units, seasonal_adjustment, id, observation_start, observation_end in zip(search_titles, search_frequency, search_units, search_seasonal_adjustment, search_IDs, search_observation_start, search_observation_end)]
        
        return out_dict


    def show_metadata(rows, i):

        values = [row['Variable ID'] for row in rows]
        try:
            info = fred.get_series_info(values[i])
            info = info[['id', 'title', 'observation_start', 'observation_end', 'frequency', 'units', 'seasonal_adjustment',
                    'last_updated', 'notes']]
            title = '{} ({})'.format(info['title'], info['id'])
            meta_uni = 'Units: {}'.format(info['units'])
            meta_fre = 'Frequency: {}'.format(info['frequency'])
            meta_sea = 'Seasonal Adjustment: {}'.format(info['seasonal_adjustment'])
            meta_obs = 'Observation Period: {} to {}'.format(info['observation_start'], info['observation_end'])
            meta_las = 'Last Updated: {}'.format(info['last_updated'])
            meta_not = 'Notes: {}'.format(info['notes'])

            return [html.Div([html.P('{}'.format(title), style=dict( maxHeight='400px', fontSize='16px', fontWeight ='bold', backgroundColor = '#D0E5D2'))]),
                    html.Div([html.P('{}'.format(meta_uni), style=dict( maxHeight='400px', fontSize='14px' ))]),
                    html.Div([html.P('{}'.format(meta_fre), style=dict( maxHeight='400px', fontSize='14px' ))]),
                    html.Div([html.P('{}'.format(meta_sea), style=dict( maxHeight='400px', fontSize='14px' ))]),
                    html.Div([html.P('{}'.format(meta_obs), style=dict( maxHeight='400px', fontSize='14px' ))]),
                    html.Div([html.P('{}'.format(meta_las), style=dict( maxHeight='400px', fontSize='14px' ))]),
                    html.Div([html.P('{}'.format(meta_not), style=dict( maxHeight='400px', fontSize='14px' ))])], {}
        
        except IndexError:
            return [], {'display':'none'}


    #Show the metadata tables (multiple if necessary)
    for i in range(30):

        app.callback(
            [Output('meta{}'.format(i), 'children'),
            Output('meta{}'.format(i), 'style')],
            [Input('table-dropdown', 'data')]
        )(partial(show_metadata, i=i))



    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)

    #In the future, save the filename by user or by session start time - so that there will be one copy per session that can easily be reloaded

    #When a file is uploaded on Dash, save it into upload_directory
    def save_file(content):
        print(content)
        #name = datetime.now().strftime("%m%d%Y-%H%M%S") + '.txt'
        name = 'output.txt'
        with open(os.path.join(UPLOAD_DIRECTORY, name), "w") as text_file:
            text_file.write(content)

        
    #Function to save image file to upload_directory
    def save_image(figure):
        #name = datetime.now().strftime("%m%d%Y-%H%M%S") + '.png'
        name = 'graph.png'
        with open(os.path.join(UPLOAD_DIRECTORY_POST, name), 'wb') as img_file:
            pio.write_image(figure, file = img_file, format = 'png')

    @app.callback(
        Output('hidden-div1', 'children'),
        [Input('postButton', 'n_clicks')],
        [State('outputBox', 'value')]
    )
    def update_saved_output(n_clicks, output_box_value):
        if output_box_value is not None or '':
            save_file(output_box_value)
        return ''

    @app.callback(
        Output('hidden-div2', 'children'),
        [Input('graph', 'figure')]
    )
    def update_saved_graph(figure):
        if figure is not None:
            save_image(figure)
        return ''
        
        

