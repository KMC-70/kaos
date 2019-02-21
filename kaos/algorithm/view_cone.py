"""Implementation of Viewing cone algorithm"""

from __future__ import division
import mpmath as mp
from numpy import cross

from .coord_conversion import geod_to_geoc_lat
from ..constants import SECONDS_PER_DAY, ANGULAR_VELOCITY_EARTH, THETA_NAUGHT, EARTH_RADIUS
from ..tuples import TimeInterval
from ..errors import ViewConeError


def reduce_poi(site_lat_lon, sat_pos, sat_vel, q_magnitude, poi):
    """Performs a series of viewing cone calculations and shrinks the input POI
    Args:
      site_eci(Vector3D) = site location in ECI at the start of POI
      sat_pos(Vector3D) = position of satellite (at an arbitrary time)
      sat_vel(Vector3D) = velocity of satellite (at the same arbitrary time as sat_pos)
      q_magnitude(int) = maximum orbital radius
      poi(TimeInterval) = period of interest
    Returns:
      list of TimeIntervals that the orbit is inside viewing cone
    Raises:
      ValueError: on unexpected input
      ViewConeError: on inconclusive result from Viewing cone
    """

    site_geoc_lat = geod_to_geoc_lat(site_lat_lon[0])

    GMT_sidereal_angle = (poi.start - mp.mpf(946728000))*(360/SECONDS_PER_DAY) + mp.mpf('280.46062')
    site_lon = GMT_sidereal_angle + site_lat_lon[1]
    site_lon = mp.floor(site_lon)%360 + (site_lon - mp.floor(site_lon))

    if site_lon > 180:
        site_lon -= 360

    if poi.start > poi.end:
        raise ValueError("poi.start is after poi.end")

    # Maximum m
    expected_final_m = mp.ceil((poi.end - poi.start)/(24*60*60))
    # Find the intervals to cover the input POI
    interval_list = []
    m = 0
    while m < expected_final_m:
        try:
            t_1, t_2, t_3, t_4 = _view_cone_calc(site_geoc_lat, site_lon, sat_pos, sat_vel, q_magnitude, m)
            # Validate the intervals
            if (t_3 < t_1):
                interval_list.append(TimeInterval(poi.start+t_3, poi.start+t_1))
            else:
                interval_list.append(TimeInterval(poi.start+t_3, poi.start+(m+1)*24*60*60))
                interval_list.append(TimeInterval(poi.start+m*24*60*60, poi.start+t_1))

            if (t_2 < t_4):
                interval_list.append(TimeInterval(poi.start+t_2, poi.start+t_4))
            else:
                interval_list.append(TimeInterval(poi.start+t_2, poi.start+(m+1)*24*60*60))
                interval_list.append(TimeInterval(poi.start+m*24*60*60, poi.start+t_4))
            m += 1

        except ValueError:
            # The case were the formulas have less than 4 roots
            raise ViewConeError("Unsupported viewing cone and orbit configuration.")

    # Adjusting the intervals to fit inside the input POI and return
    return _trim_poi_segments(interval_list, poi)

def _trim_poi_segments(interval_list, poi):
    """Semi-private: Adjusts list of intervals so that all intervals fit inside the poi
        Args:
          interval_list(list of TimeIntervals) = the interval to be trimmed
          poi(TimeInterval) = period of interest, reference for trimming
        Returns:
          List of TimeIntervals that fit inside the poi
    """
    ret_list = []
    for interval in interval_list:
        if (interval.start > poi.end) or (interval.end < poi.start):
            # Outside the input POI
            continue
        elif (interval.start < poi.end) and (interval.end > poi.end):
            ret_list.append(TimeInterval(interval.start, poi.end))
        elif (interval.end > poi.start) and (interval.start < poi.start):
            ret_list.append(TimeInterval(poi.start, interval.end))
        else:
            ret_list.append(TimeInterval(interval.start, interval.end))

    return ret_list


