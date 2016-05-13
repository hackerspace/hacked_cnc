import logging

from twisted.python import log

from . import config


def setup(level=logging.DEBUG):
    '''
    Setup logging bridge from twisted to python
    '''

    observer = log.PythonLoggingObserver()
    observer.start()
    level = config.get('loglevel', 'info')
    try:
        l = getattr(logging, level.upper())
    except:
        l = logging.INFO

    logging.basicConfig(level=l)

msg = log.msg
