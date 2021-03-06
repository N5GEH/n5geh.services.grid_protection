#  Copyright (c) 2019.
#  Author: Sebastian Krahmer
import os
from distutils.util import strtobool

__version__ = '0.5'
__author__ = 'Sebastian Krahmer'


class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """
    def __init__(self, target_for_update, subscriber="client"):
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT")))
        self.mclass = target_for_update
        self.subscriber = subscriber

    def datachange_notification(self, node, val, data):
        self.mclass.update_data(node, data.monitored_item.Value.SourceTimestamp, val)

        # if self.DEBUG_MODE_PRINT:
            # print("New data change event:", node, val, "@", data.monitored_item.Value.SourceTimestamp)
            # pass

    def event_notification(self, event):
        if self.DEBUG_MODE_PRINT:
            print("New Event: ", event)
        else:
            pass

    def status_change_notification(self, status):
        if self.DEBUG_MODE_PRINT:
            print("New Status: ", status)
        else:
            pass
