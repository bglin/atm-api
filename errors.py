from flask import jsonify


def custom_error_message(message,status):
    res = jsonify({"message":message})
    res.status_code = status

    return res