import os
import sys

level = 2

def out(output, debug_level=1):
    if debug_level >= level:
        print(output)
