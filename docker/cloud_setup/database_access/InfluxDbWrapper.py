#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Database Wrapper for a InfluxDB.

This class can write and read from a InfluxDB instance
"""

import os
import sys
import threading
import time

from distutils.util import strtobool

from helper.DateHelper import DateHelper
from influxdb import DataFrameClient
from database_access.OPCClient_Database import OPCClientDatabase

sys.path.insert(0, "..")

__version__ = '0.7'
__author__ = 'Sebastian Krahmer'


class InfluxDbWrapper(object):
    def __init__(self, host='localhost', port=8086, update_period=500, db_name="demonstrator_grid_protection"):
        self.UPDATE_PERIOD = int(os.environ.get("DATABASE_UPDATE_PERIOD", update_period))
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT", "False")))
        self.INFLUXDB_HOST = os.environ.get("INFLUXDB_HOST", host)
        self.INFLUXDB_PORT = os.environ.get("INFLUXDB_PORT", port)
        self.INFLUXDB_NAME = os.environ.get("INFLUXDB_NAME", db_name)

        # TimeLoop
        # https://medium.com/greedygame-engineering/an-elegant-way-to-run-periodic-tasks-in-python-61b7c477b679
        self.ticker = threading.Event()

        # DB related stuff
        self._db_user = 'root'
        self._db_password = 'n5geh2019'
        self._db_protocol = 'line'
        self.db_client = None

        # OPC Client
        self.opc_client = None

        self._terminated = False

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful init")

    def _init_OPCUA(self):
        if self.opc_client:
            self._del_OPCUA()

        self.opc_client = OPCClientDatabase("n5geh_opcua_client1", "n5geh2019")
        self.opc_client.start()

    def _del_OPCUA(self):
        self.opc_client.stop()

    def _finalize(self):
        self._del_OPCUA()

    def terminate(self):
        self._terminated = True

    def start(self):
        while not self._terminated:
            try:
                self.db_client = DataFrameClient(self.INFLUXDB_HOST, self.INFLUXDB_PORT, self._db_user, self._db_password, self.INFLUXDB_NAME)
                self.db_client.create_database(self.INFLUXDB_NAME)

                self._init_OPCUA()

                while not self._terminated and not self.ticker.wait(self.UPDATE_PERIOD/1000):
                    try:
                        # check is server node browsename still exists/is valid
                        browse_name = self.opc_client.client.get_server_node().get_browse_name()

                        df = self.opc_client.get_last_dataframe()
                        self.update_database(df)
                    except Exception as ex:
                        print(DateHelper.get_local_datetime(), self.__class__.__name__, " lost client connection")
                        print(ex)
                        break
            except Exception as ex:
                print(ex)

            finally:
                if not self._terminated:
                    print(DateHelper.get_local_datetime(), 'Restart ', self.__class__.__name__)
                    time.sleep(1)
        self._finalize()

    # region Database Update
    def update_database(self, dataframe):
        self.db_client.write_points(dataframe, self.INFLUXDB_NAME, protocol=self._db_protocol)
        if self.DEBUG_MODE_PRINT:
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
    # # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_CERT", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem")
    # # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem")
    # os.environ.setdefault("OPCUA_SERVER_DIR_NAME", "demo")
    # os.environ.setdefault("DEBUG_MODE_PRINT", "False")
    # os.environ.setdefault("DATABASE_UPDATE_PERIOD", "1000")        # in microsec
    # os.environ.setdefault("INFLUXDB_NAME", "demonstrator_grid_protection")
    ##################

    mInfluxDbWrapper = InfluxDbWrapper()
    mInfluxDbWrapper.start()
