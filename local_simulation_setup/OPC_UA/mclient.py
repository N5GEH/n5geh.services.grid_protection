#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

import sys
from opcua import ua, Client
from UC2_grid_protection.SimulationSetup.OPC_UA.subscription import SubHandler
import UC2_grid_protection.SimulationSetup.OPC_UA.mconfig as config
import datetime
sys.path.insert(0, "..")


class CustomClient(object):
    def __init__(self, data_point_list=None):
        self.client = Client(config.SERVER_ENDPOINT)    # ## connect using a user
        self.data_point_list = data_point_list
        self.pf_vars = []

        print(self.__class__.__name__, " successful init")

    def start(self):
        self.client.connect()

        # ## Now getting a variable node using its browse path
        root = self.client.get_root_node()       # objects = client.get_objects_node()
        uri = config.NAMESPACE
        idx = self.client.get_namespace_index(uri)

        # ## Server intern variables
        handler = SubHandler("client")

        # ## Object "ServerStuff": contains only server internal variables for testing
        # sub1 = self.client.create_subscription(500, handler)    # ## subscription interval: 1 ms
        # mvar1 = root.get_child(["0:Objects", "{}:ServerStuff".format(idx), "{}:mServerOnlineTime".format(idx)])
        # mvar2 = root.get_child(["0:Objects", "{}:ServerStuff".format(idx), "{}:mServerOnlineTime2".format(idx)])
        # sub1.subscribe_data_change([mvar1, mvar2])

        # ## Object "PF": contains server external variables from PowerFactory grid simulation
        handler = SubHandler("client", self.data_point_list)
        sub2 = self.client.create_subscription(1, handler)      # ## subscription interval: 1 ms
        obj = root.get_child(["0:Objects", "{}:PF".format(idx)])
        self.pf_vars = obj.get_variables()                      # ## pf_vars is type Node
        sub2.subscribe_data_change(self.pf_vars)                # ## Subscription Variant 1
        # for var in self.pf_vars:                              # ## Subscription Variant 2
        #     sub2.subscribe_data_change(var)

        print(self.__class__.__name__, " successful started")
        
    def stop(self):
        self.client.disconnect()
        print(self.__class__.__name__, " successful stopped")

    def set_vars(self, ctrl_list, value_list):
        i = 0
        for ctrl in ctrl_list:
            for var in self.pf_vars:
                if var.nodeid == ctrl.nodeid:
                    # dv = ua.Variant(value_list[ctrl_list.index(ctrl)], ua.VariantType.Int16)
                    # dv = ua.DataValue(ua.Variant(value_list[ctrl_list.index(ctrl)], variantType))
                    # dv.SourceTimestamp = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
                    # dv.ServerTimestamp = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
                    variant_type = var.get_data_value().Value.VariantType
                    var.set_value(value_list[i], variant_type)
                    break
            i += 1


if __name__ == "__main__":
    client = CustomClient()
    client.start()
