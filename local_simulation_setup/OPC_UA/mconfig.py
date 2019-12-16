#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

# from ruamel.yaml import YAML
import yaml
import sys
current_module = sys.modules["UC2_grid_protection.SimulationSetup.OPC_UA.mconfig"]


def init(module):
    with open("OPC_UA/mconfig.yaml", "r") as config:
        for elm, val in yaml.full_load(config).items():
            setattr(module, elm, val)


def print_config():
    with open("OPC_UA/mconfig.yaml", "r") as config:
        for elm, val in yaml.full_load(config).items():
            print(elm + ":" + str(val))
    config.close()


# def save():
#     with open("mconfig.yaml", "w") as config:
#         mdict = {}
#         for num, attr in enumerate(dir(eval(current_module))):
#             mdict[attr] = getattr(current_module, attr)
#         yaml.dump(mdict, config)


init(current_module)
#########################################################################


# def init():
#     mdict = {'a':1, 'b':3}
#     f = open("mconfig.yaml", "w")
#     yaml.dump(mdict, f)
#     f.close()
#
#
# def add_property(name, value):
#     mdict = yaml.full_load(open("mconfig.yaml", "r"))
#     # mdict[name1] = value_1
#     mdict['TEST'] = '34'
#     yaml.dump(mdict)
#
#
# def get_property(name):
#     mdict = yaml.load(open("mconfig.yaml"))
#     return mdict[name]

###################################################################################

# # https://codereview.stackexchange.com/questions/186653/pyyaml-saving-data-to-yaml-files
# class Config(dict):
#     def __init__(self, filename, auto_dump=True):
#         self.filename = filename
#         self.auto_dump = auto_dump
#         self.changed = False
#         self.yaml = YAML()
#         self.yaml.preserve_quotes = True
#         # uncomment and adapt to your specific indentation
#         # self.yaml.indent(mapping=4, sequence=4, offset=2)
#         if os.path.isfile(filename):
#             with open(filename) as f:
#                 # use super here to avoid unnecessary write
#                 super(Config, self).update(self.yaml.load(f) or {})
#
#     def dump(self, force=False):
#         if not self.changed and not force:
#             return
#         with open(self.filename, "w") as f:
#             yaml.dump(self, f)
#         self.changed = False
#
#     def updated(self):
#         if self.auto_dump:
#             self.dump(force=True)
#         else:
#             self.changed = True
#
#     def __setitem__(self, key, value):
#         super(Config, self).__setitem__(key, value)
#         self.updated()
#
#     def __delitem__(self, key):
#         super(Config, self).__delitem__(key)
#         self.updated()
#
#     def update(self, kwargs):
#         super(Config, self).update(kwargs)
#         self.updated()


if __name__ == '__main__':
    print_config()
    # init(current_module)
