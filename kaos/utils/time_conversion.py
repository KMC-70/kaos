"""This module contains all date/time related conversion code."""

import datetime
import calendar

def utc_to_unix(time_string):
    """Takes a string input of the format 'YYYYMMDDTHH:MM:SS.MS' and converts it to a UNIX
    time stamp.

    Args:
        time_string (str): String representation of UTC time in the stated format. Must be
                           greater 19700101.

    Returns:
        The UNIX time stamp representation of the input time string.

    Raises:
        ValueError: If the string is malformed or the date represented by the string is invalid
                    in the POSIX epoch.

    Note:
        This function returns the UNIX time stamps to second precision only.
    """

    date_time = datetime.datetime.strptime(time_string, '%Y%m%dT%H:%M:%S.%f')
    return calendar.timegm(date_time.utctimetuple())

