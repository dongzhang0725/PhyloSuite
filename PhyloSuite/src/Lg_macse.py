#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import glob
import re

import multiprocessing
import shutil
import signal

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from uifiles.Ui_MACSE import Ui_MACSE
from src.factory import Factory, WorkThread
import inspect
import os
import sys
import traceback
import subprocess
import platform
from multiprocessing.pool import ApplyResult


def run(dict_args, command, file, num):
    if dict_args["refine"]:
        alignment = " -align \"%s\"" % file
        if dict_args["seq_files"]:
            if (num + 1) > len(dict_args["seq_files"]):
                seq = " -seq \"%s\"" % dict_args["seq_files"][-1]  # 用最后个文件
            else:
                seq = " -seq \"%s\"" % dict_args["seq_files"][num]
        else:
            seq = ""
        if dict_args["seq_lr_files"]:
            if (num + 1) > len(dict_args["seq_lr_files"]):
                seq_lr = " -seq_lr \"%s\"" % dict_args["seq_lr_files"][-1]  # 用最后个文件
            else:
                seq_lr = " -seq_lr \"%s\"" % dict_args["seq_lr_files"][num]
        else:
            seq_lr = ""
        command = command.replace(" -seq seqFile", seq).replace(" -seq_lr seqLrFile", seq_lr).replace(" -align alignment", alignment)
    else:
        seq = " -seq \"%s\"" % file
        if dict_args["seq_lr_files"]:
            if (num + 1) > len(dict_args["seq_lr_files"]):
                seq_lr = " -seq_lr \"%s\"" % dict_args["seq_lr_files"][-1]  # 用最后个文件
            else:
                seq_lr = " -seq_lr \"%s\"" % dict_args["seq_lr_files"][num]
        else:
            seq_lr = ""
        command = command.replace(" -seq seqFile", seq).replace(" -seq_lr seqLrFile", seq_lr)
    startupINFO = None
    if platform.system().lower() == "windows":
        startupINFO = subprocess.STARTUPINFO()
        startupINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupINFO.wShowWindow = subprocess.SW_HIDE
        popen = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO)
    else:
        popen = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO, shell=True,
            preexec_fn=os.setsid)
    run.queue.put(("popen", popen.pid))
    # 存log文件
    with open(file + ".log", "a", encoding="utf-8") as log_file:
        log_file.write(command + "\n")
        run.queue.put(("log", "%sCommands%s\n%s\n%s" % ("=" * 45, "=" * 45, command, "=" * 98)))
        fileBase = os.path.basename(file)
        rgx_init_dist = re.compile(
            r"compute initial pairwise distances", re.I)  #3
        rgx_fst_align_with_tree = re.compile(
            r"compute first alignment with guide tree", re.I) # 10
        # rgx_fst_align_score = re.compile(
        #     r"first alignment score", re.I) # 25 OR 95
        rgx_start_refine = re.compile(
            r"^start refining", re.I) # 判断一下接下来就是rgx_refine_process了,# 25 OR 95
        rgx_refine_process = re.compile(r"([.+-]+)\n") # 25 + 70 * (sum-+)/sum
        rgx_end = re.compile("PROGRAM HAS FINISHED SUCCESSFULLY", re.I) # 100
        noOptim = True if "-optim 0" in command else False
        startRefine = False
        while True:
            try:
                out_line = popen.stdout.readline().decode("utf-8", errors='ignore')
            except UnicodeDecodeError:
                out_line = popen.stdout.readline().decode("gbk", errors='ignore')
            if out_line == "" and popen.poll() is not None:
                break
            if rgx_init_dist.search(out_line):
                run.queue.put(("prog", fileBase, 3))
            elif rgx_fst_align_with_tree.search(out_line):
                run.queue.put(("prog", fileBase, 10))
            # elif rgx_fst_align_score.search(out_line):
            #     if noOptim:
            #         run.queue.put(("prog", fileBase, 95))
            #     else:
            #         run.queue.put(("prog", fileBase, 25))
            elif rgx_start_refine.search(out_line):
                if noOptim:
                    run.queue.put(("prog", fileBase, 95))
                else:
                    run.queue.put(("prog", fileBase, 25))
                startRefine = True
            elif rgx_refine_process.search(out_line) and startRefine:
                text = rgx_refine_process.search(out_line).group(1)
                len_text = len(text)
                sum_plus = text.count("+")
                progress = 25 + 70 * ((len_text-sum_plus)/len_text)
                run.queue.put(("prog", fileBase, progress))
            elif rgx_end.search(out_line):
                run.queue.put(("prog", fileBase, 100))
            if re.search(r"\S+", out_line):
                # print(fileBase + "---" + out_line.strip())
                log_file.write(out_line)
                run.queue.put(("log", fileBase + " --- " + out_line.strip()))
        run.queue.put(("popen finished", popen.pid))
    return "finished"

