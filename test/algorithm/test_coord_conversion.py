from algorithm import coord_conversion
from ddt import ddt,data
import pytest, unittest

@ddt
class Test_lla_to_ecef(unittest.TestCase):

    @data((0.0,0.0,0.0,6378137.0,0.0,0.0),
          (49.2827,-123.1207,0.0,-2277772.9,-3491338.7,4811126.5),
          (43.7615,-79.41107,0.0,847846.8,-4535275.1,4388991.1),
          (39.9138,116.3636,0.0,-2175414.8,4389344.3,4070649.0),
          (27.9861,86.9226,8848,303011.566,5636116.783,2979297.096))
    def test_lla_to_ecef(self,test_data):
        """
        Test for lat,lon,height to ECEF conversion with 0.1 meter accuracy
        test_data format:
          input lat, input lon, hight,  expectd x, expected y, expected z
        Values generated using: https://www.ngs.noaa.gov/NCAT/
        """
        ecef = coord_conversion.lla_to_ecef(test_data[0],test_data[1],test_data[2])
        self.assertAlmostEqual(ecef[0], test_data[3], places=1)
        self.assertAlmostEqual(ecef[1], test_data[4], places=1)
        self.assertAlmostEqual(ecef[2], test_data[5], places=1)

@ddt
class Test_geod_to_geoc_lat(unittest.TestCase):

    @data((0.0,0.0),(10.0,9.9344),(25,24.8529),(45.0,44.8076),(-11,-10.9281),
          (-63.55648,-63.4027),(89.99,89.9899),(-89.9799,-89.9798),(53.2576,53.0729),
          (90,90),(-90,-90))
    def test_geod_to_geoc_lat(self,test_data):
        """
        Test for latitude conversion from geodetic to geocentric with 0.0001 accuracy
        test_data format:
          latitude(geodetic-WGS84), expected latitude(geocentric)
        Values generated using Matlab: geod2geoc(lat,0,'WGS84')
        """
        geoc_lat_deg = coord_conversion.geod_to_geoc_lat(test_data[0])
        self.assertAlmostEqual(geoc_lat_deg,test_data[1],places=4)

@ddt
class Test_lla_to_eci(unittest.TestCase):

    @data((0,0,0,946684800,(-1.1040230676e+6,6.28185996625e+6,145.726867)),
        (10,120,0,946684800,(-4.81449119049e+6,-4.0352367821e+6,1.100005365e+6)),
        (-25,80,0,946684800,(-5.78394065413e+6,3.324200655e+3,-2.6792309935e+6)),
        (-70.54,-12.53,0,946684800,(9.5436e+4,2.1293e+6,-5.9913e+6)),
        (60.21,-80.46,0,946684800,(2.9943e+6,1.0607e+6,5.5122e+6)))
    def test_lla_to_eci(self,test_data):
        """
        Test for lat,lon,alt conversion to GCRS
        Note the 200m delta, see function docstring for details.

        Test_data format:
          lat,lon,alt,time_posix,(GCRS expected x,GCRS expected y,GCRS expected z)
        Values generated using Matlab: lla2eci([lat,lon,alt],time) which is in a J2000 FK5 frame
        """
        loc_eci = coord_conversion.lla_to_eci(test_data[0],test_data[1],test_data[2],test_data[3])
        self.assertAlmostEqual(loc_eci[0],test_data[4][0],delta=200)
        self.assertAlmostEqual(loc_eci[1],test_data[4][1],delta=200)
        self.assertAlmostEqual(loc_eci[2],test_data[4][2],delta=200)
