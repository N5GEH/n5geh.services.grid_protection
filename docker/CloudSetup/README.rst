CloudSetup
=========================

Python Module to make the usage of Python OPC-UA Server-Client-Link to setup OPC-UA server and communicate bidirectional
with Powerfactory and grid protection script.

Either use main.py to setup all local, or use Dockerfiles to setup OPC- Server, Protection and MeasDevice-OPC-Client
separately.

* based on FreeOpcUA/python-opcua

Install:
pip install opcua==0.98.3

For use with Python 3.7 and opcua<0.98.3:
You have to manually change the command in opcua/common/utils Line 171 to "asyncio.ensure_future"

Dependencies:
Python > 3.4: cryptography, dateutil, lxml and pytz.

