#  Copyright (c) 2019.
#  Author: Sebastian Krahmer

# from ruamel.yaml import YAML
import yaml
import sys
current_module = sys.modules["UC2_grid_protection.cloud_setup.mconfig"]


def init(module):
    with open("mconfig.yaml", "r") as config:
        for elm, val in yaml.full_load(config).items():
            setattr(module, elm, val)


def print_config():
    with open("mconfig.yaml", "r") as config:
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

if __name__ == '__main__':
    print_config()
    # init(current_module)
