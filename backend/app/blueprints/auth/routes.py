from flask import render_template, redirect, url_for, flash, session, request
from flask_login import login_user, current_user, logout_user, login_required

from app import login_manager, db, bcrypt
from .forms import (
    SignUpForm,
    LogInForm,
    UpdateAccountForm,
    RequestResetForm,
    ResetPasswordForm,
)
from . import auth_bp, google_auth, dao
from . import decorators


@auth_bp.route("/login", methods=["GET", "POST"])
@decorators.anonymous_user
def login():
    form = LogInForm()
    # if method is POST and form is valid
    if form.validate_on_submit():
        user = dao.authenticate_user(form.email.data, form.password.data)
        if user:
            login_user(user, remember=form.remember.data)
            flash(
                f"Welcome back, {user.first_name} {user.last_name}!",
                category="success",
            )
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("main.home"))
        flash("Login failed. Please check your email and password.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/signup", methods=["GET", "POST"])
@decorators.anonymous_user
def signup():
    form = SignUpForm()
    if "user_info" in session:
        user_info = session["user_info"]
        form.email.data = user_info["email"]
        form.email.render_kw = {"readonly": True}
        form.first_name.data = user_info["first_name"]
        form.first_name.render_kw = {"readonly": True}
        form.last_name.data = user_info["last_name"]
        form.last_name.render_kw = {"readonly": True}
        form.avatar.data = user_info["avatar"]
        form.avatar.render_kw = {"readonly": True}
        session.pop("user_info", None)
    # if method is POST and form is valid
    if form.validate_on_submit():
        user = dao.add_user(
            form.email.data,
            form.password.data,
            form.citizen_id.data,
            form.first_name.data,
            form.last_name.data,
            form.phone.data,
            avatar=form.avatar.data,
        )
        flash(
            f"Account created successfully for {form.email.data}!", category="success"
        )
        login_user(user)
        return redirect(url_for("main.home"))
    return render_template("auth/signup.html", form=form)


@login_manager.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@auth_bp.route("/logout")
def logout_process():
    logout_user()
    session.clear()
    return redirect("/login")


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("user/profile.html")


@auth_bp.route("/update_account", methods=["GET", "POST"])
@login_required
def update_account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        if form.picture.data:
            dao.update_user_avatar(current_user, form.picture.data)
            flash("It's gonna take a while to update your avatar!", "info")
        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("auth.profile"))
    return render_template("user/update_account.html", form=form)


@auth_bp.route("/login/google")
@decorators.anonymous_user
def google_login():
    authorization_url, state = google_auth.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@auth_bp.route("/authorize/google")
@decorators.anonymous_user
def google_authorize():
    """
    This route is called after the user has authorized the app on Google.\n
    If the user is already in the database, log them in.\n
    If the user is not in the database, save their information and redirect them to the signup page with their gg info.
    """
    try:
        user_oauth = dao.get_user_oauth()
        print(user_oauth)
        user = dao.get_user_by_email(user_oauth["email"])
        if user is None:
            flash(
                "You are a few steps away from creating an account. Please fill in the form below 🥳",
                "info",
            )
            session["user_info"] = {
                "email": user_oauth["email"],
                "first_name": user_oauth["given_name"],
                "last_name": user_oauth["family_name"],
                "avatar": user_oauth["picture"],
            }
            return redirect(url_for("auth.signup"))
        flash(f"Welcome back, {user.first_name} {user.last_name}!", "success")
        login_user(user)
    except Exception as err:
        print(err)
        flash(
            "An error occurred while trying to log you in. Please try again.", "danger"
        )
    return redirect(url_for("main.home"))


@auth_bp.route("/reset_password", methods=["GET", "POST"])
@decorators.anonymous_user
def reset_request():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = dao.get_user_by_email(form.email.data)
        dao.send_reset_email(user)
        flash(
            "An email has been sent with instructions to reset your password.", "info"
        )
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_request.html", form=form, title="Reset Password")


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
@decorators.anonymous_user
def reset_token(token):
    user = dao.verify_reset_token(token)
    if user is None:
        flash("That is an invalid or expired token", "warning")
        return redirect(url_for("auth.reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        dao.change_password(user, form.password.data)
        flash("Your password has been updated! You are now able to log in", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_token.html", form=form, title="Reset Password")
