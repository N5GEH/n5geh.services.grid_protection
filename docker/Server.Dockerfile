FROM python:3.7-slim-buster
RUN apt-get update && apt-get install -y git

# install dependencies and libs via requirements.txt and setup.py in cloud_setup
WORKDIR /usr/src/cloud_setup
ADD docker/cloud_setup .
RUN pip install -r requirements.txt
RUN pip install -e .

# remove git and not used packages
RUN apt-get purge -y git && apt-get autoremove -y

# add environment variables
ENV PYTHONPATH /usr/src
ENV SERVER_ENDPOINT opc.tcp://0.0.0.0:4840/OPCUA/python_server/
ENV NAMESPACE https://n5geh.de
#ENV SERVER_NAME N5GEH_FreeOpcUa_Server
#ENV ENABLE_CERTIFICATE False
ENV CERTIFICATE_PATH_SERVER_CERT /cloud_setup/opc_ua/certificates/n5geh_opcua_server_cert.pem
ENV CERTIFICATE_PATH_SERVER_PRIVATE_KEY /cloud_setup/opc_ua/certificates/n5geh_opcua_server_private_key.pem

EXPOSE 4840
LABEL type="opcua_python_server" \
<<<<<<< HEAD
<<<<<<< HEAD
      version="0.7"
=======
      version="0.6"

>>>>>>> develop
=======
      version="0.7"
>>>>>>> 10b06bd... adapt ENV vars for deployment with kubernetes on demonstrator pc
CMD [ "python", "/usr/src/cloud_setup/opc_ua/server/OPCServer.py"]