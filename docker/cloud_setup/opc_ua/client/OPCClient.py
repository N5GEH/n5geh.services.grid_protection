#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-client class.

This class setups a new OPC-client with for a server with a address specified by os.environ.get("SERVER_ENDPOINT").
This client is connected to a DataHandler.
This class can register new vars at server by calling server method.
    vars specified by PFInputFiles
This class makes subscriptions to OPC-nodes of a given list (+ forwards DataHandler as arg to SubHandler)
This class can set new values for OPC-nodes of a given list.
"""
import os
import sys

from opcua import ua, Client
from distutils.util import strtobool
# from opcua.ua import DataValue

from cloud_setup.opc_ua.client.subscription import SubHandler
from opcua.ua.uaerrors import BadNoMatch

sys.path.insert(0, "..")

__version__ = '0.5'
__author__ = 'Sebastian Krahmer'


def format_textfile(mlist):
    result = []
    for i in mlist:
        a = i.replace('\t', ' ')
        b = a.replace('\n', ' ')
        c = b.replace(',0', ' ')
        d = c.replace(',', ' ')
        result.append(d)
    return result


def numbers_to_vartyps(arg):
    if arg == 2:
        return ua.VariantType.Int16
    elif arg == 4:
        return ua.VariantType.Float
    else:
        return None     # ua.VariantType.Variant


def numbers_to_typestrings(arg):
    if arg == 2:
        return "Int16"
    elif arg == 4:
        return "Float"
    else:
        return None     # ua.VariantType.Variant


class CustomClient(object):
    def __init__(self, server_endpoint, client_request_timeout=4):

        self.SERVER_ENDPOINT = os.environ.get("SERVER_ENDPOINT", server_endpoint)
        self.NAMESPACE = os.environ.get("NAMESPACE")
        self.ENABLE_CERTIFICATE = bool(strtobool(os.environ.get("ENABLE_CERTIFICATE")))
        self.CERTIFICATE_PATH_CLIENT_CERT = os.path.dirname(os.getcwd()) + os.environ.get("CERTIFICATE_PATH_CLIENT_CERT")
        self.CERTIFICATE_PATH_CLIENT_PRIVATE_KEY = os.path.dirname(os.getcwd()) + os.environ.get("CERTIFICATE_PATH_CLIENT_PRIVATE_KEY")
        self.DEBUG_MODE_PRINT = bool(strtobool(os.environ.get("DEBUG_MODE_PRINT")))

        self.client = Client(self.SERVER_ENDPOINT, client_request_timeout)
        #TODO experimental( cf. client.py @line 60)

        # self.client.session_timeout = 10*1000            # 30h = 30*60*60*1000
        # self.client.secure_channel_timeout = 10*1000     # 30h
        self.client.set_user("n5geh_opcua_client1")
        self.client.set_password("n5geh2019")
        if self.ENABLE_CERTIFICATE:
            self.client.set_security_string("Basic256Sha256,SignAndEncrypt," + self.CERTIFICATE_PATH_CLIENT_CERT + "," +
                                            self.CERTIFICATE_PATH_CLIENT_PRIVATE_KEY)

        self.root = None
        self.idx = None
        self.observed_nodes = []

        self.observed_status_nodes = []
        self.subscription_status_nodes = None
        self.subscription_handle_status_nodes = None

        self.observed_meas_nodes = []
        self.subscription_meas_nodes = None
        self.subscription_handle_meas_nodes = None

        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful init")

    def start(self):
        self.client.connect()

        # Now getting root variable node using its browse path
        self.root = self.client.get_root_node()
        uri = self.NAMESPACE

        self.idx = self.client.get_namespace_index(uri)

        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful connected")

    def create_dir_on_server(self, child):
        # get object node
        objects_node = self.client.get_objects_node()

        # add new folder "child" first
        for method in objects_node.get_methods():
            # print(method.get_browse_name().Name)
            if "ADD_NEW_OBJECTS_FOLDER" in method.get_browse_name().Name:
                objects_node.call_method(method, child)

    def register_variables_to_server(self, child, file_path):
        # get object node
        objects_node = self.client.get_objects_node()
        # get tags of variables and register them serverside in folder "child"
        mtagfile = open(file_path, 'r')
        tags_pf_output = format_textfile(mtagfile.readlines())
        mtagfile.close()

        # VARIANT A
        for method in objects_node.get_methods():
            # print(method.get_browse_name().Name)
            if "ADD_OPC_TAG" in method.get_browse_name().Name:
                for i in tags_pf_output:
                    opctag, typ = i.split()
                    opctag, typ = opctag.strip(), int(typ)

                    # call method to register var
                    objects_node.call_method(method, opctag, numbers_to_typestrings(typ), child)

        # VARIANT B
        # for i in tags_pf_output:
        #     opctag, typ = i.split()
        #     opctag, typ = opctag.strip(), int(typ)
        #
        #
        #     # register vars at server
        #     mvar = folder.add_variable(self.idx, opctag.strip(), ua.Variant(0, numbers_to_vartyps(typ)))
        #     mvar.set_writable()
        #
        #     # Test
        #     # dv = DataValue()
        #     # dv.Value = ua.Variant(1,numbers_to_vartyps(typ))
        #     # mvar.set_value(dv)

    def make_subscription(self, target_object, dir_name, list_of_nodes_to_observe, are_status_nodes=False,
                          sub_interval=1):
        """
        Make a subscription for list of nodes and set some properties.
        :param target_object: object the datachange_notification of subscription is sent to
        :param dir_name: subfolder, which contains the requested nodes
        :param list_of_nodes_to_observe: list of nodes/customVars
        :param are_status_nodes: flag if requested subscription is only for status flags
        :param sub_interval: time interval the subscribed node is checked (in ms)
        """
        self.observed_nodes = []
        sub_handler = SubHandler(target_object, "client")

        if are_status_nodes is True:
            self._subscribe(sub_handler, self.subscription_status_nodes, self.subscription_handle_status_nodes,
                            list_of_nodes_to_observe, dir_name, self.observed_status_nodes, sub_interval)
        else:
            self._subscribe(sub_handler, self.subscription_meas_nodes, self.subscription_handle_meas_nodes,
                            list_of_nodes_to_observe, dir_name, self.observed_meas_nodes, sub_interval)

        self.observed_nodes = self.observed_meas_nodes + self.observed_status_nodes

        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful updates subscription")

    def _subscribe(self, sub_handler, subscription, subscription_handle, list_of_nodes_to_observe, dir_name,
                   new_observed_nodes, sub_interval):

        if subscription is not None:
            subscription.unsubscribe(subscription_handle)
            # subscription.delete()
            new_observed_nodes = []
        all_server_nodes = self.get_server_vars(dir_name)

        for node in all_server_nodes:
            for var in list_of_nodes_to_observe:
                if node.nodeid == var.nodeid:
                    new_observed_nodes.append(node)

        # make subscription
        subscription = self.client.create_subscription(sub_interval, sub_handler)
        subscription_handle = subscription.subscribe_data_change(new_observed_nodes)

    def get_server_vars(self, child):
        # TODO raise TimeOutError, (cf. ua_client.py: send_request)
        try:
            obj = self.root.get_child(["0:Objects", ("{}:" + child).format(self.idx)])
            print(obj.get_browse_name())
            print(obj.get_variables())
        except BadNoMatch:
            return None
        return obj.get_variables()

    # TODO will raise TimeoutError() - why? --> use self.subscription.delete() instead
    # def unsubscribe(self):
    #     if self.subscription_handle is not None:
    #
    #         # self.stop()
    #         # self.start()
    #         # self.subscription.delete()
    #         self.subscription.unsubscribe(self.subscription_handle)
        
    def stop(self):
        self.client.disconnect()
        if self.DEBUG_MODE_PRINT:
            print(self.__class__.__name__, " successful disconnected")

    def set_vars(self, ctrl_list, value_list):
        """
        Set new value for node.
        :param ctrl_list: list of nodes to update
        :param value_list: list of values to assign
        """
        i = 0
        for ctrl in ctrl_list:
            for var in self.observed_nodes:
                if var.nodeid == ctrl.nodeid:
                    variant_type = var.get_data_value().Value.VariantType
                    var.set_value(value_list[i], variant_type)
                    break
            i += 1
