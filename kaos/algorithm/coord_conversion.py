from math import sqrt,sin,cos,atan,tan

from numpy import rad2deg,deg2rad
from astropy import coordinates
from astropy.time import Time

from kaos.algorithm import Vector3D,ELLIPSOID_A,ELLIPSOID_E

def lla_to_ecef(lat_deg, lon_deg, alt=0):
    """converts latitude, longitude, and altitude to earth-centered, earth-fixed (ECEF) Cartesian.

    Args:
    lat(int) = geodetic latitude (decimal degrees)
    lon(int) = longitude (decimal degrees)
    alt(int) = height above WGS84 ellipsoid (m)

    Returns:
    Vector3D(x,y,z) such that:
      x = ECEF X-coordinate (m)
      y = ECEF Y-coordinate (m)
      z = ECEF Z-coordinate (m)

    Notes: This function assumes the WGS84 model. Latitude is customary geodetic (not geocentric).

    Source: Adapted from a Matlab script by Michael Kleder
    https://www.mathworks.com/matlabcentral/fileexchange/7942-covert-lat-lon-alt-to-ecef-cartesian

    based on: Department of Defense World Geodetic System 1984"
              Page 4-4
              National Imagery and Mapping Agency
              Last updated June, 2004
              NIMA TR8350.2
    """

    #decimal degrees to radians
    lat_rad = deg2rad(lat_deg)
    lon_rad = deg2rad(lon_deg)
    # intermediate calculation
    # (prime vertical radius of curvature)
    N = ELLIPSOID_A / sqrt(1 - pow(ELLIPSOID_E,2) * pow(sin(lat_rad),2))
    # results:
    x = (N+alt) * cos(lat_rad) * cos(lon_rad)
    y = (N+alt) * cos(lat_rad) * sin(lon_rad)
    z = ((1-pow(ELLIPSOID_E,2)) * N + alt) * sin(lat_rad)

    return Vector3D(x,y,z)

def geod_to_geoc_lat(geod_lat_deg):
    """Converts geodetic latitude to geocentric latitude

    Args:
    geod_lat_deg(int) = geodetic latitude (decimal degrees)

    Returns:
    geocentric latitude (decimal degrees)

    based on:
    https://www.mathworks.com/help/aeroblks/geodetictogeocentriclatitude.html
    http://www.jqjacobs.net/astro/geodesy.html
    http://ccar.colorado.edu/asen5070/handouts/geodeticgeocentric.doc
    """
    flattening = 0.00335281068118
    geod_lat_rad =deg2rad(geod_lat_deg)
    geoc_lat_rad = atan(((1-flattening)**2)*tan(geod_lat_rad))
    return rad2deg(geoc_lat_rad)

def lla_to_eci(lat, lon, alt, time_posix):
    """Converts geodetic lat,lon,alt, to a Cartesian vector in GCRS frame at the given time.

    Args:
    lat(int) = geodetic latitude (decimal degrees)
    lon(int) = longitude (decimal degrees)
    alt(int) = height above WGS84 ellipsoid (m)
    time_posix(int) = reference frame time

    Returns:
    Vector3D(x,y,z) such that:
      x = GCRS X-coordinate (m)
      y = GCRS Y-coordinate (m)
      z = GCRS Z-coordinate (m)

    Important Note: Unlike the rest of the software that uses J2000 FK5, the ECI frame used here is
    GCRS; This can potentially introduce around 200m error for locations on surface of Earth.
    """
    posix_time_internal = Time(time_posix, format='unix')
    loc_lla = coordinates.EarthLocation.from_geodetic(lon,lat,alt)
    loc_eci = loc_lla.get_gcrs_posvel(posix_time_internal)
    return Vector3D(loc_eci[0].x.value,loc_eci[0].y.value,loc_eci[0].z.value)
