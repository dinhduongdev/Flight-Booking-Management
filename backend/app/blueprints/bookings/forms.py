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

from app.blueprints.auth import dao as auth_dao


class BookingForm(FlaskForm):
    citizen_id = StringField("Citizen ID", validators=[DataRequired()])
    submit = SubmitField("Next")

    def validate_citizen_id(self, citizen_id):
        if not auth_dao.get_user_by_citizen_id(citizen_id.data):
            raise ValidationError(
                "This citizen ID is not asscociated with any account!"
            )
