from flask import render_template, redirect, url_for

# Import the blueprint instance from the `__init__.py`
from . import main_bp
from app.blueprints.flights import forms


@main_bp.route("/", methods=["GET"])
def home():
    form = forms.SearchFlightForm()
    form.fill_airport_selects()

    if form.validate_on_submit():
        return redirect(
            url_for(
                "flights.searchFlights",
                departure_airport=form.departure_airport.data,
                arrival_airport=form.arrival_airport.data,
                depart_date=form.departure_date.data,
            )
        )
    return render_template("main/home.html", form=form)


@main_bp.route("/about")
def about():
    return render_template("main/about.html")
