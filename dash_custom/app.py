"""

Created Date: Monday December 28th 2021
Author: hafa1029
-----
Last Modified:
Modified By:
-----
Based on: https://github.com/plotly/dash-sample-apps/tree/main/apps/dash-uber-rides-demo


To do: 
- Hexbinmap wenn keine Werte angezeigt werden, einfach leere Map erstellen?
  aktuell wird einfach die leere Tripmap genommen
- Colorscale für scattermabbox -> var tripMap
    bei add_trace ? 
    hochgeladene run-traces werden in HandleUpload() hinzugefügt
    habs kurz probiert, will aber irgendwie nicht
    -> vllt einfach für die Tripmap weglassen? -> radio auswahl bei tripmap wegmachen
    

"""


import dash
from dash import dcc
from dash import html
import json

import pandas as pd
import numpy as np
import pathlib
import os
from helpers import (
    ParseCsv, 
    Df2MarkerString,
    Upload2Df,
    CalcHexNumber,
    markerDict,
)

from dash.dependencies import Input, Output, State
from plotly import graph_objs as go
from plotly.graph_objs import *
import plotly.figure_factory as ff
from datetime import datetime as dt
import dash_bootstrap_components as dbc

""""""""""""""""""""""""" Einstellungen """""""""""""""""""""""""

hexIncircleDia = 50 # m


""""""""""""""""""""""""" App """""""""""""""""""""""""
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
app.title = "Fine dust measuring system map"
server = app.server

# Plotly mapbox public token, nicht genutzt
# mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"


""""""""""""""""""""""""" Demo Data """""""""""""""""""""""""
APP_PATH = str(pathlib.Path(__file__).parent.resolve())

df = pd.read_csv(os.path.join(APP_PATH, os.path.join("data", "demo.csv")),  delimiter = ";", skiprows = 1, skipinitialspace=True)

demoRun = ParseCsv(df)
demoRun = demoRun[0]


""""""""""""""""""""""""" Map_Figure_Variabeln """""""""""""""""""""""""

# Hier werden alle csvs mit ihren Daten in dieser Form gespeichert, zum Start die demo.csv reinschreiben
data = {
    "demo.csv" : {
        "dropdown" : {
            "label" : "demo.csv",
            "value" : "demo.csv"
        },
        "runs" :[demoRun]
    },
}

# Df mit den gesammelten Daten
meanDf = pd.DataFrame(data["demo.csv"]["runs"][0])


# Wertbereich für die Hexbinmap
colorRanges = {
    "PM1.0" : (0, 500),
    "PM2.5" : (0, 500),
    "PM10" : (0, 500),
    "Temperature" : (0, 50), # Wenn cmin negativ ist, werden weiße Punkte angezeigt?
    "Humidity" : (0, 100),
    "Pressure" : (926, 1100),
    "Acc-X" : None,
    "Acc-Y" : None,
    "Acc-Z" : None,
    "CO2" : (0, 1000),
    "Time" : None,
    "Date" : None,
    "Fix" : None,
    "Quality" : None,
    "Voltage" : None,
    "Current" : None,
    "Power"	: None,
    "Speed" : None,
    "Angle" : None,
    "Altidude" : None,
    "Satellites" : None, 
}

# Startmaps werden hier manuell erzeugt, besser wäre die Funktionen zu nutzen
tripMap =  go.Figure(
    go.Scattermapbox(
            mode = "markers+lines",
            showlegend=True,
            # lon = demoRun["Lon"],
            # lat = demoRun["Lat"],
            # marker = {'size': 10},
            # hovertext = Df2MarkerString(demoRun), 
            # name  = "demoRun"
        )
    )

tripMap.add_trace(go.Scattermapbox(
    mode = "markers+lines",
    lon = demoRun["Lon"],
    lat = demoRun["Lat"],
    marker = {'size': 10},
    hovertext = Df2MarkerString(demoRun), 
    name  = "demo.csv",
    uid = "demo.csv",
    )
)

tripMap.update_layout(
    paper_bgcolor="#31302F",
    mapbox_style="carto-darkmatter", 
    margin={"r":0,"t":25,"l":0,"b":0},
    mapbox = dict(
        center = dict(lat = demoRun["Lat"][0], lon = demoRun["Lon"][0]),
        zoom=10
        ),
    font_family="Open Sans",
    font_color="white",
)


