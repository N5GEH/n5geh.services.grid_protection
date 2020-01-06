# Generating docker images

For this project a gitlab runner is established. For now, there are 3 separate images specified:
- an OPCUA server
- an external client emulation as instance of a OPCUA client
- a grid protection framework

You could generate docker images following one of this two ways.

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

## Create Container with portainer
1. choose "registry.git.rwth-aachen.de/" as registry root and insert the particular image tag (cf. Container Registry @ Gitlab)
2. always pull the image: true
3. restart policy: allways

### Appendum to OPCUA server container
- publish network ports manually (cf. EXPOSE in xx.Dockerfile): 4840
- one can show the OPCUA server (variables, methods) via an OPCUA client program e.g. UaExpert 

### Appendum to OPCUA client (external device emulation) container
- publish network ports manually (cf. EXPOSE in xx.Dockerfile): 4850

### Appendum to grid protection container
When one creates a container out of the image, specify a VOLUME via docker-compose.yml or via the GUI of portainer.
The volume contains the topologyFile and the measDeviceConfig.
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

