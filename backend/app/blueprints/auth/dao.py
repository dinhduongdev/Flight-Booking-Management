import cloudinary.api
import random as rd
import cloudinary
import cloudinary.uploader
from pathlib import Path
import requests
from flask import request, render_template
from pip._vendor import cachecontrol
from google.oauth2 import id_token
import google.auth.transport.requests
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask_mail import Message


from app import db, bcrypt, app, mail
from app import CloudinaryConfig
from .models import User, UserRole
from . import google_auth


def get_cloudinary_default_imgs():
    try:
        print("Fetching default images from cloudinary...")
        resources = cloudinary.api.resources_by_asset_folder(
            CloudinaryConfig.DEFAULT_AVATARS_PATH, fields=["secure_url"]
        )
        return [resource["secure_url"] for resource in resources["resources"]]
    except cloudinary.exceptions.Error as e:
        print(f"An error occurred: {e}")
        return []


DEFAULT_PROFILE_PICTURES = get_cloudinary_default_imgs()
PROFILE_PICTURES_PATH = str(Path(CloudinaryConfig.DEFAULT_AVATARS_PATH).parent).replace(
    "\\", "/"
)


def randomize_profile_img():
    return rd.choice(DEFAULT_PROFILE_PICTURES)


def get_user_by_id(user_id):
    return User.query.get(user_id)


def add_user(
    email,
    password,
    citizen_id,
    first_name,
    last_name,
    phone,
    role=UserRole.CUSTOMER,
    avatar=None,
):
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(
        email=email,
        password=hashed_password,
        role=role,
        citizen_id=citizen_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        avatar=avatar if avatar else randomize_profile_img(),
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if user and bcrypt.check_password_hash(user.password, password):
        return user
    return None


def get_users(limit=1000):
    return User.query.limit(limit).all()


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_user_by_citizen_id(citizen_id):
    return User.query.filter_by(citizen_id=citizen_id).first()


def update_user_avatar(user, avatar):
    """
    Update user avatar
    If the avatar is one of the default images, upload the image to cloudinary
    Else update the user's avatar with the provided image
    """
    if user.avatar not in DEFAULT_PROFILE_PICTURES:
        cloudinary.uploader.destroy(user.avatar)
    res = cloudinary.uploader.upload(
        avatar,
        use_asset_folder_as_public_id_prefix=True,
        folder=PROFILE_PICTURES_PATH,
        public_id=user.email,
    )
    user.avatar = res["secure_url"]

    db.session.commit()


def get_user_oauth():
    """
    Fetches and verifies the OAuth2 token from Google and returns the user information.
    This function performs the following steps:
    1. Fetches the OAuth2 token using the authorization response from the request URL.
    2. Retrieves the credentials from the Google OAuth2 client.
    3. Creates a cached session to handle token requests.
    4. Verifies the OAuth2 token using Google's ID token verification process.
    5. Returns the user information obtained from the verified token.
    Returns:
        dict: A dictionary containing the user information obtained from the verified OAuth2 token.
    """

    google_auth.fetch_token(authorization_response=request.url)

    credentials = google_auth.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    user_oauth = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=google_auth.client_config["client_id"],
        clock_skew_in_seconds=10,
    )
    return user_oauth


def verify_reset_token(token, expires_sec=300):
    s = Serializer(app.config["SECRET_KEY"])
    try:
        user_id = s.loads(token, max_age=expires_sec, salt="something")["user_id"]
    except:
        return None
    return User.query.get(user_id)


def send_reset_email(user):
    token = user.get_reset_token()
    message = Message(
        subject="Password Reset Request",
        sender="noreply@6789lacachbonanhsong.com",
        recipients=[user.email],
        html=render_template("auth/reset_email.html", user=user, token=token),
    )
    mail.send(message)


def change_password(user, password):
    user.password = bcrypt.generate_password_hash(password).decode("utf-8")
    db.session.commit()
