from itsdangerous import URLSafeTimedSerializer as Serializer


from app import db, bcrypt, app
from .models import User, UserRole
from . import utils


def get_user_by_id(user_id):
    return User.query.get(user_id)


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def get_user_by_citizen_id(citizen_id):
    return User.query.filter_by(citizen_id=citizen_id).first()


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
    hashed_password = utils.generate_hashed_password(password)
    user = User(
        email=email,
        password=hashed_password,
        role=role,
        citizen_id=citizen_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        avatar=avatar if avatar else utils.randomize_profile_img(),
    )
    db.session.add(user)
    db.session.commit()
    return user


def update_user_avatar(user, avatar):
    user.avatar = utils.replace_user_avatar(user, avatar)
    db.session.commit()


def authenticate_user(email, password):
    user = get_user_by_email(email)
    if user and bcrypt.check_password_hash(user.password, password):
        return user
    return None


def change_password(user, password):
    user.password = utils.generate_hashed_password(password)
    db.session.commit()


def verify_reset_token(token, expires_sec=300):
    s = Serializer(app.config["SECRET_KEY"])
    try:
        user_id = s.loads(token, max_age=expires_sec, salt="something")["user_id"]
    except:
        return None
    return User.query.get(user_id)
