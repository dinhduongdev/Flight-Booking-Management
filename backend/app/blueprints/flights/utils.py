from datetime import datetime
from flask import flash
from . import dao


def to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def to_datetime(datetime_str):
    return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M")


def validate_stopover_form(data):
    max_stopover_airports = dao.get_max_stopover_airports()
    min_stopover_duration = dao.get_min_stopover_duration()
    max_stopover_duration = dao.get_max_stopover_duration()
    # Get number of stopovers
    stopover_count = data.get("stopovers_num", type=int)

    if stopover_count <= 0:
        return True

    if stopover_count > max_stopover_airports:
        flash("Number of stopovers is too large", "danger")
        return False

    # Check if the stopover info is provided
    for i in range(1, stopover_count + 1):
        if (
            not data.get(f"stopover_airport_{i}")
            or not data.get(f"stopover_arrival_time_{i}")
            or not data.get(f"stopover_departure_time_{i}")
        ):
            flash(f"Stopover {i} info is not provided fully!", "danger")
            return False

    # Check if the airports are unique
    stopover_airports = [
        data.get(f"stopover_airport_{i}", type=int)
        for i in range(1, stopover_count + 1)
    ]
    if len(stopover_airports) != len(set(stopover_airports)):
        flash("Stopover airports must be unique", "danger")
        return False
    if (
        data.get("departure_airport", type=int) in stopover_airports
        or data.get("arrival_airport", type=int) in stopover_airports
    ):
        flash(
            "Departure and arrival airports must be different from stopover airports",
            "danger",
        )
        return False

    # Check if the stopover times are valid
    departure_time = data.get("departure_time", type=to_datetime)
    arrival_time = data.get("arrival_time", type=to_datetime)
    latest_departure_time = (
        departure_time  # The latest departure time of the previous stopover
    )
    for i in range(1, stopover_count + 1):
        s_arrival_time = data.get(f"stopover_arrival_time_{i}", type=to_datetime)
        s_departure_time = data.get(f"stopover_departure_time_{i}", type=to_datetime)
        # The stopover must be between departure and arrival time
        if (
            s_departure_time <= s_arrival_time
            or s_arrival_time <= departure_time
            or s_departure_time >= arrival_time
        ):
            flash(f"Stopover {i} arrival time is invalid", "danger")
            return False
        # The stopover must be in order
        if s_arrival_time <= latest_departure_time:
            flash(f"Stopover {i} doesn't be in order!", "danger")
            return False

        # The stopover duration must be between min and max stopover duration
        stopover_duration = (s_departure_time - s_arrival_time).total_seconds() // 60
        if not (min_stopover_duration <= stopover_duration <= max_stopover_duration):
            flash(f"Stopover {i} duration is invalid", "danger")
            flash(
                f"Stopover minutes must be: {min_stopover_duration} - {max_stopover_duration}",
                "info",
            )
            return False

        # Update the latest departure time
        latest_departure_time = s_departure_time

    return True
