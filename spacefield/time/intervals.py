from datetime import datetime, timezone


J2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
def julian_centuries_interval(t: datetime):
    """
    Calculates T as the interval in Julian centuries (of 36525 days)
    from the standard epoch.

    :param t: a date
    :return: interval in Julian centuries
    """
    return days_interval(t) / 36525.0


def days_interval(t):
    """
    Calculate d as the interval in days from the standard epoch

    :param t: a date
    :return: interval in days
    """
    return (t - J2000).total_seconds() / 86400.0
