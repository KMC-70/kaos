from math import sqrt,sin,cos,pi,atan,tan
from numpy import rad2deg,deg2rad
from astropy import coordinates, units
from astropy.time import Time
from kaos.algorithm import Vector3D

def lla_to_ecef(lat, lon, alt=0):
    """converts latitude, longitude, and altitude to earth-centered, earth-fixed (ECEF) Cartesian.

    Args:
    lat = geodetic latitude (decimal degrees)
    lon = longitude (decimal degrees)
    alt = height above WGS84 ellipsoid (m)

    Returns:
    (x,y,z) such that:
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

    # WGS84 ellipsoid constants:
    a = 6378137
    e = 8.1819190842622e-2
    #decimal degrees to radians
    lat = lat/360*2*pi
    lon = lon/360*2*pi
    # intermediate calculation
    # (prime vertical radius of curvature)
    N = a / sqrt(1 - pow(e,2) * pow(sin(lat),2))
    # results:
    x = (N+alt) * cos(lat) * cos(lon)
    y = (N+alt) * cos(lat) * sin(lon)
    z = ((1-pow(e,2)) * N + alt) * sin(lat)

    return (x,y,z)

def geod_to_geoc_lat(geod_lat_deg):
    """Converts geodetic latitude to geocentric latitude

    Args:
    geod_lat_deg = geodetic latitude (decimal degrees)

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

def lla_to_eci(lat, lon, alt=0, time_posix=946684800):
    """
    Converts geodetic lat,lon,alt, to a Cartesian vector in GCRS frame at the given time.

    Args:
    at = geodetic latitude (decimal degrees)
    lon = longitude (decimal degrees)
    alt = height above WGS84 ellipsoid (m)
    time_posix= reference frame time

    Returns:
    Vector3D(x,y,z) such that:
      x = GCRS X-coordinate (m)
      y = GCRS Y-coordinate (m)
      z = GCRS Z-coordinate (m)

    Important Note: Unlike the rest of the software that uses J2000 FK5, the ECI frame used here is
    GCRS; This can potentially introduce around 200m error for locations on surface of Earth.
    """
    posix_zero = Time(time_posix, format='unix')
    loc_lla = coordinates.EarthLocation.from_geodetic(lon,lat,alt)
    loc_eci = loc_lla.get_gcrs_posvel(posix_zero)
    return Vector3D(loc_eci[0].x.value,loc_eci[0].y.value,loc_eci[0].z.value)