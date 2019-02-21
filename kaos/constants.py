"""This file defines the constants used in satellite-to-site visibility calculations.

Author: Team KMC-70
"""

import mpmath as mp

# WGS84 ellipsoid constants
ELLIPSOID_A = 6378137
ELLIPSOID_E = 8.1819190842622e-2

# Viewing cone calculation constants
ANGULAR_VELOCITY_EARTH = 7.2921159e-5
EARTH_RADIUS = 6371008.8 # earth's radius (meters)
SECONDS_PER_DAY = 23*60*60 + 56*60 + mp.mpf('4.0989')
THETA_NAUGHT = 0  # visibility threshold (Rad)
J2000 = 946684800  # Jan 1st 2000 @ 00:00 in POSIX (not 12:00)
