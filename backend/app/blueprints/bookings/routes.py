from flask import request, render_template, redirect, url_for, flash, session
from flask_login import login_required, current_user
from datetime import datetime as dt

from . import bookings_bp
from app.blueprints.flights import dao as flight_dao
from app.blueprints.auth import dao as auth_dao
from app.blueprints.auth.models import UserRole
from . import dao as booking_dao
from .forms import BookingForm
from .models import Reservation, PaymentStatus, Payment
import re
from app.blueprints.auth import decorators
from app.blueprints.bookings.vnpay import vnpay
from app import app, db


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


@bookings_bp.route("/booking", methods=["GET", "POST"])
@login_required
def reserve_ticket():
    form = BookingForm()
    flight = request.args.get("flight", type=flight_dao.get_flight_by_id)
    seat_class = request.args.get("seat_class", type=flight_dao.get_seat_class_by_id)

    # Check params are valid
    if not validate_flight_seat_class(flight, seat_class):
        return redirect(url_for("main.home"))

    # if method is POST and form is valid
    if form.validate_on_submit():
        owner = auth_dao.get_user_by_citizen_id(form.citizen_id.data)
        flight_seat_id = request.form.get("flight_seat_id", type=int)

        # Check if flight seat is valid
        flight_seat = flight.get_seat_by_id(flight_seat_id)
        if not flight_seat or flight_seat.is_sold():
            flash("Invalid flight seat or sold!", "danger")
            return redirect(request.referrer)

        # Check if user has already booked this flight seat whether it is paid or not
        if owner.get_reservation_by_flight_seat_id(flight_seat_id):
            flash(f"This user has already booked this flight seat!", "danger")
            return redirect(request.referrer)

        # Store reservation details in session
        session["pending_reservation"] = {
            "owner_id": owner.id,
            "author_id": current_user.id,
            "flight_seat_id": flight_seat_id,
        }

        return redirect(url_for("bookings.confirmation"))

    return render_template(
        "bookings/index.html",
        form=form,
        flight=flight,
        seat_class=seat_class,
        search_time=dt.now(),
        staff_min_booking_time=flight_dao.get_staff_min_booking_time(),
        customer_min_booking_time=flight_dao.get_customer_min_booking_time(),
    )


@bookings_bp.route("/booking/confirmation", methods=["GET", "POST"])
@login_required
def confirmation():
    """
    Confirm the reservation and store it in the database.
    If the user is staff, the reservation is created along with payment (Staff sells ticket offline).
    """
    # Retrieve reservation details from session
    reservation_details = session.get("pending_reservation", None)
    if not reservation_details:
        flash("No reservation to confirm", "danger")
        return redirect(url_for("bookings.manage_own_bookings"))

    owner = auth_dao.get_user_by_id(reservation_details["owner_id"])
    author = auth_dao.get_user_by_id(reservation_details["author_id"])
    seat = flight_dao.get_flight_seat_by_id(reservation_details["flight_seat_id"])
    flight = seat.flight

    # Check if flight is still bookable
    if not flight.is_bookable_now() or seat.is_sold():
        session.pop("reservation_details", None)
        flash("Flight is no longer bookable", "danger")
        return redirect(request.referrer)

    # Clear the reservation details from session
    if request.method == "POST":
        session.pop("pending_reservation", None)
        # Get payment type if user is staff
        if current_user.role != UserRole.CUSTOMER:
            payment_type = request.form.get("payment_type")
        else:
            payment_type = "card"

        # Create reservation
        if payment_type == "cash":
            booking_dao.add_reservation(owner.id, author.id, seat.id, is_paid=True)
        elif payment_type == "card":
            booking_dao.add_reservation(owner.id, author.id, seat.id)

        flash("Reservation created!", "success")
        return redirect(url_for("bookings.manage_own_bookings"))

    return render_template(
        "bookings/confirmation.html",
        owner=owner,
        author=author,
        seat=seat,
        flight=flight,
    )


@bookings_bp.route("/manage-bookings/own")
@login_required
def manage_own_bookings():
    """
    Only the user who owns the reservation can see it.
    """
    page_num = request.args.get("page", default=1, type=int)
    reservations = booking_dao.get_reservations_of_owned_user(current_user.id, page_num)
    return render_template("bookings/manage_bookings.html", page=reservations)


