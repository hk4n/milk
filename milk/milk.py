import yaml
import os
import sys
import logging
from .milkarguments import MilkArguments
from .milkbase import MilkBase
from .milktemplate import MilkTemplate
from .pluginloader import PluginLoader


class MilkExceptions:
    supress = 100
    expose = 200


class Milk:
    def __init__(self, arguments=None, config=None, loggingLevel=logging.INFO, exceptions=MilkExceptions.expose):

        # set logging level, TODO! add support for logging to file and narrow the log printing to Milk and plugins only
        logging.basicConfig(format='%(message)s', level=loggingLevel)

        with MilkBase() as m:
            m.initialize()

        # create argument parser
        parser = MilkArguments(arguments=arguments)

        # load plugins from default location
        defaultPluginDir = os.path.join(os.path.dirname(__file__), "plugins")
        plugins = PluginLoader(defaultPluginDir, loggingLevel=loggingLevel)

        # parse the yaml config file
        if config:
            self.parsed = yaml.load(config)
            configDir = None
        else:
                if os.path.isfile(parser.args.config):
                    configDir = os.path.dirname(parser.args.config)
                    try:
                        with open(parser.args.config, "r") as f:
                            self.parsed = yaml.load(f.read())
                    except IOError as e:
                        print("Error: '%s' (%s)" % (e, parser.args.config))
                        sys.exit(1)

                else:
                    print("No config file found")
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

        # load custom user plugins
        self.load_plugins_from_working_dir(plugins)

        self.load_plugins_from_config_file_location(configDir, plugins)

        self.load_plugins_from_config(plugins)

        # remove config
        for item in list(self.parsed):
            if "config" in item:
                self.parsed.remove(item)
                break

        # execute the flow
        for item in self.parsed:
            key, value = item.popitem()

            # run jinja on the value variable
            value = self.jinja(value)

            # instantiate the plugin
            try:
                plugins.get_class(key)(config=value)
            except Exception as e:
                # implement cleanup
                if exceptions == MilkExceptions.supress:
                    logging.debug("Exception for plugin: %s config: %s" % (key, value))
                    logging.info("Error: %s" % e)
                    return
                else:
                    logging.debug("Exception for plugin: %s config: %s" % (key, value))
                    raise

    def load_plugins_from_working_dir(self, plugins):
        workingDir = os.getcwd()
        pluginDir = os.path.join(workingDir, "plugins")
        if os.path.isdir(pluginDir):
            plugins.load_plugins(pluginDir)

    def load_plugins_from_config_file_location(self, configDir, plugins):
        if configDir:
            pluginDir = os.path.join(configDir, "plugins")
            if os.path.isdir(pluginDir):
                plugins.load_plugins(pluginDir)

    def load_plugins_from_config(self, plugins):
        def makeAbs(location):
            if os.path.isabs(location):
                return location
            else:
                absLocation = os.path.join(os.getcwd(), location)
                if os.path.isdir(absLocation):
                    return absLocation
                else:
                    raise IOError("Plugin directory does not exist")

        for item in list(self.parsed):
            if "config" in item:
                if "plugin_locations" in item["config"]:
                    pluginLocations = item["config"]["plugin_locations"]
                    if type(pluginLocations) is list:
                        for loc in pluginLocations:
                            plugins.load_plugins(makeAbs(loc))
                    else:
                        plugins.load_plugins(makeAbs(pluginLocations))
                    break

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
