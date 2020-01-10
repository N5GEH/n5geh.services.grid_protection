#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is a simple NTP-client.

This module requests the actual time from a ntp server and format to datetime string.
    Methods:
            getNTPDateTime(server_adress)
"""
import datetime
import ntplib

def getNTPDateTime(server):
    try:
        ntpDate = None
        client = ntplib.NTPClient()
        response = client.request(server, version=3)
        ntpDate = response.tx_time
        # print(ntpDate)
        # print(response.offset)
    except Exception as e:
        print(e)
    print(datetime.datetime.fromtimestamp(ntpDate).strftime("%Y-%m-%d %H:%M:%S.%f"))
    return datetime.datetime.fromtimestamp(ntpDate).strftime("%Y-%m-%d %H:%M:%S.%f")


if __name__ == "__main__":
    getNTPDateTime('ubuntu5g.etieeh.loc')
