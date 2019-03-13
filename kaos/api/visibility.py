"""This file contains routing code for the APIs. It should not contain much.

Author: Team KMC-70.
"""

import json

from flask import Blueprint, request, jsonify

from .schema import SEARCH_QUERY_VALIDATOR, OPERTUNITY_QUERY_VALIDATOR
from .validators import validate_request_schema
from .errors import InputError
from ..errors import ViewConeError
from ..utils.time_conversion import utc_to_unix
from ..utils.time_intervals import calculate_common_intervals
from ..models import DB, Satellite, ResponseHistory
from ..algorithm.interpolator import Interpolator
from ..algorithm.coord_conversion import lla_to_eci, lla_to_ecef, ecef_to_eci
from ..algorithm.view_cone import reduce_poi
from ..algorithm.visibility_finder import VisibilityFinder
from ..tuples import TimeInterval

# pylint: disable=invalid-name
visibility_bp = Blueprint('visibility', __name__, url_prefix='/visibility')
opertunity_bp = Blueprint('opertunity', __name__, url_prefix='/opertunity')
# pylint: enable=invalid-name


def request_parse_poi(validated_request):
    """Parses the POI from a provided visibility api request.

    Args:
        validated_request (obj):  A Flask request object that has been generated for a
                                  visibility/opertunity endpoint.

    Requieres:
        The request object MUST have been validated against the requested schema and must have a
        'POI' key in its JSON payload.

    Throws:
        ValueError: If the POI is invalid. i.e. The start time is greater than the end time.

    Returns:
        A tuple of (start_time, end_time) where each of the two times are represented in UNIX time.
    """
    try:
        start_time = utc_to_unix(validated_request.json['POI']['startTime'])
        end_time = utc_to_unix(validated_request.json['POI']['endTime'])

        if start_time > end_time:
            raise ValueError("Start time is greater than the end time!")

    except ValueError as error:
        raise InputError('POI', str(error))

    return start_time, end_time


def request_parse_platform_id(validated_request):
    """Parses the PlatformID from a provided visibility api request.

    Args:
        validated_request (obj):  A Flask request object that has been generated for a
                                  visibility/opertunity endpoint.

    Requieres:
        The request object MUST have been validated against the requested schema.

    Throws:
        InputError: If any provided platform ID(s) are invalid.

    Returns:
        A list of Satellite model objects.
    """

    if 'PlatformID' not in validated_request.json:
        return Satellite.query.all()

    satellites = []
    for satellite in validated_request.json['PlatformID']:
        satellite = Satellite.query.get(satellite)
        if satellite is None:
            raise InputError('PlatformID', 'No such platform')

        satellites.append(satellite)

    return satellites


def get_point_visibility_helper(satellite, site, poi):
    start_time, end_time = poi
    # Due to limitations of the accuracy of the view cone calculations the POI must be split into in
    # intervals of 3600 seconds
    poi_list = [TimeInterval(poi_start, min(poi_start + 86400, end_time))
                for poi_start in xrange(start_time, end_time, 86400)]

    reduced_poi_list = poi_list
    # TODO Uncomment when the viecone fix is merged
    """
    interpolator = Interpolator(satellite.platform_id)
    for poi in poi_list:
        site_pos_eci, site_pos_eci = lla_to_eci(site[0], site[1], 0, poi.start)
        try:
            sat_pos_ecef, sat_vel_ecef = interpolator.interpolate(poi.start)
        except ValueError:
            raise InputError('Platform',
                             'No satellite data at {}'.format(poi))

        # Since the viewing cone only works with eci coordinates, the sat coordinates must be
        # converted
        sat_pos_eci, sat_vel_eci = ecef_to_eci(sat_pos_ecef, sat_vel_ecef, poi.start)

        try:
            reduced_poi_list.extend(reduce_poi(site_pos_eci, sat_pos_eci, sat_vel_eci,
                                               satellite.maximum_altitude, poi))
        except ViewConeError:
            reduced_poi_list.append(poi)
        """
    # Now that the POI has been reduced manageable chunks, the visibility can be computed
    visibility_periods = []
    for reduced_poi in reduced_poi_list:
        visibility_finder = VisibilityFinder(satellite.platform_id, site, reduced_poi)
        visibility_periods.extend(visibility_finder.determine_visibility())

    return visibility_periods


@opertunity_bp.route('/search', methods=['POST'])
@validate_request_schema(OPERTUNITY_QUERY_VALIDATOR)
def get_area_visibility():
    """Stuff"""

    satellites = request_parse_platform_id(request)
    poi = request_parse_poi(request)

    satellite_area_visibility = {}
    for satellite in satellites:
        target_visibility = {}
        for target in request.json['TargetArea']:
            target_visibility[target[0]] = get_point_visibility_helper(satellite, target, poi)

        satellite_area_visibility[satellite] = \
            calculate_common_intervals(target_visibility.values())


    __import__('pdb').set_trace()
    # Prepare the response
    response_history = ResponseHistory(response="{}")
    response_history.save()
    DB.session.commit()

    response = {
        'id': response_history.uid,
        'Opportunities': [{'PlatformID': satellite.platform_id,
                           'start_time': float(access.start),
                           'end_time': float(access.end)}
                          for satellite, accesses in satellite_area_visibility.items()
                          for access in accesses]
    }

    # Save the result for future use
    response_history.response = json.dumps(response)
    response_history.save()
    DB.session.commit()

    return jsonify(response)


@visibility_bp.route('/search', methods=['POST'])
@validate_request_schema(SEARCH_QUERY_VALIDATOR)
def get_satellite_visibility():
    """Get the number of satellites that have visibility to a site.

    Requires:
        A user request that contains a JSON payload which follows the SEARCH_SCHEMA.
    """
    # Input data processing and conversion
    poi = request_parse_poi(request)
    satellites = request_parse_platform_id(request)
    target = request.json['Target']

    visibility_periods = {}
    for satellite in satellites:
        visibility_periods[satellite.platform_id] = get_point_visibility_helper(satellite,
                                                                                target,
                                                                                poi)

    # Prepare the response
    response_history = ResponseHistory(response="{}")
    response_history.save()
    DB.session.commit()

    response = {
        'id': response_history.uid,
        'Opportunities': [{'PlatformID': satellite,
                           'start_time': float(access.start),
                           'end_time': float(access.end)}
                          for satellite, accesses in visibility_periods.items()
                          for access in accesses]
    }

    # Save the result for future use
    response_history.response = json.dumps(response)
    response_history.save()
    DB.session.commit()

    return jsonify(response)
