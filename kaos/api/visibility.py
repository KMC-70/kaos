"""This file contains routing code for the APIs. It should not contain much.

Author: Team KMC-70.
"""

import json

from flask import Blueprint, request, jsonify
import numpy as np

from .schema import SEARCH_QUERY_VALIDATOR
from .validators import validate_request_schema
from .errors import InputError
from ..errors import ViewConeError
from ..utils.time_conversion import utc_to_unix
from ..utils.time_intervals import fuse_neighbor_intervals
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
        A user request that contains a JSON payload which follows the SEARCH_SCHEMA.
    """
    # Input data processing and conversion
    try:
        start_time = utc_to_unix(request.json['POI']['startTime'])
        end_time = utc_to_unix(request.json['POI']['endTime'])
    except ValueError as error:
        raise InputError('POI', str(error))

    visibility_periods = []
    for satellite_id in request.json['PlatformID']:
        if Satellite.query.get(satellite_id) is None:
            raise InputError('PlatformID', 'No such platform')

        # Due to limitations of the accuracy of the view cone calculations the POI must be split
        # into intervals of one day
        poi_list = [TimeInterval(poi_start, min(poi_start + 86400, end_time))
                    for poi_start in xrange(start_time, end_time, 86400)]

        satellite = Satellite.get_by_id(request.json['PlatformID'])
        interpolator = Interpolator(request.json['PlatformID'])

        # Gather data for every 24 hour period of the input interval
        sampling_time_list = [time.start for time in poi_list]
        sampling_time_list.append(end_time)

        sat_ecef_positions, sat_ecef_velocities = map(list, zip(*[interpolator.interpolate(t) for t
                                                                  in sampling_time_list]))

        # Since the viewing cone only works with ECI coordinates, the sat coordinates must be
        # converted
        sat_position_velocity_pairs = ecef_to_eci(np.transpose(np.asarray(sat_ecef_positions)),
                                                 np.transpose(np.asarray(sat_ecef_velocities)),
                                                 sampling_time_list)

        # Run viewing cone
        try:
            reduced_poi_list = [reduced_poi for idx, poi in enumerate(poi_list) for reduced_poi in
                                reduce_poi((request.json['Target'][0],request.json['Target'][1]),
                                           sat_position_velocity_pairs[idx:idx+2],
                                           satellite.maximum_altitude, poi)]

            reduced_poi_list = fuse_neighbor_intervals(reduced_poi_list)

        except ViewConeError:
            reduced_poi_list = [TimeInterval(start_time, end_time)]

        # Now that the POI has been reduced manageable chunks, the visibility can be computed
        for poi in reduced_poi_list:
            visibility_finder = VisibilityFinder(satellite_id,
                                                 (request.json['Target'][0],
                                                  request.json['Target'][1]),
                                                 poi)
            visibility_periods.append((satellite_id, visibility_finder.determine_visibility()))

    # Prepare the response
    response_history = ResponseHistory(response="{}")
    response_history.save()
    DB.session.commit()

    response = {
        'id': response_history.uid,
        'Opportunities': []
    }
    for satellite_id, pois in visibility_periods:
        response['Opportunities'].extend([{'PlatformID': satellite_id,
                                           'start_time': float(poi.start),
                                           'end_time': float(poi.end)} for poi in pois])

    # Save the result for future use
    response_history.response = json.dumps(response)
    response_history.save()
    DB.session.commit()

    return jsonify(response)
