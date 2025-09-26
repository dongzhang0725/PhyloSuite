#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Parse the nexus file given through the console"""

import sys
from . import parse

def main():
    if len(sys.argv) == 2:
        print(' ')
        a = parse.from_file(sys.argv[1], run=True)
    else:
        print('Usage: pyr8s NEXUS_FILE')
        print('Ex:    pyr8s tests/legacy_1')
