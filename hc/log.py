import logging

from twisted.python import log


def setup(level=logging.DEBUG):
    '''
    Setup logging bridge from twisted to python
    '''

    observer = log.PythonLoggingObserver()
    observer.start()
    logging.basicConfig(level=logging.DEBUG)

msg = log.msg
