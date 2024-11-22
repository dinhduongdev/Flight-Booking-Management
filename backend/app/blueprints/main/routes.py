from flask import render_template

# Import the blueprint instance from the `__init__.py`
from . import main_bp


@main_bp.route("/")
def home():
    """Render the home page."""
    return render_template("main/home.html")


@main_bp.route("/about")
def about():
    """Render the about page."""
    return render_template("main/about.html")
