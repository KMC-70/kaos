"""This file defines the exceptions that KAOS might raise.

Author: Team KMC-70
"""


class ViewConeError(Exception):
    """Raised when the viewing cone algorithm cannot shrink the input interval."""
    pass


class InterpolationError(Exception):
    """Raised when the database has insufficient data points to perform interpolation."""
    pass


class VisibilityFinderError(Exception):
    """Raised when the visibility algorithm enters an inconsistent state."""
    pass
