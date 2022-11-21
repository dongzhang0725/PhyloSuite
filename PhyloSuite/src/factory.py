#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 所有类的工厂类
import glob
import traceback
import sys

import time

from Bio import Phylo

from ete3 import Tree

from src.CustomWidget import DetectItemWidget, DetectPopupGui, AnimationShadowEffect, NoteMessage, \
    NoteMessage_option, MyQProgressDialog, Inputbox_message, JobFinishMessageBox
import subprocess
import pickle
import os
import re
import copy
import zipfile
import shutil
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import QLocalSocket, QLocalServer, QNetworkReply
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from collections import OrderedDict, Counter
import csv
import platform

# from src.Lg_settings import Setting
from src.Lg_NCBI_DB import LG_NCBIdb
from src.plugins import dict_plugin_settings
from src.preset_values import init_sequence_type, preset_workflow
from uifiles.Ui_NCBI_db import Ui_NCBI_DB


class Factory_sub(object):

    def get_version(self, program, parent):
        if program == "IQ-TREE":
            command = f"\"{parent.iqtree_exe}\" -h"
            popen = self.init_popen(command)
            stdout = self.getSTDOUT(popen)
            rgx_version = re.compile(r"version (\d+\.\d+\.\d+)")
            if rgx_version.search(stdout):
                parent.version = rgx_version.search(stdout).group(1)
            else:
                parent.version = ""
        elif program == "ModelFinder":
            command = f"\"{parent.modelfinder_exe}\" -h"
            popen = self.init_popen(command)
            stdout = self.getSTDOUT(popen)
            rgx_version = re.compile(r"version (\d+\.\d+\.\d+)")
            if rgx_version.search(stdout):
                parent.version = rgx_version.search(stdout).group(1)
            else:
                parent.version = ""
        elif program == "FastTree":
            command = f"\"{parent.FastTreePath}\" -expert"
            popen = self.init_popen(command)
            stdout = self.getSTDOUT(popen)
            rgx_version = re.compile(r"FastTree (\d+\.\d+\.\d+)")
            if rgx_version.search(stdout):
                parent.version = rgx_version.search(stdout).group(1)
            else:
                parent.version = ""
        elif program == "ASTRAL":
            command = f"\"{parent.ASTRALPath}\" -h"
            popen = self.init_popen(command)
            stdout = self.getSTDOUT(popen)
            rgx_version = re.compile(r"Version: v(\d+\.\d+\.\d+\.\d+)")
            if rgx_version.search(stdout):
                parent.version = rgx_version.search(stdout).group(1)
            else:
                parent.version = ""
        elif program == "Gblocks":
            # 无效,需要关程序的时候才会有stdout。需要在一个新的线程里面获取才行，见https://stackoverflow.com/questions/19880190/interactive-input-output-using-python
            command = f"\"{parent.gb_exe}\""
            popen = self.init_popen(command)
            stdout = self.getSTDOUT(popen)
            # print(stdout)
            rgx_version = re.compile(r"GBLOCKS (\d+\.\d+b)")
            if rgx_version.search(stdout):
                parent.version = rgx_version.search(stdout).group(1)
            else:
                parent.version = ""
        elif program == "MAFFT":
            command = f"\"{parent.mafft_exe}\" -h"
            popen = self.init_popen(command)
            stdout = self.getSTDOUT(popen)
            rgx_version = re.compile(r"MAFFT v(\d+\.\d+)")
            if rgx_version.search(stdout):
                parent.version = rgx_version.search(stdout).group(1)
            else:
                parent.version = ""
        elif program == "trimAl":
            command = f"\"{parent.TApath}\" --version"
            popen = self.init_popen(command)
            stdout = self.getSTDOUT(popen)
            rgx_version = re.compile(r"trimAl (\d+\.\S+)")
            if rgx_version.search(stdout):
                parent.version = rgx_version.search(stdout).group(1)
            else:
                parent.version = ""
        elif program == "MrBayes":
            command = f"\"{parent.MB_exe}\" -v"
            popen = self.init_popen(command)
            stdout = self.getSTDOUT(popen)
            rgx_version = re.compile(r"MrBayes v(\d+\.\d+\.\d+\S*)")
            if rgx_version.search(stdout):
                parent.version = rgx_version.search(stdout).group(1)
            else:
                rgx_version = re.compile(r"Version:\s+(\d+\.\d+\.\d+\S*)")
                if rgx_version.search(stdout):
                    parent.version = rgx_version.search(stdout).group(1)
                else:
                    parent.version = ""
        elif program == "MACSE":
            command = f"\"{parent.java}\" -jar \"{parent.macseEXE}\" -h"
            popen = self.init_popen(command)
            stdout = self.getSTDOUT(popen)
            rgx_version = re.compile(r" MACSE V(\d+\.\d+)")
            if rgx_version.search(stdout):
                parent.version = rgx_version.search(stdout).group(1)
            else:
                parent.version = ""

    def zipFolder(self, file, list_folder):
        # shutil.make_archive(os.path.splitext(file)[0], "zip",
        #                     root_dir=os.path.relpath(list_folder[0]),
        #                     base_dir=os.path.basename(list_folder[0]))
        def zip_directory(folder_path, zipf):
            len_dir_path = len(folder_path)
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path,
                               os.path.basename(folder_path) + os.sep + file_path[len_dir_path:])
        # print(list_folder)
        with zipfile.ZipFile(file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder in list_folder:
                zip_directory(folder, zipf)

    def unzipFolder(self, zip_file, rootPath):
        file_zip = zipfile.ZipFile(zip_file, 'r')
        namelists = file_zip.namelist()
        for num, file in enumerate(namelists):
            path_root = rootPath + os.sep + file
            if os.path.exists(path_root):
                ##如果已经存在的文件夹就替换名字
                if os.path.basename(file):
                    try:
                        ##如果重命名失败，也不能移动文件，这里是可能造成更新失败的地方
                        os.rename(path_root, path_root + ".old")
                    except:
                        pass
            try:
                file_zip.extract(file, rootPath)
                if platform.system().lower() in ["darwin", "linux"]:
                    os.system("chmod 744 %s"%(rootPath + os.sep + file))
            except:
                pass
        file_zip.close()
        # 删除old files：在每次启动phylosuite的时候检测并删除

    def remove_old_files(self, folder):
        ##删除更新留下的旧文件
        def remove_path(path):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path, True)
            except:
                pass
        for path in glob.glob(folder + os.sep + "**" + os.sep + "*.old", recursive=True) + \
                    glob.glob(folder + os.sep + "**" + os.sep + ".*.old", recursive=True):
            remove_path(path)
        # if os.path.basename(folder) in ["settings", "plugins"]:
        #     for path in glob.glob(folder + os.sep + "**" + os.sep + "*.old", recursive=True) + \
        #         glob.glob(folder + os.sep + "**" + os.sep + ".*.old", recursive=True):
        #         # 隐藏文件需要".*.old"匹配
        #         remove_path(path)

    def read_fasta_to_dic(self, input_file_path, keep_name=True):
        dict_fas = {}
        seq_name = ""
        with open(input_file_path, errors="ignore", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(">"):
                    seq_name = line.replace(">", "")
                    seq_name = seq_name if keep_name else self.refineName(seq_name)
                else:
                    dict_fas.setdefault(seq_name, []).append(line)
            for key, value in dict_fas.items():
                dict_fas[key] = re.sub(r"\s", "", "".join(value))
        return dict_fas

    def is_plot_engine_ok(self):
        flag = False
        try:
            import plotly.express as px
            import plotly
            import pandas as pd
            flag = True
        except:
            flag = False
        return flag

    def get_PS_version(self):
        with open(self.thisPath + os.sep + "NEWS_version.md", encoding="utf-8") as f:
            content = f.read()
            current_version = re.search(
                r"## *PhyloSuite v([^ ]+?) \(", content)
        return current_version.group(1) if current_version else None

    def judge_NCBI_tax_database(self, parent=None):
        db_file = f"{self.thisPath}{os.sep}db{os.sep}NCBI{os.sep}taxa.sqlite"
        db_path = f"{self.thisPath}{os.sep}db{os.sep}NCBI"
        os.makedirs(db_path, exist_ok=True)
        if os.path.exists(db_file):
            return True
        else:
            reply = QMessageBox.information(
                parent,
                "Confirmation",
                "<p style='line-height:25px; height:25px'>First time using this function? "
                "Do you want to configure NCBI taxonomy database to"
                " enable this function? </p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.NCBIdb_window = LG_NCBIdb(db_file=db_file,
                                               db_path=db_path,
                                               parent=parent,
                                               thisPath=self.thisPath)
                self.NCBIdb_window.setWindowFlags(self.NCBIdb_window.windowFlags() |
                                                  Qt.WindowMinMaxButtonsHint)
                self.NCBIdb_window.show()
            else:
                return False
        return False

    def update_NCBI_tax_database(self, parent=None):
        db_file = f"{self.thisPath}{os.sep}db{os.sep}NCBI{os.sep}taxa.sqlite"
        db_path = f"{self.thisPath}{os.sep}db{os.sep}NCBI"
        self.NCBIdb_window = LG_NCBIdb(db_file=db_file,
                                       db_path=db_path,
                                       parent=parent,
                                       thisPath=self.thisPath)
        self.NCBIdb_window.setWindowFlags(self.NCBIdb_window.windowFlags() |
                                          Qt.WindowMinMaxButtonsHint)
        self.NCBIdb_window.show()

    def get_OS_bit(self):
        # 有时候用户下载的是32位版本的phylosuite
        os_bit = ""
        if not os.path.exists(f"{self.thisPath}{os.sep}os_bit"):
            os_bit = "64bit" if platform.machine().endswith('64') else "32bit"
        else:
            with open(f"{self.thisPath}{os.sep}os_bit", encoding="utf-8", errors="ignore") as f:
                os_bit = f.readline().rstrip()
        return os_bit

    def get_update_path(self):
        url = ""
        country = self.path_settings.value("country", "UK")
        os_bit = self.get_OS_bit()
        if country == "China":
            if platform.system().lower() == "windows":
                if os_bit == "64bit":
                    if self.is_plot_engine_ok():
                        url = "http://phylosuite.jushengwu.com/updates/update_plot_Win64.zip"
                    else:
                        url = "http://phylosuite.jushengwu.com/updates/update_Win64.zip"
                else:
                    if self.is_plot_engine_ok():
                        url = "http://phylosuite.jushengwu.com/updates/update_plot_Win32.zip"
                    else:
                        url = "http://phylosuite.jushengwu.com/updates/update_Win32.zip"
            elif platform.system().lower() == "darwin":
                if self.is_plot_engine_ok():
                    url = "http://phylosuite.jushengwu.com/updates/update_plot_Mac.zip"
                else:
                    url = "http://phylosuite.jushengwu.com/updates/update_Mac.zip"
            elif platform.system().lower() == "linux":
                url = "http://phylosuite.jushengwu.com/updates/update_linux.zip"
        else:
            if platform.system().lower() == "windows":
                if os_bit == "64bit":
                    if self.is_plot_engine_ok():
                        url = "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite/master/update_plot_Win64.zip"
                    else:
                        url = "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite/master/update_Win64.zip"
                else:
                    if self.is_plot_engine_ok():
                        url = "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite/master/update_plot_Win32.zip"
                    else:
                        url = "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite/master/update_Win32.zip"
            elif platform.system().lower() == "darwin":
                if self.is_plot_engine_ok():
                    url = "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_Mac/master/update_plot_Mac.zip"
                else:
                    url = "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_Mac/master/update_Mac.zip"
            elif platform.system().lower() == "linux":
                url = "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_linux/master/update_linux.zip"
        return url

class Factory(QObject, Factory_sub, object):

    def __init__(self, parent=None):
        super(Factory, self).__init__(parent)
        thisPath = os.path.dirname(os.path.abspath(os.path.dirname(sys.argv[0])))  #上一级目录
        thisPath = os.path.dirname(os.path.abspath(os.path.dirname(__file__))) if not os.path.exists(
            thisPath + os.sep + "style.qss") else thisPath
        QSettings.setDefaultFormat(QSettings.IniFormat)
        # print(QSettings().fileName()) # get the default path of ini file
        self.path_settings = QSettings()
        self.thisPath = self.path_settings.value("thisPath", thisPath)
        self.country = self.path_settings.value("country", "China")
        self.workPlaceSettingPath = self.path_settings.value("current workplace setting path", thisPath)
        self.settings_ini = QSettings(
            self.thisPath + '/settings/setting_settings.ini', QSettings.IniFormat)
        self.settings_ini.setFallbacksEnabled(False)
        self.dict_autoInputs = None

    def creat_dir(self, folder):  # 创建文件夹
        if not os.path.exists(folder):
            os.makedirs(folder)
        return folder

    def creat_dirs(self, folder):  # 创建多级文件夹
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        #     print("mkdir: %s"%folder)
        # else:
        #     print("exist folder:%s"%folder)
        return folder

    def remove_dir(self, path, parent=None, removeRoot=False):  # 强制删除路径
        # 有parent代表可以提醒
        if not os.path.exists(path):
            return
        filelist = os.listdir(path)
        mainwindow_settings = QSettings(
            self.thisPath +
            '/settings/mainwindow_settings.ini',
            QSettings.IniFormat, parent=self)
        mainwindow_settings.setFallbacksEnabled(False)
        ifPopRemoveRemind = mainwindow_settings.value(
            "ifPopRemoveRemind", "true")
        clear_results_bool = mainwindow_settings.value("clear_results", "yes")
        if self.str2bool(ifPopRemoveRemind) and parent and filelist:
            icon = ":/picture/resourses/msg_info.png"
            message = "Previous results found in \"%s\", you can choose to:" % (
                os.path.basename(path))
            remindinfo = "Do not remind again (also apply to other analyses)  "
            windInfo = NoteMessage_option(
                message, icon, checkboxText=remindinfo, parent=parent)
            windInfo.checkBox.clicked.connect(
                lambda bool_: mainwindow_settings.setValue("ifPopRemoveRemind", not bool_))
            if self.str2bool(clear_results_bool):
                windInfo.clearResults.setChecked(True)
            else:
                windInfo.retainResults.setChecked(True)
            windInfo.clearResults.toggled.connect(
                lambda bool_: mainwindow_settings.setValue("clear_results", bool_))
            if windInfo.exec_() != QDialog.Accepted:
                return False
            else:
                if windInfo.retainResults.isChecked():
                    # 如果用户选择保留结果，就不删除文件继续运行
                    return True
        else:
            if not self.str2bool(clear_results_bool):
                # 如果用户不显示删除文件的弹窗，并且用户选择的保留结果文件
                return True
        self.remove_dir_directly(path, removeRoot)
        # try:
        #     for f in filelist:
        #         filepath = os.path.join(path, f)
        #         if os.path.isfile(filepath):
        #             os.remove(filepath)
        #             #print(filepath+" removed!")
        #         elif os.path.isdir(filepath):
        #             shutil.rmtree(filepath, True)
        #             #print("dir "+filepath+" removed!")
        #     if removeRoot:
        #         shutil.rmtree(path)
        # except:
        #     pass
        return True

    def remove_dir_directly(self, path, removeRoot=False):
        if not os.path.exists(path):
            return
        filelist = os.listdir(path)
        try:
            for f in filelist:
                filepath = os.path.join(path, f)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    # print(filepath+" removed!")
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath, True)
                    # print("dir "+filepath+" removed!")
            if removeRoot:
                shutil.rmtree(path)
        except:
            pass


    def saveArgs(self, path, arg, filename):
        with open(path + os.sep + "%s.args" % filename, "wb", encoding="utf-8") as lginfile:
            pickle.dump(arg, lginfile)

    def readArgs(self, path, filename):
        file = path + os.sep + "%s.args" % filename
        if os.path.isfile(file):
            with open(file, "rb", encoding="utf-8") as pfile:
                return pickle.load(pfile)
        else:
            return None

    def read_file(self, file):  # 解决读取文件的时候的编码问题
        try:
            f = open(file, encoding="utf-8", errors='ignore')
            line = f.readline()
        except UnicodeDecodeError:
            # try:
            #     f = codecs.open(file, encoding="utf-8-sig", errors='ignore')  # 转为utf-8的无BOM格式
            #     line = f.readline()
            # except UnicodeDecodeError:
            f = open(file, encoding="gbk", errors='ignore')
            try:
                line = f.readline()
            except UnicodeDecodeError:
                # messagebox.showerror(
                #     "UnicodeDecodeError",
                #     "Undefined encoding!",
                #     parent=self.root)
                pass
        f.seek(0, 0)  # 回到起始读取位置
        return f

    def rmvGB(self, IDs, contents):
        # 将指定ID的序列从gb文件删除
        for i in IDs:
            rgx = re.compile(r"(?s)LOCUS       %s.+?//\s*?(?=LOCUS|$)" % i)
            contents = rgx.sub("", contents)
        return contents

    def extract(self, IDs, contents, advance=False, findRepeat=False, findValidated=False):
        gbExtract = ""
        restContents = contents
        restIDs = copy.deepcopy(IDs)
        extractIDs = []
        for i in IDs:
            rgx = re.compile(r"(?s)LOCUS       %s.+?//\s*?(?=LOCUS|$)" % i)
