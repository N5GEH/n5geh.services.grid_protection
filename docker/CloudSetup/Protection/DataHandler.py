#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Data handler.

This module collects all incoming (subscribed) data, which is relevant in term of the chosen topology file.
After collecting at least one data point from each Meas device, the "FaultAssessment" DiffCore is called.
    Methods:
            register_devices(device_config_path)
            update_topology(topo_path)
"""
import os
from threading import Thread

import pandas as pd
import datetime
from distutils.util import strtobool
from CloudSetup.Protection.DataSource import TopologyData
from CloudSetup.Protection.DataSource import CustomVar
from CloudSetup.Protection.DiffCore import DiffCore
from CloudSetup.OPC_UA.Client.OPCClient import CustomClient

import time

from Protection import settings

__version__ = '0.5'
__author__ = 'Sebastian Krahmer'


class DataHandler(object):
    def __init__(self, topology_path):
        """
            Args:
                topology_path (String): path of TopologyFile.json
        """
        self.SERVER_ENDPOINT = os.environ.get("SERVER_ENDPOINT")
        self.DEBUG_MODE_VAR_UPDATER = bool(strtobool(os.environ.get("DEBUG_MODE_VAR_UPDATER")))
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT")))
        self.TIMESTAMP_PRECISION = int(os.environ.get("TIMESTAMP_PRECISION"))
        self.PF_INPUT_PATH = os.environ.get("PF_INPUT_PATH")

        self.opc_client = CustomClient(self.SERVER_ENDPOINT)
        self.opc_client.start()
        self.topo_path = topology_path
        self.topo_data = None

        self.slack_ph1 = None
        self.slack_ph2 = None
        self.slack_ph3 = None
        self.Iph1_nodes_list = []   # CustomVars related to I-measurement in phase 1 (will used only for Diff-Sum); (PF: RES-Variable, read only)
        self.Iph2_nodes_list = []
        self.Iph3_nodes_list = []
        self.ctrl_nodes_list = []   # CustomVars related to actuators (will used only for feedback-control); (PF: CTRL-Variable, control only)
        self.misc_nodes_list = []   # CustomVars not directly related to grid protection (mostly status vars and vars providing additional infos); (PF: RES-Variable which contain not to I-measurement + PF intern simulation vars)

        self.df_ph1 = pd.DataFrame()          # dataframe for phase 1 to pass to fault_assessment
        self.df_ph2 = pd.DataFrame()
        self.df_ph3 = pd.DataFrame()

        settings.init()

    def start(self):
        # Registration of vars at server
        self.register_devices(os.path.dirname(os.getcwd()) + self.PF_INPUT_PATH)

        # Set Topology used for grid protection
        self.update_topology(os.path.dirname(os.getcwd()) + self.topo_path)

        # Set start values for controllable nodes
        self.set_start_values_for_ctrls()

    def register_devices(self, device_config_path):
        self.opc_client.register_variables_to_server(device_config_path)

    def update_topology(self, path):
        # stop subscription
        self.opc_client.unsubscribe()

        # get at server registered vars allocated as CustomVar
        server_vars = self.get_customized_server_vars()

        # get new topology
        self.clear_topo_data()
        self.topo_data = TopologyData(path)

        # cluster topology nodes into lists (current, ctrl and misc) and assign the appropriate CustomVar
        for topo_opctag, topo_browsename in self.topo_data.get_itempairs():
            for var in server_vars:
                if var.opctag == topo_opctag:
                    if "_I_" in topo_opctag and "RES" in topo_opctag:

                        # ## separate nodes into groups for each phase
                        if "PH1" in topo_opctag:
                            self.Iph1_nodes_list.append(var)
                            if "slack" in topo_browsename.lower():  # find slack node for each phase and
                                self.slack_ph1 = var                # assign the appropriate CustomVar
                        elif "PH2" in topo_opctag:
                            self.Iph2_nodes_list.append(var)
                            if "slack" in topo_browsename.lower():
                                self.slack_ph2 = var
                        elif "PH3" in topo_opctag:
                            self.Iph3_nodes_list.append(var)
                            if "slack" in topo_browsename.lower():
                                self.slack_ph3 = var
                    elif "CTRL" in topo_opctag:
                        self.ctrl_nodes_list.append(var)
                    else:
                        self.misc_nodes_list.append(var)
                    break
        # ## update OPC-Client and start subscription again
        self.update_subscription_opc_client()

        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful updated topology")

    def get_customized_server_vars(self):
        all_observed_opc_nodes = self.opc_client.get_server_vars()
        mvars = []
        for var in all_observed_opc_nodes:
            opctag = var.get_browse_name().Name
            if 'PH1' in opctag:
                mvars.append(CustomVar(opctag, var.nodeid, 1))
            elif 'PH2' in opctag:
                mvars.append(CustomVar(opctag, var.nodeid, 2))
            elif 'PH3' in opctag:
                mvars.append(CustomVar(opctag, var.nodeid, 3))
            else:
                mvars.append(CustomVar(opctag, var.nodeid))
        return mvars

    def update_subscription_opc_client(self):
        self.opc_client.make_subscription(self, self.Iph1_nodes_list + self.Iph2_nodes_list + self.Iph3_nodes_list +
                                          self.ctrl_nodes_list + self.misc_nodes_list)

    def clear_topo_data(self):
        self.slack_ph1 = None
        self.slack_ph2 = None
        self.slack_ph3 = None
        self.Iph1_nodes_list = []
        self.Iph2_nodes_list = []
        self.Iph3_nodes_list = []
        self.ctrl_nodes_list = []
        self.misc_nodes_list = []

    def update_data(self, nodeid, datetime_source, val):
        for var in (self.Iph1_nodes_list + self.Iph2_nodes_list + self.Iph3_nodes_list):
            if var.nodeid == nodeid:
                # print(datetime_source)
                ts = self.round_time(datetime_source, self.TIMESTAMP_PRECISION)
                # print(ts)
                # ts = self.format_datetime(datetime_source)
                if var.opctag == self.slack_ph1.opctag or var.opctag == self.slack_ph2.opctag or var.opctag == self.slack_ph3.opctag:
                    val = -val  # IMPORTANT: slack counts in negative manner

                if var.phase == 1:
                    self.df_ph1.loc[ts, var.opctag] = val
                    if self.DEBUG_MODE_PRINT:
                        print(self.df_ph1)
                elif var.phase == 2:
                    self.df_ph2.loc[ts, var.opctag] = val
                    if self.DEBUG_MODE_PRINT:
                        print(self.df_ph2)
                elif var.phase == 3:
                    self.df_ph3.loc[ts, var.opctag] = val
                    if self.DEBUG_MODE_PRINT:
                        print(self.df_ph3)

                if self.DEBUG_MODE_PRINT:
                    print(self.__class__.__name__, " successful updated data")
                break

        start = time.time_ns()                  # in ns
        if self.check_data_queue_for_completeness():
            dc = DiffCore(self.opc_client, self.ctrl_nodes_list, self.misc_nodes_list, self.df_ph1, self.df_ph2, self.df_ph3)
            dc.start()
            self.clear_meas_data()
        end = time.time_ns()                    # in ns

        if self.DEBUG_MODE_PRINT:
            print(str((end-start) / (1000 * 1000)) + " ms")  # in ms

    # def format_datetime(self, datetime):
    #     ts = pd.to_datetime(datetime, format="%Y-%m-%d-%H:%M:%S.%f")
    #     ts.round('100ms')    # round to 10ms
    #     return ts

    def round_time(self, dt=None, time_precision=10000, to='average'):
        """
        Round a datetime object to a multiple of a timedelta
        dt : datetime.datetime object, default now.
        time_precision : precision of time resolution, default 20.000 microseconds (20ms).
        based partly on:  http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python
        """
        # ## get source timestamp and round to defined precision
        if dt is None:
            dt = datetime.datetime.now()

        microseconds = (dt - dt.min).microseconds
        rounding_up = (microseconds + time_precision / 2) // time_precision * time_precision
        rounding_down = (microseconds - time_precision / 2) // time_precision * time_precision
        if to == 'up':
            delta = rounding_up - microseconds
        elif to == 'down':
            delta = rounding_down - microseconds
        else:
            if abs(rounding_up - microseconds) < abs(microseconds - rounding_down):
                delta = rounding_up - microseconds
            else:
                delta = rounding_down - microseconds
        return dt + datetime.timedelta(0, 0, delta)  # rounding-microseconds

    def check_data_queue_for_completeness(self):
        # drops all rows where not all columns filled with values != NaN and check if length is
        df_ph1 = self.df_ph1.dropna()
        df_ph2 = self.df_ph2.dropna()
        df_ph3 = self.df_ph3.dropna()
        if len(df_ph1.columns) == len(self.Iph1_nodes_list) and len(df_ph1.index) >= 1 \
                and len(df_ph2.columns) == len(self.Iph2_nodes_list) and len(df_ph2.index) >= 1 \
                and len(df_ph3.columns) == len(self.Iph3_nodes_list) and len(df_ph3.index) >= 1:
            self.df_ph1.dropna(inplace=True)    # drops all rows where not all columns filled with values != NaN
            self.df_ph2.dropna(inplace=True)
            self.df_ph3.dropna(inplace=True)
            return True
        return False

    def clear_meas_data(self):
        self.df_ph1 = pd.DataFrame()
        self.df_ph2 = pd.DataFrame()
        self.df_ph3 = pd.DataFrame()

    def set_start_values_for_ctrls(self):
        # set start value of PRED_CTRL to 1000%
        ctrls = []
        values = []
        for ctrl in self.ctrl_nodes_list:
            if "PRED_CTRL" in ctrl.opctag:
                ctrls.append(ctrl)
                values.append(1000)
        self.opc_client.set_vars(ctrls, values)


if __name__ == "__main__":
    ##################
    # if using local (means not in Docker)
    # local = False   # if Server is local or as Docker
    # if local:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/freeopcua/server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/freeopcua/server/")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    # os.environ.setdefault("DEBUG_MODE_PRINT", "True")
    # os.environ.setdefault("DEBUG_MODE_VAR_UPDATER", "True")
    # os.environ.setdefault("UPDATE_PERIOD", "500000")        # in microsec
    # os.environ.setdefault("TIMESTAMP_PRECISION", "10000")   # in microsec
    # os.environ.setdefault("MAX_FAULTY_STATES", "5")
    # os.environ.setdefault("NOMINAL_CURRENT", "275")
    # os.environ.setdefault("CURRENT_EPS", "0.05")
    # os.environ.setdefault("TOPOLOGY_PATH", "/Topology/TopologyFile_demonstrator.json")
    # os.environ.setdefault("PF_INPUT_PATH", "/PFInputFiles/demonstrator_setup.txt")
    ##################

    topo_path = (os.path.dirname(os.getcwd()) + os.environ.get("TOPOLOGY_PATH"))
    print(os.path.dirname(os.getcwd()))
    print(topo_path)
    mDataHandler = DataHandler(topo_path)
    mDataHandler.start()
