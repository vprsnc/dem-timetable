import pandas as pd
from datetime import date

import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash import dash_table
from dash.dependencies import Input, Output
import plotly.graph_objs as go

from mailwizz_parser import scrape_from_mailwizz


# Function for a week dropdown menu
def select_week(week, data):
    # the_day = date.today()
    # In normal case you would use the actual date, but since this is an expamle:
    the_day = '2021-01-15'
    today = pd.to_datetime(the_day).week
    # In normal case, the data should be scraped, but here we use csv
    # df = pd.DataFrame(data)
    df = data
    df["Planned"] = pd.to_datetime(df['Planned']).dt.floor('1H')
    df['Week'] = df['Planned'].dt.isocalendar().week
    df['WeekDay'] = df['Planned'].dt.day_name()
    df['DayTime'] = df['Planned'].dt.time
    df = df[df['Week'] == today - week]
    return df


# Function for a server selection dropdown menu
def select_server(data, servername, week):
    df = pd.DataFrame(data)
    match servername:
        case 'ALL':
            return df
        case 'expotorussia':
            mask = df[
                'Campaign'].str.contains(
                    r'\b{}\b'.format('|'.join(available_servers.values()))
                    )
            dff = df[~mask]
            return dff
        case _:
            mask = df[
                'Campaign'
            ].str.contains(f'{servername}', case=False)
            dff = df[mask]
            return dff


# Function for building a pivot table organising data by weekday and hour of the day
def build_timetable(data):
    df = pd.DataFrame(data)
    timetable = df.pivot_table(
        index="DayTime",
        columns="WeekDay",
        values="Campaign",
        aggfunc=lambda x: "; ".join([str(v) for v in x])
    )
    try:
        timetable.insert(0, 'Monday', '', allow_duplicates=False)
    except ValueError:
        pass
    try:
        timetable.insert(1, 'Tuesday', '', allow_duplicates=False)
    except ValueError:
        pass
    try:
        timetable.insert(2, 'Wednesday', '', allow_duplicates=False)
    except ValueError:
        pass
    try:
        timetable.insert(3, 'Thursday', '', allow_duplicates=False)
    except ValueError:
        pass
    try:
        timetable.insert(4, 'Friday', '', allow_duplicates=False)
    except ValueError:
        pass

    timetable = timetable[
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    ].fillna('')
    timetable.reset_index(inplace=True)

    return timetable


# Pivot table summarizing data for the whole week seleted
def create_week_report(data):
    df = pd.DataFrame(data)
    df = df[df['Campaign'].str.contains(r'\.') == False]
    df = df[df['Opens'] != 'N/A']

# Usually scraped data contains campaign numbers in
# format like "200 (100%)"
#    columns = ['Opens', 'Clicks', 'Bounces', 'Unsubs']
#    for column in columns:
#        df[f'{column}'] = df[f'{column}'].str.split(' ', expand=True)[
#                                                    0].astype(int)

    df['Sent'] = df['Sent'].astype(int)
    df['Language'] = ''

    languages = ['English', 'Spain', 'France', 'Germany', 'Italy']
    for language in languages:
        df.loc[
            df['Campaign'].str.contains(f'{language}'), 'Language'
        ] = f'{language}'
    weektable = pd.pivot_table(
        df, ['Sent', 'Opens', 'Clicks', 'Bounces', 'Unsubs'],
        'Language', aggfunc='sum')
    weektable.reset_index(inplace=True)
    weektable = weektable[
            ['Language', 'Sent', 'Opens', 'Clicks', 'Bounces', 'Unsubs']
            ]

    return weektable


# Pivot table for the Heatmap represening load on a server by hour
def create_server_load(data):
    df = pd.DataFrame(data)
    df = df[df['Opens'] != 'N/A']

    df['Sent'] = df['Sent'].astype(int)

    servertable = pd.pivot_table(
        df, 'Sent', ['WeekDay', 'DayTime'],
        aggfunc='sum'
    )
    servertable = servertable.reindex(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        level='WeekDay').fillna(0)
    servertable.reset_index(inplace=True)
    return servertable


# Options and values for week selection dropdown
available_weeks = {
    'Week 0': 0,
    'Week -1': 1,
    'Week -2': 2,
    'Week -3': 3,
    'Week 1': -1,
    'Week 2': -2,
}

# Options for server selection
available_servers = {
    "ALL": "ALL",
    "expotorussia": "expotorussia",
    "buyersinrussia": "NEWSERVER",
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.VAPOR])
server = app.server