#             rgxSub = re.compile(r"(?s)LOCUS       %s.+?//\s*?(?=LOCUS|$)" % i)
            if rgx.search(contents):
                gbExtract += rgx.search(contents).group() + "\n\n"
                restContents = rgx.sub("", restContents)
                restIDs.remove(i)
                extractIDs.append(i)

        if advance:
            return gbExtract, restContents, restIDs
        elif findRepeat:
            return gbExtract, restContents, extractIDs
        elif findValidated:
            return restIDs, extractIDs
        else:
            return gbExtract

    # 替换正则pattern里面的特殊字符
    def repPattern(self, pattern):
        for i in "[]*.?+$^(){}|\/":
            pattern = pattern.replace(i, "[" + i + "]")
        return pattern

    def str2bool(self, v):
        if type(v) == bool:
            return v
        elif type(v) == str:
            return v.lower() in ("yes", "true", "t", "1", "2", "3")
        elif type(v) == int:
            return v > 0
        else:
            return False

    def refineName(self, name, remain_words="", limit=None):  # 替换名字的不识别符号
        if not remain_words:
            fefined_name = re.sub(r"\W", "_", name)
        else:
            # 用户指定的字母
            p = "\\" + "\\".join(list(remain_words))
            fefined_name = re.sub(
                r'[^a-zA-Z0-9_%s]'%p,
                '_',
                name)
        # remain
        if limit and len(fefined_name) > limit:
            # 存文件名字太长的时候会报错，limit即字数限制
            fefined_name = fefined_name[:limit - 1]
        return fefined_name

    def sort_error_report(self, content):
        list_content = sorted(content.split("\n"))
        return "\n".join(list_content).lstrip()

    def delete_all_files(self, path):
        # 删除路径下所有文件，留下folder
        folder_path = []
        for i in os.walk(path):
            folder_path.append(i[0].replace("/", "\\"))
            # 有文件时
            if i[-1] != []:
                for j in i[-1]:
                    os.remove(i[0] + os.sep + j)
        return folder_path

    def unZip(self, zip, target, errorSig):
        # 如果遇到2个不同文件夹，有同一个名字的文件，就麻烦，比如都有mafft.exe
        try:
            input_path = os.path.dirname(
                zip) if os.path.dirname(
                zip) else '.'
            file_zip = zipfile.ZipFile(zip, 'r')
            namelist = file_zip.namelist()
            self.topFolder = namelist[0].strip("/")
            self.exe_file = ""
            list_target = [target] if type(target) == str else target #有些软件有2种名字
            for file in file_zip.namelist():
                file_zip.extract(file, input_path)
                if (os.path.basename(file) in list_target) and os.path.isfile(input_path + os.sep + file):
                    self.exe_file = file
            file_zip.close()
            return self.topFolder, self.exe_file
        except:
            errorSig.emit(''.join(
                traceback.format_exception(*sys.exc_info())) + "\n")

    def ctrl_startButton_status(self, list_):
        button, progressbar, state, path, qss, parent = list_
        if (type(progressbar) != list) and progressbar.maximum()==0: progressbar.setMaximum(100)  # 取消busy状态
        if state == "start":
            button.setEnabled(False)  # 使之失效
            button.setStyleSheet(
                'QPushButton {color: red; background-color: rgb(219, 217, 217)}')
            button.setText("Running...")
        elif state == "except":
            button.setEnabled(True)
            button.setStyleSheet(qss)
            button.setText("Start")
            if type(progressbar) == list:
                for i in progressbar:
                    i.setProperty("value", 0)
            else:
                progressbar.setProperty("value", 0)
        elif state == "simple stop":
            button.setEnabled(True)
            button.setStyleSheet(qss)
            button.setText("Start")
        elif state == "workflow stop":
            button.setStyleSheet(qss)
            button.setText("Start")
        elif state == "stop":
            button.setEnabled(True)
            button.setStyleSheet(qss)
            button.setText("Start")
            dict_ = {
                "Extraction": ["Open the results folder", "Import the results to MAFFT", "Import the results to MACSE (for CDS)",
                               "Import the results to Draw RSCU figure", "Import the results to Draw gene order"],
                "MAFFT": ["Open the results folder", "Import the results to MACSE (for CDS)", "Import the results to Gblocks",
                          "Import the results to trimAl",
                          "Import the results to HmmCleaner", "Import the results to Convert Sequence Format",
                          "Import the results to Concatenate Sequence", "Import the results to FastTree"],
                "MACSE": ["Open the results folder", "Import the results to Gblocks", "Import the results to trimAl",
                          "Import the results to HmmCleaner",
                          "Import the results to Convert Sequence Format", "Import the results to Concatenate Sequence",
                          "Import the results to FastTree"],
                "Concatenation": ["Open the results folder", "Import the results to Gblocks", "Import the results to trimAl",
                                  "Import the results to HmmCleaner", "Import the results to IQ-TREE",
                                  "Import the results to ModelFinder", "Import the results to PartitionFinder2",
                                  "Import the results to FastTree"],
                "PartitionFinder2": ["Open the results folder", "Import the results to IQ-TREE", "Import the results to MrBayes"],
                "ModelFinder": ["Open the results folder", "Import the results to IQ-TREE",
                                "Import the results to MrBayes", "Import the results to FastTree"],
                "Gblocks": ["Open the results folder", "Import the results to Convert Sequence Format",
                            "Import the results to Concatenate Sequence", "Import the results to FastTree"],
                "trimAl": ["Open the results folder", "Import the results to Convert Sequence Format",
                           "Import the results to Concatenate Sequence", "Import the results to FastTree"],
                "HmmCleaner": ["Open the results folder", "Import the results to Convert Sequence Format",
                               "Import the results to Concatenate Sequence", "Import the results to FastTree"],
                "IQ-TREE": ["Open the results folder", "Import the results to TreeSuite",
                               "Import the results to ASTRAL"],
                "MrBayes": ["Open the results folder", "Import the results to TreeSuite"],
                "FastTree": ["Open the results folder", "Import the results to TreeSuite",
                             "Import the results to ASTRAL"]
            }
            if hasattr(parent, "function_name") and (parent.function_name in dict_):
                windInfo = JobFinishMessageBox(":/picture/resourses/msg_info.png", parent=parent)
                windInfo.refreshCombo(dict_[parent.function_name])
                if windInfo.exec_() == QDialog.Accepted:
                    selection = windInfo.combox.currentText()
                    if selection == "Open the results folder":
                        self.openPath(path, parent)
                    elif selection == "Import the results to MAFFT":
                        parent.parent.on_Mafft_triggered()
                    elif selection == "Import the results to MACSE (for CDS)":
                        parent.parent.on_MACSE_triggered()
                    elif selection == "Import the results to Gblocks":
                        parent.parent.on_actionGblocks_triggered()
                    elif selection == "Import the results to trimAl":
                        parent.parent.on_actiontrimAl_triggered()
                    elif selection == "Import the results to HmmCleaner":
                        parent.parent.on_actionHmmCleaner_triggered()
                    elif selection == "Import the results to Convert Sequence Format":
                        parent.parent.on_ConvertFMT_triggered()
                    elif selection == "Import the results to Concatenate Sequence":
                        parent.parent.on_Concatenate_triggered()
                    elif selection == "Import the results to ModelFinder":
                        parent.parent.on_actionModelFinder_triggered()
                    elif selection == "Import the results to PartitionFinder2":
                        parent.parent.on_actionPartitionFinder_triggered()
                    elif selection == "Import the results to IQ-TREE":
                        parent.parent.on_actionIQTREE_triggered()
                    elif selection == "Import the results to MrBayes":
                        parent.parent.on_actionMrBayes_triggered()
                    elif selection == "Import the results to Draw RSCU figure":
                        parent.parent.on_actionRSCUfig_triggered()
                    elif selection == "Import the results to Draw gene order":
                        parent.parent.on_actionDrawGO_triggered()
                    elif selection == "Import the results to TreeSuite":
                        parent.parent.on_TreeSuite_triggered()
                    elif selection == "Import the results to ASTRAL":
                        parent.parent.on_actionASTRAL_triggered()
                    elif selection == "Import the results to FastTree":
                        parent.parent.on_actionFastTree_triggered()
            else:
                reply = QMessageBox.information(
                    parent,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>Task completed! Open the results folder?        </p>",
                    QMessageBox.Ok,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.openPath(path, parent)
            if type(progressbar) == list:
                for i in progressbar:
                    i.setProperty("value", 0)
            else:
                progressbar.setProperty("value", 0)
        elif state.startswith("extract_no_feature"):
            button.setEnabled(True)
            button.setStyleSheet(qss)
            button.setText("Start")
            str_ids = state.replace("extract_no_feature", "")
            num_ids = len(str_ids.split(", "))
            msg = QMessageBox(parent)
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg.setIcon(QMessageBox.Information)
            msg.setText(
                "<p style='line-height:25px; height:25px'>Task completed (%d IDs with no features are ignored, see details)! Open the results folder?</p>"%num_ids)
            msg.setWindowTitle("Extraction")
            msg.setDetailedText("No features could be found in these IDs: " + str_ids)
            reply = msg.exec_()
            if reply == QMessageBox.Ok:
                self.openPath(path, parent)
            if type(progressbar) == list:
                for i in progressbar:
                    i.setProperty("value", 0)
            else:
                progressbar.setProperty("value", 0)
        elif state.startswith("warnings"):
            button.setEnabled(True)
            button.setStyleSheet(qss)
            button.setText("Start")
            warning_str = re.sub("^warnings", "", state)
            msg = QMessageBox(parent)
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg.setIcon(QMessageBox.Information)
            msg.setText(
                "<p style='line-height:25px; height:25px'>Task completed with warnings "
                "(see the warning file or click show details)! Open the results folder?</p>")
            msg.setWindowTitle("Warning")
            msg.setDetailedText(warning_str)
            reply = msg.exec_()
            if reply == QMessageBox.Ok:
                self.openPath(path, parent)
            if type(progressbar) == list:
                for i in progressbar:
                    i.setProperty("value", 0)
            else:
                progressbar.setProperty("value", 0)
        else:
            button.setEnabled(True)
            button.setStyleSheet(qss)
            button.setText("Start")
            msg = QMessageBox(parent)
            msg.setStandardButtons(QMessageBox.Ok)
            # msg.setStandardButtons(QMessageBox.Cancel)
            msg.setIcon(QMessageBox.Question)
            msg.setText(
                "<p style='line-height:25px; height:25px'>Task completed with error (see details)! </p>")
            msg.setWindowTitle("Error")
            msg.setDetailedText(state)
            msg.exec_()
            if type(progressbar) == list:
                for i in progressbar:
                    i.setProperty("value", 0)
            else:
                progressbar.setProperty("value", 0)

    def ctrl_installButton_status(self, list_):
        button, table, row, state, qss = list_
        startQSS = '''
        border-style:none;
        border:1px solid #B2B6B9;
        color:red;
        padding:5px;
        min-height:15px;
        border-radius:5px;
        background-color: rgb(219, 217, 217);
        background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #E1E4E6,stop:1 #CCD3D9);
        '''
        if state == "start":
            button.setEnabled(False)  # 使之失效
            button.setStyleSheet(startQSS)
            button.setText("Installing...")
        elif state == "cancel":
            button.setEnabled(True)
            button.setStyleSheet(qss)
            button.setIcon(
                QIcon(":/picture/resourses/Install.png"))
            button.setText("Install")
        elif state == "succeed":
            button.setEnabled(True)
            button.setStyleSheet(qss)
            button.setIcon(QIcon(":/picture/resourses/Uninstall.png"))
            button.setText("Uninstall")
            table.item(row, 2).setText("Installed")
            table.item(row, 2).setForeground(QBrush(QColor(57, 173, 0)))
        elif state == "uninstall":
            button.setEnabled(True)
            button.setStyleSheet(qss)
            table.item(row, 2).setText("Uninstalled")
            table.item(row, 2).setForeground(QBrush(Qt.red))
            button.setText("Install")
            button.setIcon(
                QIcon(":/picture/resourses/Install.png"))
            # button.setIconSize(QSize(25, 25))
        elif state == "not need":
            button.setEnabled(False)
            button.setStyleSheet(qss)
            table.item(row, 2).setText("Not needed")
            table.item(row, 2).setForeground(QBrush(Qt.black))
            button.setText("Not needed")

    def ctrl_file_label(self, label, state):
        if state == "finished":
            label.setText("file:")

    def numbered_Name(self, list_repeat_name_num, name, omit=False, suffix="_copy"):
        # 如果这个name已经记录在里面了, omit代表为1的时候省略
        if ((name + f"{suffix}1") in list_repeat_name_num) or (name in list_repeat_name_num):
            num = 2
            while True:
                numbered_name = f"{name}{suffix}{num}"
                if numbered_name not in list_repeat_name_num:
                    break
                num += 1
        else:
            numbered_name = name + f"{suffix}1" if not omit else name
        list_repeat_name_num.append(numbered_name)
        return numbered_name, list_repeat_name_num

    def myProgressDialog(self, title, label, busy=False, parent=None, rewrite=False):
        progressDialog = MyQProgressDialog(parent) if rewrite else QProgressDialog(parent)
        progressDialog.setWindowFlags(
            progressDialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        progressDialog.setWindowModality(Qt.WindowModal)
        # 太快了就不打开这个窗口
        progressDialog.setMinimumDuration(10)
        progressDialog.setWindowTitle(title)
        progressDialog.setLabelText(label)
        progressDialog.setCancelButtonText("Cancel")
        progressDialog.canceled.connect(progressDialog.close)
        # if busy:
        #     progressDialog.setStyleSheet('''QProgressBar{
        #                                     min-height:20px;
        #                                     background:#E1E4E6;
        #                                     border-radius:5px;
        #                                     text-align:center;
        #                                     border:1px solid #E1E4E6;
        #                                     }
        #
        #                                     QProgressBar:chunk{
        #                                     border-radius:5px;
        #                                     background-color:rgb(76, 169, 106);
        #                                     margin=0.5px;
        #                                     width=5px;
        #                                     }''')
        progressDialog.setMinimumWidth(260)
        if busy:
            # progressDialog.setMaximum(0)
            progressDialog.setMaximum(0)
        return progressDialog

    def int2word(self, n):
        """
        convert an integer number n into a string of english words
        """
        # break the number into groups of 3 digits using slicing
        # each group representing hundred, thousand, million, billion, ...
        ones = ["", "one ", "two ", "three ", "four ", "five ",
                "six ", "seven ", "eight ", "nine "]
        tens = ["ten ", "eleven ", "twelve ", "thirteen ", "fourteen ",
                "fifteen ", "sixteen ", "seventeen ", "eighteen ", "nineteen "]
        twenties = ["", "", "twenty ", "thirty ", "forty ",
                    "fifty ", "sixty ", "seventy ", "eighty ", "ninety "]
        thousands = ["", "thousand ", "million ", "billion ", "trillion ",
                     "quadrillion ", "quintillion ", "sextillion ", "septillion ", "octillion ",
                     "nonillion ", "decillion ", "undecillion ", "duodecillion ", "tredecillion ",
                     "quattuordecillion ", "quindecillion", "sexdecillion ", "septendecillion ",
                     "octodecillion ", "novemdecillion ", "vigintillion "]
        n3 = []
        r1 = ""
        # create numeric string
        ns = str(n)
        for k in range(3, 33, 3):
            r = ns[-k:]
            q = len(ns) - k
            # break if end of ns has been reached
            if q < -2:
                break
            else:
                if q >= 0:
                    n3.append(int(r[:3]))
                elif q >= -1:
                    n3.append(int(r[:2]))
                elif q >= -2:
                    n3.append(int(r[:1]))
            r1 = r
        # print n3  # test
        # break each group of 3 digits into
        # ones, tens/twenties, hundreds
        # and form a string
        nw = ""
        for i, x in enumerate(n3):
            b1 = x % 10
            b2 = (x % 100) // 10
            b3 = (x % 1000) // 100
            # print b1, b2, b3  # test
            if x == 0:
                continue  # skip
            else:
                t = thousands[i]
            if b2 == 0:
                nw = ones[b1] + t + nw
            elif b2 == 1:
                nw = tens[b1] + t + nw
            elif b2 > 1:
                nw = twenties[b2] + ones[b1] + t + nw
            if b3 > 0:
                nw = ones[b3] + "hundred " + nw
        return nw

    def write_csv_file(self, path, array, parent=None, silence=False, sep=","):
        try:
            if sep == ",":
                with open(path, 'w', newline='', encoding="utf-8") as csv_file:
                    writer = csv.writer(csv_file, dialect='excel')
                    # if head:
                    #     writer.writerow(head)
                    for row in array:
                        writer.writerow(row)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join([sep.join(i) for i in array]))
            if silence:
                return
            QMessageBox.information(
                parent,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>File saved successfully!</p>")
        except Exception as exception:
            rgx = re.compile(r"(?i)Permission.+?[\'\"](.+\.csv)[\'\"]")
            if (not silence) and rgx.search(str(exception)):
                csvfile = rgx.search(str(exception)).group(1)
                reply = QMessageBox.question(
                    parent,
                    "Error",
                    "<p style='line-height:25px; height:25px'>Please close '%s' file first!</p>" % os.path.basename(
                        csvfile),
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Yes and platform.system().lower() == "windows":
                    os.startfile(csvfile)
            else:
                print("Write an CSV file to path: %s, Case: %s" %
                      (path, exception))

    def is_aligned(self, dict_taxon):  # 判定序列是否比对过
        list_lenth = []
        d_ = {}
        for i in dict_taxon:
            list_lenth.append(len(dict_taxon[i]))
            d_[i] = len(dict_taxon[i])
        if len(set(list_lenth)) == 1:
            return True
        else:
            return False

    def is_aligned_file(self, file):  # 判定序列是否比对过
        dict_taxon = Parsefmt().readfile(file)
        list_lenth = []
        for i in dict_taxon:
            list_lenth.append(len(dict_taxon[i]))
        if len(set(list_lenth)) == 1:
            return True
        else:
            return False

    def fetchAlignmentFile(self, path):
        list_valid_exts = [
            ".FA", ".FAS", ".FASTA", ".PHY", ".PHYLIP", ".NEX", ".NXS", ".NEXUS"]
        return [path + os.sep + i for i in os.listdir(path) if os.path.splitext(i)[1].upper() in list_valid_exts]

    def fetchResuilts(self, rootpath, resuilts):
        gbPath = rootpath + os.sep + "GenBank_File"
        otherPath = rootpath + os.sep + "Other_File"
        gbMatch = [gbPath + os.sep + path1 + os.sep + resuilts
                   for path1 in os.listdir(gbPath)
                   if os.path.exists(gbPath + os.sep + path1 + os.sep + resuilts)]
        otherMatch = [otherPath + os.sep + path1 + os.sep + resuilts
                      for path1 in os.listdir(otherPath)
                      if os.path.exists(otherPath + os.sep + path1 + os.sep + resuilts)]
        return gbMatch + otherMatch

    def fetchSubResults(self, folder):
        return sorted([folder + os.sep + i for i in os.listdir(folder) if os.path.isdir(folder + os.sep + i)],
                      key=os.path.getmtime, reverse=True)

    def detectAvailableInputs(self, rootpath, mode=None):
        gbPath = rootpath + os.sep + "GenBank_File"
        otherPath = rootpath + os.sep + "Other_File"
        dict_autoInputs = OrderedDict()  # 每一个值的最后一项保存可用文件数目？
        if mode == "Concatenation":
            for mafftPath in self.fetchResuilts(rootpath, "mafft_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(mafftPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_mafft.[!log]*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(mafftPath)] = dict_subResults
            for macsePath in self.fetchResuilts(rootpath, "MACSE_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(macsePath):
                    autoInputs = glob.glob(subResults + os.sep + "*_NT_removed_chars.*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(macsePath)] = dict_subResults
            for gblocksPath in self.fetchResuilts(rootpath, "Gblocks_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(gblocksPath):
                    autoInputs = [subResults + os.sep + i for i in os.listdir(subResults)
                                  if os.path.splitext(i)[1].upper() == ".FASTA" and os.path.splitext(i)[0].endswith("_gb")]
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(gblocksPath)] = dict_subResults
            for trimAlPath in self.fetchResuilts(rootpath, "trimAl_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(trimAlPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_trimAl.*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(trimAlPath)] = dict_subResults
            for HmmCleanerPath in self.fetchResuilts(rootpath, "HmmCleaner_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(HmmCleanerPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_hmm.fasta")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(HmmCleanerPath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = self.fetchAlignmentFile(
                    otherPath + os.sep + each_path)
                list_alignments = [os.path.normpath(
                    alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                if list_alignments:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): list_alignments}
        elif mode == "format conversion":
            for mafftPath in self.fetchResuilts(rootpath, "mafft_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(mafftPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_mafft.[!log]*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(mafftPath)] = dict_subResults
            for macsePath in self.fetchResuilts(rootpath, "MACSE_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(macsePath):
                    autoInputs = glob.glob(subResults + os.sep + "*_NT_removed_chars.*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(macsePath)] = dict_subResults
            for gblocksPath in self.fetchResuilts(rootpath, "Gblocks_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(gblocksPath):
                    autoInputs = [subResults + os.sep + i for i in os.listdir(subResults)
                                  if os.path.splitext(i)[1].upper() == ".FASTA" and os.path.splitext(i)[0].endswith("_gb")]
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(gblocksPath)] = dict_subResults
            for trimAlPath in self.fetchResuilts(rootpath, "trimAl_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(trimAlPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_trimAl.*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(trimAlPath)] = dict_subResults
            for HmmCleanerPath in self.fetchResuilts(rootpath, "HmmCleaner_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(HmmCleanerPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_hmm.fasta")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(HmmCleanerPath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = self.fetchAlignmentFile(
                    otherPath + os.sep + each_path)
                list_alignments = [os.path.normpath(
                    alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                if list_alignments:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): list_alignments}
        elif mode == "Gblocks":
            for mafftPath in self.fetchResuilts(rootpath, "mafft_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(mafftPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_mafft.[!log]*")
                        # glob.glob(
                        # subResults + os.sep + "*.fas") + glob.glob(subResults + os.sep + "*.fasta")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(mafftPath)] = dict_subResults
            for macsePath in self.fetchResuilts(rootpath, "MACSE_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(macsePath):
                    autoInputs = glob.glob(subResults + os.sep + "*_NT_removed_chars.*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(macsePath)] = dict_subResults
            for concatenatePath in self.fetchResuilts(rootpath, "concatenate_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(concatenatePath):
                    autoInputs = glob.glob(subResults + os.sep + "*.fas") +\
                        glob.glob(subResults + os.sep + "*.fasta")
                    if autoInputs:
                        dict_subResults[
                            os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(concatenatePath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = self.fetchAlignmentFile(
                    otherPath + os.sep + each_path)
                list_alignments = [os.path.normpath(
                    alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                if list_alignments:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): list_alignments}
        elif mode == "trimAl":
            for mafftPath in self.fetchResuilts(rootpath, "mafft_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(mafftPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_mafft.[!log]*")
                        # glob.glob(
                        # subResults + os.sep + "*.fas") + glob.glob(subResults + os.sep + "*.fasta")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(mafftPath)] = dict_subResults
            for macsePath in self.fetchResuilts(rootpath, "MACSE_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(macsePath):
                    autoInputs = glob.glob(subResults + os.sep + "*_NT_removed_chars.*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(macsePath)] = dict_subResults
            for concatenatePath in self.fetchResuilts(rootpath, "concatenate_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(concatenatePath):
                    autoInputs = glob.glob(subResults + os.sep + "*.fas") +\
                        glob.glob(subResults + os.sep + "*.fasta")
                    if autoInputs:
                        dict_subResults[
                            os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(concatenatePath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = self.fetchAlignmentFile(
                    otherPath + os.sep + each_path)
                list_alignments = [os.path.normpath(
                    alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                if list_alignments:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): list_alignments}
        elif mode == "HmmCleaner":
            for mafftPath in self.fetchResuilts(rootpath, "mafft_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(mafftPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_mafft.[!log]*")
                        # glob.glob(
                        # subResults + os.sep + "*.fas") + glob.glob(subResults + os.sep + "*.fasta")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(mafftPath)] = dict_subResults
            for macsePath in self.fetchResuilts(rootpath, "MACSE_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(macsePath):
                    autoInputs = glob.glob(subResults + os.sep + "*_NT_removed_chars.*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(macsePath)] = dict_subResults
            for concatenatePath in self.fetchResuilts(rootpath, "concatenate_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(concatenatePath):
                    autoInputs = glob.glob(subResults + os.sep + "*.fas") +\
                        glob.glob(subResults + os.sep + "*.fasta")
                    if autoInputs:
                        dict_subResults[
                            os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(concatenatePath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = self.fetchAlignmentFile(
                    otherPath + os.sep + each_path)
                list_alignments = [os.path.normpath(
                    alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                if list_alignments:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): list_alignments}
        elif mode == "MAFFT":
            # 自动导入特殊一些
            for extractPath in self.fetchResuilts(rootpath, "extract_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(extractPath):
                    PCG_NUC_files, PCG_AA_files, RNAs_files = [], [], []
                    if os.path.exists(subResults + os.sep + "CDS_NUC"):
                        PCG_NUC_files = [
                            f"{subResults}/CDS_NUC/{i}"
                                for i in os.listdir(
                                subResults +
                                os.sep +
                                "CDS_NUC") if os.path.isfile(f"{subResults}/CDS_NUC/{i}")]
                    if os.path.exists(subResults + os.sep + "CDS_AA"):
                        PCG_AA_files = [
                            f"{subResults}/CDS_AA/{j}"
                            for j in os.listdir(
                                subResults +
                                os.sep +
                                "CDS_AA") if os.path.isfile(f"{subResults}/CDS_AA/{j}")]
                    if os.path.exists(subResults + os.sep + "RNAs"):
                        RNAs_files.extend([
                            f"{subResults}/RNAs/{k}"
                            for k in os.listdir(
                                subResults +
                                os.sep +
                                "RNAs") if os.path.isfile(f"{subResults}/RNAs/{k}")])
                    if os.path.exists(subResults + os.sep + "rRNA"):
                        RNAs_files.extend([
                            f"{subResults}/rRNA/{k}"
                            for k in os.listdir(
                                subResults +
                                os.sep +
                                "rRNA") if os.path.isfile(f"{subResults}/rRNA/{k}")])
                    if os.path.exists(subResults + os.sep + "tRNA"):
                        RNAs_files.extend([
                            f"{subResults}/tRNA/{k}"
                            for k in os.listdir(
                                subResults +
                                os.sep +
                                "tRNA") if os.path.isfile(f"{subResults}/tRNA/{k}")])
                    if glob.glob(subResults + os.sep + "*.fas"):
                        ##默认提取的情况
                        autoInputs = glob.glob(subResults + os.sep + "*.fas")
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                    elif PCG_AA_files or PCG_NUC_files or RNAs_files:
                        autoInputs = (PCG_NUC_files, PCG_AA_files, RNAs_files)
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(extractPath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = [os.path.normpath(
                                    alignment) for alignment in self.fetchAlignmentFile(
                                    otherPath + os.sep + each_path) if os.path.splitext(alignment)[1].upper()
                                                                       in [".FA", ".FASTA", ".FAS", ".FSA"]]
                if list_alignments:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): list_alignments}
        elif mode == "MACSE":
            # 自动导入特殊一些
            for extractPath in self.fetchResuilts(rootpath, "extract_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(extractPath):
                    PCG_NUC_files, CDS_files = [], []
                    if os.path.exists(subResults + os.sep + "CDS_NUC"):
                        #mitogenome
                        PCG_NUC_files = [
                            f"{subResults}/CDS_NUC/{i}"
                            for i in os.listdir(
                                subResults +
                                os.sep +
                                "CDS_NUC") if os.path.isfile(f"{subResults}/CDS_NUC/{i}")]
                    if os.path.exists(subResults + os.sep + "CDS"):
                        CDS_files = [
                            f"{subResults}/CDS/{i}"
                            for i in os.listdir(
                                subResults +
                                os.sep +
                                "CDS") if os.path.isfile(f"{subResults}/CDS/{i}")]
                    if PCG_NUC_files or CDS_files:
                        autoInputs = PCG_NUC_files + CDS_files
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(extractPath)] = dict_subResults
            for mafftPath in self.fetchResuilts(rootpath, "mafft_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(mafftPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_mafft.[!log]*")
                        # glob.glob(
                        # subResults + os.sep + "*.fas") + glob.glob(subResults + os.sep + "*.fasta")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(mafftPath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = [os.path.normpath(
                                    alignment) for alignment in self.fetchAlignmentFile(
                                    otherPath + os.sep + each_path) if os.path.splitext(alignment)[1].upper()
                                                                       in [".FA", ".FASTA", ".FAS", ".FSA"]]
                if list_alignments:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): list_alignments}
        elif mode == "PartitionFinder2":
            for concatenatePath in self.fetchResuilts(rootpath, "concatenate_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(concatenatePath):
                    if os.listdir(subResults):
                        dict_subResults[
                            os.path.normpath(subResults)] = subResults
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(concatenatePath)] = dict_subResults
        elif mode == "ModelFinder":
            for concatenatePath in self.fetchResuilts(rootpath, "concatenate_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(concatenatePath):
                    input_files = sorted([subResults + os.sep + i for i in os.listdir(subResults) if
                                   os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA", ".NEX", ".NEXUS",
                                                                      ".ALN"]], key=lambda x: ["F", "P", "A", "N"].index(os.path.splitext(x)[1][1].upper()))
                    input_file = input_files[0] if input_files else None
                    list_partition = [
                        subResults + os.sep + i for i in os.listdir(subResults) if i == "partition.txt"]
                    partition_file = list_partition[0] if list_partition else None
                    if input_file or partition_file:
                        dict_subResults[os.path.normpath(subResults)] = [
                            input_file, partition_file]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(concatenatePath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = self.fetchAlignmentFile(
                    otherPath + os.sep + each_path)
                list_alignments = [os.path.normpath(
                    alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                if list_alignments:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                            {os.path.normpath(otherPath + os.sep + each_path): [list_alignments, None]}
        elif mode == "IQ-TREE":
            for concatenatePath in self.fetchResuilts(rootpath, "concatenate_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(concatenatePath):
                    input_files = sorted([subResults + os.sep + i for i in os.listdir(subResults) if
                                   os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA", ".NEX", ".NEXUS",
                                                                      ".ALN"]], key=lambda x: ["F", "P", "A", "N"].index(os.path.splitext(x)[1][1].upper()))
                    input_MSA = input_files[0] if input_files else None
                    list_partition = [
                        subResults + os.sep + i for i in os.listdir(subResults) if i == "partition.txt"]
                    partition_file = list_partition[0] if list_partition else ""
                    model = ["CAT", partition_file] if os.path.exists(
                        partition_file) else ["", None]
                    if (model != ["", None]) or input_MSA:
                        dict_subResults[
                            os.path.normpath(subResults)] = [[input_MSA], model]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(concatenatePath)] = dict_subResults
            for MfPath in self.fetchResuilts(rootpath, "ModelFinder_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(MfPath):
                    list_msa = []
                    model = ["", None]
                    mf_part_model = None
                    for i in os.listdir(subResults):
                        if "best_scheme.nex" in i:
                            mf_part_model = subResults + os.sep + i
                        elif os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA", ".NEX", ".NEXUS",
                                                                ".NXS", ".ALN"]:
                            list_msa.append(subResults + os.sep + i)
                        elif os.path.splitext(i)[1].upper() == ".IQTREE":
                            model = ["MB_normal", subResults + os.sep + i]
                    model = [
                        "mf_part_model", mf_part_model] if mf_part_model else model
                    input_MSA = list_msa[0] if list_msa else None
                    if (model != ["", None]) or input_MSA:
                        dict_subResults[
                            os.path.normpath(subResults)] = [[input_MSA], model]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(MfPath)] = dict_subResults
            for PfPath in self.fetchResuilts(rootpath, "PartFind_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(PfPath):
                    input_MSAs = [subResults + os.sep + i for i in os.listdir(subResults) if
                                  os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP"]]
                    input_MSA = input_MSAs[0] if input_MSAs else None
                    path = subResults + os.sep + "analysis" + \
                        os.sep + "best_scheme.txt"
                    model = ["PF", path] if os.path.exists(path) else ["PF", None]
                    if (model != ["PF", None]) or input_MSA:
                        dict_subResults[
                            os.path.normpath(subResults)] = [[input_MSA], model]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(PfPath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = self.fetchAlignmentFile(
                    otherPath + os.sep + each_path)
                list_alignments = [os.path.normpath(
                    alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                if list_alignments:
                    dict_autoInputs[os.path.normpath(
                        otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): [list_alignments, ["", None]]}
        elif mode == "FastTree":
            for concatenatePath in self.fetchResuilts(rootpath, "concatenate_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(concatenatePath):
                    input_files = sorted([subResults + os.sep + i for i in os.listdir(subResults) if
                                          os.path.splitext(i)[1].upper() in [".FA", ".FAS", ".FASTA", ".PHY", ".PHYLIP"]],
                                         key=lambda x: ["F", "P"].index(os.path.splitext(x)[1][1].upper()))
                    input_MSA = input_files[0] if input_files else None
                    if input_MSA:
                        dict_subResults[
                            os.path.normpath(subResults)] = [[input_MSA], None]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(concatenatePath)] = dict_subResults
            for MfPath in self.fetchResuilts(rootpath, "ModelFinder_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(MfPath):
                    list_msa = []
                    model = None
                    for i in os.listdir(subResults):
                        if os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA"]:
                            list_msa.append(subResults + os.sep + i)
                        elif os.path.splitext(i)[1].upper() == ".IQTREE":
                            model = subResults + os.sep + i
                    input_MSA = list_msa[0] if list_msa else None
                    if input_MSA:
                        dict_subResults[
                            os.path.normpath(subResults)] = [[input_MSA], model]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(MfPath)] = dict_subResults
            for mafftPath in self.fetchResuilts(rootpath, "mafft_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(mafftPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_mafft.[!log]*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = [autoInputs, None]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(mafftPath)] = dict_subResults
            for macsePath in self.fetchResuilts(rootpath, "MACSE_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(macsePath):
                    autoInputs = glob.glob(subResults + os.sep + "*_NT_removed_chars.*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = [autoInputs, None]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(macsePath)] = dict_subResults
            for gblocksPath in self.fetchResuilts(rootpath, "Gblocks_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(gblocksPath):
                    autoInputs = [subResults + os.sep + i for i in os.listdir(subResults)
                                  if os.path.splitext(i)[1].upper() == ".FASTA" and os.path.splitext(i)[0].endswith("_gb")]
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = [autoInputs, None]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(gblocksPath)] = dict_subResults
            for trimAlPath in self.fetchResuilts(rootpath, "trimAl_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(trimAlPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_trimAl.*")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = [autoInputs, None]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(trimAlPath)] = dict_subResults
            for HmmCleanerPath in self.fetchResuilts(rootpath, "HmmCleaner_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(HmmCleanerPath):
                    autoInputs = glob.glob(subResults + os.sep + "*_hmm.fasta")
                    if autoInputs:
                        dict_subResults[os.path.normpath(subResults)] = [autoInputs, None]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(HmmCleanerPath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = self.fetchAlignmentFile(
                    otherPath + os.sep + each_path)
                list_alignments = [os.path.normpath(
                    alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                if list_alignments:
                    dict_autoInputs[os.path.normpath(
                        otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): [list_alignments, None]}
        elif mode == "MrBayes":
            for MfPath in self.fetchResuilts(rootpath, "ModelFinder_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(MfPath):
                    input_MSAs = [subResults + os.sep + i for i in os.listdir(subResults) if
                                  os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA", ".NEX", ".NEXUS",
                                                                     ".ALN"]]
                    input_MSA = input_MSAs[0] if input_MSAs else None
                    list_input_model_file = [subResults + os.sep + i for i in os.listdir(subResults) if
                                             os.path.splitext(i)[1].upper() == ".IQTREE"]
                    input_model_file = list_input_model_file[
                        0] if list_input_model_file else ""
                    list_part_model = [subResults + os.sep + i for i in os.listdir(subResults) if
                                       "best_scheme.nex" in i]
                    input_part_model = list_part_model[
                        0] if list_part_model else ""
                    if os.path.exists(input_part_model):
                        f = self.read_file(input_part_model)
                        input_model = f.read()
                    elif os.path.exists(input_model_file):
                        f = self.read_file(input_model_file)
                        model_content = f.read()
                        f.close()
                        rgx_model = re.compile(
                            r"Best-fit model according to.+?\: (.+)")
                        input_model = rgx_model.search(model_content).group(1)
                    else:
                        input_model = None
                    if input_model or input_MSA:
                        dict_subResults[
                            os.path.normpath(subResults)] = [input_MSA, input_model]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(MfPath)] = dict_subResults
            for PfPath in self.fetchResuilts(rootpath, "PartFind_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(PfPath):
                    input_MSAs = [subResults + os.sep + i for i in os.listdir(subResults) if
                                  os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP"]]
                    input_MSA = input_MSAs[0] if input_MSAs else None
                    rgx_blk = re.compile(r"(?si)begin mrbayes;(.+)end;")
                    if os.path.exists(subResults + os.sep + "analysis" + os.sep + "best_scheme.txt"):
                        f = self.read_file(
                            subResults + os.sep + "analysis" + os.sep + "best_scheme.txt")
                        scheme = f.read()
                        f.close()
                        input_model = rgx_blk.search(scheme).group(
                            1).strip().replace("\t", "")
                    else:
                        input_model = None
                    if input_model or input_MSA:
                        dict_subResults[
                            os.path.normpath(subResults)] = [input_MSA, input_model]
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(PfPath)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_alignments = self.fetchAlignmentFile(
                    otherPath + os.sep + each_path)
                list_alignments = [os.path.normpath(
                    alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                if list_alignments:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): [list_alignments, None]}
        elif mode == "parseANNT":
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_docx_files = [each_path + os.sep + i for i in os.listdir(otherPath + os.sep + each_path)
                                   if os.path.splitext(i)[1].upper() in [".DOCX", ".DOC", ".ODT", ".DOCM", ".DOTX", ".DOTM", ".DOT"]]
                if list_docx_files:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): list_docx_files}
        elif mode == "tree suite":
            for iq_path in self.fetchResuilts(rootpath, "IQtree_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(iq_path):
                    autoInputs = glob.glob(subResults + os.sep + "*.treefile")
                    log = f"{subResults}{os.sep}PhyloSuite_IQ-TREE.log"
                    if os.path.exists(log):
                        with open(log) as f:
                            content = f.read()
                    else:
                        content = ""
                    if content and re.search(r'\-s +\"([^"]+?)\"\W', content):
                        file_path = re.search(r'\-s +\"([^"]+?)\"\W', content).group(1)
                        file_name = os.path.basename(file_path)
                        alignments = glob.glob(f"{subResults}{os.sep}{file_name}")
                    else:
                        alignments = [os.path.splitext(tree)[0] for tree in autoInputs]
                    autoInputs = [autoInputs, alignments]
                    if autoInputs:
                        dict_subResults[
                            os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(iq_path)] = dict_subResults
            for mb_path in self.fetchResuilts(rootpath, "MrBayes_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(mb_path):
                    autoInputs = glob.glob(subResults + os.sep + "*.tre")
                    alignments = glob.glob(f"{subResults}{os.sep}[!stop_run]*.nex") + \
                                 glob.glob(f"{subResults}{os.sep}[!stop_run]*.nexus") + \
                                 glob.glob(f"{subResults}{os.sep}[!stop_run]*.nxs")
                                    # [subResults + os.sep + i for i in os.listdir(subResults) if
                                    # os.path.splitext(i)[1].upper() in [".NEX", ".NEXUS", "NXS"]]
                    autoInputs = [autoInputs, alignments]
                    if autoInputs:
                        dict_subResults[
                            os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(mb_path)] = dict_subResults
            for each_path in os.listdir(otherPath):
                # other file的自动导入
                if not os.path.isdir(otherPath + os.sep + each_path):
                    continue
                list_tree_files = [each_path + os.sep + i for i in os.listdir(otherPath + os.sep + each_path)
                                   if os.path.splitext(i)[1].upper() in [".TRE", ".TREEFILE", ".NWK", ".NEWICK"]]
                if list_tree_files:
                    dict_autoInputs[
                        os.path.normpath(otherPath + os.sep + each_path)] = \
                        {os.path.normpath(otherPath + os.sep + each_path): [list_tree_files, []]}
        elif mode == "ASTRAL":
            for iq_path in self.fetchResuilts(rootpath, "IQtree_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(iq_path):
                    autoInputs = glob.glob(subResults + os.sep + "all_gene_trees.nwk")
                    if autoInputs:
                        dict_subResults[
                            os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(iq_path)] = dict_subResults
            for ft_path in self.fetchResuilts(rootpath, "FastTree_results"):
                dict_subResults = OrderedDict()  # 按修改时间排序
                for subResults in self.fetchSubResults(ft_path):
                    autoInputs = glob.glob(subResults + os.sep + "all_gene_trees.nwk")
                    if autoInputs:
                        dict_subResults[
                            os.path.normpath(subResults)] = autoInputs
                if dict_subResults:
                    dict_autoInputs[os.path.normpath(ft_path)] = dict_subResults
        self.dict_autoInputs = dict_autoInputs
        return dict_autoInputs

    def judgeAutoInputs(self, mode=None, resultsPath=None):
        autoInputs = []
        if not resultsPath: return autoInputs
        resultsParentName = os.path.basename(os.path.dirname(resultsPath))
        if mode == "Concatenation":
            if resultsParentName == "mafft_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_mafft.[!log]*")
            if resultsParentName == "MACSE_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_NT_removed_chars.*")
            if resultsParentName == "Gblocks_results":
                autoInputs = [resultsPath + os.sep + i for i in os.listdir(resultsPath)
                              if
                              os.path.splitext(i)[1].upper() == ".FASTA" and os.path.splitext(i)[0].endswith("_gb")]
            if resultsParentName == "trimAl_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_trimAl.*")
            if resultsParentName == "HmmCleaner_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_hmm.fasta")
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File": # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = self.fetchAlignmentFile(resultsPath)
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                    if list_alignments: autoInputs = list_alignments
        elif mode == "format conversion":
            if resultsParentName == "mafft_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_mafft.[!log]*")
            if resultsParentName == "MACSE_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_NT_removed_chars.*")
            if resultsParentName == "Gblocks_results":
                autoInputs = [resultsPath + os.sep + i for i in os.listdir(resultsPath)
                                  if
                                  os.path.splitext(i)[1].upper() == ".FASTA" and os.path.splitext(i)[0].endswith("_gb")]
            if resultsParentName == "trimAl_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_trimAl.*")
            if resultsParentName == "HmmCleaner_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_hmm.fasta")
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File": # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = self.fetchAlignmentFile(resultsPath)
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                    if list_alignments: autoInputs = list_alignments
        elif mode == "Gblocks":
            if resultsParentName == "mafft_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_mafft.[!log]*")
                        # glob.glob(
                        # resultsPath + os.sep + "*.fas") + glob.glob(resultsPath + os.sep + "*.fasta")
            if resultsParentName == "MACSE_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_NT_removed_chars.*")
            if resultsParentName == "concatenate_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*.fas") + \
                                 glob.glob(resultsPath + os.sep + "*.fasta")
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File":  # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = self.fetchAlignmentFile(resultsPath)
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                    if list_alignments: autoInputs = list_alignments
        elif mode == "trimAl":
            if resultsParentName == "mafft_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_mafft.[!log]*")
                        # glob.glob(
                        # resultsPath + os.sep + "*.fas") + glob.glob(resultsPath + os.sep + "*.fasta")
            if resultsParentName == "MACSE_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_NT_removed_chars.*")
            if resultsParentName == "concatenate_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*.fas") + \
                                 glob.glob(resultsPath + os.sep + "*.fasta")
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File":  # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = self.fetchAlignmentFile(resultsPath)
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                    if list_alignments: autoInputs = list_alignments
        elif mode == "HmmCleaner":
            if resultsParentName == "mafft_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_mafft.[!log]*")
                        # glob.glob(
                        # resultsPath + os.sep + "*.fas") + glob.glob(resultsPath + os.sep + "*.fasta")
            if resultsParentName == "MACSE_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_NT_removed_chars.*")
            if resultsParentName == "concatenate_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*.fas") + \
                                 glob.glob(resultsPath + os.sep + "*.fasta")
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File":  # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = self.fetchAlignmentFile(resultsPath)
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                    if list_alignments: autoInputs = list_alignments
        elif mode == "MAFFT":
            # 自动导入特殊一些
            if resultsParentName == "extract_results":
                PCG_NUC_files, PCG_AA_files, RNAs_files = [], [], []
                if os.path.exists(resultsPath + os.sep + "CDS_NUC"):
                    PCG_NUC_files = [
                        f"{resultsPath}/CDS_NUC/{i}"
                        for i in os.listdir(
                            resultsPath +
                            os.sep +
                            "CDS_NUC") if os.path.isfile(f"{resultsPath}/CDS_NUC/{i}")]
                if os.path.exists(resultsPath + os.sep + "CDS_AA"):
                    PCG_AA_files = [
                        f"{resultsPath}/CDS_AA/{j}"
                        for j in os.listdir(
                            resultsPath +
                            os.sep +
                            "CDS_AA") if os.path.isfile(f"{resultsPath}/CDS_AA/{j}")]
                if os.path.exists(resultsPath + os.sep + "RNAs"):
                    RNAs_files.extend([
                        f"{resultsPath}/RNAs/{k}"
                        for k in os.listdir(
                            resultsPath +
                            os.sep +
                            "RNAs") if os.path.isfile(f"{resultsPath}/RNAs/{k}")])
                if os.path.exists(resultsPath + os.sep + "rRNA"):
                    RNAs_files.extend([
                        f"{resultsPath}/rRNA/{k}"
                        for k in os.listdir(
                            resultsPath +
                            os.sep +
                            "rRNA") if os.path.isfile(f"{resultsPath}/rRNA/{k}")])
                if os.path.exists(resultsPath + os.sep + "tRNA"):
                    RNAs_files.extend([
                        f"{resultsPath}/tRNA/{k}"
                        for k in os.listdir(
                            resultsPath +
                            os.sep +
                            "tRNA") if os.path.isfile(f"{resultsPath}/tRNA/{k}")])
                if glob.glob(resultsPath + os.sep + "*.fas"):
                    ##默认提取的情况
                    autoInputs = glob.glob(resultsPath + os.sep + "*.fas")
                elif PCG_AA_files or PCG_NUC_files or RNAs_files:
                    autoInputs = (PCG_NUC_files, PCG_AA_files, RNAs_files)
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File":  # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in self.fetchAlignmentFile(resultsPath)
                        if os.path.splitext(alignment)[1].upper() in [".FA", ".FASTA", ".FAS", ".FSA"]]
                    if list_alignments:
                        autoInputs = list_alignments
        elif mode == "MACSE":
            # 自动导入特殊一些
            if resultsParentName == "extract_results":
                PCG_NUC_files, CDS_files, single_gene_files = [], [], []
                if os.path.exists(resultsPath + os.sep + "CDS_NUC"):
                    # mitogenome
                    PCG_NUC_files = [
                        f"{resultsPath}/CDS_NUC/{i}"
                        for i in os.listdir(
                            resultsPath +
                            os.sep +
                            "CDS_NUC") if os.path.isfile(f"{resultsPath}/CDS_NUC/{i}")]
                if os.path.exists(resultsPath + os.sep + "CDS"):
                    CDS_files = [
                        f"{resultsPath}/CDS/{i}"
                        for i in os.listdir(
                            resultsPath +
                            os.sep +
                            "CDS") if os.path.isfile(f"{resultsPath}/CDS/{i}")]
                if glob.glob(resultsPath + os.sep + "*.fas"):
                    ##默认提取的情况
                    autoInputs = glob.glob(resultsPath + os.sep + "*.fas")
                if PCG_NUC_files or CDS_files or single_gene_files:
                    autoInputs = PCG_NUC_files + CDS_files + single_gene_files
            if resultsParentName == "mafft_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_mafft.[!log]*")
                        # glob.glob(
                        # resultsPath + os.sep + "*.fas") + glob.glob(resultsPath + os.sep + "*.fasta")
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File":  # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in self.fetchAlignmentFile(
                        resultsPath) if os.path.splitext(alignment)[1].upper()
                                                           in [".FA", ".FASTA", ".FAS", ".FSA"]]
                    if list_alignments: autoInputs = list_alignments
        elif mode == "PartitionFinder2":
            if resultsParentName == "concatenate_results":
                if os.listdir(resultsPath): autoInputs = resultsPath
        elif mode == "ModelFinder":
            if resultsParentName == "concatenate_results":
                input_files = sorted([resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                                      os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA",
                                                                         ".NEX", ".NEXUS",
                                                                         ".ALN"]],
                                     key=lambda x: ["F", "P", "A", "N"].index(os.path.splitext(x)[1][1].upper()))
                input_file = input_files[0] if input_files else None
                list_partition = [
                    resultsPath + os.sep + i for i in os.listdir(resultsPath) if i == "partition.txt"]
                partition_file = list_partition[0] if list_partition else None
                if input_file or partition_file: autoInputs = [input_file, partition_file]
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File":  # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = self.fetchAlignmentFile(resultsPath)
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                    if list_alignments: autoInputs = [list_alignments, None]
        elif mode == "IQ-TREE":
            if resultsParentName == "concatenate_results":
                input_files = sorted([resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                                      os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA",
                                                                         ".NEX", ".NEXUS",
                                                                         ".ALN"]],
                                     key=lambda x: ["F", "P", "A", "N"].index(os.path.splitext(x)[1][1].upper()))
                input_MSA = input_files[0] if input_files else None
                list_partition = [
                    resultsPath + os.sep + i for i in os.listdir(resultsPath) if i == "partition.txt"]
                partition_file = list_partition[0] if list_partition else ""
                model = ["CAT", partition_file] if os.path.exists(
                    partition_file) else ["", None]
                if (model != ["", None]) or input_MSA: autoInputs = [[input_MSA], model]
            if resultsParentName == "ModelFinder_results":
                list_msa = []
                model = ["", None]
                mf_part_model = None
                for i in os.listdir(resultsPath):
                    if "best_scheme.nex" in i:
                        mf_part_model = resultsPath + os.sep + i
                    elif os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA", ".NEX", ".NEXUS",
                                                            ".NXS", ".ALN"]:
                        list_msa.append(resultsPath + os.sep + i)
                    elif os.path.splitext(i)[1].upper() == ".IQTREE":
                        model = ["MB_normal", resultsPath + os.sep + i]
                model = [
                    "mf_part_model", mf_part_model] if mf_part_model else model
                input_MSA = list_msa[0] if list_msa else None
                if (model != ["", None]) or input_MSA: autoInputs = [[input_MSA], model]
            if resultsParentName == "PartFind_results":
                input_MSAs = [resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                              os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP"]]
                input_MSA = input_MSAs[0] if input_MSAs else None
                path = resultsPath + os.sep + "analysis" + \
                       os.sep + "best_scheme.txt"
                model = ["PF", path] if os.path.exists(path) else ["PF", None]
                if (model != ["PF", None]) or input_MSA: autoInputs = [[input_MSA], model]
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File":  # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = self.fetchAlignmentFile(resultsPath)
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                    if list_alignments: autoInputs = [list_alignments, ["", None]]
        elif mode == "FastTree":
            if resultsParentName == "concatenate_results":
                input_files = sorted([resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                                      os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA"]],
                                     key=lambda x: ["F", "P"].index(os.path.splitext(x)[1][1].upper()))
                input_MSA = input_files[0] if input_files else None
                model = ""
                if input_MSA:
                    autoInputs = [[input_MSA], model]
            if resultsParentName == "ModelFinder_results":
                list_msa = []
                model = ""
                for i in os.listdir(resultsPath):
                    if os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA"]:
                        list_msa.append(resultsPath + os.sep + i)
                    elif os.path.splitext(i)[1].upper() == ".IQTREE":
                        model = resultsPath + os.sep + i
                input_MSA = list_msa[0] if list_msa else None
                if input_MSA:
                    autoInputs = [[input_MSA], model]
            if resultsParentName == "mafft_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_mafft.[!log]*")
                autoInputs = [autoInputs, None]
            if resultsParentName == "MACSE_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_NT_removed_chars.*")
                autoInputs = [autoInputs, None]
            if resultsParentName == "Gblocks_results":
                autoInputs = [resultsPath + os.sep + i for i in os.listdir(resultsPath)
                              if
                              os.path.splitext(i)[1].upper() == ".FASTA" and os.path.splitext(i)[0].endswith("_gb")]
                autoInputs = [autoInputs, None]
            if resultsParentName == "trimAl_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_trimAl.*")
                autoInputs = [autoInputs, None]
            if resultsParentName == "HmmCleaner_results":
                autoInputs = glob.glob(resultsPath + os.sep + "*_hmm.fasta")
                autoInputs = [autoInputs, None]
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File":  # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = self.fetchAlignmentFile(resultsPath)
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                    if list_alignments:
                        autoInputs = [list_alignments, ""]
        elif mode == "MrBayes":
            if resultsParentName == "ModelFinder_results":
                input_MSAs = [resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                              os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FA", ".FAS", ".FASTA", ".NEX",
                                                                 ".NEXUS",
                                                                 ".ALN"]]
                input_MSA = input_MSAs[0] if input_MSAs else None
                list_input_model_file = [resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                                         os.path.splitext(i)[1].upper() == ".IQTREE"]
                input_model_file = list_input_model_file[
                    0] if list_input_model_file else ""
                list_part_model = [resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                                   "best_scheme.nex" in i]
                input_part_model = list_part_model[
                    0] if list_part_model else ""
                if os.path.exists(input_part_model):
                    f = self.read_file(input_part_model)
                    input_model = f.read()
                elif os.path.exists(input_model_file):
                    f = self.read_file(input_model_file)
                    model_content = f.read()
                    f.close()
                    rgx_model = re.compile(
                        r"Best-fit model according to.+?\: (.+)")
                    input_model = rgx_model.search(model_content).group(1)
                else:
                    input_model = None
                if input_model or input_MSA: autoInputs = [input_MSA, input_model]
            if resultsParentName == "PartFind_results":
                input_MSAs = [resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                              os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP"]]
                input_MSA = input_MSAs[0] if input_MSAs else None
                rgx_blk = re.compile(r"(?si)begin mrbayes;(.+)end;")
                if os.path.exists(resultsPath + os.sep + "analysis" + os.sep + "best_scheme.txt"):
                    f = self.read_file(
                        resultsPath + os.sep + "analysis" + os.sep + "best_scheme.txt")
                    scheme = f.read()
                    f.close()
                    input_model = rgx_blk.search(scheme).group(
                        1).strip().replace("\t", "")
                else:
                    input_model = None
                if input_model or input_MSA: autoInputs = [input_MSA, input_model]
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File":  # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_alignments = self.fetchAlignmentFile(resultsPath)
                    list_alignments = [os.path.normpath(
                        alignment) for alignment in list_alignments if self.is_aligned_file(alignment)]  # 只要比对过的
                    if list_alignments: autoInputs = [list_alignments, None]
        elif mode == "parseANNT":
            if os.path.basename(os.path.dirname(resultsPath)) == "Other_File":  # 这里的resultsPath类似于Other_File下面的files
                # other file的自动导入
                if os.path.isdir(resultsPath):
                    list_docx_files = [resultsPath + os.sep + i for i in os.listdir(resultsPath)
                                       if os.path.splitext(i)[1].upper() in [".DOCX", ".DOC", ".ODT", ".DOCM", ".DOTX",
                                                                             ".DOTM", ".DOT"]]
                    if list_docx_files: autoInputs = list_docx_files
        elif mode == "RSCU":
            if resultsParentName == "extract_results":
                stack_files = glob.glob(f"{resultsPath}{os.sep}StatFiles{os.sep}RSCU{os.sep}*_stack.csv")
                allStack = f"{resultsPath}{os.sep}StatFiles{os.sep}RSCU{os.sep}all_AA_stack.csv"
                if os.path.exists(allStack):
                    stack_files.remove(allStack)
                autoInputs = stack_files
        elif mode == "drawGO":
            if resultsParentName == "extract_results":
                autoInputs = glob.glob(
                    resultsPath + os.sep + f"files{os.sep}linear_order.txt")
                # autoInputs += glob.glob(
                #     resultsPath + os.sep + "files\\linear_order.txt")
                # autoInputs += glob.glob(
                #     resultsPath + os.sep + "files\\linear_order.txt")
                # autoInputs += glob.glob(
                #     resultsPath + os.sep + "files\\linear_order.txt")
        elif mode == "compare_table":
            if resultsParentName == "extract_results":
                files = glob.glob(
                    resultsPath + os.sep + f"StatFiles{os.sep}speciesSTAT{os.sep}*.csv")
                orgFiles = [i for i in files if "_org" in i]
                autoInputs = orgFiles
        elif mode == "tree suite":
            if resultsParentName == "MrBayes_results":
                input_trees = [resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                              os.path.splitext(i)[1].upper() in [".TRE"]]
                alignments = glob.glob(f"{resultsPath}{os.sep}[!stop_run]*.nex") + \
                             glob.glob(f"{resultsPath}{os.sep}[!stop_run]*.nexus") + \
                             glob.glob(f"{resultsPath}{os.sep}[!stop_run]*.nxs")
                            # [resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                            #   os.path.splitext(i)[1].upper() in [".NEX", ".NEXUS", "NXS"]]
                autoInputs = [input_trees, alignments]
            elif resultsParentName == "IQtree_results":
                input_trees = [resultsPath + os.sep + i for i in os.listdir(resultsPath) if
                               os.path.splitext(i)[1].upper() in [".TREEFILE"]]
                log = f"{resultsPath}{os.sep}PhyloSuite_IQ-TREE.log"
                if os.path.exists(log):
                    with open(log) as f:
                        content = f.read()
                else:
                    content = ""
                if content and re.search(r'\-s +\"([^"]+?)\"\W', content):
                    file_path = re.search(r'\-s +\"([^"]+?)\"\W', content).group(1)
                    file_name = os.path.basename(file_path)
                    alignments = glob.glob(f"{resultsPath}{os.sep}{file_name}")
                else:
                    alignments = [os.path.splitext(tree)[0] for tree in input_trees]
                autoInputs = [input_trees, alignments]
        elif mode == "ASTRAL":
            if resultsParentName in ["IQtree_results", "FastTree_results"]:
                input_trees = [resultsPath + os.sep + "all_gene_trees.nwk"] if \
                    os.path.exists(resultsPath + os.sep + "all_gene_trees.nwk") else []
                autoInputs = input_trees
        if not autoInputs:
            #["ModelFinder", "IQ-TREE", "MrBayes"]: [list_alignments, None]；IQ-TREE：[list_alignments, ["", None]]
            if mode in ["ModelFinder", "MrBayes", "FastTree"]:
                autoInputs = [None, None]
            elif mode == "IQ-TREE":
                autoInputs = [None, ["", None]]
        return autoInputs

    def popUpAutoDetect(self, mode, currentPath, auto_popSig, parent, dict_autoInputs=None):
        # 先找到rootpath
        rootPath = currentPath.split("GenBank_File")[0] \
            if "GenBank_File" in currentPath else currentPath.split("Other_File")[0]
        rootPath = rootPath.rstrip(r"/").rstrip(os.sep)
        if not dict_autoInputs:
            gbWorker = WorkThread(lambda: self.detectAvailableInputs(rootPath, mode),
                                  parent=parent)
            self.progressDialog_search = self.myProgressDialog(
                "Please Wait", "Searching for inputs...", busy=True, parent=parent, rewrite=True)
            self.progressDialog_search.show()
            self.popupAuto_break = False
            self.progressDialog_search.canceled.connect(lambda: [setattr(self, "popupAuto_break", True),
                                                          gbWorker.stopWork])
            def work_finish(mode, rootPath, parent, auto_popSig):
                # self.progressDialog_search.close()  # close会调用canceled这个信号,所以重写了QProgressDialog的closeEvent
                if not self.popupAuto_break:
                    self.popUpAutoDetectSub(mode, rootPath, parent, auto_popSig, self.dict_autoInputs)
            gbWorker.start()
            gbWorker.finished.connect(lambda: work_finish(mode, rootPath, parent,
                                                          auto_popSig))
        else:
            self.popUpAutoDetectSub(mode, rootPath, parent, auto_popSig, dict_autoInputs)

    def popUpAutoDetectSub(self, mode, rootPath, parent, auto_popSig=None, dict_autoInputs=None):
        if dict_autoInputs:
            # 这里造一个带有qlistwidget的dialog
            popupGui = DetectPopupGui(mode, parent)
            list_paths = sorted(
                list(dict_autoInputs), key=lambda x: os.path.basename(x))
            for path in list_paths:
                listItemWidget = DetectItemWidget(path, rootPath, parent, dict_autoInputs[path])
                listItemWidget.autoInputs = next(iter(dict_autoInputs[path].items()))[1]  # 最近修改的
                listwitem = QListWidgetItem(popupGui.listWidget_framless)
                listwitem.setToolTip(
                    '<br><span style="color: green">&#9733;Double-click to open folder</span></body></html>    ')
                listwitem.setSizeHint(listItemWidget.sizeHint())
                popupGui.listWidget_framless.addItem(listwitem)
                popupGui.listWidget_framless.setItemWidget(
                    listwitem, listItemWidget)
            popupGui.listWidget_framless.setFocus()
            popupGui.listWidget_framless.item(0).setSelected(True)
            popupGui.listWidget_framless.setCurrentRow(0)
            # popupGui.listWidget_framless.itemWidget(popupGui.listWidget_framless.item(0)).setFocus()
            popupGui.listWidget_framless.itemDoubleClicked.connect(lambda item: self.openPath(
                popupGui.listWidget_framless.itemWidget(item).pathText, parent))
            # 添加最大化按钮
            popupGui.setWindowFlags(
                popupGui.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.progressDialog_search.close() # close会调用canceled这个信号,所以重写了QProgressDialog的closeEvent
            auto_popSig.emit(popupGui)
        else:
            self.progressDialog_search.close()
            auto_popSig.emit(None)

    def popupViewMenu(self, view, point):
        if view.indexAt(point).isValid():
            view.exec_(QCursor.pos())

    def programIsValid(self, program, mode="settings"):
        # 由存的文件里面读取
        if program == "python27":
            PyPath = self.settings_ini.value('python27', "python")
            PyPath = "python" if not PyPath else PyPath  # 有时候路径为空
            try:
                popen = subprocess.Popen(
                    "%s -V" % PyPath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            except:
                return "uninstall" if mode == "settings" else False
            stdout = self.getSTDOUT(popen)
            if re.search(r"python\s+?2\.[3-7]\.", stdout, re.I):
                # 判断是python 2.3-2.7的版本
                self.settings_ini.setValue("python27", PyPath)  ##设置一遍，不然workflow报错
                return "succeed" if mode == "settings" else PyPath
        elif program == "RscriptPath":
            RscriptPath = self.settings_ini.value('RscriptPath', "Rscript")
            # 有时候路径为空
            RscriptPath = "Rscript" if not RscriptPath else RscriptPath
            # try:
            #     popen = subprocess.Popen(
            #         RscriptPath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall" if mode == "settings" else False
            # stdout = self.getSTDOUT(popen)
            if shutil.which(RscriptPath): #"Usage: /path/to/Rscript [--options]" in stdout:
                self.settings_ini.setValue("RscriptPath", RscriptPath)  ##设置一遍，不然workflow报错
                return "succeed" if mode == "settings" else RscriptPath
        elif program == "mafft":
            MAFFTpath = self.settings_ini.value('mafft', "")
            # if platform.system().lower() == "linux":
            #     #只在linux判断环境变量
            #     if (not MAFFTpath) and shutil.which(
            #         "mafft"): return "succeed" if mode == "settings" else "mafft"
            if platform.system().lower() == "windows":
                env_name = dict_plugin_settings[program]["target_win"]
            elif platform.system().lower() == "darwin":
                env_name = dict_plugin_settings[program]["target_mac"]
            else:
                env_name = dict_plugin_settings[program]["target_linux"]
            if not MAFFTpath:
                if type(env_name) == list:
                    for each_env in env_name:
                        if shutil.which(each_env):
                            return "succeed" if mode == "settings" else each_env
                else:
                    if shutil.which(env_name):
                        return "succeed" if mode == "settings" else env_name
            MAFFTpath = self.getDefaultpluginPath("mafft") if \
                not MAFFTpath else MAFFTpath
            if shutil.which(MAFFTpath):
                return "succeed" if mode == "settings" else MAFFTpath
        elif program == "tbl2asn":
            TSpath = self.settings_ini.value('tbl2asn', "")
            if (not TSpath) and shutil.which(
                "tbl2asn"): return "succeed" if mode == "settings" else "tbl2asn"
            TSpath = os.path.join(self.thisPath, "plugins", "tbl2asn-master", "win.tbl2asn", "tbl2asn.exe") if \
                not TSpath else TSpath
            if shutil.which(TSpath):
                return "succeed" if mode == "settings" else TSpath
        elif program == "PF2":
            PFpath = self.settings_ini.value('PF2', "")
            PFpath = self.getDefaultpluginPath("PF2") if \
                not PFpath else PFpath
            if PFpath:
                pf_compiled = PFpath + os.sep + "PartitionFinder.exe" if platform.system().lower() == "windows" else \
                    PFpath + os.sep + "PartitionFinder"
                if os.path.exists(PFpath + os.sep + "PartitionFinder.py") or os.path.exists(pf_compiled):
                    return "succeed" if mode == "settings" else PFpath
        elif program == "gblocks":
            GBpath = self.settings_ini.value('gblocks', "")
            # if (not GBpath) and shutil.which(
            #     "Gblocks"): return "succeed" if mode == "settings" else "Gblocks"
            if platform.system().lower() == "windows":
                env_name = dict_plugin_settings[program]["target_win"]
            elif platform.system().lower() == "darwin":
                env_name = dict_plugin_settings[program]["target_mac"]
            else:
                env_name = dict_plugin_settings[program]["target_linux"]
            if not GBpath:
                if type(env_name) == list:
                    for each_env in env_name:
                        if shutil.which(each_env):
                            return "succeed" if mode == "settings" else each_env
                else:
                    if shutil.which(env_name):
                        return "succeed" if mode == "settings" else env_name
            GBpath = self.getDefaultpluginPath("gblocks") if \
                not GBpath else GBpath
            if shutil.which(GBpath):
                return "succeed" if mode == "settings" else GBpath
        elif program == "iq-tree":
            IQpath = self.settings_ini.value('iq-tree', "")
            # if (not IQpath) and shutil.which(
            #     "iqtree"): return "succeed" if mode == "settings" else "iqtree"
            if platform.system().lower() == "windows":
                env_name = dict_plugin_settings[program]["target_win"]
            elif platform.system().lower() == "darwin":
                env_name = dict_plugin_settings[program]["target_mac"]
            else:
                env_name = dict_plugin_settings[program]["target_linux"]
            if not IQpath:
                if type(env_name) == list:
                    for each_env in env_name:
                        if shutil.which(each_env):
                            return "succeed" if mode == "settings" else each_env
                else:
                    if shutil.which(env_name):
                        return "succeed" if mode == "settings" else env_name
            IQpath = self.getDefaultpluginPath("iq-tree") if \
                not IQpath else IQpath
            if shutil.which(IQpath):
                return "succeed" if mode == "settings" else IQpath
        elif program == "MrBayes":
            MBpath = self.settings_ini.value('MrBayes', "")
            # if platform.system().lower() == "windows":
            #     env_name = "mrbayes_x64" if platform.machine().endswith('64') else "mrbayes_x86"
            # else:
            #     env_name = "mb"
            if platform.system().lower() == "windows":
                env_name = dict_plugin_settings[program]["target_win"]
            elif platform.system().lower() == "darwin":
                env_name = dict_plugin_settings[program]["target_mac"]
            else:
                env_name = dict_plugin_settings[program]["target_linux"]
            if not MBpath:
                if type(env_name) == list:
                    for each_env in env_name:
                        if shutil.which(each_env):
                            return "succeed" if mode == "settings" else each_env
                else:
                    if shutil.which(env_name):
                        return "succeed" if mode == "settings" else env_name
            MBpath = self.getDefaultpluginPath("MrBayes") if \
                not MBpath else MBpath
            if shutil.which(MBpath):
                return "succeed" if mode == "settings" else MBpath
        elif program == "mpi":
            MPIpath = self.settings_ini.value('mpi', "mpirun")
            # 有时候路径为空
            MPIpath = "mpirun" if not MPIpath else MPIpath
            if shutil.which(MPIpath):
                return "succeed" if mode == "settings" else MPIpath
            # try:
            #     popen = subprocess.Popen(
            #         "%s --version"%MPIpath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall" if mode == "settings" else False
            # stdout = ""
            # while True:
            #     try:
            #         out_line = popen.stdout.readline().decode("utf-8", errors="ignore")
            #     except UnicodeDecodeError:
            #         out_line = popen.stdout.readline().decode("gbk", errors="ignore")
            #     if out_line == "" and popen.poll() is not None:
            #         break
            #     stdout += out_line
            # if ("Version:" in stdout) and ("Release Date:" in stdout):
            #     return "succeed" if mode == "settings" else MPIpath
        elif program == "java":
            javaPath = self.settings_ini.value('java', "java")
            javaPath = "java" if not javaPath else javaPath  # 有时候路径为空
            if shutil.which(javaPath):
                self.settings_ini.setValue("java", javaPath)  ##设置一遍，不然workflow报错
                return "succeed" if mode == "settings" else javaPath
            # try:
            #     popen = subprocess.Popen(
            #         "%s -version" % javaPath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall" if mode == "settings" else False
            # stdout = self.getSTDOUT(popen)
            # # print(stdout)
            # if re.search(r"Runtime Environment.+?\(.+?(\d+?\.\d+?)\.", stdout, re.I):
            #     # 判断是java > 1.5
            #     version = float(re.search(r"Runtime Environment.+?\(.+?(\d+?\.\d+?)\.", stdout, re.I).group(1))
            #     if version >= 1.5:
            #         self.settings_ini.setValue("java", javaPath)  ##设置一遍，不然workflow报错
            #         return "succeed" if mode == "settings" else javaPath
        elif program == "macse":
            MACSEpath = self.settings_ini.value('macse', "")
            if not MACSEpath:
                # 自动判断下是否存在于环境变量
                if platform.system().lower() == "windows":
                    env_name = dict_plugin_settings[program]["target_win"]
                elif platform.system().lower() == "darwin":
                    env_name = dict_plugin_settings[program]["target_mac"]
                else:
                    env_name = dict_plugin_settings[program]["target_linux"]
                for target in env_name:
                    if shutil.which(target):
                        return "succeed" if mode == "settings" else target
            MACSEpath = self.getDefaultpluginPath("macse") if \
                not MACSEpath else MACSEpath
            if MACSEpath and os.path.exists(MACSEpath):
                return "succeed" if mode == "settings" else MACSEpath
        elif program == "trimAl":
            trimAlpath = self.settings_ini.value('trimAl', "")
            # 自动判断下是否存在于环境变量
            if (not trimAlpath) and shutil.which("trimal"):
                return "succeed" if mode == "settings" else "trimal"
                # try: popen = subprocess.Popen(
                #         "trimal -h", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                # except: pass
                # stdout = self.getSTDOUT(popen)
                # if shutil.which("trimal"):
                #     return "succeed" if mode == "settings" else "trimal"
            trimAlpath = self.getDefaultpluginPath("trimAl") if \
                not trimAlpath else trimAlpath
            if shutil.which(trimAlpath):
                return "succeed" if mode == "settings" else trimAlpath
        elif program == "perl":
            PERLPath = self.settings_ini.value('perl', "perl")
            PERLPath = "perl" if not PERLPath else PERLPath  # 有时候路径为空
            # try:
            #     popen = subprocess.Popen(
            #         "%s -version" % PERLPath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall" if mode == "settings" else False
            # stdout = self.getSTDOUT(popen)
            # print(stdout)
            if shutil.which(PERLPath):
                self.settings_ini.setValue("perl", PERLPath)  ##设置一遍，不然workflow报错
                return "succeed" if mode == "settings" else PERLPath
        elif program == "HmmCleaner":
            HmmClPath = self.settings_ini.value('HmmCleaner', "HmmCleaner.pl")
            HmmClPath = "HmmCleaner.pl" if not HmmClPath else HmmClPath  # 有时候路径为空
            # try:
            #     popen = subprocess.Popen(
            #         "%s --help" % HmmClPath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall" if mode == "settings" else False
            # stdout = self.getSTDOUT(popen)
            if shutil.which(HmmClPath):
                self.settings_ini.setValue("HmmCleaner", HmmClPath)  ##设置一遍，不然workflow报错
                return "succeed" if mode == "settings" else HmmClPath
        elif program == "CodonW":
            CodonPath = self.settings_ini.value('CodonW', "")
            env_name = "CodonW.exe" if platform.system().lower() == "windows" else "codonw"
            # 判断是否环境变量有该软件
            if (not CodonPath) and shutil.which(env_name):
                return "succeed" if mode == "settings" else env_name
            CodonPath = self.getDefaultpluginPath("CodonW") if \
                not CodonPath else CodonPath
            if shutil.which(CodonPath):
                return "succeed" if mode == "settings" else CodonPath
        else:
            plugin_name = dict_plugin_settings[program]["plugin_name"]
            pluginPath = self.settings_ini.value(plugin_name, "")
            if platform.system().lower() == "windows":
                env_name = dict_plugin_settings[program]["target_win"]
            elif platform.system().lower() == "darwin":
                env_name = dict_plugin_settings[program]["target_mac"]
            else:
                env_name = dict_plugin_settings[program]["target_linux"]
            # 判断是否环境变量有该软件
            if not pluginPath:
                if type(env_name) == list:
                    for each_env in env_name:
                        if shutil.which(each_env):
                            return "succeed" if mode == "settings" else each_env
                else:
                    if shutil.which(env_name):
                        return "succeed" if mode == "settings" else env_name
            pluginPath = self.getDefaultpluginPath(plugin_name) if \
                not pluginPath else pluginPath
            if shutil.which(pluginPath):
                return "succeed" if mode == "settings" else pluginPath
        return "uninstall" if mode == "settings" else False

    def programIsValid_2(self, program, path, parent=None, btn=None):
        # 只有该功能有提醒功能,不能在线程里面使用，专用于settings里面使用
        if program == "python27":
            PyPath = path
            PyPath = "python" if not PyPath else PyPath  # 有时候路径为空
            try:
                popen = subprocess.Popen(
                    "\"%s\" -V" % PyPath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            except:
                return "uninstall"
            stdout = self.getSTDOUT(popen)
            if re.search(r"python\s+?2\.[3-7]\.", stdout, re.I):
                # 判断是python 2.3-2.7的版本
                return "succeed"
            else:
                if btn == "OK":
                    if PyPath == "python":
                        QMessageBox.critical(
                            parent,
                            "Settings",
                            "<p style='line-height:25px; height:25px'>The path is not validated!</p>")
                    elif parent:
                        QMessageBox.information(
                            parent,
                            "Install Python 2.7",
                            "<p style='line-height:25px; height:25px'>Only Python 2.3-2.7 is allowed, please specify anew!</p>")
        elif program == "RscriptPath":
            RscriptPath = path
            # 有时候路径为空
            RscriptPath = "Rscript" if not RscriptPath else RscriptPath
            # try:
            #     popen = subprocess.Popen(
            #         RscriptPath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall"
            # stdout = self.getSTDOUT(popen)
            if shutil.which(RscriptPath):
                return "succeed"
        elif program == "mafft":
            MAFFTpath = path
            # ok = self.checkPath(MAFFTpath, parent=parent, allow_space=True)
            if shutil.which(MAFFTpath):
                return "succeed"
            # MAFFTpath = path
            # try:
            #     popen = subprocess.Popen(
            #         "\"%s\" --version"%MAFFTpath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall"
            # stdout = self.getSTDOUT(popen)
            # if re.search(r"v(\d)\.(\d)", stdout, re.I):
            #     v1, v2 = re.findall(r"v(\d)\.(\d)", stdout, re.I)[0]
            #     if int(v1) < 7 or int(v2) < 3:
            #         QMessageBox.information(
            #             parent,
            #             "Information",
            #             "<p style='line-height:25px; height:25px'>Only MAFFT versions newer than 7.3 is allowed, please specify anew!</p>")
            #     else:
            #         if MAFFTpath and os.path.exists(MAFFTpath):
            #             return "succeed"
        elif program == "tbl2asn":
            TSpath = path
            if shutil.which(TSpath):
                return "succeed"
        elif program == "PF2":
            PFpath = path
            if PFpath:
                pf_compiled = PFpath + os.sep + "PartitionFinder.exe" if platform.system().lower() == "windows" else \
                    PFpath + os.sep + "PartitionFinder"
                if (os.path.exists(PFpath + os.sep + "PartitionFinder.py") or os.path.exists(pf_compiled)):
                    return "succeed"
        elif program == "gblocks":
            GBpath = path
            if shutil.which(GBpath):
                return "succeed"
        elif program == "iq-tree":
            IQpath = path
            if shutil.which(IQpath):
                return "succeed"
        elif program == "MrBayes":
            MBpath = path
            if shutil.which(MBpath):
                return "succeed"
            # MBpath = path
            # try:
            #     popen = subprocess.Popen(
            #         "\"%s\" -v"%MBpath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall"
            # stdout = self.getSTDOUT(popen)
            # if re.search(r"v(\d)\.(\d)", stdout, re.I):
            #     v1, v2 = re.findall(r"v(\d)\.(\d)", stdout, re.I)[0]
            #     if int(v1) < 3 or int(v2) < 2:
            #         QMessageBox.information(
            #             parent,
            #             "Information",
            #             "<p style='line-height:25px; height:25px'>Only MrBayes versions newer than 3.2 is allowed, please specify anew!</p>")
            #     else:
            #         if MBpath and os.path.exists(MBpath):
            #             return "succeed"
        elif program == "mpi":
            MPIpath = path
            # 有时候路径为空
            MPIpath = "mpirun" if not MPIpath else MPIpath
            # try:
            #     popen = subprocess.Popen(
            #         "\"%s\" --version" % MPIpath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall"
            # stdout = ""
            # while True:
            #     try:
            #         out_line = popen.stdout.readline().decode("utf-8", errors="ignore")
            #     except UnicodeDecodeError:
            #         out_line = popen.stdout.readline().decode("gbk", errors="ignore")
            #     if out_line == "" and popen.poll() is not None:
            #         break
            #     stdout += out_line
            if shutil.which(MPIpath):
                return "succeed"
        elif program == "java":
            JAVApath = path
            # 有时候路径为空
            JAVApath = "java" if not JAVApath else JAVApath
            if shutil.which(JAVApath):
                return "succeed"
            # try:
            #     popen = subprocess.Popen(
            #         "\"%s\" -version" % JAVApath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall"
            # stdout = self.getSTDOUT(popen)
            # match = re.search(r"Runtime Environment.+?\(.+?(\d+?\.\d+?)\.", stdout, re.I)
            # if match and float(match.group(1)) >= 1.5:
            #     # 判断是JAVA 1.5以上的版本
            #     return "succeed"
            # else:
            #     if btn == "OK":
            #         if JAVApath == "java":
            #             QMessageBox.critical(
            #                 parent,
            #                 "Settings",
            #                 "<p style='line-height:25px; height:25px'>The path is not validated!</p>")
            #         elif parent:
            #             QMessageBox.information(
            #                 parent,
            #                 "Install JAVA",
            #                 "<p style='line-height:25px; height:25px'>Only JAVA with JRE above 1.5 is allowed, please specify anew!</p>")
        elif program == "macse":
            MSpath = path
            if MSpath and os.path.exists(MSpath):
                return "succeed"
        elif program == "trimAl":
            TApath = path
            if shutil.which(TApath):
                return "succeed"
        elif program == "perl":
            PERLpath = path
            # 有时候路径为空
            PERLpath = "perl" if not PERLpath else PERLpath
            # try:
            #     popen = subprocess.Popen(
            #         "\"%s\" -version" % PERLpath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall"
            # stdout = self.getSTDOUT(popen)
            # match = re.search(r"is perl", stdout, re.I)
            if shutil.which(PERLpath):
                # 判断是PERL 5以上的版本
                return "succeed"
            # else:
            #     if btn == "OK":
            #         if PERLpath == "perl":
            #             QMessageBox.critical(
            #                 parent,
            #                 "Settings",
            #                 "<p style='line-height:25px; height:25px'>The path is not validated!</p>")
            #         elif parent:
            #             QMessageBox.information(
            #                 parent,
            #                 "Install PERL",
            #                 "<p style='line-height:25px; height:25px'>Only PERL above 5 is allowed, please specify anew!</p>")
        elif program == "HmmCleaner":
            HmmClPath = path
            # 有时候路径为空
            HmmClPath = "HmmCleaner.pl" if not HmmClPath else HmmClPath
            # try:
            #     popen = subprocess.Popen(
            #         "\"%s\" --help" % HmmClPath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            # except:
            #     return "uninstall"
            # stdout = self.getSTDOUT(popen)
            # match = re.search(r"Usage:", stdout, re.I)
            if shutil.which(HmmClPath):
                return "succeed"
        elif program == "CodonW":
            Codonpath = path
            if shutil.which(Codonpath):
                return "succeed"
        else:
            if shutil.which(path):
                return "succeed"
        return "uninstall"

    def init_check(self, parent):
        try:
            # 删掉插件不合格的路径
            for i in ["python27", "mafft", "PF2", "gblocks", "iq-tree", "MrBayes", "tbl2asn", "RscriptPath", "mpi",
                      "perl", "java", "macse", "trimAl", "HmmCleaner"] + list(dict_plugin_settings.keys()):
                path = self.settings_ini.value(i, "")
                if path and not os.path.exists(path):
                    self.settings_ini.setValue(i, "")
            # 更新1.2.1版本的时候，没有整理分类相关设置的
            ini_data = [['Class', 'Order', 'Superfamily', 'Family', 'Subfamily', 'Genus'],
                        [['', '*tera', '*dea', '*dae', '*nae', ''],
                         ['', '', '*ida', '', '', ''],
                         ['', '', '', '', '', ''],
                         ['', '', '', '', '', ''],
                         ['', '', '', '', '', '']]]
            data = self.settings_ini.value("Taxonomy Recognition", ini_data)
            if type(data) == list:
                new_data = OrderedDict(
                    [("Default taxonomy settings", data)])
                self.settings_ini.setValue("Taxonomy Recognition", new_data)
            # 检查是否中国用户
            import json
            import urllib.request
            try:
                with urllib.request.urlopen("https://geolocation-db.com/json/") as url:
                    data = json.loads(url.read().decode())
                    country = data["country_name"]
                self.path_settings.setValue("country", country)
            except: pass
            # 判断将mainwindow里面的data的相关设置拷贝到对应workplace的设置里面
            data_settings = QSettings(
                self.workPlaceSettingPath + os.sep + 'data_settings.ini', QSettings.IniFormat)
            mainwindow_settings = QSettings(
                self.thisPath +
                '/settings/mainwindow_settings.ini',
                QSettings.IniFormat)
            keys = mainwindow_settings.allKeys()
            for key in keys:
                if key.endswith("_displayedArray") or key.endswith("_availableInfo"):
                    path = key.replace("_displayedArray", "").replace("_availableInfo", "")
                    workplace_path = re.sub(r"/|\\", "_", os.path.dirname(self.workPlaceSettingPath))
                    remainingStr = path.replace(workplace_path, "")
                    if remainingStr.startswith("_GenBank_File"):
                        data_settings.setValue(key, mainwindow_settings.value(key))
                        mainwindow_settings.remove(key)
            # 初始化extract settings
            GenBankExtract_settings = QSettings(
                self.thisPath + '/settings/GenBankExtract_settings.ini', QSettings.IniFormat)
            GenBankExtract_settings.setFallbacksEnabled(False)
            dict_gbExtract_set = GenBankExtract_settings.value("set_version", None)
            if not dict_gbExtract_set:
                GenBankExtract_settings.setValue("set_version", init_sequence_type)
            else:
                # 如果没有预设的类型，就加上
                flag = False
                for seq_type in init_sequence_type:
                    if seq_type not in dict_gbExtract_set:
                        flag = True
                        dict_gbExtract_set[seq_type] = init_sequence_type[seq_type]
                    if seq_type == "general" and "extract all features" not in dict_gbExtract_set[seq_type]:
                        dict_gbExtract_set[seq_type]["extract all features"] = True
                if flag:
                    GenBankExtract_settings.setValue("set_version", dict_gbExtract_set)
            # 初始化workflow设置
            workflow_settings = QSettings(
                self.thisPath +
                '/settings/workflow_settings.ini',
                QSettings.IniFormat)
            workflow_settings.setFallbacksEnabled(False)
            workflow_settings.beginGroup('Workflow')
            keys = workflow_settings.allKeys()
            if not keys or ("Test run/PartitionFinder/comboBox" not in keys) or \
                    ("Align CDS, Refine alignment, Optimize alignment, "
                     "Concatenation and Select best-fit model/Concatenate Sequence/checkBox" not in keys):
                for key in preset_workflow:
                    workflow_settings.setValue(key, preset_workflow[key])
            workflow_settings.endGroup()
            # 初始化sequence view settings
            Seq_viewer_setting = QSettings(
                self.thisPath +
                '/settings/Seq_viewer_setting.ini',
                QSettings.IniFormat)
            Seq_viewer_setting.setFallbacksEnabled(False)
            font = Seq_viewer_setting.value("display font", None)
            if not font:
                Seq_viewer_setting.setValue(
                    "display font", QFont("Courier New", 11))
            ini_fore_colors = {'W': '#000000', 'I': '#000000', 'U': '#ffffff', '-': '#000000', 'C': '#000000',
                               'A': '#000000', '.': '#000000', 'M': '#000000', 'V': '#000000', 'P': '#ffffff',
                               'K': '#000000', 'G': '#000000', 'N': '#000000', 'E': '#ffffff', '...': '#000000',
                               'H': '#000000', 'Q': '#ffffff', 'R': '#ffffff', 'D': '#000000', 'T': '#ffffff',
                               'L': '#000000', 'S': '#000000', 'F': '#000000', 'Y': '#000000'}
            dict_foreColor = Seq_viewer_setting.value("foreground colors", None)
            if not dict_foreColor:
                Seq_viewer_setting.setValue("foreground colors", ini_fore_colors)
            ini_back_colors = {'W': '#ff0000', 'I': '#ffcc00', 'U': '#ff0000', '-': '#ffffff', 'C': '#00aaff',
                               'A': '#99ff00', '.': '#ffffff', 'M': '#99ff00', 'V': '#ffcc00', 'P': '#3cb371',
                               'K': '#00ffff', 'G': '#ffcc00', 'N': '#87ceeb', 'E': '#ff00ff', '...': '#808080',
                               'H': '#ff0000', 'Q': '#ff00ff', 'R': '#ff69b4', 'D': '#87ceeb', 'T': '#ff0000',
                               'L': '#99ff00', 'S': '#ff0000', 'F': '#99ff00', 'Y': '#87ceeb'}
            dict_backColor = Seq_viewer_setting.value("background colors", None)
            if not dict_backColor:
                Seq_viewer_setting.setValue("background colors", ini_back_colors)
            # 初始化parse ANNT的settings
            init_value2 = {'tRNA Abbreviation': [['tRNA-Val', 'V'], ['tRNA-Tyr', 'Y'], ['tRNA-Trp', 'W'], ['tRNA-Thr', 'T'], ['tRNA-Ser', 'S'], ['tRNA-Pro', 'P'], ['tRNA-Phe', 'F'], ['tRNA-Met', 'M'], ['tRNA-Lys', 'K'], ['tRNA-Leu', 'L'], ['tRNA-Ile', 'I'], ['tRNA-His', 'H'], ['tRNA-Gly', 'G'], ['tRNA-Glu', 'E'], ['tRNA-Gln', 'Q'], ['tRNA-Cys', 'C'], ['tRNA-Asp', 'D'], ['tRNA-Asn', 'N'], ['tRNA-Arg', 'R'], ['tRNA-Ala', 'A']], 'Protein Gene Full Name': [['atp6', 'ATP synthase F0 subunit 6'], ['atp8', 'ATP synthase F0 subunit 8'], ['cox1', 'cytochrome c oxidase subunit 1'], ['cox2', 'cytochrome c oxidase subunit 2'], ['cox3', 'cytochrome c oxidase subunit 3'], ['cytb', 'cytochrome b'], ['nad1', 'NADH dehydrogenase subunit 1'], ['nad2', 'NADH dehydrogenase subunit 2'], ['nad3', 'NADH dehydrogenase subunit 3'], ['nad4', 'NADH dehydrogenase subunit 4'], ['nad4L', 'NADH dehydrogenase subunit 4L'], ['nad5', 'NADH dehydrogenase subunit 5'], ['nad6', 'NADH dehydrogenase subunit 6']], 'Name From Word': [['trnY(gta)', 'tRNA-Tyr(gta)'], ['trnY', 'tRNA-Tyr(gta)'], ['trnW(tca)', 'tRNA-Trp(tca)'], ['trnW', 'tRNA-Trp(tca)'], ['trnV(tac)', 'tRNA-Val(tac)'], ['trnV', 'tRNA-Val(tac)'], ['trnT(tgt)', 'tRNA-Thr(tgt)'], ['trnT', 'tRNA-Thr(tgt)'], ['trnR(tcg)', 'tRNA-Arg(tcg)'], ['trnR', 'tRNA-Arg(tcg)'], ['trnQ(ttg)', 'tRNA-Gln(ttg)'], ['trnQ', 'tRNA-Gln(ttg)'], ['trnP(tgg)', 'tRNA-Pro(tgg)'], ['trnP', 'tRNA-Pro(tgg)'], ['trnN(gtt)', 'tRNA-Asn(gtt)'], ['trnN', 'tRNA-Asn(gtt)'], ['trnM(cat)', 'tRNA-Met(cat)'], ['trnM', 'tRNA-Met(cat)'], ['trnK(ctt)', 'tRNA-Lys(ctt)'], ['trnK', 'tRNA-Lys(ctt)'], ['trnI(gat)', 'tRNA-Ile(gat)'], ['trnI', 'tRNA-Ile(gat)'], ['trnH(gtg)', 'tRNA-His(GTG)'], ['trnH', 'tRNA-His(gtg)'], ['trnG(tcc)', 'tRNA-Gly(tcc)'], ['trnG', 'tRNA-Gly(tcc)'], ['trnF(gaa)', 'tRNA-Phe(gaa)'], ['trnF', 'tRNA-Phe(gaa)'], ['trnE(ttc)', 'tRNA-Glu(ttc)'], ['trnE', 'tRNA-Glu(ttc)'], ['trnD(gtc)', 'tRNA-Asp(gtc)'], ['trnD', 'tRNA-Asp(gtc)'], ['trnC(gca)', 'tRNA-Cys(gca)'], ['trnC', 'tRNA-Cys(gca)'], ['trnA(tgc)', 'tRNA-Ala(tgc)'], ['trnA', 'tRNA-Ala(tgc)'], ['tRNA-Val', 'tRNA-Val(tac)'], ['tRNA-Tyr', 'tRNA-Tyr(gta)'], ['tRNA-Trp', 'tRNA-Trp(tca)'], [
                'tRNA-Thr', 'tRNA-Thr(tgt)'], ['tRNA-Pro', 'tRNA-Pro(tgg)'], ['tRNA-Phe', 'tRNA-Phe(gaa)'], ['tRNA-Met', 'tRNA-Met(cat)'], ['tRNA-Lys', 'tRNA-Lys(ctt)'], ['tRNA-Ile', 'tRNA-Ile(gat)'], ['tRNA-His', 'tRNA-His(GTG)'], ['tRNA-Gly', 'tRNA-Gly(tcc)'], ['tRNA-Glu', 'tRNA-Glu(ttc)'], ['tRNA-Gln', 'tRNA-Gln(ttg)'], ['tRNA-Cys', 'tRNA-Cys(gca)'], ['tRNA-Asp', 'tRNA-Asp(gtc)'], ['tRNA-Asn', 'tRNA-Asn(gtt)'], ['tRNA-Arg', 'tRNA-Arg(tcg)'], ['tRNA-Ala', 'tRNA-Ala(tgc)'], ['small subunit ribosomal RNA', '12S'], ['small ribosomal RNA subunit RNA', '12S'], ['small ribosomal RNA', '12S'], ['s-rRNA', '12S'], ['ribosomal RNA small subunit', '12S'], ['ribosomal RNA large subunit', '16S'], ['large subunit ribosomal RNA', '16S'], ['large ribosomal RNA subunit RNA', '16S'], ['large ribosomal RNA', '16S'], ['l-rRNA', '16S'], ['cytochrome c oxidase subunit III', 'COX3'], ['cytochrome c oxidase subunit II', 'COX2'], ['cytochrome c oxidase subunit I', 'COX1'], ['cytochrome c oxidase subunit 3', 'COX3'], ['cytochrome c oxidase subunit 2', 'COX2'], ['cytochrome c oxidase subunit 1', 'COX1'], ['cytochrome b', 'CYTB'], ['ND6', 'NAD6'], ['ND5', 'NAD5'], ['ND4L', 'NAD4L'], ['ND4', 'NAD4'], ['ND3', 'NAD3'], ['ND2', 'NAD2'], ['ND1', 'NAD1'], ['NADH dehydrogenase subunit5', 'NAD5'], ['NADH dehydrogenase subunit 6', 'NAD6'], ['NADH dehydrogenase subunit 5', 'NAD5'], ['NADH dehydrogenase subunit 4L', 'NAD4L'], ['NADH dehydrogenase subunit 4', 'NAD4'], ['NADH dehydrogenase subunit 3', 'NAD3'], ['NADH dehydrogenase subunit 2', 'NAD2'], ['NADH dehydrogenase subunit 1', 'NAD1'], ['CYT B', 'CYTB'], ['COXIII', 'COX3'], ['COXII', 'COX2'], ['COXI', 'COX1'], ['COIII', 'COX3'], ['COII', 'COX2'], ['COI', 'COX1'], ['COB', 'CYTB'], ['CO3', 'COX3'], ['CO2', 'COX2'], ['CO1', 'COX1'], ['ATPase subunit 6', 'ATP6'], ['ATPASE8', 'ATP8'], ['ATPASE6', 'ATP6'], ['ATPASE 8', 'ATP8'], ['ATPASE 6', 'ATP6'], ['ATP synthase F0 subunit 6', 'ATP6'], ['16s rRNA', '16S'], ['16S subunit RNA', '16S'], ['16S ribosomal RNA', '16S'], ['16S rRNA', '16S'], ['12s rRNA', '12S'], ['12S subunit RNA', '12S'], ['12S ribosomal RNA', '12S'], ['12S rRNA', '12S'], ['12S Ribosomal RNA', '12S']]}
            parseANNT_settings = QSettings(
                self.thisPath +
                '/settings/parseANNT_settings.ini',
                QSettings.IniFormat)
            parseANNT_settings.setFallbacksEnabled(False)
            dict_data = parseANNT_settings.value(
                "extract listed gene", None)
            if not dict_data:
                parseANNT_settings.setValue("extract listed gene", init_value2)
            # 初始化 color set
            PS_color1 = [
                "#2E91E5",
                "#E15F99",
                "#1CA71C",
                "#FB0D0D",
                "#DA16FF",
                "#222A2A",
                "#B68100",
                "#750D86",
                "#EB663B",
                "#511CFB",
                "#00A08B",
                "#FB00D1",
                "#FC0080",
                "#B2828D",
                "#6C7C32",
                "#778AAE",
                "#862A16",
                "#A777F1",
                "#620042",
                "#1616A7",
                "#DA60CA",
                "#6C4516",
                "#0D2A63",
                "#AF0038",
            ]
            PS_color2 = [
                "#FD3216",
                "#00FE35",
                "#6A76FC",
                "#FED4C4",
                "#FE00CE",
                "#0DF9FF",
                "#F6F926",
                "#FF9616",
                "#479B55",
                "#EEA6FB",
                "#DC587D",
                "#D626FF",
                "#6E899C",
                "#00B5F7",
                "#B68E00",
                "#C9FBE5",
                "#FF0092",
                "#22FFA7",
                "#E3EE9E",
                "#86CE00",
                "#BC7196",
                "#7E7DCD",
                "#FC6955",
                "#E48F72",
            ]
            PS_color3 = [
                "#636EFA",
                "#EF553B",
                "#00CC96",
                "#AB63FA",
                "#FFA15A",
                "#19D3F3",
                "#FF6692",
                "#B6E880",
                "#FF97FF",
                "#FECB52",
            ]
            PS_color4 = [
                "#1F77B4",
                "#FF7F0E",
                "#2CA02C",
                "#D62728",
                "#9467BD",
                "#8C564B",
                "#E377C2",
                "#7F7F7F",
                "#BCBD22",
                "#17BECF",
            ]
            PS_color5 = [
                "#3366CC",
                "#DC3912",
                "#FF9900",
                "#109618",
                "#990099",
                "#0099C6",
                "#DD4477",
                "#66AA00",
                "#B82E2E",
                "#316395",
            ]
            PS_color6 = [
                "#4C78A8",
                "#F58518",
                "#E45756",
                "#72B7B2",
                "#54A24B",
                "#EECA3B",
                "#B279A2",
                "#FF9DA6",
                "#9D755D",
                "#BAB0AC",
            ]
            default_colors = {
                "PhyloSuite color1": PS_color1,
                "PhyloSuite color2": PS_color2,
                "PhyloSuite color3": PS_color3,
                "PhyloSuite color4": PS_color4,
                "PhyloSuite color5": PS_color5,
                "PhyloSuite color6": PS_color6,
            }
            color_settings = QSettings(
                self.thisPath +
                '/settings/color_sets.ini',
                QSettings.IniFormat)
            color_settings.setFallbacksEnabled(False)
            values = color_settings.value("PhyloSuite colors", None)
            if not values:
                color_settings.setValue("PhyloSuite colors", default_colors)
        except:
            parent.exception_signal.emit(''.join(
                traceback.format_exception(*sys.exc_info())) + "\n")

    def display_check(self, array, gbManager, exceptSig, display_checkSig, progressBarSig):
        try:
            # print(int(QThread.currentThreadId()))
            # time_start = time.time()
            haveUpdate = gbManager.updateModifiedRecord(0, 50, progressBarSig)
            if haveUpdate:
                # print("haveUpdate")
                array = gbManager.fetch_array()
            # time_end = time.time()
            # print('totally cost1:', time_end - time_start)
            # time_start = time.time()
            haveNewArray = gbManager.updateArrayByInfo(
                50, 50, progressBarSig)  # 检查是否有需要补充的信息
            if haveNewArray:
                # print("haveNewArray")
                array = gbManager.fetch_array()
            # time_end = time.time()
            # print('totally cost2:', time_end - time_start)
            # time_start = time.time()
            # validatedIDs = gbManager.fetchVerifiedIDs()  #8秒
            # time_end = time.time()
            # print('totally cost3:', time_end - time_start)
            # reverse_array = [array[0]] + sorted(array[1:], reverse=True)  # 反转一下
            # validatedIDs = gbManager.fetchVerifiedIDs(20, 80, progressBarSig)  ##这一步也很慢
            # displayTableModel.updateModel(array)
            # return
            display_checkSig.emit(array)
        except:
            exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            exceptSig.emit(exceptionInfo)  # 激发这个信号

    def normalizeMT_child(self, gbManager, dict_NML_settings):
        # 子线程要执行的任务
        from src.handleGB import Normalize_MT
        parent = dict_NML_settings["parent"]
        try:
            validate_content = gbManager.fetchContentsByIDs(
                dict_NML_settings["list_IDs"])
            dict_NML_settings["gbContents"] = validate_content
            parent.nmlgb = Normalize_MT(**dict_NML_settings)
        except:
            exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            print(exceptionInfo)
            parent.exception_signal.emit(exceptionInfo)  # 激发这个信号
        # return nmlgb

    def normalizeMT_main(self, nmlgb):
        from src.Lg_gbEditor import GbEditor
        # 子线程任务完成，主线程要执行的任务
        gbeditor = GbEditor(nmlgb)
        # 添加最大化按钮
        gbeditor.setWindowFlags(
            gbeditor.windowFlags() | Qt.WindowMinMaxButtonsHint)
        gbeditor.exec_()

    def checkUpdates(self, updateSig, exceptSig, mode="check", parent=None):
        try:
            with open(self.thisPath + os.sep + "NEWS_version.md", encoding="utf-8") as f:
                content = f.read()
                current_version = re.search(
                    r"## *PhyloSuite v([^ ]+?) \(", content).group(1)
            if self.path_settings.value("country", "UK") == "China":
                version_url = "http://phylosuite.jushengwu.com/NEWS_version.md"
            elif platform.system().lower() == "windows":
                version_url = "https://github.com/dongzhang0725/PhyloSuite/blob/master/NEWS_version.md"
            elif platform.system().lower() == "darwin":
                version_url = "https://github.com/dongzhang0725/PhyloSuite_Mac/blob/master/NEWS_version.md"
            elif platform.system().lower() == "linux":
                version_url = "https://github.com/dongzhang0725/PhyloSuite_linux/blob/master/NEWS_version.md"
            else:
                return
            def slot(urlContent):
                # 如果是error开始的字符串，这里写一下
                if urlContent.startswith("Error"):
                    if mode == "check":
                        urlContent += "\nUpdate: please check network connection"
                        exceptSig.emit(urlContent)
                    return
                if "<h2>" not in urlContent:
                    # 国内源，匹配markdown内容
                    rgx = re.compile(r"(?s)## *PhyloSuite v([^ ]+?) \(.+?\)\n(.+?)## PhyloSuite")
                    rgx_search = rgx.search(urlContent)
                    if rgx_search:
                        description = rgx_search.group(2).replace("\n", "<br>").replace(" ", "&nbsp;")
                        new_version = rgx_search.group(1)
                    else:
                        description, new_version = None, None
                else:
                    rgx = re.compile(
                        r"(?sm)(<h2>.*?PhyloSuite v([^ ]+?) \(.+?</h2>.+?<ul>.+?</ul>)\s+?(?=<h2>|</article>)")
                    rgx_search = rgx.search(urlContent)
                    if rgx_search:
                        description = rgx_search.group(1)
                        new_version = rgx_search.group(2)
                    else:
                        description, new_version = None, None
                # print(current_version, new_version, description)
                if description and new_version:
                    updateSig.emit(current_version, new_version, description)
            httpread = HttpRead(parent=parent)
            httpread.finishedSig.connect(slot)
            httpread.doRequest(version_url)
            # httpread.doRequest()
            # print(urlContent)
            # 这里要花点儿时间，如果没网怎么办
            # urlContent = text.read().decode('utf-8')
        except Exception as ex:
            updateSig.emit(None, None, None)  # 关闭状态窗口
            exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            if mode == "check":
                if ex.__class__.__name__ == "URLError":
                    exceptionInfo += "\nUpdate: please check network connection"
                exceptSig.emit(exceptionInfo)  # 激发这个信号

    def popupException(self, parent, exception):
        print(exception)
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        country = self.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#7-1-Update-failed-how-to-revert-to-previous-settings-and-plugins" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#7-1-Update-failed-how-to-revert-to-previous-settings-and-plugins"
        if (platform.system().lower() == "linux") and ("Error creating SSL context" in exception):
            msg.setWindowTitle("Network error")
            msg.setText(
                "<p style='line-height:25px; height:25px'>Network library malfunction while checking for updates, "
                "see <a href=\"https://github.com/barryvdh/laravel-snappy/issues/217\">https://github.com/barryvdh/laravel-snappy/issues/217</a> for resolutions! "
                "Alternatively, you also can update PhyloSuite manually following this <a href=\"%s\">instruction</a></p>"%url)
        elif exception.endswith("Update: please check network connection"):
            msg.setWindowTitle("Update failed")
            msg.setText(
                "<p style='line-height:25px; height:25px'>Please check your network connection! "
                "Alternatively, you also can update PhyloSuite manually following this "
                "<a href=\"%s\">instruction</a></p>"%url)
        elif exception.endswith("GenBank file parse failed"):
            msg.setWindowTitle("GenBank file parse failed")
            msg.setText(
                "<p style='line-height:25px; height:25px'>GenBank file parse failed, please check your file carefully!</p>")
        elif exception.endswith("partial GenBank file failed"):
            exception = exception.replace("partial GenBank file failed", "")
            if re.search(r"(?sm)(LOCUS {7}(\S+).+?^//\s*?(?=LOCUS|$))", exception):
                list_IDs = [i[-1] for i in re.findall(r"(?sm)(LOCUS {7}(\S+).+?^//\s*?(?=LOCUS|$))", exception)]
            else:
                list_IDs=[]
            list_IDs = list_IDs[:20] if len(list_IDs) > 20 else list_IDs
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("GenBank file parse warning")
            msg.setText(
                "<p style='line-height:25px; height:25px'>Parsing of the following IDs failed: %s! Click \"Show Details\" to check them carefully.</p>"%", ".join(list_IDs))
        elif exception.endswith("part of IDs failed taxonomy"):
            exception = exception.replace("part of IDs failed taxonomy", "")
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Get taxonomy warning")
            msg.setText(
                "<p style='line-height:25px; height:25px'>Get taxonomy for some sequences failed! Click \"Show Details\" to check them carefully.</p>")
        elif exception.endswith("<normal exception>"):
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Warning")
            msg.setText(
                "<p style='line-height:25px; height:25px'>%s</p>"%exception.replace("<normal exception>", ""))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        else:
            msg.setWindowTitle("Error")
            msg.setText(
                "<p style='line-height:25px; height:25px'>The program encountered an unforeseen problem, please report "
                "the bug at <a href=\"https://github.com/dongzhang0725/PhyloSuite/issues\">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed "
                "traceback to dongzhang0725@gmail.com</p>")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def highlightWidgets(self, widget, *widgets, color="purple"):
        widgets_ = (widget,) + widgets
        for widget_ in widgets_:
            widget_.setGraphicsEffect(
                AnimationShadowEffect(QColor(color), widget_))

    def deHighlightWidgets(self, widget, *widgets):
        widgets_ = (widget,) + widgets
        for widget_ in widgets_:
            graphicsEffect = widget_.graphicsEffect()
            try: graphicsEffect.stop()
            except: pass

    def openPath(self, path, parent):
        if platform.system().lower() == "windows":
            path = path.replace("/", "\\")
            os.startfile(path)
        elif platform.system().lower() == "darwin":
            if os.path.isfile(path):
                if os.system('open %s' % path) != 0:
                    QMessageBox.information(
                        parent,
                        "PhyloSuite",
                        "<p style='line-height:25px; height:25px'>Path: %s</p>" % path,
                        QMessageBox.Ok)
            elif os.path.isdir(path):
                subprocess.Popen(["open", path])
        elif platform.system().lower() == "linux":
            if os.path.isfile(path):
                if os.system('open %s' % path) != 0:
                    QMessageBox.information(
                        parent,
                        "PhyloSuite",
                        "<p style='line-height:25px; height:25px'>Path: %s</p>" % path,
                        QMessageBox.Ok)
            elif os.path.isdir(path):
                subprocess.Popen(["xdg-open", path])
        else:
            QMessageBox.information(
                parent,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>Path: %s</p>" % path,
                QMessageBox.Ok)

    def checkPath(self, path, mode="normal", parent=None, allow_space=False):
        rgx = re.compile(r"([^a-zA-Z0-9\-\.\\\/\:_]+)",
                         re.I) if not allow_space else re.compile(r"([^a-zA-Z0-9\-\.\\\/\:_ ]+)", re.I)
        if rgx.search(path):
            path_text = rgx.sub("<span style=\"color:red\">\\1</span>", path)
            path_text = path_text.replace("<span style=\"color:red\"> </span>",
                                          "<span style=\"background:red\">&nbsp;&nbsp;</span>")
            illegalTXT = rgx.search(path).group()
            if re.search(r" +", illegalTXT):
                illegalTXT = "spaces"
            if mode == "silence":
                return illegalTXT, path_text
            elif mode != "app path":
                QMessageBox.critical(
                    parent,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>There may be some non-standard characters in the path (<span style=\"color:red\">%s</span>),"
                    " try to use a different path. The archcriminal characters in the path are shown in red:<br> \"%s\"</p>" % (
                        illegalTXT, path_text),
                    QMessageBox.Ok)
                return False
            else:
                mainwindow_settings = QSettings(
                    self.thisPath +
                    '/settings/mainwindow_settings.ini',
                    QSettings.IniFormat, parent=parent)
                mainwindow_settings.setFallbacksEnabled(False)
                PopPathRemind = mainwindow_settings.value(
                    "remind_path", "true")
                if self.str2bool(PopPathRemind):
                    icon = ":/picture/resourses/icons8-cancel-50.png"
                    message = "There may be some non-standard characters in the path of the PhyloSuite (<span style=\"color:red\">%s</span>), which can cause" \
                              " the software to <span style=\"color:red\">malfunction</span>. Try to reinstall the PhyloSuite to a different path " \
                              "(no spaces and no non-standard characters). The archcriminal characters in the path are shown in red:<br> \"%s\"" % (
                                  illegalTXT, path_text)
                    windInfo = NoteMessage(
                        message, icon, singleBtn=True, parent=parent, hideReminder=True)
                    windInfo.checkBox.clicked.connect(
                        lambda bool_: mainwindow_settings.setValue("remind_path", not bool_))
                    if windInfo.exec_() == QDialog.Accepted:
                        return
        return True
    # def fetch_thisPath(self):
    #     thisPath = os.path.dirname(sys.argv[0])  # MAC打包后获取当前脚本路径方式
    #     thisPath = "." if not thisPath else thisPath  ##有时候当前目录是空
    #     return thisPath

    def init_popen(self, commands):
        startupINFO = None
        if platform.system().lower() == "windows":
            startupINFO = subprocess.STARTUPINFO()
            startupINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupINFO.wShowWindow = subprocess.SW_HIDE
            popen = subprocess.Popen(
                commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO, shell=True)
        else:
            popen = subprocess.Popen(
                commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO, shell=True,
                preexec_fn=os.setsid)
        return popen

    def set_direct_dir(self, action, parent):
        name, ok = QInputDialog.getText(
            parent, 'Set output directory name', 'Output directory name:')
        if ok and name:
            name = self.refineName(name, remain_words="-")
            self.sync_dir(action, name=name)

    def sync_dir(self, action, name=None):
        #同步输出文件名字
        if name:
            action.setText("Output Dir: %s"%name)
        else:
            time_str = time.strftime('%Y_%m_%d-%H_%M_%S', time.localtime(time.time()))
            action.setText("Output Dir: %s"%time_str)

    def fetchAllWorkFolders(self, currentPath, byRoot=False):
        if byRoot:
            rootPath = currentPath
        else:
            rootPath = currentPath.split("GenBank_File")[0] \
                if "GenBank_File" in currentPath else currentPath.split("Other_File")[0]
        rootPath = rootPath.rstrip(r"/").rstrip(os.sep)
        list_wFolders = []
        gb_path = rootPath + os.sep + "GenBank_File"
        for i in os.listdir(gb_path):
            if os.path.isdir(gb_path + os.sep + i) and i != "recycled":
                list_wFolders.append(gb_path + os.sep + i)
        other_path = rootPath + os.sep + "Other_File"
        for i in os.listdir(other_path):
            if os.path.isdir(other_path + os.sep + i) and i != "recycled":
                list_wFolders.append(other_path + os.sep + i)
        return list_wFolders

    def swithWorkPath(self, action, init=False, parent=None):
        allItems = self.fetchAllWorkFolders(parent.workPath)
        items = []
        dict_items = {}
        index = 0
        for num,i in enumerate(allItems):
            if os.path.samefile(i, parent.workPath):
                index = num
            if parent.parent.isWorkFolder(i, mode="gb"):
                item_text = "\"%s\" in GenBank_File" % os.path.basename(i)
                items.append(item_text)
            else:
                item_text = "\"%s\" in Other_File" % os.path.basename(i)
                items.append(item_text)
            dict_items[item_text] = i
        if not init:
            item, ok = QInputDialog.getItem(parent, "Set work path",
                                                  "Work path:", items, index, False)
            if ok and item:
                ##初始化工作路径
                action.setText("Work folder: %s"%item)
                parent.workPath = dict_items[item]
                action.setToolTip(parent.workPath)
                return
        action.setText("Work folder: %s"%items[index])
        action.setToolTip(parent.workPath)

    def fetch_output_dir_name(self, action):
        #如果给flowchart命名了，那么就用那个名字来？
        return time.strftime('%Y_%m_%d-%H_%M_%S', time.localtime(time.time())) \
            if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+", action.text()) or (action.text() == "Output Dir: ")\
            else action.text().replace("Output Dir: ", "")

    def settingsGroup2Group(self, qsettingsPath, group1, group2, baseGroup=None):
        #将group1的设置复制到group2,如果group1是空，就用默认的那个。
        qsettings = QSettings(qsettingsPath, QSettings.IniFormat)
        qsettings.setFallbacksEnabled(False)
        if baseGroup:
            #如果已经有一个group，就进入它
            qsettings.beginGroup(baseGroup)
        #先清空group2
        qsettings.beginGroup(group2)
        qsettings.remove("")
        qsettings.endGroup()
        #将group1的设置拷贝到字典
        qsettings.beginGroup(group1)
        dict_settings = OrderedDict((i, qsettings.value(i, "")) for i in qsettings.allKeys())
        qsettings.endGroup()
        #拷贝到group2
        qsettings.beginGroup(group2)
        for j in dict_settings:
            qsettings.setValue(j, dict_settings[j])
        qsettings.endGroup()
        if baseGroup:
            qsettings.endGroup()

    def getSTDOUT(self, popen):
        stdout = []
        try:
            while True:
                try:
                    out_line = popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = popen.stdout.readline().decode("gbk", errors="ignore")
                if out_line == "" and popen.poll() is not None:
                    break
                stdout.append(out_line)
        except:
            stdout = []
        return "".join(stdout)

    def getDefaultpluginPath(self, plugin=""):
        path = ""
        # if plugin == "mafft":
        #     if platform.system().lower() == "windows":
        #         target = dict_plugin_settings["mafft"]["target_win"]
        #     elif platform.system().lower() == "darwin":
        #         target = dict_plugin_settings["mafft"]["target_mac"]
        # elif plugin == "PF2":
        #     # path = os.path.join(self.thisPath, "plugins", "partitionfinder-2.1.1")
        #     if platform.system().lower() == "windows":
        #         target = dict_plugin_settings["PF2"]["target_win"]
        #     elif platform.system().lower() == "darwin":
        #         target = dict_plugin_settings["PF2"]["target_mac"]
        # elif plugin == "gblocks":
        #     if platform.system().lower() == "windows":
        #         path = os.path.join(self.thisPath, "plugins", "Gblocks_0.91b", "Gblocks.exe")
        #     elif platform.system().lower() == "darwin":
        #         path = os.path.join(self.thisPath, "plugins", "Gblocks_0.91b", "Gblocks")
        # elif plugin == "iq-tree":
        #     if platform.system().lower() == "windows":
        #         if platform.machine().endswith('64'):
        #             path = os.path.join(self.thisPath, "plugins", "iqtree-1.6.8-Windows", "bin", "iqtree.exe")
        #         else:
        #             path = os.path.join(self.thisPath, "plugins", "iqtree-1.6.8-Windows32", "bin", "iqtree.exe")
        #     elif platform.system().lower() == "darwin":
        #         path = os.path.join(self.thisPath, "plugins", "iqtree-1.6.8-MacOSX", "bin", "iqtree")
        # elif plugin == "MrBayes":
        #     if platform.system().lower() == "windows":
        #         if platform.machine().endswith('64'):
        #             path = os.path.join(self.thisPath, "plugins", "MrBayes", "mrbayes_x64.exe")
        #         else:
        #             path = os.path.join(self.thisPath, "plugins", "MrBayes", "mrbayes_x86.exe")
        #     elif platform.system().lower() == "darwin":
        #         path = os.path.join(self.thisPath, "plugins", "MrBayes", "mb")
        # elif plugin == "macse":
        #     path = os.path.join(self.thisPath, "plugins", "macse_v2.03.jar")
        # elif plugin == "trimAl":
        #     if platform.system().lower() == "windows":
        #         path = os.path.join(self.thisPath, "plugins", "trimAl", "bin", "trimal.exe")
        # elif plugin == "CodonW":
        #     if platform.system().lower() == "windows":
        #         path = os.path.join(self.thisPath, "plugins", "Win32CodonW", "CodonW.exe")
        #     elif platform.system().lower() == "darwin":
        #         path = os.path.join(self.thisPath, "plugins", "MacOSCodonW", "codonw")
        # else:
        #     if platform.system().lower() == "windows":
        #         path = os.path.join(self.thisPath, "plugins",
        #                             dict_plugin_settings[plugin]["relative_path_win"])
        #     elif platform.system().lower() == "darwin":
        #         path = os.path.join(self.thisPath, "plugins",
        #                             dict_plugin_settings[plugin]["relative_path_mac"])
        #     else:
        #         path = os.path.join(self.thisPath, "plugins",
        #                             dict_plugin_settings[plugin]["relative_path_linux"])
        if platform.system().lower() == "windows":
            target = dict_plugin_settings[plugin]["target_win"]
        elif platform.system().lower() == "darwin":
            target = dict_plugin_settings[plugin]["target_mac"]
        else:
            target = None
        if type(target) == list:
            for target_file in target:
                path_glob = glob.glob(f"{self.thisPath}{os.sep}plugins{os.sep}**{os.sep}{target_file}", recursive=True)
                if path_glob:
                    path = path_glob[0]
                    break
        else:
            if target:
                path_glob = glob.glob(f"{self.thisPath}{os.sep}plugins{os.sep}**{os.sep}{target}", recursive=True)
                if path_glob:
                    path = path_glob[0]
        # print(plugin, path)
        return path

    def autoInputDisbled(self):
        if not hasattr(self, "mainwindow_settings"):
            self.mainwindow_settings = QSettings(
                self.thisPath +
                '/settings/mainwindow_settings.ini',
                QSettings.IniFormat, parent=self)
            # File only, no fallback to registry or or.
            self.mainwindow_settings.setFallbacksEnabled(False)
        return not self.str2bool(self.mainwindow_settings.value("auto detect", "true"))

    def init_judge(self, mode=None, filePath=None, parent=None):
        if parent.isOtherFileSelected():
            ##展示的是otherfile的工作文件夹, 只导入选择的文件
            autoInputs = self.judgeAutoInputs(mode, resultsPath=filePath) # 判断other file的文件
            # 特殊情况的autoInputs  modelfinder与MRBAYES：[list_alignments, None]；IQ-TREE：[list_alignments, ["", None]]
            list_align, list_docx = parent.fetchSelectFile(filePath)
            if mode in ["ModelFinder", "IQ-TREE", "MrBayes", "FastTree"]:
                list_alignments = autoInputs[0]
                msa = list(set(list_alignments).intersection(set(list_align)))
                autoInputs = [msa, None] if mode != "IQ-TREE" else [msa, ["", None]]
            else:
                autoInputs = list(set(autoInputs).intersection(set(list_align)))
        elif parent.stackedWidget.currentIndex() != 8: #没有展示结果界面以及选中.data的时候
            if mode in ["ModelFinder", "MrBayes", "FastTree"]:
                autoInputs = [None, None]
            elif mode == "IQ-TREE":
                autoInputs = [None, ["", None]]
            else:
                autoInputs = []
        else:
            ##先找到可以用于自动导入的路径
            resultsPath = parent.fetchResultsPath()
            if not resultsPath:
                ## 如果没有选中一个结果文件夹，自动获得最新的结果文件夹
                if parent.isResultsFolder(filePath):
                    subResults = self.fetchSubResults(filePath)
                    if subResults:
                        resultsPath = subResults[0]
            autoInputs = self.judgeAutoInputs(mode, resultsPath=resultsPath)
        return autoInputs

    def centerWindow(self, window):
        if platform.system().lower() != "linux":
            # linux 系统会出现找不到窗口的情况
            frameGm = window.frameGeometry()
            screen = QApplication.desktop().screenNumber(
                QApplication.desktop().cursor().pos())
            centerPoint = QApplication.desktop().screenGeometry(screen).center()
            frameGm.moveCenter(centerPoint)
            window.move(frameGm.topLeft())

    def emitCommands(self, logGuiSig, commands):
        logGuiSig.emit("%sCommands%s\n%s\n%s" % ("=" * 45, "=" * 45, commands, "=" * 98))

    def getCurrentTaxSetData(self):
        ini_data = OrderedDict(
            [("Default taxonomy settings", [['Class', 'Order', 'Superfamily', 'Family', 'Subfamily', 'Genus'],
                                           [['', '*tera', '*dea', '*dae', '*nae', ''],
                                            ['', '', '*ida', '', '', ''],
                                            ['', '', '', '', '', ''],
                                            ['', '', '', '', '', ''],
                                            ['', '', '', '', '', '']]])])
        currentTaxSetName = self.settings_ini.value("comboBox", "Default taxonomy settings")
        return self.settings_ini.value("Taxonomy Recognition", ini_data)[currentTaxSetName]

    def judgeWindowSize(self, setting, width, height):
        qsize = setting.value('size', QSize(width, height))
        width_, height_ = qsize.width(), qsize.height()
        return qsize if width_ >= width and height_ >= height else QSize(width, height)

    def read_tree(self, file, parent=None):
        def read_use_ete3(tree):
            flag = False
            tre = None
            for format in list(range(10)) + [100]:
                try:
                    tre = Tree(tree, format=format)
                    flag=True
                    break
                except: pass
                try:
                    tre = Tree(tree, format=format, quoted_node_names=True)
                    flag=True
                    break
                except: pass
            return flag, tre
        ## ete3 读树
        ok, tre = read_use_ete3(file)
        if ok:
            return tre
        ## Biopython的phylo读树
        for format in ["nexus", "newick", "phyloxml", "nexml"]:
            try:
                tree = next(Phylo.parse(file, format))
                if tree.count_terminals() == 1:
                    raise Exception("File read filed!")
                nwk_tree_str = tree.format("newick")
                ok, tre = read_use_ete3(nwk_tree_str)
                if ok:
                    return tre
            except:
                pass
        QMessageBox.information(
            parent,
            "Import tree",
            "<p style='line-height:25px; height:25px'>Tree imported failed, please check the format!</p>")
        return


class WorkThread(QThread):
    # workerfinished = pyqtSignal()

    def __init__(self, function, parent=None):
        super(WorkThread, self).__init__(parent)
        self.function = function
        # self.finished.connect(self.stopWork)
        # print("主线程", QThread.currentThreadId())

    def run(self):
        self.function()

    def stopWork(self):
        if self.isRunning():
            self.terminate()
            self.wait()


class WorkRunThread(QRunnable):

    def __init__(self, function):
        super(WorkRunThread, self).__init__()
        self.function = function
        self.setAutoDelete(True)
        # self.finished.connect(self.stopWork)
        # print("主线程", QThread.currentThreadId())

    def run(self):
        self.function()


class SeqGrab(object):  # 统计序列

    def __init__(self, sequence, decimal=1):
        self.sequence = sequence.upper()
        self.length = len(self.sequence)
        self.size = str(self.length)
        self.decimal = "%." + "%df" % decimal
        self.A = self.sequence.count("A")
        self.T = self.sequence.count("T")
        self.C = self.sequence.count("C")
        self.G = self.sequence.count("G")
        self.A_percent = self.decimal % (self.A * 100 / self.length)
        self.T_percent = self.decimal % (self.T * 100 / self.length)
        self.C_percent = self.decimal % (self.C * 100 / self.length)
        self.G_percent = self.decimal % (self.G * 100 / self.length)
        self.AT_percent = self.decimal % (
            float(self.A_percent) + float(self.T_percent))
        self.GC_percent = self.decimal % (
            float(self.C_percent) + float(self.G_percent))
        self.GT_percent = self.decimal % (
            float(self.G_percent) + float(self.T_percent))
        if self.A != 0 or self.T != 0:  # 避免不包含AT的序列
            self.AT_skew = "%.3f" % ((self.A - self.T) / (self.A + self.T))
        else:
            self.AT_skew = "NA"
        if self.G != 0 or self.C != 0:
            self.GC_skew = "%.3f" % ((self.G - self.C) / (self.G + self.C))
        else:
            self.GC_skew = "NA"

    def splitCodon(self):
        first, second, third = "", "", ""
        for num, i in enumerate(self.sequence):
            if num % 3 == 0:
                first += i
            elif num % 3 == 1:
                second += i
            else:
                third += i
        return first, second, third


class HttpWindowDownload(QDialog):
    errorSig = pyqtSignal(str)

    def __init__(self, parent=None, **dict_args):
        super(HttpWindowDownload, self).__init__(parent)
        self.parent = parent
        self.factory = Factory()
        self.url = QUrl(dict_args["httpURL"])
        self.exportPath = dict_args["exportPath"]
        self.plugin_path = os.path.dirname(self.exportPath)
        self.outFile = QFile(self.exportPath)
        self.httpGetId = 0
        self.httpRequestAborted = False
        self.download_button = dict_args["download_button"]
        self.tableWidget = dict_args["tableWidget"]
        self.row = dict_args["row"]
        self.status = dict_args["status"]
        self.qss_file = dict_args["qss"]
        self.installButtonSig = dict_args["installButtonSig"]
        self.flag = dict_args["flag"]
        self.exe_window = dict_args[
            "exe_path_window"] if "exe_path_window" in dict_args else None
        self.save_pathSig = dict_args["save_pathSig"]
        self.dict_args = dict_args
        self.target_exe = dict_args["target"]
        self.qnam = QNetworkAccessManager()
        self.qnam.authenticationRequired.connect(
            self.slotAuthenticationRequired)
        self.qnam.sslErrors.connect(self.sslErrors)
        self.progressDialog = QProgressDialog(self.parent)
        self.progressDialog.resize(354, 145)
        self.progressDialog.canceled.connect(self.cancelDownload)
        self.progress_text = ""
        self.errorSig.connect(self.popupException)
        self.downloadFile()

    def startRequest(self, url):
        self.reply = self.qnam.get(QNetworkRequest(url))
        self.reply.finished.connect(self.httpFinished)
        self.reply.readyRead.connect(self.httpReadyRead)
        self.reply.downloadProgress.connect(self.updateDataReadProgress)

    def downloadFile(self):
        fileName = os.path.splitext(os.path.basename(self.exportPath))[0]
        if QFile.exists(fileName):
            try:
                QFile.remove(fileName)
            except:
                pass
        if not self.outFile.open(QIODevice.WriteOnly):
            QMessageBox.information(self, "HTTP",
                                          "Unable to save the file %s: %s." % (fileName, self.outFile.errorString()))
            self.outFile = None
            return

        self.progressDialog.setWindowTitle("HTTP")
        self.top_text = "    Downloading %s..." % fileName + " " * \
            5 if platform.system().lower(
            ) == "darwin" else "Downloading %s..." % fileName + " " * 10
        self.progressDialog.setLabelText(self.top_text)
        self.httpRequestAborted = False
        self.progressDialog.setWindowFlags(
            self.progressDialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.startRequest(self.url)
        self.progressDialog.exec_()

    def cancelDownload(self):
        self.httpRequestAborted = True
        self.reply.abort()
        self.installButtonSig.emit(
            [self.download_button, self.tableWidget, self.row, "cancel", self.qss_file])

    def httpFinished(self):
        if self.httpRequestAborted:
            if self.outFile is not None:
                self.outFile.close()
                self.outFile.remove()
                self.outFile = None
            self.reply.deleteLater()
            self.reply = None
            self.progressDialog.hide()
            return
        self.progressDialog.hide()
        self.outFile.flush()
        self.outFile.close()
        redirectionTarget = self.reply.attribute(
            QNetworkRequest.RedirectionTargetAttribute)
        if self.reply.error():
            self.outFile.remove()
            QMessageBox.information(self, "HTTP",
                                    "Download failed: %s." % self.reply.errorString())
        elif redirectionTarget is not None:
            newUrl = self.url.resolved(redirectionTarget)

            ret = QMessageBox.question(self, "HTTP",
                                       "Redirect to %s?" % newUrl.toString(),
                                       QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.url = newUrl
                self.reply.deleteLater()
                self.reply = None
                self.outFile.open(QIODevice.WriteOnly)
                self.outFile.resize(0)
                self.startRequest(self.url)
                return
        if self.flag == "RscriptPath":
            if platform.system().lower() == "windows":
                subprocess.call(self.exportPath)
                binary = "Rscript.exe"
            elif platform.system().lower() == "darwin":
                os.system("chmod 755 %s" % self.exportPath)
                os.system("open %s" % self.exportPath)
                binary = "Rscript"
            self.installButtonSig.emit(
                [self.download_button, self.tableWidget, self.row, "uninstall", self.qss_file])  #方便执行那个按钮
            text = "Please specify the path of <span style='font-weight:600; color:#ff0000;'>'%s'</span> you installed!" % binary
            self.dict_args["installFinishedSig"].emit(text, "Rscript")
        elif self.flag == "python27":
            if platform.system().lower() == "windows":
                subprocess.call(self.exportPath)
                binary = "python.exe"
            elif platform.system().lower() == "darwin":
                os.system("chmod 755 %s" % self.exportPath)
                os.system("open %s" % self.exportPath)
                binary = "python"
            self.installButtonSig.emit(
                [self.download_button, self.tableWidget, self.row, "uninstall", self.qss_file])  # 方便执行那个按钮
            text = "Please specify the path of <span style='font-weight:600; color:#ff0000;'>'%s'</span> you installed!</p>" % binary
            self.dict_args["installFinishedSig"].emit(text, "py27")
        elif self.flag == "plot_engine":
            from src.update import UpdateAPP
            self.parent.zipSig.emit("Unziping")
            self.worker = WorkThread(lambda : UpdateAPP().unzipNewApp(self.exportPath), parent=self)
            self.worker.start()
            self.worker.finished.connect(lambda : [self.parent.zipSig.emit("Unzip finished"),
                                                   self.dict_args["installFinishedSig"].emit("installed successfully!",
                                                                                             "plot_engine")])
        else:
            self.parent.zipSig.emit("Unziping")
            self.zipWorker = WorkThread(
                lambda: self.factory.unZip(self.exportPath, self.target_exe, self.errorSig), parent=self)
            self.zipWorker.start()
            self.zipWorker.finished.connect(lambda : [self.parent.zipSig.emit("Unzip finished"), self.unzipFinished()])
            # self.factory.unZip(self.exportPath, self.target_exe)
            # self.parent.zipSig.emit("Unzip finished")
            # self.unzipFinished()
        self.reply.deleteLater()
        self.reply = None
        self.outFile = None

    def httpReadyRead(self):
        if self.outFile is not None:
            self.outFile.write(self.reply.readAll())

    def updateDataReadProgress(self, bytesRead, totalBytes):
        if self.httpRequestAborted:
            return
        progress_text = self.humanbytes(
            bytesRead) + "/" + self.humanbytes(totalBytes)
        if self.progress_text != progress_text:
            self.top_text = self.top_text.replace(
                self.progress_text, progress_text) if self.progress_text != "" else self.top_text + progress_text
            self.progressDialog.setLabelText(self.top_text)
            self.progress_text = progress_text
        oldValue = self.progressDialog.value()
        done_int = int(100 * bytesRead/totalBytes)
        if done_int > oldValue:
            self.progressDialog.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def slotAuthenticationRequired(self, authenticator):
        import os
        from PyQt5 import uic

        ui = os.path.join(os.path.dirname(self.plugin_path) + os.sep + "uifiles", 'authenticationdialog.ui')
        dlg = uic.loadUi(ui)
        dlg.adjustSize()
        dlg.siteDescription.setText(
            "%s at %s" % (authenticator.realm(), self.url.host()))

        dlg.userEdit.setText(self.url.userName())
        dlg.passwordEdit.setText(self.url.password())

        if dlg.exec_() == QDialog.Accepted:
            authenticator.setUser(dlg.userEdit.text())
            authenticator.setPassword(dlg.passwordEdit.text())

    def sslErrors(self, reply, errors):
        errorString = ", ".join([str(error.errorString()) for error in errors])

        ret = QMessageBox.warning(self, "HTTP",
                                  "One or more SSL errors has occurred: %s" % errorString,
                                  QMessageBox.Ignore | QMessageBox.Abort)

        if ret == QMessageBox.Ignore:
            self.reply.ignoreSslErrors()

    def humanbytes(self, B):
        'Return the given bytes as a human friendly KB, MB, GB, or TB string'
        B = float(B)
        KB = float(1024)
        MB = float(KB ** 2)  # 1,048,576
        GB = float(KB ** 3)  # 1,073,741,824
        TB = float(KB ** 4)  # 1,099,511,627,776
        if B < KB:
            return '{0} {1}'.format(B, 'Bytes' if 0 == B > 1 else 'Byte')
        elif KB <= B < MB:
            return '{0:.2f} KB'.format(B / KB)
        elif MB <= B < GB:
            return '{0:.2f} MB'.format(B / MB)
        elif GB <= B < TB:
            return '{0:.2f} GB'.format(B / GB)
        elif TB <= B:
            return '{0:.2f} TB'.format(B / TB)

    def unzipFinished(self):
        path = self.plugin_path + os.sep + \
               self.factory.topFolder if self.flag == "PF2" else self.plugin_path + \
                                                    os.sep + self.factory.exe_file
        if platform.system().lower() in ["darwin", "linux"]:
            # 给每个文件权限
            if self.factory.topFolder:
                os.system("chmod -R 755 %s" %
                          (self.plugin_path + os.sep + self.factory.topFolder))
        if path:
            # self.installButtonSig.emit(
            #     [self.download_button, self.tableWidget, self.row, self.status, self.qss_file])
            self.save_pathSig.emit(f"{self.flag}##**", path)
            # 会刷新所有button的status
            self.dict_args["installFinishedSig"].emit("installed successfully!", "other plugins")
            # QMessageBox.information(
            #     self.parent, "Settings", "<p style='line-height:25px;height:25px'>installed successfully!</p>")
        else:
            self.installButtonSig.emit(
                [self.download_button, self.tableWidget, self.row, "uninstall", self.qss_file])
            # QMessageBox.information(
            #     self.parent, "Settings", "<p style='line-height:25px;height:25px'>installed failed!</p>")
        if QFile.exists(self.exportPath):
            # 安装完删除安装包
            try:
                QFile.remove(self.exportPath)
            except:
                pass

    def popupException(self, exception):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


class HttpRead(QDialog):
    # 该方法不能放子线程里面，因为它本来就是异步的
    finishedSig = pyqtSignal(str)

    def __init__(self, parent=None):
        super(HttpRead, self).__init__(parent)
        # self.doRequest()
        # request = QNetworkRequest()
        # request.setUrl(QUrl(self.url))
        # manager = QNetworkAccessManager()
        # replyObject = manager.get(request)
        # print(replyObject)
        # replyObject.finished.connect(print)

    def doRequest(self, url):
        self.url = url
        req = QNetworkRequest(QUrl(self.url))
        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self.handleResponse)
        self.nam.get(req)

    def handleResponse(self, reply):
        er = reply.error()
        if er == QNetworkReply.NoError:
            bytes_string = reply.readAll()
            # print(str(bytes_string, 'utf-8'))
            self.finishedSig.emit(str(bytes_string, 'utf-8'))
        else:
            self.finishedSig.emit("Error: " + reply.errorString())
            # print("Error occured: ", er)
            # print(reply.errorString())
        # QCoreApplication.quit()


class QSingleApplication(QApplication):

    messageReceived = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super(QSingleApplication, self).__init__(*args, **kwargs)
        appid = QApplication.applicationFilePath().lower().split("/")[-1]
        self._socketName = "qtsingleapp-" + appid
#         print("socketName", self._socketName)
        self._activationWindow = None
        self._activateOnMessage = False
        self._socketServer = None
        self._socketIn = None
        self._socketOut = None
        self._running = False

        # 先尝试连接
        self._socketOut = QLocalSocket(self)
        self._socketOut.connectToServer(self._socketName)
        self._socketOut.error.connect(self.handleError)
        self._running = self._socketOut.waitForConnected()

        if not self._running:  # 程序未运行
            self._socketOut.close()
            del self._socketOut
            self._socketServer = QLocalServer(self)
            self._socketServer.listen(self._socketName)
            self._socketServer.newConnection.connect(self._onNewConnection)
            self.aboutToQuit.connect(self.removeServer)

    def handleError(self, message):
        print("handleError message: ", message)

    def isRunning(self):
        return self._running

    def activationWindow(self):
        return self._activationWindow

    def setActivationWindow(self, activationWindow, activateOnMessage=True):
        self._activationWindow = activationWindow
        self._activateOnMessage = activateOnMessage

    def activateWindow(self):
        if not self._activationWindow:
            return
        self._activationWindow.setWindowState(
            self._activationWindow.windowState() & ~Qt.WindowMinimized)
        self._activationWindow.raise_()
        self._activationWindow.activateWindow()

    def sendMessage(self, message, msecs=5000):
        if not self._socketOut:
            return False
        if not isinstance(message, bytes):
            message = str(message).encode()
        self._socketOut.write(message)
        if not self._socketOut.waitForBytesWritten(msecs):
            raise RuntimeError("Bytes not written within %ss" %
                               (msecs / 1000.))
        return True

    def _onNewConnection(self):
        if self._socketIn:
            self._socketIn.readyRead.disconnect(self._onReadyRead)
        self._socketIn = self._socketServer.nextPendingConnection()
        if not self._socketIn:
            return
        self._socketIn.readyRead.connect(self._onReadyRead)
        if self._activateOnMessage:
            self.activateWindow()

    def _onReadyRead(self):
        while 1:
            message = self._socketIn.readLine()
            if not message:
                break
            print("Message received: ", message)
            self.messageReceived.emit(message.data().decode())

    def removeServer(self):
        self._socketServer.close()
        self._socketServer.removeServer(self._socketName)


class Parsefmt(object):

    def __init__(self, error_message="", warning_message=""):
        self.error_message = error_message
        self.warning_message = warning_message
        self.factory = Factory()

    def judge(self, seq):  # 要拿全部序列来判断，因为有可能会有很长的-；不过这个方法可以筛选是否为序列
        set_standard = {'A', 'C', '-', 'T', 'G', 'N', '?'}
        set_RNA = {'A', 'C', '-', 'U', 'G', 'N', '?'}
        set_seq = set(seq.upper())
        list_rest = list(set_seq - set_standard)
        list_rest_RNA = list(set_seq - set_RNA)
        count_rest = sum([seq.upper().count(i) for i in list_rest])
        count_rest_RNA = sum([seq.upper().count(i) for i in list_rest_RNA])
        if not len(seq):
            return "UNKNOWN"
        count_rest_ratio = count_rest / len(seq)
        count_rest_ratio_RNA = count_rest_RNA / len(seq)
        if count_rest_ratio < 0.03:
            return 'DNA'
        elif count_rest_ratio_RNA < 0.03:
            return 'RNA'
        else:
            return 'PROTEIN'

    def standardizeFas(self, handle, removeAlign=False):
        dict_fas = self.read_fas(handle, removeAlign=removeAlign)
        return "".join([f'>{key}\n{value}\n' for key,value in dict_fas.items()])

    def read_fas(self, file, base=None, proportion=None, processSig=None,
                 removeAlign=False, clean_name=True):
        if not hasattr(self, "name_mapping"):
            self.name_mapping = {}
        dict_fas = {}
        try:
            handle = open(file, encoding="utf-8", errors='ignore')
        except:
            handle = file
        for line in handle:
            line = line.strip()
            if line.startswith(">"):
                old_name = line.lstrip(">")
                seq_name = self.factory.refineName(old_name) if clean_name else old_name
                self.name_mapping[old_name] = seq_name
            else:
                if removeAlign:
                    line = line.replace("-", "")
                dict_fas.setdefault(seq_name, []).append(line) # re.sub(r"\s", "", line)
        handle.close()
        for key,value in dict_fas.items():
            dict_fas[key] = re.sub(r"\s", "", "".join(value))
        if processSig:
            processSig.emit(base + proportion)
        return dict_fas

    # 生成self.dict_taxon
    def readfile(self, file, base=None, proportion=None, processSig=None, clean_name=True):
        # 进度条相关
        if processSig:
            processSig.emit(0)
        self.name_mapping = {}
        self.file = file
        with open(self.file, encoding="utf-8", errors='ignore') as f:
            self.content = f.read()
        # self.content = content
        if os.path.splitext(file)[1].upper() in [".FA", ".FAS", ".FASTA", ".FAA", ".FNA", ".FFN", ".FRN"]:
            # FAS 格式
            self.standard_dict_taxon = self.read_fas(file, base=base, proportion=proportion,
                                                    processSig=processSig, clean_name=clean_name)
            self.dict_taxon = self.standard_dict_taxon
            return self.standard_dict_taxon
        self.dict_taxon = OrderedDict()
        self.rgxinitial = re.compile(
            r"(?smi)(^[\t ]*MATRIX[\r\n]|^ *(\d+) +(\d+)[\r\n]|^[\r\n])(.+?)(^[\r\n;])")
        self.rgxphy = re.compile(r"(\d+) +(\d+)")
        self.rgxnex = re.compile(r"(?i)ntax=\s*(\d+).+nchar=\s*(\d+)")
        # 判断是否裸数据
        if self.content.count("\n") <= 1:  # 裸数据只允许存在一行
            self.dict_taxon[os.path.basename(self.file)] = [re.sub(
                r" |\t|\n|\r", "", self.content)]
        else:
            # 判定是否为nex格式
            if self.rgxnex.search(self.content) and re.search(
                    r"matrix\s*\n", self.content, re.I):
                taxnum, seqlenth = int(
                    self.rgxnex.search(self.content).group(1)), int(
                    self.rgxnex.search(self.content).group(2))
                flag = "phynex"
            elif self.rgxphy.search(self.content) and (not re.search(r">.+[\r\n]", self.content)):
                taxnum, seqlenth = int(
                    self.rgxphy.search(self.content).group(1)), int(
                    self.rgxphy.search(self.content).group(2))
                flag = "phynex"
            else:
                flag = "others"
            if flag == "phynex":
                stop = 0
                self.content += "\n"  # 因为有些交互式格式最后没有\n，所以最后一点儿无法匹配上
                initial_match = self.rgxinitial.search(
                    self.content, stop)  # 详见【匹配上的东西.txt】
                count = 1  # 用于处理是否第1次都匹配上hash1
                fmt_flag = 0  # 如果是交互式，flag保持0，就不进行sequential的匹配
                if not initial_match:
                    fmt_flag = 1
                # 进度条相关
                if processSig:
                    total = len(self.rgxinitial.findall(self.content))
                    count_proc = 0
                # 只要能匹配上就进行，如果下面的hash1也没匹配上，就不是交互式
                has_interleave_seq = False
                while initial_match and fmt_flag != 1:
                    item = initial_match.groups()[-2]  # 取出序列部分
                    stop = initial_match.span()[1] - 4
                    # 如果不处理序列内部有空格的情况，这里的^符号可以去掉，那么就可以匹配名字前面有空白字符的情况
                    hash1 = re.findall(
                        r"(?mi)(^[^\r\n\t\f\v #]+)[ \t]+([GAVLIFWYDHNEKQMRSTCPUBXJ\-\?]+)[\r\n]", item)
                    # 交互式特征匹配，名字+空白字符+序列
                    hash2 = re.findall(
                        r"(?mi)^[ \t]+([GAVLIFWYDHNEKQMRSTCPUBXJ\-\?]+)[\r\n]", item)
                    # 前面没有名字的情况
                    hash1_beta = re.findall(
                        r"(?mi)(^[^\r\n\t\f\v #]+)[ \t]+(( [GAVLIFWYDHNEKQMRSTCPUBXJ\-\?]+)+) ?[\r\n]",
                        item)  # 这里新加了一个^以区别下面的空格起头
                    # 匹配交互式，每隔10个碱基一个空格的格式
                    hash2_beta = re.findall(
                        r"(?mi)^[ \t]+(( [GAVLIFWYDHNEKQMRSTCPUBXJ\-\?]+)+) ?[\r\n]", item)
                    # 如果没匹配上，就是[],由于是第一次匹配上，可能会有nex的heading在里面
                    if hash1 and count == 1:
                        count += 1  # hash1匹配上了的标志
                        list_spes = []  # 存放序列长度
                        for spe, seq in hash1:
                            list_spes.append(spe)
                            self.dict_taxon[spe] = [seq]  # seq要替换其他符号
                            has_interleave_seq = True
                        if len(list_spes) != taxnum:
                            # list_spes[0:-taxnum]索引非taxon
                            for i in list_spes[0:-taxnum]:
                                self.dict_taxon.pop(i)  # 删除匹配到的heading的spe
                    elif hash1 and count == 2:  # 第二个匹配位置，此时count应该很大了
                        for spe, seq in hash1:
                            if spe in self.dict_taxon:
                                self.dict_taxon[spe].append(seq)
                                has_interleave_seq = True
                            else:
                                self.error_message += "Unexpected taxon: %s\n" % spe
                    # 处理第二次是以空格开头的情况
                    elif hash1 and hash2 and count == 2:
                        list_inter_keys = list(self.dict_taxon.keys())
                        for ords, seq in enumerate(hash2):
                            self.dict_taxon[
                                list_inter_keys[ords]].append(seq)  # 这里有一个顺序
                            has_interleave_seq = True
                        if ords != taxnum - 1:
                            self.error_message += "Unexpected taxon number: %d" % (
                                ords + 1)
                    # 以下3个elif处理序列内部有空格的情况
                    elif hash1_beta != [] and count == 1:
                        count += 1
                        list_spes = []  # 存放序列长度
                        # ('XtIFNi13', 'MSQ------S PIILPVVLLL LPVLVL---- CSPECPWLDN KGEFQVQKIL ', 'KGEFQVQKIL ')
                        for spe, seq, last in hash1_beta:
                            list_spes.append(spe)
                            self.dict_taxon[spe] = [seq.replace(
                                " ", "")]  # seq要替换其他符号
                            has_interleave_seq = True
                        if len(list_spes) != taxnum:
                            for i in list_spes[0:-taxnum]:
                                self.dict_taxon.pop(i)  # 删除匹配到的heading的spe
                    elif hash1_beta != [] and count == 2:
                        for spe, seq, last in hash1_beta:
                            if spe in self.dict_taxon:
                                self.dict_taxon[spe].append(seq.replace(" ", ""))
                                has_interleave_seq = True
                            else:
                                self.error_message += "Unexpected taxon: %s\n" % spe
                    # 处理第二次是以空格开头的情况
                    elif hash1_beta == [] and hash2_beta != [] and count == 2:
                        list_inter_keys = list(self.dict_taxon.keys())
                        for ords, seqs in enumerate(hash2_beta):
                            # 这里seqs=('TVLDHMEPTE EIPDDCFLP- --LPPIDFTH N-MSLGAAAA IVDKVARETI ', 'IVDKVARETI ')
                            self.dict_taxon[list_inter_keys[ords]
                                            ].append(seqs[0].replace(" ", ""))
                            has_interleave_seq = True
                        if ords != taxnum - 1:
                            self.error_message += "Unexpected taxon number: %d" % (
                                ords + 1)
                    else:  # 匹配不上hash1和hash1_beta
                        if not has_interleave_seq:
                            # print("匹配不上hash1和hash1_beta", fmt_flag)
                            fmt_flag = 1
                    if processSig:
                        count_proc += 1
                        processSig.emit(
                            base + (count_proc / total) * proportion)
                    initial_match = self.rgxinitial.search(self.content, stop)
                list_iterv_keys = list(self.dict_taxon.keys())
                # interleave 判定是否正确
                if list_iterv_keys != []:  # 不等于[]就证明是交互式
                    for each in list_iterv_keys:
                        current_seqLen = len("".join(self.dict_taxon[each]))
                        if current_seqLen != seqlenth:
                            # print(self.dict_taxon, self.dict_taxon[each])
                            # print(each, "".join(self.dict_taxon[each]))
                            self.error_message += "Unexpected sequence length in 【%s】, %d : %d\n!" % (each, current_seqLen, seqlenth)
                # sequential
                if fmt_flag:  # 证明不是交互式，进行sequential匹配
                    # 进度条相关
                    if processSig:
                        total = self.content.count("\n")
                        count_proc = 0
                    with open(self.file, encoding="utf-8", errors='ignore') as f1:
                        line = f1.readline()
                        if re.search(r"matrix\s*\n", self.content, re.I):  # nex格式
                            while re.search(
                                    r"matrix\s*\n", line, re.I) is None:
                                line = f1.readline()
                        elif re.search(r"(\d+) +(\d+)", self.content):  # phy和paml格式
                            while re.search(
                                    r"(\d+) +(\d+)", line, re.I) is None:
                                line = f1.readline()
                        line = f1.readline()
                        messages = ""
                        while line:
                            while line and (line == "\n" or line == "\r\n"):  # 跳过空行
                                line = f1.readline()
                                if processSig:
                                    count_proc += 1
                                    processSig.emit(
                                        base + (count_proc / total) * proportion)
                            # 这是单行的sequential
                            if re.search(
                                r"([^\r\n\t\f\v ]+)[ \t]+([GAVLIFWYDHNEKQMRSTCPUBXJ\-\?]+)[\r\n]",
                                line,
                                    re.I):
                                seqt_name = re.search(
                                    r"([^\r\n\t\f\v ]+)[ \t]+([GAVLIFWYDHNEKQMRSTCPUBXJ\-\?]+)[\r\n]",
                                    line,
                                    re.I).group(1)
                                seqt_seq = [re.search(
                                    r"([^\r\n\t\f\v ]+)[ \t]+([GAVLIFWYDHNEKQMRSTCPUBXJ\-\?]+)[\r\n]",
                                    line,
                                    re.I).group(2)]
                                if len(seqt_seq[0]) == seqlenth:
                                    self.dict_taxon[seqt_name] = seqt_seq
                                else:
                                    # print(seqt_seq)
                                    # print(self.dict_taxon, seqt_seq)
                                    self.error_message += "Unexpected sequence length in 【%s】!, %d : %d\n!" % (seqt_name, len(seqt_seq[0]), seqlenth)
                                line = f1.readline()
                            else:  # 序列名下面有换行的sequential
                                seqt_name = re.search(
                                    r"([^\r\n\f\v]+)(?=[\r\n])",
                                    line).group().replace(
                                    " ",
                                    "").replace(
                                    "\t",
                                    "")
                                line = f1.readline()
                                while line and (line == "\n" or line == "\r\n"):  # 跳过空行
                                    line = f1.readline()
                                seqt_seq = [line.strip().replace(
                                    " ", "").replace("\t", "")]
                                # 这里容易陷入死循环，如果差一点儿位置
                                while len("".join(seqt_seq)) != seqlenth and line:
                                    line = f1.readline()
                                    seqt_seq.append(line.strip().replace(" ",
                                                                     "").replace("\t", ""))
                                    # 避免死循环，读到的长度大于文件显示长度就报错
                                    if len("".join(seqt_seq)) > seqlenth:
                                        self.error_message += "Unexpected long sequence length in 【%s】!" % seqt_name
                                        break
                                self.dict_taxon[seqt_name] = seqt_seq
                                line = f1.readline()
                            if processSig:
                                count_proc += 1
                                processSig.emit(
                                    base + (count_proc / total) * proportion)
                            if len(self.dict_taxon.keys()) == taxnum:
                                break
            else:  # 不是phy\nex\paml
                if re.search(r"^#.+[\r\n]", self.content):  # MEGA格式
                    # 进度条相关
                    if processSig:
                        total = self.content.count("\n")
                        count_proc = 0
                    with open(self.file, encoding="utf-8", errors='ignore') as f2:
                        line = f2.readline()
                        while line:
                            while (not line.startswith('#') or re.search(
                                    r"^#mega", line, re.I)) and line:
                                line = f2.readline()
                            mega_name = line.strip().replace("#", "")
                            mega_seq = []
                            line = f2.readline()
                            while not line.startswith('#') and line:
                                mega_seq.append(line.strip().replace(" ",
                                                                 "").replace("\t", ""))
                                line = f2.readline()
                                if processSig:
                                    count_proc += 1
                                    processSig.emit(
                                        base + (count_proc / total) * proportion)
                            self.dict_taxon[mega_name] = mega_seq
                            if processSig:
                                count_proc += 1
                                processSig.emit(
                                    base + (count_proc / total) * proportion)
                elif re.search(r"^>.+[\r\n]", self.content):  # fas格式
                    # 进度条相关
                    if processSig:
                        total = self.content.count("\n")
                        count_proc = 0
                    with open(self.file, encoding="utf-8", errors='ignore') as f2:
                        line = f2.readline()
                        while line:
                            while (not line.startswith('>')) and line:
                                line = f2.readline()
                            fas_name = line.strip().replace(">", "")
                            fas_seq = []
                            line = f2.readline()
                            while not line.startswith('>') and line:
                                fas_seq.append(line.strip().replace(" ",
                                                                "").replace("\t", ""))
                                line = f2.readline()
                                if processSig:
                                    count_proc += 1
                                    processSig.emit(
                                        base + (count_proc / total) * proportion)
                            self.dict_taxon[fas_name] = fas_seq
                            if processSig:
                                count_proc += 1
                                processSig.emit(
                                    base + (count_proc / total) * proportion)
                else:  # 匹配aln格式
                    rgxaln = re.compile(
                        r"([^\r\n\t\f\v #]+)[ \t]{4,}([GAVLIFWYDHNEKQMRSTCPUBXJ\-\?]+)[\r\n]",
                        re.I)  # 与hash1一样
                    stop = 0
                    match = rgxaln.search(self.content, stop)
                    # 进度条相关
                    if processSig:
                        total = len(self.rgxinitial.findall(self.content))
                        count_proc = 0
                    while match:
                        name, sequence, stop = match.group(1), match.group(
                            2), match.span()[1] - 1  # 这里span-1是\n，span是下一行开始的名字
                        # 替换序列内部的非序列成分
                        sequence = re.sub(r"\r|\n|\t| ", "", sequence)
                        self.dict_taxon.setdefault(name, []).append(sequence)
                        # if name in self.dict_taxon:
                        #     self.dict_taxon[name] += sequence
                        # else:
                        #     self.dict_taxon[name] = sequence
                        # print(name,stop)
                        # #如果陷入死循环，开启这个方法，可以查看是哪个序列含有非法符号，把对应序列复制出来，用(?i)[^ATCG-]这个正则查找
                        if processSig:
                            count_proc += 1
                            processSig.emit(
                                base + (count_proc / total) * proportion)
                        match = rgxaln.search(self.content, stop)

        # def standard_name():
        #     self.standard_dict_taxon = OrderedDict()
        #     factory = Factory()
        #     for i in self.dict_taxon:
        #         new_name = factory.refineName(i)  # 去掉头尾空格,并替换空格
        #         self.standard_dict_taxon[new_name] = self.dict_taxon[i]
        #         self.name_mapping[i] = new_name
        # standard_name()
        self.standard_dict_taxon = OrderedDict()
        for key,value in self.dict_taxon.items():
            if clean_name:
                new_key = self.factory.refineName(key)
                self.standard_dict_taxon[new_key] = re.sub(r"\s", "", "".join(value))
                self.name_mapping[key] = new_key
            else:
                self.standard_dict_taxon[key] = re.sub(r"\s", "", "".join(value))
                self.name_mapping[key] = key
        return self.standard_dict_taxon

    # 判断pattern,以dict_taxon形式传入参数
    def which_pattern(self, dict_taxon, file):
        list_pattern = []  # 每一个taxon的序列都验证一些类型存放到列表里面 [name, AA]
        for name, seq in dict_taxon.items():
            if len(seq) != seq.count("-"):  # 过滤掉全是-的序列，不判断
                list_pattern.append([name, self.judge(seq)])
        list_seq_types = [pattern[1] for pattern in list_pattern]
        set_pattern = set(list_seq_types)  # 将其转换为集合
        # 长度不等于一就证明有taxon跟其他taxon类型不同
        if set_pattern and len(set_pattern) != 1:
            type_details = "Sequence types:\n" + "\n".join([":\t".join(i) for i in list_pattern]) + "\n"
            self.warning_message += "Warning: mixed nucleotide and AA sequences in %s!\n%s" % (file, type_details)
            pattern_counter = Counter(list_seq_types)
            most_common_pattern = pattern_counter.most_common(1)[0][0]
            return most_common_pattern
        elif not list_seq_types:
            return "N/A"
        else:
            return list_seq_types[0]


class Convertfmt(object):
    exception_signal = pyqtSignal(str)

    def __init__(self, **kwargs):
        self.dict_args = kwargs
        for i in ["export_phylip", "export_nex", "export_nexi", "export_paml", "export_axt", "export_fas", "export_stat"]:
            if i not in self.dict_args:
                self.dict_args[i] = False
        self.error_message = ""
        self.parsefmt = Parsefmt(self.error_message)
        self.factory = Factory()
        self.unaligns = []
        self.f3 = None

    def exec_(self):
        if "files" in self.dict_args:
            self.outpath = self.dict_args["export_path"]
            # 如果用户没有传文件，就是调用generate_each导入dict_taxon
            total = len(self.dict_args["files"])
            for num, file in enumerate(self.dict_args["files"]):
                dict_taxon = self.parsefmt.readfile(file)
                if ("remove B" in self.dict_args) and self.dict_args["remove B"]:
                    for taxon in dict_taxon:
                        dict_taxon[taxon] = re.sub(r"B", "-", dict_taxon[taxon], re.I)
                self.error_message += self.parsefmt.error_message
                if self.factory.is_aligned(dict_taxon):
                    self.generate_each(dict_taxon, file)
                else:
                    self.unaligns.append(os.path.basename(file))
                if "progressSig" in self.dict_args:
                    self.dict_args["progressSig"].emit(
                        ((num + 1) * 100 / total))
        # if self.error_message and "exception_signal" in self.dict_args:
        #     self.dict_args["exception_signal"].emit(self.error_message)
        # if self.unaligns:
        #     self.dict_args["unaligned_signal"].emit(self.unaligns)

    def generate_each(self, dict_taxon, file):  # 判定序列是否比对过
        self.phy = []
        self.nex = []
        self.nxs_inter = []
        self.fas = []
        self.paml = []
        self.axt_name = []
        self.axt_seq = []
        # self.raw_data = []
        self.statistics = ['Name,Length\n']
        self.count = 1
        self.dict_taxon = dict_taxon
        if self.factory.is_aligned(self.dict_taxon):  # 判断是是否比对过
            list_lenth = [len(i) for i in self.dict_taxon.keys()]
            self.longest = max(list_lenth)
            for self.name, self.seq in sorted(self.dict_taxon.items()):
                self.seq = self.seq.upper()
                self.name = self.name.ljust(self.longest)  # 统计名字长度，让序列名对齐
                self.assign()
            self.complete(file)
            if "userSave" in self.dict_args:
                self.userSave(self.dict_args["userSave"])
            else:
                self.save(file)
        else:
            self.exception_signal.emit("Unaligned!")

    def align(self):
        list_seq = re.findall(r'(.{60})', self.seq)
        remainder = len(self.seq) % 60
        if remainder == 0:
            self.align_seq = '\n'.join(list_seq) + '\n'
        else:
            self.align_seq = '\n'.join(
                list_seq) + '\n' + self.seq[-remainder:] + '\n'

    def assign(self):
        self.align()
        if self.dict_args["export_stat"]:
            self.statistics.append(f"{self.name.strip()},{len(self.seq)}\n")
        if self.dict_args["export_fas"]:
            self.fas.append(f">{self.name.strip()}\n{self.seq}\n")
        if self.dict_args["export_phylip"]:
            self.phy.append(f"{self.name} {self.seq}\n")
        if self.dict_args["export_nex"]:
            self.nex.append(f"{self.name} {self.seq}\n")
        if self.dict_args["export_paml"]:
            self.paml.append(f"{self.name.strip()}\n{self.align_seq}\n") #.replace("T", "U") + '\n'
        if self.dict_args["export_axt"]:
            self.axt_name.append(f"{self.name.strip()}")
            self.axt_seq.append(f"{self.seq}\n") #.replace("T", "U") + '\n'
        # self.raw_data.append(f"{self.seq}\n")
        self.count += 1

    def nxs_interfmt(self):
        length = len(self.dict_taxon[self.list_fmtkeys[-1]])  # 总长
        integer = length // 60
        num = 1
        while num <= integer:
            for i in self.list_fmtkeys:  # 对齐名字
                self.nxs_inter.append(f"{i.ljust(self.longest)} {self.dict_taxon[i][(num - 1) * 60:num * 60]}\n")
            self.nxs_inter.append("\n")
            num += 1
        if length % 60 != 0:
            for i in self.list_fmtkeys:
                self.nxs_inter.append(f"{i.ljust(self.longest)} {self.dict_taxon[i][(num - 1) * 60:length]}\n")
        self.nxs_inter.append(';\nEND;\n')

    def complete(self, file):
        len_seq = len(self.seq)
        seq_num = self.count - 1
        self.pattern = self.parsefmt.which_pattern(
            self.dict_taxon, file)
        self.phy = f" {seq_num} {len_seq}\n{''.join(self.phy)}"
        # self.phy = ' ' + str(seq_num) + ' ' + \
        #     str(len_seq) + '\n' + self.phy # insert
        self.nex = f"#NEXUS\nBEGIN DATA;\ndimensions ntax={seq_num} nchar={len_seq};\nformat missing=?\n" \
                   f"datatype={self.pattern} gap= -;\n\nmatrix\n{''.join(self.nex)};\nEND;\n"
        # self.nex = '#NEXUS\nBEGIN DATA;\ndimensions ntax=%s nchar=%s;\nformat missing=?\ndatatype=%s gap= -;\n\nmatrix\n'\
        #     % (str(seq_num), str(len_seq), self.pattern) + self.nex + ';\nEND;\n'
        self.nxs_inter = [f'#NEXUS\nBEGIN DATA;\ndimensions ntax={seq_num} nchar={len_seq};\nformat missing=?\n'
                          f'datatype={self.pattern} gap= - interleave;\n\nmatrix\n']
        self.paml = f"{seq_num}  {len_seq}\n\n{''.join(self.paml)}"
        self.axt = f"{'-'.join(self.axt_name)}\n{''.join(self.axt_seq)}"
        self.list_fmtkeys = sorted(list(self.dict_taxon.keys()))
        if self.dict_args["export_nexi"]:
            self.nxs_interfmt()  # 生成interleave格式的nxs

    def save(self, inputfile):
        rawname = os.path.splitext(os.path.basename(inputfile))[0]
        if self.dict_args["export_phylip"]:
            with open(self.outpath + os.sep + rawname + '.phy', 'w', encoding="utf-8") as f1:
                f1.write(self.phy)
        if self.dict_args["export_nex"]:
            self.f2 = self.outpath + os.sep + rawname + '.nex'  # 由于贝叶斯需要
            with open(self.f2, 'w', encoding="utf-8") as f2:
                f2.write(self.nex)
        if self.dict_args["export_nexi"]:
            self.f3 = self.outpath + os.sep + rawname + '_interleave.nex'
            with open(self.f3, 'w', encoding="utf-8") as f3:
                f3.write("".join(self.nxs_inter))
        if self.dict_args["export_paml"]:
            with open(self.outpath + os.sep + rawname + '.PML', 'w', encoding="utf-8") as f4:
                f4.write(self.paml)
        if self.dict_args["export_axt"]:
            self.axt_file = self.outpath + os.sep + rawname + '.axt'
            with open(self.axt_file, 'w', encoding="utf-8") as f5:
                f5.write(self.axt)
        if self.dict_args["export_fas"]:
            self.f6 = self.outpath + os.sep + rawname + '.fas'
            with open(self.f6, 'w', encoding="utf-8") as f6:
                f6.write("".join(self.fas))
        if self.dict_args["export_stat"]:
            with open(self.outpath + os.sep + rawname + '_stat.csv', 'w', encoding="utf-8") as f7:
                f7.write("".join(self.statistics))

    def userSave(self, outputName):
        if self.dict_args["export_phylip"]:
            with open(outputName, 'w', encoding="utf-8") as f1:
                f1.write(self.phy)
        if self.dict_args["export_nex"]:
            with open(outputName, 'w', encoding="utf-8") as f2:
                f2.write(self.nex)
        if self.dict_args["export_nexi"]:
            with open(outputName, 'w', encoding="utf-8") as f3:
                f3.write("".join(self.nxs_inter))
        if self.dict_args["export_paml"]:
            with open(outputName, 'w', encoding="utf-8") as f4:
                f4.write(self.paml)
        if self.dict_args["export_axt"]:
            with open(outputName, 'w', encoding="utf-8") as f5:
                f5.write(self.axt)
        if self.dict_args["export_fas"]:
            with open(outputName, 'w', encoding="utf-8") as f6:
                f6.write("".join(self.fas))
        if self.dict_args["export_stat"]:
            with open(outputName, 'w', encoding="utf-8") as f7:
                f7.write("".join(self.statistics))


class Find(QDialog):

    def __init__(self, parent=None, target=None, sig=None):

        #         QDialog.__init__(self, parent)
        super(Find, self).__init__(parent)

        self.parent = parent

        self.lastMatch = None

        self.target = target

        self.findSig = sig
        # 如果传入了要匹配的目标，就直接执行find
        if self.target:
            self.find()
        else:
            self.initUI()

    def initUI(self):

        # Button to search the document for something
        findButton = QPushButton("Find", self)
        findButton.clicked.connect(self.find)

        # Button to replace the last finding
        replaceButton = QPushButton("Replace", self)
        replaceButton.clicked.connect(self.replace)

        # Button to remove all findings
        allButton = QPushButton("Replace all", self)
        allButton.clicked.connect(self.replaceAll)

        # Normal mode - radio button
        self.normalRadio = QRadioButton("Normal", self)
        self.normalRadio.toggled.connect(self.normalMode)

        # Regular Expression Mode - radio button
        self.regexRadio = QRadioButton("RegEx", self)
        self.regexRadio.toggled.connect(self.regexMode)

        # The field into which to type the query
        self.findField = QTextEdit(self)
        self.findField.resize(250, 50)

        # The field into which to type the text to replace the
        # queried text
        self.replaceField = QTextEdit(self)
        self.replaceField.resize(250, 50)

        optionsLabel = QLabel("Options: ", self)

        # Case Sensitivity option
        self.caseSens = QCheckBox("Case sensitive", self)

        # Whole Words option
        self.wholeWords = QCheckBox("Whole words", self)

        # Layout the objects on the screen
        layout = QGridLayout(self)

        layout.addWidget(self.findField, 1, 0, 1, 4)
        layout.addWidget(self.normalRadio, 2, 2)
        layout.addWidget(self.regexRadio, 2, 3)
        layout.addWidget(findButton, 2, 0, 1, 2)

        layout.addWidget(self.replaceField, 3, 0, 1, 4)
        layout.addWidget(replaceButton, 4, 0, 1, 2)
        layout.addWidget(allButton, 4, 2, 1, 2)

        # Add some spacing
        spacer = QWidget(self)

        spacer.setFixedSize(0, 10)

        layout.addWidget(spacer, 5, 0)

        layout.addWidget(optionsLabel, 6, 0)
        layout.addWidget(self.caseSens, 6, 1)
        layout.addWidget(self.wholeWords, 6, 2)

        self.setGeometry(300, 300, 360, 250)
        self.setWindowTitle("Find and Replace")
        self.setLayout(layout)

        # By default the normal mode is activated
        self.normalRadio.setChecked(True)
        # rect = self.parent.geometry()
        # x = rect.x() + rect.width() / 2 - self.width() / 2
        # y = rect.y() + rect.height() / 2 - self.height()
        # self.move(x, y)

    def find(self):

        # Grab the parent's text
        text = self.parent.toPlainText()

        # And the text to find
        query = self.findField.toPlainText(
        ) if self.target is None else self.target

        # If the 'Whole Words' checkbox is checked, we need to append
        # and prepend a non-alphanumeric character
        if self.target is None:
            if self.wholeWords.isChecked():
                query = r'\W' + query + r'\W'

        # By default regexes are case sensitive but usually a search isn't
        # case sensitive by default, so we need to switch this around here
        if self.target is None:
            flags = 0 if self.caseSens.isChecked() else re.I
        else:
            flags = 0
            for i in "[]*.?+$^(){}|\/":
                query = query.replace(i, "[" + i + "]")

        # Compile the pattern
        pattern = re.compile(query, flags)

        # If the last match was successful, start at position after the last
        # match's start, else at 0
        start = self.lastMatch.start() + 1 if self.lastMatch else 0

        # The actual search
        self.lastMatch = pattern.search(text, start)

        if self.lastMatch:

            start = self.lastMatch.start()
            end = self.lastMatch.end()

            # If 'Whole words' is checked, the selection would include the two
            # non-alphanumeric characters we included in the search, which need
            # to be removed before marking them.
            if self.target is None:
                if self.wholeWords.isChecked():
                    start += 1
                    end -= 1

            self.moveCursor(start, end)

        else:
            if self.findSig is None:
                # We set the cursor to the end if the search was unsuccessful
                self.parent.moveCursor(QTextCursor.End)
            else:
                self.findSig.emit()

    def replace(self):

        # Grab the text cursor
        cursor = self.parent.textCursor()

        # Security
        if self.lastMatch and cursor.hasSelection():

            # We insert the new text, which will override the selected
            # text
            cursor.insertText(self.replaceField.toPlainText())

            # And set the new cursor
            self.parent.setTextCursor(cursor)

    def replaceAll(self):

        # Set lastMatch to None so that the search
        # starts from the beginning of the document
        self.lastMatch = None

        # Initial find() call so that lastMatch is
        # potentially not None anymore
        self.find()

        # Replace and find until find is None again
        while self.lastMatch:
            self.replace()
            self.find()

    def regexMode(self):

        # First uncheck the checkboxes
        self.caseSens.setChecked(False)
        self.wholeWords.setChecked(False)

        # Then disable them (gray them out)
        self.caseSens.setEnabled(False)
        self.wholeWords.setEnabled(False)

    def normalMode(self):

        # Enable checkboxes (un-gray them)
        self.caseSens.setEnabled(True)
        self.wholeWords.setEnabled(True)

    def moveCursor(self, start, end):

        # We retrieve the QTextCursor object from the parent's QTextEdit
        cursor = self.parent.textCursor()
        # 先把目标位置顶到中间，对waring效果不好
        # cursor.setPosition(start+1000)
        # self.parent.setTextCursor(cursor)

        # Then we set the position to the beginning of the last match
        cursor.setPosition(start)

        # Next we move the Cursor by over the match and pass the KeepAnchor parameter
        # which will make the cursor select the the match's text
        cursor.movePosition(
            QTextCursor.Right,
            QTextCursor.KeepAnchor,
            end - start)

        # And finally we set this new cursor as the parent's
        self.parent.setTextCursor(cursor)
