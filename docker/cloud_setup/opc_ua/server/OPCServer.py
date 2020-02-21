#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-server class.

This class setups a new OPC-server with:
 - address specified by Config
 - provides method to create variables remotely
"""

import sys
import os
import logging
from distutils.util import strtobool

from helper.DateHelper import DateHelper
from opcua import Server, ua, uamethod
from opcua.server.user_manager import UserManager
from opcua.ua.uaerrors import BadNoMatch

sys.path.insert(0, "..")

__version__ = '0.6'
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


def clamp(n, minn, maxn):
    if n < minn:
        return minn
    elif n > maxn:
        return maxn
    else:
        return n


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

        # set the security endpoints for identification of clients
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

            self.server.set_security_IDs(["Username", "Basic256Sha256"])
        else:
            self.server.set_security_policy([ua.SecurityPolicyType.NoSecurity])
            self.server.set_security_IDs(["Anonymous", "Username"])

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

        # method: SET_PV_LIMIT
        inarg1 = ua.Argument()
        inarg1.Name = "active_power_setpoint"
        inarg1.DataType = ua.NodeId(ua.ObjectIds.Int32)  # Integer
        inarg1.ValueRank = -1
        inarg1.ArrayDimensions = []
        inarg1.Description = ua.LocalizedText("Type in active power setpoint in percent [0 ... 100]")

        inarg2 = ua.Argument()
        inarg2.Name = "parent_node"
        inarg2.DataType = ua.NodeId(ua.ObjectIds.String)  # String
        inarg2.ValueRank = -1
        inarg2.ArrayDimensions = []
        inarg2.Description = ua.LocalizedText("Type in the name of the parent node")

        method_node = self.obj.add_method(self.idx, "SET_PV_LIMIT", self.set_pv_active_power_setpoint, [inarg1, inarg2])

    @uamethod
    def add_objects_subfolder(self, parent, dir_name):
        # check if old dir with dir_name exists. if so then delete this dir first
        try:
            obj = self.root.get_child(["0:Objects", ("{}:" + dir_name).format(self.idx)])
            self.server.delete_nodes([obj], True)
        except BadNoMatch:
            print(DateHelper.get_local_datetime(), "There is no old folder with the name: " + dir_name)

        folder = self.obj.add_folder(self.idx, dir_name)
        print(DateHelper.get_local_datetime(), "Add subfolder: " + dir_name)

    @uamethod
    def register_opc_tag(self, parent, opctag, variant_type="Float", parent_node=""):
        # Object "parent_node":
        try:
            obj = self.root.get_child(["0:Objects", ("{}:" + parent_node).format(self.idx)])
        except BadNoMatch:
            print(DateHelper.get_local_datetime(),
                  "register_opc_tag(): OPCUA_server_dir the variables should be assigned to, doesn't exists.")
            raise

        var = ua.Variant(0, strings_to_vartyps(variant_type))
        mvar = obj.add_variable(self.idx, opctag.strip(), var)
        mvar.set_writable()
        print(DateHelper.get_local_datetime(),
              "Add variable: " + opctag + " of type " + variant_type + " @node " + parent_node)

    @uamethod
    def set_pv_active_power_setpoint(self, parent, setpoint, parent_node=""):
        try:
            obj = self.root.get_child(["0:Objects", ("{}:" + parent_node).format(self.idx)])
        except BadNoMatch:
            print(DateHelper.get_local_datetime(), "set_pv_active_power_setpoint(): assign new value to node failed.")
            raise

        for mvar in obj.get_variables():
            if "PV" and "CTRL" in mvar.get_browse_name().Name:
                variant_type = mvar.get_data_value().Value.VariantType
                mvar.set_value(clamp(setpoint, 0, 100), variant_type)
                print(DateHelper.get_local_datetime(),
                      "Set Value of node " + mvar.get_browse_name().Name + " to " + str(clamp(setpoint, 0, 100)))

    def start(self):
        self.server.start()
        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful started")

    def stop(self):
        self.server.stop()
        print(DateHelper.get_local_datetime(), self.__class__.__name__, " successful stopped")


if __name__ == "__main__":
    # optional: setup logging
    logging.basicConfig(level=logging.WARN)
    logger = logging.getLogger("opcua.uaprocessor")
    logger.setLevel(logging.DEBUG)

    #################################
    # if using local (means not in Docker)
    # local = True   # if server is local or as Docker
    # if local:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/OPCUA/python_server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/OPCUA/python_server/")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    # os.environ.setdefault("SERVER_NAME", "N5GEH_FreeOpcUa_Python_Server")
    # os.environ.setdefault("ENABLE_CERTIFICATE", "False")
    # os.environ.setdefault("CERTIFICATE_PATH_SERVER_CERT",
    #                       "/cloud_setup/opc_ua/certificates/n5geh_opcua_server_cert.pem")
    # os.environ.setdefault("CERTIFICATE_PATH_SERVER_PRIVATE_KEY",
    #                       "/cloud_setup/opc_ua/certificates/n5geh_opcua_server_private_key.pem")
    #################################
    server = CustomServer()
    server.start()
