from . import log
from . import client as hc_client
from . import server as hc_server

client = hc_client
server = hc_server


def setup():
    log.setup()
