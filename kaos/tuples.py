"""This file contains the data structures used in KAOS.

Author: Team KMC-70
"""

from collections import namedtuple


class Vector3D(namedtuple('Vector3D', 'x, y, z')):
    """Representation of a 3D cartesian vector."""
    __slots__ = ()

    def __str__(self):
        return 'Vector3D: x={}, y={}, z={}'.format(self.x, self.y, self.z)


class TimeInterval(namedtuple('TimeInterval', 'start, end')):
    """Tuple that represents a time interval."""
    __slots__ = ()

    def __str__(self):
        return 'TimeInterval: start={}, end={}'.format(self.start, self.end)


class OrbitPoint(namedtuple('OrbitPoint', 'time, pos, vel')):
    """Orbit information for a given point in time."""
    __slots__ = ()

    def __str__(self):
        return 'OrbitPoint: time={}, pos={}, vel={}'.format(self.time, self.pos, self.vel)
