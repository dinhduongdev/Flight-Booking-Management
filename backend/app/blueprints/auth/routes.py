from flask import Blueprint, jsonify

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/hello", methods=["GET"])
def hello_auth():
    return jsonify({"message": "Hello from the Auth Blueprint!"})
