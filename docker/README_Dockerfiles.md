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

## Appendum to protection image
When you create a container out of the image, specify a VOLUME via docker-compose.yml or via the GUI of portainer.
The volume should be named /data and contains the topologyFile and the measDeviceConfig.
Either you must create this file manually on the VOLUME or create a container that listens to external commands 
(e.g. via IEC 60870-5-104) and creates these files automatically.
