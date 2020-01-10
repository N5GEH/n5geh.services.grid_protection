FROM python:3.7-slim-buster

# install dependencies and libs via setup.py in cloud_setup
WORKDIR /usr/src/cloud_setup
ADD docker/cloud_setup .
RUN pip install -e .

# add environment variables
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://0.0.0.0:4840/OPCUA/python_server/
ENV NAMESPACE https://n5geh.de
ENV SERVER_NAME N5GEH_FreeOpcUa_Python_Server
ENV ENABLE_CERTIFICATE True
ENV CERTIFICATE_PATH_SERVER_CERT /cloud_setup/opc_ua/certificates/n5geh_opcua_server_cert.pem
ENV CERTIFICATE_PATH_SERVER_PRIVATE_KEY /cloud_setup/opc_ua/certificates/n5geh_opcua_server_private_key.pem

EXPOSE 4840
LABEL type="opcua_python_server" \
      version="0.5"
CMD [ "python", "/usr/src/cloud_setup/opc_ua/server/OPCServer.py"]