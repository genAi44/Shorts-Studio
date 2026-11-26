"""Small JSON helpers shared by the Flask routes in app.py and app_llm.py."""
from flask import jsonify, request


def err(msg, code=400):
    return jsonify({"error": msg}), code


def body():
    return request.get_json(silent=True) or {}
