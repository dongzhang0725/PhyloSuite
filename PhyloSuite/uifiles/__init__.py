#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
description goes here
'''
import glob


class Commander(object):

    def __init__(self):
        pass


if __name__ == "__main__":
    import re
    import os
    import sys
    import argparse
    import logging

    # 得到脚本所在位置
    script_file_path = sys.argv[0]
    script_name = os.path.basename(script_file_path)
    scriptPath = os.path.abspath(os.path.dirname(script_file_path))
    scriptPath = "." if not scriptPath else scriptPath

    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s')
    #FileHandler
    file_handler = logging.FileHandler('%s.log' % os.path.splitext(script_name)[0], mode="w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    # StreamHandler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level=logging.DEBUG)
    logger.addHandler(stream_handler)

    listFiles = glob.glob(scriptPath + os.sep + "*.fas")


    def parameter():
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            prog='%s.py' % os.path.splitext(script_name)[0],
            description='',
            epilog=r'''
              ''')
        listFiles_ = [i for i in listFiles if "_reorder" not in i]
        parser.add_argument(
            '-f', dest='file', required=True, help='input file')
        parser.add_argument('-n', dest='num', help='the amount of the protein plus rRNA genes among mtDNA',
                            choices=[14, 15], default=14, type=int)
        parser.add_argument(
            "files", help='input file', default=listFiles_, nargs='*')
        parser.add_argument('-aa', dest='AA', help='generate AA sequence files (fasta) of individual PCGs',
                            default=False, action='store_true')
        myargs = parser.parse_args(sys.argv[1:])
        return myargs


    myargs = parameter()
    Commander()
    print("Done!")