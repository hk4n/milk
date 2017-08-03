from jinja2 import Environment
from .milkbase import MilkBase


class MilkTemplate(MilkBase):

    def render(self, value):
        template = Environment().from_string(value)

        # init globals
        for k, v in self.items():
            template.globals[k] = v

        return template.render()
