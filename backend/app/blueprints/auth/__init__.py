from flask import Blueprint

from app import oauth
from app import GoogleAuthConfig
from google_auth_oauthlib.flow import Flow

# Create the main blueprint
auth_bp = Blueprint("auth", __name__)

google_auth = Flow.from_client_config(
    GoogleAuthConfig.CLIENT_CONFIG,
    scopes=GoogleAuthConfig.SCOPES,
    redirect_uri=GoogleAuthConfig.REDIRECT_URI,
)
# Import routes to register them with the blueprint
from . import routes
