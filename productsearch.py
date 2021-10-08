import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
from dash.dependencies import Input, Output
from dash_table.Format import Format, Scheme
import numpy

from mixer import Mixer as M
import mixer as m
from amplifier import Amplifier as A
from powerdivider import PowerDivider as PD
import powerdivider as powdiv
from coupler import Coupler as CO
from balun import Balun as B
import balun

ACTIVE_GRAPHS = []

LOADED_PRODUCT_OBJECTS = {}

SEARCHED_PRODUCT_OBJECTS = {}
LOW_FREQ, HIGH_FREQ = None, None

COLOR = {
    'yellow-green': '#EBEB7C',
    'green': '#7FB539',
    'teal': '#00A6A6',
    'blue': '#008BC4',
    'purple': '#724993',
    'violet': '#29235C',
    'magenta': '#ED1E79',
    'grey': '#666666'
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

'''
==============================================================================
Display component layouts
==============================================================================
'''

def add_error():
    '''
    This function uses the ConfirmDialog dash core component to display an error
    message using the browser's native "confirm" modal with optional message parameter and
    "OK" and "Cancel" buttons.
    
    Parameters:
        message : string
            message to be displayed in confirm modal
    Returns:
        object : ConfirmDialog object (dash_core_components)
            
    '''
    return dcc.ConfirmDialog(id='error-msg', message='')

def add_header(title):
    '''
    This function adds html "header" divs using dash html components.
    
    Parameters:
        title : string
            title string to be displayed (indicates which product is being searched)
    Returns:
        object : html.Div (dash_html_components)
    '''
    return html.Div([ 
            html.Br(),

            html.Div(title,
                style={
                    'color' : COLOR['violet'], 
                    'font-weight' : '700',
                    'font-size' : 'xx-large',
                    },
            ),

            html.Div(['Enter desired parameters below, then click SEARCH']),
            html.Div(['For fixed-frequency searches, enter same value for both low & high values, or leave one field blank.']),

            html.Br(),
        ], id='header-text-rows', 
        style={
            'text-align' : 'center', 
            'color': COLOR['magenta'], 
            }
        )

def add_inputs(idname, text, unit, hide):
    '''
    This function adds user text input blocks and associated labels using
    dash html.Div and dcc.Input components.  The function uses input parameters
    to dynamically create unique ids for each component.
    
    Parameters:
        idname : string
            string used as part of defining the id of the input component
        text : string
            text used as part of defining the label of the input component
        unit : string
            text used as part of defining the label of the input component
        hide : boolean
            True or False indicating whether or not to display the input
    Returns:
        object : html.Div (dash_html_components)
    '''
    return html.Div([
            html.Div(
                (text + ' Low ' + unit + ':'), 
                id=('low-' + idname + '-text'), 
                className='four columns',
                style={
                    'text-align' : 'right',
                    'margin-top' : '0.5%',
                    'margin-left' : '1%',
                    'font-weight' : '300',
                    'color' : COLOR['grey'],
                },
            ),

            html.Div([
                dcc.Input(id=('low-' + idname + '-input'), 
                        type='number', 
                        placeholder='Low',
                        value = None,
                        debounce=True,
                        style={
                            'width':'150%',
                            }
                        ),
            ], 
            style={
                'margin-left' : '1%',
            },
            className='one columns'
            ),

            html.Div(
                (text + ' High ' + unit + ':'), 
                id=('high-' + idname + '-text'), 
                className='two columns',
                style={
                    'text-align' : 'right',
                    'margin-top' : '0.5%',
                    'margin-left' : '7%',
                    'font-weight' : '300',
                    'color' : COLOR['grey'],
                },
            ),

            html.Div([
                dcc.Input(id=('high-' + idname + '-input'), 
                        type='number', 
                        placeholder='High',
                        value = None,
                        debounce=True,
                        style={
                            'width':'150%',
                            }
                        ),
            ], 
            style={
                'margin-left' : '1%',
            },
            className='one column'),

            html.Div(className='four columns'),
        ], id=(idname + '-inputs-row'), hidden=hide, className='row')

def add_buttons():
    '''
    This function adds user input buttons using the dash html.Div and
    html.Button components from the dash_html_components library.
    
    Parameters:
        None
    Returns:
        object : html.Div (dash_html_components)
    '''
    return html.Div([    
        html.Div([
            html.Button('Search', 
                        id='search-button',
                        n_clicks=0,
                        style={
                            'color' : COLOR['blue'],
                            'border-color' : COLOR['blue'],
                        },
                        ),
        ], 
        style={
            'text-align' : 'right', 
        },
        className='five columns'
        ),

        html.Div([
            html.Button('Reset', 
                        id='reset-button',
                        n_clicks=0,
                        style={
                            'color' : COLOR['blue'],
                            'border-color' : COLOR['blue'],
                        }
                        ),
        ], 
        style={
            'text-align' : 'right',
        },
        className='three columns'
        ),
    ], id='search-reset-row', style={'display' : 'inline'}, className='row')

def add_settings_text():
    '''
    This function adds "Settings" text to the html layout.  This component
    is used later in a callback to open a series of "Settings" options.
    
    Parameters:
        None
    Returns:
        object : html.Div (dash_html_components)
    '''
    return html.Div([
        html.Div('.',
        style={
            'color' : 'white'
        },
        className='five columns'),

        html.Div(
        'Settings',
        id='settings-text',
        style={
            'text-align' : 'center',
            'text-decoration' : 'underline',
            'font-style' : 'italic',
            'color' : COLOR['purple']
        },
        className='two columns',
        ),
    ], id='settings-text-row', className='row')

def add_checklist(o,v):
    '''
    This function adds settings checkboxes to the html layout using the dash
    dcc.Checklist component.
    
    Parameters:
        o: List of Dicts (from product object x.graph_options)
        v: List (used to select which checkboxes are default selections)
    Returns:
        object : html.Div (dash_html_components)
    '''
    return html.Div([
        html.Div('.',
        style= {
            'color' : 'white'
        },
        className='five columns'),

        html.Div([
            dcc.Checklist(
                id='settings-checklist',
                options=o,
                value=v,
                style={
                    'color' : COLOR['teal']
                },
            ) 
        ], className='two columns')
    ], id='checklist-container', hidden=True, className='row' )

def add_radiobuttons(o,v):
    '''
    This function adds table sortting radio buttons to the html layout using the dash
    dcc.RadioItems component.
    
    Parameters:
        o: List of Dicts
        v: List (used to select which button is selected by default)
    Returns:
        object : html.Div (dash_html_components)
    '''
    return html.Div([
        html.Div('.', style={'color':'white'}, className='one columns'),

        html.Div([
            dcc.RadioItems(id='sort-options',
                options=o,
                value=v,
                labelStyle={'display':'inline-block'}
            )
        ], className='six columns')
    ], id='sort-options-row', className='row')

def add_table(cols,sb,hcols,sdc):
    '''
    This function adds a table to the html layout using the DataTable from the 
    dash_table library.  It also makes use of the dash dcc.Loading component
    to provide an indication that the table is being populated in the background.
    
    Parameters:
        cols: list of dicts
            list of dicts used to store format information for the data table
        sb : list of dicts (column used for sorting data table)
            list of dicts used to indicate which column is used to sort the data table
        hcols : list (hidden columns)
            list used to indicate which columns are hidden
        sdc : list of dicts
            list of dicts used to change formatting of column being used to sort
    Returns:
        object : html.Div (dash_html_components)
    '''
    return dcc.Loading(id='loading-graphs',
        type='default',
        fullscreen=False,
        children=[
            html.Div([
                html.Div('.', style={'color':'white'}, className='one columns'),

                html.Div([
                    dt.DataTable(id='products-table',
                            columns=cols,
                            merge_duplicate_headers=True,
                            virtualization=True,
                            fixed_rows={'headers': True},
                            page_action='none',
                            sort_action='native',
                            sort_by=sb,
                            sort_mode='single',
                            row_selectable='multi',
                            selected_rows=[],
                            hidden_columns=hcols,
                            style_data={
                                'maxWidth': '100px',
                                'minWidth': '50px',
                            },
                            style_table={
                                'maxHeight': 350,
                                'overflowX': 'auto',
                            },
                            style_cell={
                                'color' : COLOR['purple'],
                                'border' :'1px solid ' + COLOR['teal']
                            },
                            style_cell_conditional=[
                                {
                                    'if': {'column_id': 'model'},
                                    'width': '10%',
                                    'textAlign': 'left',
                                },
                            ],
                            style_header={
                                'backgroundColor': COLOR['violet'],
                                'fontWeight': '700',
                                'color' : COLOR['magenta'],
                                'border': '1px solid ' + COLOR['grey'],
                            },
                            style_data_conditional=sdc,
                            css =[
                            {'selector':'.dash-spreadsheet-menu','rule':'display:none'},
                            ] ,  
                        ),
                    ],
                    className='ten columns',
                ),
            ], id='products-table-row', className='row'),
        ],
        style={
            'align-self':'start',
        }
    )

def add_figures():
    '''
    This function adds a container for figures to the html layout using the dash
    html.Div component.  It also makes use of the dash dcc.Loading component
    to provide an indication that figures are being populated in the background.
    
    Parameters:
        None
    Returns:
        object : html.Div (dash_html_components)
    '''
    return dcc.Loading(id='loading-figures',
        type='circle',
        fullscreen=False,
        children=[
            html.Div(id='graphs', className='row'),
        ],
        style={
            'align-self':'start',
        }
    )

def search_container(product):
    '''
    This function configures the master html container for searching the selected
    product type.  This function calls the other layout methods for configuring input,
    settings and table options.
    
    Parameters:
        product: String
            String indicating which product type to configure the search for:
                (mixer 'm', amplifier 'a', power divider 'pd', coupler 'c',
                 balun 'b', etc.)
    Returns:
        object : html.Div (dash_html_components)
    '''
    container_children = []

    container_children.append(add_error())

    if product == 'm': 
        M.load_class_vars()
        title = ['Mixer Search']
    elif product == 'a': 
        A.load_class_vars()
        title = ['Amplifier Search']
    elif product == 'pd': 
        PD.load_class_vars()
        title = ['Power Divider Search']
    elif product == 'co': 
        CO.load_class_vars()
        title = ['Coupler Search']
    elif product == 'b': 
        B.load_class_vars()
        title = ['Balun Search']

    container_children.append(add_header(title))

    inputs = [('rf', 'RF', '(GHz)'), 
              ('lo', 'LO', '(GHz)'), 
              ('if', 'IF', '(GHz)'), 
              ('lodr', 'LO Drive', '(dBm)'), 
              ('freq', 'Frequency', '(GHz)') ]
    if product == 'm': hide = [False, False, False, False, True]
    else: hide = [True, True, True, True, False]

    for i in range(len(inputs)):
        inputs[i] = inputs[i] + (hide[i],)

    for idname, text, unit, hide in inputs:
        container_children.append(add_inputs(idname,text,unit,hide))

    container_children.append(add_buttons())
    container_children.append(add_settings_text())

    if product == 'm':
        options=[
            {'label': M.graph_options[0], 'value': M.graph_options[0]},
            {'label': M.graph_options[1], 'value': M.graph_options[1]},
            {'label': M.graph_options[2], 'value': M.graph_options[2]},
            {'label': M.graph_options[3], 'value': M.graph_options[3]},
            {'label': M.graph_options[4], 'value': M.graph_options[4]},
            {'label': M.graph_options[5], 'value': M.graph_options[5]},
            {'label': M.graph_options[6], 'value': M.graph_options[6]},
            {'label': M.graph_options[7], 'value': M.graph_options[7]},
            {'label': 'P1dB', 'value': 'p1db'},
        ]
        value=[M.graph_options[0], M.graph_options[1], M.graph_options[2]]         
    elif product == 'a':
        options=[
            {'label': A.graph_options[0], 'value': A.graph_options[0]},
            {'label': A.graph_options[1], 'value': A.graph_options[1]},
            {'label': A.graph_options[3], 'value': A.graph_options[3]},
            {'label': A.graph_options[4], 'value': A.graph_options[4]},
            {'label': A.graph_options[5], 'value': A.graph_options[5]},
            {'label': A.graph_options[6], 'value': A.graph_options[6]},
        ]
        value=[A.graph_options[0], A.graph_options[1]]
    elif product == 'pd':
        options=[
            {'label': PD.graph_options[0], 'value': PD.graph_options[0]},
            {'label': PD.graph_options[1], 'value': PD.graph_options[1]},
            {'label': PD.graph_options[2], 'value': PD.graph_options[2]},
            {'label': PD.graph_options[3], 'value': PD.graph_options[3]},
            {'label': PD.graph_options[4], 'value': PD.graph_options[4]},
        ]
        value=[PD.graph_options[0], PD.graph_options[1], PD.graph_options[2]]
    elif product == 'co':
        options=[
            {'label': CO.graph_options[0], 'value': CO.graph_options[0]},
            {'label': CO.graph_options[1], 'value': CO.graph_options[1]},
            {'label': CO.graph_options[2], 'value': CO.graph_options[2]},
            {'label': CO.graph_options[3], 'value': CO.graph_options[3]},
        ]
        value=[CO.graph_options[0], CO.graph_options[1], CO.graph_options[2], CO.graph_options[3]]
    elif product == 'b':
        options=[
            {'label': B.graph_options[0], 'value': B.graph_options[0]},
            {'label': B.graph_options[1], 'value': B.graph_options[1]},
            {'label': B.graph_options[2], 'value': B.graph_options[2]},
            {'label': B.graph_options[3], 'value': B.graph_options[3]},
            {'label': B.graph_options[4], 'value': B.graph_options[4]},
        ]
        value=[B.graph_options[0], B.graph_options[1], B.graph_options[2]]

    container_children.append(add_checklist(options, value))

    if product == 'm':
        options = [
            {'label': 'Model Name', 'value': 'mn'},
            {'label': 'Lowest Loss', 'value': 'll'},
            {'label': 'Best Linearity', 'value': 'bl'},
            {'label': 'Best Isolation', 'value': 'bi'},
        ]
        value='mn'
    elif product == 'pd':
        options = [
            {'label': 'Model Name', 'value': 'mn'},
            {'label': 'Lowest Loss', 'value': 'll'},
        ]
        value = 'mn'
    elif product == 'b':
        options = [
            {'label': 'Model Name', 'value': 'mn'},
            {'label': 'Lowest Loss', 'value': 'll'},
            ]
        value = 'mn'
    else:
        options = []
        value = None

    container_children.append(add_radiobuttons(options,value))

    if product == 'm':
        columns=[
            {'name': ['', 'Model'], 'id': 'model'},
            {'name': ['', 'Datasheet'], 'id': 'datasheet', 'type':'text', 'presentation': 'markdown'},
            {'name': ['', 'Stock'], 'id': 'stock'},
            {'name': ['RF (GHz)', 'Low'], 'id': 'rf-low'},
            {'name': ['RF (GHz)', 'High'], 'id': 'rf-high-s'},
            {'name': ['LO (GHz)', 'Low'], 'id': 'lo-low'},
            {'name': ['LO (GHz)', 'High'], 'id': 'lo-high-s'},
            {'name': ['IF (GHz)', 'Low'], 'id': 'if-low'},
            {'name': ['IF (GHz)', 'High'], 'id': 'if-high'},
            {'name': ['LO Drive (dBm)', 'Low'], 'id': 'lodr-low'},
            {'name': ['LO Drive (dBm)', 'High'], 'id': 'lodr-high'},
            {'name': ['', 'P1dB (dBm)'], 'id': 'p1db', 'type': 'numeric', 'format': Format(nully='---')},
            {'name': ['Conv. Loss (dB)', 'Min'], 'id': 'cl-min'},
            {'name': ['Conv. Loss (dB)', 'Median'], 'id': 'cl-med'},
            {'name': ['Conv. Loss (dB)', 'Max'], 'id': 'cl-max'},
            {'name': ['Input IP3 (dBm)', 'Min'], 'id': 'iip3-min'},
            {'name': ['Input IP3 (dBm)', 'Median'], 'id': 'iip3-med'},
            {'name': ['Input IP3 (dBm)', 'Max'], 'id': 'iip3-max'},
            {'name': ['LO-RF Isolation (dB)', 'Min'], 'id': 'lr-iso-min'},
            {'name': ['LO-RF Isolation (dB)', 'Median'], 'id': 'lr-iso-med'},
            {'name': ['LO-RF Isolation (dB)', 'Max'], 'id': 'lr-iso-max'},
            {'name': ['Conv. Loss Value', 'Med'], 'id': 'cl-med-v', 'type': 'numeric'},
            {'name': ['IIP3 Value', 'Med'], 'id': 'iip3-med-v', 'type': 'numeric'},
            {'name': ['LORF ISO Value', 'Med'], 'id': 'lr-iso-med-v', 'type': 'numeric'},
        ]
        sort_by=[{'column_id': 'model', 'direction': 'asc'}]
        hidden_columns=['p1db', 'iip3-min', 'iip3-med', 'iip3-max',
                        'lr-iso-min', 'lr-iso-med', 'lr-iso-max',
                        'cl-med-v', 'iip3-med-v', 'lr-iso-med-v', 'rf-high']
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(230, 230, 230)' },
            {'if': {'column_id': 'model'}, 'backgroundColor': COLOR['blue']},
        ]
    elif product == 'a':
        columns=[
            {'name': ['', 'Model'], 'id': 'model'},
            {'name': ['', 'Datasheet'], 'id': 'datasheet', 'type':'text', 'presentation': 'markdown'},
            {'name': ['', 'Stock'], 'id': 'stock'},
            {'name': ['Freq (GHz)', 'Low'], 'id': 'freq-low'},
            {'name': ['Freq (GHz)', 'High'], 'id': 'freq-high'},
            {'name': ['', 'Small Signal Gain (dB)'], 'id': 'ssg'},
            {'name': ['', 'Saturated Output Power (dBm)'], 'id': 'sop'},
        ]
        sort_by=[{'column_id': 'model','direction': 'asc'}]
        hidden_columns=[]
        style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(230, 230, 230)'}]
    elif product == 'pd':
        columns=[
            {'name': ['', 'Model'], 'id': 'model'},
            {'name': ['', 'Datasheet'], 'id': 'datasheet', 'type':'text', 'presentation': 'markdown'},
            {'name': ['', 'Stock'], 'id': 'stock'},
            {'name': ['Frequency (GHz)', 'Low'], 'id': 'freq-low'},
            {'name': ['Frequency (GHz)', 'High'], 'id': 'freq-high'},
            {'name': ['Insertion Loss (dB)', 'Min'], 'id': 'il-min'},
            {'name': ['Insertion Loss (dB)', 'Median'], 'id': 'il-med'},
            {'name': ['Insertion Loss (dB)', 'Max'], 'id': 'il-max'},
            {'name': ['Amplitude Balance (dB)', 'Min'], 'id': 'ab-min', 
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Amplitude Balance (dB)', 'Median'], 'id': 'ab-med',
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Amplitude Balance (dB)', 'Max'], 'id': 'ab-max',
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Phase Balance (degree)', 'Min'], 'id': 'pb-min',
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Phase Balance (degree)', 'Median'], 'id': 'pb-med',
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Phase Balance (degree)', 'Max'], 'id': 'pb-max',
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Insertion Loss Value', 'Med'], 'id': 'il-med-v', 'type': 'numeric'},
        ]
        sort_by=[{'column_id': 'model','direction': 'asc'}]
        hidden_columns=['il-med-v']
        style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(230, 230, 230)'},
                                {'if': {'column_id': 'model'},'backgroundColor': COLOR['blue']}]
    elif product == 'co':
        columns=[
            {'name': ['', 'Model'], 'id': 'model'},
            {'name': ['', 'Datasheet'], 'id': 'datasheet', 'type':'text', 'presentation': 'markdown'},
            {'name': ['', 'Stock'], 'id': 'stock'},
            {'name': ['Frequency (GHz)', 'Low'], 'id': 'freq-low'},
            {'name': ['Frequency (GHz)', 'High'], 'id': 'freq-high'},
            {'name': ['', 'VSWR'], 'id': 'vswr'},
            {'name': ['', 'Mean Coupling (dB)'], 'id': 'mn-coup'},
            {'name': ['', 'Directivity (dB)'], 'id': 'direct'},
        ]
        sort_by=[{'column_id': 'model','direction': 'asc'}]
        hidden_columns=[]
        style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(230, 230, 230)'}]
    elif product == 'b':
        columns=[
            {'name': ['', 'Model'], 'id': 'model'},
            {'name': ['', 'Datasheet'], 'id': 'datasheet', 'type':'text', 'presentation': 'markdown'},
            {'name': ['', 'Stock'], 'id': 'stock'},
            {'name': ['Frequency (GHz)', 'Low'], 'id': 'freq-low'},
            {'name': ['Frequency (GHz)', 'High'], 'id': 'freq-high'},
            {'name': ['Insertion Loss (dB)', 'Min'], 'id': 'il-min'},
            {'name': ['Insertion Loss (dB)', 'Median'], 'id': 'il-med'},
            {'name': ['Insertion Loss (dB)', 'Max'], 'id': 'il-max'},
            {'name': ['Amplitude Balance (dB)', 'Min'], 'id': 'ab-min', 
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Amplitude Balance (dB)', 'Median'], 'id': 'ab-med',
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Amplitude Balance (dB)', 'Max'], 'id': 'ab-max',
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Phase Balance (degree)', 'Min'], 'id': 'pb-min',
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Phase Balance (degree)', 'Median'], 'id': 'pb-med',
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Phase Balance (degree)', 'Max'], 'id': 'pb-max',
            'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed, nully='---')},
            {'name': ['Insertion Loss Value', 'Med'], 'id': 'il-med-v', 'type': 'numeric'},
        ]
        sort_by=[{'column_id': 'model','direction': 'asc'}]
        hidden_columns=['il-med-v']
        style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(230, 230, 230)'},
                                {'if': {'column_id': 'model'},'backgroundColor': COLOR['blue']}]

    container_children.append(add_table(columns, sort_by, hidden_columns, style_data_conditional))

    container_children.append(html.Br())

    container_children.append(add_figures())

    return html.Div(children=container_children, id='container')

