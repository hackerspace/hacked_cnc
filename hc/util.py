import base64
import cPickle as pickle


def encdata(data):
    return base64.b64encode(pickle.dumps(data))


def decdata(data):
    return pickle.loads(base64.b64decode(data))


def trace(func):
    def wrapper(*args, **kwargs):
        print('{0}'.format(func.__name__))
        val = func(*args, **kwargs)
        print('/{0}'.format(func.__name__))
        return val
    return wrapper
