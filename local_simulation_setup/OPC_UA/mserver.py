
#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

import sys
import time
from threading import Thread
from dataclasses import dataclass
from opcua import ua, Server
from UC2_grid_protection.SimulationSetup.OPC_UA.subscription import SubHandler
import UC2_grid_protection.SimulationSetup.OPC_UA.mconfig as config
sys.path.insert(0, "..")


def make_textfiles_compatible(mlist):
    result = []
    for i in mlist:
        a = i.replace('\t', ' ')
        b = a.replace('\n', ' ')
        c = b.replace(',0', ' ')
        d = c.replace(',', ' ')
        result.append(d)
    return result


def numbers_to_vartyps(arg):
    if arg == 2:
        return ua.VariantType.Int16
    elif arg == 4:
        return ua.VariantType.Float
    else:
        return None     # ua.VariantType.Variant


class VarUpdater(Thread):
    def __init__(self, mvars, period=1):
        Thread.__init__(self)
        self._stopev = False
        self.vars = mvars
        self.period = period
        for var in self.vars:
            self.count = var.get_value()

    def stop(self):
        self._stopev = True

    def run(self):
        while not self._stopev:
            time.sleep(self.period)
            self.count += 0.1
            for var in self.vars:
                var.set_value(self.count)


@dataclass
class OPCVariable:
    opctag: str
    nodeid: ua.NodeId
    phase: int = -1


class CustomServer(object):
    def __init__(self):
        self.vars = []
        self.server = Server()
        self.vup = None

    def start(self):
        # ## setup our server
        self.server.set_endpoint(config.SERVER_ENDPOINT)    # "opc.tcp://localhost:4840/freeopcua/server/"

        # ## setup our own namespace, not really necessary but should as spec
        uri = config.NAMESPACE  # "http://examples.freeopcua.github.io"
        idx = self.server.register_namespace(uri)

        # ## get Objects node, this is where we should put our nodes
        objects = self.server.get_objects_node()

        # ## populating our address space
        # ## Object "ServerStuff": contains only server internal variables for testing
        # mobj = objects.add_object(idx, "ServerStuff")
        # mServerOnlineTime = mobj.add_variable(idx, "mServerOnlineTime", ua.Variant(0, ua.VariantType.Float))
        # mServerOnlineTime2 = mobj.add_variable(idx, "mServerOnlineTime2", ua.Variant(100, ua.VariantType.Float))

        # ## Object "PF": contains server external variables from PowerFactory grid simulation
        mobj = objects.add_object(idx, "PF")

        # ## get tags from PF txt file (console output after Script "PrintOPCServerConfig) and add variables
        # mtagfile = open('PFInputFiles/PF_ExtMeas_OPCexample.txt', 'r')   # basic example for OPC from Digsilent
        mtagfile = open('PFInputFiles/PF_ExtMeas_GridProtection.txt', 'r')
        tags_pf_output = make_textfiles_compatible(mtagfile.readlines())

        # mvar_list = []
        for i in tags_pf_output:
            opctag, typ = i.split()
            opctag, typ = opctag.strip(), int(typ)

            mvar = mobj.add_variable(idx, opctag, ua.Variant(0, numbers_to_vartyps(typ)))
            mvar.set_writable()
            # mvar_list.append(mvar)

            if 'PH1' in opctag:
                self.vars.append(OPCVariable(opctag, mvar.nodeid, 1))
            elif 'PH2' in opctag:
                self.vars.append(OPCVariable(opctag, mvar.nodeid, 2))
            elif 'PH3' in opctag:
                self.vars.append(OPCVariable(opctag, mvar.nodeid, 3))
            else:
                self.vars.append(OPCVariable(opctag, mvar.nodeid))

        mtagfile.close()

        # self.vup = VarUpdater(mvar_list)
        # self.vup.start()
        # self.vup = VarUpdater([mServerOnlineTime, mServerOnlineTime2])
        # self.vup.start()

        # ## starting!
        self.server.start()

        # ## make server-side subscription
        handler = SubHandler("server")
        sub = self.server.create_subscription(1, handler)   # ## subscription interval: 1 ms
        handle = sub.subscribe_data_change(self.vars)       # ## Subscription Variant 1
        # for var in mvar_list:                             # ## Subscription Variant 2
        #     handle = sub.subscribe_data_change(var)

        print(self.__class__.__name__, " successful started")
        return True

    def stop(self):
        # ## close connection
        self.vup.stop()
        self.server.stop()
        print(self.__class__.__name__, " successful stopped")


if __name__ == "__main__":
    server = CustomServer()
    server.start()
