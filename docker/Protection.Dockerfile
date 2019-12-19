FROM python:3.7-slim-buster

RUN mkdir /data
ADD Docker/CloudSetup/Topology          /data/Topology
ADD Docker/CloudSetup/MeasDeviceConfig  /data/MeasDeviceConfig
VOLUME /data


WORKDIR /usr/src/CloudSetup
ADD Docker/CloudSetup .
# install dependencies and libs via setup.py in CloudSetup
RUN pip install -e .[protection]
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://ubuntu5g:4840
ENV NAMESPACE https://n5geh.de
ENV DEBUG_MODE_PRINT True
ENV DEBUG_MODE_VAR_UPDATER True
ENV UPDATE_PERIOD 500000
ENV TIMESTAMP_PRECISION 10000
ENV MAX_FAULTY_STATES 5
ENV NOMINAL_CURRENT 275
ENV CURRENT_EPS 0.05
ENV TOPOLOGY_PATH /Topology/TopologyFile_demonstrator.json
ENV PF_INPUT_PATH /MeasDeviceConfig/demonstrator_setup.txt

EXPOSE 4860
LABEL type="protection_python" \
      version="0.5"
CMD [ "python", "/usr/src/CloudSetup/Protection/DataHandler.py"]