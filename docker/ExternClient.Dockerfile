FROM python:3.7-slim-buster

# install dependencies and libs via setup.py in cloud_setup
WORKDIR /usr/src/cloud_setup
ADD docker/cloud_setup .
RUN pip install -e .

# add environment variables
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://ubuntu5g:4840
ENV NAMESPACE https://n5geh.de
ENV ENABLE_CERTIFICATE False
ENV CERTIFICATE_PATH_CLIENT_CERT /cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem
ENV CERTIFICATE_PATH_CLIENT_PRIVATE_KEY /cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem
ENV OPCUA_SERVER_DIR_NAME default_demonstrator
ENV DEBUG_MODE_PRINT True
ENV DEBUG_MODE_VAR_UPDATER True
ENV UPDATE_PERIOD 500000
ENV TIMESTAMP_PRECISION 10000
ENV START_THRESHOLD 5000000

EXPOSE 4850
LABEL type="opcua_externClient_python" \
      version="0.5"
CMD [ "python", "/usr/src/cloud_setup/opc_ua/client/OPCClient_MeasSim.py"]