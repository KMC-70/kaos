from math import asin,atan,sqrt,sin,cos,pi
from  kaos.algorithm.coord_conversion import lla_to_ecef,geod_to_geoc_lat
import numpy

ang_vel_earth = 7.2921159 * pow(10,-5)
theta_naught = 0 #visibility threshold

def view_cone_calc():

    # TODO: Set this to be a range of values based on period of interest
    m = 0

    #TODO: Get these from db instead
    v_sat = (-1.0403250597511601e+02, 3.9287755525413295e+03,-4.0852319656141594e+03)
    r_sat = (-4.3505082856028304e+06,-9.5770906938376985e+06,-9.0462013544963021e+06)

    #TODO: Add function to calculate maximum orbital radius = a(1+e)
    q_magnitude = 6970.181856*1000*(1+0.004969)

    #TODO: Get these from input
    lat_geoc = numpy.deg2rad(geod_to_geoc_lat(25))
    lon_geoc = numpy.deg2rad(110)
    (r_site_x,r_site_y,r_site_z) = lla_to_ecef(25,110)

    r_site_magnitude = numpy.linalg.norm([r_site_x,r_site_y,r_site_z])

    (p_hat_x, p_hat_y, p_hat_z) = numpy.cross(r_sat,v_sat) \
                                  /(numpy.linalg.norm(r_sat) * numpy.linalg.norm(v_sat))

    gamma = theta_naught + asin(r_site_magnitude * sin(pi/2+theta_naught) \
                                /q_magnitude)

    t1 = (1/ang_vel_earth)*(asin(cos(gamma)-(p_hat_z*sin(lat_geoc)) \
                                /sqrt((p_hat_x**2)+(p_hat_y**2))*cos(lat_geoc))- \
            lon_geoc - atan(p_hat_x/p_hat_y) + 2*pi*m)

    t2 = (1/ang_vel_earth)*(pi - asin(cos(gamma)-(p_hat_z*sin(lat_geoc)) \
                                /sqrt((p_hat_x**2)+(p_hat_y**2))*cos(lat_geoc))+ \
            lon_geoc + atan(p_hat_x/p_hat_y) + 2*pi*m)

    return t1, t2