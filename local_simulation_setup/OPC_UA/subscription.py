#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

import UC2_grid_protection.SimulationSetup.OPC_UA.mconfig as config


class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """
    def __init__(self, subscriber="server", meas_data_list=[]):
        self.subscriber = subscriber
        self.md_list = meas_data_list
        self.counter = 0

    def datachange_notification(self, node, val, data):
        if self.subscriber == "client":
            for md in self.md_list:
                if node.nodeid == md.nodeid:
                    md.update_data(data.monitored_item.Value.SourceTimestamp, val)
            if config.DEBUG_MODE:
                # print("New data change event:", node, val, "@", data.monitored_item.Value.SourceTimestamp)
                pass
        else:
            pass

    def event_notification(self, event):
        if config.DEBUG_MODE:
            print("Python: New event", event)
        else:
            pass
