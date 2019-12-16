#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Differential Protection Algorithm Core module.

This module checks for a specific time stamp if sum of currents of all registered POCs within the subgrid is zero.
"""

__version__ = '0.1'
__author__ = 'Sebastian Krahmer'

import UC2_grid_protection.SimulationSetup.OPC_UA.mconfig as config
from datetime import datetime
from collections import deque


class DiffCore:
    def __init__(self, topology_data, meas_data_list, nominal_current=275, eps=0.05, number_of_faulty_dates_to_failure=5):
        """
            Args:
                topology_data (TopologyData): object with attr dict_POC containing OPC tag for each POC
                meas_data_list ([MeasurementData]): list with all OPC vars converted in Type MeasurmentData
                nominal_current (int): nominal current of biggest cable close to MV/LV transformer  in A
                eps (float): permissible deviation of current sum to zero in x/100%
                number_of_faulty_dates_to_failure (int): number of allowed consecutive faulty states within one phase
        """
        self.work_status = 'init'
        self.eps_abs = nominal_current * eps      # 5 %
        self.max_faulty_dates = number_of_faulty_dates_to_failure
        self.max_archives = config.MAX_ARCHIVES     # 20
        self.opc_client = None

        # ## get opctags of slack node for each phase
        self.td = topology_data
        self.name_slack_ph1 = None
        self.name_slack_ph2 = None
        self.name_slack_ph3 = None
        for key, value in self.td.dict_POC.items():
            if "slack" in value.lower():
                if "PH1" in key:
                    self.name_slack_ph1 = key
                elif "PH2" in key:
                    self.name_slack_ph2 = key
                elif "PH3" in key:
                    self.name_slack_ph3 = key
            if None not in (self.name_slack_ph1, self.name_slack_ph2, self.name_slack_ph3):
                break

        # ## separate all MeasurementData objects into 3 characteristics
        self.md_list = []       # ## RES-variables of I-measurement (will used only for Diff-Sum); read only
        self.ctrl_list = []     # ## CTRL-variables; control only
        self.misc_list = []     # ## RES-variables which contain not to I-measurement + PF intern simulation vars
        for md in meas_data_list:
            if md.opctag in self.td.dict_POC.keys():
                if "_I_" in md.opctag and "RES" in md.opctag:
                    self.md_list.append(md)       # TODO maybe generate an {add_md} function
                elif "CTRL" in md.opctag:
                    self.ctrl_list.append(md)
                else:
                    self.misc_list.append(md)

        # ## initial state for Diff-Protection
        now = datetime.utcnow()
        self.last_computed_timestamp = now.strftime("%Y-%m-%d-%H:%M:%S.%f")[:-3]
        self.sum_ph1 = deque([0], self.max_archives)
        self.sum_ph2 = deque([0], self.max_archives)
        self.sum_ph3 = deque([0], self.max_archives)
        self.evaluated_timestamps = deque([self.last_computed_timestamp], self.max_archives)

        self.print_work_status()

    def start(self, opc_client):
        self.opc_client = opc_client
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

    def compute_balance_of_current(self):  # ## of subgrid with md in md_list
        i = 0
        while self.work_status == 'started':
            try:
                # ## check if newer timestamp than last computed one is available
                if datetime.strptime(self.md_list[-1].timestamps[i], "%Y-%m-%d-%H:%M:%S.%f") > datetime.strptime(self.last_computed_timestamp, "%Y-%m-%d-%H:%M:%S.%f"):
                    investigated_date = self.md_list[-1].timestamps[i]

                    # ## iter through all md listed at server and sum up (phase specific)
                    sum_ph1 = 0
                    sum_ph2 = 0
                    sum_ph3 = 0

                    for md in self.md_list:
                        if md.phase == 1:
                            if md.opctag == self.name_slack_ph1:
                                sum_ph1 -= getattr(md, investigated_date)
                            else:
                                sum_ph1 += getattr(md, investigated_date)

                        elif md.phase == 2:
                            if md.opctag == self.name_slack_ph2:
                                sum_ph2 -= getattr(md, investigated_date)
                            else:
                                sum_ph2 += getattr(md, investigated_date)

                        elif md.phase == 3:
                            if md.opctag == self.name_slack_ph3:
                                sum_ph3 -= getattr(md, investigated_date)
                            else:
                                sum_ph3 += getattr(md, investigated_date)

                    # ## all md had requested attribute = timestamp --> successful
                    self.sum_ph1.appendleft(sum_ph1)    # https://stackoverflow.com/a/10155753
                    self.sum_ph2.appendleft(sum_ph2)
                    self.sum_ph3.appendleft(sum_ph3)
                    self.last_computed_timestamp = investigated_date
                    self.evaluated_timestamps.appendleft(self.last_computed_timestamp)
                    self.evaluate_balance_of_current()

                    # ## reset i to newest timestamp index
                    i = 0

            except AttributeError:      # ## not all md had requested attribute = timestamp
                # if config.DEBUG_MODE:
                #     print("AttributeError - Timestamp not available: var=", md.opctag, " @ ", investigated_date)
                # if i < 5:
                #     i += 1  # get older timestamp index and try again
                # else:
                i = 0                   # ## keep at first index and try again
            except IndexError:
                if config.DEBUG_MODE:
                    print("IndexError - No MeasValues available: i=", i)

    # ## evaluate the balance (of current) for the actual selected timestamp
    def evaluate_balance_of_current(self):
        result_code = "INVALID"
        if abs(self.sum_ph1[0]) < self.eps_abs:     # ## if sum smaller than threshold: super
            result_code = "VALID"
        else:
            result_code = "INVALID"
            self.evaluate_historical_balances_of_current(1)   # ## otherwise check if in past sum=0 was violated as well

        if abs(self.sum_ph2[0]) < self.eps_abs and result_code == "VALID":
            result_code = "VALID"
        else:
            result_code = "INVALID"
            self.evaluate_historical_balances_of_current(2)

        if abs(self.sum_ph3[0]) < self.eps_abs and result_code == "VALID":
            result_code = "VALID"
        else:
            result_code = "INVALID"
            self.evaluate_historical_balances_of_current(3)

        if config.DEBUG_MODE:
            self.print_current_result(result_code)

    # ## check the recent balances (of current) of selected phase
    def evaluate_historical_balances_of_current(self, faulty_phase):
        limit = 0
        for i in getattr(self, "sum_ph" + str(faulty_phase)):
            if abs(i) > self.eps_abs:
                limit += 1

        # ## if within the last stored timestamps (size of MAX_ARCHIVES) are at least MAX_FAULTY_STATES
        # ## --> dissolve_grid_failure()
        if limit >= config.MAX_FAULTY_STATES:
            self.dissolve_grid_failure()

    def dissolve_grid_failure(self):
        ctrls = []
        values = []

        # # ## check the actual state of BREAKER at Slack
        self.update_ctrl_states()

        # ## update the state of BREAKER at Slack
        for ctrl in self.ctrl_list:
            if "BUS_LV_BREAKER" in ctrl.opctag:
                # ## add new state
                ctrls.append(ctrl)
                values.append(0)  # open breaker
            # if "PRED_CTRL" in ctrl.opctag:
            #     ctrls.append(ctrl)
            #     values.append(500)  # open breaker

        # ## execute set_vars()
        self.opc_client.set_vars(ctrls, values)
        print("All CTRL devices are set to power feedin = 0.")


    def update_ctrl_states(self):
        ctrls = []
        values = []

        for ctrl in self.ctrl_list:
            for misc in self.misc_list:
                if ctrl.opctag[:-4] in misc.opctag:
                    ctrls.append(ctrl)
                    values.append(getattr(misc, misc.timestamps[0]))
                    break

        self.opc_client.set_vars(ctrls, values)

    def print_current_result(self, result_code):
        print(self.last_computed_timestamp, result_code, ': '
              , str(format(self.sum_ph1[0], '.2f')) + ', '
              , str(format(self.sum_ph2[0], '.2f')) + ', '
              , str(format(self.sum_ph3[0], '.2f')) + ";" + '\n')

    def print_work_status(self):
        print(self.__class__.__name__, self.work_status)
