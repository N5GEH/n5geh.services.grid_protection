FROM python:3.7-slim-buster
RUN apt-get update && apt-get install -y git

# install dependencies and libs via requirements.txt and setup.py in cloud_setup
WORKDIR /usr/src/cloud_setup
ADD docker/cloud_setup .
RUN pip install -r requirements.txt
RUN pip install -e .
RUN pip install -e .[sim_device]

# remove git and not used packages
RUN apt-get purge -y git && apt-get autoremove -y

# add environment variables
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://ubuntu5g:4840
ENV NAMESPACE https://n5geh.de
ENV ENABLE_CERTIFICATE False
ENV CERTIFICATE_PATH_CLIENT_CERT /cloud_setup/opc_ua/certificates/n5geh_opcua_client_cert.pem
ENV CERTIFICATE_PATH_CLIENT_PRIVATE_KEY /cloud_setup/opc_ua/certificates/n5geh_opcua_client_private_key.pem
ENV OPCUA_SERVER_DIR_NAME demo
ENV DEBUG_MODE_PRINT False

ENV AUTO_VAR_UPDATER_UPDATE_PERIOD 14
ENV AUTO_VAR_UPDATER_TIME_STEPS_NO_ERROR 60
ENV AUTO_VAR_UPDATER_TIME_STEPS_ERROR 60
ENV AUTO_VAR_UPDATER_TIMESTAMP_PRECISION 10
ENV AUTO_VAR_UPDATER_START_THRESHOLD 5000

ENV NAME_OF_ANORMAL_MEASUREMENT LAST_I_PH1_RES
ENV NAME_OF_SLACK_MEASUREMENT TRAFO_I_PH1_RES

LABEL type="opcua_simulatedDevices_python" \
      version="0.7"
CMD [ "python", "/usr/src/cloud_setup/sim_device/SimulatedDeviceManager.py"]