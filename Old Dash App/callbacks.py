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

def json_to_df(df_in_json):
    df = pd.read_json(df_in_json)
    df.index = pd.to_datetime(df.index, unit = 'ms')
    df = df.sort_index()
    return df

#Register all the callbacks in a dash app
def register_callbacks(dashapp):

    fred = Fred(api_key='51162ee18f52f0caa348af89a09c0af4')
    fred2.key('51162ee18f52f0caa348af89a09c0af4')
    
    #Input text -> Dropdown options change
    @dashapp.callback(
        Output('dropdown', 'options'),
        [Input('input', 'value')])
    def set_dropdown_options(input_value):
        ##Search FRED and gets the top 100 results
        search = {}
        if input_value != '':
            search = fred2.search(input_value)['seriess'][:100]
        #Get series IDs and information of top 100 results
        search_titles = [e['title'] for e in search]
        search_frequency = [e['frequency'] for e in search]
        search_units = [e['units'] for e in search]
        search_seasonal_adjustment = [e['seasonal_adjustment'] for e in search]
        search_IDs = [e['id'] for e in search]
        search_observation_start = [e['observation_start'] for e in search]
        search_observation_end = [e['observation_end'] for e in search]
        
        #Return list of options
        out_dict = [
            {'label': '{}, {}, {}, {}, {}, {} to {}'.format(title, frequency, units, seasonal_adjustment, 
            id, observation_start, observation_end), 'value': id} 
                for title, frequency, units, seasonal_adjustment, id, observation_start, observation_end 
                in zip(search_titles, search_frequency, search_units, search_seasonal_adjustment, 
                    search_IDs, search_observation_start, search_observation_end)]
        
        return out_dict         


    @dashapp.callback(
            Output('datatable', 'data'),
            [Input('dropdown', 'value')],
            [State('datatable', 'data')])
    def update_datatable(dropdown_value, datatable): 
        if datatable is None:
            datatable = []
            
        fred = Fred(api_key='51162ee18f52f0caa348af89a09c0af4')
        if dropdown_value != None:
            info = fred.get_series_info(dropdown_value)
            contents = {'Variable ID': dropdown_value, 'Variable': info['title'],
                        'Units': 'lin', 'Y-axis Position': 'Left'}
            datatable.append(contents)

        return datatable                   

    @dashapp.callback(Output('df_store', 'data'),
                [Input('datatable', 'data'),
                Input('datepicker', 'start_date'),
                Input('datepicker', 'end_date')])

    def update_df_store(datatable, start_date, end_date):

        #Get start and end date from datepicker
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        start = datetime(start_date.year, start_date.month, start_date.day)
        end = datetime(end_date.year, end_date.month, end_date.day)
                
        df = pd.DataFrame()
        
        #For each row in datatable, Pull data from FRED and store in df
        for e in datatable:
            e_series = fred.get_series(e['Variable ID'], start, end, units = e['Units']).reset_index()
            e_series.columns = ['index', e['Variable ID']]
            df = df.reset_index()
            df = pd.merge(df, e_series, on='index', how='outer').set_index('index').sort_values(by='index')
        
        return df.to_json()


    @dashapp.callback(Output('graph', 'figure'),
                [Input('datatable', 'data'),
                Input('datatable', 'selected_rows'),
                Input('df_store', 'data')])
    def draw_graph(datatable, datatable_selected_rows, df_store):
        #Convert df_store from JSON to df
        df = json_to_df(df_store)
        
        selected_cols = datatable_selected_rows
        df_selected = df.iloc[:, selected_cols]
        
        print(df_selected)
        traces = []
        left_axis = []
        right_axis = []
        
        for i in range(len(df_selected.columns)):
            dff = df_selected.iloc[:, i].dropna()
            
            #Setting y-axis position for each variable 
            yaxis_position = ''
            for e in datatable:
                if e['Variable ID'] == df_selected.columns[i]:
                    yaxis_position = e['Y-axis Position']
                        
            if yaxis_position == 'Right':
                yaxis_pos = 'y2'
                right_axis.append(e['Variable ID'] + '(' + e['Units'] + ')')
            else:
                yaxis_pos = 'y1'
                left_axis.append(e['Variable ID'] + '(' + e['Units'] + ')')
            
            z = go.Scatter(
                    x = dff.index,
                    y = dff,
                    name = df_selected.columns[i],
                    mode = 'lines',
                    yaxis = yaxis_pos
                )

            traces.append(z)

        layout = go.Layout(
            legend=dict(x=-.1, y=1.2),
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
        
        return {'data': traces, 'layout': layout}