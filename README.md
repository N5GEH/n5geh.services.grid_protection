Grid Protection
=========================

## Docker
This repository contains modules that can be used to establish a docker based grid protection application. For more information see [wiki.n5geh.de][https://wiki.n5geh.de/display/EN/Grid+Protection]

In order to enable a minimum functionality three services have to be deployed:

* protocol master (1): OPC-UA server
* fault detection (1): Grid Protection Manager (GPM), Grid Protection Core (GPC)
* time master (2): NTP server

Additional services can be used to improve the usability and maintainability:

* database (3): InfluxDB
* visualization (3): Grafana
* database wrapper (1)

(1) are included in CloudSetup directory  
(2) are available on dockerhub, while an example for testing can be found in ntp directory  
(3) are available on dockerhub

### Gitlab runner CI
If a gitlab runner is established, there are 4 separate images specified:
- an OPCUA server
- a device group (external client) simulation as instance of an OPCUA client
- a grid protection service
- a database access for influxDB

One can generate docker images following one of this two ways:

1. The runner will automatically generate the particular image and store them in the container registry of your gitlab project.
2. Check if failure occurs.
3. Load image into your server, e.g. via docker management tools like _portainer_.

#### Auto generation
* Look at `.gitlab-ci.yml` to see what files the gitlab runner is listen to. 
Usually these are the `xx.Dockerfile` as well the `"main".py` for each service.
* Make changes to one of these files and commit.

#### Manual generation
* Go to CI/CD of your project and run pipeline manually, be aware of selecting the right branch.


## Tutorial
The tutorial demonstrates the grid protection application and the interaction of services.
For more information see the `README` there.

## NTP
To get more in touch with the functionality of the Network Time Protocol, one can use the simple `ntp_client.py`.

## open62541_c
Deprecated. Can be used to build a docker image of an OPC-UA server based on the C library open62541.

[https://wiki.n5geh.de/display/EN/Grid+Protection]: https://wiki.n5geh.de/display/EN/Grid+Protection