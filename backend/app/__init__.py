from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import cloudinary
from authlib.integrations.flask_client import OAuth
from flask_mail import Mail

import os
from app.config import *


app = Flask(__name__)
app.config.from_object(FlaskConfig)
app.config.from_object(VNPayConfig)
app.config["PAGE_SIZE"] = 20

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

cloudinary.config(
    cloud_name=CloudinaryConfig.CLOUD_NAME,
    api_key=CloudinaryConfig.API_KEY,
    api_secret=CloudinaryConfig.API_SECRET,
    secure=CloudinaryConfig.SECURE,
)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
oauth = OAuth(app)

from app.blueprints import admin


from app.blueprints.main import main_bp
from app.blueprints.auth import auth_bp
from app.blueprints.flights import flights_bp
from app.blueprints.bookings import bookings_bp
from app.blueprints.errors import errors

# from app.blueprints.payment import payment_bp


app.register_blueprint(main_bp)
app.register_blueprint(bookings_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(errors)
app.register_blueprint(flights_bp)
# app.register_blueprint(payment_bp)
