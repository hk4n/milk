from milk import Milk
import sys


def main():
    import pprint
    pprint.pprint(sys.argv)
    print(type(sys.argv))
    Milk(sys.argv[1:])
