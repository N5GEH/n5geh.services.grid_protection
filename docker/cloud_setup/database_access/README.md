# Database Access
To store incoming data at the OPC-UA server in an Influx database, a separate service is needed consisting of the two parts OPC-UA client and DataFrameClient.

The OPCClient_Database is inhereted from OPCClient and used for connection and subscription to OPC-UA server.
The InfluxDBWrapper uses a DataFrameClient based on the influxdb lib to transfer bunches of accumulated data from the buffer to the influxdb.

