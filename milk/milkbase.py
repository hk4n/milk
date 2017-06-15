
class MilkBase:
    milkglobals = {}

    def add_global(self, key, value):

            if key in self.milkglobals:
                raise Exception("Key '%s' already exists, overwriting is not an option!")

            self.milkglobals[key] = value

    def items(self):
        return self.milkglobals.items()
