"""Helper functions for dealing with lists of time intervals."""


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
