from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import DateField
from wtforms import DateTimeLocalField
from wtforms import SubmitField
from wtforms import SelectField
from wtforms import ValidationError
from wtforms.validators import DataRequired
from datetime import datetime as dt
from . import dao


class SearchFlightForm(FlaskForm):
    departure_airport = SelectField(
        "Departure Airport",
        validators=[DataRequired()],
        coerce=int,
        render_kw={
            "class": "selectpicker",
            "data-live-search": "true",
        },
    )
    arrival_airport = SelectField(
        "Arrival Airport",
        validators=[DataRequired()],
        coerce=int,
        render_kw={
            "class": "selectpicker",
            "data-live-search": "true",
            "data-hide-disabled": "true",
        },
    )
    departure_date = DateField("Departure Date", validators=[DataRequired()])
    submit = SubmitField("Search")

    def __init__(self, formdata=None, **kwargs):
        super().__init__(formdata, **kwargs)
        self.fill_airport_selects()

    def fill_airport_selects(self):
        airports = dao.get_airports()
        self.departure_airport.choices = [
            (airport.id, f"{airport.name} ({airport.code}) - {airport.country.name}")
            for airport in airports
        ]
        self.arrival_airport.choices = [
            (airport.id, f"{airport.name} ({airport.code}) - {airport.country.name}")
            for airport in airports
        ]

    def validate(self, extra_validators=None):
        if not super().validate():
            return False
        if self.departure_airport.data == self.arrival_airport.data:
            self.departure_airport.errors.append(
                "Departure airport must be different from arrival airport!"
            )
            self.arrival_airport.errors.append(
                "Arrival airport must be different from departure airport!"
            )
            return False
        route = dao.get_route_by_airports(
            self.departure_airport.data, self.arrival_airport.data
        )
        if not route:
            self.departure_airport.errors.append(
                "Route not found for selected airports!"
            )
            self.arrival_airport.errors.append("Route not found for selected airports!")
            return False
        return True


class FlightSchedulingForm(FlaskForm):
    flight_code = StringField("Flight Code", validators=[DataRequired()])
    departure_airport = SelectField(
        label="Departure Airport",
        validators=[DataRequired()],
        coerce=int,
        render_kw={
            "class": "selectpicker",
            "data-live-search": "true",
            "title": "Select departure airport",
        },
    )
    arrival_airport = SelectField(
        "Arrival Airport",
        validators=[DataRequired()],
        coerce=int,
        render_kw={
            "class": "selectpicker",
            "data-live-search": "true",
            "title": "Select arrival airport",
        },
    )
    aircraft = SelectField(
        "Aircraft",
        validators=[DataRequired()],
        coerce=int,
        render_kw={
            "class": "selectpicker",
            "data-live-search": "true",
            "title": "Select aircraft",
        },
    )
    departure_time = DateTimeLocalField("Departure Time", validators=[DataRequired()])
    arrival_time = DateTimeLocalField("Arrival Time", validators=[DataRequired()])
    submit = SubmitField("Submit")

    def __init__(self, formdata=None, **kwargs):
        super().__init__(formdata, **kwargs)
        self.fill_airport_selects()
        self.fill_aircraft_selects()

    def fill_airport_selects(self):
        airports = dao.get_airports()
        self.departure_airport.choices = [
            (airport.id, f"{airport.name} ({airport.code}) - {airport.country.name}")
            for airport in airports
        ]
        self.arrival_airport.choices = [
            (airport.id, f"{airport.name} ({airport.code}) - {airport.country.name}")
            for airport in airports
        ]

    def fill_aircraft_selects(self):
        aircrafts = dao.get_aircrafts()
        self.aircraft.choices = [
            (aircraft.id, f"{aircraft.id} - {aircraft.name} ({aircraft.airline.name})")
            for aircraft in aircrafts
        ]

    def validate(self, extra_validators=None):
        if not super().validate():
            return False
        if self.departure_airport.data == self.arrival_airport.data:
            self.departure_airport.errors.append(
                "Departure airport must be different from arrival airport!"
            )
            self.arrival_airport.errors.append(
                "Arrival airport must be different from departure airport!"
            )
            return False
        #
        # Validate time
        #
        if self.departure_time.data < dt.now():
            self.departure_time.errors.append(
                "Departure time must be later than current time!"
            )
            return False
        if self.departure_time.data >= self.arrival_time.data:
            self.arrival_time.errors.append(
                "Arrival time must be later than departure time!"
            )
            return False
        # Validate flight duration (regulation)
        flight_minutes = (
            self.arrival_time.data - self.departure_time.data
        ).total_seconds() // 60
        min_f_duration = dao.get_min_flight_duration()
        max_f_duration = dao.get_max_flight_duration()
        if not (min_f_duration <= flight_minutes <= max_f_duration):
            self.arrival_time.errors.append(
                f"Flight duration must be between {min_f_duration} - {max_f_duration} minutes!"
            )
            return False
        #
        # Validate aircraft
        #
        aircraft = dao.get_aircraft_by_id(self.aircraft.data)
        if not aircraft:
            self.aircraft.errors.append("Aircraft not found!")
            return False
        if not aircraft.is_available(self.departure_time.data, self.arrival_time.data):
            self.aircraft.errors.append("Aircraft is not available!")
            return False
        return True
