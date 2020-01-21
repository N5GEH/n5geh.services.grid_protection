#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Date helper.

This module helps to create and transform datetime.
"""

import datetime
from dateutil import tz


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
