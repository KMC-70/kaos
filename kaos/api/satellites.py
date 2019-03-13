"""This file contains routing code for generating the satellite info.

Author: Team KMC-70.
"""
import json

from flask import Blueprint, jsonify
from kaos.models import Satellite

from .errors import NotFoundError

# pylint: disable=invalid-name
satellites_bp = Blueprint('satellites', __name__, url_prefix='/satellites')
# pylint: enable=invalid-name


@satellites_bp.route('', methods=['GET'])
def get_satellites():
    """Return the satellite id and name for each record in table Satellite
    Each API call should on success return a response with a platform_id and a platform_name.
    Querying this endpoint with this
    """

    response = []
    satellites = Satellite.query.all()
    for satellite in satellites:
        satellite_dict = {'id': satellite.platform_id, 'satellite_name': satellite.platform_name}
        response.append(satellite_dict)
    print json.dumps(response)

    if response is None:
        raise NotFoundError("No satellite found.")

    return jsonify(response)
