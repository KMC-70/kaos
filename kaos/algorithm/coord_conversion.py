"""This file contains functions to convert between LLA, ECI, ECEF coordinate systems."""

from math import sqrt, sin, cos, atan, tan

from numpy import rad2deg, deg2rad
from astropy import coordinates
from astropy.time import Time
from astropy import units

from ..constants import ELLIPSOID_A, ELLIPSOID_E
from ..tuples import Vector3D


def lla_to_ecef(lat_deg, lon_deg, alt=0):
    """Converts latitude, longitude, and altitude to earth-centered, earth-fixed (ECEF) Cartesian.

    Args:
        lat (int): geodetic latitude (decimal degrees)
        lon (int): longitude (decimal degrees)
        alt (int): height above WGS84 ellipsoid (m)

    Returns:
        A Vector3D(x,y,z) such that:
            x = ECEF X-coordinate (m)
            y = ECEF Y-coordinate (m)
            z = ECEF Z-coordinate (m)

    Note:
        This function assumes the WGS84 model. Latitude is customary geodetic (not geocentric).
        Adapted from a Matlab script by Michael Kleder
        https://www.mathworks.com/matlabcentral/fileexchange/7942-covert-lat-lon-alt-to-ecef-cartesian

        Based on: Department of Defense World Geodetic System 1984
            Page 4-4
            National Imagery and Mapping Agency
            Last updated June, 2004
            NIMA TR8350.2
    """
    # pylint: disable=invalid-name
    # decimal degrees to radians
    lat_rad = deg2rad(lat_deg)
    lon_rad = deg2rad(lon_deg)
    # intermediate calculation
    # (prime vertical radius of curvature)
    N = ELLIPSOID_A / sqrt(1 - pow(ELLIPSOID_E, 2) * pow(sin(lat_rad), 2))
    # results:
    x = (N + alt) * cos(lat_rad) * cos(lon_rad)
    y = (N + alt) * cos(lat_rad) * sin(lon_rad)
    z = ((1 - pow(ELLIPSOID_E, 2)) * N + alt) * sin(lat_rad)

    return Vector3D(x, y, z)


def geod_to_geoc_lat(geod_lat_deg):
    """Converts geodetic latitude to geocentric latitude.

    Args:
        geod_lat_deg (int): geodetic latitude (decimal degrees)

    Returns:
        geocentric latitude (decimal degrees)

    Note:
        This is based on:
        https://www.mathworks.com/help/aeroblks/geodetictogeocentriclatitude.html
        http://www.jqjacobs.net/astro/geodesy.html
        http://ccar.colorado.edu/asen5070/handouts/geodeticgeocentric.doc
    """
    flattening = 0.00335281068118
    geod_lat_rad = deg2rad(geod_lat_deg)
    geoc_lat_rad = atan(((1 - flattening) ** 2) * tan(geod_lat_rad))
    return rad2deg(geoc_lat_rad)


def lla_to_eci(lat, lon, alt, time_posix):
    """Converts geodetic lat,lon,alt, to a Cartesian vector in GCRS frame at the given time.

    Args:
        lat (int): geodetic latitude (decimal degrees)
        lon (int): longitude (decimal degrees)
        alt (int): height above WGS84 ellipsoid (m)
        time_posix (int): reference frame time

    Returns:
    A tuple of Vector3D(x,y,z):
        Position Vector:
            x = GCRS X-coordinate (m)
            y = GCRS Y-coordinate (m)
            z = GCRS Z-coordinate (m)
        Velocity Vector
            x = GCRS X-velocity (m/s)
            y = GCRS Y-velocity (m/s)
            z = GCRS Z-velocity (m/s)

    Note:
        Unlike the rest of the software that uses J2000 FK5, the ECI frame used here is
        GCRS; This can potentially introduce around 200m error for locations on surface of Earth.
    """
    posix_time_internal = Time(time_posix, format='unix')
    loc_lla = coordinates.EarthLocation.from_geodetic(lon, lat, alt)
    loc_eci = loc_lla.get_gcrs_posvel(posix_time_internal)

    eci_pos = Vector3D(loc_eci[0].x.value, loc_eci[0].y.value, loc_eci[0].z.value)
    eci_vel = Vector3D(loc_eci[1].x.value, loc_eci[1].y.value, loc_eci[1].z.value)

    return (eci_pos, eci_vel)


def ecef_to_eci(ecef_coords, ecef_vel, posix_time):
    """Converts a Cartesian vector in the ECEF to a GCRS frame at the given time.

    Args:
        ecef_coords (tuple): A tuple of the cartesian coordinates of the object in the ECCF frame
                             (m)
        ecef_vel (tuple): A tuple of the velocity of the object in the ECEF frame (m/s)
        time_posix (int): reference frame time

    Returns:
    A tuple of Vector3D(x,y,z):
        Position Vector:
            x = GCRS X-coordinate (m)
            y = GCRS Y-coordinate (m)
            z = GCRS Z-coordinate (m)
        Velocity Vector
            x = GCRS X-velocity (m/s)
            y = GCRS Y-velocity (m/s)
            z = GCRS Z-velocity (m/s)

    Note:
        Unlike the rest of the software that uses J2000 FK5, the ECI frame used here is
        GCRS; This can potentially introduce around 200m error for locations on surface of Earth.
    """
    posix_time = Time(posix_time, format='unix')
    cart_diff = coordinates.CartesianDifferential(*ecef_vel, unit='m/s')
    cart_rep = coordinates.CartesianRepresentation(*ecef_coords, unit='m', differentials=cart_diff)

    ecef = coordinates.ITRS(cart_rep, obstime=posix_time)
    gcrs = ecef.transform_to(coordinates.GCRS(obstime=posix_time))

    # pylint: disable=no-member
    return (Vector3D(*gcrs.cartesian.xyz.value),
            Vector3D(*gcrs.cartesian.differentials.values()[0].d_xyz.to(units.m / units.s).value))
    # pylint: enable=no-member
