Architecture
============

hacked_cnc is designed as client/server application
to allow for networked use.

Server
------

Server handling communication between TCP clients and
UART connections.

`hc_server` application currently implements multiple client
to single UART connection or stdin communication for testing purposes.
It runs following services:
* UART connection to machine (default port /dev/cnc, baudrate 115200)
* TCP server (default port 11011)
* monitor TCP server (default port 11010)

Client
------

Multiple client connections are allowed and each gets
its own responses to sent commands.

Monitor
-------

Monitor is a special type of TCP server that forwards
UART communication to TCP client. It is useful for
observing UART chit-chat, debugging and recording sessions
for diagnostic purposes.

Monitor server is run by `hc_server` application. It's possible
to connect to it with `hc_monitor` or `hc_gui_monitor` clients.

It is possible to run multiple monitor-like applications.
