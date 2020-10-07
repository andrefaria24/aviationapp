from flask import Flask, render_template, request
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)

awcAPI = 'https://www.aviationweather.gov/adds/dataserver_current/httpparam?'
awcCurrentWeather = 'dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=2&mostRecent=true&stationString='

#Function that retreives current raw METAR data at given airport
def getWeather():
    getWeather.aptCode = request.form['icao'].upper()
         
    reqGetCurrentWx = requests.get(awcAPI+awcCurrentWeather+getWeather.aptCode)

    if(reqGetCurrentWx.status_code == 200):
        root = ET.fromstring(reqGetCurrentWx.content)
        
        for child in root.iter(tag = 'raw_text'):
            getWeather.MetarRaw = child.text
    else:
        print("FAILED. Status Code: " + reqGetCurrentWx.status_code)

#Home page
@app.route('/')
def home():
    return render_template('index.html')

#Get weather page
@app.route('/weather', methods=['POST', 'GET'])
def weather():
    return render_template('weather.html')

#Display weather results
@app.route('/wxresult', methods=['POST'])
def wxresult():
    #Retreive value from weather form and call AviationWeather API to get current METAR
    if request.method=='POST':
        getWeather()
    return render_template('wxresult.html', MetarRaw = getWeather.MetarRaw, aptCode = getWeather.aptCode)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='8080')