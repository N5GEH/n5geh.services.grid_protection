#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-client class for SimulationDevices.

This class is an child of OPCClient.CustomClient
This class setups a new OPC-client with for a server with a address specified by os.environ.get("SERVER_ENDPOINT").
This class is used as Measurement device equivalent and updates value of vars via VarUpdater.
"""
import datetime
import os
import random
import sys
import threading
from threading import Thread
import time
from distutils.util import strtobool
from math import sin, pi

from helper.DateHelper import DateHelper
from opc_ua.client.OPCClient import CustomClient
from opcua import ua
from opcua.ua import DataValue

sys.path.insert(0, "..")

__version__ = '0.6'
__author__ = 'Sebastian Krahmer'


class VarUpdater(Thread):
    def __init__(self, mvars, start_threshold, period=500):
        super().__init__()

        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT")))
        self.TIMESTAMP_PRECISION = int(os.environ.get("TIMESTAMP_PRECISION"))
        self.PERIOD = int(os.environ.get("UPDATE_PERIOD", period))

        self.ticker = threading.Event()
        self.stop_request = False

        self.vars = mvars
        self.threshold = start_threshold
        # self.count = self.vars.get_value()

    def stop(self):
        self.stop_request = True

    def run(self):
        start_time = time.time_ns()
        while not self.stop_request or len(self.vars) >= 1:
            if time.time_ns() > (start_time + self.threshold):
                self.run2()
                print(self.__class__.__name__, "SimDevice VarUpdater started")
                break

    def run2(self):
        count = 0
        t1 = 0
        t2 = 0

        while not self.ticker.wait(self.PERIOD / 1000) and not self.stop_request:
            # self.vars.set_value(self.count)

            now = DateHelper.create_local_utc_datetime()
            for var in self.vars:
                # add "noise" to dt in the range [0 TIMESTAMP_PRECISION]
                delta = random.random() * self.TIMESTAMP_PRECISION * 1000
                now_noised = now + datetime.timedelta(0, 0, delta)

                dv = DataValue()
                dv.SourceTimestamp = now
                # dv.SourceTimestamp = now_noised

                if "LAST_I_PH1_RES" in var.get_browse_name().Name:
                    dv.Value = ua.Variant(2*sin(100*pi*(t1+t2)))
                else:
                    if "TRAFO_I_PH1_RES" in var.get_browse_name().Name:
                        dv.Value = ua.Variant(2 * 2 * sin(100 * pi * t1))
                    else:
                        dv.Value = ua.Variant(2*sin(100*pi*t1))
                var.set_value(dv)
                if self.DEBUG_MODE_PRINT:
                    print(self.__class__.__name__, dv.Value)

            t1 = count / 1000
            # make deviation after 60 time steps
            if count > 60:
                t2 = count * 0.05 / 1000
            count += 1

            # reset after 120 time steps
            if count > 120:
                count = 0
                t1 = 0
                t2 = 0


class OPCClientSimDevice(CustomClient):
    def __init__(self, meas_device_tag="RES", auth_name=None, auth_password=None, start_threshold=5000,
                 server_endpoint="opc.tcp://0.0.0.0:4840/OPCUA/python_server/"):
        # super
        self.SERVER_ENDPOINT = os.environ.get("SERVER_ENDPOINT", server_endpoint)
        self.NAMESPACE = os.environ.get("NAMESPACE")
        self.ENABLE_CERTIFICATE = bool(strtobool(os.environ.get("ENABLE_CERTIFICATE")))
        self.CERTIFICATE_PATH_CLIENT_CERT = os.path.dirname(os.getcwd()) + os.environ.get(
            "CERTIFICATE_PATH_CLIENT_CERT")
        self.CERTIFICATE_PATH_CLIENT_PRIVATE_KEY = os.path.dirname(os.getcwd()) + os.environ.get(
            "CERTIFICATE_PATH_CLIENT_PRIVATE_KEY")
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT")))

        super().__init__(self.SERVER_ENDPOINT, self.NAMESPACE, self.ENABLE_CERTIFICATE, self.CERTIFICATE_PATH_CLIENT_CERT,
                         self.CERTIFICATE_PATH_CLIENT_PRIVATE_KEY, auth_name, auth_password, self.DEBUG_MODE_PRINT)

        # custom
        self.THRESHOLD = int(os.environ.get("START_THRESHOLD", start_threshold)) * 1000 * 1000   # conversion into ns
        self.OPCUA_DIR_NAME = os.environ.get("OPCUA_SERVER_DIR_NAME")

        self.meas_device_tag = meas_device_tag
        self.vup = None

        print(self.__class__.__name__, " successful init")

    def start(self):
        super().start()
        self.prepare_auto_updater()
        self.start_auto_updater()

        print(self.__class__.__name__, " successful connected")
        
    def stop(self):
        super().stop()
        self.vup.stop()

        print(self.__class__.__name__, " successful disconnected")

    # region autoUpdater
    def prepare_auto_updater(self):
        var_list = []

        for var in self.get_server_vars(self.OPCUA_DIR_NAME):
            if self.meas_device_tag in var.get_browse_name().Name and "CTRL" not in var.get_browse_name().Name:
                var_list.append(var)
        self.vup = VarUpdater(var_list, self.THRESHOLD)

    def start_auto_updater(self):
        print(self.__class__.__name__, type(self.vup))
        self.vup.start()

        print(self.__class__.__name__, "MeasSim started Auto-VarUpdater")
    # endregion


if __name__ == "__main__":
    ##################
    # ### if using local (means not in Docker): uncomment this lines!
    # local = True  # if server is local or as Docker
    # if local:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/OPCUA/python_server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/OPCUA/python_server/")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    # os.environ.setdefault("ENABLE_CERTIFICATE", "False")
    # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_CERT", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem")
    # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem")
    # os.environ.setdefault("OPCUA_SERVER_DIR_NAME", "demo")
    # os.environ.setdefault("DEBUG_MODE_PRINT", "True")
    # os.environ.setdefault("UPDATE_PERIOD", "100")        # in ms
    # os.environ.setdefault("TIMESTAMP_PRECISION", "10")   # in ms
    # os.environ.setdefault("START_THRESHOLD", "5000")     # in ms
    ##################

    meas_device_tags = ["RES"]
    for tag in meas_device_tags:
        mClient_SimDevice = OPCClientSimDevice(tag)
        mClient_SimDevice.start()
