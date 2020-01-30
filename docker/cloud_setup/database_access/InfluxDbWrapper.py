#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Database Wrapper for a InfluxDB.

This class can write and read from a inlfuxDB instance
"""

import os
import sys
import threading

from distutils.util import strtobool

from influxdb import DataFrameClient
from database_access.OPCClient_Database import OPCClientDatabase

sys.path.insert(0, "..")

__version__ = '0.6'
__author__ = 'Sebastian Krahmer'


class InfluxDbWrapper(object):
    def __init__(self, host='localhost', port=8086, update_period=500):
        self.UPDATE_PERIOD = int(os.environ.get("DATABASE_UPDATE_PERIOD", update_period))
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT")))
        self.INFLUXDB_HOST = os.environ.get("INFLUXDB_HOST", host)
        self.INFLUXDB_PORT = os.environ.get("INFLUXDB_PORT", port)

        # TimeLoop
        # https://medium.com/greedygame-engineering/an-elegant-way-to-run-periodic-tasks-in-python-61b7c477b679
        self.ticker = threading.Event()
        self.stop_request = False

        # DB related stuff
        user = 'root'
        password = 'n5geh2019'
        self.dbname = 'demonstrator_grid_protection'
        self.protocol = 'line'

        self.db_client = DataFrameClient(self.INFLUXDB_HOST, self.INFLUXDB_PORT, user, password, self.dbname)
        self.db_client.create_database(self.dbname)

        # OPC Client
        self.opc_client = OPCClientDatabase()

        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful init")

    def start(self):
        self.opc_client.start()

        while not self.ticker.wait(self.UPDATE_PERIOD/1000):
            df = self.opc_client.get_last_dataframe()
            self.update_database(df)

    # region Database Update
    def stop_database_update(self):
        self.stop_request = True

    def update_database(self, dataframe):
        self.db_client.write_points(dataframe, self.dbname, protocol=self.protocol)
        print(dataframe)
    # endregion


if __name__ == "__main__":
    ##################
    # ### if using local (means not in Docker): uncomment this lines!
    # local = False  # if server is local or as Docker
    # if local:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/OPCUA/python_server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/OPCUA/python_server/")
    # os.environ.setdefault("INFLUXDB_HOST", "ubuntu5g")
    # # os.environ.setdefault("INFLUXDB_HOST", "141.30.194.142")
    # os.environ.setdefault("INFLUXDB_PORT", "8086")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    # os.environ.setdefault("ENABLE_CERTIFICATE", "False")
    # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_CERT", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem")
    # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem")
    # os.environ.setdefault("OPCUA_SERVER_DIR_NAME", "demo")
    # os.environ.setdefault("DEBUG_MODE_PRINT", "True")
    # os.environ.setdefault("DATABASE_UPDATE_PERIOD", "500")        # in microsec
    ##################

    mInfluxDbWrapper = InfluxDbWrapper()
    mInfluxDbWrapper.start()
