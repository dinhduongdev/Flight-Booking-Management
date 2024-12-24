from functools import wraps
from flask_login import current_user
from flask import redirect, flash, url_for, abort

from .models import UserRole
from flask_login import login_required


def anonymous_user(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if current_user.is_authenticated:
            flash("You are already logged in!", category="info")
            return redirect(url_for("main.home"))

        return f(*args, **kwargs)

    return decorated_func


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_func(*args, **kwargs):
        if current_user.role != UserRole.ADMIN:
            abort(403)
        return f(*args, **kwargs)

    return decorated_func


def flight_manager_required(f):
    @wraps(f)
    @login_required
    def decorated_func(*args, **kwargs):
        if current_user.role not in [UserRole.FLIGHT_MANAGER, UserRole.ADMIN]:
            abort(403)
        return f(*args, **kwargs)

    return decorated_func

def admin_or_flight_manager_required(f):
    @wraps(f)
    @login_required
    def decorated_func(*args, **kwargs):
        if current_user.role not in [UserRole.ADMIN, UserRole.FLIGHT_MANAGER]:
            abort(403)
        return f(*args, **kwargs)

    return decorated_func


def sales_employee_required(f):
    @wraps(f)
    @login_required
    def decorated_func(*args, **kwargs):
        if current_user.role not in [UserRole.SALES_EMPLOYEE, UserRole.ADMIN]:
            abort(403)
        return f(*args, **kwargs)

    return decorated_func
