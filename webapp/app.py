from flask import Flask, render_template, request
from flask import Flask, url_for, render_template, redirect
from forms import weatherForm, weatherResultForm
import requests
import os
import xml.etree.ElementTree as ET

app = Flask(__name__)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

awcAPI = 'https://www.aviationweather.gov/adds/dataserver_current/httpparam?'
awcStationInfo = "dataSource=stations&requestType=retrieve&format=xml&stationString="
awcCurrentWeather = 'dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=2&mostRecent=true&stationString='
awcRadialWeather = "dataSource=stations&requestType=retrieve&format=xml&radialDistance="

#Function that retreives current raw METAR data at given airport
def getWeather(aptcode):
    reqGetCurrentWx = requests.get(awcAPI+awcCurrentWeather+aptcode)

    if(reqGetCurrentWx.status_code == 200):
        root = ET.fromstring(reqGetCurrentWx.content)
        
        for child in root.iter(tag = 'raw_text'):
            getWeather.MetarRaw = child.text
    else:
        print("FAILED. Status Code: " + reqGetCurrentWx.status_code)

#Function that retreives current raw METAR data from a 25nm radius of given airport
def getRadiusWeather(aptcode):
    getRadiusWeather.AllStations = []

    reqGetStationInfo = requests.get(awcAPI+awcStationInfo+aptcode)

    if(reqGetStationInfo.status_code == 200):
        reqGetStationInfoRoot = ET.fromstring(reqGetStationInfo.content)

        for child in reqGetStationInfoRoot.iter(tag = 'longitude'):
            stationLongitude = child.text
        for child in reqGetStationInfoRoot.iter(tag = 'latitude'):
            stationLatitude = child.text

        reqGetStationRad = requests.get(awcAPI+awcRadialWeather+"25"+";"+stationLongitude+","+stationLatitude)

        if(reqGetStationRad.status_code == 200):
            allStations = []
            reqGetStationRadRoot = ET.fromstring(reqGetStationRad.content)
        
            for child in reqGetStationRadRoot.iter(tag = 'station_id'):
                allStations.append(child.text)

            for station in allStations:
                reqGetStationWx = requests.get(awcAPI+awcCurrentWeather+station)

                if(reqGetStationWx.status_code == 200):
                    reqGetStationWxRoot = ET.fromstring(reqGetStationWx.content)

                    for child in reqGetStationWxRoot.iter(tag = 'raw_text'):
                        getRadiusWeather.MetarRaw = child.text
                        getRadiusWeather.AllStations.append(getRadiusWeather.MetarRaw)
                else:
                    print("FAILED. Status Code: " + reqGetStationWx.status_code)
        else:
            print("FAILED. Status Code: " + reqGetStationRad.status_code)
    else:
        print("FAILED. Status Code: " + reqGetStationInfo.status_code)

    print(getRadiusWeather.AllStations)

#Home page
@app.route('/')
def home():
    return render_template('index.html')

#Get weather page
@app.route('/weather', methods=['POST', 'GET'])
def weather():
    return render_template('weather.html', form=weatherForm())

#Display weather results
@app.route('/wxresult', methods=['POST'])
def wxresult():
    #Retreive value from weather form and call AviationWeather API to get current METAR
    if request.method=='POST':
        wxvalue = weatherForm().wxchoice.data
        aptcode = weatherForm().icao.data.upper()

        if wxvalue == 'wxsingle':
            getWeather(aptcode)
            return render_template('wxresult.html', form=weatherResultForm(), MetarData = getWeather.MetarRaw, aptCode = aptcode, wxvalue = wxvalue)
        if wxvalue == 'wxradius':
            getRadiusWeather(aptcode)
            return render_template('wxresult.html', form=weatherResultForm(), MetarData = getRadiusWeather.AllStations, aptCode = aptcode, wxvalue = wxvalue)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='8080')