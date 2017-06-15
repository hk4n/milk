from jinja2 import Template
from .milkbase import MilkBase


class MilkTemplate(MilkBase):

    def render(self, value):

        template = Template(value)

        # init globals
        for k, v in self.items():
            template.globals[k] = v

        return template.render()
