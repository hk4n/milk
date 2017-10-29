
class MilkBase:
    milkglobals = {}

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def initialize(self):
        MilkBase.milkglobals = {}

    def add_global(self, key, value):

            if key in self.milkglobals:
                raise Exception("Key '%s' already exists, overwriting is not an option!" % key)

            self.milkglobals[key] = value

    def get_milk_config(self, key):
        pass

    def update_milk_config(self, key):
        pass

    def get_global(self, key):

        try:
            return self.milkglobals[key]
        except KeyError:
            # TODO! handle the KeyError better!
            raise

    def items(self):
        return self.milkglobals.items()
