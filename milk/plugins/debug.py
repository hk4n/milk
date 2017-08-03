from milk.plugin import Plugin
import sys


class debug(Plugin):
    def __init__(self, config):

        out = ""
        if "verbose" in config and "variable" in config:
            out += "%s: type: %s\n" % (config["variable"], type(self.get_global(config["variable"])))

        if "pretty" in config and "variable" in config:
            import pprint
            out += "%s: value: %s" % (config["variable"], pprint.pformat(self.get_global(config["variable"])))

        elif "variable" in config:
            out += "%s: value: %s" % (config["variable"], self.get_global(config["variable"]))

        elif "text" in config:
            out += "%s" % config["text"]

        sys.stdout.write(out)
        sys.stdout.write("\n")
        sys.stdout.flush()
