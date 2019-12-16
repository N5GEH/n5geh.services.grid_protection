#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-Server class.

This class setups a new OPC-Server with:
 - address specified by Config
 - provides method to create variables remotely
"""

import sys
import os
from opcua import Server, ua, uamethod
sys.path.insert(0, "..")

__version__ = '0.5'
__author__ = 'Sebastian Krahmer'


def strings_to_vartyps(arg):
    if arg == "Int16":
        return ua.VariantType.Int16
    elif arg == "Float":
        return ua.VariantType.Float
    else:
        return None     # ua.VariantType.Variant


class CustomServer(object):
    def __init__(self):
        self.SERVER_ENDPOINT = os.environ.get("SERVER_ENDPOINT")
        self.NAMESPACE = os.environ.get("NAMESPACE")

        # setup our server
        self.server = Server()
        self.server.set_endpoint(self.SERVER_ENDPOINT)

        # setup our own namespace, not really necessary but should as spec
        uri = self.NAMESPACE
        self.idx = self.server.register_namespace(uri)

        # get important nodes
        self.root = self.server.get_root_node()
        self.obj = self.server.get_objects_node()

        self.init_methods()

    def init_methods(self):
        # method: ADD_OBJECTS_DIR
        inarg1 = ua.Argument()
        inarg1.Name = "objects folder"
        inarg1.DataType = ua.NodeId(ua.ObjectIds.String)  # String
        inarg1.ValueRank = -1
        inarg1.ArrayDimensions = []
        inarg1.Description = ua.LocalizedText("Name the new objects folder")

        method_node = self.obj.add_method(self.idx, "ADD_NEW_OBJECTS_FOLDER", self.add_objects_subfolder, [inarg1])

        # method: ADD_OPC_TAG
        inarg1 = ua.Argument()
        inarg1.Name = "opctag"
        inarg1.DataType = ua.NodeId(ua.ObjectIds.String)  # String
        inarg1.ValueRank = -1
        inarg1.ArrayDimensions = []
        inarg1.Description = ua.LocalizedText("Name new OPC variable")

        inarg2 = ua.Argument()
        inarg2.Name = "variant_type"
        inarg2.DataType = ua.NodeId(ua.ObjectIds.String)  # String
        inarg2.ValueRank = -1
        inarg2.ArrayDimensions = []
        inarg2.Description = ua.LocalizedText("Type of variable")

        inarg3 = ua.Argument()
        inarg3.Name = "parent_node"
        inarg3.DataType = ua.NodeId(ua.ObjectIds.String)  # String
        inarg3.ValueRank = -1
        inarg3.ArrayDimensions = []
        inarg3.Description = ua.LocalizedText("Type in the name of the parent node the new variable should assigned to")

        method_node = self.obj.add_method(self.idx, "ADD_OPC_TAG", self.register_opc_tag, [inarg1, inarg2, inarg3])

    @uamethod
    def add_objects_subfolder(self, parent, dir_name):
        folder = self.obj.add_folder(self.idx, dir_name)
        print("Add subfolder: " + dir_name)

    @uamethod
    def register_opc_tag(self, parent, opctag, variant_type="Float", parent_node=""):
        # Object "parent_node":
        obj = self.root.get_child(["0:Objects", ("{}:" + parent_node).format(self.idx)])

        var = ua.Variant(0, strings_to_vartyps(variant_type))
        mvar = obj.add_variable(self.idx, opctag.strip(), var)
        mvar.set_writable()
        print("Add variable: " + opctag + " of type " + variant_type + " @node " + parent_node)

    def start(self):
        self.server.start()
        print(self.__class__.__name__, " successful started")

    def stop(self):
        self.server.stop()
        print(self.__class__.__name__, " successful stopped")


if __name__ == "__main__":
    # if using local (means not in Docker)
    # local = False   # if Server is local or as Docker
    # if local:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/freeopcua/server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/freeopcua/server/")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    server = CustomServer()
    server.start()
