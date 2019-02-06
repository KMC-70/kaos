from ddt import ddt, data

from kaos.algorithm.visibility_finder import VisibilityFinder
from kaos.models import Satellite
from kaos.models.parser import parse_ephemeris_file

from . import KaosVisibilityFinderTestCase

@ddt
class TestVisibilityFinder(KaosVisibilityFinderTestCase):
    """Test the visibility finder's accuracy."""

    @classmethod
    def setUpClass(cls):
        super(TestVisibilityFinder, cls).setUpClass()
        parse_ephemeris_file("ephemeris/Radarsat2.e")

    @data(('test/algorithm/vancouver.test', (1514764802, 1514764802+6*24*60*60), 60))
    def test_full_visibility(self, test_data):
        """Tests that the visibility finder produces the same results as the access file.

        Args:
            test_data (tuple): A three tuple containing the:
                                1 - The path of KAOS access test file
                                2 - A tuple of the desired test duration
                                3 - The maximum tolerated deviation in seconds
        Note:
            Ranges provided must not start or end at an access boundary. This is a result of the
            strict checking method provided.
        """
        access_file, interval, max_error = test_data

        access_info = self.parse_access_file(access_file)
        finder = VisibilityFinder(Satellite.get_by_name(access_info.sat_name)[0].platform_id,
                                  access_info.target, interval)
        access_times = finder.determine_visibility_perf()

        for predicted_access in access_times:
            found = False
            for actual_access in access_info.accesses:
                if (interval[0] > actual_access[0]) and (interval[1] < actual_access[1]):
                    if ((abs(interval[0] - predicted_access[0]) < max_error) and
                            (abs(interval[1] - predicted_access[1]) < max_error)):
                        found = True
                        break
                if interval[0] > actual_access[0]:
                    if ((abs(interval[0] - predicted_access[0]) < max_error) and
                            (abs(actual_access[1] - predicted_access[1]) < max_error)):
                        found = True
                        break
                elif interval[1] < actual_access[1]:
                    if ((abs(actual_access[0] - predicted_access[0]) < max_error) and
                            (abs(interval[1] - predicted_access[1]) < max_error)):
                        found = True
                        break

                if ((abs(actual_access[0] - predicted_access[0]) < max_error) and
                        (abs(actual_access[1] - predicted_access[1]) < max_error)):
                    found = True
                    break

            if not found:
                raise Exception('Wrong access: {}'.format(predicted_access))

