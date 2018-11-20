"""This file contains the data structures used in KAOS.

Author: Team KMC-70
"""

from collections import namedtuple

"""Representation a 3D cartesian vector"""
Vector3D = namedtuple("Vector3D", "x, y, z")

"""Tuple that represents a time interval"""
TimeInterval = namedtuple("TimeInterval", "start, end")

"""Orbit information for a given point in time"""
OrbitPoint = namedtuple("OrbitPoint", "time, pos, vel")
