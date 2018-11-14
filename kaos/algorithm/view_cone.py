from math import asin,atan,sqrt,sin,cos,pi

from ai.cs import cart2sp
from numpy import cross
from numpy.linalg import norm

from kaos.algorithm import SECONDS_PER_DAY,ANG_VEL_EARTH,THETA_NAUGHT


def view_cone(site_eci,sat_pos,sat_vel,q_magnitude,poi_start,poi_end):
    """Preforms a series of viewing cone calculations and shrinks the input POI

    Args:
      site_eci(Vector3D) = site location in ECI at the start of POI
      sat_pos(Vector3D) = position of satellite (at the same time as sat_vel)
      sat_vel(Vector3D) = velocity of satellite (at the same time as sat_pos)
      q_magnitude(int) = maximum orbital radius
      poi((int,int)) = Period of interest (start of POI, end of POI)

    Returns:
      None on error.
      list of POI tuples on success
    """
    # Return list
    poi_list = []
    # Tracking how much of the POI has been processed
    cur_end = poi_start
    # Estimate of maximum m
    expected_final_m = ((poi_end - poi_start)/SECONDS_PER_DAY) + 1

    # Find the intervals to cover the input POI
    m = 0
    while ((cur_end < poi_end) & (m < expected_final_m)):
        try:
            a,b,c,d = _view_cone_calc(site_eci,sat_pos,sat_vel,q_magnitude,m)
            if ((a < c) | (d < b)):
                # TODO: change to log
                print("Error (view_cone): Unexpected result from _view_cone_calc()")
                return None
            poi_list.append((poi_start+c, poi_start+a))
            poi_list.append((poi_start+b, poi_start+d))
            m += 1
            cur_end = poi_start + d
        except ValueError:
            # TODO: change to log
            print("Warning (view_cone): viewing cone method failed!")
            return None

    # Adjusting the intervals to fit inside the input POI
    ret_list = []
    for poi in poi_list:
        if ((poi[0] > poi_end) | (poi[1] < poi_start)):
            #outside the input POI
            continue
        elif ((poi[0] < poi_end) & (poi[1] > poi_end)):
            ret_list.append((poi[0],poi_end))
        elif ((poi[1] > poi_start) & (poi[0] < poi_start)):
            ret_list.append((poi_start,poi[1]))
        else:
            ret_list.append((poi[0],poi[1]))

    return ret_list

def _view_cone_calc(site_eci,sat_pos,sat_vel,q_magnitude,m):
    """Semi-private: Preforms the viewing cone visibility calculation for the day defined by m.

    Note: This function is based on a paper titled "rapid satellite-to-site visibility determination
    based on self-adaptive interpolation technique"  with some variation to account for interaction
    of viewing cone with the satellite orbit.

    Args:
      site_eci(Vector3D) = site location in ECI at the start of POI
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

    # Get geocentric angles from site ECI
    r_site_magnitude, lat_geoc, lon_geoc = cart2sp(site_eci.x,site_eci.y,site_eci.z)

    # P vector (also referred  to as orbital angular momentum in the paper) calculations
    p_unit_x, p_unit_y, p_unit_z = cross(sat_pos,sat_vel) / (norm(sat_pos) * norm(sat_vel))

    # Formulas from paper:
    # Note: each Txxx represents an intersection between viewing cone and the orbit
    gamma = THETA_NAUGHT + asin((r_site_magnitude * sin((pi/2)+THETA_NAUGHT))/q_magnitude)
    Tin = (1/ANG_VEL_EARTH) * (asin( (cos(gamma)-(p_unit_z*sin(lat_geoc))) / \
            (sqrt((p_unit_x**2)+(p_unit_y**2))*cos(lat_geoc))) \
            - lon_geoc - atan(p_unit_x/p_unit_y) + 2*pi*m)
    Tout = (1/ANG_VEL_EARTH) * (pi - asin((cos(gamma)-(p_unit_z*sin(lat_geoc)))/ \
            (sqrt((p_unit_x**2)+(p_unit_y**2))*cos(lat_geoc))) \
            - lon_geoc - atan(p_unit_x/p_unit_y) + 2*pi*m)

    # second set
    gamma2 = pi - gamma
    Tin_2 = (1/ANG_VEL_EARTH) * (asin( (cos(gamma2)-(p_unit_z*sin(lat_geoc))) / \
            (sqrt((p_unit_x**2)+(p_unit_y**2))*cos(lat_geoc))) \
            - lon_geoc - atan(p_unit_x/p_unit_y) + 2*pi*m)
    Tout_2 = (1/ANG_VEL_EARTH) * (pi - asin((cos(gamma2)-(p_unit_z*sin(lat_geoc))) / \
            (sqrt((p_unit_x**2)+(p_unit_y**2))*cos(lat_geoc))) \
            - lon_geoc - atan(p_unit_x/p_unit_y) + 2*pi*m)

    return Tin, Tout, Tin_2, Tout_2
