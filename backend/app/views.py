"""
Flask Documentation:     https://flask.palletsprojects.com/
Jinja2 Documentation:    https://jinja.palletsprojects.com/
Werkzeug Documentation:  https://werkzeug.palletsprojects.com/
This file creates your application.
"""

import site

from app import app, Config, mongo, Mqtt
from flask import request, jsonify, send_from_directory
from json import dumps, loads
from werkzeug.utils import secure_filename
from os import getcwd
from os.path import join, exists
from time import time


#####################################
#   Helper functions                #
#####################################

def is_valid_passcode(passcode):
    return isinstance(passcode, str) and passcode.isdigit() and len(passcode) == 4


def parse_update_payload():
    """
    Try several ways to read the payload so it works with:
    1) normal frontend/postman JSON
    2) raw JSON body from ESP/Nano
    3) badly wrapped form payloads if they occur
    """
    # 1. Normal Flask JSON parsing first
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload

    # 2. Raw body fallback (best for ESP AT HTTP POST bodies)
    raw_body = request.get_data(as_text=True)

    if raw_body:
        raw_body = raw_body.strip().replace("\x00", "")
        print("RAW BODY REPR:", repr(raw_body))

        # Sometimes raw body is valid JSON already
        try:
            parsed = loads(raw_body)
            if isinstance(parsed, dict):
                return parsed
        except Exception as e:
            print("JSON raw parse failed:", e)

    # 3. Form fallback (not expected for /api/update, but safe)
    if request.form:
        form_dict = dict(request.form)
        print("FORM PAYLOAD:", form_dict)
        return form_dict

    return None


def normalize_update_payload(payload):
    """
    Ensure required keys exist and numeric fields are numeric.
    """
    required = {"id", "type", "radar", "waterheight", "reserve", "percentage"}

    if not isinstance(payload, dict):
        return None, "payload_not_dict"

    missing = sorted(list(required.difference(set(payload.keys()))))
    if missing:
        return None, f"missing_keys:{missing}"

    try:
        normalized = {
            "id": str(payload["id"]),
            "type": str(payload["type"]),
            "radar": float(payload["radar"]),
            "waterheight": float(payload["waterheight"]),
            "reserve": float(payload["reserve"]),
            "percentage": int(float(payload["percentage"]))
        }
        return normalized, None
    except Exception as e:
        return None, f"type_conversion_failed:{e}"


#####################################
#   Routing for your application    #
#####################################

@app.route('/api/set/combination', methods=['POST'])
def set_combination():
    try:
        passcode = request.form.get("passcode", "").strip()
        print(f"PASSCODE RECEIVED: {passcode}")

        if not is_valid_passcode(passcode):
            return jsonify({"status": "failed", "data": "failed"}), 400

        ok = mongo.set_passcode(passcode)

        if ok:
            return jsonify({"status": "complete", "data": "complete"}), 200

        return jsonify({"status": "failed", "data": "failed"}), 500

    except Exception as e:
        print(f"set_combination error: {e}")
        return jsonify({"status": "failed", "data": "failed"}), 500


@app.route('/api/check/combination', methods=['POST'])
def check_combination():
    try:
        passcode = request.form.get("passcode", "").strip()
        print(f"PASSCODE CHECK RECEIVED: {passcode}")

        if not is_valid_passcode(passcode):
            return jsonify({"status": "failed", "data": "failed"}), 400

        count = mongo.check_passcode(passcode)

        if count > 0:
            return jsonify({"status": "complete", "data": "complete"}), 200

        return jsonify({"status": "failed", "data": "failed"}), 200

    except Exception as e:
        print(f"check_combination error: {e}")
        return jsonify({"status": "failed", "data": "failed"}), 500


@app.route('/api/update', methods=['POST'])
def update():
    try:
        raw_body = request.get_data(as_text=True)
        print("RAW BODY REPR:", repr(raw_body))

        if not raw_body or raw_body.strip() == "":
            return jsonify({"status": "failed", "data": "empty_body"}), 400

        try:
            payload = loads(raw_body)
        except Exception as e:
            print("JSON LOAD ERROR:", e)
            return jsonify({"status": "failed", "data": "invalid_json"}), 400

        print("PARSED PAYLOAD:", payload)

        required = {"id", "type", "radar", "waterheight", "reserve", "percentage"}
        if not isinstance(payload, dict):
            return jsonify({"status": "failed", "data": "not_dict"}), 400

        missing = sorted(list(required.difference(set(payload.keys()))))
        if missing:
            print("MISSING KEYS:", missing)
            return jsonify({"status": "failed", "data": "missing_keys", "missing": missing}), 400

        modified = dict(payload)
        modified["timestamp"] = int(time())

        inserted = mongo.insert_radar(modified)
        print("RADAR INSERT:", inserted)

        if not inserted:
            return jsonify({"status": "failed", "data": "db_insert_failed"}), 500

        try:
            topic = "elet2415/radar"
            payload_json = dumps(modified)
            published = Mqtt.publish(topic, payload_json)
            print("MQTT publish result:", published)
        except Exception as e:
            print("MQTT publish failed (ignored):", e)

        return jsonify({"status": "complete", "data": "complete"}), 200

    except Exception as e:
        print(f"/api/update error: {str(e)}")
        return jsonify({"status": "failed", "data": "failed"}), 500


@app.route('/api/reserve/<start>/<end>', methods=['GET'])
def reserve(start, end):
    try:
        start_ts = int(float(start))
        end_ts = int(float(end))

        docs = mongo.get_radar_range(start_ts, end_ts)

        if docs is None:
            docs = []

        return jsonify({"status": "found", "data": docs}), 200

    except Exception as e:
        print(f"/api/reserve error: {e}")
        return jsonify({"status": "failed", "data": 0}), 500


@app.route('/api/avg/<start>/<end>', methods=['GET'])
def average(start, end):
    try:
        start_ts = int(float(start))
        end_ts = int(float(end))

        avg_list = mongo.avg_reserve(start_ts, end_ts)

        avg = 0
        if isinstance(avg_list, list) and len(avg_list) > 0:
            avg = avg_list[0].get("average", 0) or 0

        return jsonify({"status": "found", "data": float(avg)}), 200

    except Exception as e:
        print(f"/api/avg error: {e}")
        return jsonify({"status": "failed", "data": 0}), 500


@app.route('/api/file/get/<filename>', methods=['GET'])
def get_images(filename):
    """Returns requested file from uploads folder"""
    directory = join(getcwd(), Config.UPLOADS_FOLDER)
    filePath = join(getcwd(), Config.UPLOADS_FOLDER, filename)

    if exists(filePath):
        return send_from_directory(directory, filename)

    return jsonify({"status": "file not found"}), 404


@app.route('/api/file/upload', methods=["POST"])
def upload():
    """Saves a file to the uploads folder"""
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(join(getcwd(), Config.UPLOADS_FOLDER, filename))
    return jsonify({"status": "File upload successful", "filename": f"{filename}"})


###############################################################
# The functions below should be applicable to all Flask apps. #
###############################################################

@app.after_request
def add_header(response):
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.errorhandler(405)
def page_not_found(error):
    return jsonify({"status": 404}), 404