from . import log
from . import client as hc_client
from . import monitor as hc_monitor
from . import server as hc_server

client = hc_client
monitor = hc_monitor
server = hc_server


def setup():
    log.setup()
