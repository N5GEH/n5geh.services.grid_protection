#  Copyright (c) 2019.
#  Author: Sebastian Krahmer
"""This is the Data Source module.

This module handles the InputData.
"""

import json

__version__ = '0.1'
__author__ = 'Sebastian Krahmer'

import csv
import os
import datetime
import tkinter as tk
from tkinter import filedialog
from collections import deque
import UC2_grid_protection.SimulationSetup.OPC_UA.mconfig as config


class TopologyData(object):
    def __init__(self, *argv):
        self.dict_POC = dict()
        if argv.__len__() == 0:
            self.path = None
            self.choose_data_file()
        else:
            self.path = argv[0]

        self.import_jsonfile()
        # self.import_csvfile()

    def __print__(self):
        return print(self.dict_POC.items())

    def choose_data_file(self):
        root = tk.Tk()
        root.withdraw()
        self.path = filedialog.askopenfilename(initialdir="",
                           filetypes=[("Json File", "*.json")],
                           title="Choose a file.")

    def import_csvfile(self):
        with open(self.path) as csvfile:
            m_csvreader = csv.reader(csvfile, delimiter=':')
            opctags = []
            browsename = []
            for row in m_csvreader:
                opctags.append(row[0].strip())
                browsename.append(row[1].strip())
            self.dict_POC = dict(zip(opctags, browsename))

    def import_jsonfile(self):
        with open(self.path) as jsonfile:
            data = json.load(jsonfile)
            opctags = []
            browsename = []
            for poc in data["POCs"]:
                for key, value in poc.items():
                    opctags.append(key)
                    browsename.append(value)
            self.dict_POC = dict(zip(opctags, browsename))

    def get_opctags(self):
        return self.dict_POC.keys()

    def get_browsenames(self):
        return self.dict_POC.values()

    def get_numberofpoc(self):
        return self.dict_POC.__len__


class MeasurementData(object):
    def __init__(self, *argv):
        """
            Args:
                param1 (str): OPC Tag name.
                param2 (nodeid): NodeID of OPC Tag
                param3 (int): Number of phase which variable is connected to (comes from OPC Tag)
                param4 (int): precision of timestamp in microseconds (will be round to)
                param5 (bool): record incoming OPC-UA data for each node
        """
        self.timestamps = deque([], config.MAX_ARCHIVES)
        self.time_precision = 5000     # in microseconds
        self.do_data_recording = False
        if argv.__len__() == 0:
            self.opctag = None
            self.nodeid = None
        elif argv.__len__() >= 2:
            self.opctag = str(argv[0])
            self.nodeid = argv[1]   # .NamespaceIndex ; .Identifier
            if argv.__len__() >= 3:
                self.phase = int(argv[2])
            if argv.__len__() == 4:
                self.time_precision = int(argv[3])
            if argv.__len__() == 5:
                self.do_data_recording = bool(argv[4])

        # ## if OPC-UA data have to be recorded: init the json file for each node
        if self.do_data_recording:
            dirpath = os.getcwd()
            self.jsonpath = dirpath + "/Diff_Protection/RecordedData/" + self.opctag + ".json"
            data = {}
            with open(self.jsonpath, 'w') as jsonfile:
                json.dump(data, jsonfile)

    def __print__(self, key):
        if key == 'last':
            return print(self.opctag, self.nodeid, self.timestamps[0])
        elif key == 'all':
            return print(self.opctag, self.nodeid, self.timestamps[:])

    def update_data(self, timestamp, value):
        # ## get source timestamp and round to defined precision
        microseconds = (timestamp - timestamp.min).microseconds
        rounding_up = (microseconds + self.time_precision / 2) // self.time_precision * self.time_precision
        rounding_down = (microseconds - self.time_precision / 2) // self.time_precision * self.time_precision
        if abs(rounding_up-microseconds) < abs(microseconds-rounding_down):
            delta = rounding_up-microseconds
        else:
            delta = microseconds-rounding_down
        timestamp_roundup = timestamp + datetime.timedelta(0, 0, delta)     # rounding-microseconds

        # ## set new attr for new data --> key: timestamp, value: meas value
        new_attr = timestamp_roundup.strftime("%Y-%m-%d-%H:%M:%S.%f")[:-3]  # trim to 1ms resolution
        if not hasattr(self, new_attr):
            setattr(self, new_attr, value)

            if len(self.timestamps) == config.MAX_ARCHIVES:
                # print(self.timestamps)
                try:
                    delattr(self, self.timestamps[-1])
                except AttributeError:
                    print("AttributeError UpdateData: i=", self, self.timestamps[-1])
            self.timestamps.appendleft(new_attr)

        if config.DEBUG_MODE:
            # print("MD update:")
            # self.__print__('last')
            pass

        # ## only do ones to record data
        if self.do_data_recording:
            data = dict()
            with open(self.jsonpath, 'r') as jsonfile:
                data = json.load(jsonfile)
                jsonfile.close()
            with open(self.jsonpath, 'w') as jsonfile:
                data[timestamp.strftime("%Y-%m-%d-%H:%M:%S.%f")[:-3]] = value
                json.dump(data, jsonfile)
                jsonfile.close()


if __name__ == '__main__':
    tf = TopologyData()
    tf.import_csvfile()
    tf.__print__()
