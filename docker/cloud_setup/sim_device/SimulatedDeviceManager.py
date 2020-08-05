#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-client class for SimulationDevices.

This class setups a new instance of OPCClient_SimulatedDevice.
This class is used as Measurement device equivalent and updates value of vars via VarUpdater within a loop specified by
AUTO_VAR_UPDATER_xxx variables.
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
from opcua import ua
from opcua.ua import DataValue
from sim_device.OPCClient_SimulatedDevice import OPCClientSimulatedDevice

sys.path.insert(0, "..")

__version__ = '0.7'
__author__ = 'Sebastian Krahmer'


class VarUpdater(Thread):
    def __init__(self, mvars, opc_client, start_threshold, period=500):
        super().__init__()

        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT", "False")))
        self.TIMESTAMP_PRECISION = int(os.environ.get("AUTO_VAR_UPDATER_TIMESTAMP_PRECISION"))
        self.PERIOD = int(os.environ.get("AUTO_VAR_UPDATER_UPDATE_PERIOD", period))
        self.TIME_STEPS_NO_ERROR = int(os.environ.get("AUTO_VAR_UPDATER_TIME_STEPS_NO_ERROR", "60"))
        self.TIME_STEPS_ERROR = int(os.environ.get("AUTO_VAR_UPDATER_TIME_STEPS_ERROR", "60"))

        self.ticker = threading.Event()
        self._terminated = False

        self.vars = mvars
        self.opc_client = opc_client
        self.threshold = start_threshold
        # self.count = self.vars.get_value()

    def stop(self):
        self._terminated = True

    def run(self):
        start_time = time.time_ns()
        while not self._terminated or len(self.vars) >= 1:
            if time.time_ns() > (start_time + self.threshold):
                print(DateHelper.get_local_datetime(), self.__class__.__name__, " started")
                self.run2()
                break

    def run2(self):
        count = 0
        t1 = 0
        t2 = 0

        while not self.ticker.wait(self.PERIOD / 1000) and not self._terminated:
            now = DateHelper.create_local_utc_datetime()

            values = []
            for var in self.vars:
                # add "noise" to dt in the range [0 TIMESTAMP_PRECISION]
                delta = random.random() * self.TIMESTAMP_PRECISION * 1000
                now_noised = now + datetime.timedelta(0, 0, delta)

                dv = DataValue()
                dv.SourceTimestamp = now
                # dv.SourceTimestamp = now_noised

                if "LAST_I_PH1_RES" in var.get_browse_name().Name:
                    dv.Value = ua.Variant(2 * sin(100 * pi * (t1 + t2)))
                else:
                    if "TRAFO_I_PH1_RES" in var.get_browse_name().Name:
                        dv.Value = ua.Variant((len(self.vars)-1) * 2 * sin(100 * pi * t1))
                    else:
                        dv.Value = ua.Variant(2 * sin(100 * pi * t1))
                values.append(dv)
                if self.DEBUG_MODE_PRINT:
                    print(self.__class__.__name__, dv.Value)

            self.opc_client.set_vars(self.vars, values)

            t1 = count / 1000
            # make deviation after 60 time steps
            if count > self.TIME_STEPS_NO_ERROR:
                t2 = count * 0.05 / 1000
            count += 1

            # reset after 120 time steps
            if count > self.TIME_STEPS_NO_ERROR + self.TIME_STEPS_ERROR:
                print(DateHelper.get_local_datetime(), self.__class__.__name__, " reset Var_Updater loop")
                count = 0
                t1 = 0
                t2 = 0

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " stopped")


