#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Main for Cloud-GridProtection based on OPC-UA connection.

    1) starts OPCServer
    2) starts DataHandler
    3) starts MeasSim OPC Clients
"""
import logging

from cloud_setup.protection.GridProtectionManager import DataHandler
from cloud_setup.opc_ua.server.OPCServer import CustomServer
from sim_device.SimulatedDeviceManager import DeviceManager
from multiprocessing import Process
import os


__version__ = '0.6'
__author__ = 'Sebastian Krahmer'

from database_access.InfluxDbWrapper import InfluxDbWrapper


def runInParallel(*fns):
    proc = []
    for fn in fns:
        p = Process(target=fn)
        p.start()
        proc.append(p)
    for p in proc:
        p.join()


if __name__ == "__main__":
    # optional: setup logging
    logging.basicConfig(level=logging.WARN)
    # logger = logging.getLogger("opcua.address_space")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.internal_server")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.binary_server_asyncio")
    # logger.setLevel(logging.DEBUG)
    # logger = logging.getLogger("opcua.uaprocessor")
    # logger.setLevel(logging.DEBUG)

    local = True
    if local:
        os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/OPCUA/python_server/")
    else:
        os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://0.0.0.0:4840/OPCUA/python_server/")
    os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    os.environ.setdefault("SERVER_NAME", "N5GEH_FreeOpcUa_Python_Server")
    os.environ.setdefault("ENABLE_CERTIFICATE", "False")
    os.environ.setdefault("CERTIFICATE_PATH_SERVER_CERT", "/cloud_setup/opc_ua/certificates/n5geh_opcua_server_cert.pem")
    os.environ.setdefault("CERTIFICATE_PATH_SERVER_PRIVATE_KEY", "/cloud_setup/opc_ua/certificates/n5geh_opcua_server_private_key.pem")
    os.environ.setdefault("CERTIFICATE_PATH_CLIENT_CERT", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem")
    os.environ.setdefault("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem")
    os.environ.setdefault("OPCUA_SERVER_DIR_NAME", "demo")
    os.environ.setdefault("TOPOLOGY_PATH", "/cloud_setup/data/topology/TopologyFile_demonstrator.json")
    os.environ.setdefault("DEVICE_PATH", "/cloud_setup/data/device_config/Setup_demonstrator.txt")

    os.environ.setdefault("THREE_PHASE_CALCULATION", "False")
    os.environ.setdefault("UPDATE_PERIOD", "50")              # in ms
    os.environ.setdefault("TIMESTAMP_PRECISION", "10")         # in ms
    os.environ.setdefault("MAX_FAULTY_STATES", "5")
    os.environ.setdefault("NOMINAL_CURRENT", "2")
    os.environ.setdefault("CURRENT_EPS", "0.05")

    os.environ.setdefault("AUTO_VAR_UPDATER_UPDATE_PERIOD", "100")        # in ms
    os.environ.setdefault("AUTO_VAR_UPDATER_TIMESTAMP_PRECISION", "10")   # in ms
    os.environ.setdefault("AUTO_VAR_UPDATER_START_THRESHOLD", "5000")     # in ms
    os.environ.setdefault("AUTO_VAR_UPDATER_TIME_STEPS_NO_ERROR", "60")
    os.environ.setdefault("AUTO_VAR_UPDATER_TIME_STEPS_ERROR", "60")

    os.environ.setdefault("INFLUXDB_HOST", "ubuntu5g")
    os.environ.setdefault("INFLUXDB_PORT", "8086")
    os.environ.setdefault("DATABASE_UPDATE_PERIOD", "1000")  # in ms

    os.environ.setdefault("DEBUG_MODE_PRINT", "True")

    # setup OPC server
    mServer = CustomServer()
    mServer.start()

    # start DataHandler and pass topo_path of TopologyData
    topo_path = os.environ.get("TOPOLOGY_PATH")
    opcua_dir_name = os.environ.get("OPCUA_SERVER_DIR_NAME")
    mDataHandler = DataHandler(topo_path, opcua_dir_name)
    mDataHandler.start()

    # setup meas devices as OPC client
    meas_device_tags = ["RES"]
    for tag in meas_device_tags:
        mClient_MeasSim = DeviceManager(tag, "n5geh_opcua_client2", "n5geh2020")
        mClient_MeasSim.start()

    # # setup influxDb wrapper
    #     mInfluxDbWrapper = InfluxDbWrapper()
    #     mInfluxDbWrapper.start()