def _view_cone_calc(lat_geoc, lon_geoc, sat_pos, sat_vel, q_magnitude, m):
    """Semi-private: Performs the viewing cone visibility calculation for the day defined by m.
    Note: This function is based on a paper titled "rapid satellite-to-site visibility determination
    based on self-adaptive interpolation technique"  with some variation to account for interaction
    of viewing cone with the satellite orbit.
    Args:
      lat_geoc(mpf) = site location in degrees at the start of POI
      lon_geoc(mpf) = site location in degrees at the start of POI
      sat_pos(Vector3D) = position of satellite (at the same time as sat_vel)
      sat_vel(Vector3D) = velocity of satellite (at the same time as sat_pos)
      q_magnitude(int) = maximum orbital radius
    Returns:
      Returns 4 numbers representing times at which the orbit is tangent to the viewing cone,
    Raises:
      ValueError: if any of the 4 formulas has a complex answer. This happens when the orbit and
      viewing cone do not intersect or only intersect twice.
      Note: With more analysis it should be possible to find a correct interval even in the case
      where there are only two intersections but this is beyond the current scope of the project.
    """

    lat_geoc = (lat_geoc*mp.pi)/180
    lon_geoc = (lon_geoc*mp.pi)/180

    # P vector (also referred  to as orbital angular momentum in the paper) calculations
    p_unit_x, p_unit_y, p_unit_z = cross(sat_pos, sat_vel) / (mp.norm(sat_pos) * mp.norm(sat_vel))

    # Formulas from paper:
    gamma = THETA_NAUGHT + mp.asin((EARTH_RADIUS * mp.sin((mp.pi / 2) + THETA_NAUGHT)) / q_magnitude)
    gamma2 = mp.pi - gamma

    arctan_term = mp.atan2(p_unit_x , p_unit_y)
    arcsin_term = lambda g:(mp.asin((mp.cos(g) - p_unit_z * mp.sin(lat_geoc)) /
                            (mp.sqrt((p_unit_x ** 2) + (p_unit_y ** 2)) * mp.cos(lat_geoc))))

    arcsin_term_gamma = arcsin_term(gamma)
    arcsin_term_gamma2 = arcsin_term(gamma2)

    angle_1 = (arcsin_term_gamma - lon_geoc - arctan_term + 2 * mp.pi * m)
    angle_2 = (mp.pi - arcsin_term_gamma - lon_geoc - arctan_term + 2 * mp.pi * m)
    angle_3 = (arcsin_term_gamma2 - lon_geoc - arctan_term + 2 * mp.pi * m)
    angle_4 = (mp.pi - arcsin_term_gamma2 - lon_geoc - arctan_term + 2 * mp.pi * m)

    # Map all angles to 0 to 2*pi
    while angle_1 < 0:
        angle_1 += 2*mp.pi
    while angle_1 > 2*mp.pi:
        angle_1 -= 2*mp.pi

    while angle_2 < 0:
        angle_2 += 2*mp.pi
    while angle_2 > 2*mp.pi:
        angle_2 -= 2*mp.pi

    while angle_3 < 0:
        angle_3 += 2*mp.pi
    while angle_3 > 2*mp.pi:
        angle_3 -= 2*mp.pi

    while angle_4 < 0:
        angle_4 += 2*mp.pi
    while angle_4 > 2*mp.pi:
        angle_4 -= 2*mp.pi

    time_1 = (1 / ANGULAR_VELOCITY_EARTH) * angle_1
    time_2 = (1 / ANGULAR_VELOCITY_EARTH) * angle_2
    time_3 = (1 / ANGULAR_VELOCITY_EARTH) * angle_3
    time_4 = (1 / ANGULAR_VELOCITY_EARTH) * angle_4

    # Check for complex answers
    if [x for x in [time_1, time_2, time_3, time_4] if not isinstance(x, mp.mpf)]:
        raise ValueError()

    return time_1, time_2, time_3, time_4
