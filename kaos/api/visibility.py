"""This file contains routing code for the APIs. It should not contain much.

Author: Team KMC-70.
"""

from flask import Blueprint, jsonify, request

from .schema import SEARCH_QUERY_VALIDATOR
from .validators import validate_request_schema
from .errors import InputError
from ..utils.date import utc_to_unix
from ..models import SatelliteInfo
from ..algorithm.interpolator import Interpolator
from ..algorithm.coord_conversion import lla_to_eci

# pylint: disable=invalid-name
visibility_bp = Blueprint('visibility', __name__, url_prefix='/visibility')
# pylint: enable=invalid-name


@visibility_bp.route('/search', methods=['POST'])
@validate_request_schema(SEARCH_QUERY_VALIDATOR)
def get_satellite_visibility():
    """Get the number of satellites that have visibility to a site.

    Requires:
        The user supplies a query param, 'coords.'

    Returns:
        A string to be displayed.
    """

    # Input data processing and conversion
    if SatelliteInfo.query.get(request.json['PlatformID']) is None:
        raise InputError('PlatformID', 'No such platform')

    try:
        start_time = utc_to_unix(request.json['POI']['startTime'])
        end_time = utc_to_unix(request.json['POI']['endTime'])
    except ValueError as error:
        raise InputError('POI', str(error))

    try:
        linear_interpolator = Interpolator(request.json['PlatformID'])
        pos, vel = linear_interpolator.interpolate(start_time)
    except ValueError as error:
        raise InputError('Platform',
                         'No satellite data at {}'.format(request.json['POI']['startTime']))

    target = lla_to_eci(request.json['Target'][0], request.json['Target'][1], 0, start_time)
    # TODO Pass to view_cone

    return start_time, end_time