def pool_init(queue):
    # see http://stackoverflow.com/a/3843313/852994
    run.queue = queue


class MACSE(QDialog, Ui_MACSE, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    # 用于输入文件后判断用
    ui_closeSig = pyqtSignal(str)
    # 用于flowchart自动popup combobox等操作
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    # 比对完有空文件报错
    emptySig = pyqtSignal(str)
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)

    def __init__(
            self,
            workPath=None,
            focusSig=None,
            workflow=False,
            java=None,
            macseEXE=None,
            autoMFPath=None,
            parent=None):
        super(MACSE, self).__init__(parent)
        self.parent = parent
        self.function_name = "MACSE"
        self.workflow = workflow
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.java = java
        self.macseEXE = macseEXE
        self.autoMFPath = autoMFPath
        self.setupUi(self)
        # 保存设置
        if not workflow:
            self.MACSE_settings = QSettings(
                self.thisPath + '/settings/MACSE_settings.ini', QSettings.IniFormat)
        else:
            self.MACSE_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.MACSE_settings.beginGroup("Workflow")
            self.MACSE_settings.beginGroup("temporary")
            self.MACSE_settings.beginGroup('MACSE')
        # File only, no fallback to registry or or.
        self.MACSE_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        # 判断程序的版本
        self.version = ""
        version_worker = WorkThread(
            lambda : self.factory.get_version("MACSE", self),
            parent=self)
        version_worker.start()
        #
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.logGuiSig.connect(self.addText2Log)
        self.comboBox_4.installEventFilter(self)
        self.comboBox_4.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        self.comboBox_5.installEventFilter(self)
        self.comboBox_7.installEventFilter(self)
        self.log_gui = self.gui4Log()
        # self.pushButton_2.clicked.connect(print)
        self.doubleSpinBox_5.valueChanged.connect(self.judgeStopCost)
        self.doubleSpinBox.valueChanged.connect(self.judgeStopCost)
        self.doubleSpinBox_2.valueChanged.connect(self.judgeStoplrCost)
        self.doubleSpinBox_6.valueChanged.connect(self.judgeStoplrCost)
        self.comboBox_5.itemRemovedSig.connect(self.judgeCombobox5)
        self.checkBox_2.toggled.connect(self.controlRefineText)
        self.emptySig.connect(self.popup_MACSE_exception)
        self.interrupt = False
        # 给开始按钮添加菜单
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        action = QAction(QIcon(":/picture/resourses/terminal-512.png"), "View | Edit command", menu,
                         triggered=self.showCMD)
        self.work_action = QAction(QIcon(":/picture/resourses/work.png"), "", menu)
        self.work_action.triggered.connect(lambda: self.factory.swithWorkPath(self.work_action, parent=self))
        self.dir_action = QAction(QIcon(":/picture/resourses/folder.png"), "Output Dir: ", menu)
        self.dir_action.triggered.connect(lambda: self.factory.set_direct_dir(self.dir_action, self))
        menu.addAction(action)
        menu.addAction(self.work_action)
        menu.addAction(self.dir_action)
        self.pushButton.toolButton.setMenu(menu)
        self.pushButton.toolButton.menu().installEventFilter(self)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-3-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-3-1-Brief-example"
        self.label_7.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        """
        self.command = self.fetchCommands()
        if self.command:
            self.interrupt = False
            self.list_pids = []
            self.queue = multiprocessing.Queue()
            thread = int(self.comboBox_6.currentText())
            if self.dict_args["refine"]:
                thread = thread if len(self.dict_args["alignment"]) > thread else len(self.dict_args["alignment"])
            else:
                thread = thread if len(self.dict_args["seq_files"]) > thread else len(self.dict_args["seq_files"])
            self.pool = multiprocessing.get_context("spawn").Pool(processes=thread,
                                             initializer=pool_init, initargs=(self.queue,)) # \
                # if platform.system().lower() == "windows" else multiprocessing.Pool(processes=thread,
                #                                                 initializer=pool_init, initargs=(self.queue,))
            # Check for progress periodically
            self.timer = QTimer()
            self.timer.timeout.connect(self.updateProcess)
            self.timer.start(1)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        sequence file
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input sequence file",
            filter="Fasta Format(*.fas *.fasta *.fa *.fna);;")
        if fileNames[0]:
            self.input(self.comboBox_4, fileNames[0])

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        """
        less reliable sequence file
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input sequence file",
            filter="Fasta Format(*.fas *.fasta *.fa *.fna);;")
        if fileNames[0]:
            self.input(self.comboBox_5, fileNames[0])

    @pyqtSlot()
    def on_pushButton_22_clicked(self):
        """
        alignment
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input alignment",
            filter="Fasta Format(*.fas *.fasta *.fa *.fna);;")
        if fileNames[0]:
            self.input(self.comboBox_7, fileNames[0])

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        show log
        """
        self.log_gui.show()

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        Stop
        """
        if self.isRunning():
            if not self.workflow:
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "<p style='line-height:25px; height:25px'>MACSE is still running, terminate it?</p>",
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
            else:
                reply = QMessageBox.Yes
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    self.pool.terminate()  # Terminate all processes in the Pool
                    ## 删除subprocess
                    if platform.system().lower() == "windows":
                        for pid in self.list_pids: os.popen('taskkill /F /T /PID %s' % pid)
                    else:
                        for pid in self.list_pids: os.killpg(os.getpgid(pid), signal.SIGTERM)
                    self.pool = None
                    self.interrupt = True
                except:
                    self.pool = None
                    self.interrupt = True
                if not self.workflow:
                    QMessageBox.information(
                        self,
                        "MACSE",
                        "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        [self.progressBar],
                        "except",
                        self.dict_args["exportPath"],
                        self.qss_file,
                        self])

    def run_command(self):
        try:
            # 清空文件夹，放在这里方便统一报错
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "start",
                    self.dict_args["exportPath"],
                    self.qss_file,
                    self])
            ##进度条用
            if self.dict_args["refine"]:
                self.dict_file_progress = {os.path.basename(file): 0 for file in self.dict_args["alignment"]}
                async_results = [self.pool.apply_async(run, args=(self.dict_args, self.command, file, num)) for
                                 num, file in enumerate(self.dict_args["alignment"])]
            else:
                self.dict_file_progress = {os.path.basename(file): 0 for file in self.dict_args["seq_files"]}
                async_results = [self.pool.apply_async(run, args=(self.dict_args, self.command, file, num)) for
                                 num, file in enumerate(self.dict_args["seq_files"])]
            self.pool.close()  # 关闭进程池，防止进一步操作。如果所有操作持续挂起，它们将在工作进程终止前完成
            map(ApplyResult.wait, async_results)
            lst_results = [r.get() for r in async_results]
            # 判断比对是否成功
            macse_NT_results = glob.glob(self.dict_args["exportPath"] + os.sep + "*_NT.*")
            empty_files = [os.path.basename(file) for file in macse_NT_results if os.stat(file).st_size == 0]
            has_error = False
            refine_nopt = True if (self.checkBox_2.isChecked() and self.comboBox_2.currentText() == "NONE") else False #fefine模式，并且不optimization
            if not macse_NT_results or empty_files:
                log = self.textEdit_log.toPlainText()
                list_commands = re.findall(r"Command: (.+)\n", log)
                last_cmd = list_commands[-1] if list_commands else ""
                if ("StringIndexOutOfBoundsException" in log) and ("-prog refineAlignment" in log):
                    has_error = True
                    self.emptySig.emit(
                        "MACSE executes failed, click <span style=\"color:red\">Show log</span> to see details! "
                        "<br>As you selected \"Refine\", please ensure that your input files are aligned. "
                        "<br>You can also copy this command to terminal to debug: %s" % last_cmd)
                elif not refine_nopt:
                    has_error = True
                    # if self.checkBox_2.isChecked():
                    #     self.emptySig.emit("MACSE executes failed, click <span style=\"color:red\">Show log</span> to see details! "
                    #                        "<br>As you selected \"Refine\", please ensure that your input files are aligned. "
                    #                        "<br>You can also copy this command to terminal to debug: %s" % last_cmd)
                    # else:
                    self.emptySig.emit(
                        "MACSE execute failed, click <span style=\"color:red\">Show log</span> to see details! "
                        "<br>You can also copy this command to terminal to debug: %s"%last_cmd)
            if not has_error:
                # 替换感叹号和星号，以便下游程序调用
                macse_AA_results = glob.glob(self.dict_args["exportPath"] + os.sep + "*_AA.*")
                self.replaceSymbols(macse_NT_results + macse_AA_results)
            ##预防optimization为0的时候
            self.progressSig.emit(100)
            self.workflow_progress.emit(100)
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (
            str(time_start), str(time_end),
            self.time_used)
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(
                    self.description + "\n\nIf you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n"
                                       "If you use MACSE, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
            if (not self.interrupt) and (not has_error):
                self.pool = None
                self.interrupt = False
                if self.workflow:
                    # work flow跑的
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton,
                            self.progressBar,
                            "workflow stop",
                            self.exportPath,
                            self.qss_file,
                            self])
                    self.workflow_finished.emit("finished")
                    return
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        "stop",
                        self.exportPath,
                        self.qss_file,
                        self])
                self.focusSig.emit(self.exportPath)
            else:
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])
                self.pool = None
                self.interrupt = False
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "except",
                    self.dict_args["exportPath"],
                    self.qss_file,
                    self])
            self.pool = None
            self.interrupt = False

    def guiSave(self):
        # Save geometry
        self.MACSE_settings.setValue('size', self.size())
        # self.MACSE_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.MACSE_settings.setValue(name, index)
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.MACSE_settings.setValue(name, state)
            elif isinstance(obj, QSpinBox):
                value = obj.value()
                self.MACSE_settings.setValue(name, value)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.MACSE_settings.setValue(name, float_)
            elif isinstance(obj, QLineEdit):
                value = obj.text()
                self.MACSE_settings.setValue(name, value)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.factory.judgeWindowSize(self.MACSE_settings, 826, 590))
        if platform.system().lower() != "linux":
            self.factory.centerWindow(self)
        # self.move(self.MACSE_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox_6":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.MACSE_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(list_cpu):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
                elif name == "comboBox_4":
                    if self.autoMFPath and (not "_mafft." in self.autoMFPath[0]):
                        self.input(self.comboBox_4, self.autoMFPath)
                        self.input(self.comboBox_7, [])
                    else: self.input(self.comboBox_4, [])
                elif name == "comboBox_5":
                    self.input(self.comboBox_5, None)
                elif name == "comboBox_7":
                    if self.autoMFPath and ("_mafft." in self.autoMFPath[0]):
                        ## MAFFT的结果导入
                        self.checkBox_2.setChecked(True)
                        self.input(self.comboBox_7, self.autoMFPath)
                        self.input(self.comboBox_4, [])
                    else: self.input(self.comboBox_7, [])
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.MACSE_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(allItems):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
            if isinstance(obj, QCheckBox):
                value = self.MACSE_settings.value(
                    name, "no setting")  # get stored value from registry
                if value != "no setting":
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QSpinBox):
                ini_value = obj.value()
                value = self.MACSE_settings.value(name, ini_value)
                obj.setValue(int(value))
            elif isinstance(obj, QDoubleSpinBox):
                ini_float_ = obj.value()
                float_ = self.MACSE_settings.value(name, ini_float_)
                obj.setValue(float(float_))
            elif isinstance(obj, QLineEdit):
                value = self.MACSE_settings.value(
                    name, "")  # get stored value from registry
                if value:
                    obj.setText(value)  # restore checkbox

    def runProgress(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def popupException(self, exception):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        self.guiSave()
        self.log_gui.close()  # 关闭子窗口
        self.closeSig.emit("MACSE", self.fetchWorkflowSetting())
        # 断开showSig和closeSig的槽函数连接
        try: self.showSig.disconnect()
        except: pass
        try: self.closeSig.disconnect()
        except: pass
        if self.workflow:
            self.ui_closeSig.emit("MACSE")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            reply = QMessageBox.question(
                self,
                "MACSE",
                "<p style='line-height:25px; height:25px'>MACSE is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    self.pool.terminate()  # Terminate all processes in the Pool
                    ## 删除subprocess
                    if platform.system().lower() == "windows":
                        for pid in self.list_pids: os.popen('taskkill /F /T /PID %s' % pid)
                    else:
                        for pid in self.list_pids: os.killpg(os.getpgid(pid), signal.SIGTERM)
                    self.pool = None
                    self.interrupt = True
                except:
                    self.pool = None
                    self.interrupt = True
            else:
                event.ignore()

    def showEvent(self, event):
        QTimer.singleShot(100, lambda: self.showSig.emit(self))

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        if isinstance(
                obj,
                QComboBox):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                self.input(obj, files)
        if (event.type() == QEvent.Show) and (obj == self.pushButton.toolButton.menu()):
            if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+",
                         self.dir_action.text()) or self.dir_action.text() == "Output Dir: ":
                self.factory.sync_dir(self.dir_action)  ##同步文件夹名字
            menu_x_pos = self.pushButton.toolButton.menu().pos().x()
            menu_width = self.pushButton.toolButton.menu().size().width()
            button_width = self.pushButton.toolButton.size().width()
            pos = QPoint(menu_x_pos - menu_width + button_width,
                         self.pushButton.toolButton.menu().pos().y())
            self.pushButton.toolButton.menu().move(pos)
            return True
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(MACSE, self).eventFilter(obj, event)  # 0

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of MACSE:")
        horizontalLayout_2.addWidget(label)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        horizontalLayout_2.addItem(spacerItem)
        toolButton = QToolButton(dialog)
        icon2 = QIcon()
        icon2.addPixmap(QPixmap(":/picture/resourses/interface-controls-text-wrap-512.png"))
        toolButton.setIcon(icon2)
        toolButton.setCheckable(True)
        toolButton.setToolTip("Use Wraps")
        toolButton.clicked.connect(self.setWordWrap)
        toolButton.setChecked(True)
        horizontalLayout_2.addWidget(toolButton)
        pushButton = QPushButton("Save to file", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/Save-icon.png"))
        pushButton.setIcon(icon)
        pushButton_2 = QPushButton("Close", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/if_Delete_1493279.png"))
        pushButton_2.setIcon(icon)
        self.textEdit_log = QTextEdit(dialog)
        self.textEdit_log.setReadOnly(True)
        gridLayout.addLayout(horizontalLayout_2, 0, 0, 1, 2)
        gridLayout.addWidget(self.textEdit_log, 1, 0, 1, 2)
        gridLayout.addWidget(pushButton, 2, 0, 1, 1)
        gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
        pushButton.clicked.connect(self.save_log_to_file)
        pushButton_2.clicked.connect(dialog.close)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def addText2Log(self, text):
        if re.search(r"\w+", text):
            self.textEdit_log.append(text)
            with open(self.exportPath + os.sep + "PhyloSuite_MACSE.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "MACSE", "log", "text Format(*.txt)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    def setWordWrap(self):
        button = self.sender()
        if button.isChecked():
            button.setChecked(True)
            self.textEdit_log.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            button.setChecked(False)
            self.textEdit_log.setLineWrapMode(QTextEdit.NoWrap)

    def input(self, combobox, list_items=None):
        if list_items:
            combobox.refreshInputs(list_items)
        else:
            combobox.refreshInputs([])
            if combobox == self.comboBox_5:
                self.comboBox_5.lineEdit().setText("Optional!")
            elif combobox == self.comboBox_7:
                self.comboBox_7.lineEdit().setText("No input MSA (Improves previously computed alignments)")

    def judgeStopCost(self, value):
        stop_value = self.doubleSpinBox_5.value()
        fs_value = self.doubleSpinBox.value()
        if stop_value >= (2 * fs_value):
            QMessageBox.information(
                self,
                "MACSE",
                "<p style='line-height:25px; height:25px'>The value of \"stop\" should be less than twice the value of \"fs\".</p>")
            self.doubleSpinBox.setValue(30.0)
            self.doubleSpinBox_5.setValue(50.0)

    def judgeStoplrCost(self, value):
        stop_value = self.doubleSpinBox_6.value()
        fs_value = self.doubleSpinBox_2.value()
        if stop_value >= (2 * fs_value):
            QMessageBox.information(
                self,
                "MACSE",
                "<p style='line-height:25px; height:25px'>The value of \"stop_lr\" should be less than twice the value of \"fs_lr\".</p>")
            self.doubleSpinBox_2.setValue(10.0)
            self.doubleSpinBox_6.setValue(17.0)

    def fetchCommands(self):
        if self.isFileIn():
            self.interrupt = False
            self.dict_args = {}
            self.dict_args["allowNT"] = " -allow_NT \"%s\"" % self.lineEdit.text() if self.lineEdit.text() else ""
            self.dict_args["alphabetAA"] = " -alphabet_AA %s" % self.comboBox.currentText()
            self.dict_args["ambiOFF"] = " -ambi_OFF true" if self.checkBox.isChecked() else ""
            self.dict_args["fs"] = " -fs %.1f" % self.doubleSpinBox.value() if self.doubleSpinBox.value() != 30.0 else ""
            self.dict_args[
                "fs_lr"] = " -fs_lr %.1f" % self.doubleSpinBox_2.value() if self.doubleSpinBox_2.value() != 10.0 else ""
            self.dict_args[
                "fs_lr_term"] = " -fs_lr_term %.1f" % self.doubleSpinBox_3.value() if self.doubleSpinBox_3.value() != 7.0 else ""
            self.dict_args[
                "fs_term"] = " -fs_term %.1f" % self.doubleSpinBox_4.value() if self.doubleSpinBox_4.value() != 10.0 else ""
            self.dict_args[
                "gap_ext"] = " -gap_ext %.1f" % self.doubleSpinBox_7.value() if self.doubleSpinBox_7.value() != 1.0 else ""
            self.dict_args[
                "gap_ext_term"] = " -gap_ext_term %.1f" % self.doubleSpinBox_9.value() if self.doubleSpinBox_9.value() != 0.9 else ""
            self.dict_args[
                "gap_op"] = " -gap_op %.1f" % self.doubleSpinBox_8.value() if self.doubleSpinBox_8.value() != 7.0 else ""
            self.dict_args[
                "gap_op_term"] = " -gap_op_term %.1f" % self.doubleSpinBox_10.value() if self.doubleSpinBox_10.value() != 6.3 else ""
            self.dict_args[
                "local_realign_dec"] = " -local_realign_dec %.1f" % self.doubleSpinBox_11.value() if self.doubleSpinBox_11.value() != 0.5 else ""
            self.dict_args[
                "local_realign_init"] = " -local_realign_init %.1f" % self.doubleSpinBox_12.value() if self.doubleSpinBox_12.value() != 0.5 else ""
            self.dict_args[
                "max_refine_iter"] = " -max_refine_iter %d" % self.spinBox.value() if self.spinBox.value() != -1 else ""
            self.dict_args["gc_def"] = " -gc_def %s" % str(
                self.comboBox_9.currentText()).split(" ")[0]
            if self.comboBox_2.currentText() == "NONE":
                self.dict_args["optim"] = " -optim 0"
            elif self.comboBox_2.currentText() == "BASIC":
                self.dict_args["optim"] = " -optim 1"
            else:
                self.dict_args["optim"] = ""
            self.dict_args["score_matrix"] = " -score_matrix %s" % str(
                self.comboBox_3.currentText())
            self.dict_args[
                "stop"] = " -stop %.1f" % self.doubleSpinBox_5.value() if self.doubleSpinBox_5.value() != 50.0 else ""
            self.dict_args[
                "stop_lr"] = " -stop_lr %.1f" % self.doubleSpinBox_6.value() if self.doubleSpinBox_6.value() != 17.0 else ""
            self.dict_args["java"] = self.java
            self.dict_args["macseEXE"] = self.macseEXE
            self.dict_args["refine"] = self.checkBox_2.isChecked()
            self.dict_args["prog"] = "alignSequences" if not self.dict_args["refine"] else "refineAlignment"
            self.dict_args["algn_cmd"] = " -align alignment" if self.dict_args["refine"] else ""
            self.reference = "Ranwez V, Douzery EJP, Cambon C, Chantret N, Delsuc F. 2018. MACSE v2: Toolkit for the " \
                             "Alignment of Coding Sequences Accounting for Frameshifts and Stop Codons. Mol Biol Evol. " \
                             "35: 2582-2584. doi: 10.1093/molbev/msy159."
            prefix = "The sequences were aligned" if not self.dict_args["refine"] else "The alignments were refined"
            self.description = "%s using the codon-aware program MACSE v%s (Ranwez et al., 2018), " \
                               "which preserves reading frame and allows incorporation of sequencing errors or " \
                               "sequences with frameshifts."%(prefix, self.version)
            # self.dict_args["exception_signal"] = self.exception_signal
            # self.dict_args["progressSig"] = self.progressSig
            self.dict_args["workPath"] = self.workPath
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath + \
                                                     os.sep + "MACSE_results" + os.sep + self.output_dir_name)
            self.dict_args["exportPath"] = self.exportPath
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                # 提醒是否删除旧结果，如果用户取消，就不执行
                return
            ##拷贝输入文件进去
            self.dict_args["seq_files"] = []
            self.dict_args["seq_lr_files"] = []
            self.dict_args["alignment"] = []
            try:
                for seq_file in self.comboBox_4.fetchListsText():
                    self.dict_args["seq_files"].append(shutil.copy(seq_file, self.exportPath))
                for seq_lr_file in self.comboBox_5.fetchListsText():
                    self.dict_args["seq_lr_files"].append(shutil.copy(seq_lr_file, self.exportPath))
                for alin in self.comboBox_7.fetchListsText():
                    self.dict_args["alignment"].append(shutil.copy(alin, self.exportPath))
            except:
                QMessageBox.information(
                    self,
                    "MACSE",
                    "<p style='line-height:25px; height:25px'>File copying failed, please check your input files!</p>")
                return
            command = "\"{java}\" -jar \"{macseEXE}\" -prog {prog}{allowNT}{alphabetAA}{ambiOFF}{fs}{fs_lr}" \
                            "{fs_lr_term}{fs_term}{gap_ext}{gap_ext_term}{gap_op}{gap_op_term}{local_realign_dec}" \
                            "{local_realign_init}{max_refine_iter}{gc_def}{optim}{score_matrix}{stop}{stop_lr}" \
                            "{algn_cmd} -seq seqFile -seq_lr seqLrFile".format(**self.dict_args)
            self.textEdit_log.clear()  # 清空
            return command
        else:
            if self.checkBox_2.isChecked():
                QMessageBox.critical(
                    self,
                    "MACSE",
                    "<p style='line-height:25px; height:25px'>Please input files to \"Refine\" box first!</p>")
            else:
                QMessageBox.critical(
                    self,
                    "MACSE",
                    "<p style='line-height:25px; height:25px'>Please input files to \"Seq.\" box first!</p>")

    @pyqtSlot(str, result=bool)
    def fetchPopen(self, command):
        self.MS_popen = self.factory.init_popen(command)
        return True

    def showCMD(self):
        """
        show command
        """
        self.command = self.fetchCommands()
        if self.command:
            dialog = QDialog(self)
            dialog.resize(600, 200)
            dialog.setWindowTitle("Command")
            gridLayout = QGridLayout(dialog)
            label = QLabel(dialog)
            label.setText("Current Command:")
            pushButton = QPushButton("Save and run", dialog)
            icon = QIcon()
            icon.addPixmap(QPixmap(":/picture/resourses/Save-icon.png"))
            pushButton.setIcon(icon)
            pushButton_2 = QPushButton("Close", dialog)
            icon = QIcon()
            icon.addPixmap(
                QPixmap(":/picture/resourses/if_Delete_1493279.png"))
            pushButton_2.setIcon(icon)
            self.textEdit_cmd = QTextEdit(dialog)
            self.textEdit_cmd.setText(self.command)
            self.textEdit_cmd.textChanged.connect(self.judgeCmdText)
            gridLayout.addWidget(label, 0, 0, 1, 2)
            gridLayout.addWidget(self.textEdit_cmd, 1, 0, 1, 2)
            gridLayout.addWidget(pushButton, 2, 0, 1, 1)
            gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
            pushButton.clicked.connect(
                lambda: [self.run_with_CMD(self.textEdit_cmd.toPlainText()), dialog.close()])
            pushButton_2.clicked.connect(dialog.close)
            dialog.setWindowFlags(
                dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
            dialog.exec_()

    def judgeCombobox5(self):
        if not self.comboBox_5.fetchListsText(): self.comboBox_5.lineEdit().setText("Optional!")

    def run_with_CMD(self, cmd):
        self.command = cmd
        if self.command:
            self.interrupt = False
            self.list_pids = []
            self.queue = multiprocessing.Queue()
            thread = int(self.comboBox_6.currentText())
            thread = thread if len(self.dict_args["seq_files"]) > thread else len(self.dict_args["seq_files"])
            self.pool = multiprocessing.get_context("spawn").Pool(processes=thread,
                                             initializer=pool_init, initargs=(self.queue,)) # \
                # if platform.system().lower() == "windows" else multiprocessing.Pool(processes=thread,
                #                                                 initializer=pool_init, initargs=(self.queue,))
            # Check for progress periodically
            self.timer = QTimer()
            self.timer.timeout.connect(self.updateProcess)
            self.timer.start(1)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

    def judgeCmdText(self):
        text = self.textEdit_cmd.toPlainText()
        judge_text = "%s -seq seqFile -seq_lr seqLrFile"%self.dict_args["algn_cmd"]
        if judge_text not in text:
            QMessageBox.information(
                self,
                "MACSE",
                "<p style='line-height:25px; height:25px'>\"%s\" cannot be changed!</p>"%judge_text)
            self.textEdit_cmd.undo()

    def updateProcess(self):
        if self.queue.empty(): return
        info = self.queue.get()
        if info[0] == "log":
            message = info[1]
            self.logGuiSig.emit(message)
        elif info[0] == "prog":
            flag, file, progress = info
            self.dict_file_progress[file] = progress
            total_progress = 0.95*(sum(self.dict_file_progress.values())/len(self.dict_file_progress))
            self.workflow_progress.emit(total_progress)
            self.progressSig.emit(total_progress)
        elif info[0] == "popen":
            self.list_pids.append(info[1])
        elif info[0] == "popen finished":
            if info[1] in self.list_pids:
                self.list_pids.remove(info[1])

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "pool") and self.pool and not self.interrupt

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("MACSE", self.workPath, self.auto_popSig, self)

    def popupAutoDecSub(self, popupUI):
        if not popupUI:
            if not self.init:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "<p style='line-height:25px; height:25px'>No available file detected!</p>")
            return
        if not self.init: popupUI.checkBox.setVisible(False)
        if popupUI.exec_() == QDialog.Accepted:
            widget = popupUI.listWidget_framless.itemWidget(
                popupUI.listWidget_framless.selectedItems()[0])
            autoInputs = widget.autoInputs
            self.input(self.comboBox_4, autoInputs)

    def fetchWorkflowSetting(self):
        '''* Alignment Mode
          * Code table(if codon mode)
          * strategy
          * export format'''
        settings = '''<p class="title">***MACSE (Aligns nucleotide coding sequences)***</p>''' if not \
            self.checkBox_2.isChecked() else '''<p class="title">***MACSE (Improves a previously computed alignment)***</p>'''
        code_table = self.comboBox_9.currentText()
        settings += '<p>Code table: <a href="self.MACSE_exe comboBox_9.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_9)">%s</a></p>' % code_table
        Alphabet_AA = self.comboBox.currentText()
        settings += '<p>Alphabet_AA: <a href="self.MACSE_exe comboBox.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox)">%s</a></p>' % Alphabet_AA
        fs = self.doubleSpinBox.value()
        settings += '<p>fs: <a href="self.MACSE_exe doubleSpinBox.setFocus() doubleSpinBox.selectAll()' \
                    ' factory.highlightWidgets(x.doubleSpinBox)">%s</a></p>' % fs
        stop = self.doubleSpinBox_5.value()
        settings += '<p>stop: <a href="self.MACSE_exe doubleSpinBox_5.setFocus() doubleSpinBox_5.selectAll()' \
                    ' factory.highlightWidgets(x.doubleSpinBox_5)">%s</a></p>' % stop
        local_realign_dec = self.doubleSpinBox_11.value()
        settings += '<p>local_realign_dec: <a href="self.MACSE_exe doubleSpinBox_11.setFocus() doubleSpinBox_11.selectAll()' \
                    ' factory.highlightWidgets(x.doubleSpinBox_11)">%s</a></p>' % local_realign_dec
        local_realign_init = self.doubleSpinBox_12.value()
        settings += '<p>local_realign_init: <a href="self.MACSE_exe doubleSpinBox_12.setFocus() doubleSpinBox_12.selectAll()' \
                    ' factory.highlightWidgets(x.doubleSpinBox_12)">%s</a></p>' % local_realign_init
        max_refine_iter = self.spinBox.value()
        settings += '<p>max_refine_iter: <a href="self.MACSE_exe spinBox.setFocus() spinBox.selectAll()' \
                    ' factory.highlightWidgets(x.spinBox)">%s</a></p>' % max_refine_iter
        optimization = self.comboBox_2.currentText()
        settings += '<p>Optimization: <a href="self.MACSE_exe comboBox_2.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_2)">%s</a></p>' % optimization
        score_matrix = self.comboBox_3.currentText()
        settings += '<p>Score matrix: <a href="self.MACSE_exe comboBox_3.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_3)">%s</a></p>' % score_matrix
        thread = self.comboBox_6.currentText()
        settings += '<p>Thread: <a href="self.MACSE_exe comboBox_6.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_6)">%s</a></p>' % thread
        return settings

    def isFileIn(self):
        if self.checkBox_2.isChecked():
            return self.comboBox_7.count()
        else:
            return self.comboBox_4.count()

    def controlRefineText(self, bool_):
        if bool_:
            if not self.comboBox_7.count():
                self.comboBox_7.lineEdit().switchColor("No input MSA (Improves previously computed alignments)")
            else:
                self.comboBox_7.lineEdit().switchColor()
        else:
            self.comboBox_7.lineEdit().switchColor()

    def popup_MACSE_exception(self, text):
        QMessageBox.critical(
            self,
            "MACSE",
            "<p style='line-height:25px; height:25px'>%s</p>" % text)
        if "Show log" in text:
            self.on_pushButton_9_clicked()

    def replaceSymbols(self, list_results):
        '''
        替换结果里面的！和*
        :return:
        '''
        for num, file in enumerate(list_results):
            with open(file, encoding="utf-8", errors="ignore") as f:
                content = f.read()
            name, ext = os.path.splitext(file)
            with open("%s_removed_chars%s"%(name, ext), "w", encoding="utf-8") as f1:
                f1.write(content.replace("!", "?").replace("*", "?"))
            self.progressSig.emit(95 + (5 * (num + 1)/len(list_results)))
            self.workflow_progress.emit(95 + (5 * (num + 1)/len(list_results)))


if __name__ == "__main__":
    import cgitb
    sys.excepthook = cgitb.Hook(1, None, 5, sys.stderr, 'text')
    app = QApplication(sys.argv)
    ui = MACSE()
    ui.show()
    sys.exit(app.exec_())