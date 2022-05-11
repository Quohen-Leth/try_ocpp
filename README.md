Simple server-client EV charging system emulation.
Based on OCPP v2.0 protocol over websockets.

To start Charging Station Management System server:
 - run csms_ocpp.py for server with CLI;
 - run csms_fastapi.py for server with web interface
To start one or more Charging Stations, run station_ocpp -n <Station Name>

Supported CLI commands:
"au" - send authorization message
"br" - get base report
"st" - transaction event info