from .milkbase import MilkBase
import argparse


class MilkArguments(MilkBase):

    def __init__(self, arguments=None):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument("-f", "--config", default="milk.yml", dest="config")

        self.usergroup = self.parser.add_argument_group(description="User defined arguments")

        self.args, self.reminder = self.parser.parse_known_args(args=arguments)

    def add_argument(self, **kwargs):

        option = []

        if "short_option" in kwargs:
            option.append(kwargs["short_option"])
            del kwargs["short_option"]

        if "long_option" in kwargs:
            option.append(kwargs["long_option"])
            del kwargs["long_option"]

        if len(option) == 2:
            self.usergroup.add_argument(option[0], option[1], **kwargs)
        elif len(option) == 1:
            self.usergroup.add_argument(option[0], **kwargs)
        else:
            import pprint
            pprint.pprint(kwargs)
            raise Exception("missing short_option or long_option")

    def parse_args(self):
        args = self.parser.parse_args(self.reminder)

        for key, value in vars(args).items():
            if key == 'config':
                continue

            print("adding '%s':'%s' to global" % (key, value))
            self.add_global(key, value)
