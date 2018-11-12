# Copyright (c) 2018 Zeyad Tamimi.  All rights reserved.

from collections import namedtuple

Vector3D = namedtuple( "Vector3D", "x,y,z" )

# WGS84 ellipsoid constants:
ELLIPSOID_A = 6378137
ELLIPSOID_E = 8.1819190842622e-2
