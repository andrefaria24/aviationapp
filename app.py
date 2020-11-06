import requests
import os
import xml.etree.ElementTree as ET
import bs4
import re
from flask import Flask, render_template, request
from flask import Flask, url_for, render_template, redirect
from forms import weatherForm, weatherResultForm, aptinfoForm, wbForm
from webcalls import awcAPI, awcStationInfo, awcCurrentWeather, awcRadialWeather, skyvectorAirportInfo

app = Flask(__name__)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

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

#Function that retrieves information for given airport
def getAirportInfo(aptcode):
    aptreq = skyvectorAirportInfo+aptcode
    html = requests.get(aptreq).text
    soup = bs4.BeautifulSoup(html, "html.parser")

    aptName = soup.find('div', attrs={'id':'titlebgright'}).text
    
    ctwr = soup.find('th', text="Control Tower:").find_next_sibling().text
    if (ctwr == "Yes"):
        twr = soup.find('th', text=re.compile("TOWER:")).find_next_sibling().text
        gnd = soup.find('th', text=re.compile("GROUND:")).find_next_sibling().text
    else:
        twr = ''
        gnd = ''
    
    atischeck = soup.find('th', text="ATIS:")
    if (atischeck != None):
        atis = atischeck.find_next_sibling().text
    else:
        atis = ''
    
    asoscheck = soup.find('th', text="ASOS:")
    if (asoscheck != None):
        asos = asoscheck.find_next_sibling().text
    else:
        asos = ''

    ctafcheck = soup.find('th', text="CTAF:")
    if (ctafcheck != None):
        ctaf = ctafcheck.find_next_sibling().text
    else:
        ctaf = ''

    depcheck = soup.find('th', text=re.compile("DEPARTURE:"))
    if (depcheck != None):
        dep = depcheck.find_next_sibling().text
    else:
        dep = ''

    appcheck = soup.find('th', text=re.compile("APPROACH:"))
    if (appcheck != None):
        app = appcheck.find_next_sibling().text
    else:
        app = ''

    return aptName, twr, gnd, atis, asos, ctaf, dep, app

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
    #Retrieve value from weather form and call AviationWeather API to get current METAR
    if request.method=='POST':
        wxvalue = weatherForm().wxchoice.data
        aptcode = weatherForm().icao.data.upper()

        if wxvalue == 'wxsingle':
            getWeather(aptcode)
            return render_template('wxresult.html', form=weatherResultForm(), MetarData = getWeather.MetarRaw, aptCode = aptcode, wxvalue = wxvalue)
        if wxvalue == 'wxradius':
            getRadiusWeather(aptcode)
            return render_template('wxresult.html', form=weatherResultForm(), MetarData = getRadiusWeather.AllStations, aptCode = aptcode, wxvalue = wxvalue)

#Get airport information page
@app.route('/aptinfo', methods=['GET'])
def aptinfo():
    return render_template('aptinfo.html', form=aptinfoForm())

#Display airport information results page
@app.route('/aptinforesult', methods=['POST'])
def aptinforesult():
    aptcode = aptinfoForm().icao.data.upper()

    aptName, twr, gnd, atis, asos, ctaf, dep, app = getAirportInfo(aptcode)
    
    return render_template('aptinforesult.html', aptcode = aptcode, aptName = aptName, tower = twr, ground = gnd, atis = atis, asos = asos, ctaf = ctaf, dep = dep, app = app)

#Aircraft weight and balance page
@app.route('/wb', methods=['GET', 'POST'])
def wb():
    #N9121H W&B Numbers
    emptyWeight = 1486
    emptyWeightArm = 39.04
    emptyWeightMom = emptyWeight * emptyWeightArm
    frontSeatArm = 37.00
    backSeatArm = 73.00
    baggage1Arm = 95.00
    baggage2Arm = 123.00
    fuelArm = 48.00

    #Insert W&B data in form
    if request.method == 'GET':
        return render_template('wb.html', form=wbForm(), emptyWeight = emptyWeight, emptyWeightArm = emptyWeightArm, emptyWeightMom = emptyWeightMom, frontSeatArm = frontSeatArm, backSeatArm = backSeatArm, baggage1Arm = baggage1Arm, baggage2Arm = baggage2Arm, fuelArm = fuelArm)

    #Calculate W&B numbers and display in form
    elif request.method == 'POST':

        frontSeatWeightL = request.form['frontSeatWeightL']
        frontSeatWeightR = request.form['frontSeatWeightR']
        frontSeatMom = (float(frontSeatWeightL) + float(frontSeatWeightR)) * frontSeatArm

        backSeatWeightL = request.form['backSeatWeightL']
        backSeatWeightR = request.form['backSeatWeightR']
        backSeatMom = (float(backSeatWeightL) + float(backSeatWeightR)) * backSeatArm

        baggage1Weight = request.form['baggage1Weight']
        baggage1Mom = float(baggage1Weight) * float(baggage1Arm)

        baggage2Weight = request.form['baggage2Weight']
        baggage2Mom = float(baggage2Weight) * float(baggage2Arm)

        zFuelWeight = float(emptyWeight) + float(frontSeatWeightL) + float(frontSeatWeightR) + float(backSeatWeightL) + float(backSeatWeightR) + float(baggage1Weight) + float(baggage2Weight)
        zFuelMom = emptyWeightMom + frontSeatMom + backSeatMom + baggage1Mom + baggage2Mom
        zFuelArm = zFuelMom / zFuelWeight

        fuelGal = request.form['fuelGal']
        fuelWeight = float(fuelGal) * 6
        fuelMom = fuelWeight * fuelArm

        totalWeight = zFuelWeight + fuelWeight
        totalMom = zFuelMom + fuelMom
        totalArm = totalMom / totalWeight
        
        return render_template('wb.html', form=wbForm(), emptyWeight = emptyWeight, emptyWeightArm = emptyWeightArm, emptyWeightMom = emptyWeightMom, frontSeatWeightL = frontSeatWeightL, frontSeatWeightR = frontSeatWeightR, backSeatWeightL = backSeatWeightL, backSeatWeightR = backSeatWeightR, baggage1Weight = baggage1Weight, baggage2Weight = baggage2Weight, frontSeatArm = frontSeatArm, backSeatArm = backSeatArm, baggage1Arm = baggage1Arm, baggage2Arm = baggage2Arm, fuelArm = fuelArm, frontSeatMom = frontSeatMom, backSeatMom = backSeatMom, baggage1Mom = baggage1Mom, baggage2Mom = baggage2Mom, zFuelWeight = zFuelWeight, zFuelMom = "{:.2f}".format(zFuelMom), zFuelArm = "{:.2f}".format(zFuelArm), fuelWeight = fuelWeight, fuelMom = "{:.2f}".format(fuelMom), fuelGal = fuelGal, totalWeight = totalWeight, totalMom = totalMom, totalArm = "{:.2f}".format(totalArm))

#if __name__ == '__main__':
#    app.run(debug=False, port='80')