#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Main for Cloud-GridProtection based on OPC-UA connection.

    1) starts OPCServer
    2) starts DataHandler
    3) starts MeasSim OPC Clients
"""
import logging
from distutils.util import strtobool

from cloud_setup.protection.DataHandler import DataHandler
from cloud_setup.opc_ua.server.OPCServer import CustomServer
from cloud_setup.opc_ua.client.OPCClient_SimDevice import OPCClientSimDevice
from multiprocessing import Process
import os


__version__ = '0.6'
__author__ = 'Sebastian Krahmer'


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
    os.environ.setdefault("DEBUG_MODE_PRINT", "True")
    os.environ.setdefault("UPDATE_PERIOD", "500000")              # in microsec
    os.environ.setdefault("TIMESTAMP_PRECISION", "10000")         # in microsec
    os.environ.setdefault("MAX_FAULTY_STATES", "5")
    os.environ.setdefault("NOMINAL_CURRENT", "275")
    os.environ.setdefault("CURRENT_EPS", "0.05")
    os.environ.setdefault("OPCUA_SERVER_DIR_NAME", "default_demonstrator")
    os.environ.setdefault("TOPOLOGY_PATH", "/cloud_setup/topology/TopologyFile_demonstrator.json")
    os.environ.setdefault("PF_INPUT_PATH", "/cloud_setup/device_config/demonstrator_setup.txt")
    os.environ.setdefault("DATABASE_UPDATE_PERIOD", "50000")  # in microsec

    # config.DEBUG_MODE_PRINT = "True"
    # config.DEBUG_MODE_VAR_UPDATER = "True"
    # config.SERVER_ENDPOINT = "opc.tcp://0.0.0.0:4840/freeopcua/server/"   # admin@hostname # 0.0.0.0 instead of localhost from outside
    # config.NAMESPACE = "https://n5geh.de"
    # # config.SERVER_ENDPOINT = "opc.tcp://ubuntu5g:4840/"
    # # config.NAMESPACE = "http://opcfoundation.org/UA/"

    # config.MAX_ARCHIVES = 20
    # config.MAX_FAULTY_STATES = 5
    # config.TIMESTAMP_PRECISION = 10000      # in microsec
    # config.UPDATE_PERIOD = 500000           # in microsec

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
        mClient_MeasSim = OPCClientSimDevice(tag, "n5geh_opcua_client2", "n5geh2020")
        mClient_MeasSim.start()
        # meas_devices.append(mClient_MeasSim)
    # runInParallel(meas_devices[0].start(), meas_devices[1].start())