'''
=============================================================================
display layout (Build the main page)
=============================================================================
'''

app.layout = html.Div([
    html.Div('DEMO - Updated 9/3/2021 11:00 am'),
    dcc.Tabs(id='search-tabs', value='m', children=[
        dcc.Tab(label='Mixers', value='m'),
        dcc.Tab(label='Amplifiers', value='a'),
        dcc.Tab(label='Power Dividers', value='pd'),
        dcc.Tab(label='Couplers', value='co'),
        dcc.Tab(label='Balun', value='b'),
    ]),
    html.Div([search_container('m')], id='search-tabs-container')
], style = {'font-family' : 'Roboto'})

'''
=============================================================================
Helper Functions
=============================================================================
'''

def merge_lists(list1, list2):
    '''
    This function combines input list 1 with input list 2 and returns the combined list.
    
    Parameters:
        list1: list
            input list 1
        list2: list
            input list 2
    Returns:
        list
            list with combined elements of list1 and list2
    '''
    l = list1
    for i in list2:
        l.append(i)
    return l

def sort_list(list, order):
    '''
    This function sorts input list "list" to match the order of list input "order.
    
    Parameters:
        list: list
            input list 1 (unsorted input list)
        order: list
            input list 2 (list with desired sort)
    Returns:
        list
            returns "list" sorted to match "order"
    '''
    temp = []
    for i in order:
        if i in list:
            temp.append(i)
    return temp

