from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SelectField
from wtforms import SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired

from app.blueprints.flights import dao


class CreateAircraftForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    airline = SelectField("Airline", validators=[DataRequired()])
    submit = SubmitField("Save")
