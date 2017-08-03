
class MilkBase:
    milkglobals = {}

    def add_global(self, key, value):

            if key in self.milkglobals:
                raise Exception("Key '%s' already exists, overwriting is not an option!")

            self.milkglobals[key] = value

    def get_global(self, key):

        try:
            return self.milkglobals[key]
        except KeyError:
            # TODO! handle the KeyError better!
            raise

    def items(self):
        return self.milkglobals.items()
