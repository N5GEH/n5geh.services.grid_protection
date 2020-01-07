# from: https://github.com/FreeOpcUa/python-opcua/issues/916
# alternative use: https://github.com/node-opcua/node-opcua-pki to enable CA authorithy
openssl genrsa -out n5geh_opcua_server_private_key.pem 2048
openssl req -x509 -days 365 -new -out n5geh_opcua_server_cert.pem -key n5geh_opcua_server_private_key.pem -config ssl.conf