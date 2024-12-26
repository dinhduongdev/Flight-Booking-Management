from flask import render_template, jsonify, request, redirect, flash, url_for
from datetime import datetime as dt


from app import db
from . import flights_bp
from app.blueprints.auth import decorators
from . import dao
from . import utils
from .forms import FlightSchedulingForm, SearchFlightForm


@flights_bp.route("/api/airlines", methods=["GET"])
def get_airlines():
    return jsonify([airline.to_dict() for airline in dao.get_airlines()])


@flights_bp.route("/api/seatclasses", methods=["GET"])
def get_seatclasses():
    return jsonify([seatclass.to_dict() for seatclass in dao.get_seat_classes()])


@flights_bp.route("/api/airports")
def get_airports():
    return jsonify([airport.to_dict() for airport in dao.get_airports()])


@flights_bp.route("/api/routes")
def get_routes():
    return jsonify([route.to_dict() for route in dao.get_routes()])


@flights_bp.route("/api/countries")
def get_countries():
    return jsonify([country.to_dict() for country in dao.get_countries()])


@flights_bp.route("/api/aircrafts")
def get_aircrafts():
    return jsonify([aircraft.to_dict() for aircraft in dao.get_aircrafts()])


@flights_bp.route("/schedule", methods=["GET", "POST"])
@decorators.admin_or_flight_manager_required
def flight_scheduling():
    form = FlightSchedulingForm(request.form)
    max_stopover_airports = dao.get_max_stopover_airports()
    if form.validate_on_submit() and utils.validate_stopover_form(request.form):
        # Get the route if the route doesn't exist, create a new one
        route = dao.get_route_by_airports(
            depart_airport_id=form.departure_airport.data,
            arrive_airport_id=form.arrival_airport.data,
        )
        if not route:
            route = dao.add_route(
                depart_airport_id=form.departure_airport.data,
                arrive_airport_id=form.arrival_airport.data,
            )

        # Add the flight
        flight = dao.add_flight(
            route_id=route.id,
            code=form.flight_code.data,
            depart_time=form.departure_time.data,
            arrive_time=form.arrival_time.data,
            aircraft_id=form.aircraft.data,
        )

        # Add the stopovers
        stopover_count = request.form.get("stopovers_num", type=int)
        for i in range(1, stopover_count + 1):
            stopover_airport = request.form.get(f"stopover_airport_{i}", type=int)
            stopover_arrival_time = request.form.get(
                f"stopover_arrival_time_{i}", type=utils.to_datetime
            )
            stopover_departure_time = request.form.get(
                f"stopover_departure_time_{i}", type=utils.to_datetime
            )
            dao.add_stopover(
                airport_id=stopover_airport,
                flight_id=flight.id,
                arrival_time=stopover_arrival_time,
                departure_time=stopover_departure_time,
                order=i,
                note=request.form.get(f"stopover_note_{i}", None),
            )

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Error scheduling flight!", "danger")
            return redirect(request.referrer)

        flash("Flight scheduled successfully! Please provide flight prices.", "success")
        return redirect(url_for("flights.set_prices", id=flight.id))

    return render_template(
        "flights/schedule.html", form=form, max_stopover_airports=max_stopover_airports
    )


@flights_bp.route("/schedule/<id>/prices", methods=["GET", "POST"])
@decorators.admin_or_flight_manager_required
def set_prices(id):
    flight = dao.get_flight_by_id(id)
    if not flight or flight.seats:
        flash("Flight not found!", "info")
        return redirect("/")

    if request.method == "POST":
        data = request.form

        # Get the prices of all seat classes of the flight
        prices = {}
        for seatclass in dao.get_seat_classes():
            if f"price_class_{seatclass.id}" in data.to_dict():
                prices[seatclass.id] = data.get(
                    f"price_class_{seatclass.id}", type=float
                )

        # Add flight seats
        for aircraft_seat in data.getlist("seat_ids", type=int):
            seat = dao.get_aircraft_seat_by_id(aircraft_seat)
            # Check if the seat exists and belongs to the aircraft
            if not seat or seat.aircraft_id != flight.aircraft_id:
                flash(f"Seat {aircraft_seat} not found!", "info")
                continue

            price = prices.get(seat.seat_class_id, None)

            dao.add_flight_seat(flight.id, seat.id, price)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("Error setting prices!", "danger")
            return redirect(request.referrer)
        flash("Flight prices set successfully!", "success")
        return redirect(url_for("flights.showFlight", id=flight.id))
    return render_template("flights/create_flight_seats.html", flight=flight)


@flights_bp.route("/search/flight", methods=["GET"])
def searchFlights():
    # Get params from request
    form = SearchFlightForm(request.form)

    departure_airport_id = request.args.get("departure_airport", type=int)
    arrival_airport_id = request.args.get("arrival_airport", type=int)
    depart_date = request.args.get("departure_date", type=utils.to_date)

    if not all([departure_airport_id, arrival_airport_id, depart_date]):
        # If user first access the page, return the plain search page
        return render_template("flights/search.html", form=form)

    # Get the route
    route = dao.get_route_by_airports(departure_airport_id, arrival_airport_id)
    if not route:
        # If the route does not exist, return an error message
        flash("This route doesn't exist!", "warning")
        return render_template("flights/search.html", form=form)

    # Get flights for the route
    page = request.args.get("page", default=1, type=int)
    flights = dao.get_flights_by_route_and_date(route.id, depart_date, page)

    if not flights.items:
        # If there are no flights for the route, return an error message
        flash("Couldn't find any flights!", "warning")

    return render_template(
        "flights/search.html",
        route=route,
        flights=flights,
        depart_date=depart_date,
        search_time=dt.now(),
        staff_min_booking_time=dao.get_staff_min_booking_time(),
        customer_min_booking_time=dao.get_customer_min_booking_time(),
        form=form,
    )


@flights_bp.route("/flight/<id>", methods=["GET"])
def showFlight(id):
    flight = dao.get_flight_by_id(id)
    if not flight:
        flash("Flight not found!", "info")
        return redirect("/")
    return render_template(
        "flights/details.html",
        flight=flight,
        search_time=dt.now(),
        staff_min_booking_time=dao.get_staff_min_booking_time(),
        customer_min_booking_time=dao.get_customer_min_booking_time(),
        title="Flight Details",
    )
