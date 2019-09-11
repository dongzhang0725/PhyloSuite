#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
description goes here
'''
import glob
import os
import sys
import re

# 得到脚本所在位置
script_file_path = sys.argv[0]
script_name = os.path.basename(script_file_path)
scriptPath = os.path.abspath(os.path.dirname(script_file_path))
scriptPath = "." if not scriptPath else scriptPath

listFiles = glob.glob(scriptPath + os.sep + "*.py")

listFiles.remove(scriptPath + os.sep + "correct_myRes.py")
listFiles.remove(scriptPath + os.sep + "myRes_rc.py")
listFiles.remove(scriptPath + os.sep + "__init__.py")

for file in listFiles:
    with open(file, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    if re.search(r"(?m)^import myRes_rc", content):
        content = re.sub(r"(?m)^import myRes_rc", "from uifiles import myRes_rc", content)
        with open(file, "w", encoding="utf-8") as f1:
            f1.write(content)