meanMap = go.Figure(
    ff.create_hexbin_mapbox(
        data_frame=demoRun, lat="Lat", lon="Lon",
        nx_hexagon= CalcHexNumber(data, hexIncircleDia), 
        opacity=0.5, labels={"color": "PM1.0 " + markerDict["PM1.0"]},
        show_original_data=True,
        original_data_marker = {
            'size': 5,
            "opacity" : 0.9,
            "color": demoRun["PM1.0"],
            # "range_color" : colorRanges["PM1.0"]
            "cmin" : 0,
            "cmax" : 500,
            "colorscale" : "jet"
        },
        color="PM1.0",
        agg_func=np.mean,
        mapbox_style="carto-darkmatter",
        center = dict(lat = demoRun["Lat"][0], lon = demoRun["Lon"][0]),
        range_color = colorRanges["PM1.0"],
        color_continuous_scale = "jet"
    )
)

meanMap.update_layout(
    paper_bgcolor="#31302F",
    margin={"r":0,"t":25,"l":0,"b":0},
    font_family="Open Sans",
    font_color="white",
    )


# # Fehlermeldung falls Upload schief geht
# modal = html.Div(
#     [
#         dbc.Button("Open modal", id="open", n_clicks=0),
#         dbc.Modal(
#             [
#                 dbc.ModalHeader(dbc.ModalTitle("Header")),
#                 dbc.ModalBody("This is the content of the modal"),
#                 dbc.ModalFooter(
#                     dbc.Button(
#                         "Close", id="close", className="ms-auto", n_clicks=0
#                     )
#                 ),
#             ],
#             id="modal",
#             is_open=False,
#         ),
#     ]
# )

# Fehlermeldung mit dcc.ConfirmeDialog
uploadError = dcc.ConfirmDialog(
            id='upload-error',
            message='Something went wrong processing the uploaded data.\nData has to be a .csv file with the right format.',
)

""""""""""""""""""""""""" Inline Styles """""""""""""""""""""""""
# Tab Styles, aus css ausgelagert weil dort scheinbar nur tabs styling funktioniert
tabs_styles = {
    # "border" : None,
    "background" : "#31302F",
    'boxShadow': "#31302F",
    #'height': '44px'
    'borderBottom': '0px',
    #'border-radius': '4px'
}
tab_style = {
    'background' : '#1E1E1E',
    "color" : "grey", 
    'borderLeft': 'none',
    'borderRight': 'none',
    'borderTop': 'none',
}

tab_selected_style = {
    'background' : '#31302F',
    "color" : "white",
    'borderLeft': 'none',
    'borderRight': 'none',
    'borderTop': 'none',
    "borderBottom": "4px solid white",
}

upload_style = {
    'width': '100%',
    'height': '30px',
    'lineHeight': '30px',
    "fontSize" : "12px",
    'borderWidth': '1px',
    'borderStyle': 'dashed',
    'borderRadius': '5px',
    'textAlign': 'center',
    'margin': '10px',
}


""""""""""""""""""""""""" Layout """""""""""""""""""""""""
# Layout of Dash App
app.layout = html.Div(
    children=[
        html.Div(children = [
            uploadError,
        ]
        ),
        html.Div(
            className="row",
            children=[
                # Column for user controls
                html.Div(
                    className="three columns div-user-controls",
                    children=[
                        html.A(
                            html.Img(
                                className="logo",
                                src=app.get_asset_url("HKA_MMT_Logo_Gesamt-h_RGB.svg"),
                            ),
                            href="https://www.h-ka.de/",
                        ),
                        html.H2("Mobile fine dust measuring system"),
                        html.P(
                            """
                            A Energy Efficient Microcontrollers MEM242_2 project.
                            """
                        ),
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div([
                                'Drag and Drop or ',
                                html.A('Select csv')
                            ]),
                            style=upload_style,
                            # Allow multiple files to be uploaded
                            multiple=True
                        ),
                        dcc.Markdown(
                        """
                            Select csv's to be mapped
                        """
                        ),
                        dcc.Dropdown(
                            id="csv-select",
                            options=[data["demo.csv"]["dropdown"]],    # Startwerte
                            value=["demo.csv"],
                            multi=True,
                        ),
                        dcc.Markdown(
                            """
                            Links: 
                            [HIT Karlsruhe] (http://www.hit-karlsruhe.de/) |    
                            Feinstaub Messsystem [Mechanik] (http://hit-karlsruhe.de/hit-info/info-ws21/FMSM) | [Elektronik] (http://hit-karlsruhe.de/hit-info/info-ws21/FMSE) | [Software] (http://hit-karlsruhe.de/hit-info/info-ws21/FMSS)
                            
                            Credits for Layout: 
                            [xhlulu] (https://github.com/plotly/dash-sample-apps/tree/main/apps/dash-uber-rides-demo)
                            """,
                            style={'marginTop': 10} #, 'padding': '6px 0px 0px 8px'},
                        ),
                    ],
                ),
                # Column for app graphs and plots
                html.Div(
                    className="nine columns div-for-charts bg-grey",
                    children=[
                        dcc.Tabs(
                            id="map-tabs",
                            value="tab_trip_map",
                            parent_className='custom-tabs',
                            #className = "custom-tabs-container",
                            children=[
                                dcc.Tab(
                                    label="Trip map",
                                    value ="tab_trip_map",
                                    style=tab_style, 
                                    selected_style=tab_selected_style
                                    #className = "custom-tab"
                                ),
                                dcc.Tab(
                                    label="Mean map",
                                    value="tab_mean_map",
                                    style=tab_style, 
                                    selected_style=tab_selected_style
                                    #className = "custom-tab"
                                ),
                            ], 
                            style=tabs_styles

                        ),
                        html.Div(
                            [dcc.RadioItems(
                            options=[
                                {'label': 'PM1.0', 'value': 'PM1.0'},
                                {'label': 'PM2.5', 'value': 'PM2.5'},
                                {'label': 'PM10', 'value': 'PM10'},
                                {'label': 'CO2', 'value': 'CO2'},
                                {'label': 'Pressure', 'value': 'Pressure'},
                                {'label': 'Temperature', 'value': 'Temperature'},
                                {'label': 'Humidity', 'value': 'Humidity'},
                                
                            ],
                            value='PM1.0',
                            labelStyle={'display': 'none',
                                        "font-family" : "Open Sans"
                                        },
                            id = "value-radio",
                            ),
                            ],
                        ),
                        html.Div(
                            id="map-tabs-graph",
                        ),
                    ],
                ),
            ],
        )
    ]
)


