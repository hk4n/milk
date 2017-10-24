import os
import inspect
import sys
import importlib
import logging
from .plugin import Plugin


class PluginLoader():
    classes = {}

    def __init__(self, path, loggingLevel=logging.INFO):
        self.path = path
        logging.basicConfig(level=loggingLevel)
        self.load_plugins(path)

    # this function handles the loading of an module from a file
    def load_module(self, filename):
        sys.path.append(os.path.dirname(filename))
        mname = os.path.splitext(os.path.basename(filename))[0]
        imported = importlib.import_module(mname)
        sys.path.pop()
        return imported

    def load_classes(self, current_module):
        classes = {}
        for key in dir(current_module):
            cls = getattr(current_module, key)

            if key == "Plugin" or not inspect.isclass(cls):
                continue

            if issubclass(cls, Plugin):
                classes[key] = cls
                logging.debug("loaded plugin '%s'" % key)

        return classes

    def load_plugins(self, path):
        modules = []
        files = os.listdir(path)
        files = [f for f in files if f.endswith(".py") and not f.endswith("__init__.py")]
        logging.debug(files)

        for f in files:
            modules.append(self.load_module(os.path.join(path, f)))

        for m in modules:
            self.classes.update(self.load_classes(m))

    def get_class(self, name):
        return self.classes[name]

    def find_plugins_folder(self):
        workdir = os.getcwd()
        files = os.listdir(workdir)
        if "plugins" in files:
            logging.debug("plugins folder found in : %s" % workdir)
            return os.path.join(workdir, "plugins")
        else:
            logging.debug("NO plugins folder found in : %s" % workdir)

    def _print_class_members(self, cls):
        import inspect
        res = inspect.getmembers(cls, predicate=inspect.ismethod)
        print(res)
