#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-Client class.

This class setups a new OPC-Client with for a server with a address specified by os.environ.get("SERVER_ENDPOINT").
This class is used as Measurement device equivalent and updates value of vars via VarUpdater.
"""
import datetime
import os
import random
import sys
from threading import Thread
import time
from distutils.util import strtobool
from opcua import Client, ua
from opcua.ua import DataValue

sys.path.insert(0, "..")

__version__ = '0.5'
__author__ = 'Sebastian Krahmer'


class VarUpdater(Thread):
    def __init__(self, mvars, start_threshold, period=500000):
        super().__init__()

        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT")))
        self.TIMESTAMP_PRECISION = int(os.environ.get("TIMESTAMP_PRECISION"))
        self.PERIOD = int(os.environ.get("UPDATE_PERIOD", period)) * 1000  # conversion into ns

        self._stopev = False
        self.vars = mvars
        self.threshold = start_threshold
        for var in self.vars:
            self.count = var.get_value()
            if self.DEBUG_MODE_PRINT:
                print(self.__class__.__name__, "MeasSim VarUpdater for: ", var)
        # self.count = self.vars.get_value()

    def stop(self):
        self._stopev = True

    def run(self):
        start_time = time.time_ns()
        while not self._stopev or len(self.vars) >= 1:
            if time.time_ns() > (start_time + self.threshold):
                self.run2()
                break

    def run2(self):
        next_update_time = time.time_ns() + self.PERIOD
        while not self._stopev:
            if (time.time_ns()) > next_update_time:
                next_update_time = next_update_time + self.PERIOD
                # time.sleep(self.period)
                self.count += 0.1
                if self.DEBUG_MODE_PRINT:
                    print(self.__class__.__name__, self.count)
                # self.vars.set_value(self.count)
                now = datetime.datetime.now()
                for var in self.vars:
                    # start = time.process_time_ns()
                    # print(start, var.get_browse_name().Name)
                    # var.set_value(self.count)

                    # add "noise" to dt in the range [0 TIMESTAMP_PRECISION]
                    delta = random.random() * self.TIMESTAMP_PRECISION
                    now_noised = now + datetime.timedelta(0, 0, delta)

                    dv = DataValue()
                    dv.SourceTimestamp = now_noised
                    dv.Value = ua.Variant(self.count)
                    var.set_value(dv)


class CustomClient(object):
    def __init__(self, meas_device_tag="RES", start_threshold=5000000, server_endpoint="opc.tcp://0.0.0.0:4840/freeopcua/server/"):

        self.SERVER_ENDPOINT = os.environ.get("SERVER_ENDPOINT", server_endpoint)
        self.NAMESPACE = os.environ.get("NAMESPACE")
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT")))
        self.THRESHOLD = int(os.environ.get("START_THRESHOLD", start_threshold)) * 1000   # conversion into ns

        self.client = Client(self.SERVER_ENDPOINT)
        self.meas_device_tag = meas_device_tag
        self.vup = None

        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, "MeasSim successful init")

    def start(self):
        self.client.connect()
        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, "MeasSim successful connected")
        self.prepare_auto_updater()
        self.start_auto_updater()

    def get_server_vars(self, child="PF"):
        # ## Now getting a variable node using its browse path
        root = self.client.get_root_node()  # objects = client.get_objects_node()
        uri = self.NAMESPACE
        idx = self.client.get_namespace_index(uri)

        obj = root.get_child(["0:Objects", ("{}:" + child).format(idx)])
        return obj.get_variables()
        
    def stop(self):
        self.client.disconnect()
        self.vup.stop()
        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, "MeasSim successful disconnected")

    def prepare_auto_updater(self):
        var_list = []

        for var in self.get_server_vars():
            if self.meas_device_tag in var.get_browse_name().Name and "CTRL" not in var.get_browse_name().Name:
                var_list.append(var)
        self.vup = VarUpdater(var_list, self.THRESHOLD)

    def start_auto_updater(self):
        print(self.__class__.__name__, type(self.vup))
        self.vup.start()

        print(self.__class__.__name__, "MeasSim started Auto-VarUpdater")


if __name__ == "__main__":
    ##################
    # ### if using local (means not in Docker): uncomment this lines!
    # local = False  # if Server is local or as Docker
    # if local:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/freeopcua/server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/freeopcua/server/")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    # os.environ.setdefault("DEBUG_MODE_PRINT", "True")
    # os.environ.setdefault("DEBUG_MODE_VAR_UPDATER", "True")
    # os.environ.setdefault("UPDATE_PERIOD", "500000")        # in microsec
    # os.environ.setdefault("TIMESTAMP_PRECISION", "10000")   # in microsec
    # os.environ.setdefault("START_THRESHOLD", "5000000")     # in microsec
    ##################

    if bool(strtobool(os.environ.get("DEBUG_MODE_VAR_UPDATER"))):
        meas_device_tags = ["RES"]
        for tag in meas_device_tags:
            mClient_MeasSim = CustomClient(tag)
            mClient_MeasSim.start()
