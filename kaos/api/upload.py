"""This file contains code for uploading ephemeris files via POST requests.

Author: Team KMC-70.
"""
import json
import os
from flask import Flask, Blueprint, request, render_template, jsonify
from werkzeug.utils import secure_filename
from kaos.models import ResponseHistory
from kaos.models.parser import parse_ephemeris_file
from .errors import InputError


app = Flask(__name__)
app.config['UPLOAD_DIRECTORY'] = "ephemeris"


# pylint: disable=invalid-name
upload_bp = Blueprint('upload', __name__, url_prefix='/upload')
# pylint: enable=invalid-name


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() == 'e'


@upload_bp.route('')
def render_upload():
    return render_template("upload.html")


@upload_bp.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    """ Upload ephemeris files via POST requests.

    Returns:
        On success: HTTP 200 if filename successfully
        On error:   HTTP error code associated with error.
    """
    if request.method == 'POST':
        # check if the post request has included the file
        if 'file' not in request.files:
            raise InputError("file", "file is missing from POST request")
        file = request.files['file']

        # check if filename included by browser
        if file.filename == '':
            raise InputError("filename", "empty filename")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            local_filename = os.path.join(app.config['UPLOAD_DIRECTORY'], filename)
            file.save(local_filename)

            # add the ephemeris data to the DB
            sat_id = parse_ephemeris_file(local_filename)
            if sat_id < 0:
                raise InputError("contents", "malformed ephemeris file")
    return jsonify({'response': 'OK', 'status_code': 200})
