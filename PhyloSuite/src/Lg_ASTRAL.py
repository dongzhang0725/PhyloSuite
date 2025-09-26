#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 自己调整好一个size，然后再guirestore恢复一下
import datetime
import glob
import re

import multiprocessing
import shutil
import signal

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from uifiles.Ui_ASTRAL import Ui_ASTRAL
from uifiles.Ui_HmmCleaner import Ui_HmmCleaner
from src.factory import Factory, WorkThread, Parsefmt
import inspect
import os
import sys
import traceback
import subprocess
import platform
from multiprocessing.pool import ApplyResult
from src.CustomWidget2 import MyMappingTableModel


def run(dict_args, command, file):
    fileBase = os.path.basename(file)
    inputFile = " \"%s\"" % file
    command = command.replace(" $alignment$", inputFile) #html输出替换名字
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
        run.queue.put(("log", "%sCommands%s\n%s\n%s" % ("=" * 45, "=" * 45, command, "=" * 98)))
        is_error = False
        while True:
            try:
                out_line = popen.stdout.readline().decode("utf-8", errors='ignore')
            except UnicodeDecodeError:
                out_line = popen.stdout.readline().decode("gbk", errors='ignore')
            if out_line == "" and popen.poll() is not None:
                break
            if re.search(r"\S+", out_line):
                log_file.write(out_line)
                run.queue.put(("log", fileBase + " --- " + out_line.strip()))
            if re.search(r"ERROR", out_line):
                run.queue.put(("log", fileBase + " --- " + out_line.strip()))
                error_text = ""
                is_error = True
            elif re.search(r"BAD CPU TYPE", out_line, re.IGNORECASE):
                is_error = True
                error_text = "ASTER is incompatible with your current CPU type. To proceed, please follow the manual " \
                             "configuration guide available at https://github.com/chaoszhang/ASTER"
                break
        if is_error:
            run.queue.put(("error", error_text))
        else:
            pass
        run.queue.put(("prog", "finished"))
        run.queue.put(("log", fileBase + " --- " + "Done!"))
        run.queue.put(("popen finished", popen.pid))
    return "finished"

def pool_init(queue):
    # see http://stackoverflow.com/a/3843313/852994
    run.queue = queue

