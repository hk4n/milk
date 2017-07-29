import yaml
import os
import logging
from .milkarguments import MilkArguments
from .milktemplate import MilkTemplate
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
        # import pprint
        # print("\n")
        # pprint.pprint(self.parsed)

        # parse arguments
        for item in list(self.parsed):
            if "argument" in item:
                parser.add_argument(**item["argument"])

        i = 0
        for item in list(self.parsed):
            if "argument" in item:
                del self.parsed[i]
            i = i + 1

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

        # execute the flow
        for item in self.parsed:
            key, value = item.popitem()

            # run jinja on the value variable
            value = self.jinja(value)
            # instantiate the plugin
            plugins.get_class(key)(value)

    def jinja(self, item):
        # dict
        if type(item) is dict:
            for key, value in dict(item).items():
                item[key] = self.jinja(value)

        # list
        elif type(item) is list:
            i = 0
            for v in item:
                item[i] = self.jinja(v)
                i = i + 1

        # all other
        else:
            if item is not None and type(item) is not bool:
                template = MilkTemplate()
                item = template.render(item)

        return item
