FROM python:3.7-slim-buster

WORKDIR /usr/src/CloudSetup

ADD Docker/CloudSetup .
# install dependencies and libs via setup.py in CloudSetup
RUN pip install -e .
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://0.0.0.0:4840/freeopcua/server/
ENV NAMESPACE https://n5geh.de

EXPOSE 4840
LABEL type="opcua_server_python" \
      version="0.5"
CMD [ "python", "/usr/src/CloudSetup/OPC_UA/Server/OPCServer.py"]