class ASTRAL(QDialog, Ui_ASTRAL, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    ASTRAL_exception = pyqtSignal(str)
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    # 用于输入文件后判断用
    ui_closeSig = pyqtSignal(str)
    # 用于flowchart自动popup combobox等操作
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)
    unfinishedSig = pyqtSignal()

    def __init__(
            self,
            autoInputs=None,
            workPath=None,
            ASTRALPath=None,
            focusSig=None,
            workflow=None,
            parent=None):
        super(ASTRAL, self).__init__(parent)
        self.parent = parent
        self.function_name = "ASTRAL/CASTER/WASTER"
        self.workflow = workflow
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.autoInputs = autoInputs
        self.ASTRALPath = ASTRALPath
        self.setupUi(self)
        # 屏蔽进度条
        self.progressBar.setVisible(False)
        # 保存设置
        if not workflow:
            self.ASTRAL_settings = QSettings(
                self.thisPath + '/settings/ASTRAL_settings.ini', QSettings.IniFormat)
        else:
            self.ASTRAL_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.ASTRAL_settings.beginGroup("Workflow")
            self.ASTRAL_settings.beginGroup("temporary")
            self.ASTRAL_settings.beginGroup('ASTRAL')
        # File only, no fallback to registry or or.
        self.ASTRAL_settings.setFallbacksEnabled(False)
        # print(self.ASTRAL_settings.childGroups())
        # self.factory.settingsGroup2Group(self.ASTRAL_settings, "PCGs", "temporary")
        # 开始装载样式表
        # with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
        #     self.qss_file = f.read()
        # self.setStyleSheet(self.qss_file)
        self.qss_file = self.factory.set_qss(self)
        # 判断程序的版本
        self.version = ""
        version_worker = WorkThread(
            lambda : self.factory.get_version("ASTRAL/CASTER/WASTER", self),
            parent=self)
        version_worker.start()
        #
        self.interrupt = False
        self.comboBox_20.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        # self.comboBox_20.refreshInputs([])
        self.comboBox_18.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        # self.comboBox_18.refreshInputs([])
        self.comboBox_19.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        # self.comboBox_19.refreshInputs([])
        self.comboBox_20.itemsChanged.connect(self.update_mapping_array)
        self.comboBox_18.itemsChanged.connect(self.update_mapping_array)
        self.comboBox_19.itemsChanged.connect(self.update_mapping_array)
        self.comboBox_20.installEventFilter(self)
        self.comboBox_18.installEventFilter(self)
        self.comboBox_19.installEventFilter(self)
        self.lineEdit_2.installEventFilter(self)
        self.lineEdit_3.installEventFilter(self)
        # self.lineEdit_4.installEventFilter(self)
        # self.lineEdit_5.autoDetectSig.connect(self.popupAutoDec)
        self.radioButton_2.toggled['bool'].connect(self.treesInputProgram)
        self.radioButton.toggled['bool'].connect(self.msaInputProgram)
        self.radioButton_3.toggled['bool'].connect(self.fastaqInputProgram)
        # 恢复用户的设置
        self.guiRestore()
        self.log_gui = self.gui4Log()
        ## 信号槽
        # self.lineEdit_5.deleteFile.clicked.connect(
        #     self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        self.lineEdit_2.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        self.lineEdit_3.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        # self.lineEdit_4.deleteFile.clicked.connect(
        #     self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.logGuiSig.connect(self.addText2Log)
        self.ASTRAL_exception.connect(self.popup_ASTRAL_exception)
        self.unfinishedSig.connect(self.popup_unfinished_exception)
        self.comboBox_9.currentTextChanged.connect(self.switch_widgets)
        self.switch_widgets(self.comboBox_9.currentText())
        self.comboBox_12.currentTextChanged.connect(self.switch_support)
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
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-5-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-5-1-Brief-example"
        self.label_2.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
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
            self.error_has_shown = False  # 保证只报一次错
            self.ASTRAL_popen = self.factory.init_popen(self.command)
            self.factory.emitCommands(self.logGuiSig, f"cd \"{os.path.normpath(self.exportPath)}\"\n{self.command}")
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
            self.on_pushButton_9_clicked()

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        show log
        """
        self.log_gui.show()

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        gene trees
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input gene tree file(s)")
        if fileNames[0]:
            self.input(files=fileNames[0], combobox=self.comboBox_20)

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        """
        alignments
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input alignment file(s)")
        if fileNames[0]:
            self.input(files=fileNames[0], combobox=self.comboBox_19)

    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        """
        fasta/fastq
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input fasta/fastq file(s)")
        if fileNames[0]:
            self.input(files=fileNames[0], combobox=self.comboBox_18)

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        """
        constraint file
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input constraint tree file")
        file = fileName[0]
        if file:
            self.input(files=file, lineedit=self.lineEdit_2)
            # base = os.path.basename(file)
            # self.lineEdit_2.setText(base)
            # self.lineEdit_2.setToolTip(file)

    @pyqtSlot()
    def on_pushButton_5_clicked(self):
        """
        guide tree file
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input guide tree file")
        file = fileName[0]
        if file:
            self.input(files=file, lineedit=self.lineEdit_3)
            # base = os.path.basename(file)
            # self.lineEdit_3.setText(base)
            # self.lineEdit_3.setToolTip(file)

    @pyqtSlot()
    def on_toolButton_3_clicked(self):
        """
        mapping file for gene trees
        """
        tree_files = self.comboBox_20.fetchListsText()
        if not tree_files:
            QMessageBox.warning(self, "Warning",
                "<p style='line-height:25px; height:25px'>Please input gene tree files first!</p>")
            return
        self.create_mapping_widgets(self.geneTreeMapArray, mode="gene trees")

    @pyqtSlot()
    def on_toolButton_2_clicked(self):
        """
        mapping file for alignments
        """
        msa_files = self.comboBox_19.fetchListsText()
        if not msa_files:
            QMessageBox.warning(self, "Warning",
                "<p style='line-height:25px; height:25px'>Please input alignment files first!</p>")
            return
        self.create_mapping_widgets(self.msaMapArray, mode="alignments")

    @pyqtSlot()
    def on_toolButton_clicked(self):
        """
        mapping file for fasta/fastq
        """
        files = self.comboBox_18.fetchListsText()
        if not files:
            QMessageBox.warning(self, "Warning",
                "<p style='line-height:25px; height:25px'>Please input fasta/fastq files first!</p>")
            return
        self.create_mapping_widgets(self.fastMapArray, mode="fasta/q")

    @pyqtSlot()
    def on_pushButton_2_clicked(self, quiet=False):
        """
        Stop
        """
        if self.isRunning():
            if (not self.workflow) and (not quiet):
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "<p style='line-height:25px; height:25px'>ASTRAL is still running, terminate it?</p>",
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
                if (not self.workflow) and (not quiet):
                    QMessageBox.information(
                        self,
                        "ASTRAL/CASTER/WASTER",
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
            self.run_code()
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (
                str(time_start), str(time_end),
                self.time_used)
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(
                    self.description + f"\n\nIf you use PhyloSuite v2, please cite:\n{self.factory.get_PS_citation()}\n\n"
                                       "If you use ASTRAL, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
            ## 判断是否运行成功
            unfinished = False
            if (not os.path.exists(self.output_astral_tree)) or (os.stat(self.output_astral_tree).st_size == 0):
                self.unfinishedSig.emit()
                unfinished = True
            if (not self.interrupt) and (not unfinished):
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
        self.ASTRAL_settings.setValue('size', self.size())
        # self.ASTRAL_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.ASTRAL_settings.setValue(name, index)
            # if isinstance(obj, QCheckBox):
            #     state = obj.isChecked()
            #     self.ASTRAL_settings.setValue(name, state)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.ASTRAL_settings.setValue(name, float_)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.ASTRAL_settings.value('size', QSize(1000, 750)))
        self.factory.centerWindow(self)
        # self.move(self.ASTRAL_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                obj.installEventFilter(self)  # 安装事件过滤器，为了取消滚轮事件
                if name == "comboBox_6":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.ASTRAL_settings.value(name, "0")
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
                elif (name in ["comboBox_20", "comboBox_19", "comboBox_18"]) and self.autoInputs:
                    self.input(files=self.autoInputs, combobox=obj)
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.ASTRAL_settings.value(name, "0")
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
                    if (int(index) + 1) > obj.count():
                        # 避免comboBox_11出问题
                        index = 1
                    obj.setCurrentIndex(int(index))
            # elif isinstance(obj, QCheckBox):
            #     value = self.ASTRAL_settings.value(
            #         name, "no setting")  # get stored value from registry
            #     if value != "no setting":
            #         obj.setChecked(
            #             self.factory.str2bool(value))  # restore checkbox
            # elif isinstance(obj, QLineEdit):
            #     if name == "lineEdit_5" and self.autoInputs:
            #         self.input(self.autoInputs, obj)
            elif isinstance(obj, QDoubleSpinBox):
                obj.installEventFilter(self)  # 安装事件过滤器，为了取消滚轮事件
                ini_float_ = obj.value()
                float_ = self.ASTRAL_settings.value(name, ini_float_)
                obj.setValue(float(float_))

    def run_code(self):
        # rgx_test_model = re.compile(r"^ModelFinder will test (\d+) \w+ models")
        # rgx_part_model = re.compile(r"^Loading (\d+) partitions\.\.\.")
        # rgx_finished = re.compile(r"^Date and Time:")
        is_error = False  ##判断是否出了error
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = self.ASTRAL_popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = self.ASTRAL_popen.stdout.readline().decode("gbk", errors="ignore")
                if out_line == "" and self.ASTRAL_popen.poll() is not None:
                    break
                # list_outline = out_line.strip().split()
                self.logGuiSig.emit(out_line.strip())
                if out_line.startswith("Error"):
                    is_error = True
                    error_text = ""
                    break
                elif re.search(r"BAD CPU TYPE", out_line, re.IGNORECASE):
                    is_error = True
                    error_text = "ASTER is incompatible with your current CPU type. To proceed, please follow the manual " \
                                 "configuration guide available at https://github.com/chaoszhang/ASTER"
                    break
            else:
                break
        if is_error:
            self.interrupt = True
            self.ASTRAL_exception.emit(
                "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!" \
                if not error_text else error_text)
        self.ASTRAL_popen = None

    def clear_lineEdit(self):
        sender = self.sender()
        lineEdit = sender.parent()
        lineEdit.setText("")
        lineEdit.setToolTip("")

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
        # self.closeSig.emit("ASTRAL", self.fetchWorkflowSetting())
        # 断开showSig和closeSig的槽函数连接
        try:
            self.showSig.disconnect()
        except:
            pass
        try:
            self.closeSig.disconnect()
        except:
            pass
        if self.workflow:
            self.ui_closeSig.emit("ASTRAL/CASTER/WASTER")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            reply = QMessageBox.question(
                self,
                "ASTRAL/CASTER/WASTER",
                "<p style='line-height:25px; height:25px'>ASTRAL is still running, terminate it?</p>",
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
                QLineEdit):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                self.input(files=files, lineedit=obj)
        elif isinstance(
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
                self.input(files=files, combobox=obj)
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

        if (isinstance(obj, QDoubleSpinBox) or isinstance(obj, QSpinBox) or isinstance(obj, QComboBox)) and event.type()==QEvent.Wheel:
            return True  # 过滤掉滚轮事件

        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(ASTRAL, self).eventFilter(obj, event)  # 0

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of ASTRAL:")
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
            with open(self.exportPath + os.sep + "PhyloSuite_ASTRAL.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "ASTRAL/CASTER/WASTER", "log", "text Format(*.txt)")
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

    def update_mapping_array(self):
        sender = self.sender()
        files = sender.fetchListsText()
        l_ = []
        if sender == self.comboBox_20:
            for file in files:
                ete_tre = self.factory.read_tree(file)
                l_.extend(ete_tre.get_leaf_names())
            self.geneTreeMapArray = [[i, i] for i in list(set(l_))]
        elif sender == self.comboBox_19:
            for file in files:
                parseFmt = Parsefmt()
                parseFmt.readfile(file)
                dict_taxon = parseFmt.dict_taxon
                l_.extend(list(dict_taxon.keys()))
            self.msaMapArray = [[i, i] for i in list(set(l_))]
        elif sender == self.comboBox_18:
            self.fastMapArray = []
            for file in files:
                base = os.path.splitext(os.path.basename(file))[0]
                self.fastMapArray.append([base, file])

    def input(self, files=None, combobox=None, lineedit=None):
        if combobox is not None:
            if type(files[0]) == list:
                # 自动识别的iqtree等上游建树结果
                trees, msas = files
                if trees:
                    self.comboBox_20.refreshInputs(trees)
                    # self.geneTreeMapArray = self.get_mapping_array(trees)
                else:
                    self.comboBox_20.refreshInputs([])
                if msas:
                    self.comboBox_19.refreshInputs(msas)
                    # self.msaMapArray = self.get_mapping_array(msas, mode="msa")
                else:
                    self.comboBox_19.refreshInputs([])
            else:
                if files:
                    combobox.refreshInputs(files)
                else:
                    combobox.refreshInputs([])
        if lineedit is not None:
            if files:
                base = os.path.basename(files)
                lineedit.setText(base)
                lineedit.setToolTip(files)
            else:
                lineedit.setText("")

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
            # self.textEdit_cmd.textChanged.connect(self.judgeCmdText)
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

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "ASTRAL_popen") and self.ASTRAL_popen and not self.interrupt

    def run_with_CMD(self, cmd):
        self.command = cmd
        if self.command:
            self.interrupt = False
            self.error_has_shown = False
            # self.list_pids = []
            # self.queue = multiprocessing.Queue()
            # thread = int(self.comboBox_6.currentText())
            # thread = thread if len(self.dict_args["inputFiles"]) > thread else len(self.dict_args["inputFiles"])
            # thread = 1 if not self.dict_args["inputFiles"] else thread # compare的情况
            # self.pool = multiprocessing.Pool(processes=thread,
            #                                  initializer=pool_init, initargs=(self.queue,))
            # # # Check for progress periodically
            # self.timer = QTimer()
            # self.timer.timeout.connect(self.updateProcess)
            # self.timer.start(1)
            self.ASTRAL_popen = self.factory.init_popen(self.command)
            self.factory.emitCommands(self.logGuiSig, f"cd \"{os.path.normpath(self.exportPath)}\"\n{self.command}")
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
            self.on_pushButton_9_clicked()

    def fetchCommands(self):
        if self.isFileIn():
            self.interrupt = False
            self.error_has_shown = False
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath + \
                                                      os.sep + "ASTER_results" + os.sep + self.output_dir_name)
            self.dict_args = {}
            self.dict_args["workPath"] = self.workPath
            self.dict_args["exportPath"] = self.exportPath
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                # 提醒是否删除旧结果，如果用户取消，就不执行
                return
            ## 切换到当前路径
            os.chdir(self.exportPath)
            list_command = []
            if self.comboBox_9.currentText() == "ASTRAL":
                program = f"\"{self.ASTRALPath}\""
            elif self.comboBox_9.currentText() == "ASTRAL-PRO (for both paralogs and othorlogs)":
                if platform.system().lower() != "windows":
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/astral-pro\""
                else:
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/astral-pro.exe\""
            elif self.comboBox_9.currentText() == "Weighted ASTRAL (branch length | support value | both | unweighted)":
                if platform.system().lower() != "windows":
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/astral-hybrid\""
                else:
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/astral-hybrid.exe\""
            elif self.comboBox_9.currentText() == "Caster-site (Coalescence-aware Alignment-based Species Tree EstimatoR - Site)":
                if platform.system().lower() != "windows":
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/caster-site\""
                else:
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/caster-site.exe\""
            elif self.comboBox_9.currentText() == "Caster-pair (Coalescence-aware Alignment-based Species Tree EstimatoR - Pair)":
                if platform.system().lower() != "windows":
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/caster-pair\""
                else:
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/caster-pair.exe\""
            elif self.comboBox_9.currentText() == "Waster (Without-Alignment/Assembly Species Tree EstimatoR)":
                if platform.system().lower() != "windows":
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/waster\""
                else:
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/waster.exe\""
            elif self.comboBox_9.currentText() == "Waster with branch (Without-Alignment/Assembly Species Tree EstimatoR) SLOW":
                if platform.system().lower() != "windows":
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/waster_branchlength\""
                else:
                    program = f"\"{os.path.dirname(self.ASTRALPath)}/waster_branchlength.exe\""
            list_command.append(program)
            # shutil.copy(self.lineEdit_5.toolTip(), self.exportPath)
            # list_command.append(f"-i \"{self.lineEdit_5.text()}\"")
            if self.radioButton_2.isChecked():
                tree_files = self.comboBox_20.fetchListsText()
                l_ = []
                for tree_file in tree_files:
                    with open(tree_file, encoding="utf-8", errors='ignore') as f_in:
                        l_.append(f_in.read().strip())
                tree_file = f"{self.exportPath}{os.sep}input.trees"
                with open(tree_file, "w", encoding="utf-8", errors='ignore') as f_out:
                    f_out.write("\n".join(l_) + "\n")
                list_command.append(f"-i input.trees")
                with open(f"{self.exportPath}{os.sep}gene_spe_map.txt", 'w', errors='ignore') as f:
                    f.write("\n".join(["\t".join(row) for row in self.geneTreeMapArray]))
                list_command.append(f"-a gene_spe_map.txt")
            elif self.radioButton_3.isChecked():
                with open(f"{self.exportPath}{os.sep}list_fastaq_files.txt", 'w', errors='ignore') as f:
                    f.write("\n".join(["\t".join(row) for row in self.fastMapArray]))
                list_command.append(f"-i list_fastaq_files.txt")
            elif self.radioButton.isChecked():
                files = self.comboBox_19.fetchListsText()
                with open(f"{self.exportPath}{os.sep}list_msa_files.txt", 'w', errors='ignore') as f:
                    f.write("\n".join(files))
                list_command.append(f"-i list_msa_files.txt")
                list_command.append(f"-f list")
                with open(f"{self.exportPath}{os.sep}gene_spe_map.txt", 'w', errors='ignore') as f:
                    f.write("\n".join(["\t".join(row) for row in self.msaMapArray]))
                list_command.append(f"-a gene_spe_map.txt")
            if self.lineEdit_2.text():
                shutil.copy(self.lineEdit_2.toolTip(), self.exportPath)
                list_command.append(f"-c \"{self.lineEdit_2.text()}\"")
            # if self.lineEdit_4.text():
            #     shutil.copy(self.lineEdit_4.toolTip(), self.exportPath)
            #     list_command.append(f"-a \"{self.lineEdit_4.text()}\"")
            if self.lineEdit_3.text():
                shutil.copy(self.lineEdit_3.toolTip(), self.exportPath)
                list_command.append(f"-g \"{self.lineEdit_3.text()}\"")
            search_ = self.comboBox_10.currentText()
            if search_ == "Default (r=4, s=4)":
                list_command.append("-r 4 -s 4")
            elif search_ == "Large (r=16, s=16)":
                list_command.append("-r 16 -s 16")
            elif search_ == "Minimum (r=1, s=0)":
                list_command.append("-r 1 -s 0")
            support_ = self.comboBox_11.currentText()
            if support_ == "length and support only":
                list_command.append("-u 1")
            elif support_ == "no branch or support":
                list_command.append("-u 0")
            elif support_ == "detailed":
                list_command.append("-u 2")
            elif support_ == "freqQuad.csv":
                list_command.append("-u 3")
            # length unit
            if self.comboBox_14.isEnabled():
                list_command.append(f"--length {self.comboBox_14.currentText().split(':')[0].strip()}")
            # Ambiguity
            if self.comboBox_15.isEnabled():
                list_command.append(f"--ambiguity {self.comboBox_15.currentText().split(':')[0].strip()}")
            # chunk
            if self.spinBox.isEnabled():
                list_command.append(f"--chunk {self.spinBox.value()}")
            # Objective
            if self.comboBox_16.isEnabled():
                list_command.append(f"--objective {self.comboBox_16.currentText().split(':')[0].strip()}")
            # Pairdist
            if self.spinBox_2.isEnabled():
                list_command.append(f"--pairdist {self.spinBox_2.value()}")
            # waster mode
            if self.comboBox_17.isEnabled():
                list_command.append(f"--mode {self.comboBox_17.currentText().split(':')[0].strip()}")
            if self.spinBox_3.isEnabled():
                list_command.append(f"--qcs {self.spinBox_3.value()}")
            if self.spinBox_4.isEnabled():
                list_command.append(f"--qcn {self.spinBox_4.value()}")
            list_command.append(f"-t {self.comboBox_6.currentText()}")
            list_command.append(f"--proportion {self.doubleSpinBox.value()}")
            # support 相关
            if self.comboBox_12.isEnabled():
                if self.comboBox_12.currentText() == "Bootstrap support value":
                    list_command.append("-S")
                elif self.comboBox_12.currentText() == "Likelihood (alrt) support value":
                    list_command.append("-L")
                elif self.comboBox_12.currentText() == "Probability (abayes) support value":
                    list_command.append("-B")
                else:
                    list_command.append(f"-x {self.doubleSpinBox_3.value()} "
                                        f"-n {self.doubleSpinBox_2.value()} "
                                        f"-d {self.doubleSpinBox_4.value()}")
            self.output_astral_tree = f"{self.exportPath}/{self.lineEdit.text() if self.lineEdit.text() else 'ASTRAL.nwk'}"
            list_command.append(f"-o \"{self.output_astral_tree}\"")
            command = " ".join(list_command)
            program = self.comboBox_9.currentText()
            if program == "ASTRAL":
                self.reference = "[1] Chao Zhang, Siavash Mirarab, Weighting by Gene Tree Uncertainty Improves Accuracy of " \
                                 "Quartet-based Species Trees, Molecular Biology and Evolution, 2022, msac215, " \
                                 "https://doi.org/10.1093/molbev/msac215.\n" \
                                 "[2] Zhang, Chao, Maryam Rabiee, Erfan Sayyari, and Siavash Mirarab. 2018. " \
                                 "“ASTRAL-III: Polynomial Time Species Tree Reconstruction from Partially Resolved " \
                                 "Gene Trees.” BMC Bioinformatics 19 (S6): 153. https://doi.org/10.1186/s12859-018-2129-y."
                cmd_used = f"We obtained the species tree from gene trees using wASTRAL-unweighted v{self.version} " \
                           f"[1] by optimizing the objective function of ASTRAL [2]."
            elif program == "ASTRAL-PRO (for both paralogs and othorlogs)":
                self.reference = "[1] Chao Zhang, Rasmus Nielsen, Siavash Mirarab, ASTER: A Package for Large-scale " \
                                 "Phylogenomic Reconstructions, Molecular Biology and Evolution, 2025, msaf172, " \
                                 "https://doi.org/10.1093/molbev/msaf172\n" \
                                 "[2] Chao Zhang, Celine Scornavacca, Erin K Molloy, Siavash Mirarab, ASTRAL-Pro: " \
                                 "Quartet-Based Species-Tree Inference despite Paralogy, " \
                                 "Molecular Biology and Evolution, Volume 37, Issue 11, November 2020, Pages 3292–3307, " \
                                 "https://doi.org/10.1093/molbev/msaa139"
                cmd_used = f"We obtained the species tree from muti-copy gene family trees using " \
                           f"ASTRAL-Pro3 v{self.version} [1] by optimizing the objective function of " \
                           f"ASTRAL-Pro [2]."
            else:
                self.reference = "[1] Chao Zhang, Siavash Mirarab, Weighting by Gene Tree Uncertainty Improves Accuracy " \
                                 "of Quartet-based Species Trees, Molecular Biology and Evolution, 2022, msac215, " \
                                 "https://doi.org/10.1093/molbev/msac215\n" \
                                 "[2] Chao Zhang, Maryam Rabiee, Erfan Sayyari, and Siavash Mirarab. 2018. " \
                                 "“ASTRAL-III: Polynomial Time Species Tree Reconstruction from Partially " \
                                 "Resolved Gene Trees.” BMC Bioinformatics 19 (S6): 153. doi:10.1186/s12859-018-2129-y."
                cmd_used = f"We obtained the species tree from gene trees using wASTRAL-unweighted v{self.version} [1] " \
                           f"by optimizing the objective function of ASTRAL [2]. "
            self.description = cmd_used # f"Low similarity segments within the alignment were removed with ASTRAL " \
                               # f"v{self.version} (Di Franco et al., 2019) using \"{cmd_used}\" command."
            self.textEdit_log.clear()  # 清空
            return command
        else:
            QMessageBox.critical(
                self,
                "ASTRAL/CASTER/WASTER",
                "<p style='line-height:25px; height:25px'>Please input file first!</p>")

    def updateProcess(self):
        if self.queue.empty(): return
        info = self.queue.get()
        if info[0] == "log":
            message = info[1]
            self.logGuiSig.emit(message)
        elif info[0] == "prog":
            self.finishedFileNum += 1
            if not self.interrupt:
                self.progressSig.emit(self.finishedFileNum * 100/self.totalFileNum)
                self.workflow_progress.emit(self.finishedFileNum * 100/self.totalFileNum)
        elif info[0] == "popen":
            self.list_pids.append(info[1])
        elif info[0] == "error":
            error_text = info[1]
            self.on_pushButton_2_clicked(quiet=True) #杀掉进程
            self.ASTRAL_exception.emit(
                "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!" \
                if not error_text else error_text)
            self.error_has_shown = True
        elif info[0] == "popen finished":
            if info[1] in self.list_pids:
                self.list_pids.remove(info[1])

    def popup_ASTRAL_exception(self, text):
        if not self.error_has_shown:
            QMessageBox.critical(
                self,
                "ASTRAL/CASTER/WASTER",
                "<p style='line-height:25px; height:25px'>%s</p>" % text)
            if "Show log" in text:
                self.on_pushButton_9_clicked()

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("ASTRAL/CASTER/WASTER", self.workPath, self.auto_popSig, self)

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
            self.input(files=autoInputs, combobox=self.comboBox_20)

    def fetchWorkflowSetting(self):
        '''* Alignment Mode
          * Code table(if codon mode)
          * strategy
          * export format'''
        settings = '''<p class="title">***ASTRAL***</p>'''
        c1 = self.doubleSpinBox.value()
        c2 = self.doubleSpinBox_2.value()
        c3 = self.doubleSpinBox_3.value()
        c4 = self.doubleSpinBox_4.value()
        settings += '<p>costs: \"<a href="self.ASTRAL_exe doubleSpinBox.setFocus() doubleSpinBox.selectAll() ' \
                    'factory.highlightWidgets(x.doubleSpinBox)">%s</a>\" ' \
                    '\"<a href="self.ASTRAL_exe doubleSpinBox_2.setFocus() doubleSpinBox_2.selectAll() ' \
                    'factory.highlightWidgets(x.doubleSpinBox_2)">%s</a>\" ' \
                    '\"<a href="self.ASTRAL_exe doubleSpinBox_3.setFocus() doubleSpinBox_3.selectAll() ' \
                    'factory.highlightWidgets(x.doubleSpinBox_3)">%s</a>\" ' \
                    '\"<a href="self.ASTRAL_exe doubleSpinBox_4.setFocus() doubleSpinBox_4.selectAll() ' \
                    'factory.highlightWidgets(x.doubleSpinBox_4)">%s</a>\"</p>' % (c1, c2, c3, c4)
        verbosity = self.comboBox_5.currentText()
        settings += '<p>verbosity: <a href="self.ASTRAL_exe comboBox_5.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_5)">%s</a></p>' % verbosity
        profile = self.comboBox_3.currentText()
        settings += '<p>profile: <a href="self.ASTRAL_exe comboBox_3.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_3)">%s</a></p>' % profile
        thread = self.comboBox_6.currentText()
        settings += '<p>Thread: <a href="self.ASTRAL_exe comboBox_6.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_6)">%s</a></p>' % thread
        specificity = "Yes" if self.checkBox.isChecked() else "No"
        settings += '<p>specificity: <a href="self.ASTRAL_exe' \
                    ' factory.highlightWidgets(x.checkBox)">%s</a></p>' % specificity
        large = "Yes" if self.checkBox_2.isChecked() else "No"
        settings += '<p>large: <a href="self.ASTRAL_exe' \
                    ' factory.highlightWidgets(x.checkBox_2)">%s</a></p>' % large
        changeID = "Yes" if self.checkBox_6.isChecked() else "No"
        settings += '<p>changeID: <a href="self.ASTRAL_exe' \
                    ' factory.highlightWidgets(x.checkBox_6)">%s</a></p>' % changeID
        noX = "Yes" if self.checkBox_5.isChecked() else "No"
        settings += '<p>noX: <a href="self.ASTRAL_exe' \
                    ' factory.highlightWidgets(x.checkBox_5)">%s</a></p>' % noX
        return settings

    def isFileIn(self):
        if self.radioButton_3.isChecked():
            return self.comboBox_18.count()
        elif self.radioButton_2.isChecked():
            return self.comboBox_20.count()
        elif self.radioButton.isChecked():
            return self.comboBox_19.count()

    def popup_unfinished_exception(self):
        QMessageBox.critical(
            self,
            "ASTRAL/CASTER/WASTER",
            "<p style='line-height:25px; height:25px'>ASTRAL run failed, "
            "click <span style=\"color:red\">Show log</span> to see details!</p>",
            QMessageBox.Ok)
        self.on_pushButton_9_clicked()

    def switch_widgets(self, text):
        if text in ["Weighted ASTRAL (branch length | support value | both | unweighted)"]:
            for i in [self.label_25, self.comboBox_12, self.label_7, self.doubleSpinBox_2,
                      self.label_11, self.doubleSpinBox_3, self.label_12, self.doubleSpinBox_4,
                      self.comboBox_13, self.label_26]:
                i.setEnabled(True)
        else:
            for i in [self.label_25, self.comboBox_12, self.label_7, self.doubleSpinBox_2,
                      self.label_11, self.doubleSpinBox_3, self.label_12, self.doubleSpinBox_4,
                      self.comboBox_13, self.label_26]:
                i.setEnabled(False)
        # -u
        if text in ["Caster-site (Coalescence-aware Alignment-based Species Tree EstimatoR - Site)",
                    "Caster-pair (Coalescence-aware Alignment-based Species Tree EstimatoR - Pair)",
                    "Waster (Without-Alignment/Assembly Species Tree EstimatoR)"]:
            self.comboBox_11.setCurrentIndex(1)
            self.comboBox_11.removeItem(3)
        else:
            if self.comboBox_11.count() < 4:
                self.comboBox_11.addItem("freqQuad.csv")
        # length unit
        if text in ["Caster-pair (Coalescence-aware Alignment-based Species Tree EstimatoR - Pair)",
                    "Weighted ASTRAL (branch length | support value | both | unweighted)"]:
            self.comboBox_14.setEnabled(False)
            self.label_27.setEnabled(False)
        else:
            self.comboBox_14.setEnabled(True)
            self.label_27.setEnabled(True)
        # Ambiguity:
        if text in ["Caster-site (Coalescence-aware Alignment-based Species Tree EstimatoR - Site)"]:
            self.comboBox_15.setEnabled(True)
            self.label_28.setEnabled(True)
        else:
            self.comboBox_15.setEnabled(False)
            self.label_28.setEnabled(False)
        # chunk
        if text in ["Caster-site (Coalescence-aware Alignment-based Species Tree EstimatoR - Site)",
                    "Caster-pair (Coalescence-aware Alignment-based Species Tree EstimatoR - Pair)"]:
            self.spinBox.setEnabled(True)
            self.label_29.setEnabled(True)
            self.radioButton.setChecked(True)
            self.lineEdit.setText("Caster.nwk")
        else:
            self.spinBox.setEnabled(False)
            self.label_29.setEnabled(False)
        # Objective,Pairdist
        if text in ["Caster-pair (Coalescence-aware Alignment-based Species Tree EstimatoR - Pair)"]:
            self.comboBox_16.setEnabled(True)
            self.spinBox_2.setEnabled(True)
            self.label_31.setEnabled(True)
            self.label_30.setEnabled(True)
        else:
            self.comboBox_16.setEnabled(False)
            self.spinBox_2.setEnabled(False)
            self.label_31.setEnabled(False)
            self.label_30.setEnabled(False)
        # waster mode
        if text in ["Waster (Without-Alignment/Assembly Species Tree EstimatoR)",
                    "Waster with branch (Without-Alignment/Assembly Species Tree EstimatoR) SLOW"]:
            self.comboBox_17.setEnabled(True)
            self.spinBox_3.setEnabled(True)
            self.spinBox_4.setEnabled(True)
            self.label_34.setEnabled(True)
            self.label_32.setEnabled(True)
            self.label_33.setEnabled(True)
            self.radioButton_3.setChecked(True)
            self.lineEdit.setText("WASTER.nwk")
        else:
            self.comboBox_17.setEnabled(False)
            self.spinBox_3.setEnabled(False)
            self.spinBox_4.setEnabled(False)
            self.label_34.setEnabled(False)
            self.label_32.setEnabled(False)
            self.label_33.setEnabled(False)
        # ASTRAL mode
        if text in ["ASTRAL",
                    "ASTRAL-PRO (for both paralogs and othorlogs)",
                    "Weighted ASTRAL (branch length | support value | both | unweighted)"]:
            self.radioButton_2.setChecked(True)
            self.lineEdit.setText("ASTRAL.nwk")

    def switch_support(self, text):
        if text == "Bootstrap support value":
            self.doubleSpinBox_4.setValue(0)
            self.doubleSpinBox_2.setValue(0)
            self.doubleSpinBox_3.setValue(100)
        elif text == "Likelihood (alrt) support value":
            self.doubleSpinBox_4.setValue(0)
            self.doubleSpinBox_2.setValue(0)
            self.doubleSpinBox_3.setValue(1)
        elif text == "Probability (abayes) support value":
            self.doubleSpinBox_4.setValue(0.333)
            self.doubleSpinBox_2.setValue(0.333)
            self.doubleSpinBox_3.setValue(1)

    def create_mapping_widgets(self, init_array, mode="species-file"):
        self.MapDialog = QDialog(self)
        self.MapDialog.resize(1000, 1000)
        self.MapDialog.setWindowTitle("Mapping table")
        self.MapDialog.setObjectName("MappingDialog")
        verticalLayout = QVBoxLayout(self.MapDialog)
        verticalLayout.setObjectName("verticalLayout")
        horizontalLayout_2 = QHBoxLayout()
        horizontalLayout_2.setObjectName("horizontalLayout_2")
        label = QLabel("Mapping file:", self.MapDialog)
        label.setObjectName("label")
        horizontalLayout_2.addWidget(label)
        lineEdit_3 = QLineEdit(self.MapDialog)
        lineEdit_3.setEnabled(True)
        lineEdit_3.setCursor(QCursor(Qt.ArrowCursor))
        lineEdit_3.setReadOnly(True)
        lineEdit_3.setObjectName("lineEdit_3")
        lineEdit_3.setPlaceholderText("Optional! The table will be updated based on the file input")
        horizontalLayout_2.addWidget(lineEdit_3)
        pushButton_22 = QPushButton(self.MapDialog)
        pushButton_22.setEnabled(True)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/Open_folder_add_512px_1186192_easyicon.net.png"),
            QIcon.Normal, QIcon.Off)
        pushButton_22.setIcon(icon)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(pushButton_22.sizePolicy().hasHeightForWidth())
        pushButton_22.setSizePolicy(sizePolicy)
        pushButton_22.setMinimumSize(QSize(30, 26))
        pushButton_22.setMaximumSize(QSize(30, 26))
        # pushButton_22.setStyleSheet("")
        pushButton_22.setText("")
        pushButton_22.setObjectName("pushButton_22")
        horizontalLayout_2.addWidget(pushButton_22)
        verticalLayout.addLayout(horizontalLayout_2)
        pushButton = QPushButton("Export mapping table", self.MapDialog)
        pushButton.setObjectName("pushButton")
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/report_disk_32px_507034_easyicon.net.png"),
            QIcon.Normal, QIcon.Off)
        pushButton.setIcon(icon)
        # table view
        tableView = QTableView(self.MapDialog)
        if mode in ["alignments", "gene trees"]:
            col_names = ["Individual/Gene name", "Species name"]
            col_fixed = [0]
        elif mode=="fasta/q":
            col_names = ["Species name", "File"]
            col_fixed = [1]
        verticalLayout.addWidget(tableView)
        pushButton_22.clicked.connect(lambda: self.input_mapping_file(lineEdit_3, tableView))
        pushButton.clicked.connect(lambda: self.export_mapping_file(tableView))
        model_ = MyMappingTableModel(init_array, col_names, column_fixed=col_fixed, parent=tableView)
        tableView.setModel(model_)
        horizontalLayout = QHBoxLayout()
        horizontalLayout.setObjectName("horizontalLayout")
        label_2 = QLabel("<html><head/><body><p>Double click to edit the cell. <span style=\" color:#aa0000;\">"
                         "Close the window to apply the changes.</span></p></body></html>", self.MapDialog)
        horizontalLayout.addWidget(label_2)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        horizontalLayout.addItem(spacerItem)
        horizontalLayout.addWidget(pushButton)
        verticalLayout.addLayout(horizontalLayout)
        self.MapDialog.finished.connect(lambda : self.saveMapArray(tableView.model().arraydata, mode))
        self.MapDialog.setWindowFlags(self.MapDialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.MapDialog.exec_()

    def saveMapArray(self, array, mode):
        if mode == "alignments":
            self.msaMapArray = array
        elif mode == "gene trees":
            self.geneTreeMapArray = array
        elif mode=="fasta/q":
            self.fastMapArray = array

    def input_mapping_file(self, lineEdit, tableView):
        fileName, filetype = QFileDialog.getOpenFileName(self,
            "Open Mapping Table",
            filter="All Files (*);;Text Files (*.txt);;CSV Files (*.csv)")
        if fileName:
            base = os.path.basename(fileName)
            lineEdit.setText(base)
            lineEdit.setToolTip(fileName)
            # 处理tableview
            with open(fileName) as f:
                lines = [line.strip().split() for line in f if line.strip()]
            # 更新table
            tableView.model().arraydata = lines

    def export_mapping_file(self, tableView):
        fileName, filetype = QFileDialog.getSaveFileName(self,
            "Export Mapping Table",
            "mapping_table.txt",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)")
        if fileName:
            with open(fileName, 'w') as f:
                f.write("\n".join(["\t".join(row) for row in tableView.model().arraydata]))
            QMessageBox.information(self, "Export Successful", "Mapping table exported successfully!")

    def msaInputProgram(self, isChecked):
        if isChecked and (self.comboBox_9.currentText() not in ["Caster-site (Coalescence-aware Alignment-based Species Tree EstimatoR - Site)",
                                                 "Caster-pair (Coalescence-aware Alignment-based Species Tree EstimatoR - Pair)"]):
            self.comboBox_9.setCurrentText("Caster-site (Coalescence-aware Alignment-based Species Tree EstimatoR - Site)")

    def treesInputProgram(self, isChecked):
        if isChecked and (self.comboBox_9.currentText() not in ["ASTRAL", "ASTRAL-PRO (for both paralogs and othorlogs)",
                                                                "Weighted ASTRAL (branch length | support value | both | unweighted)"]):
            self.comboBox_9.setCurrentText("ASTRAL")

    def fastaqInputProgram(self, isChecked):
        if isChecked and (self.comboBox_9.currentText() not in ["Waster (Without-Alignment/Assembly Species Tree EstimatoR)",
                                                                "Waster with branch (Without-Alignment/Assembly Species Tree EstimatoR) SLOW"]):
            self.comboBox_9.setCurrentText("Waster (Without-Alignment/Assembly Species Tree EstimatoR)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = ASTRAL()
    ui.show()
    sys.exit(app.exec_())