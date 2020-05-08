Grid Protection
=========================

These modules can be used to run a docker based grid protection service. For more information see [wiki.n5geh.de][link_to_n5geh_wiki].
[link_to_n5geh_wiki]: https://wiki.n5geh.de/display/EN/Grid+Protection

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

# Gitlab runner CI
For this project a gitlab runner is established. For now, there are 4 separate images specified:
- an OPCUA server
- a device group (external client) simulation as instance of an OPCUA client
- a grid protection service
- a database access for influxDB

Ones could generate docker images following one of this two ways.

## Auto generation
1. Look at .gitlab-ci.yml to see what files the gitlab runner is listen to. Usally this are the xx.dockerfiles as well the main python file for each image.
2. make changes to one of these files and commit
3. the runner will automatically generate the particular image and store them in the container registry of your gitlab project
4. check if failure occurs
5. load image into your server, e.g. via portainer 

## Manual generation
1. Go to CI/CD of your project and run pipeline manually, be aware of selecting the right branch
2. the runner will automatically generate the particular image and store them in the container registry of your gitlab project
3. check if failure occurs
4. load image into your server, e.g. via portainer


