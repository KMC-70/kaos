import datetime

def UTC_to_Linux():
    dt = datetime.datetime.strptime\
        ('20181010T20:10:05.123', '%Y%m%dT%H:%M:%S.%f')
    ut = dt.timestamp()

    return ut
