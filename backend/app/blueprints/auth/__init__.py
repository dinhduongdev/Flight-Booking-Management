from flask import Blueprint

# Create the main blueprint
auth_bp = Blueprint("auth", __name__)

# Import routes to register them with the blueprint
from . import routes
