import yaml
import os
import logging
from .milkarguments import MilkArguments
from .milktemplate import MilkTemplate
from .pluginloader import PluginLoader


class Milk:
    def __init__(self, arguments=None, config=None, loggingLevel=logging.INFO):

        # set logging level, TODO! add support for logging to file
        logging.basicConfig(level=loggingLevel)

        # create argument parser
        parser = MilkArguments(arguments=arguments)

        # load plugins from default location
        plugins = PluginLoader(os.path.join(os.path.dirname(__file__), "plugins"), loggingLevel=loggingLevel)

        # parse the yaml config file
        if config:
            self.parsed = yaml.load(config)
        else:
            with open(parser.args.config, "r") as f:
                self.parsed = yaml.load(f.read())


        # check for arguments and version config
        for item in list(self.parsed):
            if "argument" in item:
                parser.add_argument(**item["argument"])
                self.parsed.remove(item)

            elif "version" in item:
                self.configVersion = item["version"]
                self.parsed.remove(item)

        # verify the config version
        try:
            if self.configVersion:
                pass  # TODO! handle the config version properly
        except AttributeError:
            raise NoConfigVersionException()

        # parse user defined arguments
        parser.parse_args()

        # TODO! load plugins from current working dir

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

    # parse the jinja2 code if any
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


class NoConfigVersionException(Exception):
    pass
