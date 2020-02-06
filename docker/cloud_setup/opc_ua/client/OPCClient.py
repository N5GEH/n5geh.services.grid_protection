#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-client class.

This class setups a new OPC-client for a server with a address specified by server_endpoint.

This class can register new vars at server by calling server method.
This class can make subscriptions to OPC-nodes of a given list
This class can set new values for OPC-nodes of a given list.
"""
import sys

from helper.DateHelper import DateHelper
from opcua import ua, Client
# from opcua.ua import DataValue

from opcua.ua.uaerrors import BadNoMatch

sys.path.insert(0, "..")

__version__ = '0.6'
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
    def __init__(self, server_endpoint, namespace, enable_cert, client_cert_path, client_key_path, auth_name=None,
                 auth_password=None, debug_print=False, client_request_timeout=4):

        self.NAMESPACE = namespace
        self.DEBUG_MODE_PRINT = debug_print

        self.client = Client(server_endpoint, client_request_timeout)

        if auth_name is not None and auth_password is not None:
            self.client.set_user(auth_name)
            self.client.set_password(auth_password)
        if enable_cert:
            self.client.set_security_string("Basic256Sha256,SignAndEncrypt," + client_cert_path + "," + client_key_path)

        # TODO experimental( cf. client.py @line 60)
        # self.client.session_timeout = 10*1000            # 30h = 30*60*60*1000
        # self.client.secure_channel_timeout = 10*1000     # 30h

        self.root = None
        self.idx = None

    def start(self):
        try:
            self.client.connect()
        except Exception as ex:
            print(DateHelper.get_local_datetime(), ex)
            sys.exit(1)
        except ConnectionError as er:
            print(DateHelper.get_local_datetime(), er)
            sys.exit(1)

        # Now getting root variable node using its browse path
        self.root = self.client.get_root_node()
        uri = self.NAMESPACE
        self.idx = self.client.get_namespace_index(uri)

    def stop(self):
        try:
            self.client.disconnect()
        except Exception as ex:
            print("Couldn't stop OPC Client because of: ", ex)

    def get_server_vars(self, child):
        # TODO raise TimeOutError when called after subscription was set up, (cf. ua_client.py: send_request)
        try:
            obj = self.root.get_child(["0:Objects", ("{}:" + child).format(self.idx)])
            # print(obj.get_browse_name())
            # print(obj.get_variables())
        except BadNoMatch:
            return None
        return obj.get_variables()

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

    @staticmethod
    def set_vars(observed_nodes_list, ctrl_list, value_list):
        """
        Set new value for node.
        :param observed_nodes_list: list of nodes, the client subscribed to
        :param ctrl_list: list of nodes to update
        :param value_list: list of values to assign
        """
        i = 0
        for ctrl in ctrl_list:
            for var in observed_nodes_list:
                if var.nodeid == ctrl.nodeid:
                    variant_type = var.get_data_value().Value.VariantType
                    var.set_value(value_list[i], variant_type)
                    break
            i += 1

    # region subscription
    def _subscribe(self, dir_name, sub_handler, subscription, subscription_handle, list_of_nodes_to_subscribe,
                   already_subscribed_nodes, sub_interval):
        """
            Make a subscription for list of nodes and return handle for subscription
                :param dir_name: subfolder, which contains the requested nodes
                :param sub_handler: SubHandler which will call the update_data function
                :param subscription: subscription object
                :param subscription_handle: handle can used to unsubscribe
                :param list_of_nodes_to_subscribe: list of nodes/customVars
                :param already_subscribed_nodes: list of nodes which already within subscription
                :param sub_interval: time interval the subscribed node is checked (in ms)

                :return subscription:
                :return subscription_handle
                :return subscribed_nodes
        """
        if subscription is not None:
            self._unsubscribe(subscription, subscription_handle)
            already_subscribed_nodes = []

        all_server_nodes = self.get_server_vars(dir_name)

        for node in all_server_nodes:
            for var in list_of_nodes_to_subscribe:
                if node.nodeid == var.nodeid:
                    already_subscribed_nodes.append(node)

        # make subscription
        subscription = self.client.create_subscription(sub_interval, sub_handler)
        subscription_handle = subscription.subscribe_data_change(already_subscribed_nodes)

        return subscription, subscription_handle, already_subscribed_nodes

    # will raise TimeoutError() - why? --> use self.subscription.delete() instead
    @staticmethod
    def _unsubscribe(self, subscription, subscription_handle):
        if subscription_handle is not None:
            # self.stop()
            # self.start()
            # self.subscription.delete()
            subscription.unsubscribe(subscription_handle)
    # endregion
