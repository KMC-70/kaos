"""This file defines the constants used in satellite-to-site visibility calculations.

Author: Team KMC-70
"""

# WGS84 ellipsoid constants
ELLIPSOID_A = 6378137
ELLIPSOID_E = 8.1819190842622e-2

# Viewing cone calculation constants
ANGULAR_VELOCITY_EARTH = 7.2921159e-5  # at equator
SECONDS_PER_DAY = 86164  # 23:56:04, in seconds
THETA_NAUGHT = 0  # visibility threshold
J2000 = 946684800  # Jan 1st 1970 in POSIX
