import os
from urllib.parse import quote
from dotenv import load_dotenv
import json
from pathlib import Path

load_dotenv()


class MySQLConfig:
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "admin")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_HOST_PORT = os.getenv("MYSQL_HOST_PORT", "3306")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "flight_booking")
    DB_URI = f"mysql+pymysql://{MYSQL_USER}:{quote(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_HOST_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"


class PostgresConfig:
    # use for deployment on render.com
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "flight_booking")
    DB_URI = f"postgresql+psycopg2://{POSTGRES_USER}:{quote(POSTGRES_PASSWORD)}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"


class FlaskConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "6789lacachbonanhsong")
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = os.getenv("SQLITE_URI")
    # SQLALCHEMY_DATABASE_URI = PostgresConfig.DB_URI
    SQLALCHEMY_DATABASE_URI = PostgresConfig.DB_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.googlemail.com")
    MAIL_PORT = os.getenv("MAIL_PORT", 587)
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", True)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    FLASK_ADMIN_SWATCH = "lux"


class CloudinaryConfig:
    CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    API_KEY = os.getenv("CLOUDINARY_API_KEY")
    API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    SECURE = os.getenv("CLOUDINARY_SECURE")
    DEFAULT_AVATARS_PATH = os.getenv("CLOUDINARY_DEFAULT_AVATARS_PATH")


CLIENT_CONFIG_PATH = Path(__file__).parent.parent / "client_secret.json"


class GoogleAuthConfig:
    CLIENT_CONFIG = json.loads(CLIENT_CONFIG_PATH.read_text())
    SCOPES = [
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid",
    ]
    REDIRECT_URI = CLIENT_CONFIG["web"]["redirect_uris"][0]


class VNPayConfig:
    VNPAY_RETURN_URL = os.getenv("VNPAY_RETURN_URL")
    VNPAY_PAYMENT_URL = os.getenv("VNPAY_PAYMENT_URL")
    VNPAY_API_URL = os.getenv("VNPAY_API_URL")
    VNPAY_TMN_CODE = os.getenv("VNPAY_TMN_CODE")
    VNPAY_HASH_SECRET_KEY = os.getenv("VNPAY_HASH_SECRET_KEY")
