Grid Protection
=========================
## Disclosure
This repository was developed within the scope of the research project N5GEH and serves the exemplary implementation of a cloud-based grid protection. 
There is therefore no claim to absence of errors, especially for a possible commercial adaptation. The use is without guarantee. 

## Docker
These modules can be used to run a docker based grid protection service. For more information see [wiki.n5geh.de [1]][n5geh_wiki].

In order to enable a minimum functionality three services have to be deployed:
* protocol master (1): OPC-UA server
* fault detection (1): Grid Protection Manager (GPM), Grid Protection Core (GPC)
* time master (2): NTP server

Additional services can be used to improve the usability and maintainability:
* database (3): InfluxDB
* visualization (3): Grafana
* database access (1)

(1) are included in [CloudSetup directory][dir_cloudsetup] \
(2) are available on [dockerhub [2]][dockerhub], while an example for testing can be found in [ntp directory][dir_ntp] \
(3) are available on [dockerhub [2]][dockerhub]

# Gitlab runner CI
For this project a gitlab runner is established. For now, there are 4 separate images specified:
- an OPCUA server
- a device group (external client) simulation as instance of an OPCUA client
- a grid protection service
- a database access for influxDB

One can generate docker images following one of this two ways:
1. The runner will automatically generate the particular image and store them in the container registry of your gitlab project.
2. Check if failure occurs.
3. Load image into your server, e.g. via docker management tools like _portainer_.

#### Auto generation
1. Look at `.gitlab-ci.yml` to see what files the gitlab runner is listen to. Usally this are the `xx.Dockerfile` as well as the corresponding main file in Python for each image.
2. Make changes to one of these files and commit.
3. The runner will automatically generate the particular image and store them in the container registry of your gitlab project.
4. Check if failure occurs.
5. Load image into your server environment, e.g. via portainer.

#### Manual generation
1. Go to CI/CD of your project and run pipeline manually, be aware of selecting the right branch.
2. The runner will automatically generate the particular image and store them in the container registry of your gitlab project.
3. Check if failure occurs.
4. Load image into your server, e.g. via portainer.

## Tutorial
The tutorial demonstrates the grid protection application and the interaction of services.

## NTP
To get more in touch with the functionality of the Network Time Protocol, one can use the simple `ntp_client.py`.

## open62541_c
Deprecated. Can be used to build a docker image of an OPC-UA server based on the C library open62541.

# License
License: MIT Copyright (c) 2020 N5GEH

# Acknowledgement
The project is funded by the German Federal Ministry of Economics and Energy and is part of the federal government’s digitalization strategy. 


## Links
[[1] https://wiki.n5geh.de/display/EN/Grid+Protection][n5geh_wiki] \
[[2] https://hub.docker.com][dockerhub]

[n5geh_wiki]: https://wiki.n5geh.de/display/EN/Grid+Protection
[dir_cloudsetup]: /docker/cloud_setup
[dir_ntp]: /ntp
[dockerhub]: https://hub.docker.com