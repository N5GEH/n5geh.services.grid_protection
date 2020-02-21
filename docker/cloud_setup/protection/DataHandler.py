#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the Data handler.

This module collects all incoming data from monitored items, which is relevant in term of the chosen topology file.
After collecting at least one data point from each Meas device, the "FaultAssessment" DiffCore is called.
    Methods:

"""
import os
from threading import Lock

import pandas as pd
import time
from distutils.util import strtobool
from protection import LocalData
from helper.DateHelper import DateHelper

__version__ = '0.7'
__author__ = 'Sebastian Krahmer'

LocalData.mFaultStateCounter_ph1 = 0
LocalData.mFaultStateCounter_ph2 = 0
LocalData.mFaultStateCounter_ph3 = 0


class DataResultWrapper:
    def __init__(self, ctrl, misc, df_ph1, df_ph2, df_ph3):
        """
        :param:
                trl_nodes ([CustomVar]): list of all controllable OPC vars
                misc_nodes ([CustomVar]): list of protection relevant status flag OPC vars
                dataframe_phx (dataframe): dataframe for each phase containing all measured values for (several) timestamps
                """
        self.ctrl_nodes_list = ctrl
        self.misc_nodes_list = misc
        self.df_ph1 = df_ph1
        self.df_ph2 = df_ph2
        self.df_ph3 = df_ph3


class DataHandler(object):
    def __init__(self, opc_client):
        """
        :param opc_client (CustomClient): opc_client which registered the monitored items
        """
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT", "False")))
        self.TIMESTAMP_PRECISION = int(os.environ.get("TIMESTAMP_PRECISION"))
        self.THREE_PHASE_CALCULATION = bool(strtobool(os.environ.get("THREE_PHASE_CALCULATION", "False")))

        self.__lock = Lock()

        self.opc_client = opc_client

        self.slack_ph1 = None
        self.slack_ph2 = None
        self.slack_ph3 = None
        self.Iph1_nodes_list = []  # CustomVars related to I-measurement in phase 1 (will used only for Diff-Sum); (PF: RES-Variable, read only)
        self.Iph2_nodes_list = []
        self.Iph3_nodes_list = []
        self.ctrl_nodes_list = []  # CustomVars related to actuators (will used only for feedback-control); (PF: CTRL-Variable, control only)
        self.misc_nodes_list = []  # CustomVars not directly related to grid protection (mostly status vars and vars providing additional infos); (PF: PF intern simulation vars)

        self.df_ph1 = pd.DataFrame()          # dataframe for phase 1 to pass to fault_assessment
        self.df_ph2 = pd.DataFrame()
        self.df_ph3 = pd.DataFrame()

        self.clear_meas_data_flag = False
        self.buffer_limit = 100

    def set_topology(self, slack_ph1, slack_ph2, slack_ph3, i_ph1_nodes_list, i_ph2_nodes_list, i_ph3_nodes_list,
                     ctrl_nodes_list, misc_nodes_list):
        self.slack_ph1 = slack_ph1
        self.slack_ph2 = slack_ph2
        self.slack_ph3 = slack_ph3
        self.Iph1_nodes_list = i_ph1_nodes_list
        self.Iph2_nodes_list = i_ph2_nodes_list
        self.Iph3_nodes_list = i_ph3_nodes_list
        self.ctrl_nodes_list = ctrl_nodes_list
        self.misc_nodes_list = misc_nodes_list

    def update_data(self, node, datetime_source, val):
        # pause DiffCore Thread to not rw DataFrame which is in Update process
        with self.__lock:
            if self.clear_meas_data_flag:
                self.clear_meas_data()
            start = time.time_ns()
            # otherwise update data used for DiffCore
            for var in (self.Iph1_nodes_list + self.Iph2_nodes_list + self.Iph3_nodes_list):
                if var.nodeid == node.nodeid:

                    # TODO necessary for real meas devices with fixed timestamp?
                    ts = DateHelper.round_time(datetime_source, self.TIMESTAMP_PRECISION)

                    if self.slack_ph1 is not None and var.opctag == self.slack_ph1.opctag or \
                            self.slack_ph2 is not None and var.opctag == self.slack_ph2.opctag or \
                            self.slack_ph3 is not None and var.opctag == self.slack_ph3.opctag:
                        val = -val  # IMPORTANT: slack counts in negative manner

                    if var.phase == 1:
                        self.df_ph1.loc[ts, var.opctag] = val
                        self.print_dataframe(self.df_ph1)
                    elif var.phase == 2:
                        self.df_ph2.loc[ts, var.opctag] = val
                        self.print_dataframe(self.df_ph2)
                    elif var.phase == 3:
                        self.df_ph3.loc[ts, var.opctag] = val
                        self.print_dataframe(self.df_ph3)

                    end = time.time_ns()
                    self.print_process_time(start, end)
                    break

    def get_newest_data(self):
        """
            :returns:
                DataResultWrapper
                None: if data is not complete yet
        """
        # pause mainthread which wants to call update_data()
        with self.__lock:
            if self.check_if_all_rows_have_an_entry():
                df_ph1, df_ph2, df_ph3 = self.remove_nans_from_dataframe()

                ctrl = self.ctrl_nodes_list.copy()
                misc = self.misc_nodes_list.copy()

                self.clear_meas_data_flag = True

                return DataResultWrapper(ctrl, misc, df_ph1, df_ph2, df_ph3)
            else:
                self.check_for_unused_meas_data()
                return None

    # drops all rows where not all columns filled with values != NaN and check if length is
    def check_if_all_rows_have_an_entry(self):
        res = False
        if self.THREE_PHASE_CALCULATION:
            df_ph1 = self.df_ph1.dropna()
            df_ph2 = self.df_ph2.dropna()
            df_ph3 = self.df_ph3.dropna()
            if len(df_ph1.columns) == len(self.Iph1_nodes_list) and len(df_ph1.index) >= 1 \
                    and len(df_ph2.columns) == len(self.Iph2_nodes_list) and len(df_ph2.index) >= 1 \
                    and len(df_ph3.columns) == len(self.Iph3_nodes_list) and len(df_ph3.index) >= 1:
                res = True
        else:
            df_ph1 = self.df_ph1.dropna()
            if len(df_ph1.columns) == len(self.Iph1_nodes_list) and len(df_ph1.index) >= 1:
                res = True
        return res

    def remove_nans_from_dataframe(self):
        # drops all rows where not all columns filled with values != NaN
        if self.THREE_PHASE_CALCULATION:
            self.df_ph1.dropna(inplace=True)
            self.df_ph2.dropna(inplace=True)
            self.df_ph3.dropna(inplace=True)
        else:
            self.df_ph1.dropna(inplace=True)

        return self.df_ph1, self.df_ph1, self.df_ph1

    # def check_if_all_rows_have_an_entry(self):
    #     df_ph1 = None
    #     df_ph2 = None
    #     df_ph3 = None
    #     try:
    #         if self.THREE_PHASE_CALCULATION:
    #             # drops all rows where not all columns filled with values != NaN and check if length is
    #             df_ph1 = self.df_ph1.dropna()
    #             df_ph2 = self.df_ph2.dropna()
    #             df_ph3 = self.df_ph3.dropna()
    #             if len(df_ph1.columns) == len(self.Iph1_nodes_list) and len(df_ph1.index) >= 1 \
    #                     and len(df_ph2.columns) == len(self.Iph2_nodes_list) and len(df_ph2.index) >= 1 \
    #                     and len(df_ph3.columns) == len(self.Iph3_nodes_list) and len(df_ph3.index) >= 1:
    #                 return True
    #             return False
    #         else:
    #             # drops all rows where not all columns filled with values != NaN and check if length is
    #             df_ph1 = self.df_ph1.dropna()
    #             if len(df_ph1.columns) == len(self.Iph1_nodes_list) and len(df_ph1.index) >= 1:
    #                 return True
    #             return False
    #             #todo class
    #     except ValueError as ex:
    #         print('check_data_queue_for_completeness()')
    #         print(ex)
    #         self.print_dataframe(self.df_ph1)
    #     except pd.core.indexing.IndexingError as ex:
    #         print('check_data_queue_for_completeness()')
    #         print(ex)
    #         print(df_ph1)
    #     except TypeError as ex:
    #         print('check_data_queue_for_completeness()')
    #         print(ex)
    #         print(df_ph1)
    #     return False

    # def remove_nans_from_dataframe(self):
    #     # drops all rows where not all columns filled with values != NaN
    #     df_ph1 = None
    #     df_ph2 = None
    #     df_ph3 = None
    #     try:
    #         if self.THREE_PHASE_CALCULATION:
    #             df_ph1 = self.df_ph1
    #             df_ph1.dropna(inplace=True)
    #             df_ph2 = self.df_ph2
    #             df_ph2.dropna(inplace=True)
    #             df_ph3 = self.df_ph3
    #             df_ph3.dropna(inplace=True)
    #         else:
    #             df_ph1 = self.df_ph1
    #             df_ph1.dropna(inplace=True)
    #
    #     except ValueError as ex:
    #         print('remove_nans_from_dataframe()')
    #         print(ex)
    #         print(df_ph1)
    #         df_ph1 = None
    #         df_ph2 = None
    #         df_ph3 = None
    #     finally:
    #         return df_ph1, df_ph2, df_ph3

    def check_for_unused_meas_data(self):
        if len(self.df_ph1.index) > self.buffer_limit or len(self.df_ph2.index) > self.buffer_limit or \
                len(self.df_ph3.index) > self.buffer_limit:
            self.clear_meas_data_flag = True

    def clear_meas_data(self):
        self.df_ph1 = pd.DataFrame()
        self.df_ph2 = pd.DataFrame()
        self.df_ph3 = pd.DataFrame()

        self.clear_meas_data_flag = False

    def print_dataframe(self, dataframe):
        if self.DEBUG_MODE_PRINT:
            pass
            # print(dataframe)

    def print_process_time(self, start, end):
        if self.DEBUG_MODE_PRINT:
            print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful updated data @ ",
                  str((end - start) / (1000 * 1000)) + " ms")
