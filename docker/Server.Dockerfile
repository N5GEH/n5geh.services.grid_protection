FROM python:3.7-slim-buster

WORKDIR /usr/src/CloudSetup

ADD Docker/CloudSetup .
# install dependencies and libs via setup.py in CloudSetup
RUN pip install -e .
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://0.0.0.0:4840/OPCUA/python_server/
ENV NAMESPACE https://n5geh.de
ENV SERVER_NAME N5GEH_FreeOpcUa_Python_Server
ENV ENABLE_CERTIFICATE True
ENV CERTIFICATE_PATH /OPC_UA/certificates/

EXPOSE 4840
LABEL type="opcua_python_server" \
      version="0.5"
CMD [ "python", "/usr/src/CloudSetup/OPC_UA/Server/OPCServer.py"]