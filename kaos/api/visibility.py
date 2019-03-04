"""This file contains routing code for the APIs. It should not contain much.

Author: Team KMC-70.
"""

import json

from flask import Blueprint, request, jsonify

from .schema import SEARCH_QUERY_VALIDATOR
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
    if Satellite.query.get(request.json['PlatformID']) is None:
        raise InputError('PlatformID', 'No such platform')

    #satellite = Satellite.get_by_id(request.json['PlatformID'])

    try:
        start_time = utc_to_unix(request.json['POI']['startTime'])
        end_time = utc_to_unix(request.json['POI']['endTime'])
    except ValueError as error:
        raise InputError('POI', str(error))

    # Due to limitations of the accuracy of the view cone calculations the POI must be split into in
    # intervals of 3600 seconds
    #interpolator = Interpolator(request.json['PlatformID'])
    poi_list = [TimeInterval(poi_start, min(poi_start + 86400, end_time))
                for poi_start in xrange(start_time, end_time, 86400)]

    reduced_poi_list = poi_list
    # TODO: This part will be uncommented when viewcone is reliable.
    """
    for poi in poi_list:
        site_eci = lla_to_eci(request.json['Target'][0], request.json['Target'][1], 0, poi.start)
        try:
            sat_pos, sat_vel = interpolator.interpolate(start_time)
        except ValueError as error:
            raise InputError('Platform',
                             'No satellite data at {}'.format(request.json['POI']['startTime']))

        # Since the viewing cone only works with eci coordinates, the sat coordinates must be
        # converted
        sat_pos, sat_vel = ecef_to_eci(sat_pos, sat_vel, poi.start)

        try:
            reduced_poi_list.extend(reduce_poi(site_eci[0], sat_pos, sat_vel,
                                               satellite.maximum_altitude, poi))
        except ViewConeError:
            reduced_poi_list.append(poi)
    """

    # Now that the POI has been reduced manageable chunks, the visibility can be computed
    visibility_periods = []
    for poi in reduced_poi_list:
        visibility_finder = VisibilityFinder(request.json['PlatformID'],
                                             (request.json['Target'][0], request.json['Target'][1]),
                                             poi)
        visibility_periods.extend(visibility_finder.determine_visibility())

    # Prepare the response
    response_history = ResponseHistory(response="{}")
    response_history.save()
    DB.session.commit()

    response = {
        'id': response_history.uid,
        'Opportunities': []
    }
    for poi in visibility_periods:
        response['Opportunities'].append({'PlatformID': request.json['PlatformID'],
                                          'start_time': float(poi.start),
                                          'end_time': float(poi.end)})

    # Save the result for future use
    response_history.response = json.dumps(response)
    response_history.save()
    DB.session.commit()

    return jsonify(response)
