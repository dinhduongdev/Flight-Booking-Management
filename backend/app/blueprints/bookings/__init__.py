from flask import Blueprint

# Create a blueprint
bookings_bp = Blueprint("bookings", __name__)

# Import the routes
from . import routes
