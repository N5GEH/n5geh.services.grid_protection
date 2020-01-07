#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-Server class.

This class setups a new OPC-Server with:
 - address specified by Config
 - provides method to create variables remotely
"""

import sys
import os
from distutils.util import strtobool

from opcua import Server, ua, uamethod
from opcua.server.user_manager import UserManager
from opcua.ua.uaerrors import BadNoMatch

sys.path.insert(0, "..")

__version__ = '0.5'
__author__ = 'Sebastian Krahmer'

# users database
users_db = {
    'n5geh_opcua_client1': 'n5geh2019',
    'n5geh_opcua_client2': 'n5geh2020',
}


# user manager
def user_manager(isession, username, password):
    print(isession, username, password)
    isession.user = UserManager.User
    return username in users_db and password == users_db[username]


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
        self.SERVER_NAME = os.environ.get("SERVER_NAME")
        self.ENABLE_CERTIFICATE = bool(strtobool(os.environ.get("ENABLE_CERTIFICATE")))
        self.CERTIFICATE_PATH_SERVER_CERT = os.path.dirname(os.getcwd()) + os.environ.get("CERTIFICATE_PATH_SERVER_CERT")
        self.CERTIFICATE_PATH_SERVER_PRIVATE_KEY = os.path.dirname(os.getcwd()) + os.environ.get("CERTIFICATE_PATH_SERVER_PRIVATE_KEY")

        # setup our server
        self.server = Server()
        self.server.set_endpoint(self.SERVER_ENDPOINT)
        self.server.set_server_name(self.SERVER_NAME)

        if self.ENABLE_CERTIFICATE:
            # load server certificate and private key. This enables endpoints with signing and encryption.
            self.server.load_certificate(self.CERTIFICATE_PATH_SERVER_CERT)
            self.server.load_private_key(self.CERTIFICATE_PATH_SERVER_PRIVATE_KEY)

            # set all possible endpoint policies for clients to connect through
            self.server.set_security_policy([
                # ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
                # ua.SecurityPolicyType.Basic256Sha256_Sign,
            ])

        # set the security endpoints for identification of clients
        # self.server.set_security_IDs(["Anonymous", "Basic256Sha256", "Username"])
        self.server.set_security_IDs(["Username"])

        # set the user_manager function
        self.server.user_manager.set_user_manager(user_manager)

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
        # check if old dir with dir_name exists. if so then delete this dir first
        try:
            obj = self.root.get_child(["0:Objects", ("{}:" + dir_name).format(self.idx)])
            print(obj)
            # a = self.obj.get_child(dir_name)
            if obj is not None:
                if obj.get_browse_name().Name == dir_name:
                    self.server.delete_nodes([obj])
                    print("delete subfolder: " + dir_name)
        except BadNoMatch:
            print("There is no old folder with the name: " + dir_name)

        folder = self.obj.add_folder(self.idx, dir_name)
        print("Add subfolder: " + dir_name)

    @uamethod
    def register_opc_tag(self, parent, opctag, variant_type="Float", parent_node=""):
        # Object "parent_node":
        try:
            obj = self.root.get_child(["0:Objects", ("{}:" + parent_node).format(self.idx)])
        except BadNoMatch:
            print("register_opc_tag(): OPCUA_server_dir the variables should be assigned to, doesn't exists.")
            raise

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
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/OPCUA/python_server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/OPCUA/python_server/")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    # os.environ.setdefault("SERVER_NAME", "ENV SERVER_NAME N5GEH_FreeOpcUa_Python_Server")
    # os.environ.setdefault("ENABLE_CERTIFICATE", "True")
    # os.environ.setdefault("CERTIFICATE_PATH", "/OPC_UA/certificates/")

    server = CustomServer()
    server.start()
