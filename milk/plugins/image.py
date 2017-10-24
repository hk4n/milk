from milk.plugin import Plugin

import docker
import os


class image(Plugin):
    client = None

    def __init__(self, config):

        if self.client is None:
            self.client = docker.from_env(version='auto')

        print(self.client)

        if "build" in config:
            build(self.client, config["build"])

        elif "remove" in config:
            remove(self.client, config["remove"])


class build():
    def __init__(self, client, config):
        print(client)
        print(config)
        if "dockerfile" not in config:
            raise Exception("'dockerfile' is missing")
        else:
            if not os.path.isabs(config["dockerfile"]):
                config["dockerfile"] = os.path.join(os.getcwd(), config["dockerfile"])

            if not os.path.isfile(config["dockerfile"]):
                raise Exception("'dockerfile' does not contain the correct path: %s " % config["dockerfile"])

        if "tag" not in config:
            raise Exception("'tag' is missing")

        try:
            print(client.images.build(**config))
        except docker.errors.BuildError as e:
            print(e)
            raise


class remove():
    def __init__(self, client, config):
        print("Removed: %s" % client.images.remove(image=config))
        # implement prune and force
