FROM python:3.7-slim-buster

# install dependencies and libs via setup.py in CloudSetup
WORKDIR /usr/src/CloudSetup
ADD docker/CloudSetup .
RUN pip install -e .

# add environment variables
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://0.0.0.0:4840/OPCUA/python_server/
ENV NAMESPACE https://n5geh.de
ENV SERVER_NAME N5GEH_FreeOpcUa_Python_Server
ENV ENABLE_CERTIFICATE True
ENV CERTIFICATE_PATH_SERVER_CERT /CloudSetup/OPC_UA/certificates/n5geh_opcua_server_cert.pem
ENV CERTIFICATE_PATH_SERVER_PRIVATE_KEY /CloudSetup/OPC_UA/certificates/n5geh_opcua_server_private_key.pem

EXPOSE 4840
LABEL type="opcua_python_server" \
      version="0.5"
CMD [ "python", "/usr/src/CloudSetup/OPC_UA/Server/OPCServer.py"]