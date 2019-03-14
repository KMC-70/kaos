"""Implementation of Viewing cone algorithm"""

from __future__ import division

import mpmath as mp
from numpy import cross, asarray

from .coord_conversion import geod_to_geoc_lat, geod_to_eci_geoc_lon
from ..utils import time_intervals
from ..constants import ANGULAR_VELOCITY_EARTH, EARTH_A_AXIS, EARTH_B_AXIS, THETA_NAUGHT
from ..tuples import TimeInterval
from ..errors import ViewConeError


def reduce_poi(site_lat_lon, sat_position_velocity_pairs, q_max, poi):
    """Performs a series of viewing cone calculations and shrinks the input POI

    Args:
        site_lat_lon (tuple): site's Geodetic Latitude and longitude (lat, lon)
        sat_position_velocity_pairs (list of (position Vector3D, velocity Vector3D): list
        of satellite position and velocity pairs at an arbitrary time. (see note for optimal
        selection of pos/vel samples.)
        q_max (float): maximum orbital radius
        poi (TimeInterval): period of interest (see note below)

    Returns:
        list of TimeIntervals that the orbit is inside viewing cone

    Raises:
        ValueError: on unexpected input
        ViewConeError: on inconclusive result from Viewing cone

    Note: In the referenced paper, the changes in orbit plane are completely ignored for viewing
        cone calculations. In practice, this simplification adds significant error over large POIs.
        This error can be completely eliminated by limiting the POI duration to one day and
        providing two samples of position/velocity (beginning and end of input time).
    """
    if poi.start > poi.end:
        raise ValueError("poi.start is after poi.end")

    # Get geocentric lat/lon (in the ECI frame) at the beginning of poi
    site_geoc_lat = geod_to_geoc_lat(site_lat_lon[0])
    site_lon = geod_to_eci_geoc_lon(site_lat_lon[1], poi.start)

    # Maximum m
    expected_final_m = mp.ceil((poi.end - poi.start) / (24 * 60 * 60))

    # Find the intervals to cover the input POI
    interval_list = []
    m = 0
    while m < expected_final_m:
        try:
            roots = []
            for sat_pos, sat_vel in sat_position_velocity_pairs:
                roots.append(_view_cone_calc(site_geoc_lat, site_lon, sat_pos, sat_vel, q_max, m))

            # Finding roots that result in the largest interval
            roots = asarray(roots)
            t_1, t_2 = max(roots[:, 0]), min(roots[:, 1])
            t_3, t_4 = min(roots[:, 2]), max(roots[:, 3])

            # Construct intervals based on calculated roots
            if t_3 < t_1:
                interval_list.append(TimeInterval(poi.start + t_3, poi.start + t_1))
            else:
                interval_list.append(TimeInterval(poi.start + m * 24 * 60 * 60, poi.start + t_1))
                interval_list.append(TimeInterval(poi.start + t_3, poi.start +
                                                  (m + 1) * 24 * 60 * 60))

            if t_2 < t_4:
                interval_list.append(TimeInterval(poi.start + t_2, poi.start + t_4))
            else:
                interval_list.append(TimeInterval(poi.start + m * 24 * 60 * 60, poi.start + t_4))
                interval_list.append(TimeInterval(poi.start + t_2, poi.start +
                                                  (m + 1) * 24 * 60 * 60))

            if t_2 > t_4 and t_3 > t_1:
                # It's unexpected that two roots wrap around (i.e. both if conditions to be false)
                raise ViewConeError("Internal Viewing cone error")
            m += 1

        except ValueError:
            # The case were the formulas have less than 4 roots
            raise ViewConeError("Unsupported viewing cone and orbit configuration.")

    # Adjusting the intervals to fit inside the input POI and return
    return time_intervals.trim_poi_segments(interval_list, poi)


