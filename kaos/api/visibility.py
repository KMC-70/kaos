"""This file contains routing code for the APIs. It should not contain much.

Author: Team KMC-70.
"""

from flask import Blueprint, request

from .schema import SEARCH_QUERY_VALIDATOR
from .validators import validate_request_schema
from .errors import InputError
from ..errors import ViewConeError
from ..utils.time_conversion import utc_to_unix
from ..models import Satellite
from ..algorithm.interpolator import Interpolator
from ..algorithm.coord_conversion import lla_to_eci
from ..algorithm.view_cone import reduce_poi
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

    satellite = Satellite.get_by_id(request.json['PlatformID'])

    try:
        start_time = utc_to_unix(request.json['POI']['startTime'])
        end_time = utc_to_unix(request.json['POI']['endTime'])
    except ValueError as error:
        raise InputError('POI', str(error))

    # Due to limitations of the accuracy of the view cone calculations the POI must be split into in
    # intervals of 3600 seconds
    interpolator = Interpolator(request.json['PlatformID'])
    poi_list = (TimeInterval(poi_start, min(poi_start + 3600), end_time)
                for poi_start in xrange(start_time, end_time, 3600))

    for poi in poi_list:
        site_eci = lla_to_eci(request.json['Target'][0], request.json['Target'][1], 0, poi.start)
        try:
            sat_pos, sat_vel = interpolator.interpolate(start_time)
        except ValueError as error:
            raise InputError('Platform',
                             'No satellite data at {}'.format(request.json['POI']['startTime']))

    try:
        poi_list = reduce_poi(site_eci, sat_pos, sat_vel, satellite.maximum_altitude, poi)
    except ViewConeError:
        poi_list = [poi]
    except:
        # TODO Throw a 505
        pass

    for poi in poi_list:
        pass

    # Now that the POI has been reduced manageable chunks, the visibility can be computer

    return start_time, end_time

