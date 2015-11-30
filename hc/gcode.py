from .error import ParseError


def checksum(cmd):
    '''
    Compute checksum by XORing each byte of the
    input `cmd`.

    Returns int between 0-255.
    '''

    return reduce(lambda x, y: x ^ y, map(ord, cmd))


def parse(line):
    '''
    Parse g-code `line`

    Returns tuple consisting of
    (gcode_command_string, line_number_integer, checksum_integer)

    Raises ParseError on invalid input.
    '''

    i = 0
    ln = None
    crc = None
    cmd = None

    if line[0] == 'N':  # numbered
        i = 1
        while line[i].isdigit():
            i += 1

        try:
            ln = int(line[1:i])
        except ValueError:
            raise ParseError('Line number is not integer: "{}", input: "{}"'
                             .format(line[1:i], line))

    sp = line[i:].strip().split('*')
    cmd = sp[0]
    if len(sp) == 2:  # with crc
        try:
            crc = int(sp[1])
        except ValueError:
            raise ParseError('CRC is not integer: "{}", input: "{}"'
                             .format(sp[1], line))

    return (cmd, ln, crc)
