from milk.plugin import Plugin


class variables(Plugin):
    def __init__(self, config):
        for key, value in config.items():
            self.add_global(key, value)
