#  Copyright (c) 2019.
#  Author: Sebastian Krahmer
"""This is the Main Routine module for Diff_Application based on OPC-UA connection.

1) starts OPC_server 2) starts OPC_client 3) starts Diff_Application
"""
import UC2_grid_protection.SimulationSetup.OPC_UA.mconfig as config
from UC2_grid_protection.SimulationSetup.OPC_UA.mserver import CustomServer
from UC2_grid_protection.SimulationSetup.OPC_UA.mclient import CustomClient
from UC2_grid_protection.SimulationSetup.Diff_Protection.DataSource import TopologyData
from UC2_grid_protection.SimulationSetup.Diff_Protection.DataSource import MeasurementData
from UC2_grid_protection.SimulationSetup.Diff_Protection.DiffCore import DiffCore
import os

__version__ = '0.2'
__author__ = 'Sebastian Krahmer'

if __name__ == "__main__":
    config.DEBUG_MODE = "True"
    config.SERVER_ENDPOINT = "opc.tcp://localhost:4840/freeopcua/server/" # ## 0.0.0.0 instead of localhost from outside
    config.NAMESPACE = "http://examples.freeopcua.github.io"
    config.MAX_ARCHIVES = 20
    config.MAX_FAULTY_STATES = 5
    config.TIMESTAMP_PRECISION = 20000          # ## in microsec
    # config.save()

    mserver = CustomServer()
    if mserver.start():  # ## starts server and return true if set up
        # ## get Topology Data from csv file
        dirpath = os.getcwd()
        td = TopologyData(dirpath + "/Diff_Protection/TopologyFile.json")
        # td = TopologyData('//etieeh.loc/ev/Projekte/AG-PlanungUndBetriebVonNetzen/Projekte/EVSG1705_TOZ_BMWi_5G/05_Bearbeiter_intern/Krahmer/Python/Diff_Protection_OPCbased/TopologyFile.csv')
        # td = TopologyData('//etieeh.loc/ev/Projekte/AG-PlanungUndBetriebVonNetzen/Projekte/EVSG1705_TOZ_BMWi_5G/05_Bearbeiter_intern/Krahmer/Python/Diff_Protection_OPCbased/TopologyFile.json')

        # ## create new MeasurementData(md) objects based on OPC vars and save in md_list
        md_list = []
        for var in mserver.vars:
            md_list.append(MeasurementData(var.opctag, var.nodeid, var.phase, config.TIMESTAMP_PRECISION, False))

        # ## init DiffCore with relevant topology and measurement data
        mdiffcore = DiffCore(td, md_list)

        # ## create subscription for all OPC vars and give callback to md objects via subscription.py
        mclient = CustomClient(mdiffcore.md_list + mdiffcore.ctrl_list + mdiffcore.misc_list)
        mclient.start()

        # ## start DiffCore Calculation
        mdiffcore.start(mclient)
