#  encoding: utf-8
#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Differential protection Algorithm Core module.

    This module checks for a dataframe (which contains for all relevant nodes at least one value)
    if sum of currents within the subgrid is zero.

    If there is an deviation greater than an epsilon, that ctrl_nodes gets new values via OPC-client.
"""
import os
import time
from distutils.util import strtobool
from threading import Thread

from helper.DateHelper import DateHelper
from protection import LocalData

__version__ = '0.7'
__author__ = 'Sebastian Krahmer'


def sums(row):
    return row.sum()


class DiffCore(Thread):
    def __init__(self, opc_client, data_handler, nominal_current=275, eps=0.05, number_of_faulty_states_to_failure=5):
        Thread.__init__(self)

        # super().__init__()
        """
            Args:
                opc_client (CustomClient): instance of CustomClient used to set ctrl_node
                data_handler (DataHandler): instance of DataHandler (Bufferclass for incoming data of monitored items)
                nominal_current (int): nominal current of biggest cable close to MV/LV transformer in A
                eps (float): permissible deviation of current sum to zero in x/100%
                number_of_faulty_dates_to_failure (int): number of allowed consecutive faulty states within one phase
        """
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT", "False")))
        self.NOMINAL_CURRENT = int(os.environ.get("NOMINAL_CURRENT", nominal_current))
        self.CURRENT_EPS = float(os.environ.get("CURRENT_EPS", eps))
        self.MAX_FAULTY_STATES = int(os.environ.get("MAX_FAULTY_STATES", number_of_faulty_states_to_failure))
        # three_phase_mode: True if calculation should be for all three phases, False if only single phase
        self.THREE_PHASE_CALCULATION = bool(strtobool(os.environ.get("THREE_PHASE_CALCULATION", "False")))

        self.opc_client = opc_client
        self.data_handler = data_handler
        self.eps_abs = self.NOMINAL_CURRENT * self.CURRENT_EPS  # 5 %

        self.ctrl_nodes_list = []
        self.misc_nodes_list = []

        self.df_ph1 = None
        self.df_ph2 = None
        self.df_ph3 = None

        self._is_running = False
        self.print_work_status('init')

    def run(self):
        self._is_running = True
        self.set_status_online_grid_protection(1)
        self.print_work_status('started')
        while True:
            while self.is_running():
                self.check_for_new_data()
                time.sleep(0.005)
            time.sleep(1)

    def pause(self):
        self._is_running = False
        self.set_status_online_grid_protection(0)
        self.print_work_status('paused')

    def resume(self):
        self._is_running = True
        self.set_status_online_grid_protection(1)
        self.print_work_status('resumed')

    def is_running(self):
        return self._is_running

    def check_for_new_data(self):
        res = self.data_handler.get_newest_data()

        if res is not None:
            self.ctrl_nodes_list = res.ctrl_nodes_list
            self.misc_nodes_list = res.misc_nodes_list
            self.df_ph1 = res.df_ph1
            self.df_ph2 = res.df_ph2
            self.df_ph3 = res.df_ph3

            if self.THREE_PHASE_CALCULATION and (self.df_ph1 is None or self.df_ph2 is None or self.df_ph3 is None)\
                    or not self.THREE_PHASE_CALCULATION and self.df_ph1 is None:
                pass
            else:
                self.evaluate_balance_of_current()

    # evaluate the balance (of current) for the closest timestamp
    def evaluate_balance_of_current(self):
        self.df_ph1['sum'] = self.df_ph1.apply(func=sums, axis=1)

        if self.THREE_PHASE_CALCULATION:
            self.df_ph2['sum'] = self.df_ph2.apply(func=sums, axis=1)
            self.df_ph3['sum'] = self.df_ph3.apply(func=sums, axis=1)

        result_code = "VALID"

        try:
            if self.THREE_PHASE_CALCULATION:
                if abs(self.df_ph1.iloc[-1][
                           'sum']) >= self.eps_abs:  # if sum of closest timestamp is bigger than threshold
                    result_code = "INVALID"
                    self.evaluate_historical_balances_of_current(1)  # otherwise check if in past sum=0 was violated as well
                else:
                    self.decrease_fault_state_counter(1)

                if abs(self.df_ph2.iloc[-1]['sum']) >= self.eps_abs and result_code == "VALID":
                    result_code = "INVALID"
                    self.evaluate_historical_balances_of_current(2)
                else:
                    self.decrease_fault_state_counter(2)

                if abs(self.df_ph3.iloc[-1]['sum']) >= self.eps_abs and result_code == "VALID":
                    result_code = "INVALID"
                    self.evaluate_historical_balances_of_current(3)
                else:
                    self.decrease_fault_state_counter(3)
            else:
                if abs(self.df_ph1.iloc[-1]['sum']) >= self.eps_abs:
                    result_code = "INVALID"
                    self.evaluate_historical_balances_of_current(1)
                else:
                    self.decrease_fault_state_counter(1)

            self.send_fault_state_counter_to_server()

            self.print_current_result(result_code)
        except IndexError as ex:
            print('evaluate_balance_of_current()')
            print(ex)

    # check the recent balances (of current) of selected phase
    def evaluate_historical_balances_of_current(self, faulty_phase):
        if faulty_phase == 1:
            self.increase_fault_state_counter(faulty_phase)
            # if within the last stored timestamps (size of MAX_ARCHIVES) are at least MAX_FAULTY_STATES
            if LocalData.mFaultStateCounter_ph1 >= self.MAX_FAULTY_STATES:
                self.set_power_infeed_limit(0)

        elif faulty_phase == 2:
            self.increase_fault_state_counter(faulty_phase)
            # if within the last stored timestamps (size of MAX_ARCHIVES) are at least MAX_FAULTY_STATES
            if LocalData.mFaultStateCounter_ph2 >= self.MAX_FAULTY_STATES:
                self.set_power_infeed_limit(0)

        elif faulty_phase == 3:
            self.increase_fault_state_counter(faulty_phase)
            # if within the last stored timestamps (size of MAX_ARCHIVES) are at least MAX_FAULTY_STATES
            if LocalData.mFaultStateCounter_ph3 >= self.MAX_FAULTY_STATES:
                self.set_power_infeed_limit(0)

    def send_fault_state_counter_to_server(self):
        nodes = []
        values = []
        for misc in self.misc_nodes_list:
            if "FEHLER_COUNTER" and "PH1" in misc.opctag:
                nodes.append(misc)
                values.append(LocalData.mFaultStateCounter_ph1)
            elif "FEHLER_COUNTER" and "PH2" in misc.opctag:
                nodes.append(misc)
                values.append(LocalData.mFaultStateCounter_ph2)
            elif "FEHLER_COUNTER" and "PH3" in misc.opctag:
                nodes.append(misc)
                values.append(LocalData.mFaultStateCounter_ph3)

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

        print(DateHelper.get_local_datetime(), self.__class__.__name__, "All CTRL devices are set to power feedin = 0.")

    def set_status_online_grid_protection(self, status_value):
        """Set a value for node RUN_ONLINE_GRID_PROTECTION
        """
        nodes = []
        values = []
        for node in self.misc_nodes_list:
            if "RUN_ONLINE_GRID_PROTECTION" in node.opctag:
                nodes.append(node)
                values.append(status_value)
        self.opc_client.set_vars(nodes, values)

        print(DateHelper.get_local_datetime(), self.__class__.__name__, "updated status of Online Grid Protection.")


    @staticmethod
    def decrease_fault_state_counter(faulty_phase):
        if faulty_phase == 1 and LocalData.mFaultStateCounter_ph1 > 0:
            LocalData.mFaultStateCounter_ph1 -= 1
        elif faulty_phase == 2 and LocalData.mFaultStateCounter_ph2 > 0:
            LocalData.mFaultStateCounter_ph2 -= 1
        elif faulty_phase == 3 and LocalData.mFaultStateCounter_ph3 > 0:
            LocalData.mFaultStateCounter_ph3 -= 1

    def increase_fault_state_counter(self, faulty_phase):
        if faulty_phase == 1 and LocalData.mFaultStateCounter_ph1 < self.MAX_FAULTY_STATES:
            LocalData.mFaultStateCounter_ph1 += 1
        elif faulty_phase == 2 and LocalData.mFaultStateCounter_ph2 < self.MAX_FAULTY_STATES:
            LocalData.mFaultStateCounter_ph2 += 1
        elif faulty_phase == 3 and LocalData.mFaultStateCounter_ph3 < self.MAX_FAULTY_STATES:
            LocalData.mFaultStateCounter_ph3 += 1

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
            if self.THREE_PHASE_CALCULATION:
                print(result_code, ': '
                      , str(format(self.df_ph1.iloc[-1]['sum'], '.2f')) + '(' + str(LocalData.mFaultStateCounter_ph1) + ')' + ', '
                      , str(format(self.df_ph2.iloc[-1]['sum'], '.2f')) + '(' + str(LocalData.mFaultStateCounter_ph2) + ')' + ', '
                      , str(format(self.df_ph3.iloc[-1]['sum'], '.2f')) + '(' + str(LocalData.mFaultStateCounter_ph3) + ')' + ";" + '\n')
            else:
                print(result_code, ': '
                      , str(format(self.df_ph1.iloc[-1]['sum'], '.2f')) + '(' + str(LocalData.mFaultStateCounter_ph1) + ')' + ";" + '\n')

    def print_work_status(self, work_status):
        print(DateHelper.get_local_datetime(), self.__class__.__name__, work_status)
