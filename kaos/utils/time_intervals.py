"""Helper functions for dealing with TimeInterval objects."""

from itertools import tee

from ..tuples import TimeInterval


# pylint: disable=invalid-name
def calculate_common_intervals_helper(intervals1, intervals2):
    """Helper function to calculate_common_intervals used to calculate the intersecting intervals
    between two lists of intervals.

    Args:
        intervals1 (list):  A list of TimeIntervals
        intervals2 (list):  A list of TimeIntervals

    Returns:
        A list of TimeIntervals common to both the supplied intervals.
    """
    common_intervals = []
    for interval1 in intervals1:
        for interval2 in intervals2:
            intersection = interval1.intersection(interval2)
            if intersection:
                common_intervals.append(intersection)

    return common_intervals
# pylint: enable=invalid-name


def calculate_common_intervals(intervals_list):
    """Calculates the common intervals between a list of interval lists.

    Args:
        intervals_list (list):  A list of TimeInterval lists.

    Return:
        A list of TimeIntervals that are common to each supplied TimeInterval list.
    """
    if len(intervals_list) == 1:
        return intervals_list[0]

    other_intervals = calculate_common_intervals(intervals_list[1:])
    return calculate_common_intervals_helper(intervals_list[0], other_intervals)


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

    Args:
        input_list (list of TimeInterval): list of time intervals to be fused.
        assume_sorted (boolean): Whether input list is sorted with respect to TimeInterval.start
                                 values. defaults to False.
    """
    if not assume_sorted:
        input_list.sort(key=lambda x: x.start)

    output_list = []
    fused_interval_start = None
    for i, j in pairwise(input_list):

        if j is not None and i.end == j.start:
            # We are in a fuse-able interval
            if fused_interval_start is None:
                # Update the start only at the beginning
                fused_interval_start = i.start

        else:
            # We are not in a fuse-able interval
            if fused_interval_start is not None:
                # Append the fused interval if we just exited a fuse-able interval
                output_list.append(TimeInterval(fused_interval_start, i.end))
                fused_interval_start = None
            else:
                # No neighbor case, just append
                output_list.append(TimeInterval(i.start, i.end))

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

