from milk.plugin import Plugin


class testplugin2(Plugin):
    def __init__(self, config):
        for key, value in config.items():
            print("%s: %s" % (key, value))
