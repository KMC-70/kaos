"""This module contains all functions required to perform the visibility computations.

These computations are based on a paper by Chao Han, Xiaojie Gao and Xiucong Sun:
    Rapid Satellite-to-Site Visibility Determination Based on Self-Adaptive Interpolation Technique.
    https://arxiv.org/abs/1611.02402
"""
# pylint: disable=too-many-locals

from __future__ import division

import logging

import numpy as np
import mpmath as mp

from .interpolator import Interpolator
from .coord_conversion import lla_to_ecef
from ..errors import VisibilityFinderError


class VisibilityFinder(object):
    """An adaptive visibility finder used to determine the visibility interval of a point on earth
    from a satellite.
    """

    def __init__(self, satellite_id, site, interval):
        """Args:
            satellite_id (integer): Satellite ID in the database
            site (tuple:float): The site location as a lat/lon tuple
            interval (tuple:float): The search window as a start_time, end_time tuple
        """
        self.satellite_id = satellite_id
        self.site = site
        self.interval = interval

        self.sat_irp = Interpolator(satellite_id)

    def visibility(self, posix_time):
        """Calculate the visibility function of the satellite and the site at a given time.

        Args:
            posix_time (float): The time to evaluate the visibility function at

        Returns:
            The value of the visibility function evaluated at the provided time.

        Note:
            This function assumes the FOV of the sensors on the satellite are 180 degrees
        """

        # Since most helper functions don't play well with mpmath floats we have to perform a lossy
        # conversion.
        posix_time = float(posix_time)
        site_pos = np.array(lla_to_ecef(self.site[0], self.site[1], 0)) * mp.mpf(1.0)
        site_normal_pos = site_pos / mp.norm(site_pos)
        sat_pos = self.sat_irp.interpolate(posix_time)[0]
        sat_site = np.subtract(sat_pos, site_pos)

        return mp.mpf(mp.fdot(sat_site, site_normal_pos) / mp.norm(sat_site))

    def visibility_first_derivative(self, posix_time):
        """Calculate the derivative of the visibility function of the satellite and the site at a
        given time.

        Args:
            posix_time (float): The UNIX time to evaluate the derivative visibility function at.

        Returns:
            The value of the visibility function evaluated at the provided time.
        """

        # Since most helper functions don't play well with mpmath floats we have to perform a lossy
        # conversion.
        posix_time = float(posix_time)
        sat_pos_vel = np.array(self.sat_irp.interpolate(posix_time)) * mp.mpf(1.0)
        site_pos = np.array(lla_to_ecef(self.site[0], self.site[1], 0)) * mp.mpf(1.0)

        pos_diff = np.subtract(sat_pos_vel[0], site_pos[0])
        vel_diff = sat_pos_vel[1]

        site_normal_pos = site_pos / mp.norm(site_pos)
        site_normal_vel = [0, 0, 0]

        first_term = mp.mpf(((1.0 / mp.norm(pos_diff)) *
                             (mp.fdot(vel_diff, site_normal_pos) +
                              mp.fdot(pos_diff, site_normal_vel))))

        second_term = mp.mpf(((1.0 / mp.power((mp.norm(pos_diff)), 3)) *
                              mp.fdot(pos_diff, vel_diff) * mp.fdot(pos_diff, site_normal_pos)))

        return first_term - second_term

    # pylint: disable=invalid-name
    def visibility_fourth_derivative_max(self, sub_interval):
        """Calculate the maximum of the fourth derivative of the visibility function of the
        satellite through a given sub interval.

        Args:
            time (float): The time at which to evaluate the fourth derivative of the  visibility
                          function
            time_interval (tuple): A tuple containing the time stamps that mark the boundaries of
                                   the subinterval under consideration.

        Returns:
            The value of the visibility function evaluated at the provided time.

        Note:
            This function uses the approximation defined in the Rapid Satellite-to-Site Visibility
            paper.
        """
        start_time, end_time = sub_interval
        interval_length = end_time - start_time
        mid_time = start_time + (interval_length / 2)

        # In order to approximate the fourth order derivative, we need to evaluate both the
        # visibility function and its first derivative at 3 points:
        #   1- The interval start
        #   2- The interval midpoint
        #   3- The interval end
        visibility_start = mp.mpf(self.visibility(start_time))
        visibility_mid = mp.mpf(self.visibility(mid_time))
        visibility_end = mp.mpf(self.visibility(end_time))

        visibility_d_start = mp.mpf(self.visibility_first_derivative(start_time))
        visibility_d_mid = mp.mpf(self.visibility_first_derivative(mid_time))
        visibility_d_end = mp.mpf(self.visibility_first_derivative(end_time))

        # Calculating the a5 and a4 constants used in the approximation
        a5 = mp.mpf((((24.0 / (interval_length ** 5.0)) * (visibility_start - visibility_end)) +
                     ((4.0 / (interval_length ** 4.0)) *
                      (visibility_d_start + (4.0 * visibility_d_mid) + visibility_d_end))))

        # Since a4's computation is complex, it was split into several parts
        a4_first_term = mp.mpf(((4.0 / (interval_length ** 4.0)) *
                                (visibility_start + (4.0 * visibility_mid) + visibility_end)))
        a4_second_term = mp.mpf(((4.0 / (interval_length ** 4.0)) *
                                 ((visibility_d_start * ((2.0 * start_time) + (3.0 * end_time))) +
                                  ((10.0 * visibility_d_mid) * (start_time + end_time)) +
                                  (visibility_d_end * ((3.0 * start_time) + (2.0 * end_time))))))
        a4_third_term = mp.mpf(((24.0 / (interval_length ** 5.0)) *
                                ((visibility_start * ((2.0 * start_time) + (3.0 * end_time))) -
                                 (visibility_end * ((3.0 * start_time) + (2.0 * end_time))))))

        a4 = a4_first_term - a4_second_term - a4_third_term

        return max(abs((120 * a5 * start_time) + (24 * a4)), abs((120 * a5 * end_time) + (24 * a4)))
        # pylint: enable=invalid-name

    def bound_time_step_error(self, time_interval, error):
        """Corrects the time step for the current sub interval to mach the desired error rate.

        Args:
            time_interval (tuple): The two UNIX timestamps that bound the desired sub-interval
            error (float): The desired approximate error in results. This error is the max deviation
                           presented as the difference between the approximated and real value of
                           the visibility function

        Returns:
            The new time step to use in order to mach the approximate error.

        """
        # First we compute the maximum of the fourth derivative as per eq 8 in the referenced
        # paper
        visibility_4_prime_max = self.visibility_fourth_derivative_max(time_interval)

        # Then we use the error and eq 9 to calculate the new time_step.
        return mp.power((16.0 * mp.mpf(error)) / (visibility_4_prime_max / 24), 0.25)

    def find_approx_coeffs(self, time_interval):
        """Calculates the coefficients of the Hermite approximation to the visibility function for a
        given interval.

        Args:
            interval (tuple): The two UNIX timestamps that bound the desired interval

        Returns:
            An array containing the coefficients for the Hermite approximation of the
            visibility function

        Note:
            This function assumes the FOV of the sensors on the satellite are 180 degrees
        """
        start_time, end_time = time_interval
        time_step = mp.mpf(end_time - start_time)
        visibility_start = mp.mpf(self.visibility(start_time))
        visibility_end = mp.mpf(self.visibility(end_time))
        visibility_first_start = mp.mpf(self.visibility_first_derivative(start_time))
        visibility_first_end = mp.mpf(self.visibility_first_derivative(end_time))

        const = (((-2 * (start_time ** 3) * visibility_start) / (time_step ** 3)) +
                 ((2 * (start_time ** 3) * visibility_end) / (time_step ** 3)) +
                 ((-1 * (start_time ** 2) * end_time * visibility_first_end) / (time_step ** 2)) +
                 ((-1 * 3 * (start_time ** 2) * visibility_start) / (time_step ** 2)) +
                 ((3 * (start_time ** 2) * visibility_end) / (time_step ** 2)) +
                 ((-1 * start_time * (end_time ** 2) * visibility_first_start) / (time_step ** 2)) +
                 visibility_start)

        t_coeffs = (((6 * (start_time ** 2) * visibility_start) / (time_step ** 3)) +
                    ((-1 * 6 * (start_time ** 2) * visibility_end) / (time_step ** 3)) +
                    (((start_time ** 2) * visibility_first_end) / (time_step ** 2)) +
                    ((2 * start_time * end_time * visibility_first_start) / (time_step ** 2)) +
                    ((2 * start_time * end_time * visibility_first_end) / (time_step ** 2)) +
                    ((6 * start_time * visibility_start) / (time_step ** 2)) +
                    ((-1 * 6 * start_time * visibility_end) / (time_step ** 2)) +
                    (((end_time ** 2) * visibility_first_start) / (time_step ** 2)))

        t_2_coeffs = (((-1 * 6 * start_time * visibility_start) / (time_step ** 3)) +
                      ((6 * start_time * visibility_end) / (time_step ** 3)) +
                      ((-1 * start_time * visibility_first_start) / (time_step ** 2)) +
                      ((-1 * 2 * start_time * visibility_first_end) / (time_step ** 2)) +
                      ((-1 * 2 * end_time * visibility_first_start) / (time_step ** 2)) +
                      ((-1 * end_time * visibility_first_end) / (time_step ** 2)) +
                      ((-1 * 3 * visibility_start) / (time_step ** 2)) +
                      ((3 * visibility_end) / (time_step ** 2)))

        t_3_coeffs = (((2 * visibility_start) / (time_step ** 3)) +
                      ((-1 * 2 * visibility_end) / (time_step ** 3)) +
                      ((visibility_first_start) / (time_step ** 2)) +
                      ((visibility_first_end) / (time_step ** 2)))

        return [t_3_coeffs, t_2_coeffs, t_coeffs, const]

    def find_visibility(self, time_interval):
        """Given a sub interval, this function uses the adaptive Hermite interpolation method to
        calculate the roots of the visibility function and hence the visibility period.

        Args:
            time_interval (tuple): The subinterval over which the visibility period is to be
            calculated.

        """
        # Calculate angle of visibility theta.
        roots = mp.polyroots(self.find_approx_coeffs(time_interval), maxsteps=2000,
                             extraprec=110)

        return roots

    def determine_visibility(self, error=0.1, tolerance_ratio=0.1, max_iter=100):
        """Using the self adapting interpolation algorithm described in the cited paper, this
        function returns the subintervals for which the satellites have visibility.

        The accuracy of this function is tuned by changing:
            * error
            * tolerance_ratio
            * max_iter

        The error in each interpolation sub period is defined by an approximate error tolerance.
        This error tolerance is approximate since the algorithm will deem the accuracy sufficient
        when for a give interpolation sub period either:
            * The max number of iterations is exceeded
            * The tolerance ratio is exceeded

        Args:
            error (float): The desired approximate error in results. This error is the max deviation
                           presented as the difference between the approximated and real value of
                           the visibility function. Defaults to 0.1
            tolerance_ratio (float, optional): The tolerance ratio of the desired error.
                                               Defaults to 0.1
            max_iter (int, optional): The maximum number of iterations per sub interval. Defaults to
                                      100

        Returns:
            The subintervals over which the site is visible.

        Note:
            This function assumes a viewing angle of 180 degrees
        """
        start_time, end_time = self.interval

        # Initialize the algorithm variables
        subinterval_start = start_time
        # The subinterval_end is set to start the initial loop iteration
        subinterval_end = start_time
        # Defines the length of the initial subinterval (h)
        prev_time_step = 1000

        # Check if we began scanning in the beginning of an access interval
        sat_accesses = []
        if self.visibility(start_time) > 0:
            access_start = start_time
        else:
            access_start = None

        while subinterval_end < end_time:
            new_time_step_1 = prev_time_step
            # Hack loop since python does not support do-while
            iter_num = 0
            while True:
                subinterval_end = subinterval_start + new_time_step_1

                new_time_step_2 = self.bound_time_step_error((subinterval_start, subinterval_end),
                                                             error)
                if ((abs(new_time_step_2 - new_time_step_1)) / new_time_step_1) <= tolerance_ratio:
                    break

                if (iter_num >= max_iter) and (new_time_step_1 <= new_time_step_2):
                    break

                new_time_step_1 = new_time_step_2
                iter_num += 1

            # At this stage for the current interpolation stage the time step is sufficiently small
            # to keep the error low
            new_time_step = new_time_step_1
            subinterval_end = subinterval_start + new_time_step

            roots = [root for root in self.find_visibility((subinterval_start, subinterval_end))
                     if isinstance(root, mp.mpf) and root <= subinterval_end
                     and root >= subinterval_start]

            for root in roots:
                if access_start is None:
                    access_start = root
                else:
                    sat_accesses.append((access_start, root))
                    access_start = None

            # Set the start time and time step for the next interval
            subinterval_start = subinterval_end
            prev_time_step = new_time_step

        # If the loop terminates and an access end was still not found that means that point should
        # still be visible at the end of the period.
        # NOTE: subinterval_end would also work here but is difficult to test.
        if access_start is not None:
            if self.visibility(end_time) <= 0:
                raise VisibilityFinderError("Visibility interval started at {} "
                                            "but did not end at {}".format(access_start, end_time))
            sat_accesses.append((access_start, end_time))

        return sat_accesses
