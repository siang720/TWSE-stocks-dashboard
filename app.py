#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from turtle import width
import dash
from dash import html
from dash import dcc
from dash import dash_table

from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from webscraping_v1 import *
import sys

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Stock Dashboard"

server = app.server

def reusable_graph_table(name):
    
    div = html.Div(
        className='one-half column',
        style={'textAlign': 'center'},
        children=[
            dcc.Graph(id=f'{name}-fig'),
            dash_table.DataTable(
                id=f'{name}-df',
                style_table={'minWidth': '100%', 'height': '250px', 'overflowY': 'auto', 'overflowX': 'auto', 'margin': '0 auto', 'backgroundColor': 'white'},
                fixed_columns={'headers': True, 'data': 1},
                page_size=20,
                fixed_rows={'headers': True, 'data': 0},
                style_cell={
                    'height': '45px',
                    'minWidth': '130px', 'width': '130px', 'maxWidth': '130px',
                    'whiteSpace': 'normal',
                    'fontSize': '1.2rem'
                },
                style_header={'fontWeight': '600'}
            )
        ]
    )
    
    @app.callback([
        Output(f'{name}-fig', 'figure'),
        Output(f'{name}-df', 'columns'),
        Output(f'{name}-df', 'data')],
        Input('stock-list-dropdown', 'value'))
    def update_output(symbol):
        
        if not symbol:
            raise PreventUpdate
            
        symbol = symbol.split('.')[0]
        
        func = getattr(sys.modules[__name__], f'get_{name}')
        
        df, fig = func(symbol)
        columns = [get_column_dict(column, dtype) for column, dtype in df.dtypes.items()]
        data = df.to_dict(orient='records')
        
        return fig, columns, data
    
    return div
    
app.layout = html.Div(
    className='container',
    style={
        'marginTop': 60,
        'marginBottom': 60,
        'textAlign': 'center'
    },
    children=[
        html.Div(
            className='row',
            style={
                'marginBottom': 30,
            },
            children=[
                html.H3('Stock Dashboard'),
                dcc.Dropdown(
                    id='stock-list-dropdown',
                    options=get_stock_list(),
                    placeholder='Search for stock ID (TWSE Limited)'
                )
            ]
        ),
        html.Div(
            className='row',
            children=[
                reusable_graph_table('shareholder_structure'),
                reusable_graph_table('inst_investors')
            ]
        ),
        html.Hr(),
        html.Div(
            className='row',
            children=[
                reusable_graph_table('monthly_revenue'),
                reusable_graph_table('cashflow')
            ]
        ),
        html.Hr(),
        html.Div(
            className='row',
            children=[
                reusable_graph_table('profitability'),
                reusable_graph_table('dividends')
            ]
        )
    ]
)


if __name__ == '__main__':
    app.run_server(debug=True)
    