'''
=============================================================================
input/domain ranges calculation functions
=============================================================================
'''

def minmaxx(products, graph):
    '''
    This function finds the absoulte min and max range for the data of the 
    given products and graph types.
    
    Parameters:
        products: list
            list of product objects
        graph: text
            text name of data/graph type (i.e. "Phase Balance")
    Returns:
        Float64
            returns xlow and xhigh as Float64 values
    '''
    xlow, xhigh = None, None
    for p in products:
        try:
            a = p.getdata(graph, list(p.getdata(graph).keys())[0])
        except:
            break
        for v in a[list(a)[0]]:
            if xlow == None or v <= xlow:
                xlow = v
            if xhigh == None or v >= xhigh:
                xhigh = v

    return (xlow, xhigh)

def minmaxy(products, xmin, xmax, graph_type):
    '''
    This function returns the min and max y values for the range xmin-to-xmax
    for the provided product and graph_type.
    
    Parameters:
        products: list
            list of product objects
        xmin: Float64
            x-range min value
        xmax: Float64
            x-range max value
        graph_type: text
            text name of data/graph type (i.e. "Phase Balance")
    Returns:
        Float64
            returns ylow and yhigh as Float64 values
    '''
    ylow, yhigh = None, None
    for p in products:

        for key in p.getlinekeys(graph_type):
            a = p.getdata(graph_type, key)


            for i in range(len(a[list(a)[1]])):
                k = a[list(a)[0]][i]
                v = a[list(a)[1]][i]
                if xmin < k < xmax:
                    if ylow == None or v < ylow:
                        ylow = v
                    if yhigh == None or v > yhigh:
                        yhigh = v

    if ylow != None and yhigh != None:
        ydiff = yhigh - ylow

        ylow = ylow - ydiff * 0.1
        yhigh = yhigh + ydiff *  0.1

    return (ylow, yhigh)

