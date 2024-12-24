from sqlalchemy import (
    Column,
    Integer,
    String,
    VARCHAR,
    ForeignKey,
    DateTime,
    Double,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from datetime import datetime as dt
from flask_login import current_user

from app.blueprints.auth.models import UserRole
from app.blueprints.bookings.models import Reservation, PaymentStatus
from app import db
from . import dao

class Country(db.Model):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    code = Column(VARCHAR(5), unique=True, nullable=False)
    airports = relationship(
        "Airport", back_populates="country", lazy=True, cascade="all, delete"
    )

    def __repr__(self):
        return f"Country({self.id}, '{self.name}', '{self.code}')"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Airport(db.Model):
    __tablename__ = "airports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    code = Column(VARCHAR(5), unique=True, nullable=False)
    country_id = Column(
        Integer,
        ForeignKey(
            "countries.id",
        ),
        nullable=False,
    )
    country = relationship("Country", back_populates="airports", lazy=True)

    def __repr__(self):
        return f"Airport({self.id}, '{self.name}', '{self.code}', '{self.country_id}')"

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.country.name}"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Airline(db.Model):
    __tablename__ = "airlines"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    aircrafts = relationship(
        "Aircraft", backref="airline", lazy=True, cascade="all, delete"
    )

    def __repr__(self):
        return f"Airline({self.id}, '{self.name}')"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Aircraft(db.Model):
    __tablename__ = "aircrafts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    airline_id = Column(Integer, ForeignKey("airlines.id"), nullable=False)
    seats = relationship(
        "AircraftSeat", backref="aircraft", lazy=True, cascade="all, delete"
    )

    def __repr__(self):
        return f"Aircraft({self.id}, '{self.airline.name}', '{self.name}')"

    def is_available(self, depart_time, arrive_time):
        for flight in self.flights:
            if flight.depart_time < arrive_time and flight.arrive_time > depart_time:
                return False
        return True


class SeatClass(db.Model):
    __tablename__ = "seat_classes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)

    def __repr__(self):
        return f"SeatClass({self.id}, '{self.name}')"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class AircraftSeat(db.Model):
    __tablename__ = "aircraft_seats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    aircraft_id = Column(Integer, ForeignKey("aircrafts.id"), nullable=False)
    seat_class_id = Column(Integer, ForeignKey("seat_classes.id"), nullable=False)
    seat_name = Column(String(5), nullable=False)

    seat_class = relationship("SeatClass", backref="seats", lazy=True)
    flight_seats = relationship("FlightSeat", backref="aircraft_seat", lazy=True)

    def __repr__(self):
        return f"AircraftSeat({self.id}, {self.aircraft}, '{self.seat_class.name}', '{self.seat_name}')"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class FlightSeat(db.Model):
    __tablename__ = "flight_seats"
    __table_args__ = (UniqueConstraint("flight_id", "aircraft_seat_id"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    aircraft_seat_id = Column(Integer, ForeignKey("aircraft_seats.id"), nullable=True)
    price = Column(Double, nullable=False)
    currency = Column(VARCHAR(20), nullable=False)

    def __repr__(self):
        return f"FlightSeat({self.id}, Flight-{self.flight_id}, '{self.aircraft_seat.seat_name}', '{self.aircraft_seat.seat_class.name}', {self.price}-{self.currency})"

    def is_sold(self):
        return next((r for r in self.reservations if r.is_paid()), None) is not None


class Route(db.Model):
    __tablename__ = "routes"
    __table_args__ = (
        UniqueConstraint("depart_airport_id", "arrive_airport_id", name="unique_route"),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    depart_airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    arrive_airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    depart_airport = relationship(
        "Airport",
        foreign_keys=[depart_airport_id],
        backref="depart_routes",
        passive_deletes=True,
    )
    arrive_airport = relationship(
        "Airport",
        foreign_keys=[arrive_airport_id],
        backref="arrive_routes",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"Route({self.id}, '{self.depart_airport}', '{self.arrive_airport}')"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Flight(db.Model):
    __tablename__ = "flights"
    __table_args__ = (
        CheckConstraint("depart_time < arrive_time", name="check_depart_time"),
    )
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True)
    depart_time = Column(DateTime, nullable=False)
    arrive_time = Column(DateTime, nullable=False)
    aircraft_id = Column(Integer, ForeignKey("aircrafts.id"), nullable=True)
    route = relationship("Route", backref="flights", lazy=True)
    aircraft = relationship("Aircraft", backref="flights", lazy=True)
    seats = relationship(
        "FlightSeat", backref="flight", lazy=True, cascade="all, delete"
    )
    stopovers = relationship(
        "Stopover", backref="flight", lazy=True, cascade="all, delete"
    )

    def __repr__(self):
        return f"Flight({self.id}, {self.route}, '{self.depart_time}', '{self.arrive_time}', {self.aircraft})"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def get_remaining_seatclasses_and_info(self):
        seat_classes_prices = {}
        for seat in self.seats:
            seat_class_id = seat.aircraft_seat.seat_class_id
            if seat_class_id not in seat_classes_prices:
                seat_classes_prices[seat_class_id] = {
                    "class_name": SeatClass.query.get(seat_class_id).name,
                    "price": seat.price,
                    "currency": seat.currency,
                    "remaining": 0,
                }
            if not seat.is_sold():
                seat_classes_prices[seat_class_id]["remaining"] += 1
        return seat_classes_prices

    def is_bookable_now(self):
        # Check if flight is departed
        if self.depart_time <= dt.now():
            return False

        # Check if user can book this flight
        if current_user.role != UserRole.CUSTOMER:
            min_booking_time = dao.get_staff_min_booking_time()
        else:
            min_booking_time = dao.get_customer_min_booking_time()

        remaining_time_to_book = (self.depart_time - dt.now()).total_seconds() / 60
        if remaining_time_to_book < min_booking_time:
            return False

        return True

    def get_seat_by_id(self, seat_id):
        return next((fs for fs in self.seats if fs.id == seat_id), None)


class Stopover(db.Model):
    __tablename__ = "stopovers"
    __table_args__ = (
        CheckConstraint("arrival_time < departure_time", name="check_times"),
        UniqueConstraint("flight_id", "order", name="unique_flight_order"),
    )

    airport_id = Column(
        Integer, ForeignKey("airports.id"), primary_key=True, nullable=False
    )
    flight_id = Column(
        Integer,
        ForeignKey("flights.id"),
        primary_key=True,
        nullable=False,
    )
    order = Column(Integer, primary_key=True, nullable=False)
    arrival_time = Column(DateTime, nullable=False)  # Thời gian đến
    departure_time = Column(DateTime, nullable=False)  # Thời gian đi
    note = Column(Text, nullable=True)

    # Quan hệ
    airport = relationship("Airport", backref="stopovers", lazy=True)

    def __repr__(self):
        return (
            f"Stopover('{self.airport_id}', '{self.flight_id}', "
            f"'{self.arrival_time}', '{self.departure_time}', '{self.order}')"
        )

    def to_dict(self):
        return {
            "airport_id": self.airport_id,
            "flight_id": self.flight_id,
            "arrival_time": self.arrival_time.isoformat(),
            "departure_time": self.departure_time.isoformat(),
            "order": self.order,
        }


class Regulation(db.Model):
    __tablename__ = "regulations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(150), unique=True, nullable=False)
    value = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
