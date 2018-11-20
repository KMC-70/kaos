"""Implementation of Viewing cone algorithm"""
from math import asin, atan, sqrt, sin, cos, pi
import numpy as np
from numpy import cross
from numpy.linalg import norm

from ..constants import SECONDS_PER_DAY, ANGULAR_VELOCITY_EARTH, THETA_NAUGHT
from ..tuples import TimeInterval
from ..errors import ViewConeError


def cart2sp(x, y, z):
    """Converts data from cartesian coordinates into spherical.

    Args:
        x (scalar or array_like): X-component of data.
        y (scalar or array_like): Y-component of data.
        z (scalar or array_like): Z-component of data.

    Returns:
        Tuple (r, theta, phi) of data in spherical coordinates.
    """
    x = np.asarray(x)
    y = np.asarray(y)
    z = np.asarray(z)
    scalar_input = False
    if x.ndim == 0 and y.ndim == 0 and z.ndim == 0:
        x = x[None]
        y = y[None]
        z = z[None]
        scalar_input = True
    r = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    theta = np.arcsin(z / r)
    phi = np.arctan2(y, x)
    if scalar_input:
        return (r.squeeze(), theta.squeeze(), phi.squeeze())
    return (r, theta, phi)


def reduce_poi(site_eci, sat_pos, sat_vel, q_magnitude, poi):
    """Performs a series of viewing cone calculations and shrinks the input POI.

    Args:
        site_eci (Vector3D): site location in ECI at the start of POI
        sat_pos (Vector3D): position of satellite (at an arbitrary time)
        sat_vel (Vector3D): velocity of satellite (at the same arbitrary time as sat_pos)
        q_magnitude (int): maximum orbital radius
        poi (TimeInterval): period of interest

    Returns:
        A list of TimeIntervals that the orbit is inside viewing cone.

    Raises:
        ValueError: on unexpected input
        ViewConeError: on inconclusive result from Viewing cone
    """
    if poi.start > poi.end:
        raise ValueError("poi.start is after poi.end")

    # Tracking how much of the POI has been processed
    cur_end = poi.start
    # Estimate of maximum m
    expected_final_m = ((poi.end - poi.start) / SECONDS_PER_DAY) + 1

    # Find the intervals to cover the input POI
    interval_list = []
    m = 0
    while (cur_end < poi.end) and (m < expected_final_m):
        try:
            t_1, t_2, t_3, t_4 = _view_cone_calc(site_eci, sat_pos, sat_vel, q_magnitude, m)
            # Validate the intervals
            if (t_3 > t_1) or (t_2 > t_4):
                # Unexpected order of times
                raise ViewConeError("Viewing Cone internal error")
            # Add intervals to the list
            interval_list.append(TimeInterval(poi.start + t_3, poi.start + t_1))
            interval_list.append(TimeInterval(poi.start + t_2, poi.start + t_4))
            m += 1
            cur_end = poi.start + t_4
        except ValueError:
            # The case were the formulas have less than 4 roots
            raise ViewConeError("Unsupported viewing cone and orbit configuration.")

    # Adjusting the intervals to fit inside the input POI and return
    return _trim_poi_segments(interval_list, poi)


def _trim_poi_segments(interval_list, poi):
    """Semi-private: Adjusts list of intervals so that all intervals fit inside the poi

        Args:
            interval_list (list of TimeIntervals): the intervals to be trimmed
            poi (TimeInterval): period of interest, reference for trimming

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


def _view_cone_calc(site_eci, sat_pos, sat_vel, q_magnitude, m):
    """Semi-private: Performs the viewing cone visibility calculation for the day defined by m.

    This function is based on a paper titled "rapid satellite-to-site visibility determination
    based on self-adaptive interpolation technique"  with some variation to account for interaction
    of viewing cone with the satellite orbit.

    Args:
        site_eci (Vector3D): site location in ECI at the start of POI
        sat_pos (Vector3D): position of satellite (at the same time as sat_vel)
        sat_vel (Vector3D): velocity of satellite (at the same time as sat_pos)
        q_magnitude (int): maximum orbital radius

    Returns:
        Returns 4 numbers representing times at which the orbit is tangent to the viewing cone,

    Raises:
        ValueError: if any of the 4 formulas has a complex answer. This happens when the orbit and
            viewing cone do not intersect or only intersect twice.

    Note:
        With more analysis it should be possible to find a correct interval even in the case
        where there are only two intersections but this is beyond the current scope of the project.
    """

    # Get geocentric angles from site ECI
    r_site_magnitude, lat_geoc, lon_geoc = cart2sp(site_eci.x, site_eci.y, site_eci.z)

    # P vector (also referred  to as orbital angular momentum in the paper) calculations
    p_unit_x, p_unit_y, p_unit_z = cross(sat_pos, sat_vel) / (norm(sat_pos) * norm(sat_vel))

    # Formulas from paper:
    # Note: each Txxx represents an intersection between viewing cone and the orbit
    gamma = THETA_NAUGHT + asin((r_site_magnitude * sin((pi / 2)+THETA_NAUGHT)) / q_magnitude)
    tin = ((1 / ANGULAR_VELOCITY_EARTH) * (asin((cos(gamma) - (p_unit_z * sin(lat_geoc))) /
            (sqrt((p_unit_x ** 2) + (p_unit_y ** 2)) * cos(lat_geoc)))
            - lon_geoc - atan(p_unit_x / p_unit_y) + 2 * pi * m))
    tout = ((1 / ANGULAR_VELOCITY_EARTH) * (pi - asin((cos(gamma) - (p_unit_z * sin(lat_geoc)))/
            (sqrt((p_unit_x ** 2) + (p_unit_y ** 2)) * cos(lat_geoc)))
            - lon_geoc - atan(p_unit_x / p_unit_y) + 2 * pi * m))

    # Second set
    gamma2 = pi - gamma
    tin_2 = ((1 / ANGULAR_VELOCITY_EARTH) * (asin((cos(gamma2) - (p_unit_z * sin(lat_geoc))) /
            (sqrt((p_unit_x ** 2) + (p_unit_y ** 2)) * cos(lat_geoc)))
            - lon_geoc - atan(p_unit_x / p_unit_y) + 2 * pi * m))
    tout_2 = ((1 / ANGULAR_VELOCITY_EARTH) * (pi - asin((cos(gamma2) - (p_unit_z * sin(lat_geoc))) /
            (sqrt((p_unit_x**2)+(p_unit_y**2))*cos(lat_geoc)))
            - lon_geoc - atan(p_unit_x/p_unit_y) + 2*pi*m))

    return tin, tout, tin_2, tout_2
