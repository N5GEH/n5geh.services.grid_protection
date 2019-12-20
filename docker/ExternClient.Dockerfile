FROM python:3.7-slim-buster

WORKDIR /usr/src/CloudSetup

ADD Docker/CloudSetup .
# install dependencies and libs via setup.py in CloudSetup
RUN pip install -e .
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://ubuntu5g:4840
ENV NAMESPACE https://n5geh.de
ENV ENABLE_CERTIFICATE True
ENV CERTIFICATE_PATH /OPC_UA/certificates/
ENV DEBUG_MODE_PRINT True
ENV DEBUG_MODE_VAR_UPDATER True
ENV UPDATE_PERIOD 500000
ENV TIMESTAMP_PRECISION 10000
ENV START_THRESHOLD 5000000

EXPOSE 4850
LABEL type="opcua_externClient_python" \
      version="0.5"
CMD [ "python", "/usr/src/CloudSetup/OPC_UA/Client/OPCClient_MeasSim.py"]