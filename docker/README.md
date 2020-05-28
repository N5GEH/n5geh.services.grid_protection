# Working with grid protection services

## Generating docker images

Images can be created either by the gitlab runner or via docker commands in a console of the target host OS.
Please have a look at the [tutorial][link_to_tutorial].

Importing: The IP address 0.0.0.0 only refers to inside a container and not to the host OS in which the container is running.

### Appendum to container Server (OPC-UA server)
- have to publish network ports manually (cf. EXPOSE in xx.Dockerfile): 4840
- one can show the OPCUA server (variables, methods) via an OPCUA client program e.g. UaExpert 

| Name                                | Value (example)                | Description                                                                                                          |
|-------------------------------------|--------------------------------|----------------------------------------------------------------------------------------------------------------------|
| SERVER_ENDPOINT                     | "opc.tcp://0.0.0.0:4840/OPCUA/python_server/"      | URL to OPC-UA server with self referencing IP 0.0.0.0:port                                              |
| NAMESPACE                           | "https://n5geh.de"             | name of namespace to allocate nodes                                                                                          |
| SERVER_NAME                         | "N5GEH_FreeOpcUa_Server"       | name of server for identification
| ENABLE_CERTIFICATE                  | default setting for demonstration because of open issues in library: "False"                              | boolean setting, if connection between server and client should use certificates for identification and username/password for authentification                                                                                          |
| CERTIFICATE_PATH_SERVER_CERT        | "/cloud_setup/opc_ua/certificates/n5geh_opcua_server_cert.pem"                               | path of server certificate if certificate is enabled                                                                                          |
| CERTIFICATE_PATH_SERVER_PRIVATE_KEY | "/cloud_setup/opc_ua/certificates/n5geh_opcua_server_private_key.pem"                               | path of server private key if certificate is enabled                                                                                          |

### Appendum to container Protection 
When one creates a container out of the image, specify a VOLUME via docker-compose.yml or via the GUI of portainer.
The volume can be used to store the topologyFile and the measDeviceConfig.
Either you must create this file manually on the VOLUME or create a container that listens to external commands 
(e.g. via IEC 60870-5-104) and creates these files automatically. It has to mention, that for now a topology update can 
only to be perfomed by an exchange of the topology file within container directory specified by TOPOLOGY_PATH.

