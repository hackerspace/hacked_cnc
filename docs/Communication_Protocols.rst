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
* used by Smoothieware too


Repetier-Firmware
-----------------

* https://github.com/repetier/Repetier-Firmware/blob/master/repetier%20communication%20protocol.txt
