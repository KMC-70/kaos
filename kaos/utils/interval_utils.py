""" Utility functions to manage TimeInterval objects"""

from itertools import tee

from ..tuples import TimeInterval


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ... , (sn, None)
    from: https://docs.python.org/2/library/itertools.html
    """
    iterable.append(None)
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def fuse_neighbor_intervals(input_list, assume_sorted=False):
    """Merges neighboring TimeIntervals that share the same start/end time.
    example: [(0,100),(100,200),(300,400)] -> [(0,200),(300,400)]

    Assumptions:
        Intervals don't overlaps.
        Maximum of 2 intervals share any one border.
        For any interval, there is maximum of one neighbor.

    Args:
        input_list (list of TimeInterval): list of time intervals to be fused.
        assume_sorted (boolean): Whether input list is sorted with respect to TimeInterval.start
                                 values. defaults to False.
    """
    if not assume_sorted:
        input_list.sort(key=lambda x: x.start)

    output_list = []
    skip_next = False
    for i, j in pairwise(input_list):
        if skip_next is True:
            skip_next = False
            continue
        if j is not None and i[1] == j[0]:
            output_list.append(TimeInterval(i[0], j[1]))
            skip_next = True
        else:
            output_list.append(TimeInterval(i[0], i[1]))

    return output_list


def trim_poi_segments(interval_list, poi):
    """Adjusts list of intervals so that all intervals fit inside the poi

    Args:
      interval_list(list of TimeIntervals) = the interval to be trimmed
      poi(TimeInterval) = period of interest, reference for trimming

    Returns:
      List of TimeIntervals that fit inside the poi
    """
    ret_list = []
    for interval in interval_list:
        if (interval.start > poi.end) or (interval.end < poi.start):
            # Outside the input POI
            continue
        elif (interval.start < poi.end) and (interval.end > poi.end):
            ret_list.append(TimeInterval(interval.start, poi.end))
        elif (interval.end > poi.start) and (interval.start < poi.start):
            ret_list.append(TimeInterval(poi.start, interval.end))
        else:
            ret_list.append(TimeInterval(interval.start, interval.end))

    return ret_list