@bookings_bp.route("/manage-bookings/created-for-others")
@login_required
def manage_bookings_created_for_others():
    """
    Only the user who created the reservation can see it.
    """
    page_num = request.args.get("page", default=1, type=int)
    reservations = booking_dao.get_reservations_created_for_others(
        current_user.id, page_num
    )
    return render_template("bookings/manage_bookings.html", page=reservations)


@bookings_bp.route(
    "/booking/edit-reservation/<int:reservation_id>", methods=["GET", "POST"]
)
@login_required
def edit_reservation(reservation_id):
    """
    Only the user and author of the reservation can edit it.
    The user can't edit the reservation once paid.
    """
    reservation = booking_dao.get_reservation_by_id_and_user(
        reservation_id, current_user.id
    )
    if not reservation:
        flash("Reservation not found", "danger")
        return redirect(url_for("bookings.manage_own_bookings"))

    if not reservation.is_editable():
        flash("You can't edit this reservation", "danger")
        return redirect(url_for("bookings.manage_own_bookings"))

    flight = reservation.flight_seat.flight
    seat_class = request.args.get(
        "seat_class",
        type=flight_dao.get_seat_class_by_id,
        default=reservation.flight_seat.aircraft_seat.seat_class,
    )
    if not validate_flight_seat_class(flight, seat_class):
        return redirect(request.referrer)

    if request.method == "POST":
        flight_seat_id = request.form.get("flight_seat_id", type=int)

        # Check if flight seat is valid
        flight_seat = flight.get_seat_by_id(flight_seat_id)
        if not flight_seat or flight_seat.is_sold():
            flash("Invalid flight seat or sold!", "danger")
            return redirect(request.referrer)

        # Check if owner has already booked this flight seat whether it is paid or not
        if reservation.owner.get_reservation_by_flight_seat_id(flight_seat_id):
            flash(f"This user has already booked this flight seat!", "danger")
            return redirect(request.referrer)

        # Edit reservation
        reservation = booking_dao.update_reservation_seat(reservation, flight_seat_id)
        return redirect(url_for("bookings.manage_own_bookings"))

    return render_template(
        "bookings/change_seat.html",
        reservation=reservation,
        seat_class=seat_class,
        search_time=dt.now(),
        staff_min_booking_time=flight_dao.get_staff_min_booking_time(),
        customer_min_booking_time=flight_dao.get_customer_min_booking_time(),
    )


@bookings_bp.route("/manage-bookings/delete/<int:reservation_id>", methods=["POST"])
@login_required
def delete_reservation(reservation_id):
    """
    Only the user who owns the reservation can delete it.
    Even author of the reservation can't delete it.
    """
    if booking_dao.delete_reservation_of_owner(current_user.id, reservation_id):
        flash("Reservation deleted", "success")
    else:
        flash("Reservation not found", "danger")

    response = redirect(request.referrer)
    return response


def get_client_ip(request):
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.remote_addr
    return ip


