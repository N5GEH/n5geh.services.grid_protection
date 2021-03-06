#  encoding: utf-8
#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Grid Protection Manager.

This module init all opc clients, register variables, evaluate topology file and listen for topology updates.
Init DataHandler class with relevant nodes (coming from topology mapping).
    Methods:
            register_devices(device_config_path)
            update_topology(topo_path)
"""
import os
import time

from distutils.util import strtobool
from cloud_setup.protection.DataSource import TopologyData
from cloud_setup.protection.DataSource import CustomVar
from cloud_setup.protection.DiffCore import DiffCore
from protection.DataHandler import DataHandler
from protection.OPCClient_DataHandler import OPCClientDataHandler
from helper.DateHelper import DateHelper

__version__ = '0.7'
__author__ = 'Sebastian Krahmer'


class GridProtectionManager(object):
    def __init__(self, topology_path, dir_name, client_username, client_pw):
        """
        :param topology_path (String): path of TopologyFile.json
        :param dir_name (String): name of subfolder to create; parent of all created nodes
        """
        self.SERVER_ENDPOINT = os.environ.get("SERVER_ENDPOINT")
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT", "False")))
        self.DEVICE_PATH = os.environ.get("DEVICE_PATH")

        self.client_username = client_username
        self.client_pw = client_pw

        self.opc_client = None

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
        self.misc_nodes_list = []   # CustomVars related to status information of grid protection; (PF: PF intern simulation vars)

        self.DataHandler = None
        self.mDiffCore = None

        self._terminated = False

    def _init_OPCUA(self):
        if self.opc_client:
            self._del_OPCUA()

        self.opc_client = OPCClientDataHandler(self.client_username, self.client_pw, self.SERVER_ENDPOINT)
        self.opc_client.start()

    def _del_OPCUA(self):
        self.opc_client.stop()

    def _finalize(self):
        self._del_OPCUA()

    def terminate(self):
        self._terminated = True

    def start(self):
        """Start routine to setup GridProtectionManager
        """
        while not self._terminated:
            try:
                # start opc client
                self._init_OPCUA()

                # Init DataHandler
                self.DataHandler = DataHandler(self.opc_client)

                # Init DiffCore
                self.mDiffCore = DiffCore(self.opc_client, self.DataHandler)
                time.sleep(1)

                # Registration of vars at server
                self.register_devices(self.server_dir_name, os.path.dirname(os.getcwd()) + self.DEVICE_PATH)

                # Set status nodes used for monitoring and topology/device updates
                self.set_status_flags(self.topo_path, [], self.server_dir_name)

                # Set topology used for grid protection functionality itself
                self.set_meas_topology(self.topo_path, [], self.server_dir_name)

                # Set start value for controllable node
                self.set_start_value_for_ctrl_node(100, "LIMIT_CTRL")  # set start value of PV_LIMIT_CTRL to 100%

                # Set start value for misc node
                self.set_start_value_for_misc_node(1, "RUN_ONLINE_GRID_PROTECTION")  # set start value to ON

                # start DiffCore
                time.sleep(1)
                self.mDiffCore.start()

                print(DateHelper.get_local_datetime(), self.__class__.__name__, " finished Start-Routine")

                # start server status request loop
                while not self._terminated:
                    try:
                        browse_name = self.opc_client.client.get_server_node().get_browse_name()
                        time.sleep(1)
                    except Exception as ex:
                        print(DateHelper.get_local_datetime(), self.__class__.__name__, 'lost connection to server:')
                        print(ex)
                        break

            except Exception as ex:
                print(ex)
            finally:
                if not self._terminated:
                    print(DateHelper.get_local_datetime(), 'Restart ', self.__class__.__name__)
                    time.sleep(1)
        self._finalize()

    def register_devices(self, dir_name, device_config_path):
        """Register device representation specified in *device_config_path* as node on *dir_name* at opc server
        """

        self.opc_client.create_dir_on_server(dir_name)
        self.opc_client.register_variables_to_server(dir_name, device_config_path)

        print(DateHelper.get_local_datetime(), self.__class__.__name__,
              " successful register devices from file:" + device_config_path)

    def set_meas_topology(self, path, list_of_nodes_to_reset, dir_name):
        """Match topology specified in *path* used for grid protection with all available nodes on *dir_name* at opc
        server

        This results in defining slack nodes for subgrids as well as mapping each node to information about the
        representing phase. After all node are sorted in local lists the opc client is requested to make a subscription
        for each node of interest at the opc server.
        """
        # get at server registered vars allocated as CustomVar
        server_vars = self.get_customized_server_vars(dir_name)

        # get new topology
        self._clear_topo_meas()
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
        print(DateHelper.get_local_datetime(), self.__class__.__name__,
              " successful updated meas topology from file:" + path)

        # update topology of DataHandler
        self.DataHandler.set_topology(self.slack_ph1, self.slack_ph2, self.slack_ph3, self.Iph1_nodes_list,
                                      self.Iph2_nodes_list, self.Iph3_nodes_list, self.ctrl_nodes_list,
                                      self.misc_nodes_list)

        # update OPC-client: delete old subscription and start new subscription
        self._update_subscription_opc_client(self.DataHandler, self.Iph1_nodes_list + self.Iph2_nodes_list +
                                             self.Iph3_nodes_list + self.other_meas_nodes_list + self.ctrl_nodes_list,
                                             False)
        # reset flags
        self.reset_flags(list_of_nodes_to_reset, dir_name)

    def update_topology(self, path, list_of_nodes_to_reset, dir_name):
        """Update used grid topology by stopping DiffCore and calling set_meas_topology() and starting DiffCore again
        """
        # stop DiffCore if running
        if self.mDiffCore.is_running():
            self.mDiffCore.pause()

        # Set status nodes used monitoring and topology/device updates
        self.set_status_flags(self.topo_path, [], self.server_dir_name)

        # set new topology
        self.set_meas_topology(path, list_of_nodes_to_reset, dir_name)

        # start DiffCore
        if not self.mDiffCore.is_running():
            self.mDiffCore.resume()

    def set_status_flags(self, path, list_of_nodes_to_reset, dir_name):
        """Get status_nodes from topology file specified by *path* and map they with nodes on *dir_name* at opc server.
        In a next step make subscription for status nodes.
        """
        # get at server registered vars allocated as CustomVar
        server_vars = self.get_customized_server_vars(dir_name)

        # get new topology
        self._clear_topo_status_flags()
        self.topo_data = TopologyData(path)

        # cluster topology nodes into lists (here searching only for misc) and assign the appropriate CustomVar
        for topo_opctag, topo_browsename in self.topo_data.get_itempairs():
            for var in server_vars:
                if var.opctag == topo_opctag:
                    if "RES" not in topo_opctag and "CTRL" not in topo_opctag:
                        self.misc_nodes_list.append(var)
                    break

        print(DateHelper.get_local_datetime(), self.__class__.__name__,
              " successful updated status flags from file:" + path)

        # update OPC-client: delete old subscription and start new subscription
        self._update_subscription_opc_client(self, self.misc_nodes_list, True, 500)

        self.reset_flags(list_of_nodes_to_reset, dir_name)

    def reset_flags(self, list_of_flags_to_reset, dir_name):
        """Reset the value of each node in the provided *list_of_flags_to_reset* on *dir_name* at opc sever to 0.
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
        """Get server nodes and convert them into CustomVar to store opctag, nodeid and phase information together.
        """
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

    def _update_subscription_opc_client(self, notification_target_class, list_of_nodes, are_status_nodes=False, sub_interval=1):
        self.opc_client.make_subscription(notification_target_class, self.server_dir_name, list_of_nodes, are_status_nodes, sub_interval)

    def _clear_topo_meas(self):
        self.slack_ph1 = None
        self.slack_ph2 = None
        self.slack_ph3 = None
        self.Iph1_nodes_list = []
        self.Iph2_nodes_list = []
        self.Iph3_nodes_list = []
        self.ctrl_nodes_list = []
        self.other_meas_nodes_list = []

    def _clear_topo_status_flags(self):
        self.misc_nodes_list = []

    def update_data(self, node, datetime_source, val):
        """Function called from outside (by subscription class) when the state of an so-called update_node has changed.
        """
        # check for Update Request topology
        for var in self.misc_nodes_list:
            if var.nodeid == node.nodeid and "UPDATE_REQUEST_TOPOLOGY" in var.opctag:
                if val == 1:
                    self.update_topology(self.topo_path, [var], self.server_dir_name)
                    return
            elif var.nodeid == node.nodeid and "RUN_ONLINE_GRID_PROTECTION" in var.opctag:
                if val == 1:
                    # run DiffCore if is not running
                    if not self.mDiffCore.is_running():
                        self.mDiffCore.resume()
                    return
                else:
                    # stop DiffCore if is running
                    if self.mDiffCore.is_running():
                        self.mDiffCore.pause()
                    return

    def set_start_value_for_ctrl_node(self, start_value, key_phrase):
        """Set a *start_value* for a node specified as controllable by *key_phrase*
        """
        nodes = []
        values = []
        for node in self.ctrl_nodes_list:
            if key_phrase in node.opctag:
                nodes.append(node)
                values.append(start_value)
        self.opc_client.set_vars(nodes, values)

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful set startValues for ctrl node")

    def set_start_value_for_misc_node(self, start_value, key_phrase):
        """Set a *start_value* for a node specified as misc by *key_phrase*
        """
        nodes = []
        values = []
        for node in self.misc_nodes_list:
            if key_phrase in node.opctag:
                nodes.append(node)
                values.append(start_value)
        self.opc_client.set_vars(nodes, values)

        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful set startValues for misc node")


