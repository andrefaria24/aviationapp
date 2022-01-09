from flask_wtf import FlaskForm
from wtforms import StringField, TextField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length

class weather_form(FlaskForm):
    icao = TextField('ICAO')
    wxchoice = RadioField('WxChoices', choices=[('wxsingle','Get latest weather from single airport'),('wxradius','Get latest weather within a 25nm radius of selected airport')])
    submit = SubmitField('Submit')

class weather_result_form(FlaskForm):
    result = TextField('Result')

class apt_info_form(FlaskForm):
    icao = TextField('ICAO')
    submit = SubmitField('Submit')

class wb_form(FlaskForm):
    frontSeatWeightL = TextField('frontSeatWeightL')
    frontSeatWeightR = TextField('frontSeatWeightR')
    backSeatWeightL = TextField('backSeatWeightL')
    backSeatWeightR = TextField('backSeatWeightR')
    baggage1Weight = TextField('baggage1Weight')
    baggage2Weight = TextField('baggage2Weight')
    fuelGal = TextField('fuelGal')
    calc = SubmitField('Calculate')