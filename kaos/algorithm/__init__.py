# Copyright (c) 2018 Zeyad Tamimi.  All rights reserved.

from collections import namedtuple

Vector3D = namedtuple( "Vector3D", "x,y,z" )
TimeInterval = namedtuple( "TimeInterval", "start,end")
# WGS84 ellipsoid constants:
ELLIPSOID_A = 6378137
ELLIPSOID_E = 8.1819190842622e-2

# Viewing cone calculation constants:
ANG_VEL_EARTH =  7.2921159e-5
SECONDS_PER_DAY = 86164 #23:56:04
THETA_NAUGHT = 0 #visibility threshold

class ViewConeFailure(Exception):
    """ Raised when Viewing cone algorithm cannot shrink the input interval"""
    pass
