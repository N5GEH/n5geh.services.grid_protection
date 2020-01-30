#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-client class for connection to a Database.

This class is an child of OPCClient.CustomClient
This class setups a new OPC-client with for a server with a address specified by os.environ.get("SERVER_ENDPOINT").
This class is used as Measurement device equivalent and updates value of vars via VarUpdater.
"""
import os
import sys
from distutils.util import strtobool
import pandas as pd
from helper.DateHelper import DateHelper


from opc_ua.client.OPCClient import CustomClient
from opc_ua.client.subscription import SubHandler

sys.path.insert(0, "..")

__version__ = '0.6'
__author__ = 'Sebastian Krahmer'


class OPCClientDatabase(CustomClient):
    def __init__(self, auth_name=None, auth_password=None, server_endpoint="opc.tcp://0.0.0.0:4840/OPCUA/python_server/"):
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
        self.OPCUA_DIR_NAME = os.environ.get("OPCUA_SERVER_DIR_NAME", 'default_demonstrator')

        self.node_dict = dict()

        self.subscribed_nodes = []
        self.subscription = None
        self.subscription_handle = None

        self.df = pd.DataFrame()

        print(self.__class__.__name__, " successful init")

    def start(self):
        # start opc client
        super().start()

        # get_all_observed_nodes have to requested before subscription # TimeoutError()
        all_observed_nodes = self.get_server_vars(self.OPCUA_DIR_NAME)
        for var in all_observed_nodes:
            opctag = var.get_browse_name().Name
            nodeid_identifier = str(var.nodeid.Identifier)
            self.node_dict.update({nodeid_identifier: opctag})

        # make subscription
        self.make_subscription(self.OPCUA_DIR_NAME, self.get_server_vars(self.OPCUA_DIR_NAME))

        print(self.__class__.__name__, " successful connected")
        
    def stop(self):
        super().stop()
        print(self.__class__.__name__, " successful disconnected")

    # region subscription
    def make_subscription(self, dir_name, list_of_nodes_to_subscribe, sub_interval=1):
        """
        Make a subscription for list of nodes
        :param dir_name: subfolder, which contains the requested nodes
        :param list_of_nodes_to_subscribe: list of nodes/customVars
        :param sub_interval: time interval the subscribed node is checked (in ms)
        """
        sub_handler = SubHandler(self)

        self.subscription, self.subscription_handle, self.subscribed_nodes = \
            self._subscribe(dir_name, sub_handler, self.subscription, self.subscription_handle,
                            list_of_nodes_to_subscribe, self.subscribed_nodes, sub_interval)

        print(self.__class__.__name__, " successful updates subscription")

    # subscription callback
    def update_data(self, node, datetime_source, val):
        browse_name = self.node_dict[str(node.nodeid.Identifier)]
        self.df.loc[datetime_source, browse_name] = val
    # endregion

    def get_last_dataframe(self):
        df = self.df
        self.reset_dataframe()
        return df

    def reset_dataframe(self):
        self.df = pd.DataFrame()