def earth_radius_at_geocetric_lat(geoc_lat):
    """Calculates Earth's radius at a particular geocentric latitude

    Args:
        goc_lat (float): geocentric latitude (Rad)

    Returns:
        Earth's radius at the given geocentric latitude (in meters)
    """
    return EARTH_A_AXIS * EARTH_B_AXIS / mp.sqrt(EARTH_A_AXIS ** 2 * mp.sin(geoc_lat) ** 2 +
                                                 EARTH_B_AXIS ** 2 * mp.cos(geoc_lat) ** 2)


def _view_cone_calc(lat_geoc, lon_geoc, sat_pos, sat_vel, q_max, m):
    """Semi-private: Performs the viewing cone visibility calculation for the day defined by m.
    Note: This function is based on a paper titled "rapid satellite-to-site visibility determination
    based on self-adaptive interpolation technique"  with some variation to account for interaction
    of viewing cone with the satellite orbit.

    Args:
        lat_geoc (float): site location in degrees at the start of POI
        lon_geoc (float): site location in degrees at the start of POI
        sat_pos (Vector3D): position of satellite (at the same time as sat_vel)
        sat_vel (Vector3D): velocity of satellite (at the same time as sat_pos)
        q_max (float): maximum orbital radius
        m (int): interval offsets (number of days after initial condition)

    Returns:
        Returns 4 numbers representing times at which the orbit is tangent to the viewing cone,

    Raises:
        ValueError: if any of the 4 formulas has a complex answer. This happens when the orbit and
        viewing cone do not intersect or only intersect twice.

    Note: With more analysis it should be possible to find a correct interval even in the case
        where there are only two intersections but this is beyond the current scope of the project.
    """
    lat_geoc = (lat_geoc * mp.pi) / 180
    lon_geoc = (lon_geoc * mp.pi) / 180

    # P vector (also referred  to as orbital angular momentum in the paper) calculations
    p_unit_x, p_unit_y, p_unit_z = cross(sat_pos, sat_vel) / (mp.norm(sat_pos) * mp.norm(sat_vel))

    # Following are equations from Viewing cone section of referenced paper
    r_site_magnitude = earth_radius_at_geocetric_lat(lat_geoc)
    gamma1 = THETA_NAUGHT + mp.asin((r_site_magnitude * mp.sin((mp.pi / 2) + THETA_NAUGHT)) / q_max)
    gamma2 = mp.pi - gamma1

    # Note: atan2 instead of atan to get the correct quadrant.
    arctan_term = mp.atan2(p_unit_x, p_unit_y)
    arcsin_term_gamma, arcsin_term_gamma2 = [(mp.asin((mp.cos(gamma) - p_unit_z * mp.sin(lat_geoc))
                                             / (mp.sqrt((p_unit_x ** 2) + (p_unit_y ** 2)) *
                                              mp.cos(lat_geoc)))) for gamma in [gamma1, gamma2]]

    angle_1 = (arcsin_term_gamma - lon_geoc - arctan_term + 2 * mp.pi * m)
    angle_2 = (mp.pi - arcsin_term_gamma - lon_geoc - arctan_term + 2 * mp.pi * m)
    angle_3 = (arcsin_term_gamma2 - lon_geoc - arctan_term + 2 * mp.pi * m)
    angle_4 = (mp.pi - arcsin_term_gamma2 - lon_geoc - arctan_term + 2 * mp.pi * m)
    angles = [angle_1, angle_2, angle_3, angle_4]

    # Check for complex answers
    if any([not isinstance(angle, mp.mpf) for angle in angles]):
        raise ValueError()

    # Map all angles to 0 to 2*pi
    for idx in range(len(angles)):
        while angles[idx] < 0:
            angles[idx] += 2 * mp.pi
        while angles[idx] > 2 * mp.pi:
            angles[idx] -= 2 * mp.pi

    # Calculate the corresponding time for each angle and return
    return [mp.nint((1 / ANGULAR_VELOCITY_EARTH) * angle) for angle in angles]