# Defining how the dashboard gonna look like
app.layout = html.Div([
        html.Div(dcc.Store(id='weekstore')),
        html.H1("DEM REPORT", style={"text-align": "center"}),
        html.Br(),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Dropdown(id="weekselection", options=[
                                {"label": i, 'value': available_weeks[i]} for i in available_weeks
                                ], value=0, style={
                                'backgroundColor': 'rgb(68 217 232)',
                                'color': 'rgb(24, 4, 43)',
                                'width': '300px'}
                                ), width={'size': 3, 'offset': 6}
                            ),
                        dbc.Col(
                            dcc.Dropdown(id="serverselection", options=[
                                {"label": i, "value": available_servers[i]} for i in available_servers
                                ], value="ALL", style={
                                'backgroundColor': 'rgb(68 217 232)',
                                'color': 'rgb(24, 4, 43)',
                                'width': '300px'},),
                            width={'size': 3}
                            ),
                        html.Br(),
                        dbc.Row(
                            [
                                html.H2("TIMETABLE", style={
                                        "text-align": 'left'}),
                                dbc.Col(
                                    [
                                        html.Div(id="timetable")
                                        ], width={'size': 10, 'offset': 1}
                                    )
                                ]
                            ),
                        html.Br(),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H2("WEEK REPORT", style={
                                            "text-align": 'left'}),
                                        html.Div(id="weektable")
                                        ], width={'size': 6}
                                    ),
                                dbc.Col(
                                    [
                                        html.H2("SERVER LOAD", style={
                                            "text-align": 'left'}),
                                        dcc.Graph(id='serverload', config={
                                            'displayModeBar': False})
                                        ], width={'size': 6}
                                    )
                                ]
                            ),
                        html.Br(),
                        ]
                    )
                ]

            )
        ]
    )


# Inital data collection, will be stored and available for other collbacks
@app.callback(
    Output('weekstore', 'data'),
    [Input('weekselection', 'value'),
     Input('serverselection', 'value')]
    )
def collect_timetable(week, servername):
    # Run the parser:
    # scraped = scrape_from_mailwizz()
    scraped = pd.read_csv('campaigns.csv', sep=';')
    # Filter the data to apply for needed week and server:
    data = select_week(week=week, data=scraped)
    df = select_server(data, servername, week)
    # Let the data be available for other callbacks, which are unavailable
    # of readding Pandas DataFrame
    return df.to_dict('records')


@app.callback(
    Output('timetable', 'children'),
    Input('weekstore', 'data'),
    )
def update_timetable(data):
    timetable = build_timetable(data)
    datatable = dash_table.DataTable(
        columns=[{'name': i, 'id': i} for i in timetable.columns],
        style_cell={
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0
        },
        style_header={
            'backgroundColor': 'rgb(234 57 183)',
            'color': 'white'
        },
        style_data={
            'backgroundColor': 'rgb(26 8 51)',
            'color': 'white'
        },
        data=timetable.to_dict('records'),
        tooltip_data=[
            {
                column: {'value': str(value), 'type': 'markdown'}
                for column, value in row.items()
            } for row in timetable.to_dict('records')
        ],
        css=[{
            'selector': '.dash-table-tooltip',
            'rule': 'background-color: rgb(49, 17, 94);'
        }]
    )
    return datatable


@app.callback(
    Output('weektable', 'children'),
    Input('weekstore', 'data')
)
def update_weekreport(data):
    weektable = create_week_report(data)
    datatable = dash_table.DataTable(
        columns=[{'name': i, 'id': i} for i in weektable.columns],
        style_cell={
            'whiteSpace': 'normal',
            # 'height': 'auto',
            'padding': '5px'
        },
        style_header={
            'backgroundColor': 'rgb(234 57 183)',
            'color': 'white'
        },
        style_data={
            'backgroundColor': 'rgb(26 8 51)',
            'color': 'white'
        },
        style_as_list_view=True,
        data=weektable.to_dict('records'),
    )
    return datatable


@app.callback(
    Output('serverload', 'figure'),
    Input('weekstore', 'data')
)
def build_server_load(data):
    df = pd.DataFrame(data)
    servertable = create_server_load(df)
    fig = go.Figure(
        data=go.Heatmap(
            x=servertable['WeekDay'],
            y=servertable['DayTime'],
            z=servertable['Sent'],
            colorscale='Plotly3',
            zmin=0,
            zmax=500
        )
    )
    fig.update_layout(
        width=500, height=400, plot_bgcolor='rgb(0, 0, 0, 0)',
        paper_bgcolor=('rgb(0, 0, 0, 0)'),
        font_color='rgb(51, 251, 226)'
    )
    fig.update_xaxes(tickangle=-45)
    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