if __name__ == "__main__":
    ##################
    # if using local (means not in Docker)
    # local = True   # if server is local or as Docker
    # if local:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/OPCUA/python_server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/OPCUA/python_server/")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    # os.environ.setdefault("ENABLE_CERTIFICATE", "False")
    # os.environ.setdefault("CERTIFICATE_PATH_SERVER_CERT", "/opc_ua/certificates/n5geh_opcua_server_cert.pem")
    # # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_CERT", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem")
    # # os.environ.setdefault("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY", "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem")
    # os.environ.setdefault("DEBUG_MODE_PRINT", "False")
    # os.environ.setdefault("THREE_PHASE_CALCULATION", "False")
    # os.environ.setdefault("TIMESTAMP_PRECISION", "10")   # in ms
    # os.environ.setdefault("MAX_FAULTY_STATES", "5")
    # os.environ.setdefault("NOMINAL_CURRENT", "2")
    # os.environ.setdefault("CURRENT_EPS", "0.05")
    # os.environ.setdefault("OPCUA_SERVER_DIR_NAME", "demo")
    # os.environ.setdefault("TOPOLOGY_PATH", "/data/topology/TopologyFile_demonstrator.json")
    # os.environ.setdefault("DEVICE_PATH", "/data/device_config/Setup_demonstrator.txt")
    ##################

    topo_path = os.environ.get("TOPOLOGY_PATH")
    opcua_dir_name = os.environ.get("OPCUA_SERVER_DIR_NAME")

    mGridProtectionManager = GridProtectionManager(topo_path, opcua_dir_name, "n5geh_opcua_client1", "n5geh2019")
    mGridProtectionManager.start()
