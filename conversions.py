import pytz


def to_london_time(python_dt):
    """return london timezone from python date object"""
    ldn_time = python_dt.astimezone(pytz.timezone("Europe/London"))
    return ldn_time
