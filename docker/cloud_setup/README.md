CloudSetup
=========================

This is a module to run an OPC-UA based grid protection service.

Either use main.py to setup all local, or use Dockerfiles to setup OPC-UA-Server, protection service, database_access and device simulator
separately.

OPC-UA is based on FreeOpcUA/python-opcua

Dependencies:
Python > 3.7: see requirements.txt

For use with Python 3.7 and opcua<0.98.3:
You have to manually change the command in opcua/common/utils Line 171 to "asyncio.ensure_future"



