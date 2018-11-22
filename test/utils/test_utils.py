"""Testing KAOS's utility functions."""

from ddt import ddt, unpack, data

from kaos.utils.time_conversion import utc_to_unix

from .. import KaosTestCase

@ddt
class TestTimeConversions(KaosTestCase):
    """Tests time conversions utilities."""

    @unpack
    @data(('20181118T04:00:09.00', 1542513609),
          ('19700101T00:00:00.00', 0),
          ('19700101T00:00:12.00', 12),
          ('19700101T01:06:40.00', 4000),
          ('19700101T01:06:40.01', 4000.00),
          ('19700101T01:06:40.40', 4000.00),
          ('19700101T01:06:40.999', 4000.000),
          ('23000912T01:01:01.00', 10435741261))
    def test_utc_unix_valid(self, time_string, expected):
        """Tests that the UTC to UNIX time converter converts well formed strings correctly.

        Note:
            Data was generated using: https://www.epochconverter.com/
        """
        result = utc_to_unix(time_string)
        self.assertAlmostEqual(result, expected)

    @data('23000912T01:01:01.0000001',
          '23000912T01:01:011.00',
          '23000912T01:010:01.00',
          '23000912T101:01:01.00',
          '11000912T01:99:00.00',
          '17000100T01:00:00.00',
          '17000001T01:00:00.00',
          '17000140T01:00:00.00',
          '17000132T01:00:00.00',
          '17000132T99:00:00.00',
          '17000132T25:00:00.00',
          '17000132T24:00:00.00',
          '17000132T00:61:00.00',
          '17000132T00:60:00.00',
          '17000132T00:00:60.00',
          '17000132T00:00:61.00',
          '17001301T01:00:00.00',
          '17000140A01:00:00.00',
          '17000140T01:00:00:00')
    def test_utc_unix_invalid(self, time_string):
        """Tests that the UTC to UNIX time converter detects format and date errors."""
        with self.assertRaises(ValueError):
            utc_to_unix(time_string)

