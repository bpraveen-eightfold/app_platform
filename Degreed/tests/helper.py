import os
import sys


def resolve_app_path():
    dir = os.getcwd().replace("/tests", "")
    sys.path.insert(0, dir)
