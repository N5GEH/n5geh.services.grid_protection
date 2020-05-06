# Working with grid protection services

## Generating docker images

Images can be created either by the gitlab runner or via docker commands in a console of the target host OS.

## Create Container with portainer
1. choose "registry.git.rwth-aachen.de/" as registry root and insert the particular image tag (cf. Container Registry @ Gitlab)
2. always pull the image: true
3. restart policy: allways

### Appendum to container OPCUA server
- publish network ports manually (cf. EXPOSE in xx.Dockerfile): 4840
- one can show the OPCUA server (variables, methods) via an OPCUA client program e.g. UaExpert 

### Appendum to container OPCUA client (external simulation device emulation)
- publish network ports manually (cf. EXPOSE in xx.Dockerfile): 4850

### Appendum to container grid protection
When one creates a container out of the image, specify a VOLUME via docker-compose.yml or via the GUI of portainer.
The volume can be used to store the topologyFile and the measDeviceConfig.
Either you must create this file manually on the VOLUME or create a container that listens to external commands 
(e.g. via IEC 60870-5-104) and creates these files automatically.

1. first create a VOLUME on the host
    - install Volume driver "local-persist" on docker host OS, e.g. https://github.com/MatchbookLab/local-persist 
    (https://stackoverflow.com/questions/50733139/portainer-create-new-volume)
    - add new volume with local-persist driver:
        - name: "mountpoint"
        - value: "/grid_protection/data"
2. add options when create container
    - publish network ports manually (cf. EXPOSE in xx.Dockerfile): 4860
    - assign the preliminary created volume and map it with the container path **/data**

### Appendum to container OPCUA database access
- before creating this container, setup an influxdb(dockerhub/influxdb) and grafana(dockerhub/grafana/grafana)
- publish network ports manually (cf. EXPOSE in xx.Dockerfile): 8086


