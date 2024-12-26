from flask import flash
from flask_mail import Mail, Message
from flask import render_template
from app import mail


def validate_flight_seat_class(flight, seat_class):
    """
    1. Check if flight and seat class are valid
    2. Check if this flight is bookable now
    3. Check if flight has the seat class
    4. Check if there are available seats for the seat class
    """
    if not flight or not seat_class:
        flash("Invalid flight or seat class", "danger")
        return False
    if not flight.is_bookable_now():
        flash("You are not allowed to book this flight", "danger")
        return False
    remaining_seatclasses_and_info = flight.get_remaining_seatclasses_and_info()
    if seat_class.id not in remaining_seatclasses_and_info:
        flash("Flight doesn't have this seat class", "danger")
        return False
    if remaining_seatclasses_and_info[seat_class.id]["remaining"] == 0:
        flash("No available seats", "danger")
        return False
    return True


def send_flight_ticket_email(reservation, email):
    message = Message(
        subject="Flight Ticket",
        sender="noreply@6789lacachbonanhsong.com",
        recipients=[email],
        html=render_template(
            "bookings/ticket_email.html", reservation=reservation, email=True
        ),
    )
    mail.send(message)
