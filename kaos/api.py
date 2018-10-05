"""
This file contains routing code for the APIs. It should not contain much.

Author: Team KMC-70.
"""

from flask import Blueprint, request

# pylint: disable=invalid-name
bp = Blueprint('api', __name__, url_prefix='/api')
# pylint: enable=invalid-name

@bp.route('/')
def get_visible_satellites():
    """
    Get the number of satellites that have visibility to a site.

    Requires:
        The user supplies a query param, 'coords.'

    Returns:
        A string to be displayed.
    """
    coords = request.args.get('coords')
    if not coords:
        return "Bad API request, no satellites for you."

    x, y = coords.replace(' ', '').split(',')

    return "Over 9000 satellites can view location: {},{}".format(x, y)

