from flask import Blueprint

flights_bp = Blueprint("flights", __name__)

from . import routes
