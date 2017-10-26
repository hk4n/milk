from milk.plugin import Plugin

import docker
import os
import logging


class image(Plugin):
    client = None

    def __init__(self, config):

        if self.client is None:
            self.client = docker.from_env(version='auto')

        if "build" in config:
            build(self.client, config["build"])

        elif "remove" in config:
            remove(self.client, config)


class build():
    def __init__(self, client, config):
        if "dockerfile" not in config:
            raise Exception("'dockerfile' is missing")

        if "tag" not in config:
            raise Exception("'tag' is missing")

        if not os.path.isabs(config["dockerfile"]):
            config["dockerfile"] = os.path.join(os.getcwd(), config["dockerfile"])

        if not os.path.isfile(config["dockerfile"]):
            raise Exception("'dockerfile' does not contain the correct path: %s " % config["dockerfile"])

        try:
            image = client.images.build(**config)
            logging.info("Created image '%s' id: %s" % (config["tag"], image.attrs["Id"]))
        except docker.errors.BuildError:
            raise


class remove():
    def __init__(self, client, config):
        image = config["remove"]
        config.pop("remove")
        try:
            client.images.remove(image=image, **config)
        except docker.errors.ImageNotFound:
            raise

        logging.info("Removed: %s" % image)
