import base64
import cPickle as pickle

from .error import ParseError


def cmd(*args, **kwargs):
    """
    Command decorator for protocols
    """

    def decorate(func, hidden=False, name=None):
        setattr(func, '_hc_cmd', True)
        setattr(func, '_hc_hidden', hidden)
        setattr(func, '_hc_name', name or func.__name__)
        return func

    if len(args):
        return decorate(args[0], **kwargs)
    else:
        return lambda func: decorate(func, **kwargs)


def encdata(data):
    return base64.b64encode(pickle.dumps(data))


def decdata(data):
    return pickle.loads(base64.b64decode(data))


def enc_msg(txt, idx=None):
    '''
    G0 X5 F100
    [10]M114
    [123]#ping
    '''

    txt = txt.replace('\n', '\\n')
    if idx is not None:
        return '[{}]{}\n'.format(idx, txt)

    return txt


def dec_msg(msg):
    idx = None
    i = 0

    if msg[0] == '[':
        i = 1
        while msg[i].isdigit():
            i += 1

        try:
            idx = int(msg[1:i])
        except ValueError:
            raise ParseError('Message index is not integer: "{}", input: "{}"'
                             .format(msg[1:i], msg))

        i += 1  # skip trailing ]

    txt = msg[i:].strip()
    txt = txt.replace('\\n', '\n')
    return (idx, txt)


def trace(func):
    def wrapper(*args, **kwargs):
        print('{0}'.format(func.__name__))
        val = func(*args, **kwargs)
        print('/{0}'.format(func.__name__))
        return val
    return wrapper


def xyzfmt(x, y, z):
    return 'X{:04.2f} Y{:04.2f} Z{:04.2f}'.format(x, y, z)
