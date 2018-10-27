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
