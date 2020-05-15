# Protection
This module contains the three main classes, called GridProtectionManager and GridProtectionCore (DiffCore) as well as 
an intermediate buffer class called DataHandler.
 
As it is intended to run this code into a docker container, GridProtectionManager.py is the entry point. To handle 
termination of the OPC-UA server connection, a restart loop is implemented. 