@bookings_bp.route("/booking/payment/<id>", methods=["GET", "POST"])
@decorators.login_required
def payment(id):
    if request.method == "GET":
        # ...
        reservation = booking_dao.get_reservation_by_id_and_user(id, current_user.id)
        order_id = ""
        message = ""

        if reservation:
            if reservation.is_paid():
                message = "THIS TICKET HAS BEEN PAID"
            else:
                order_id = str(reservation.id)
        else:
            message = "TICKET NOT FOUND"

        return render_template(
            "bookings/payment.html",
            order_id=order_id,
            reservation=reservation,
            message=message,
        )
    else:
        order_id = request.form.get("order_id")
        order_type = request.form.get("order_type")
        amount = float(request.form.get("amount"))
        order_desc = request.form.get("order_desc")
        bank_code = request.form.get("bank_code")
        language = request.form.get("language")
        ipaddr = get_client_ip(request)

        vnp = vnpay()
        vnp.requestData["vnp_Version"] = "2.1.0"
        vnp.requestData["vnp_Command"] = "pay"
        vnp.requestData["vnp_TmnCode"] = app.config["VNPAY_TMN_CODE"]
        vnp.requestData["vnp_Amount"] = int(amount * 100)
        vnp.requestData["vnp_CurrCode"] = "VND"
        vnp.requestData["vnp_TxnRef"] = order_id
        vnp.requestData["vnp_OrderInfo"] = order_desc
        vnp.requestData["vnp_OrderType"] = order_type
        # Check language, default: vn
        if language and language != "":
            vnp.requestData["vnp_Locale"] = language
        else:
            vnp.requestData["vnp_Locale"] = "vn"
            # Check bank_code, if bank_code is empty, customer will be selected bank on VNPAY
        if bank_code and bank_code != "":
            vnp.requestData["vnp_BankCode"] = bank_code

        vnp.requestData["vnp_CreateDate"] = dt.now().strftime("%Y%m%d%H%M%S")
        vnp.requestData["vnp_IpAddr"] = ipaddr
        vnp.requestData["vnp_ReturnUrl"] = app.config["VNPAY_RETURN_URL"]
        vnpay_payment_url = vnp.get_payment_url(
            app.config["VNPAY_PAYMENT_URL"], app.config["VNPAY_HASH_SECRET_KEY"]
        )
        return redirect(vnpay_payment_url)


@bookings_bp.route("/booking/payment_return", methods=["GET"])
def payment_return():
    inputData = request.args
    if inputData:
        vnp = vnpay()
        vnp.responseData = dict(inputData)
        order_id = inputData.get("vnp_TxnRef")
        amount = int(inputData.get("vnp_Amount")) / 100
        order_desc = inputData.get("vnp_OrderInfo")
        vnp_TransactionNo = inputData.get("vnp_TransactionNo")
        vnp_ResponseCode = inputData.get("vnp_ResponseCode")
        # vnp_TmnCode = inputData['vnp_TmnCode']
        # vnp_PayDate = inputData['vnp_PayDate']
        # vnp_BankCode = inputData['vnp_BankCode']
        # vnp_CardType = inputData['vnp_CardType']

        if vnp.validate_response(app.config["VNPAY_HASH_SECRET_KEY"]):
            if vnp_ResponseCode == "00":
                # reservation
                reservation_id = order_id
                booking_dao.add_payment(
                    reservation_id=reservation_id,
                    amount=amount,
                    status=PaymentStatus.SUCCESS,
                )

                reservation = booking_dao.get_reservation_by_id(reservation_id)
                flight_seat = reservation.flight_seat
                flight = flight_seat.flight

                return render_template(
                    "bookings/payment_return.html",
                    title="Payment result",
                    result="Success",
                    order_id=order_id,
                    amount=amount,
                    order_desc=order_desc,
                    vnp_TransactionNo=vnp_TransactionNo,
                    vnp_ResponseCode=vnp_ResponseCode,
                    reservation=reservation,
                    flight=flight,
                    flight_seat=flight_seat,
                )
            elif vnp_ResponseCode == "24":
                # reservation
                reservation_id = order_id
                reservation = booking_dao.get_reservation_by_id(reservation_id)

                return render_template(
                    "bookings/payment_return.html",
                    title="Payment result",
                    result="Canceled",
                    order_id=order_id,
                    amount=amount,
                    order_desc=order_desc,
                    vnp_TransactionNo=vnp_TransactionNo,
                    vnp_ResponseCode=vnp_ResponseCode,
                    reservation=reservation,
                )
            else:
                return render_template(
                    "bookings/payment_return.html",
                    title="Payment result",
                    result="Error",
                    order_id=order_id,
                    amount=amount,
                    order_desc=order_desc,
                    vnp_TransactionNo=vnp_TransactionNo,
                    vnp_ResponseCode=vnp_ResponseCode,
                )
        else:
            return render_template(
                "bookings/payment_return.html",
                title="Payment result",
                result="Error",
                order_id=order_id,
                amount=amount,
                order_desc=order_desc,
                vnp_TransactionNo=vnp_TransactionNo,
                vnp_ResponseCode=vnp_ResponseCode,
                msg="Invalid checksum",
            )
    return render_template(
        "bookings/payment_return.html", title="Payment result", result=""
    )
