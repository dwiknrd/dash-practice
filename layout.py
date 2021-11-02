import base64
import datetime
import io

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table

import dash_auth

import plotly.graph_objs as go
from plotly.offline import iplot
import plotly.express as px

import pandas as pd

data = pd.read_csv('hotel_booking_clean.csv')
data['arrival_date'] = data['arrival_date'].astype('datetime64')
data[['hotel', 'is_canceled']] = data[['hotel', 'is_canceled']].astype('category')

data['arrival_month'] = data['arrival_date'].dt.month_name()

month = ['January','February','March','April','May','June','July','August','September','October','November','December']

no_canceled = data[data['is_canceled'] == 0]

df = no_canceled[['hotel', 'arrival_date']]

## Most Busy Month
final_rush = pd.crosstab(index=no_canceled['arrival_month'],
            columns=no_canceled['hotel'])

final_rush = final_rush.reindex(month)


## Month Highest ADR
adr_month_hotel =  data.groupby(['arrival_month', 'hotel']).mean()['adr'].round(2).reset_index()
adr_month_hotel['arrival_month'] = pd.Categorical(adr_month_hotel['arrival_month'], categories = month)
adr_month_hotel = adr_month_hotel.sort_values('arrival_month')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {'background': '#CAB3C1',
            'text': '#2E3332'}

header = '''

The hotel booking demand dataset is originally from the article [Hotel Booking Demand Datasets](https://www.sciencedirect.com/science/article/pii/S2352340918315191), written by Nuno Antonio, Ana Almeida, and Luis Nunes for Data in Brief, Volume 22, February 2019. The data was downloaded and cleaned by Thomas Mock and Antoine Bichat.

'''

app.layout = html.Div(children=[
    html.H1('Dashboard', style={'textAlign':'center',
                                    'color':colors['text']}),
    html.Div('Hotel Bookings', style={'textAlign':'center',
                                                    'color':colors['text']}),
    dcc.Markdown(children=header, style={'color':colors['text']}),
    dcc.Graph(
        id='busy-month',
        figure={
            'data': [
                go.Scatter(
                        x = final_rush.index,
                        y = final_rush['City Hotel'],
                        mode = 'lines+markers',
                        marker = {
                            'size': 12,
                            'color': '#B7EAF7',
                            'symbol': 'star',
                            'line': {'width': 2}
                        },
                        name = 'City Hotel'),
                go.Scatter(
                        x = final_rush.index,
                        y = final_rush['Resort Hotel'],
                        mode = 'lines+markers',
                        marker = {
                            'size': 12,
                            'color': '#F3BFB3',
                            'symbol': 'pentagon',
                            'line': {'width': 2}
                        },
                        name = 'Resort Hotel')
            ],
            'layout': {
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {
                    'color': colors['text']
                },
                'title': 'The Most Busy Month'
            }
        }
    ),
    
    dcc.Graph(
        id='highest-adr',
        figure=px.bar(
            adr_month_hotel,
            x = 'arrival_month',
            y = 'adr',
            color = 'hotel',
            color_discrete_sequence = ['#E0F8F5', '#B7EAF7'],
            barmode = 'group',
            labels = {
                'arrival_month': 'Month',
                'hotel': 'Hotel',
                'adr': 'Average Daily Rate'
            }
        )
    ),

    dash_table.DataTable(
        id='table-no-cancel',
        columns=[{'name':i, 'id':i} for i in df.columns],
        data=df.head().to_dict('records')
    ),

    html.Button('Download Hotel Dataset', id='button_csv'),
    dcc.Download(id='download-data-csv'),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and drop your file or ',
            html.A('select a file')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    html.Div(id='output-data-upload'),

],
style={'backgroundColor': colors['background']}
)



def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns]
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

@app.callback(
    Output("download-data-csv", "data"),
    Input("button_csv", "n_clicks"),
    prevent_initial_call=True,
)

def download_csv(n_clicks):
    return dcc.send_data_frame(df.to_csv, 'no_cancel_bookings.csv')

@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))

def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

if __name__ == '__main__':
    app.run_server()
