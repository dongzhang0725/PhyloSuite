#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 自己调整好一个size，然后再guirestore恢复一下
import datetime
import glob
import re

import multiprocessing
import signal

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from uifiles.Ui_trimAl import Ui_trimAl
from src.factory import Factory, WorkThread, Parsefmt
import inspect
import os
import sys
import traceback
import subprocess
import platform
from multiprocessing.pool import ApplyResult

def run(dict_args, command, file):
    fileBase = os.path.basename(file)
    fileBase_ = os.path.splitext(fileBase)[0]
    if " -in alignment" in command:
        input = " -in \"%s\"" % file
        command = command.replace(" -in alignment", input)
    else:
        # compare 模式
        input = " -compareset \"%s\"" % file
        command = command.replace(" -compareset setFile", input)
    # out
    outFile = " -out \"%s\"" % (dict_args["exportPath"] + os.sep +
                                fileBase_ + "_trimAl" + dict_args["suffix"])
    command = command.replace(" -out outputFile", outFile)
    command = command.replace("$fileBase$", fileBase_) #html输出替换名字
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
    with open(dict_args["exportPath"] + os.sep + fileBase_ + ".log", "a", encoding="utf-8", errors='ignore') as log_file:
        log_file.write(command + "\n")
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
                # run.queue.put(("log", fileBase + " --- " + out_line.strip()))
            if re.search(r"ERROR", out_line):
                run.queue.put(("log", fileBase + " --- " + out_line.strip()))
                is_error = True
        if is_error:
            run.queue.put(("error",))
        else:
            if dict_args["stat"]:
                run.queue.put(("log", fileBase + " --- " + "Statistics output has been saved to \"%s.log\" file"%fileBase_))
        run.queue.put(("prog", "finished"))
        run.queue.put(("log", fileBase + " --- " + "Done!"))
        run.queue.put(("popen finished", popen.pid))
    return "finished"

def pool_init(queue):
    # see http://stackoverflow.com/a/3843313/852994
    run.queue = queue