def Insert2DataLayout(csvName, data):
    return {
            "dropdown" : {
                "label" : csvName,
                "value" : csvName,
            },
            "runs" : data
    }


# Upload
@app.callback(Output('csv-select', 'options'),
              Output("upload-error", "displayed"),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def HandleUpload(list_of_contents, list_of_names, list_of_dates):
    global meanDf
    global meanMap
    global data
    global tripMap
    
    # Dropdown aktualisieren
    if list_of_contents is not None:
        
        try:
            dataName = ""
            
            for content, name, date in zip(list_of_contents, list_of_names, list_of_dates):
                # Falls ein File mit gleichem Namen hochgeladen wird
                nameIterator = 1
                dataName = name
                while dataName in data.keys():
                    dataName = name + "_" + str(nameIterator)
                    nameIterator += 1

                # Csv verarbeiten und in data schreiben
                uploadedDf = Upload2Df(content, dataName, date)
                uploadedDf = ParseCsv(uploadedDf)
                data[dataName] = Insert2DataLayout(dataName, uploadedDf)


            # TripMap traces hinzufügen -> wird noch nicht angezeigt, erst wenn figure zu html.div returned wird       
            runIterator = 1
            
            for run in data[dataName]["runs"]:
                tripMap.add_trace(go.Scattermapbox(
                    mode = "markers+lines",
                    lon = run["Lon"],
                    lat = run["Lat"],
                    marker = {'size': 10},
                    hovertext = Df2MarkerString(run), 
                    name  = dataName + "_" + str(runIterator),
                    uid = dataName
                    )
                )
                
                runIterator += 1
                
                # Alle Daten sammeln für hexbinmap
                # meanDf = pd.concat([meanDf, run], ignore_index=True)

            # meanMap = go.Figure(
            #     ff.create_hexbin_mapbox(
            #         data_frame=meanDf, lat="Lat", lon="Lon",
            #         nx_hexagon= CalcHexNumber(data, hexIncircleDia), 
            #         opacity=0.5, labels={"color": "PM1.0"},
            #         show_original_data=True,
            #         original_data_marker = {
            #             'size': 5,
            #             "opacity" : 0.9,
            #             "color": meanDf["PM1.0"],
            #             # "range_color" : colorRanges["PM1.0"]
            #             "cmin" : 0,
            #             "cmax" : 500,
            #         },
            #         color="PM1.0",
            #         agg_func=np.mean,
            #         mapbox_style="carto-darkmatter",
            #         center = dict(lat = meanDf["Lat"][0], lon = meanDf["Lon"][0]),
            #         range_color = colorRanges["PM1.0"],
            #     )
            # )
            
            # meanMap.update_layout(
            # paper_bgcolor="#31302F",
            # margin={"r":0,"t":25,"l":0,"b":0})
            return [data[key]["dropdown"] for key in data.keys()], False
        except Exception as e:
            print(e)
            return [data[key]["dropdown"] for key in data.keys()], True
        
    


def UpdateTraceVisibility(trace, activeCsvs):
    # keine csv aktiv
    if not activeCsvs:
        trace.visible = False
    elif any(trace.uid == csv for csv in activeCsvs):
        trace.visible = True
    else:
        trace.visible = False
            




def CreateHexbinMap(value2Show):
    return go.Figure(
                ff.create_hexbin_mapbox(
                    data_frame=meanDf, lat="Lat", lon="Lon",
                    nx_hexagon= CalcHexNumber(data, hexIncircleDia), 
                    opacity=0.5, labels={"color": f"{value2Show} {markerDict[value2Show]}"},
                    show_original_data=True,
                    original_data_marker = {
                        'size': 5,
                        "opacity" : 0.9,
                        # "range_color" : colorRanges["PM1.0"]
                        "cmin" : colorRanges[value2Show][0],
                        "cmax" : colorRanges[value2Show][1], 
                        "color": meanDf[value2Show],
                        "colorscale" : "jet"
                    },
                    color=value2Show,
                    agg_func=np.mean,
                    mapbox_style="carto-darkmatter",
                    # center = dict(lat = meanDf["Lat"][0], lon = meanDf["Lon"][0]),
                    range_color = colorRanges[value2Show],
                    color_continuous_scale = "jet"
                )
            ).update_layout(
                paper_bgcolor="#31302F",
                margin={"r":0,"t":25,"l":0,"b":0},
                font_family="Open Sans",
                font_color="white",
                )


# Tabs
@app.callback(
    Output('map-tabs-graph', 'children'),
    Input('map-tabs', 'value'),
    Input('csv-select', 'value'),
    Input("value-radio", "value")
) # Es werden alle aktuellen Inputs eingegeben! Egal welcher Input den Callback ausgelöst hat
def UpdateShownMap(tab, dropdownVals, radioVal):
    global meanDf
    global meanMap
    global tripMap
    
    # welcher Input hat Event ausgelöst?
    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # csv Dropdown-input?
    if(button_id == "csv-select"):
        # Tripmap
        # gehe durch jeden Trace und checke ob sein Name in der Dropdownliste ist, sichtbar machen wenn ja, unsichtbar wenn nein
        tripMap.for_each_trace(
            lambda trace: UpdateTraceVisibility(trace, dropdownVals) #ctx.inputs["csv-select.value"])
            )
        
        # Meanmap
        # Aktive Daten sammeln für hexbinmap
        meanDfList = []
        
        for csv in dropdownVals:
            for run in data[csv]["runs"]:
                meanDfList.append(run)
        
        # Falls keine Daten angezeigt werden sollen
        if not meanDfList:
            # Leere Map erzeugen? Leere hexbin_mapbox wirft Fehler
            meanMap = tripMap # hack nimm tripMap?
        # Falls Daten angezeigt werden sollen
        else:    
            meanDf = pd.concat(meanDfList, ignore_index=True)
            
            meanMap = CreateHexbinMap(radioVal)

            
    # Radio input?
    elif (button_id == "value-radio"):
        tripMap.update_traces(marker = {
            "cmin" : colorRanges[radioVal][0],
            "cmax" : colorRanges[radioVal][1]
            }
        )
        
        meanMap = CreateHexbinMap(radioVal)

    # uirevision auf irgendeinen Wert setzen um Position und Zoom der Karte bei Update beizubehalten
    # Klappt aber nicht bei Wechseln der Tabs
    meanMap["layout"]["uirevision"] = "something" 
    tripMap["layout"]["uirevision"] = "something" 

    # Return anhand offenem Map Tab
    if tab == 'tab_trip_map':
        return html.Div(
            children = dcc.Graph(
                id = "map_trip",
                figure = tripMap,
                style={"height": "89vh"}, 
                ),
            )
    elif tab == 'tab_mean_map':
        return html.Div([
            dcc.Graph(
                id = "map_mean",      
                figure = meanMap,
                style={"height": "89vh"}, 
            )
    ])


# Tabs
@app.callback(
    Output('value-radio', 'labelStyle'),
    Input('map-tabs', 'value'),
)
def SwitchRadioVisibility(tab):
    if tab == 'tab_trip_map':
        return {"display" : "none"}
    elif tab == 'tab_mean_map':
        return {"display" : "inline-block"}
    

if __name__ == "__main__":
    app.run_server(debug=False)


# # Error bei Upload
# @app.callback(
#     Output("modal", "is_open"),
#     [Input("open", "n_clicks"), Input("close", "n_clicks")],
# )
# def toggle_modal(n1, n2, is_open):
#     print("modal")
#     if n1 or n2:
#         return not is_open
#     return is_open