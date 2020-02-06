#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-client class for DataHandler.

This class is an child of OPCClient.CustomClient
This class setups a new OPC-client for a server with a address specified by os.environ.get("SERVER_ENDPOINT").
"""
import os
import sys

from helper.DateHelper import DateHelper
from opcua import ua
from distutils.util import strtobool
# from opcua.ua import DataValue

from cloud_setup.opc_ua.client.subscription import SubHandler
from opc_ua.client.OPCClient import CustomClient

sys.path.insert(0, "..")

__version__ = '0.6'
__author__ = 'Sebastian Krahmer'


def format_textfile(mlist):
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


def numbers_to_typestrings(arg):
    if arg == 2:
        return "Int16"
    elif arg == 4:
        return "Float"
    else:
        return None     # ua.VariantType.Variant


class OPCClientDataHandler(CustomClient):
    def __init__(self, auth_name=None, auth_password=None, server_endpoint="opc.tcp://0.0.0.0:4840/OPCUA/python_server/", client_request_timeout=4):
        # super

        self.NAMESPACE = os.environ.get("NAMESPACE")
        self.ENABLE_CERTIFICATE = bool(strtobool(os.environ.get("ENABLE_CERTIFICATE")))
        self.CERTIFICATE_PATH_CLIENT_CERT = os.path.dirname(os.getcwd()) + os.environ.get("CERTIFICATE_PATH_CLIENT_CERT")
        self.CERTIFICATE_PATH_CLIENT_PRIVATE_KEY = os.path.dirname(os.getcwd()) + os.environ.get("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY")
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT", "False")))

        super().__init__(server_endpoint, self.NAMESPACE, self.ENABLE_CERTIFICATE, self.CERTIFICATE_PATH_CLIENT_CERT,
                         self.CERTIFICATE_PATH_CLIENT_PRIVATE_KEY, auth_name, auth_password, self.DEBUG_MODE_PRINT)

        # custom
        self.subscribed_status_nodes = []
        self.subscription_status_nodes = None
        self.subscription_handle_status_nodes = None

        self.subscribed_meas_nodes = []
        self.subscription_meas_nodes = None
        self.subscription_handle_meas_nodes = None

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful init")

    def start(self):
        super().start()

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful connected")

    def stop(self):
        super().stop()

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful disconnected")

    # region subscription
    def make_subscription(self, target_object, dir_name, list_of_nodes_to_subscribe, are_status_nodes=False,
                          sub_interval=1):
        """
        Make a subscription for list of nodes and set some properties.
        :param target_object: object the datachange_notification of subscription is sent to
        :param dir_name: subfolder, which contains the requested nodes
        :param list_of_nodes_to_subscribe: list of nodes/customVars
        :param are_status_nodes: flag if requested subscription is only for status flags
        :param sub_interval: time interval the subscribed node is checked (in ms)
        """
        sub_handler = SubHandler(target_object)

        if are_status_nodes is True:
            self.subscription_status_nodes, self.subscription_handle_status_nodes, self.subscribed_status_nodes = \
                self._subscribe(dir_name, sub_handler, self.subscription_status_nodes, self.subscription_handle_status_nodes,
                                list_of_nodes_to_subscribe, self.subscribed_status_nodes, sub_interval)
        else:
            self.subscription_meas_nodes, self.subscription_handle_meas_nodes, self.subscribed_meas_nodes = \
                self._subscribe(dir_name, sub_handler, self.subscription_meas_nodes, self.subscription_handle_meas_nodes,
                                list_of_nodes_to_subscribe, self.subscribed_meas_nodes, sub_interval)

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful updates subscription")
    # endregion

    def set_vars(self, ctrl_list, value_list):
        super().set_vars(self.subscribed_meas_nodes + self.subscribed_status_nodes, ctrl_list, value_list)
