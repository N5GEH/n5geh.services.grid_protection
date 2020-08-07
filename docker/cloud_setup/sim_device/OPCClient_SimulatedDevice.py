#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-client class for SimulatedDeviceManager.

This class is an child of OPCClient.CustomClient
This class setups a new OPC-client for a server with a address specified by os.environ.get("SERVER_ENDPOINT").
"""
import os
import sys

from helper.DateHelper import DateHelper
from distutils.util import strtobool

from opc_ua.client.OPCClient import CustomClient

sys.path.insert(0, "..")

__version__ = '0.7'
__author__ = 'Sebastian Krahmer'


class OPCClientSimulatedDevice(CustomClient):
    def __init__(self, auth_name=None, auth_password=None, server_endpoint="opc.tcp://0.0.0.0:4840/OPCUA/python_server/", client_request_timeout=4):
        # super

        self.NAMESPACE = os.environ.get("NAMESPACE")
        self.ENABLE_CERTIFICATE = bool(strtobool(os.environ.get("ENABLE_CERTIFICATE")))
        self.CERTIFICATE_PATH_CLIENT_CERT = os.path.dirname(os.getcwd()) + os.environ.get("CERTIFICATE_PATH_CLIENT_CERT", "not_specified")
        self.CERTIFICATE_PATH_CLIENT_PRIVATE_KEY = os.path.dirname(os.getcwd()) + os.environ.get("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY", "not_specified")
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT", "False")))

        super().__init__(server_endpoint, self.NAMESPACE, self.ENABLE_CERTIFICATE, self.CERTIFICATE_PATH_CLIENT_CERT,
                         self.CERTIFICATE_PATH_CLIENT_PRIVATE_KEY, auth_name, auth_password, self.DEBUG_MODE_PRINT)

        self.full_node_list = []

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful init")

    def start(self):
        super().start()

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful connected")

    def stop(self):
        super().stop()

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful disconnected")

    def set_full_node_list(self, full_node_list):
        self.full_node_list = full_node_list

    def set_vars(self, ctrl_list, value_list):
        super().set_vars(self.full_node_list, ctrl_list, value_list)
