Hacked CNC
==========

Minimalistic host software prototype.

Goal is to support g-code streaming over network without
uploading and saving megabytes of data to slow SD cards allowing
for faster turn around times.


Requirements
------------

* python
* twisted
* PyQt5

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
attached.