def true_input_values(low, high):
    '''
    This function provides "missing" user input data required by lower level 
    search functions.  It is a form of error prevention/correction and enables
    search at single frequencies.
    
    Parameters:
        low: Float64
            user input value
        high: Float64
            user input value
    Returns:
        Float64
            returns low and high as Float64 values
    '''
    if low == None and high == None:
        low_freq, high_freq = None, None
    elif low == None:
        low_freq, high_freq = high, high
    elif high == None:
        low_freq, high_freq = low, low
    else:
        low_freq, high_freq = low, high

    return (low_freq, high_freq)


'''
=============================================================================
Product handling functions
=============================================================================
'''

def create_object(class_name, name):
    '''
    This function creates a product object and adds the product to the
    "LOADED_PRODUCT_OBJECTS" list.
    
    Parameters:
        class_name: string
            input string representing product class (i.e. 'M' for Mixers)
        name: string 
            input string parameter for naming the product object
    Returns:
        product object
            product object (Mixer, Amplifier, Coupler, Balun or Power Divider)
    '''
    global LOADED_PRODUCT_OBJECTS
    if class_name == M:
        p = M(name)
    elif class_name == A:
        p = A(name)
    elif class_name == PD:
        p = PD(name)
    elif class_name == CO:
        p = CO(name)
    elif class_name == B:
        p = B(name)
    
    LOADED_PRODUCT_OBJECTS[name] = p
    return p

def manage_load(selected_products_set, class_name):
    '''
    This function maintains a list of product objects to be used for
    calculating table parameters and plot traces.  
    
    Parameters:
        selected_products_set: string
            input string representing product class (i.e. 'M' for Mixers)
        class_name: string 
            input string parameter for naming the product object
    Returns:
        list of product objects
    '''
    global LOADED_PRODUCT_OBJECTS

    active_products = []

    for product in selected_products_set:
        if product not in LOADED_PRODUCT_OBJECTS:
            p = create_object(class_name, class_name.products[product]['id'])
        else:
            p = LOADED_PRODUCT_OBJECTS[product]
        active_products.append(p)

    return active_products

