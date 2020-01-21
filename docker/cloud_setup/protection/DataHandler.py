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

import pandas as pd
import time
from distutils.util import strtobool
from cloud_setup.protection.DataSource import TopologyData
from cloud_setup.protection.DataSource import CustomVar
from cloud_setup.protection.DiffCore import DiffCore
from cloud_setup.opc_ua.client.OPCClient_DataHandler import OPCClientDataHandler
from helper.DateHelper import DateHelper

from protection import settings

__version__ = '0.5'
__author__ = 'Sebastian Krahmer'


class DataHandler(object):
    def __init__(self, topology_path, dir_name):
        """
        :param topology_path (String): path of TopologyFile.json
        :param dir_name (String): name of subfolder to create; parent of all created nodes
        """
        self.SERVER_ENDPOINT = os.environ.get("SERVER_ENDPOINT")
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT")))
        self.TIMESTAMP_PRECISION = int(os.environ.get("TIMESTAMP_PRECISION"))
        self.PF_INPUT_PATH = os.environ.get("PF_INPUT_PATH")

        self.opc_client = OPCClientDataHandler("n5geh_opcua_client1", "n5geh2019", self.SERVER_ENDPOINT)

        self.topo_path = os.path.dirname(os.getcwd()) + topology_path
        self.topo_data = None
        self.server_dir_name = dir_name

        self.slack_ph1 = None
        self.slack_ph2 = None
        self.slack_ph3 = None
        self.Iph1_nodes_list = []   # CustomVars related to I-measurement in phase 1 (will used only for Diff-Sum); (PF: RES-Variable, read only)
        self.Iph2_nodes_list = []
        self.Iph3_nodes_list = []
        self.ctrl_nodes_list = []   # CustomVars related to actuators (will used only for feedback-control); (PF: CTRL-Variable, control only)
        self.other_meas_nodes_list = []     # CustomVars that are sensors and NOT related to I-measurement; (PF: RES-Variable which contain not to I-measurement)
        self.misc_nodes_list = []   # CustomVars not directly related to grid protection (mostly status vars and vars providing additional infos); (PF: PF intern simulation vars)

        self.df_ph1 = pd.DataFrame()          # dataframe for phase 1 to pass to fault_assessment
        self.df_ph2 = pd.DataFrame()
        self.df_ph3 = pd.DataFrame()

        settings.init()

    def _start_client(self):
        self.opc_client.start()

    def _stop_client(self):
        self.opc_client.stop()

    def start(self):
        # start opc client
        self._start_client()

        # Registration of vars at server
        self.register_devices(self.server_dir_name, os.path.dirname(os.getcwd()) + self.PF_INPUT_PATH)

        # Set topology used for grid protection
        self.set_meas_topology(self.topo_path, [], self.server_dir_name)

        # Set start values for controllable nodes
        self.set_start_values_for_ctrls()

        # Set status nodes used monitoring and topology/device updates
        self.set_status_flags(self.topo_path, [], self.server_dir_name)

    def register_devices(self, dir_name, device_config_path):
        self.opc_client.create_dir_on_server(dir_name)
        self.opc_client.register_variables_to_server(dir_name, device_config_path)
        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful register devices from file:" + device_config_path)

    def set_meas_topology(self, path, list_of_nodes_to_reset, dir_name):
        # get at server registered vars allocated as CustomVar
        server_vars = self.get_customized_server_vars(dir_name)

        # get new topology
        self.clear_topo_meas()
        self.topo_data = TopologyData(path)

        # cluster topology nodes into lists (current, ctrl and misc) and assign the appropriate CustomVar
        for topo_opctag, topo_browsename in self.topo_data.get_itempairs():
            for var in server_vars:
                if var.opctag == topo_opctag:
                    if "_I_" in topo_opctag and "RES" in topo_opctag:

                        # separate nodes into groups for each phase
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
                    elif "_I_" not in topo_opctag and "RES" in topo_opctag:
                        self.other_meas_nodes_list.append(var)
                    elif "CTRL" in topo_opctag:
                        self.ctrl_nodes_list.append(var)
                    break
        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful updated meas topology from file:" + path)

        # update OPC-client: delete old subscription and start new subscription
        self.update_subscription_opc_client(self.Iph1_nodes_list + self.Iph2_nodes_list + self.Iph3_nodes_list +
                                            self.other_meas_nodes_list + self.ctrl_nodes_list, False)

        self.reset_flags(list_of_nodes_to_reset, dir_name)

    def set_status_flags(self, path, list_of_nodes_to_reset, dir_name):
        # get at server registered vars allocated as CustomVar
        server_vars = self.get_customized_server_vars(dir_name)

        # get new topology
        self.clear_topo_status_flags()
        self.topo_data = TopologyData(path)

        # cluster topology nodes into lists (current, ctrl and misc) and assign the appropriate CustomVar
        for topo_opctag, topo_browsename in self.topo_data.get_itempairs():
            for var in server_vars:
                if var.opctag == topo_opctag:
                    if "RES" not in topo_opctag and "CTRL" not in topo_opctag:
                        self.misc_nodes_list.append(var)
                    break
        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful updated status flags from file:" + path)

        # update OPC-client: delete old subscription and start new subscription
        self.update_subscription_opc_client(self.misc_nodes_list, True, 500)

        self.reset_flags(list_of_nodes_to_reset, dir_name)

    def reset_flags(self, list_of_flags_to_reset, dir_name):
        """
        Reset the value of each node in the provided list to 0.
        :param list_of_flags_to_reset: list of nodes
        :param dir_name: <String> name of subfolder(node)
        """
        nodes = []
        values = []
        for var in self.opc_client.get_server_vars(dir_name):
            for node in list_of_flags_to_reset:
                if var.nodeid == node.nodeid:
                    nodes.append(var)
                    values.append(0)
                    break

        self.opc_client.set_vars(nodes, values)

    def get_customized_server_vars(self, dir_name):
        all_observed_nodes = self.opc_client.get_server_vars(dir_name)
        mvars = []
        for var in all_observed_nodes:
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

    def update_subscription_opc_client(self, list_of_nodes, are_status_nodes=False, sub_interval=1):
        self.opc_client.make_subscription(self, self.server_dir_name, list_of_nodes, are_status_nodes, sub_interval)

    def clear_topo_meas(self):
        self.slack_ph1 = None
        self.slack_ph2 = None
        self.slack_ph3 = None
        self.Iph1_nodes_list = []
        self.Iph2_nodes_list = []
        self.Iph3_nodes_list = []
        self.ctrl_nodes_list = []
        self.other_meas_nodes_list = []

    def clear_topo_status_flags(self):
        self.misc_nodes_list = []

    def update_data(self, node, datetime_source, val):
        # check for Update Request topology
        for var in self.misc_nodes_list:
            if var.nodeid == node.nodeid and "UPDATE_REQUEST_TOPOLOGY" in var.opctag:
                if val == 1:
                    #TODO could not stop client -->Error
                    # self._stop_client()
                    # self._start_client()
                    self.set_meas_topology(self.topo_path, [var], self.server_dir_name)
                    return

        # otherwise update data used for DiffCore
        for var in (self.Iph1_nodes_list + self.Iph2_nodes_list + self.Iph3_nodes_list):
            if var.nodeid == node.nodeid:

                # TODO necessary for real meas devices with fixed timestamp?
                ts = DateHelper.round_time(datetime_source, self.TIMESTAMP_PRECISION)
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
        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful set startValues for ctrl devices")


