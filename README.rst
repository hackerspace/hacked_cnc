Hacked CNC
==========

CNC/3D printer host software with networking capabilities.

Designed to run as a TCP server on either localhost or on the network
with various clients for different purposes.

Goal is to support G-code streaming over network without
uploading and saving megabytes of data to slow SD cards allowing
for faster turn around times.


Requirements
------------

* python
* argh
* argcomplete
* twisted
* PyQt5
* `pyqtgraph <https://github.com/pyqtgraph/pyqtgraph>`_ (latest git, develop branch)

Optional
--------

* pygame
* IPython
* trimesh

Usage
-----

Clone this repository::

        git clone https://github.com/sorki/hacked_cnc

Install default configuration file::

        cd hacked_cnc
        mkdir ~/.hc/
        cp config ~/.hc/config

You should edit this file according to your needs.

Now you can start ``hc_server``
and connect to it with one of the gui/cli clients.

For testing purposes there is ``run_fake`` script
that will start ``hc_server`` with mocked printer
attached (server communicating with mocked printer
over pipes).

CLI Clients
-----------

* hc monitor - communication monitor


GUI Clients
-----------

* hc pcb - PCB Milling tool (old hc probe)
* hc qtmonitor - GUI communication monitor
