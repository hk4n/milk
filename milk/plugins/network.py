from milk.plugin import Plugin
from milk.milkbase import MilkBase

import docker
import logging


class network(Plugin):
    client = None

    def __init__(self, config):

        if self.client is None:
            self.client = docker.from_env(version='auto')

        if "create" in config:
            create(self.client, config)

        elif "remove" in config:
            remove(self.client, config)


class create(MilkBase):
    def __init__(self, client, config):
        name = config["create"]
        config.pop("create")

        network = client.networks.create(name, **config)
        self.add_global("network_%s" % name, network)

        logging.info("Created network '%s' driver: %s" % (name, network.attrs["Driver"]))


class remove(MilkBase):
    def __init__(self, client, config):
        name = config["remove"]
        config.pop("remove")
        network = self.get_global("network_%s" % name)

        try:
            network.remove()
        except docker.errors.ImageNotFound:
            raise

        logging.info("Removed network: %s" % network.name)
