#  Copyright (c) 2019.
#  Author: Sebastian Krahmer
"""This is the Data Source module.

This module defines class for different types of InputData.
"""

import json
# import csv
# import tkinter as tk
# from tkinter import filedialog
from opcua import ua
from dataclasses import dataclass

__version__ = '0.5'
__author__ = 'Sebastian Krahmer'


class TopologyData(object):
    def __init__(self, *argv):
        self.dict_POC = dict()
        self.grid_id = None
        if argv.__len__() == 0:
            self.path = None
            quit()
            # self.choose_data_file()
        else:
            self.path = argv[0]

        self.import_jsonfile()
        # self.import_csvfile()

    def __print__(self):
        return print(self.dict_POC.items())

    # def choose_data_file(self):
    #     root = tk.Tk()
    #     root.withdraw()
    #     self.path = filedialog.askopenfilename(initialdir="",
    #                        filetypes=[("Json File", "*.json")],
    #                        title="Choose a file.")

    # def import_csvfile(self):
    #     with open(self.path) as csvfile:
    #         m_csvreader = csv.reader(csvfile, delimiter=':')
    #         opctags = []
    #         browsename = []
    #         for row in m_csvreader:
    #             opctags.append(row[0].strip())
    #             browsename.append(row[1].strip())
    #         self.dict_POC = dict(zip(opctags, browsename))

    def import_jsonfile(self):
        with open(self.path) as jsonfile:
            data = json.load(jsonfile)
            self.grid_id = data["Grid-ID"]

            # get OPCTags within the TopologyFile
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

    def get_itempairs(self):
        return self.dict_POC.items()

    def get_numberofpoc(self):
        return self.dict_POC.__len__


@dataclass
class CustomVar:
    opctag: str
    nodeid: ua.NodeId
    phase: int = -1


if __name__ == '__main__':
    tf = TopologyData()
    tf.import_jsonfile()
    tf.__print__()
