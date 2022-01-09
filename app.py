import requests
import os
import xml.etree.ElementTree as ET
import bs4
import re
from flask import Flask, render_template, request
from flask import Flask, url_for, render_template, redirect
from forms import weather_form, weather_result_form, apt_info_form, wb_form
from webcalls import awc_api, awc_station_info, awc_current_weather, awc_radial_weather, skyvector_airport_info

app = Flask(__name__)

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

#Function that retreives current raw METAR data at given airport
def get_weather(aptcode):
    req_get_current_wx = requests.get(awc_api+awc_current_weather+aptcode)

    if(req_get_current_wx.status_code == 200):
        root = ET.fromstring(req_get_current_wx.content)
        
        for child in root.iter(tag = 'raw_text'):
            get_weather.MetarRaw = child.text
    else:
        print("FAILED. Status Code: " + req_get_current_wx.status_code)

#Function that retreives current raw METAR data from a 25nm radius of given airport
def get_radius_weather(aptcode):
    get_radius_weather.all_stations = []

    req_get_station_info = requests.get(awc_api+awc_station_info+aptcode)

    if(req_get_station_info.status_code == 200):
        req_get_station_infoRoot = ET.fromstring(req_get_station_info.content)

        for child in req_get_station_infoRoot.iter(tag = 'longitude'):
            station_longitude = child.text
        for child in req_get_station_infoRoot.iter(tag = 'latitude'):
            station_latitude = child.text

        req_get_station_rad = requests.get(awc_api+awc_radial_weather+"25"+";"+station_longitude+","+station_latitude)

        if(req_get_station_rad.status_code == 200):
            all_stations = []
            req_get_station_radRoot = ET.fromstring(req_get_station_rad.content)
        
            for child in req_get_station_radRoot.iter(tag = 'station_id'):
                all_stations.append(child.text)

            for station in all_stations:
                req_get_station_wx = requests.get(awc_api+awc_current_weather+station)

                if(req_get_station_wx.status_code == 200):
                    req_get_station_wxRoot = ET.fromstring(req_get_station_wx.content)

                    for child in req_get_station_wxRoot.iter(tag = 'raw_text'):
                        get_radius_weather.MetarRaw = child.text
                        get_radius_weather.all_stations.append(get_radius_weather.MetarRaw)
                else:
                    print("FAILED. Status Code: " + req_get_station_wx.status_code)
        else:
            print("FAILED. Status Code: " + req_get_station_rad.status_code)
    else:
        print("FAILED. Status Code: " + req_get_station_info.status_code)

#Function that retrieves information for given airport
def get_airport_info(aptcode):
    aptreq = skyvector_airport_info+aptcode
    html = requests.get(aptreq).text
    soup = bs4.BeautifulSoup(html, "html.parser")

    apt_name = soup.find('div', attrs={'id':'titlebgright'}).text
    
    ctwr = soup.find('th', text="Control Tower:").find_next_sibling().text
    if (ctwr == "Yes"):
        twr = soup.find('th', text=re.compile("TOWER:")).find_next_sibling().text
        gnd = soup.find('th', text=re.compile("GROUND:")).find_next_sibling().text
    else:
        twr = ''
        gnd = ''
    
    atis_check = soup.find('th', text="ATIS:")
    if (atis_check != None):
        atis = atis_check.find_next_sibling().text
    else:
        atis = ''
    
    asos_check = soup.find('th', text="ASOS:")
    if (asos_check != None):
        asos = asos_check.find_next_sibling().text
    else:
        asos = ''

    ctaf_check = soup.find('th', text="CTAF:")
    if (ctaf_check != None):
        ctaf = ctaf_check.find_next_sibling().text
    else:
        ctaf = ''

    dep_check = soup.find('th', text=re.compile("DEPARTURE:"))
    if (dep_check != None):
        dep = dep_check.find_next_sibling().text
    else:
        dep = ''

    app_check = soup.find('th', text=re.compile("APPROACH:"))
    if (app_check != None):
        app = app_check.find_next_sibling().text
    else:
        app = ''

    return apt_name, twr, gnd, atis, asos, ctaf, dep, app

#Home page
@app.route('/')
def home():
    return render_template('index.html')

#Get weather page
@app.route('/weather', methods=['POST', 'GET'])
def weather():
    return render_template('weather.html', form=weather_form())

#Display weather results
@app.route('/wxresult', methods=['POST'])
def wxresult():
    #Retrieve value from weather form and call AviationWeather API to get current METAR
    if request.method=='POST':
        wxvalue = weather_form().wxchoice.data
        aptcode = weather_form().icao.data.upper()

        if wxvalue == 'wxsingle':
            get_weather(aptcode)
            return render_template('wxresult.html', form=weather_result_form(), MetarData = get_weather.MetarRaw, aptCode = aptcode, wxvalue = wxvalue)
        if wxvalue == 'wxradius':
            get_radius_weather(aptcode)
            return render_template('wxresult.html', form=weather_result_form(), MetarData = get_radius_weather.all_stations, aptCode = aptcode, wxvalue = wxvalue)

#Get airport information page
@app.route('/aptinfo', methods=['GET'])
def aptinfo():
    return render_template('aptinfo.html', form=apt_info_form())

#Display airport information results page
@app.route('/aptinforesult', methods=['POST'])
def aptinforesult():
    aptcode = apt_info_form().icao.data.upper()

    apt_name, twr, gnd, atis, asos, ctaf, dep, app = get_airport_info(aptcode)
    
    return render_template('aptinforesult.html', aptcode = aptcode, apt_name = apt_name, tower = twr, ground = gnd, atis = atis, asos = asos, ctaf = ctaf, dep = dep, app = app)

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
        return render_template('wb.html', form=wb_form(), emptyWeight = emptyWeight, emptyWeightArm = emptyWeightArm, emptyWeightMom = emptyWeightMom, frontSeatArm = frontSeatArm, backSeatArm = backSeatArm, baggage1Arm = baggage1Arm, baggage2Arm = baggage2Arm, fuelArm = fuelArm)

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
        
        return render_template('wb.html', form=wb_form(), emptyWeight = emptyWeight, emptyWeightArm = emptyWeightArm, emptyWeightMom = emptyWeightMom, frontSeatWeightL = frontSeatWeightL, frontSeatWeightR = frontSeatWeightR, backSeatWeightL = backSeatWeightL, backSeatWeightR = backSeatWeightR, baggage1Weight = baggage1Weight, baggage2Weight = baggage2Weight, frontSeatArm = frontSeatArm, backSeatArm = backSeatArm, baggage1Arm = baggage1Arm, baggage2Arm = baggage2Arm, fuelArm = fuelArm, frontSeatMom = frontSeatMom, backSeatMom = backSeatMom, baggage1Mom = baggage1Mom, baggage2Mom = baggage2Mom, zFuelWeight = zFuelWeight, zFuelMom = "{:.2f}".format(zFuelMom), zFuelArm = "{:.2f}".format(zFuelArm), fuelWeight = fuelWeight, fuelMom = "{:.2f}".format(fuelMom), fuelGal = fuelGal, totalWeight = totalWeight, totalMom = totalMom, totalArm = "{:.2f}".format(totalArm))

if __name__ == '__main__':
    app.run(debug=False, port=8000)