class DeviceManager(object):
    def __init__(self, meas_device_tag="RES", auth_name=None, auth_password=None, start_threshold=5000,
                 server_endpoint="opc.tcp://0.0.0.0:4840/OPCUA/python_server/"):

        self.SERVER_ENDPOINT = os.environ.get("SERVER_ENDPOINT", server_endpoint)
        self.NAMESPACE = os.environ.get("NAMESPACE")
        self.ENABLE_CERTIFICATE = bool(strtobool(os.environ.get("ENABLE_CERTIFICATE")))
        self.CERTIFICATE_PATH_CLIENT_CERT = os.path.dirname(os.getcwd()) + os.environ.get(
            "CERTIFICATE_PATH_CLIENT_CERT")
        self.CERTIFICATE_PATH_CLIENT_PRIVATE_KEY = os.path.dirname(os.getcwd()) + os.environ.get(
            "CERTIFICATE_PATH_CLIENT_PRIVATE_KEY")
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT", "False")))

        self.START_THRESHOLD = int(os.environ.get("AUTO_VAR_UPDATER_START_THRESHOLD", start_threshold)) * 1000 * 1000   # conversion into ns
        self.OPCUA_DIR_NAME = os.environ.get("OPCUA_SERVER_DIR_NAME")

        self.meas_device_tag = meas_device_tag
        self.opc_client = None
        self.vup = None

        self._terminated = False

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful init")

    def _init_OPCUA(self):
        if self.opc_client:
            self._del_OPCUA()

        self.opc_client = OPCClientSimulatedDevice("n5geh_opcua_client2", "n5geh2020", self.SERVER_ENDPOINT)
        self.opc_client.start()

    def _del_OPCUA(self):
        self.opc_client.stop()

    def _finalize(self):
        self._del_OPCUA()
        self.vup.stop()

    def terminate(self):
        self._terminated = True

    def start(self):
        while not self._terminated:
            try:
                # start opc client
                self._init_OPCUA()

                # start AutoVarUpdater
                self.prepare_auto_updater()
                self.start_auto_updater()

                print(DateHelper.get_local_datetime(), self.__class__.__name__, " finished Start-Routine")

                # start server status request loop
                while not self._terminated:
                    try:
                        browse_name = self.opc_client.client.get_server_node().get_browse_name()
                        time.sleep(1)
                    except Exception as ex:
                        print(DateHelper.get_local_datetime(), self.__class__.__name__, 'lost connection to server:')
                        print(ex)
                        break

            except Exception as ex:
                print(ex)
            finally:
                if not self._terminated:
                    print(DateHelper.get_local_datetime(), 'Restart ', self.__class__.__name__)
                    time.sleep(1)
        self._finalize()

    # region autoUpdater
    def prepare_auto_updater(self):
        var_list = []

        for var in self.opc_client.get_server_vars(self.OPCUA_DIR_NAME):
            if self.meas_device_tag in var.get_browse_name().Name:
                var_list.append(var)
        self.opc_client.set_full_node_list(var_list)
        self.vup = VarUpdater(var_list, self.opc_client, self.START_THRESHOLD)

    def start_auto_updater(self):
        print(self.__class__.__name__, type(self.vup))
        self.vup.start()

        print(DateHelper.get_local_datetime(), self.__class__.__name__, "started Auto-VarUpdater")
    # endregion


if __name__ == "__main__":
    ##################
    # ### if using local (means not in Docker): uncomment this lines!
    # local = False  # if server is local or as Docker
    # if local:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/OPCUA/python_server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/OPCUA/python_server/")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    # os.environ.setdefault("ENABLE_CERTIFICATE", "False")
    # # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_CERT", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem")
    # # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem")
    # os.environ.setdefault("OPCUA_SERVER_DIR_NAME", "demo")
    # os.environ.setdefault("DEBUG_MODE_PRINT", "False")
    # os.environ.setdefault("AUTO_VAR_UPDATER_UPDATE_PERIOD", "14")        # in ms
    # os.environ.setdefault("AUTO_VAR_UPDATER_TIMESTAMP_PRECISION", "10")   # in ms
    # os.environ.setdefault("AUTO_VAR_UPDATER_START_THRESHOLD", "5000")     # in ms
    # os.environ.setdefault("AUTO_VAR_UPDATER_TIME_STEPS_NO_ERROR", "60")
    # os.environ.setdefault("AUTO_VAR_UPDATER_TIME_STEPS_ERROR", "60")
    ##################

    meas_device_tags = ["RES"]
    for tag in meas_device_tags:
        mDeviceManager = DeviceManager(tag)
        mDeviceManager.start()