#given parameters, find matching products
def search_products(class_name, inputs):
    if class_name == M:
        low_rf, high_rf, low_lo, high_lo, low_if, high_if, low_lodr, high_lodr = inputs
    else:
        low, high = inputs

    data = []

    for product in class_name.products.values():
        if class_name == M:
            if (
                (low_rf == None or (product['rf-low'] <= low_rf and high_rf <= product['rf-high']))
                and (low_lo == None or (product['lo-low'] <= low_lo and high_lo <= product['lo-high']))
                and (low_if == None or (product['if-low'] <= low_if and high_if <= product['if-high']))
                and (low_lodr == None or (product['lodr-low'] <= low_lodr and high_lodr <= product['lodr-high']))
            ):
                data.append(product)
        elif (low == None or (product['freq-low'] <= low and high <= product['freq-high'])):
            data.append(product)

    return data

'''
=============================================================================
Figure handling functions
=============================================================================
'''

#Build the multiple graphs that will be displayed together
def generate_figures(class_name, active_products, input):
    graph_figures = []
    for graph_type in ACTIVE_GRAPHS:
        fig = create_graph(class_name, active_products, graph_type, input)
        if fig != None:
            graph = html.Div([dcc.Graph(figure=fig)],
                             style={
                                 'margin' : '0px'
                             },
                             className='six columns')
            graph_figures.append(graph)

    if len(graph_figures) == 1:
        graph_figures = graph_figures[0]
    
    return graph_figures

#Build individual graph
def create_graph(class_name, active_products, graph_type, input):
    fig = go.Figure()
    fig.update_layout(title=dict(text=graph_type, font=dict(size=25, color=COLOR['violet'])), 
                        font=dict(family='Roboto'),
                        modebar_remove=['toImage', 'zoom', 'pan', 'zoomIn', 'zoomOut', 'autoScale', 'resetScale'],)

    if class_name == M:
        low, high, low_if_i, high_if_i = input
    else:
        low, high = input


    for p in active_products:
        lines = p.getlinekeys(graph_type)

        line_types=[None, 'dash', 'dashdot', 'dot']

        if p.color == None: p.set_color()

        line_num = 0
        for label in lines:
            fig.add_trace( go.Scatter(
                                x=p.getdata(graph_type, label)['xdata'], 
                                y=p.getdata(graph_type, label)['ydata'],
                                name=class_name.products[p.name]['model']+' '+label,
                                hovertemplate = '<b>' + label + '</b><br>'
                                                + '%{y:.5f} ' + class_name.graph_labels[graph_type]['yunit'] 
                                                + '<extra><br><i>'+class_name.products[p.name]['model']+'</i></extra>',
                                line=dict(color=p.color,
                                            dash=line_types[line_num],
                                            ) 
                                        )
                            )
            line_num += 1
            if line_num >= len(line_types): line_num = 0                                

    fig.update_layout(
        legend=dict(
            font= dict(
                color=COLOR['grey']
            )
        ),
        xaxis=dict(
            title=dict(
                text= class_name.graph_labels[graph_type]['xlabel'] + ' ' + class_name.graph_labels[graph_type]['xunit'],
                font= dict(
                    color=COLOR['magenta']
                ),
            ),
            color=COLOR['grey']
        ),
        yaxis=dict(
            title=dict(
                text= class_name.graph_labels[graph_type]['ylabel'] + ' ' + class_name.graph_labels[graph_type]['yunit'],
                font= dict(
                    color=COLOR['magenta']
                ),
            ),
            color=COLOR['grey']
        ),
    ) 

    if class_name == M and graph_type == M.graph_options[m.IF_R_INDEX]:
        xlow,xhigh = minmaxx(active_products, graph_type)
    else:
        xlow, xhigh = low, high
    if xlow == None: return fig, []

    if class_name == M and graph_type == M.graph_options[m.IF_R_INDEX]:
        if low_if_i != None and xlow < low_if_i: xlow = low_if_i
        if high_if_i != None and high_if_i < xhigh: xhigh = high_if_i
    else:
        if low != None and xlow < low: xlow = low
        if high != None and high < xhigh: xhigh = high

    ylow, yhigh = minmaxy(active_products, xlow, xhigh, graph_type)
    
    fig.update_layout(
        hovermode="x",
        xaxis=dict(range=[xlow, xhigh]),
        yaxis=dict(range=[ylow, yhigh]),
    )
        
    return fig

#From settings, determin which graphs should be displayed
def handle_active_figures(class_name, checklist_values):
    global ACTIVE_GRAPHS

    ACTIVE_GRAPHS.clear()
    for value in checklist_values:
        ACTIVE_GRAPHS.append(value)
    ACTIVE_GRAPHS = sort_list(ACTIVE_GRAPHS, class_name.graph_options)

'''
=============================================================================
Interactivity
=============================================================================
'''

#Tab swicher to different product searches
@app.callback(
    Output('search-tabs-container', 'children'),
    Input('search-tabs', 'value'),
)
def select_search_tab(tab):
    return search_container(tab)

#Toggle on and off setting
@app.callback(
    Output('checklist-container', 'hidden'),
    Input('settings-text', 'n_clicks'),
)
def settings_toggle(clicks):
    if clicks == None or clicks % 2 == 0: return True
    else: return False

#On reset press clear all inputs
@app.callback(
    Output('low-rf-input', 'value'),
    Output('high-rf-input', 'value'),
    Output('low-lo-input', 'value'),
    Output('high-lo-input', 'value'),
    Output('low-if-input', 'value'),
    Output('high-if-input', 'value'),
    Output('low-lodr-input', 'value'),
    Output('high-lodr-input', 'value'),
    Output('low-freq-input', 'value'),
    Output('high-freq-input', 'value'),
    Input('reset-button', 'n_clicks'),
    )
def reset_inputs(clicks):
    return None, None, None, None, None, None, None, None, None, None

#Selecting products on table updates graphs
@app.callback(
    Output('graphs', 'children'),
    Input('settings-checklist', 'value'),
    Input('products-table', 'selected_row_ids'),
    dash.dependencies.State('search-tabs', 'value'),
    dash.dependencies.State('low-rf-input', 'value'),
    dash.dependencies.State('high-rf-input', 'value'),
    dash.dependencies.State('low-lo-input', 'value'),
    dash.dependencies.State('high-lo-input', 'value'),
    dash.dependencies.State('low-if-input', 'value'),
    dash.dependencies.State('high-if-input', 'value'),
    dash.dependencies.State('low-freq-input', 'value'),
    dash.dependencies.State('high-freq-input', 'value'),
)
def update_graph(checklist_values, selected_products, tab, low_rf_i, high_rf_i, low_lo_i, high_lo_i, low_if_i, high_if_i, low_freq_i, high_freq_i):
    if tab == 'm':
        classname = M
        low, high = mixer_true_rflo_range(low_rf_i, high_rf_i, low_lo_i, high_lo_i)
        inputs = (low, high, low_if_i, high_if_i)
    else:
        low, high = true_input_values(low_freq_i, high_freq_i)
        inputs = (low, high)
        if tab == 'a':
            classname = A
        elif tab == 'pd':
            classname = PD
        elif tab == 'co':
            classname = CO
        elif tab == 'b':
            classname = B
    
    handle_active_figures(classname, checklist_values)

    selected_products_set = set(selected_products or [])

    if selected_products_set == []:
        return None

    active_products = manage_load(selected_products_set, classname)

    if low == None and high == None:
        return []

    graph_figures = generate_figures(classname, active_products, inputs)
    
    return graph_figures

