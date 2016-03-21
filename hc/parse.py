import re

from . import vars
from .error import ParseError

probe_re = re.compile(r'Z:([^\s]+) C:([^\s]+)')

# designator regexp
# X123.12 = ('X', 123.12)
# G0 = ('G', 0)
des_re = r'([{}])(-?\d+\.?\d*)'
axes_re = re.compile(des_re.format(''.join(vars.axes_designators)))


def probe(x):
    """
    Parse probe result: 'Z:4.3393 C:44434'

    Returns tuple of (z, c) floats of (mm, count)
    """
    x = x.strip()
    match = probe_re.match(x)

    if match is None:
        raise ParseError('Unable to parse probe response: "{}"'.format(x))

    z, c = match.groups()
    return (float(z), int(c))


def axes(x):
    """
    Parse gcode coordinates: 'G0 X13 Y10 F500'

    Returns list of tuples of found axis movements, e.g.:
    [('X', 13), ('Y', 10)]
    """
    x = x.strip()
    res = axes_re.findall(x)
    return map(lambda x: (x[0], float(x[1])), res)


def xyz(x):
    """
    Return tuple of parsed floats from `x`.
    (30.123, 48.0, 1)

    Contains None if there's no movement of the axis
    (None, None, 1)
    """
    needle = ['X', 'Y', 'Z']
    res = dict(filter(lambda x: x[0] in needle, axes(x)))

    out = []
    for i in needle:
        if i in res:
            out.append(res[i])
        else:
            out.append(None)

    return tuple(out)
