import os
from urllib.parse import quote


class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.SECRET_KEY = os.getenv("SECRET_KEY", "6789lacachbonanhsong")
        self.DEBUG = True
        self.MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
        self.MYSQL_HOST_PORT = os.getenv("MYSQL_HOST_PORT", "3306")
        self.MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "flight_booking_system")
        self.MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD", "Admin@123")

        self.SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:{quote(self.MYSQL_ROOT_PASSWORD)}@{self.MYSQL_HOST}:{self.MYSQL_HOST_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        self.SQLALCHEMY_TRACK_MODIFICATIONS = True
