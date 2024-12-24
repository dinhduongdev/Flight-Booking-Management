import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime as dt
import json
from app import app, db
from app.blueprints.auth import dao as auth_dao
from app.blueprints.auth.models import User
from app.blueprints.auth.models import UserRole
from app.blueprints.flights.models import Route
from app.blueprints.flights.models import Airport
from app.blueprints.flights.models import Country
from app.blueprints.flights.models import Flight
from app.blueprints.flights.models import Airline
from app.blueprints.flights.models import Aircraft
from app.blueprints.flights.models import AircraftSeat
from app.blueprints.flights.models import FlightSeat
from app.blueprints.flights.models import SeatClass
from app.blueprints.flights.models import Stopover
from app.blueprints.flights.models import Regulation

seed_data_path = os.path.dirname(__file__) + "/data"


def seed_users():
    with open(f"{seed_data_path}/users.json") as f:
        users = json.load(f)
    for user in users:
        user["role"] = UserRole(user["role"])
        user["password"] = auth_dao.bcrypt.generate_password_hash(
            user["password"]
        ).decode("utf-8")
        user["avatar"] = user.get("avatar", None)
        if not user["avatar"]:
            user["avatar"] = auth_dao.randomize_profile_img()
        db.session.add(User(**user))

    print("Users seeded successfully!")


def seed_routes():
    with open(f"{seed_data_path}/routes.json") as f:
        routes = json.load(f)
    for route in routes:
        db.session.add(Route(**route))

    print("Routes seeded successfully!")


def seed_airports(limit=10):
    with open(f"{seed_data_path}/airports.json") as f:
        airports = json.load(f)
    for airport in airports[:limit]:
        # Tạo đối tượng Airport mới
        db.session.add(Airport(**airport))  # Thêm vào session

    print("Airports seeded successfully!")


def seed_countries():
    with open(f"{seed_data_path}/countries.json") as f:
        countries = json.load(f)
    for country in countries:
        # Rename the key "CountryCode" to "code"
        country["code"] = country.pop("CountryCode")
        # Tạo đối tượng Country mới
        db.session.add(Country(**country))  # Thêm vào session

    print("Countries seeded successfully!")


def seed_flights():
    with open(f"{seed_data_path}/flights.json") as f:
        flights = json.load(f)
    for flight in flights:
        # Chuyển đổi thời gian từ định dạng chuỗi sang đối tượng datetime
        flight["depart_time"] = dt.fromisoformat(
            flight["depart_time"].replace("Z", "+00:00")
        )
        flight["arrive_time"] = dt.fromisoformat(
            flight["arrive_time"].replace("Z", "+00:00")
        )

        db.session.add(Flight(**flight))  # Thêm vào session

    print("Flights seeded successfully!")


def seed_airlines():
    with open(f"{seed_data_path}/airlines.json") as f:
        airlines = json.load(f)
    for airline in airlines:
        db.session.add(Airline(**airline))  # Thêm vào session
    print("Airlines seeded successfully!")


def seed_aircrafts():
    with open(f"{seed_data_path}/aircrafts.json") as f:
        aircrafts = json.load(f)
    for aircraft in aircrafts:
        aircraft["airline_id"] = aircraft.pop("airline")
        db.session.add(Aircraft(**aircraft))  # Thêm vào session

    print("Aircrafts seeded successfully!")


def seed_intermediate_airport():
    with open(f"{seed_data_path}/stops.json") as f:
        stops = json.load(f)
    for stop in stops:
        stop["arrival_time"] = dt.fromisoformat(
            stop.pop("arrive_time").replace("Z", "+00:00")
        )
        stop["departure_time"] = dt.fromisoformat(
            stop.pop("depart_time").replace("Z", "+00:00")
        )
        db.session.add(Stopover(**stop))  # Thêm vào session
    print("Intermediate airports seeded successfully!")


def seed_seat_classes():
    with open(f"{seed_data_path}/seatclasses.json") as f:
        seat_classes = json.load(f)
    for seat_class in seat_classes:
        db.session.add(SeatClass(**seat_class))
    print("Seat classes seeded successfully!")


def seed_aircarft_seats():
    with open(f"{seed_data_path}/aircraft_seats.json") as f:
        aircraft_seats = json.load(f)
    for aircraft_seat in aircraft_seats:
        db.session.add(AircraftSeat(**aircraft_seat))
    print("Aircraft seats seeded successfully!")


def seed_flight_seats():
    with open(f"{seed_data_path}/flight_seats.json") as f:
        flight_seats = json.load(f)
    for flight_seat in flight_seats:
        db.session.add(FlightSeat(**flight_seat))
    print("Flight seats seeded successfully!")


def seed_regulations():
    with open(f"{seed_data_path}/regulations.json") as f:
        regulations = json.load(f)
    for regulation in regulations:
        db.session.add(Regulation(**regulation))
    print("Regulations seeded successfully!")


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()
        try:
            seed_users()
            seed_countries()
            seed_airports()
            seed_airlines()
            seed_aircrafts()
            seed_seat_classes()
            seed_routes()
            seed_flights()
            seed_intermediate_airport()
            seed_aircarft_seats()
            seed_flight_seats()
            seed_regulations()
            db.session.commit()
            print("Data seeded successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Failed to seed data: {e}")
            print("Rolling back changes...")


if __name__ == "__main__":
    seed()
