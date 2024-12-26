from functools import wraps
from flask_login import current_user, login_required
from flask import redirect, flash, url_for, abort

from . import dao


def user_own_this_reservation(f):
    """
    Only the owner of the un-deleted reservation can access it.
    """

    @wraps(f)
    def decorated_func(*args, **kwargs):
        reservation_id = kwargs.get("reservation_id")
        reservation = dao.get_reservation_of_owner(current_user.id, reservation_id)
        if not reservation:
            flash("Reservation not found!", "danger")
            abort(404)
        return f(*args, **kwargs)

    return decorated_func


def user_own_or_create_this_reservation(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        reservation_id = kwargs.get("reservation_id", None)
        reservation = dao.get_reservation_by_id_and_user(
            reservation_id, current_user.id
        )
        if not reservation:
            flash("Reservation not found!", "danger")
            abort(404)
        return f(*args, **kwargs)

    return decorated_func


def user_can_pay_this_reservation(f):
    """
    Only the user and author of the reservation can pay it.
    The user can't pay the reservation once paid/delete or flight is not bookable.
    """

    @wraps(f)
    @user_own_or_create_this_reservation
    def decorated_func(*args, **kwargs):
        reservation_id = kwargs.get("reservation_id")
        reservation = dao.get_reservation_by_id(reservation_id)
        if not reservation.is_payable():
            flash("You can't pay this reservation", "danger")
            return redirect(url_for("bookings.manage_own_bookings"))
        return f(*args, **kwargs)

    return decorated_func


def user_can_delete_this_reservation(f):
    """
    Only the owner of the reservation can delete it.
    The owner can't delete the reservation once paid/delete
    """

    @wraps(f)
    @user_own_this_reservation
    def decorated_func(*args, **kwargs):
        reservation_id = kwargs.get("reservation_id")
        reservation = dao.get_reservation_by_id(reservation_id)
        if reservation.is_paid():
            flash("You can't delete this reservation", "danger")
            return redirect(url_for("bookings.manage_own_bookings"))
        return f(*args, **kwargs)

    return decorated_func


def user_can_edit_this_reservation(f):
    """
    Only the user and author of the reservation can edit it.
    The user can't edit the reservation once paid/delete or flight is not bookable.
    """

    @wraps(f)
    @user_own_or_create_this_reservation
    def decorated_func(*args, **kwargs):
        reservation_id = kwargs.get("reservation_id")
        reservation = dao.get_reservation_by_id(reservation_id)
        if not reservation.is_editable():
            flash("You can't edit this reservation", "danger")
            return redirect(url_for("bookings.manage_own_bookings"))
        return f(*args, **kwargs)

    return decorated_func


def user_can_view_ticket(f):
    """
    Only the user and author of the reservation can view the ticket if it is paid.
    """

    @wraps(f)
    @user_own_or_create_this_reservation
    def decorated_func(*args, **kwargs):
        reservation_id = kwargs.get("reservation_id")
        reservation = dao.get_reservation_by_id(reservation_id)
        if not reservation.is_paid():
            flash("Unknown ticket!", "danger")
            abort(404)
        return f(*args, **kwargs)

    return decorated_func
