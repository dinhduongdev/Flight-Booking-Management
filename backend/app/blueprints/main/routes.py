from flask import render_template

# Import the blueprint instance from the `__init__.py`
from . import main_bp
from app.blueprints.auth import dao as auth_dao


@main_bp.route("/")
def home():
    return render_template("main/home.html")


@main_bp.route("/about")
def about():
    return render_template("main/about.html")
