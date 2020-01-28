#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Date helper.

This module helps to create and transform datetime.
"""

import datetime
from dateutil import tz
import pandas as pd


class DateHelper(object):

    @staticmethod
    def create_local_utc_datetime():
        return datetime.datetime.utcnow()

    @staticmethod
    def transform_timezone_to_local(dt):
        # now = datetime.datetime.utcnow()
        HERE = tz.tzlocal()
        UTC = tz.gettz('UTC')
        dt = dt.replace(tzinfo=UTC)
        dt = dt.astimezone(HERE)
        return dt

    @staticmethod
    def format_datetime(dt):
        ts = pd.to_datetime(dt, format="%Y-%m-%d-%H:%M:%S.%f")
        # ts.round('10ms')    # round to 10ms
        return ts

    @staticmethod
    def round_time(dt=None, time_precision=10, to='average'):
        """
        Round a datetime object to a multiple of a timedelta
        dt : datetime.datetime object, default now.
        time_precision : precision of time resolution, default 10 ms (10ms).
        based partly on:  http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python
        """
        tp = time_precision * 1000  # in microsecs
        # ## get source timestamp and round to defined precision
        if dt is None:
            dt = DateHelper.create_local_utc_datetime()

        microseconds = (dt - dt.min).microseconds
        rounding_up = (microseconds + tp / 2) // tp * tp
        rounding_down = (microseconds - tp / 2) // tp * tp
        if to == 'up':
            delta = rounding_up - microseconds
        elif to == 'down':
            delta = rounding_down - microseconds
        else:
            if abs(rounding_up - microseconds) < abs(microseconds - rounding_down):
                delta = rounding_up - microseconds
            else:
                delta = rounding_down - microseconds
        return dt + datetime.timedelta(0, 0, delta)  # rounding-microseconds
