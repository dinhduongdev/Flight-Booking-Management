from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from app.blueprints.main import main_bp
from app.blueprints.auth import auth_bp
from app.blueprints.errors import errors

from app.config import Config


app = Flask(__name__)
config = Config()
app.config.from_object(config)

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(errors)

db = SQLAlchemy(app)
