from math import sqrt,sin,cos,pi

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