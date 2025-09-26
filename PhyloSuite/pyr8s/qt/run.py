#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Entry point for Qt GUI"""

import sys
import multiprocessing
from . import main as qt_main

def main():
    # force spawning on linux for debugging
    multiprocessing.set_start_method('spawn')
    if len(sys.argv) <= 2:
        a = qt_main.show()
    else:
        print('Usage: pyr8s_qt NEXUS_FILE')
        print('Ex:    pyr8s_qt tests/legacy_1')
