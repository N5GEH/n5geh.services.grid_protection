#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Main for Cloud-GridProtection based on OPC-UA connection.

    1) starts OPCServer
    2) starts DataHandler
    3) starts MeasSim OPC Clients
"""
from distutils.util import strtobool

from CloudSetup.Protection.DataHandler import DataHandler
from CloudSetup.OPC_UA.Server.OPCServer import CustomServer
from CloudSetup.OPC_UA.Client.OPCClient_MeasSim import CustomClient
from multiprocessing import Process
import os


__version__ = '0.5'
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
    local = True
    if local:
        os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/freeopcua/server/")
    else:
        os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://0.0.0.0:4840/freeopcua/server/")
    os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    os.environ.setdefault("DEBUG_MODE_PRINT", "True")
    os.environ.setdefault("DEBUG_MODE_VAR_UPDATER", "True")
    os.environ.setdefault("UPDATE_PERIOD", "500000")              # in microsec
    os.environ.setdefault("TIMESTAMP_PRECISION", "10000")         # in microsec
    os.environ.setdefault("MAX_FAULTY_STATES", "5")
    os.environ.setdefault("NOMINAL_CURRENT", "275")
    os.environ.setdefault("CURRENT_EPS", "0.05")
    os.environ.setdefault("TOPOLOGY_PATH", "/CloudSetup/Topology/TopologyFile_demonstrator.json")
    os.environ.setdefault("PF_INPUT_PATH", "/CloudSetup/PFInputFiles/demonstrator_setup.txt")

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

    # setup OPC Server
    mServer = CustomServer()
    mServer.start()

    # start DataHandler and pass topo_path of TopologyData
    topo_path = os.environ.get("TOPOLOGY_PATH")
    mDataHandler = DataHandler(topo_path)
    mDataHandler.start()

    # setup meas devices as OPC Client
    if bool(strtobool(os.environ.get("DEBUG_MODE_VAR_UPDATER"))):
        meas_device_tags = ["RES"]
        for tag in meas_device_tags:
            mClient_MeasSim = CustomClient(tag)
            mClient_MeasSim.start()
            # meas_devices.append(mClient_MeasSim)
        # runInParallel(meas_devices[0].start(), meas_devices[1].start())
