import datetime

def UTC_to_Linux(time_string):
    """This function takes a string input of the format '20181010T20:10:05.123' representing
    'YYYYMMDDTHH:MM:SS.MS' and converts it to a linux timestamp. Note: the domain of time_string
     should be between 19700101 and 20380119.
    """
    TIME_MIN = '19700101'
    TIME_MAX = '20380119'

    dt = datetime.datetime.strptime(time_string, '%Y%m%dT%H:%M:%S.%f')
    if (dt < datetime.datetime.strptime(TIME_MIN, '%Y%m%d') or
            dt > datetime.datetime.strptime(TIME_MAX, '%Y%m%d')):
        raise ValueError('time_string out of range. Make sure it is between %s and %s'
                         % (TIME_MIN, TIME_MAX))
        return None
    return dt.timestamp()

