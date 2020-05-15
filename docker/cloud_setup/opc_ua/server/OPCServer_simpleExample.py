#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

"""This is the OPC-server class.

This class setups a new OPC-server with:
 - address specified by Config
"""
import os
import sys
from opcua import Server
sys.path.insert(0, "..")

__version__ = '0.5'
__author__ = 'Sebastian Krahmer'


class CustomServer(object):
    def __init__(self):
        self.server = Server()

        # setup our server
        self.server.set_endpoint(os.environ.get("SERVER_ENDPOINT"))

        # setup our own namespace, not really necessary but should as spec
        uri = os.environ.get("NAMESPACE")
        self.idx = self.server.register_namespace(uri)

    def start(self):
        self.server.start()
        print(self.__class__.__name__, " successful started")

    def stop(self):
        self.server.stop()
        print(self.__class__.__name__, " successful stopped")


if __name__ == "__main__":
    # if using local (means not in Docker)
    # local = False   # if server is local or as Docker
    # if local:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://localhost:4840/freeopcua/server/")
    # else:
    #     os.environ.setdefault("SERVER_ENDPOINT", "opc.tcp://ubuntu5g:4840") # 0.0.0.0:4840/freeopcua/server/")
    # os.environ.setdefault("NAMESPACE", "https://n5geh.de")
    server = CustomServer()
    server.start()