# user interactions that change product table
@app.callback(
    Output('products-table', 'data'),
    Output('products-table', 'selected_rows'),
    Output('products-table', 'selected_row_ids'),
    Output('error-msg', 'message'),
    Output('error-msg', 'displayed'),
    Output('products-table', 'sort_by'),
    Output('products-table', 'style_data_conditional'),
    Output('products-table', 'hidden_columns'),

    Input('search-button', 'n_clicks'),
    Input('sort-options', 'value'),
    Input('products-table', 'sort_by'),
    Input('settings-checklist', 'value'),

    dash.dependencies.State('products-table', 'selected_rows'),
    dash.dependencies.State('products-table', 'selected_row_ids'),
    dash.dependencies.State('search-tabs', 'value'),
    dash.dependencies.State('products-table', 'data'),
    dash.dependencies.State('products-table', 'style_data_conditional'),
    dash.dependencies.State('products-table', 'hidden_columns'),
    #inputs
    dash.dependencies.State('low-rf-input', 'value'),
    dash.dependencies.State('high-rf-input', 'value'),
    dash.dependencies.State('low-lo-input', 'value'),
    dash.dependencies.State('high-lo-input', 'value'),
    dash.dependencies.State('low-if-input', 'value'),
    dash.dependencies.State('high-if-input', 'value'),
    dash.dependencies.State('low-lodr-input', 'value'),
    dash.dependencies.State('high-lodr-input', 'value'),
    dash.dependencies.State('low-freq-input', 'value'),
    dash.dependencies.State('high-freq-input', 'value'),
)
def table_interact(n_clicks, sort_value, cur_sort_by, checklist_values,
                   cur_sel_rows, cur_sel_ids, tab, cur_data, cur_style, cur_hidden,
                   low_rf_i, high_rf_i, low_lo_i, high_lo_i, low_if_i, high_if_i, low_lodr_i, high_lodr_i, low_freq_i, high_freq_i):
    
    output_data = cur_data
    output_selected_rows = cur_sel_rows
    output_selected_ids = cur_sel_ids
    output_error = ''
    output_error_display = False
    output_sort_by = cur_sort_by
    output_style = cur_style
    output_hidden = cur_hidden

    ctx = dash.callback_context

    if not ctx.triggered:
        return (output_data, output_selected_rows, output_selected_ids, output_error, 
                output_error_display, output_sort_by, output_style, output_hidden)
    else:
        input_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # search button click
    if input_id == 'search-button':
    
        if tab == 'm':
            if (
                low_rf_i == None and 
                high_rf_i == None and 
                low_lo_i == None and 
                high_lo_i == None and 
                low_if_i == None and 
                high_if_i == None and 
                low_lodr_i == None and 
                high_lodr_i == None
            ):
                return ([], [], [], output_error, output_error_display, 
                        output_sort_by, output_style, output_hidden)

            inputs = mixer_true_input_values(low_rf_i, high_rf_i, low_lo_i, high_lo_i, low_if_i, high_if_i, low_lodr_i, high_lodr_i)

            low_rf, high_rf, low_lo, high_lo, low_if, high_if, low_lodr, high_lodr = inputs

            low_freq, high_freq = mixer_true_rflo_range(low_rf, high_rf, low_lo, high_lo)

            if ((low_rf != None and low_rf > high_rf) or 
                (low_lo != None and low_lo > high_lo) or 
                (low_if != None and low_if > high_if) or 
                (low_lodr != None and low_lodr > high_lodr)):

                return ([],[],[],'ENTER VALID LOW TO HIGH RANGE', True, 
                        output_sort_by, output_style, output_hidden)

            classname = M
        else:
            if (low_freq_i == None and high_freq_i == None):
                return ([], [], [], output_error, output_error_display, 
                        output_sort_by, output_style, output_hidden)

            inputs = true_input_values(low_freq_i, high_freq_i)

            low_freq, high_freq = inputs

            if (low_freq != None and low_freq > high_freq):
                return ([],[],[],'ENTER VALID LOW TO HIGH RANGE', True, 
                        output_sort_by, output_style, output_hidden)
            
            if tab == 'a':
                classname = A
            elif tab == 'pd':
                classname = PD
            elif tab == 'co':
                classname = CO
            elif tab == 'b':
                classname = B

        global LOW_FREQ,HIGH_FREQ
        LOW_FREQ, HIGH_FREQ = low_freq, high_freq

        products = search_products(classname, inputs)

        product_ids = []

        for p in products:
            product_ids.append(p['id'])

        searched_objects = manage_load(product_ids, classname)
        global SEARCHED_PRODUCT_OBJECTS
        SEARCHED_PRODUCT_OBJECTS = searched_objects

        if tab == 'm':
            products_table_data = m_table_data(searched_objects, sort_value, low_freq, high_freq)
        elif tab == 'a':
            products_table_data = amp_table_data(searched_objects, low_freq, high_freq)
        elif tab == 'pd':
            products_table_data = pd_table_data(searched_objects, low_freq, high_freq)
        elif tab == 'co':
            products_table_data = co_table_data(searched_objects, low_freq, high_freq)
        elif tab == 'b':
            products_table_data = ba_table_data(searched_objects, low_freq, high_freq)

        return (products_table_data, [],[], output_error, output_error_display, 
                output_sort_by, output_style, output_hidden)

    # radio button or table sort interact
    elif input_id == 'sort-options' or input_id == 'products-table':
        if tab == 'm':
            if sort_value == 'mn':
                col = 'model'
                colsort = 'model'
                dir = 'asc'
                output_hidden =['iip3-min', 'iip3-med', 'iip3-max', 
                                'lr-iso-min', 'lr-iso-med', 'lr-iso-max',
                                'cl-med-v', 'iip3-med-v', 'lr-iso-med-v', 'high-rf']
            elif sort_value == 'll':
                col = 'cl-med'
                colsort = 'cl-med-v'
                dir = 'desc'
                output_hidden =['iip3-min', 'iip3-med', 'iip3-max', 
                                'lr-iso-min', 'lr-iso-med', 'lr-iso-max',
                                'cl-med-v', 'iip3-med-v', 'lr-iso-med-v', 'high-rf']
            elif sort_value == 'bl':
                col = 'iip3-med'
                colsort = 'iip3-med-v'
                dir = 'desc'
                output_hidden =['cl-min', 'cl-med', 'cl-max', 
                                'lr-iso-min', 'lr-iso-med', 'lr-iso-max',
                                'cl-med-v', 'iip3-med-v', 'lr-iso-med-v', 'high-rf']
            elif sort_value == 'bi':
                col = 'lr-iso-med'
                colsort = 'lr-iso-med-v'
                dir = 'asc'
                output_hidden =['cl-min', 'cl-med', 'cl-max',
                                'iip3-min', 'iip3-med', 'iip3-max',
                                'cl-med-v', 'iip3-med-v', 'lr-iso-med-v', 'high-rf']
            output_sort_by = [{'column_id': colsort, 'direction': dir}]
            output_style = [{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(230, 230, 230)',},
                        {'if': {'column_id': col},'backgroundColor': COLOR['blue'],},
                        #{'if': {'column_id': 'datasheet'},'color': COLOR['blue'],'fontStyle': 'italic', 'textDecoration': 'underline'},
                        ]
            output_data = m_table_data(SEARCHED_PRODUCT_OBJECTS, sort_value, LOW_FREQ, HIGH_FREQ)
            if 'p1db' not in checklist_values:
                output_hidden.append('p1db')
        elif tab == 'a':
            output_sort_by=[{'column_id': 'model','direction': 'asc'}]
            output_style=cur_style
        elif tab == 'pd':
            if sort_value == 'mn':
                col = 'model'
                colsort = 'model'
                dir = 'asc'
            elif sort_value == 'll':
                col = 'il-med'
                colsort = 'il-med-v'
                dir = 'desc'
            output_sort_by = [{'column_id': colsort, 'direction': dir}]
            output_style = [{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(230, 230, 230)',},
                        {'if': {'column_id': col},'backgroundColor': COLOR['blue'],},
                        #{'if': {'column_id': 'datasheet'},'color': COLOR['blue'],'fontStyle': 'italic', 'textDecoration': 'underline'},
                        ]
            output_data = pd_table_data(SEARCHED_PRODUCT_OBJECTS, LOW_FREQ, HIGH_FREQ)
        elif tab == 'co':
            output_sort_by=[{'column_id': 'model','direction': 'asc'}]
            output_style=cur_style
        elif tab == 'b':
            if sort_value == 'mn':
                col = 'model'
                colsort = 'model'
                dir = 'asc'
            elif sort_value == 'll':
                col = 'il-med'
                colsort = 'il-med-v'
                dir = 'desc'
            output_sort_by = [{'column_id': colsort, 'direction': dir}]
            output_style = [{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(230, 230, 230)',},
                        {'if': {'column_id': col},'backgroundColor': COLOR['blue'],},
                        #{'if': {'column_id': 'datasheet'},'color': COLOR['blue'],'fontStyle': 'italic', 'textDecoration': 'underline'},
                        ]
            output_data = ba_table_data(SEARCHED_PRODUCT_OBJECTS, LOW_FREQ, HIGH_FREQ)
    
    # settings checklist
    elif input_id == 'settings-checklist':
        if tab == 'm':
            if sort_value == 'mn':
                output_hidden =['iip3-min', 'iip3-med', 'iip3-max', 
                                'lr-iso-min', 'lr-iso-med', 'lr-iso-max',
                                'cl-med-v', 'iip3-med-v', 'lr-iso-med-v', 'high-rf']
            elif sort_value == 'll':
                output_hidden =['iip3-min', 'iip3-med', 'iip3-max', 
                                'lr-iso-min', 'lr-iso-med', 'lr-iso-max',
                                'cl-med-v', 'iip3-med-v', 'lr-iso-med-v', 'high-rf']
            elif sort_value == 'bl':
                output_hidden =['cl-min', 'cl-med', 'cl-max', 
                                'lr-iso-min', 'lr-iso-med', 'lr-iso-max',
                                'cl-med-v', 'iip3-med-v', 'lr-iso-med-v', 'high-rf']
            elif sort_value == 'bi':
                output_hidden =['cl-min', 'cl-med', 'cl-max',
                                'iip3-min', 'iip3-med', 'iip3-max',
                                'cl-med-v', 'iip3-med-v', 'lr-iso-med-v', 'high-rf']
            if 'p1db' not in checklist_values:
                output_hidden.append('p1db')

    return (output_data, output_selected_rows, output_selected_ids, output_error,
            output_error_display, output_sort_by, output_style, output_hidden)


'''
=============================================================================
Product Functions
=============================================================================
'''

# gather info to put on product datatable
def ba_table_data(searched_objects, low, high):
    product_table_data = []
    
    for p in searched_objects:
        d = p.get_col_data()

        if low != high:
            min,max,med,bmin,bmax,bmed = p.getystats(low,high, balun.IL)
            if min == None:
                d['il-min'] = '---'
                d['il-max'] = '---'
                d['il-med'] = '---'
                d['il-med-v'] = None
            elif bmin == None:
                d['il-min'] = f'{min:.2f}'
                d['il-max'] = f'{max:.2f}'
                d['il-med'] = f'{med:.2f}'
                d['il-med-v'] = med
            else:
                d['il-min'] = f'{min:.2f} ({bmin:.2f})'
                d['il-max'] = f'{max:.2f} ({bmax:.2f})'
                d['il-med'] = f'{med:.2f} ({bmed:.2f})'
                d['il-med-v'] = med

            min,max,med,bmin,bmax,bmed = p.getystats(low,high, balun.AMP_B)
            d['ab-min'] = min
            d['ab-max'] = max
            d['ab-med'] = med

            min,max,med,bmin,bmax,bmed = p.getystats(low,high, balun.PH_B)
            d['pb-min'] = min
            d['pb-max'] = max
            d['pb-med'] = med
        else:
            d['il-min'] = '---'
            d['il-max'] = '---'
            d['il-med'] = '---'
            d['il-med-v'] = None
            d['ab-min'] = '---'
            d['ab-max'] = '---'
            d['ab-med'] = '---'
            d['pb-min'] = '---'
            d['pb-max'] = '---'
            d['pb-med'] = '---'

        d['stock'] = 0
        d['datasheet'] = f'[link]({p.datasheet})'
        product_table_data.append(d)
    
    return product_table_data

# gather info to put on product datatable
def co_table_data(searched_objects, low, high):
    product_table_data = []
    for p in searched_objects:
        d = p.get_col_data()

        d['stock'] = 0
        d['datasheet'] = f'[link]({p.datasheet})'
        product_table_data.append(d)
    
    return product_table_data

# gather info to put on product datatable
def pd_table_data(searched_objects, low, high):
    product_table_data = []
    
    for p in searched_objects:
        d = p.get_col_data()

        if low != high:
            min,max,med,bmin,bmax,bmed = p.getystats(low,high, powdiv.IL)
            if min == None:
                d['il-min'] = '---'
                d['il-max'] = '---'
                d['il-med'] = '---'
                d['il-med-v'] = None
            elif bmin == None:
                d['il-min'] = f'{min:.2f}'
                d['il-max'] = f'{max:.2f}'
                d['il-med'] = f'{med:.2f}'
                d['il-med-v'] = med
            else:
                d['il-min'] = f'{min:.2f} ({bmin:.2f})'
                d['il-max'] = f'{max:.2f} ({bmax:.2f})'
                d['il-med'] = f'{med:.2f} ({bmed:.2f})'
                d['il-med-v'] = med

            min,max,med,bmin,bmax,bmed = p.getystats(low,high, powdiv.AMP_B)
            d['ab-min'] = min
            d['ab-max'] = max
            d['ab-med'] = med

            min,max,med,bmin,bmax,bmed = p.getystats(low,high, powdiv.PH_B)
            d['pb-min'] = min
            d['pb-max'] = max
            d['pb-med'] = med
        else:
            d['il-min'] = '---'
            d['il-max'] = '---'
            d['il-med'] = '---'
            d['il-med-v'] = None
            d['ab-min'] = '---'
            d['ab-max'] = '---'
            d['ab-med'] = '---'
            d['pb-min'] = '---'
            d['pb-max'] = '---'
            d['pb-med'] = '---'

        d['stock'] = 0
        d['datasheet'] = f'[link]({p.datasheet})'
        product_table_data.append(d)
    
    return product_table_data

# gather info to put on product datatable
def amp_table_data(searched_objects, low, high):
    product_table_data = []
    for p in searched_objects:
        d = p.get_col_data()

        d['stock'] = 0
        d['datasheet'] = f'[link]({p.datasheet})'
        product_table_data.append(d)
    
    return product_table_data

#Gather info to put on product datatable
def m_table_data(searched_mixer_objects, sort, low, high):
    product_table_data = []

    for p in searched_mixer_objects:
        d = p.get_col_data()

        if low != high:
            if sort == 'll' or sort == 'mn':
                min,max,med,bmin,bmax,bmed = p.getystats(low,high, M.graph_options[m.CL_INDEX])
                if min == None:
                    d['cl-min'] = '---'
                    d['cl-max'] = '---'
                    d['cl-med'] = '---'
                    d['cl-med-v'] = None
                elif bmin == None:
                    d['cl-min'] = f'{min:.1f}'
                    d['cl-max'] = f'{max:.1f}'
                    d['cl-med'] = f'{med:.1f}'
                    d['cl-med-v'] = med
                else:
                    d['cl-min'] = f'{min:.1f} ({bmin:.1f})'
                    d['cl-max'] = f'{max:.1f} ({bmax:.1f})'
                    d['cl-med'] = f'{med:.1f} ({bmed:.1f})'
                    d['cl-med-v'] = med
            elif sort == 'bl':
                min,max,med,bmin,bmax,bmed = p.getystats(low,high, M.graph_options[m.IIP3_INDEX])
                if min == None:
                    d['iip3-min'] = '---'
                    d['iip3-max'] = '---'
                    d['iip3-med'] = '---'
                    d['iip3-med-v'] = None
                elif bmin == None:
                    d['iip3-min'] = f'{min:.0f}'
                    d['iip3-max'] = f'{max:.0f}'
                    d['iip3-med'] = f'{med:.0f}'
                    d['iip3-med-v'] = med
                else:
                    d['iip3-min'] = f'{min:.0f} ({bmin:.0f})'
                    d['iip3-max'] = f'{max:.0f} ({bmax:.0f})'
                    d['iip3-med'] = f'{med:.0f} ({bmed:.0f})'
                    d['iip3-med-v'] = med
            elif sort == 'bi':
                min,max,med,bmin,bmax,bmed = p.getystats(low,high, M.graph_options[m.LORF_ISO_INDEX])
                if min == None:
                    d['lr-iso-min'] = '---'
                    d['lr-iso-max'] = '---'
                    d['lr-iso-med'] = '---'
                    d['lr-iso-med-v'] = None
                elif bmin == None:
                    d['lr-iso-min'] = f'{min:.0f}'
                    d['lr-iso-max'] = f'{max:.0f}'
                    d['lr-iso-med'] = f'{med:.0f}'
                    d['lr-iso-med-v'] = med
                else:
                    d['lr-iso-min'] = f'{min:.0f} ({bmin:.0f})'
                    d['lr-iso-max'] = f'{max:.0f} ({bmax:.0f})'
                    d['lr-iso-med'] = f'{med:.0f} ({bmed:.0f})'
                    d['lr-iso-med-v'] = med
        else:
            d['cl-min'] = '---'
            d['cl-max'] = '---'
            d['cl-med'] = '---'
            d['cl-med-v'] = None
            d['iip3-min'] = '---'
            d['iip3-max'] = '---'
            d['iip3-med'] = '---'
            d['iip3-med-v'] = None
            d['lr-iso-min'] = '---'
            d['lr-iso-max'] = '---'
            d['lr-iso-med'] = '---'
            d['lr-iso-med-v'] = None

        d['stock'] = 0
        d['datasheet'] = f'[link]({p.datasheet})'

        d['rf-high-s'] = str(d['rf-high'])
        d['lo-high-s'] = str(d['lo-high'])

        bvalue = d['rf-high-b']
        if not numpy.isnan(bvalue):
            d['rf-high-s'] += f' ({bvalue})'

        bvalue = d['lo-high-b']
        if not numpy.isnan(bvalue):
            d['lo-high-s'] += f' ({bvalue})'

        product_table_data.append(d)

    return product_table_data


'''
==============================================================================
other MIXER Functions
==============================================================================
'''

#Fill in blank inputs for fixed-frequency searchs
def mixer_true_input_values(low_rf_i, high_rf_i, low_lo_i, high_lo_i, low_if_i, high_if_i, low_lodr_i, high_lodr_i):
    low_rf, high_rf = true_input_values(low_rf_i, high_rf_i)

    low_lo, high_lo = true_input_values(low_lo_i, high_lo_i)

    low_if, high_if = true_input_values(low_if_i, high_if_i)

    low_lodr, high_lodr = true_input_values(low_lodr_i, high_lodr_i)

    return (low_rf, high_rf, low_lo, high_lo, low_if, high_if, low_lodr, high_lodr)

#Find true min max frequencies for the separate RF and LO inputs
def mixer_true_rflo_range(low_rf, high_rf, low_lo, high_lo):
    if (low_rf == None and high_rf == None and
        high_lo == None and low_lo == None):
        return None, None
    
    low, high = None, None

    if low_rf != None:
        low, high = low_rf, low_rf

    if high_rf != None:
        if low == None:
            low, high = high_rf, high_rf
        else:
            if high_rf < low: low = high_rf
            if high_rf > high: high = high_rf
    
    if low_lo != None:
        if low == None:
            low, high = low_lo, low_lo
        else:
            if low_lo < low: low = low_lo
            if low_lo > high: high = low_lo

    if high_lo != None:
        if low == None:
            low, high = high_lo, high_lo
        else:
            if high_lo < low: low = high_lo
            if high_lo > high: high = high_lo
    
    return low, high

if __name__ == '__main__':
    #app.run_server(host='0.0.0.0', port=8080, debug=True)
    app.run_server(debug=True)