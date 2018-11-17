"""This module contains all functions required to perform the self adating hermite computations."""

import numpy as np

from .interpolator import Interpolator
from .coord_conversion import lla_to_eci

class VisibilityFinder(object):

    """An adaptive visibility finder used to determine the visibility interval of a satellite."""

    def __init__(self, satellite_id, site, interval):
        """Args:
            sattelite_id (integer): Satellite ID in the database
            site (tuple:float): The site location as a lat/lon tupple
            interval (tuple:float): The search window as a start_time, end_time tuple
        """
        self.satellite_id = satellite_id
        self.site = site
        self.interval = interval

        self.sat_irp = Interpolator(satellite_id)

    def satellite_visibility(self, posix_time):
        """Calculate the visibility function of the satellite and the site at a given time.

        Args:
            posix_time (float): The time to evaluate the visbility function at

        Returns:
            The value of the visibility function evaluated at the provided time.
        """
        site_pos = lla_to_eci(self.site[0], self.site[1], 0, posix_time)[0]
        site_normal_pos = site_pos/np.linalg.norm(site_pos)
        sat_pos = self.sat_irp.interpolate(posix_time)[0]
        sat_site = np.subtract(sat_pos, site_pos)

        return (sat_site * site_normal_pos) / np.linalg.norm(sat_site)

    def satallite_visibility_derivative(self, posix_time):
        """Calculate the dirivative of the visibility function of the satellite and the site at a
        given time.

        Args:
            posix_time (float): The time to evaluate the dirivative visbility function at.

        Returns:
            The value of the visibility function evaluated at the provided time.
        """
        sat_pos_vel = self.sat_irp.interpolate(posix_time)
        site_pos_vel = lla_to_eci(self.site[0], self.site[1], 0, posix_time)

        sat_site_pos = np.subtract(sat_pos_vel[0], site_pos_vel[0])
        sat_site_vel = np.subtract(sat_pos_vel[1], site_pos_vel[1])

        site_normal_pos = site_pos_vel[0]/np.linalg.norm(site_pos_vel[0])
        site_normal_vel = site_pos_vel[1]/np.linalg.norm(site_pos_vel[1])

        return (((1/np.linalg.norm(sat_site_pos)) *
                 (sat_site_vel * site_normal_pos) + (site_normal_pos * site_normal_vel)) -
                ((1/np.linalg.norm(sat_site_pos)**3) *
                 (sat_site_pos * sat_site_vel) * (sat_site_pos * site_normal_pos)))

