# Database Access
To store incoming data at the OPC-UA server in an Influx database, a separate service is needed consisting of the two parts OPC-UA client and DataFrameClient.

Environment variables of the container:

| Name                                | Value (example)                | Description                                                                                                          |
|-------------------------------------|--------------------------------|----------------------------------------------------------------------------------------------------------------------|
| SERVER_ENDPOINT                     | "opc.tcp://ubuntu5g:4840"      | URL of the OPC-UA server with IP of the host of OPC-UA server container                                              |
| NAMESPACE                           |                                | cf. OPC-UA server container                                                                                          |
| ENABLE_CERTIFICATE                  |                                | cf. OPC-UA server container                                                                                          |
| CERTIFICATE_PATH_CLIENT_CERT        |                                | cf. OPC-UA server container                                                                                          |
| CERTIFICATE_PATH_CLIENT_PRIVATE_KEY |                                | cf. OPC-UA server container                                                                                          |
| OPCUA_SERVER_DIR_NAME               | "demonstrator"                 | name of subdirectory of choosen node cluster                                                                         |
| DATABASE_UPDATE_PERIOD              | "1000"                         | time span between database update in ms                                                                              |
| INFLUXDB_HOST                       | "ubuntu5g"                     | host name resp. host IP of the InfluxDB instance                                                                     |
| INFLUXDB_PORT                       | "8086"                         | port number of influxDB instance set up                                                                              |
| INFLUXDB_NAME                       | "demonstrator_grid_protection" | name of database table within the InfluxDB instance the node values contained in OPCUA_SERVER_DIR_NAME will write to |
| DEBUG_MODE_PRINT                    | "False"                        | flag indicating whether status outputs should be activated for debugging                                             |