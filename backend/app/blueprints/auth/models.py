from enum import Enum as BaseEnum
from sqlalchemy import Column, Integer, String, Enum
from app import db


class UserRole(BaseEnum):
    ADMIN = 1
    EMPLOYEE = 2
    USER = 3


class User(db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True)
    password = db.Column(db.String(60), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
