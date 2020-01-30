#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Differential protection Algorithm Core module.

This module checks for a dataframe (which contains for all relevant nodes at least one value)
if sum of currents within the subgrid is zero.

If there is an deviation greater than an epsilon, that ctrl_nodes gets new values via OPC-client.
"""
import os
from threading import Thread
from protection import LocalData

__version__ = '0.6'
__author__ = 'Sebastian Krahmer'


class DiffCore(Thread):
    def __init__(self, opc_client, ctrl_nodes, misc_nodes, dataframe_ph1, dataframe_ph2, dataframe_ph3,
                 nominal_current=275, eps=0.05, number_of_faulty_dates_to_failure=5):
        Thread.__init__(self)
        # super().__init__()
        """
            Args:
                opc_client (CustomClient): instance of CustomClient used to set ctrl_node
                ctrl_nodes ([CustomVar]): list with all controllable OPC vars
                dataframe_phx (dataframe): dataframe for each phase containing all measured values for (several) timestamps
                nominal_current (int): nominal current of biggest cable close to MV/LV transformer in A
                eps (float): permissible deviation of current sum to zero in x/100%
                number_of_faulty_dates_to_failure (int): number of allowed consecutive faulty states within one phase
        """
        self.DEBUG_MODE_PRINT = os.environ.get("DEBUG_MODE_PRINT")
        self.NOMINAL_CURRENT = int(os.environ.get("NOMINAL_CURRENT", nominal_current))
        self.CURRENT_EPS = float(os.environ.get("CURRENT_EPS", eps))
        self.MAX_FAULTY_STATES = int(os.environ.get("MAX_FAULTY_STATES", number_of_faulty_dates_to_failure))

        self.work_status = 'init'
        self.opc_client = opc_client
        self.ctrl_nodes_list = ctrl_nodes
        self.misc_nodes_list = misc_nodes

        self.df_ph1 = dataframe_ph1
        self.df_ph2 = dataframe_ph2
        self.df_ph3 = dataframe_ph3

        self.eps_abs = self.NOMINAL_CURRENT * self.CURRENT_EPS  # 5 %

        self.print_work_status()

    def run(self):
        self.work_status = 'started'
        self.print_work_status()
        self.compute_balance_of_current()

    # def pause(self):
    #     self.work_status = 'paused'
    #     self.print_work_status()
    #
    # def resume(self):
    #     self.work_status = 'resumed'
    #     self.print_work_status()

    def stop(self):
        self.work_status = 'stopped'
        self.print_work_status()

    # ## I_sum for each phase of subgrid
    def compute_balance_of_current(self):
        self.df_ph1.loc[:, 'sum'] = self.df_ph1.sum(axis=1)
        self.df_ph2.loc[:, 'sum'] = self.df_ph2.sum(axis=1)
        self.df_ph3.loc[:, 'sum'] = self.df_ph3.sum(axis=1)

        self.evaluate_balance_of_current()

    # ## evaluate the balance (of current) for the closest timestamp
    def evaluate_balance_of_current(self):
        result_code = "VALID"
        if abs(self.df_ph1.iloc[-1]['sum']) >= self.eps_abs:  # ## if sum of closest timestamp is smaller than threshold
            result_code = "INVALID"
            self.evaluate_historical_balances_of_current(1)  # ## otherwise check if in past sum=0 was violated as well

        if abs(self.df_ph2.iloc[-1]['sum']) >= self.eps_abs and result_code == "VALID":
            result_code = "INVALID"
            self.evaluate_historical_balances_of_current(2)

        if abs(self.df_ph3.iloc[-1]['sum']) >= self.eps_abs and result_code == "VALID":
            result_code = "INVALID"
            self.evaluate_historical_balances_of_current(3)

        if result_code == "VALID":
            self.decrease_local_data_fault_status()

        self.print_current_result(result_code)

    # ## check the recent balances (of current) of selected phase
    def evaluate_historical_balances_of_current(self, faulty_phase):
        if faulty_phase == 1:
            # if within the last stored timestamps (size of MAX_ARCHIVES) are at least MAX_FAULTY_STATES
            if LocalData.mFaultStates_ph1 >= self.MAX_FAULTY_STATES:
                self.set_power_infeed_limit(0)
            else:
                LocalData.mFaultStates_ph1 += 1
        elif faulty_phase == 2:
            # if within the last stored timestamps (size of MAX_ARCHIVES) are at least MAX_FAULTY_STATES
            if LocalData.mFaultStates_ph2 >= self.MAX_FAULTY_STATES:
                self.set_power_infeed_limit(0)
            else:
                LocalData.mFaultStates_ph2 += 1
        elif faulty_phase == 3:
            # if within the last stored timestamps (size of MAX_ARCHIVES) are at least MAX_FAULTY_STATES
            if LocalData.mFaultStates_ph3 >= self.MAX_FAULTY_STATES:
                self.set_power_infeed_limit(0)
            else:
                LocalData.mFaultStates_ph3 += 1

        # update Status FAULTY_STATES
        nodes = []
        values = []
        for misc in self.misc_nodes_list:
            if "FEHLER_COUNTER" in misc.opctag:
                nodes.append(misc)
                values.append(max(LocalData.mFaultStates_ph1, LocalData.mFaultStates_ph2, LocalData.mFaultStates_ph3))
                self.opc_client.set_vars(nodes, values)

    def set_power_infeed_limit(self, upper_limit):
        # check the actual state of CTRLs
        # self.update_ctrl_states()

        nodes = []
        values = []
        # update the state of CTRLs
        for ctrl in self.ctrl_nodes_list:
            if "LIMIT_CTRL" in ctrl.opctag:
                nodes.append(ctrl)
                values.append(upper_limit)  # decrease power infeed to 0%

            # snippet when using with PowerFactory
            # if "BUS_LV_BREAKER" in ctrl.opctag:
            #     # ## add new state
            #     ctrls.append(ctrl)
            #     values.append(1)  # only for testing
            #     # values.append(0)    # open breaker 0

        # execute set_vars()
        self.opc_client.set_vars(nodes, values)

        self.decrease_local_data_fault_status()
        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, "All CTRL devices are set to power feedin = 0.")

    @staticmethod
    def decrease_local_data_fault_status():
        if LocalData.mFaultStates_ph1 > 0:
            LocalData.mFaultStates_ph1 -= 1
        if LocalData.mFaultStates_ph2 > 0:
            LocalData.mFaultStates_ph2 -= 1
        if LocalData.mFaultStates_ph3 > 0:
            LocalData.mFaultStates_ph3 -= 1

    # def update_ctrl_states(self):
    #     ctrls = []
    #     values = []
    #
    #     for ctrl in self.ctrl_list:
    #         for misc in self.misc_list:
    #             if ctrl.opctag[:-4] in misc.opctag:
    #                 ctrls.append(ctrl)
    #                 values.append(getattr(misc, misc.timestamps[0]))
    #                 break
    #
    #     self.opc_client.set_vars(ctrls, values)

    def print_current_result(self, result_code):
        if self.DEBUG_MODE_PRINT:
            print(result_code, ': '
                  , str(format(self.df_ph1.iloc[-1]['sum'], '.2f')) + '(' + str(LocalData.mFaultStates_ph1) + ')' + ', '
                  , str(format(self.df_ph2.iloc[-1]['sum'], '.2f')) + '(' + str(LocalData.mFaultStates_ph2) + ')' + ', '
                  , str(format(self.df_ph3.iloc[-1]['sum'], '.2f')) + '(' + str(LocalData.mFaultStates_ph3) + ')' + ";" + '\n')

    def print_work_status(self):
        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, self.work_status)
