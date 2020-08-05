# OPC-UA server and client
Both, server and client are based on https://github.com/FreeOpcUa/python-opcua

## OPC-UA server
An OPC-UA server is a precondition to run the grid protection service, because it is used as data hub.

The customized server come with methods, which can be called during runtime:

| Method name | Input args | Description |
| --- | --- | --- |
| ADD_NEW_OBJECTS_FOLDER | name :string | Add a new directory for clustering of nodes |
| ADD_OPC_TAG | opctag :string <br> variant_type :string <br> parent_node :string | Name of new OPC variable <br> Type of variable <br> Type in the name of the parent node the new variable should assigned to |
| SET_PV_LIMIT | active_power_setpoint :integer <br> parent_node :string | Type in active power setpoint in percent [0 ... 100] <br> Type in the name of the parent node |
| RUN_ONLINE_GRID_PROTECTION | On/Off :integer <br> parent_node :string | Type in 1 to RUN or 0 to STOP ONLINE_GRID_PROTECTION <br> Type in the name of the parent node |


## OPC-UA client
The OPCClient comes with methods to
- call server methods
- register new nodes at server
- subscribe to data changes of choosen nodes

## Trustworthy connection wih certificates
To enable an authorization between server and client the connection can be opened with the server security policy "Basic256Sha256_SignAndEncrypt".
If this is wanted, set ENABLE_CERTICITATE to TRUE in each Dockerfile. Also the certificates has to be generated first via bash script: [certificate generation][link_to_certificate_generation].

It has to mention that for now it is not recommended to open a secured connection because of open issues when refreshing the connection after the maximum session time. If this is requested attention should be given to the latest version of the opcua lib.

[link_to_certificate_generation]: /certificates/generate_certificate_x509v3.sh