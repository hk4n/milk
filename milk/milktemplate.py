from jinja2 import Template
from jinja2 import Environment
from .milkbase import MilkBase


class MilkTemplate(MilkBase):

    def render(self, value):
        #print(type(value))
        #import pprint
        #pprint.pprint(value)
        template = Environment().from_string(value)
        # template = Template(value)

        # init globals
        for k, v in self.items():
            template.globals[k] = v

        return template.render()
