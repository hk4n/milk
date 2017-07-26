import yaml
import os
import logging
from .milkarguments import MilkArguments
from .pluginloader import PluginLoader


class Milk:
    def __init__(self, arguments=None, config=None):

        parser = MilkArguments(arguments=arguments)

        # load plugins from default location
        plugins = PluginLoader(os.path.join(os.path.dirname(__file__), "plugins"), level=logging.DEBUG)

        # parse the yaml config file
        if config:
            self.parsed = yaml.load(config)
        else:
            with open(parser.args.config, "r") as f:
                self.parsed = yaml.load(f.read())

        # debug print
        import pprint
        print("\n")
        pprint.pprint(self.parsed)

        # parse arguments
        for item in list(self.parsed):
            if "argument" in item:
                parser.add_argument(**item["argument"])

        # parse user defined arguments
        parser.parse_args()

        # load plugins from current working dir
        # plugins.find_plugins_folder()
        # plugins.load_plugins()

        # load plugins from supplied path in config file
        for item in self.parsed:
            if "config" in item and "plugin_path" in item:
                plugins.load_plugins(item["plugin_path"])
                break

        # parse container flow
        for item in self.parsed:

            if "container" in item:
                plugins.get_class("container")(item)

            if "follow" in item:
                plugins.get_class("follow")(item)

            if "remove" in item:
                plugins.get_class("remove")(item)

            if "copy_from" in item:
                plugins.get_class("copy_from")(item)
