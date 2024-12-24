from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms import BooleanField
from wtforms import TelField
from wtforms import HiddenField
from wtforms import ValidationError
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import Email
from wtforms.validators import EqualTo
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from . import dao


class SignUpForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    citizen_id = StringField("Citizen ID", validators=[DataRequired()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    phone = TelField("Phone", validators=[DataRequired()])
    avatar = HiddenField("Hidden avatar field for Google OAuth")
    submit = SubmitField("Sign up")

    def validate_citizen_id(self, citizen_id):
        user = dao.get_user_by_citizen_id(citizen_id.data)
        if user:
            raise ValidationError("Citizen ID already exists!")

    def validate_email(self, email):
        user = dao.get_user_by_email(email.data)
        if user:
            raise ValidationError("Email already exists!")


class LogInForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")


class UpdateAccountForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    phone = TelField("Phone", validators=[DataRequired()])

    picture = FileField(
        "Update Profile Picture",
        validators=[
            FileAllowed(
                ["jpg", "png", "svg", "jpeg"],
                "Only accept: [jpg, png, svg, jpeg] file!",
            )
        ],
    )
    submit = SubmitField("Update")

    def validate_email(self, email):
        if email.data != current_user.email:
            user = dao.get_user_by_email(email.data)
            if user:
                raise ValidationError(
                    "That email is taken. Please choose a different one."
                )


class RequestResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Request Password Reset")

    def validate_email(self, email):
        user = dao.get_user_by_email(email.data)
        if user is None:
            raise ValidationError("There is no account with that email!")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Reset Password")
