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
    def __init__(self, auth_name=None, auth_password=None, update_period=50000,
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
        self.OPCUA_DIR_NAME = os.environ.get("OPCUA_SERVER_DIR_NAME")
        self.UPDATE_PERIOD = os.environ.get("DATABASE_UPDATE_PERIOD", update_period)

        self.subscribed_nodes = []
        self.subscription = None
        self.subscription_handle = None

        self.df = pd.DataFrame()

        self.stop_request = False

        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful init")

    def start(self):
        # start opc client
        super().start()

        # make subscription
        self.make_subscription(self.OPCUA_DIR_NAME, self.get_server_vars(self.OPCUA_DIR_NAME))

        # start Database Update Process


        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful connected")
        
    def stop(self):
        super().stop()
        if self.DEBUG_MODE_PRINT:
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

        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful updates subscription")

    # subscription callback
    def update_data(self, node, datetime_source, val):
        self.df.loc[datetime_source, node.get_browsw_name().Name] = val
    # endregion

    # region Database Update
    def stop_database_update(self):
        self.stop_request = True

    def start_database_update(self,update_period):
        while not self.stop_request:
            pass
            # TODO make db update every update_period
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
    # os.environ.setdefault("ENABLE_CERTIFICATE", "True")
    # os.environ.setdefault("CERTIFICATE_PATH_SERVER_CERT", "/opc_ua/certificates/n5geh_opcua_server_cert.pem")
    # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_CERT", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem")
    # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem")
    # os.environ.setdefault("CERTIFICATE_PATH", "/opc_ua/certificates/")
    # os.environ.setdefault("DEBUG_MODE_PRINT", "True")
    # os.environ.setdefault("DATABASE_UPDATE_PERIOD", "50000")        # in microsec
    # os.environ.setdefault("TIMESTAMP_PRECISION", "10000")   # in microsec
    ##################


    mClient_Database = OPCClientDatabase()
    mClient_Database.start()
