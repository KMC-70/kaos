"""This module contains all functions required to perform the self adapting Hermite computations."""

from __future__ import division
import numpy as np
import mpmath
import mpmath as mp
mp.mp.dps = 100

from .interpolator import Interpolator
from .coord_conversion import lla_to_eci

class VisibilityFinder(object):

    """An adaptive visibility finder used to determine the visibility interval of a satellite."""

    def __init__(self, satellite_id, site, interval):
        """Args:
            sattelite_id (integer): Satellite ID in the database
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
        """
        posix_time = float(posix_time)
        site_pos = lla_to_eci(self.site[0], self.site[1], 0, posix_time)[0]
        site_normal_pos = site_pos/np.linalg.norm(site_pos)
        sat_pos = self.sat_irp.interpolate(posix_time)[0]
        sat_site = np.subtract(sat_pos, site_pos)
        return mpmath.mpf(mpmath.fdot(sat_site, site_normal_pos) / mpmath.norm(sat_site))

    def visibility_first_derivative(self, time):
        """Calculate the derivative of the visibility function of the satellite and the site at a
        given time.

        Args:
            time (float): The UNIX time to evaluate the derivative visibility function at.

        Returns:
            The value of the visibility function evaluated at the provided time.
        """
        sat_pos_vel = self.sat_irp.interpolate(float(time))
        site_pos_vel = lla_to_eci(self.site[0], self.site[1], 0, time)
        sat_site_pos = np.subtract(sat_pos_vel[0], site_pos_vel[0])
        sat_site_vel = np.subtract(sat_pos_vel[1], site_pos_vel[1])

        site_normal_pos = np.divide(site_pos_vel[0], mp.norm(site_pos_vel[0]))
        site_normal_vel = np.divide(site_pos_vel[1], mp.norm(site_pos_vel[1]))

        first_term = mp.mpf(((1.0 / mp.norm(sat_site_pos)) *
                             (mp.fdot(sat_site_vel, site_normal_pos) +
                              mp.fdot(sat_site_pos, site_normal_vel))))

        second_term = mp.mpf(((1.0 / (mp.norm(sat_site_pos) ** 3.0)) *
                              mp.fdot(sat_site_pos, sat_site_vel) *
                              mp.fdot(sat_site_pos, site_normal_pos)))

        return  first_term - second_term

    def visibility_fourth_derivative(self, sub_interval):
        """Calculate the fourth derivative of the visibility function of the satellite and the site
        at a given time.

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
        #pylint: disable=too-many-locals
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
        a4_first_term = mpmath.mpf(((4.0 / (interval_length ** 4.0)) *
                         (visibility_start + (4.0 * visibility_mid) + visibility_end)))
        a4_second_term = mpmath.mpf(((4.0 / (interval_length ** 4)) *
                          ((visibility_d_start * ((2.0 * start_time) + (3.0 * end_time))) +
                           ((10.0 * visibility_d_mid) * (start_time + end_time)) +
                           (visibility_d_end * ((3.0 * start_time) + (2.0 * end_time))))))
        a4_third_term = mpmath.mpf(((24.0 / (interval_length ** 5.0)) *
                         ((visibility_start * ((2.0 * start_time) + (3.0 * end_time))) -
                          (visibility_end * ((3.0 * start_time) + (2.0 * end_time))))))
        a4 = a4_first_term - a4_second_term - a4_third_term

        # Using the above co-efficients we can determine the approximation as per Eq 5 of the cited
        # paper
        if a5 > 0:
            return (120 * a5 * end_time) + (24 * a4)
        else:
            return (120 * a5 * start_time) + (24 * a4)

    def bound_time_step_error(self, interval, error):
        """Corrects the time step for the current sub interval as to mach error to the desired rate.

        Args:
            interval (tuple): The two UNIX timestamps that bound the desired sub-interval
            error (float): The desired approximate error in results

        Returns:
            The new time step to use in order to mach the approximate error.

        Note:
        """
        # First we compute the maximum of the fourth derivative as per Eq 8 in the referenced
        # paper
        visibility_4_prime_max = self.visibility_fourth_derivative(interval)

        # Then we use the error and Eq 9 to calculate the new time_step.
        return pow((16.0 * error) / (visibility_4_prime_max / 24), 0.25)

    def find_approx_coeffs(self, start_time, end_time):
        """Calculates the coefficients of the Hermite approximation to the visibility function for a
        given interval.

        Args:
            start_timer (float): The UNIX time-stamp corresponding to the beginning of the period to
                                 be interpolated
            end_timer (float): The UNIX time-stamp corresponding to the end of the period to be
                               interpolated

        Returns:
            An array containing the coefficients for the Hermite approximation of the
            visibility function

        Note:
            The coefficients do not take into account the visibility angle theta.
        """
        time_step = mpmath.mpf(end_time - start_time)
        visibility_start = mpmath.mpf(self.visibility(start_time))
        visibility_end = mpmath.mpf(self.visibility(end_time))
        visibility_first_start = mpmath.mpf(self.visibility_first_derivative(start_time))
        visibility_first_end = mpmath.mpf(self.visibility_first_derivative(end_time))


        const = (((-2 * (start_time ** 3) * visibility_start) / (time_step ** 3)) +
                 ((2 * (start_time ** 3) * visibility_end) / (time_step ** 3)) +
                 ((-1 * (start_time ** 2) * end_time * visibility_first_end) / (time_step ** 2)) +
                 ((-1 * 3 * (start_time ** 2) * visibility_start) / (time_step ** 2)) +
                 ((3 * (start_time ** 2) * visibility_end) / (time_step ** 2)) +
                 ((-1 * start_time * (end_time ** 2) * visibility_first_start) / (time_step ** 2)) +
                 visibility_start
                )

        t_coeffs = (((6 * (start_time ** 2) * visibility_start) / (time_step ** 3)) +
                    ((-1 * 6 * (start_time ** 2) * visibility_end) / (time_step ** 3)) +
                    (((start_time ** 2) * visibility_first_end) / (time_step ** 2)) +
                    ((2 * start_time * end_time * visibility_first_start) / (time_step ** 2)) +
                    ((2 * start_time * end_time * visibility_first_end) / (time_step ** 2)) +
                    ((6 * start_time * visibility_start) / (time_step ** 2)) +
                    ((-1 * 6 * start_time * visibility_end) / (time_step ** 2)) +
                    (((end_time ** 2) * visibility_first_start) / (time_step ** 2))
                   )

        t_2_coeffs = (((-1 * 6 * start_time * visibility_start) / (time_step ** 3)) +
                      ((6 * start_time * visibility_end) / (time_step ** 3)) +
                      ((-1 * start_time * visibility_first_start) / (time_step ** 2)) +
                      ((-1 * 2 * start_time * visibility_first_end) / (time_step ** 2)) +
                      ((-1 * 2 * end_time * visibility_first_start) / (time_step ** 2)) +
                      ((-1 * end_time * visibility_first_end) / (time_step ** 2)) +
                      ((-1 * 3 * visibility_start) / (time_step ** 2)) +
                      ((3 * visibility_end) / (time_step ** 2))
                     )

        t_3_coeffs = (((2 * visibility_start) / (time_step ** 3)) +
                      ((-1 * 2 * visibility_end) / (time_step ** 3)) +
                      ((visibility_first_start) / (time_step ** 2)) +
                      ((visibility_first_end) / (time_step ** 2))
                     )
        midpoint_t = mpmath.mpf((start_time + end_time ) / 2.0)
        # print("approximate:")
        # print(mpmath.polyval([t_3_coeffs, t_2_coeffs, t_coeffs, const],midpoint_t))
        # print("real:")
        realval = self.visibility(midpoint_t)
        # print(realval)
        print("real error: ")
        print(abs(realval-mpmath.polyval([t_3_coeffs, t_2_coeffs, t_coeffs, const],midpoint_t)))
        if realval>0:
            print('VISIBLE')
        return [t_3_coeffs, t_2_coeffs, t_coeffs, const]

    def find_visibility(self, time_interval):
        """Given a sub interval, this function uses the adaptive Hermite interpolation method to
        calculate the roots of the visibility function and hence the visibility period.

        Args:
            time_interval (tuple): The subinterval over which the visibility period is to be
            calculated.

        """
        # Calculate angle of visibility theta.
        roots = mpmath.polyroots(self.find_approx_coeffs(*time_interval),maxsteps=2000, extraprec=110)
        # TODO we need to look at the roots and ignore ones outside the time interval
        # TODO I HAVE NO IDEA HOW THIS WILL WORK or what this will do, save me
        return roots

    def determine_visibility(self, error=0.1, tolerance_ratio=0.1, max_iter=1000000):
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
            error (float, optional): Tolerance value of approximated error. Defaults to 0.01
            tolerance_ratio (float, optional): The tolerance ratio of the interval time step.
                                               Defaults to 0.1
            max_iter (int, optional): The maximum number of iterations per sub interval. Defaults to
                                      1000

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
        prev_time_step = 5

        while subinterval_end < end_time:
            new_time_step_1 = prev_time_step
            # Hack loop since python does not support do-while
            iter_num = 0
            """
            while True:
                subinterval_end = subinterval_start + new_time_step_1
                new_time_step_2 = self.bound_time_step_error((subinterval_start, subinterval_end),
                                                              error)
                if (float(abs(new_time_step_2 - new_time_step_1)) / new_time_step_1) <= tolerance_ratio:
                    break

                if (iter_num >= max_iter) and (new_time_step_1 <= new_time_step_2):
                    break

                new_time_step_1 = new_time_step_2
                iter_num += 1

            """
            # At this stage for the current interpolation stage the time step is sufficiently small
            # to keep the error low
            new_time_step = new_time_step_1
            subinterval_end = subinterval_start + new_time_step

            roots = self.find_visibility((subinterval_start, subinterval_end))
            error_val = self.visibility_fourth_derivative((subinterval_start,subinterval_end)) * (1/24) * (1/16) * mpmath.mpf(prev_time_step)**4
            import pdb; pdb.set_trace()

            print ("error value :")
            print(error_val)
            # # print(roots[np.isreal(roots)])
            # print(roots)
            # # for root in roots[np.isreal(roots)]:
            # for root in roots:
            #     if root <= subinterval_end and root >= subinterval_start :
            #         print("ROOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOT:")
            #         print(root)

            # print(subinterval_end)
            # if roots:
                # import pdb; pdb.set_trace()
            print("=============================================================")
            # Set the start time and time step for the next interval
            subinterval_start = subinterval_end
            prev_time_step = new_time_step

        return []
