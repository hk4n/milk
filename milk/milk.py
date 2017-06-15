import yaml
from .milkarguments import MilkArguments
from .plugins.container import container


class Milk:
    def __init__(self, arguments=None, config=None):

        parser = MilkArguments(arguments=arguments)

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
        i = 0
        for item in list(self.parsed):
            if "argument" in item:
                parser.add_argument(**item["argument"])
                i += 1

        # parse user defined arguments
        parser.parse_args()

        # parse container flow
        for item in self.parsed:
            if "container" in item:
                c = container(item["container"])
                c.execute(item)

            if "follow" in item:
                container('tmp').follow(item["follow"])

            if "remove" in item:
                container('tmp').remove(item)

            if "copy_from" in item:
                container('tmp').copy_from(item)
