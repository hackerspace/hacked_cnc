Communication protocols
=======================

Overview of various communication protocols used by 3D Printer / CNC controllers.



Standardization attempt
-----------------------

* https://github.com/RepRapCode/RepRapCode/tree/master/spec
* https://github.com/RepRapCode/RepRapCode/blob/master/spec/03-basic-communication/index.md
* Extracted important info:
  * communication happens via a serial a serial port (8N1, usually at 115200 or 250000 baud)
  * The checksum is a value between 0 and 255 and is calculated by XORing each byte of the message_segment. It is represented decimally.
  * checksum = reduce(lambda x, y: x ^ y, map(ord, message_segment))

GRBL
----

* https://github.com/grbl/grbl/wiki/Interfacing-with-Grbl


Smoothieware
------------
* uses GRBL protocol
* Can do checksumming and line numbering though this is not need when connected via USB as USB does checksumming for us
* Supports networking http://smoothieware.org/network
  * Telnet (port 23)
  * HTTP (port 80)
  * Simple File Transfer Protocol (port 115)
  * Plan9 (9P/Styx) (port 564)
* Probe documentation http://smoothieware.org/zprobe

G38 probe format output (`source https://github.com/Smoothieware/Smoothieware/blob/edge/src/modules/tools/zprobe/ZProbe.cpp#L503`_)::

        gcode->stream->printf("ALARM:Probe fail\n");
        gcode->stream->printf("[PRB:%1.3f,%1.3f,%1.3f:%d]\n", pos[X_AXIS], pos[Y_AXIS], pos[Z_AXIS], probeok);


Repetier-Firmware
-----------------

* https://github.com/repetier/Repetier-Firmware/blob/master/repetier%20communication%20protocol.txt
