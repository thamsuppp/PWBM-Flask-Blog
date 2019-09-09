
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
import fred
from fredapi import Fred
import fred as fred2
from datetime import datetime, date, time
import json
import statsmodels.api as sm
from functools import partial




external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

units_options = {'No Transformation': 'lin',
                 'Change': 'chg',
                 'Change from Year Ago': 'ch1',
                 '% Change': 'pch',
                 '% Change from Year Ago': 'pc1',
                 'Compounded Annual Rate of Change': 'pca',
                 'Continuously Compounded Rate of Change': 'cch',
                 'Continuously Compounded Annnual Rate of Change': 'cca',
                 'Natural Log': 'log'}

url_base = '/dash/app/'


layout = html.Div(
    [   dcc.Store(id = 'df_store'),
        html.Div(
            [
                html.Div(
                    [
                        html.H1("Economic Time Series Analysis")
                    ], 
                    style = dict(
                        width = '30%',
                        display = 'table-cell',
                        verticalAlign = "middle"
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
                dash_table.DataTable(
                    id='datatable',
                    columns=[
                        {'id': 'Variable ID', 'name': 'Variable ID'},
                        {'id': 'Variable', 'name': 'Variable'},
                        {'id': 'Units', 'name': 'Units', 'presentation': 'dropdown'},
                        {'id': 'Y-axis Position', 'name': 'Y-axis Position', 'presentation': 'dropdown'}
                    ],
                    data = [],
                    column_static_dropdown=[
                            {'id': 'Units',
                             'dropdown': [
                                {'label': key, 'value': value}
                                for key, value in units_options.items()
                            ]
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
                html.Div(    
                    [
                        html.Div(
                            [
                                dcc.DatePickerRange(
                                id='datepicker',
                                start_date= datetime(1950, 1, 1),
                                end_date= datetime(2019, 1, 1))
                            ],
                            style = dict(
                                height = '2px',
                                width = '30%',
                                display = 'table-cell',
                                verticalAlign = "middle"
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
        dcc.Graph(id = 'graph')        
    ]
)
