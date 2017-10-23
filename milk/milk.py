import yaml
import os
import sys
import logging
from .milkarguments import MilkArguments
from .milkbase import MilkBase
from .milktemplate import MilkTemplate
from .pluginloader import PluginLoader


class Milk:
    def __init__(self, arguments=None, config=None, loggingLevel=logging.INFO):

        # set logging level, TODO! add support for logging to file and narrow the log printing to Milk and plugins only
        logging.basicConfig(level=loggingLevel)

        with MilkBase() as m:
            m.initialize()

        # create argument parser
        parser = MilkArguments(arguments=arguments)

        # load plugins from default location
        plugins = PluginLoader(os.path.join(os.path.dirname(__file__), "plugins"), loggingLevel=loggingLevel)

        # parse the yaml config file
        if config:
            self.parsed = yaml.load(config)
        else:
            try:
                if os.path.isfile(parser.args.config):

                    with open(parser.args.config, "r") as f:
                        self.parsed = yaml.load(f.read())

                else:
                    print("No config file found")
                    sys.exit(1)

            except IOError as e:
                print("Error: '%s' (%s)" % (e.strerror, parser.args.config))
                sys.exit(1)

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
                with MilkBase() as m:
                    m.add_global("milk", {"config": {"version": self.configVersion}})

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

    def jinja(self, item):
        """Recursivly parse the jinja2 code if any

        Args:
            item(any): this will be either and dict or list to recurse on or the value to parse the jinja2 syntax if any
        Returns:
            The jinja2 parsed item
        """
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
