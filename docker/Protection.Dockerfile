FROM python:3.7-slim-buster

#RUN mkdir /data
#ADD docker/cloud_setup/topology          /data/topology
#ADD docker/cloud_setup/device_config  /data/device_config

# install dependencies and libs via setup.py in cloud_setup
WORKDIR /usr/src/cloud_setup
ADD docker/cloud_setup .
RUN pip install -e .[protection]

# add environment variables
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://ubuntu5g:4840
ENV NAMESPACE https://n5geh.de
ENV ENABLE_CERTIFICATE True
ENV CERTIFICATE_PATH_CLIENT_CERT /cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem
ENV CERTIFICATE_PATH_CLIENT_PRIVATE_KEY /cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem
ENV DEBUG_MODE_PRINT True
ENV DEBUG_MODE_VAR_UPDATER True
ENV UPDATE_PERIOD 500000
ENV TIMESTAMP_PRECISION 10000
ENV MAX_FAULTY_STATES 5
ENV NOMINAL_CURRENT 275
ENV CURRENT_EPS 0.05
ENV VOLUME_PATH /data
ENV OPCUA_SERVER_DIR_NAME default_demonstrator
ENV TOPOLOGY_PATH /cloud_setup/topology/TopologyFile_demonstrator.json
ENV PF_INPUT_PATH /cloud_setup/device_config/demonstrator_setup.txt

EXPOSE 4860
LABEL type="protection_python" \
      version="0.5"
      
CMD [ "python", "/usr/src/cloud_setup/protection/DataHandler.py"]