class TrimAl(QDialog, Ui_trimAl, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    trimAl_exception = pyqtSignal(str)
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    # 用于输入文件后判断用
    ui_closeSig = pyqtSignal(str)
    # 用于flowchart自动popup combobox等操作
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)

    def __init__(
            self,
            workPath=None,
            TApath=None,
            autoInputs=None,
            focusSig=None,
            workflow=None,
            parent=None):
        super(TrimAl, self).__init__(parent)
        self.parent = parent
        self.function_name = "trimAl"
        self.workflow = workflow
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.TApath = TApath
        self.autoInputs = autoInputs
        self.setupUi(self)
        # 保存设置
        if not workflow:
            self.trimAl_settings = QSettings(
                self.thisPath + '/settings/trimAl_settings.ini', QSettings.IniFormat)
        else:
            self.trimAl_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.trimAl_settings.beginGroup("Workflow")
            self.trimAl_settings.beginGroup("temporary")
            self.trimAl_settings.beginGroup('trimAl')
        # File only, no fallback to registry or or.
        self.trimAl_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        # 判断程序的版本
        self.version = ""
        version_worker = WorkThread(
            lambda : self.factory.get_version("trimAl", self),
            parent=self)
        version_worker.start()
        #
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.logGuiSig.connect(self.addText2Log)
        self.trimAl_exception.connect(self.popup_trimAl_exception)
        self.comboBox_4.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        self.comboBox_4.installEventFilter(self)
        self.lineEdit_2.installEventFilter(self)
        self.lineEdit_3.installEventFilter(self)
        self.log_gui = self.gui4Log()
        # stat output file name
        self.lineEdit_2.setLineEditNoChange(True)
        self.lineEdit_3.setLineEditNoChange(True)
        self.lineEdit_2.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        self.lineEdit_3.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        # 选框联动
        self.checkBox_2.toggled.connect(self.switchCheckBox1)
        self.checkBox_5.toggled.connect(self.switchCheckBox1)
        # self.groupBox_5.toggled.connect(lambda bool_: self.groupBox_6.setChecked(not bool_))
        # self.groupBox_6.toggled.connect(lambda bool_: self.groupBox_5.setChecked(not bool_))
        self.checkBox_3.toggled.connect(self.switchCheckBox2)
        self.checkBox_6.toggled.connect(self.switchCheckBox2)
        self.checkBox_7.toggled.connect(self.switchCheckBox2)
        self.checkBox_8.toggled.connect(self.switchCheckBox2)
        self.checkBox_9.toggled.connect(self.judgeInput)
        self.radioButton.toggled.connect(self.Un_checkBox_9)
        self.comboBox_2.currentTextChanged.connect(self.judgeComboBox_2)
        self.comboBox.currentTextChanged.connect(self.judgeFormats)
        self.radioButton.toggled.connect(self.controlRefineText)
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
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-4-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-4-1-Brief-example"
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
            self.error_has_shown = False #保证只报一次错
            self.list_pids = []
            self.queue = multiprocessing.Queue()
            thread = int(self.comboBox_6.currentText())
            thread = thread if len(self.dict_args["inputFiles"]) > thread else len(self.dict_args["inputFiles"])
            thread = 1 if not self.dict_args["inputFiles"] else thread  # compare的情况
            self.pool = multiprocessing.get_context("spawn").Pool(processes=thread,
                                             initializer=pool_init, initargs=(self.queue,)) # \
                # if platform.system().lower() == "windows" else multiprocessing.Pool(processes=thread,
                #                                         initializer=pool_init, initargs=(self.queue,))
            # Check for progress periodically
            self.timer = QTimer()
            self.timer.timeout.connect(self.updateProcess)
            self.timer.start(1)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        show log
        """
        self.log_gui.show()

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        alignment file
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input alignment file")
        if fileNames[0]:
            self.input(fileNames[0])

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        """
        set file for comparison
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input file containing alignment path to compare")
        if fileName[0]:
            base = os.path.basename(fileName[0])
            self.lineEdit_2.setText(base)
            self.lineEdit_2.setToolTip(fileName[0])

    @pyqtSlot()
    def on_pushButton_22_clicked(self):
        """
        matrix file
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input matrix file")
        if fileName[0]:
            base = os.path.basename(fileName[0])
            self.lineEdit_3.setText(base)
            self.lineEdit_3.setToolTip(fileName[0])

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
                    "<p style='line-height:25px; height:25px'>trimAl is still running, terminate it?</p>",
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
                        "trimAl",
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
            if self.dict_args["keep name"]:
                ## 复制文件过来，并重命名序列名字，生成mapping文件
                list_input_files = []
                dict_name_mapping = {}
                total_file_num = len(self.dict_args["inputFiles"])
                for num, file in enumerate(self.dict_args["inputFiles"]):
                    dict_fas = self.factory.read_fasta_to_dic(file)
                    # 替换名字
                    list_fas_content = []
                    for num, key in enumerate(dict_fas.keys()):
                        if key not in dict_name_mapping.values():
                            if dict_name_mapping:
                                max_num = max(dict_name_mapping.keys(),
                                            key=lambda x: int(x.replace("seq", "")))
                                max_num = int(max_num.replace("seq", ""))
                            else:
                                max_num = 0
                            name = f"seq{max_num+1}"
                            dict_name_mapping[name] = key
                        else:
                            for new_name, old_name in dict_name_mapping.items():
                                if old_name == key:
                                    name = new_name
                                    break
                            # name = dict_name_mapping[key]
                        list_fas_content.append(f">{name}\n{dict_fas[key]}\n")
                    # 存文件
                    file_in_outpath = f"{self.dict_args['exportPath']}{os.sep}{os.path.basename(file)}"
                    list_input_files.append(file_in_outpath)
                    with open(file_in_outpath, "w") as f:
                        f.write("".join(list_fas_content))
                    self.progressSig.emit(0 + (5 * (num + 1)/total_file_num))
                    self.workflow_progress.emit(0 + (5 * (num + 1)/total_file_num))
                with open(f"{self.dict_args['exportPath']}{os.sep}html_name_mapping.tsv", "w") as f2:
                    f2.write("\n".join(["Old name\tNew name"] +
                                       [f"{old_name}\t{new_name}" for new_name, old_name in dict_name_mapping.items()]))
            else:
                list_input_files = self.dict_args["inputFiles"]
                dict_name_mapping = {}
            if self.radioButton.isChecked():
                async_results = [self.pool.apply_async(run, args=(self.dict_args, self.command, file)) for
                                 file in list_input_files]
                self.totalFileNum = len(list_input_files)
            else:
                async_results = [self.pool.apply_async(run, args=(self.dict_args, self.command,
                                                                  self.dict_args["compareFile"]))]
                self.totalFileNum = 1
            self.finishedFileNum = 0 #进度条用
            self.pool.close()  # 关闭进程池，防止进一步操作。如果所有操作持续挂起，它们将在工作进程终止前完成
            map(ApplyResult.wait, async_results)
            lst_results = [r.get() for r in async_results]
            # 判断比对是否成功
            trimAl_results = glob.glob(self.exportPath + os.sep + "*_trimAl.fas")
            empty_files = [os.path.basename(file) for file in trimAl_results if os.stat(file).st_size == 0]
            has_error = False
            if not trimAl_results or empty_files:
                has_error = True
                log = self.textEdit_log.toPlainText()
                list_commands = re.findall(r"Command: (.+)\n", log)
                last_cmd = list_commands[-1] if list_commands else ""
                self.trimAl_exception.emit(
                    "trimAl execute failed, click <span style=\"color:red\">Show log</span> to see details!"
                    "<br>You can also copy this command to terminal to debug: %s" % last_cmd)
            if not has_error:
                self.renameSequence(dict_name_mapping) #修剪后序列的名字被，需要改回来
            if self.dict_args["keep name"]:
                ## 删掉复制过来的文件
                for file in list_input_files:
                    try:
                        os.remove(file)
                    except:
                        pass
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (
                str(time_start), str(time_end),
                self.time_used)
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(
                    self.description + "\n\nIf you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n"
                                       "If you use trimAl, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
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
        self.trimAl_settings.setValue('size', self.size())
        # self.trimAl_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.trimAl_settings.setValue(name, index)
            elif isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.trimAl_settings.setValue(name, state)
            elif isinstance(obj, QRadioButton):
                state = obj.isChecked()
                self.trimAl_settings.setValue(name, state)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.trimAl_settings.setValue(name, float_)
            elif isinstance(obj, QLineEdit):
                value = obj.text()
                self.trimAl_settings.setValue(name, value)
            elif isinstance(obj, QTabWidget):
                index = obj.currentIndex()
                self.trimAl_settings.setValue(name, index)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.factory.judgeWindowSize(self.trimAl_settings, 748, 594))
        self.factory.centerWindow(self)
        # self.move(self.trimAl_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox_6":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.trimAl_settings.value(name, "0")
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
                    self.input(self.autoInputs)
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.trimAl_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(allItems):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        item.setToolTip(i)
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
            elif isinstance(obj, QCheckBox):
                value = self.trimAl_settings.value(
                    name, "no setting")  # get stored value from registry
                if value != "no setting":
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QRadioButton):
                value = self.trimAl_settings.value(
                    name, "no setting")  # get stored value from registry
                if value != "no setting":
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QDoubleSpinBox):
                ini_float_ = obj.value()
                float_ = self.trimAl_settings.value(name, ini_float_)
                obj.setValue(float(float_))
            elif isinstance(obj, QLineEdit):
                if name not in ["lineEdit_3", "lineEdit_2"]:
                    value = self.trimAl_settings.value(
                        name, "")  # get stored value from registry
                    if value:
                        obj.setText(value)  # restore checkbox
            elif isinstance(obj, QTabWidget):
                index = self.trimAl_settings.value(name, 0)
                obj.setCurrentIndex(int(index))

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
        self.closeSig.emit("trimAl", self.fetchWorkflowSetting())
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
            self.ui_closeSig.emit("trimAl")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            reply = QMessageBox.question(
                self,
                "trimAl",
                "<p style='line-height:25px; height:25px'>trimAl is still running, terminate it?</p>",
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
        name = obj.objectName()
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
                self.input(files)
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
                if name == "lineEdit_2":
                    base = os.path.basename(files[0])
                    self.lineEdit_2.setText(base)
                    self.lineEdit_2.setToolTip(files[0])
                elif name == "lineEdit_3":
                    base = os.path.basename(files[0])
                    self.lineEdit_3.setText(base)
                    self.lineEdit_3.setToolTip(files[0])
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
        return super(TrimAl, self).eventFilter(obj, event)  # 0

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of trimAl:")
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
            with open(self.exportPath + os.sep + "PhyloSuite_TrimAl_.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "trimAl", "log", "text Format(*.txt)")
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

    def input(self, list_items=None):
        if list_items:
            self.comboBox_4.refreshInputs(list_items)
        else:
            self.comboBox_4.refreshInputs([])

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

    def clear_lineEdit(self):
        sender = self.sender()
        lineEdit = sender.parent()
        lineEdit.setText("")
        lineEdit.setToolTip("")

    def fetchCommands(self):
        if (self.radioButton.isChecked() and self.comboBox_4.count()) or \
                (self.radioButton_2.isChecked() and self.lineEdit_2.toolTip()):
            self.interrupt = False
            self.error_has_shown = False
            self.dict_args = {}
            self.dict_args["workPath"] = self.workPath
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath + \
                                                      os.sep + "trimAl_results" + os.sep + self.output_dir_name)
            self.dict_args["exportPath"] = self.exportPath
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                # 提醒是否删除旧结果，如果用户取消，就不执行
                return
            if self.tabWidget.tabText(self.tabWidget.currentIndex()) == "Automated Trimming":
                # 自动模式
                method = self.getAutoMethod()
                self.dict_args["autoMethod"] = " -%s"%method
                self.dict_args["cons"] = ""
                self.dict_args["gt"] = ""
                self.dict_args["st"] = ""
                self.dict_args["ct"] = ""
                self.dict_args["w"] = ""
                self.dict_args["gw"] = ""
                self.dict_args["sw"] = ""
                self.dict_args["cw"] = ""
            else:
                # 人工模式
                self.dict_args["autoMethod"] = ""
                self.dict_args["cons"] = " -cons %.1f"%self.doubleSpinBox.value()
                self.dict_args["gt"] = " -gt %.1f" % self.doubleSpinBox_2.value()
                self.dict_args["st"] = " -st %.1f" % self.doubleSpinBox_3.value()
                self.dict_args["ct"] = " -ct %.1f" % self.doubleSpinBox_4.value() if self.checkBox_9.isChecked() else ""
                self.dict_args["w"] = " -w %.1f" % self.doubleSpinBox_7.value() if self.checkBox_3.isChecked() else ""
                self.dict_args["gw"] = " -gw %.1f" % self.doubleSpinBox_6.value() if self.checkBox_6.isChecked() else ""
                self.dict_args["sw"] = " -sw %.1f" % self.doubleSpinBox_5.value() if self.checkBox_7.isChecked() else ""
                self.dict_args["cw"] = " -cw %.1f" % self.doubleSpinBox_8.value() if self.checkBox_8.isChecked() else ""
            self.dict_args["complementary"] = " -complementary" if self.checkBox.isChecked() else ""
            self.dict_args["colnumbering"] = " -colnumbering" if self.checkBox_2.isChecked() else ""
            html_file_name = self.lineEdit_4.text() if self.lineEdit_4.text() else "summary.html"
            self.dict_args["htmlout"] = " -htmlout \"%s\""%(self.dict_args["exportPath"] +
                                                            os.sep + "$fileBase$_" + html_file_name) if self.checkBox_4.isChecked() else ""
            self.dict_args["stat"] = " -%s"%self.comboBox_2.currentText().split(":")[0] if self.checkBox_5.isChecked() else ""
            self.dict_args["outFormat"] = " -%s"%self.comboBox.currentText()
            # 输出文件后缀
            dict_suffix = {"fasta": ".fas", "phylip": ".phy", "phylip3.2": ".phy", "nexus": ".nex",
                           "mega": ".meg", "clustal":".clw", "nbrf": ".nbrf"}
            self.dict_args["suffix"] = dict_suffix[self.comboBox.currentText()]
            self.dict_args["trimAl"] = self.TApath
            # 是否保持序列的名字
            self.dict_args["keep name"] = self.checkBox_10.isChecked()
            ##输入文件
            if self.radioButton.isChecked():
                self.dict_args["compareFile"] = ""
                self.dict_args["inputFiles"] = self.comboBox_4.fetchListsText()
                command = "\"{trimAl}\" -in alignment{autoMethod}{cons}{gt}{st}{ct}" \
                          "{w}{gw}{sw}{cw}{complementary}{colnumbering}{htmlout}" \
                          "{outFormat} -out outputFile{stat}".format(**self.dict_args)
            else:
                # compare
                self.dict_args["inputFiles"] = []
                self.dict_args["compareFile"] = self.lineEdit_2.toolTip()
                command = "\"{trimAl}\" -compareset setFile{autoMethod}{cons}{gt}{st}{ct}" \
                          "{w}{gw}{sw}{cw}{complementary}{colnumbering}{htmlout}{outFormat}" \
                          " -out outputFile{stat}".format(**self.dict_args)
            self.reference = "Capella-Gutierrez S, Silla-Martinez JM, Gabaldon T. 2009. trimAl: a tool for automated" \
                             " alignment trimming in large-scale phylogenetic analyses. Bioinformatics. 25: 1972-1973. " \
                             "doi: 10.1093/bioinformatics/btp348."
            cmd_used = "{autoMethod}{cons}{gt}{st}{ct}{w}{gw}{sw}{cw}".format(**self.dict_args).strip()
            self.description = f"Gap sites were removed with trimAl v{self.version} (Capella‐Gutiérrez et al., 2009) " \
                               f"using \"{cmd_used}\" command."
            self.textEdit_log.clear()  # 清空
            return command
        else:
            if self.radioButton.isChecked():
                QMessageBox.critical(
                    self,
                    "trimAl",
                    "<p style='line-height:25px; height:25px'>Please input files to \"Input\" box first!</p>")
            else:
                QMessageBox.critical(
                    self,
                    "trimAl",
                    "<p style='line-height:25px; height:25px'>Please input files to \"Compare set\" box first!</p>")

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "pool") and self.pool and not self.interrupt

    def run_with_CMD(self, cmd):
        self.command = cmd
        if self.command:
            self.interrupt = False
            self.error_has_shown = False
            self.list_pids = []
            self.queue = multiprocessing.Queue()
            thread = int(self.comboBox_6.currentText())
            thread = thread if len(self.dict_args["inputFiles"]) > thread else len(self.dict_args["inputFiles"])
            thread = 1 if not self.dict_args["inputFiles"] else thread # compare的情况
            self.pool = multiprocessing.get_context("spawn").Pool(processes=thread,
                                             initializer=pool_init, initargs=(self.queue,)) # \
                # if platform.system().lower() == "windows" else multiprocessing.Pool(processes=thread,
                #                                                                    initializer=pool_init, initargs=(self.queue,))
            # # Check for progress periodically
            self.timer = QTimer()
            self.timer.timeout.connect(self.updateProcess)
            self.timer.start(1)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

    def judgeCmdText(self):
        text = self.textEdit_cmd.toPlainText()
        if self.radioButton.isChecked():
            if " -in alignment" not in text:
                QMessageBox.information(
                    self,
                    "trimAl",
                    "<p style='line-height:25px; height:25px'>\"-in alignment\" cannot be changed!</p>")
                self.textEdit_cmd.undo()
        else:
            if " -compareset setFile" not in text:
                QMessageBox.information(
                    self,
                    "trimAl",
                    "<p style='line-height:25px; height:25px'>\"-compareset setFile\" cannot be changed!</p>")
                self.textEdit_cmd.undo()

    def updateProcess(self):
        if self.queue.empty(): return
        info = self.queue.get()
        if info[0] == "log":
            message = info[1]
            self.logGuiSig.emit(message)
        elif info[0] == "prog":
            self.finishedFileNum += 1
            if not self.interrupt:
                self.workflow_progress.emit(5 + self.finishedFileNum * 90/self.totalFileNum)
                self.progressSig.emit(5 + self.finishedFileNum * 90/self.totalFileNum)
        elif info[0] == "popen":
            self.list_pids.append(info[1])
        elif info[0] == "error":
            self.on_pushButton_2_clicked(quiet=True) #杀掉进程
            self.trimAl_exception.emit(
                "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!")
            self.error_has_shown = True
        elif info[0] == "popen finished":
            if info[1] in self.list_pids:
                self.list_pids.remove(info[1])

    def popup_trimAl_exception(self, text):
        if not self.error_has_shown:
            QMessageBox.critical(
                self,
                "trimAl",
                "<p style='line-height:25px; height:25px'>%s</p>" % text)
            if "Show log" in text:
                self.on_pushButton_9_clicked()

    def judgeComboBox_2(self, text):
        if text in ["sfc: Print compare values for columns in the selected alignment from compare files method.",
                    "sft: Print accumulated compare values count for the selected alignment from compare files method."] \
                and self.radioButton.isChecked():
            QMessageBox.information(
                self,
                "trimAl",
                "<p style='line-height:25px; height:25px'>This option should be used in combination with \"Compare set\".</p>")
            self.comboBox_2.setCurrentIndex(0)

    def switchCheckBox1(self, bool_):
        checkbox = self.sender()
        if (checkbox == self.checkBox_2) and bool_ and self.checkBox_5.isChecked():
            self.checkBox_5.setChecked(False)
        if (checkbox == self.checkBox_5) and bool_ and self.checkBox_2.isChecked():
            self.checkBox_2.setChecked(False)

    def switchCheckBox2(self, bool_):
        checkbox = self.sender()
        if checkbox == self.checkBox_3:
            if bool_:
                for i in [self.checkBox_6, self.checkBox_7, self.checkBox_8]:
                    i.setChecked(not bool_)
        else:
            if bool_:
                self.checkBox_3.setChecked(not bool_)

    def judgeInput(self, bool_):
        if bool_ and (not self.radioButton_2.isChecked()):
            QMessageBox.information(
                self,
                "trimAl",
                "<p style='line-height:25px; height:25px'>This option should be used in combination with \"Compare set\".</p>")
            self.checkBox_9.setChecked(False)

    def Un_checkBox_9(self, bool_):
        if bool_:
            self.checkBox_9.setChecked(not bool_)

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("trimAl", self.workPath, self.auto_popSig, self)

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
            self.input(autoInputs)

    def judgeFormats(self, text):
        if text != "fasta":
            QMessageBox.warning(
                self,
                "HmmCleaner",
                "<p style='line-height:25px; height:25px'>\"%s\" format cannot be used by the downstream programs "
                "(e.g. concatenation), please select fasta format if you are going to use "
                "this result for other functions.</p>"%text)

    def renameSequence(self, dict_name_mapping):
        trimedFiles = glob.glob(self.exportPath + os.sep + "*_trimAl.fas")
        if trimedFiles:
            for num, file in enumerate(trimedFiles):
                with open(file, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                with open(file, "w", encoding="utf-8") as f1:
                    if dict_name_mapping:
                        f1.write(re.sub(r">(.+?) \d+ bp", lambda x: f">{dict_name_mapping[x.group(1)]}",
                                    content))
                    else:
                        f1.write(re.sub(r"(>.+?) \d+ bp", "\\1", content))
                self.progressSig.emit(95 + (3 * (num + 1)/len(trimedFiles)))
                self.workflow_progress.emit(95 + (3 * (num + 1)/len(trimedFiles)))
        if dict_name_mapping:
            max_len_name = len(max(dict_name_mapping.values(), key=len))
            html_files = glob.glob(self.exportPath + os.sep + "*.html")
            for html_file in html_files:
                with open(html_file, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                with open(html_file, "w", encoding="utf-8") as f1:
                    content = re.sub(r"(?m) +(\d+.+\n)^ +=",
                            lambda x: f"{' '*(max_len_name+17)}{x.group(1)}{' '*(max_len_name+9)}=", content)
                    f1.write(re.sub(r"(?m)(^ {4}%s)(.+?)(%s)"%(re.escape("<span class=sel>"), re.escape("</span>")),
                                lambda x: f"{x.group(1)}{dict_name_mapping[x.group(2)].ljust(max_len_name)}{x.group(3)}",
                                    content))
                self.progressSig.emit(98 + (2 * (num + 1)/len(html_files)))
                self.workflow_progress.emit(98 + (2 * (num + 1)/len(html_files)))
        else:
            self.progressSig.emit(100)
            self.workflow_progress.emit(100)


    def fetchWorkflowSetting(self):
        '''* Alignment Mode
          * Code table(if codon mode)
          * strategy
          * export format'''
        settings = '''<p class="title">***trimAl***</p>'''
        trim_strategy = self.tabWidget.tabText(self.tabWidget.currentIndex())
        settings += '<p>Trimming strategy: <a href="self.trimAl_exe' \
                    ' factory.highlightWidgets(x.tabWidget.tabBar())">%s</a></p>' % trim_strategy
        if trim_strategy == "Automated Trimming":
            # settings += "|--Automated Trimming--|"
            strategy = self.getAutoMethod()
            settings += '<p>Automated method: <a href="self.trimAl_exe ' \
                        'factory.highlightWidgets(x.radioButton_10,x.radioButton_11,x.radioButton_12,' \
                        'x.radioButton_13,x.radioButton_14,x.radioButton_15)">%s</a></p>' % strategy
        else:
            # settings += "|--Manual Trimming--|"
            cons = self.doubleSpinBox.value()
            settings += '<p>Minimum percentage of positions to conserve [0-100]: <a href="self.trimAl_exe ' \
                        'doubleSpinBox.setFocus() doubleSpinBox.selectAll()' \
                        ' factory.highlightWidgets(x.doubleSpinBox)">%s</a></p>' % cons
            gaps = self.doubleSpinBox_2.value()
            settings += '<p>Gap threshold, fraction of positions without gaps in a column [0-1]: <a href="self.trimAl_exe ' \
                        'doubleSpinBox_2.setFocus() doubleSpinBox_2.selectAll()' \
                        ' factory.highlightWidgets(x.doubleSpinBox_2)">%s</a></p>' % gaps
            ss = self.doubleSpinBox_3.value()
            settings += '<p>Similarity threshold, minimum level of residue similarity within a column [0-1]: <a href="self.trimAl_exe ' \
                        'doubleSpinBox_3.setFocus() doubleSpinBox_3.selectAll()' \
                        ' factory.highlightWidgets(x.doubleSpinBox_3)">%s</a></p>' % ss
            if self.checkBox_3.isChecked():
                w = self.doubleSpinBox_7.value()
                settings += '<p>General window size, applied to all stats: <a href="self.trimAl_exe ' \
                            'doubleSpinBox_7.setFocus() doubleSpinBox_7.selectAll()' \
                            ' factory.highlightWidgets(x.doubleSpinBox_7)">%s</a></p>' % w
            if self.checkBox_6.isChecked():
                gw = self.doubleSpinBox_6.value()
                settings += '<p>Window size applied to Gaps: <a href="self.trimAl_exe ' \
                            'doubleSpinBox_6.setFocus() doubleSpinBox_6.selectAll()' \
                            ' factory.highlightWidgets(x.doubleSpinBox_6)">%s</a></p>' % gw
            if self.checkBox_7.isChecked():
                sw = self.doubleSpinBox_5.value()
                settings += '<p>Window size applied to Similarity: <a href="self.trimAl_exe ' \
                            'doubleSpinBox_5.setFocus() doubleSpinBox_5.selectAll()' \
                            ' factory.highlightWidgets(x.doubleSpinBox_5)">%s</a></p>' % sw
            if self.checkBox_8.isChecked():
                cw = self.doubleSpinBox_8.value()
                settings += '<p>Window size applied to Consistency: <a href="self.trimAl_exe ' \
                            'doubleSpinBox_8.setFocus() doubleSpinBox_8.selectAll()' \
                            ' factory.highlightWidgets(x.doubleSpinBox_8)">%s</a></p>' % cw
        thread = self.comboBox_6.currentText()
        settings += '<p>Thread: <a href="self.trimAl_exe comboBox_6.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_6)">%s</a></p>' % thread
        return settings

    def isFileIn(self):
        return self.comboBox_4.count()

    def controlRefineText(self, bool_):
        if bool_:
            if not self.comboBox_4.count():
                self.comboBox_4.lineEdit().switchColor("No input files (Try to drag your file(s) and drop here)")
            else:
                self.comboBox_4.lineEdit().switchColor()
        else:
            self.comboBox_4.lineEdit().switchColor()

    def getAutoMethod(self):
        widgets = (self.gridLayout_8.itemAt(i).widget() for i in range(self.gridLayout_8.count()))
        checkedBox = [widget for widget in widgets if isinstance(widget, QRadioButton) and widget.isChecked()][0]
        return checkedBox.text()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = TrimAl()
    ui.show()
    sys.exit(app.exec_())