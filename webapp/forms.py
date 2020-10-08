from flask_wtf import FlaskForm
from wtforms import StringField, TextField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length

class weatherForm(FlaskForm):
    icao = TextField('ICAO')
    wxchoice = RadioField('WxChoices', choices=[('wxsingle','Get latest weather from single airport'),('wxradius','Get latest weather within a 25nm radius of selected airport')])
    submit = SubmitField('Submit')

class weatherResultForm(FlaskForm):
    result = TextField('Result')
    clear = SubmitField('Clear')