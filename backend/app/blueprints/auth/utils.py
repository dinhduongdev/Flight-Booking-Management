from flask_mail import Message
from flask import render_template
import random as rd
import cloudinary.uploader
import cloudinary.api
import requests
from flask import request
from pip._vendor import cachecontrol
from google.oauth2 import id_token
import google.auth.transport.requests
from pathlib import Path


from app.config import CloudinaryConfig
from app import mail, bcrypt
from . import google_auth


def get_cloudinary_default_imgs():
    try:
        print("Fetching default images from cloudinary...")
        resources = cloudinary.api.resources_by_asset_folder(
            CloudinaryConfig.DEFAULT_AVATARS_PATH, fields=["secure_url"]
        )
        return [resource["secure_url"] for resource in resources["resources"]]
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


DEFAULT_PROFILE_PICTURES = get_cloudinary_default_imgs()
PROFILE_PICTURES_PATH = str(Path(CloudinaryConfig.DEFAULT_AVATARS_PATH).parent).replace(
    "\\", "/"
)


def randomize_profile_img():
    return rd.choice(DEFAULT_PROFILE_PICTURES)


def send_reset_email(user):
    token = user.get_reset_token()
    message = Message(
        subject="Password Reset Request",
        sender="noreply@6789lacachbonanhsong.com",
        recipients=[user.email],
        html=render_template("auth/reset_email.html", user=user, token=token),
    )
    mail.send(message)


def replace_user_avatar(user, avatar):
    """
    - If the avatar is one of the default images, upload the image to cloudinary\n
    - Else replace it
    """
    if user.avatar not in DEFAULT_PROFILE_PICTURES:
        cloudinary.uploader.destroy(user.avatar)
    res = cloudinary.uploader.upload(
        avatar,
        use_asset_folder_as_public_id_prefix=True,
        folder=PROFILE_PICTURES_PATH,
        public_id=user.email,
    )
    return res["secure_url"]


def generate_hashed_password(password):
    return bcrypt.generate_password_hash(password).decode("utf-8")


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
