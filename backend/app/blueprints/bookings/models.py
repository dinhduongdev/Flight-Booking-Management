from enum import Enum as BaseEnum
from sqlalchemy import Column, Integer, Enum, ForeignKey, DateTime, Double, Boolean
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship, backref
from datetime import datetime as dt

from app import db


class Reservation(db.Model):
    __tablename__ = "reservations"
    __table_args__ = (UniqueConstraint("owner_id", "flight_seat_id"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    flight_seat_id = Column(Integer, ForeignKey("flight_seats.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=dt.now)
    is_deleted = Column(Boolean, nullable=False, default=False)

    owner = relationship(
        "User",
        foreign_keys=[owner_id],
        backref="reservations",
    )
    author = relationship(
        "User",
        foreign_keys=[author_id],
        backref="created_reservations",
    )
    flight_seat = relationship("FlightSeat", backref="reservations", lazy=True)
    payment = relationship(
        "Payment",
        uselist=False,
        backref="reservation",
        lazy=True,
    )

    def __repr__(self):
        return f"Reservation('{self.id}', '{self.flight_seat_id}', '{self.owner_id}')"

    def is_paid(self):
        return self.payment and self.payment.status == PaymentStatus.SUCCESS

    def is_editable(self):
        """
        Reservation is editable if it is unpaid and the flight is bookable
        """
        if self.is_deleted or self.is_paid():
            return False
        return self.flight_seat.flight.is_bookable_now()


class PaymentStatus(BaseEnum):
    SUCCESS = 1
    FAILED = 2
    PENDING = 3

    def __str__(self):
        return self.name.title()


class Payment(db.Model):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    amount = Column(Double, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=dt.now)

    def __repr__(self):
        return f"Bill('{self.id}', '{self.reservation.id}', '{self.amount}')"
