from milk import Milk
from milk import MilkExceptions
import sys


def main():
    Milk(sys.argv[1:], exceptions=MilkExceptions.supress)
