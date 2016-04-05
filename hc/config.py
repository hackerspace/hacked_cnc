import os
import ConfigParser

version = "0.0"
bindir = "/usr/bin"
sysconfdir = "/etc"
prefix = "/usr"
datadir = "/usr/share"
libdir = "/usr/lib64"
homeconfig = os.path.expanduser("~/.hc/config")


def config_parser():
    config = ConfigParser.SafeConfigParser()
    config_list = [os.path.join(sysconfdir, "hc", "config"),
                   homeconfig]
    if "HC_CONFIG_FILE" in os.environ:
        config_list.append(os.path.expanduser(os.environ["HC_CONFIG_FILE"]))

    if "HC_MACH" in os.environ:
        config_list.append(homeconfig + "_" + os.environ["HC_MACH"])
    config.read(config_list)
    return config


def get(key):
    if key in CONFIG:
        return CONFIG[key]

    return None


def load():
    result = {}
    parser = config_parser()
    for section in parser.sections():
        for option in parser.options(section):

            value = parser.get(section, option)
            if value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
            elif '~' in value:
                value = os.path.expanduser(value)

            result[option.lower()] = value

    return result

# on import
CONFIG = load()