if __name__ == "__main__":
    ##################
    # if using local (means not in Docker)
    # local = False   # if server is local or as Docker
    # if local:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/OPCUA/python_server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/OPCUA/python_server/")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    # os.environ.setdefault("ENABLE_CERTIFICATE", "True")
    # os.environ.setdefault("CERTIFICATE_PATH_SERVER_CERT", "/opc_ua/certificates/n5geh_opcua_server_cert.pem")
    # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_CERT", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem")
    # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem")
    # os.environ.setdefault("DEBUG_MODE_PRINT", "True")
    # os.environ.setdefault("UPDATE_PERIOD", "500000")        # in microsec
    # os.environ.setdefault("TIMESTAMP_PRECISION", "10000")   # in microsec
    # os.environ.setdefault("MAX_FAULTY_STATES", "5")
    # os.environ.setdefault("NOMINAL_CURRENT", "275")
    # os.environ.setdefault("CURRENT_EPS", "0.05")
    # os.environ.setdefault("OPCUA_SERVER_DIR_NAME", "default_demonstrator")
    # os.environ.setdefault("TOPOLOGY_PATH", "/topology/TopologyFile_demonstrator.json")
    # os.environ.setdefault("PF_INPUT_PATH", "/device_config/demonstrator_setup.txt")
    ##################

    topo_path = os.environ.get("TOPOLOGY_PATH")
    opcua_dir_name = os.environ.get("OPCUA_SERVER_DIR_NAME")
    mDataHandler = DataHandler(topo_path, opcua_dir_name)
    mDataHandler.start()
