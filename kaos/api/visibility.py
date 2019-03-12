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

def request_parse_poi(request):
    try:
        start_time = utc_to_unix(request.json['POI']['startTime'])
        end_time = utc_to_unix(request.json['POI']['endTime'])

        if start_time > end_time:
            raise ValueError("Start time is greater than the end time!")

    except ValueError as error:
        raise InputError('POI', str(error))

    return start_time, end_time


def request_parse_platform_id(request):
    if 'PlatformID' not in request.json:
        return Satellite.query.all()

    sattalites = []
    for satellite in request.json['PlatformID']:
        satellite = Satellite.query.get(satellite)
        if satellite is None:
            raise InputError('PlatformID', 'No such platform')

        sattalites.append(satellite)

    return sattalites


def common_intervals_helper(intervals1, intervals2):
    common_intervals = []
    for interval1 in intervals1:
        for interval2 in intervals2:
            intersection = interval1.intersection(interval2)
            if intersection:
                common_intervals.append(intersection)
    return common_intervals


def calculate_common_intervals(intervals_list):
    pass

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
            target_visibility[target] = get_point_visibility_helper(satellite, target, poi)

        common_target 
        satellite_area_visibility[satellite] = target_visibility


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