1. first create a VOLUME on the host
    - install Volume driver "local-persist" on docker host OS, e.g. https://github.com/MatchbookLab/local-persist 
    (https://stackoverflow.com/questions/50733139/portainer-create-new-volume)
    - add new volume with local-persist driver:
        - name: "mountpoint"
        - value: "/grid_protection/data"
2. add options when create container
    - publish network ports manually (cf. EXPOSE in xx.Dockerfile): 4860
    - assign the preliminary created volume and map it with the container path **/data**

| Name                                | Value (example)                | Description                                                                                                          |
|-------------------------------------|--------------------------------|----------------------------------------------------------------------------------------------------------------------|
| SERVER_ENDPOINT                     | "opc.tcp://ubuntu5g:4840"      | URL of the OPC-UA server with IP of the host of OPC-UA server container                                              |
| NAMESPACE                           |                                | cf. OPC-UA server container                                                                                          |
| ENABLE_CERTIFICATE                  |                                | cf. OPC-UA server container                                                                                          |
| CERTIFICATE_PATH_CLIENT_CERT        | "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem"                               | path of client certificate if certificate is enabled    |
| CERTIFICATE_PATH_CLIENT_PRIVATE_KEY | "/cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem"                               | path of client private key if certificate is enabled   |
| OPCUA_SERVER_DIR_NAME               | "demonstrator"                  | name of subdirectory of choosen node cluster |
| THREE_PHASE_CALCULATION             | "False"                         | settings flag if differential protection has to be done for all three phases of an AC grid or only for phase 1 |
| TIMESTAMP_PRECISION                 | "10"                            | desired precision of time stamps, is used to round time stamps to uniformity; the unit is ms |
| MAX_FAULTY_STATES                   | "5"                             | limit of successive evaluation results with state " Fault " from which an fault is confirmed and corresponding action returns are executed | 
| NOMINAL_CURRENT                     | "200"                           | nominal current of the main feeder of the observed subgrid; the unit is A |
| CURRENT_EPS                         | "0.05" (means 5% of 200 A = 10 A) | deviation (so-called "Epsislon" or "Delta") of the total current from 0; the unit is in percent based on the nominal current |
| TOPOLOGY_PATH                       | "/cloud_setup/data/topology/TopologyFile_demonstrator.json" | path of the stored topology file provided by the distribution grid operator |
| DEVICE_PATH                         | "/cloud_setup/data/device_config/Setup_demonstrator.txt" | path of the stored device file provided by the distribution grid operator |
| DEBUG_MODE_PRINT                    | "False"                         | flag indicating whether massive status outputs should be activated for debugging |

### Appendum to container SimDevice (external measurement simulator)

Environment variables of the container:

| Name                                | Value (example)                | Description                                                                                                          |
|-------------------------------------|--------------------------------|----------------------------------------------------------------------------------------------------------------------|
| SERVER_ENDPOINT                     |                                | cf. Protection container                                              |
| NAMESPACE                           |                                | cf. OPC-UA server container                                                                                          |
| ENABLE_CERTIFICATE                  |                                | cf. OPC-UA server container                                                                                          |
| CERTIFICATE_PATH_CLIENT_CERT        |                                | cf. Protection container                                                                                          |
| CERTIFICATE_PATH_CLIENT_PRIVATE_KEY |                                | cf. Protection container                                                                                          |
| OPCUA_SERVER_DIR_NAME               |                                | cf. Protection container                                                                           |
| AUTO_VAR_UPDATER_UPDATE_PERIOD      | "14"                           | aimed time span in ms between two value updates of a node attribute                                                  |
| AUTO_VAR_UPDATER_TIME_STEPS_NO_ERROR | "60"                          | number of time steps (cf. AUTO_VAR_UPDATER_UPDATE_PERIOD) where normal values will be send out                       |
| AUTO_VAR_UPDATER_TIME_STEPS_ERROR   | "60"                           | number of time steps (cf. AUTO_VAR_UPDATER_UPDATE_PERIOD) where abnormal values of one simulated measurement device will be send out |
| AUTO_VAR_UPDATER_TIMESTAMP_PRECISION | "10"                          | based on this timestamp precision (in ms) a randomized timestamp noize can be added                                  |
| AUTO_VAR_UPDATER_START_THRESHOLD    | "5000"                         | time threshold after the simulator will start to send periodically value update for each node                        |
| DEBUG_MODE_PRINT                    | "False"                        | flag indicating whether status outputs should be activated for debugging                                             |

### Appendum to container DatabaseAccess (InfluxDB wrapper)
- before creating this container, setup an influxdb(dockerhub/influxdb) and grafana(dockerhub/grafana/grafana)
- the exposed port of influxdb container should match with the port number of the env variables INFLUXDB_PORT.

Environment variables of the container:

| Name                                | Value (example)                | Description                                                                                                          |
|-------------------------------------|--------------------------------|----------------------------------------------------------------------------------------------------------------------|
| SERVER_ENDPOINT                     |                                | cf. Protection container                                           |
| NAMESPACE                           |                                | cf. OPC-UA server container                                                                                          |
| ENABLE_CERTIFICATE                  |                                | cf. OPC-UA server container                                                                                          |
| CERTIFICATE_PATH_CLIENT_CERT        |                                | cf. Protection container                                                                                          |
| CERTIFICATE_PATH_CLIENT_PRIVATE_KEY |                                | cf. Protection container                                                                                          |
| OPCUA_SERVER_DIR_NAME               |                                | cf. Protection container                                                                           |
| DATABASE_UPDATE_PERIOD              | "1000"                         | time span between database update in ms                                                                              |
| INFLUXDB_HOST                       | "ubuntu5g"                     | host name resp. host IP of the InfluxDB instance                                                                     |
| INFLUXDB_PORT                       | "8086"                         | port number of influxDB instance set up                                                                              |
| INFLUXDB_NAME                       | "demonstrator_grid_protection" | name of database table within the InfluxDB instance the node values contained in OPCUA_SERVER_DIR_NAME will write to |
| DEBUG_MODE_PRINT                    | "False"                        | flag indicating whether status outputs should be activated for debugging                                             |


[link_to_tutorial]: ../tutorial/