import base64
from io import StringIO
import pandas as pd
import numpy as np

# Diese Werte und entsprechende Einheiten werden später bei onMarkerHover angezeigt
markerDict = {"PM1.0" : "μg/m^3", "PM2.5" : "μg/m^3", "PM10" : "μg/m^3",
                "Temperature" : "°C", "Humidity" : "%", "Pressure" : "hPa",
                "Acc-X" : "m/s^2", "Acc-Y" : "m/s^2", "Acc-Z" : "m/s^2",
                "CO2" : "ppm", "Time" : None, "Date" : None,
                "Fix" : None, "Quality" : None, 
                "Voltage" : "V", "Current" : "mA", "Power" : "mW",
                "Speed" : "km/h", "Angle" : "°", "Altidude" : "m GND" , "Satellites" : None

}

markerLayout = ""
for key, value in zip(markerDict.keys(), markerDict.values()):
    if value is None:
        value = ""
    markerLayout += key + ":   {} " + value + "<br>"


columns2Extract = list(markerDict.keys())

# Datentypen für die einzelnen Columns
# nicht gebraucht -> pd.to_numeric: wandelt sattelites aber in float ????
columnsDtypes = {
    "PM1.0" : int, "PM2.5" : int, "PM10" : int,
    "Temperature" : float, "Humidity" : float, "Pressure" : float,
    "Acc-X" : float, "Acc-Y" : float, "Acc-Z" : float,
    "CO2" : int, "Time" : None, "Date" : None,
    "Fix" : int, "Quality" : int, 
    "Voltage" : float, "Current" : float, "Power" : float,
    "Speed" : float, "Angle" : float, "Altidude" : float , "Satellites" : int
}

def Gradmin2Dez(value):
    value = value.replace("N", "").replace("E", "")
    return float(value)//100 + float(value)%100/60

def Knots2Kmh(value):
    return float(value)/1.852

def Upload2Df(contents, filename, date):
    content_type, content_string = contents.split(',')

    content_string = content_string.replace(" ", "")

    decoded = base64.b64decode(content_string)

    df = pd.read_csv(StringIO(decoded.decode('utf-8')), delimiter = ";", skipinitialspace=True)

    return df

def ParseCsv(df, dropna = True):

    df.columns = df.columns.str.replace(' ', '')


    if dropna:
        df = df.dropna()
    
    df = df.rename({"Location" : "Lat", "Location.1" : "Lon", "Speed(knots)" : "Speed"}, axis = "columns")



    # Einzelne Aufnahmen als Liste aus dataframes speichen
    # Index der Überschriften Zeilen finden
    idx = df.index[df["PM1.0"] == "PM1.0"]

    runs = []

    if len(idx) == 0:
        runs.append(df)
    else:
        runs.append(df.loc[:idx[0]-1])

        for i in range(len(idx)):
            if i == len(idx) - 1:
                runs.append(df.loc[idx[i]+1:])
            else:
                runs.append(df.loc[idx[i] + 1:idx[i+1] - 1])

    # Leere Frames Raushauen
    runs = [run for run in runs if not run.empty]

    # Koordinaten von Gradminuten in Dezimalgrad und 
    # Geschwindigkeit von Knoten in km/h umrechnen
    # Geht erst jetzt da zuvor die Header eine neue Messung "begrenzen"
    # Numerische Spaltennamen für Umwandlung in entsprechende Datentypen
    columns = [column for column in df.columns if column not in ["Time", "Date"]]
    for run in runs:
        run["Lat"] =  run["Lat"].apply(Gradmin2Dez)
        run["Lon"] =  run["Lon"].apply(Gradmin2Dez)
        run["Speed"] = run["Speed"].apply(Knots2Kmh)
        run[columns] = run[columns].apply(pd.to_numeric)
        run.reset_index(drop = True, inplace = True)


    return runs


def Df2MarkerString(df):

    dfMarker = df[columns2Extract]
    markerTextList = []

    for index, row in dfMarker.iterrows():
        markerTextList.append(markerLayout.format(*list(row.values)))

    return markerTextList


from math import radians, cos, sin, asin, sqrt

#creds: Michael Dunn https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
    return c * r


def CalcHexNumber(data, inCircleDia):
    """Berechnet die Anzahl der Hexagone in x-Richtung für plotly.figure_factory.create_hexbin_mapbox

    Args:
        data ([dict]): [Das dict mit den Daten]
        inCircleDia ([type]): [Der gewünschte Inkreisdurchmesser der Hexagone in m]

    Returns:
        [int]: [Anzahl der Hexagone]
    """
    # np.min soll schneller sein als pd.dataframe.min

    minCords = pd.DataFrame()
    maxCords = pd.DataFrame()

    # Lat und Lon für min/max(Lon) von jedem Run
    for runs in data.values():
        for run in runs["runs"]:
        
            minCords = minCords.append(run.iloc[[run["Lon"].idxmin()]][["Lon", "Lat"]], ignore_index=True)
            maxCords = maxCords.append(run.iloc[[run["Lon"].idxmax()]][["Lon", "Lat"]], ignore_index=True)



    # Lat und Lon für min/max(Lon) vom gesamten min/max
    minCord = minCords.iloc[minCords["Lon"].idxmin()].values
    maxCord = maxCords.iloc[maxCords["Lon"].idxmax()].values
    
    # Der einfachheit halber Mittelwert der beiden Breitengrade nehmen um nur Ost-West Distanz zu bekommen
    meanLat = np.mean([minCord[1], maxCord[1]]) # np.mean([maxLon, minLon])
    
    dist = haversine(minCord[0], meanLat, maxCord[0], meanLat)

    nHex = round(dist / (inCircleDia/1000))
    
    return nHex