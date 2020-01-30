FROM python:3.7-slim-buster

# install dependencies and libs via setup.py in cloud_setup
WORKDIR /usr/src/cloud_setup
ADD docker/cloud_setup .
RUN pip install -e .[database_access]

# add environment variables
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://ubuntu5g:4840
ENV NAMESPACE https://n5geh.de
ENV ENABLE_CERTIFICATE False
ENV CERTIFICATE_PATH_CLIENT_CERT /cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem
ENV CERTIFICATE_PATH_CLIENT_PRIVATE_KEY /cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem
ENV OPCUA_SERVER_DIR_NAME demo
ENV DATABASE_UPDATE_PERIOD 1000
ENV INFLUXDB_HOST ubuntu5g
ENV INFLUXDB_PORT 8086
ENV DEBUG_MODE_PRINT True


EXPOSE INFLUXDB_PORT
LABEL type="database_access_python" \
      version="0.6"
CMD [ "python", "/usr/src/cloud_setup/database_access/InfluxDbWrapper.py"]