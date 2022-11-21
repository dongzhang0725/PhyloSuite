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

from uifiles.Ui_HmmCleaner import Ui_HmmCleaner
from src.factory import Factory, WorkThread
import inspect
import os
import sys
import traceback
import subprocess
import platform
from multiprocessing.pool import ApplyResult


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
                is_error = True
        if is_error:
            run.queue.put(("error",))
        else:
            pass
        run.queue.put(("prog", "finished"))
        run.queue.put(("log", fileBase + " --- " + "Done!"))
        run.queue.put(("popen finished", popen.pid))
    return "finished"

def pool_init(queue):
    # see http://stackoverflow.com/a/3843313/852994
    run.queue = queue

class HmmCleaner(QDialog, Ui_HmmCleaner, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    HmmCleaner_exception = pyqtSignal(str)
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
            HmmCleanerPath=None,
            autoInputs=None,
            perl=None,
            focusSig=None,
            workflow=None,
            parent=None):
        super(HmmCleaner, self).__init__(parent)
        self.parent = parent
        self.function_name = "HmmCleaner"
        self.workflow = workflow
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.autoInputs = autoInputs
        self.HmmCleanerPath = HmmCleanerPath
        self.perl = perl
        self.setupUi(self)
        # 保存设置
        if not workflow:
            self.HmmCleaner_settings = QSettings(
                self.thisPath + '/settings/HmmCleaner_settings.ini', QSettings.IniFormat)
        else:
            self.HmmCleaner_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.HmmCleaner_settings.beginGroup("Workflow")
            self.HmmCleaner_settings.beginGroup("temporary")
            self.HmmCleaner_settings.beginGroup('HmmCleaner')
        # File only, no fallback to registry or or.
        self.HmmCleaner_settings.setFallbacksEnabled(False)
        # print(self.HmmCleaner_settings.childGroups())
        # self.factory.settingsGroup2Group(self.HmmCleaner_settings, "PCGs", "temporary")
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        self.interrupt = False
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.logGuiSig.connect(self.addText2Log)
        self.comboBox_4.installEventFilter(self)
        self.comboBox_4.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        self.log_gui = self.gui4Log()
        self.HmmCleaner_exception.connect(self.popup_HmmCleaner_exception)
        self.checkBox_4.toggled.connect(self.popupAliWarning)
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
            self.error_has_shown = False  # 保证只报一次错
            self.list_pids = []
            self.queue = multiprocessing.Queue()
            thread = int(self.comboBox_6.currentText())
            thread = thread if len(self.dict_args["inputFiles"]) > thread else len(self.dict_args["inputFiles"])
            thread = 1 if not self.dict_args["inputFiles"] else thread  # compare的情况
            self.pool = multiprocessing.get_context("spawn").Pool(processes=thread,
                                             initializer=pool_init, initargs=(self.queue,)) #\
                # if platform.system().lower() == "windows" else \
                #                                 multiprocessing.Pool(processes=thread,
                #                                                      initializer=pool_init, initargs=(self.queue,))
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
    def on_pushButton_2_clicked(self, quiet=False):
        """
        Stop
        """
        if self.isRunning():
            if (not self.workflow) and (not quiet):
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "<p style='line-height:25px; height:25px'>HmmCleaner is still running, terminate it?</p>",
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
                        "HmmCleaner",
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
            # self.dict_file_progress = {os.path.basename(file): 0 for file in self.dict_args["seq_files"]}
            async_results = [self.pool.apply_async(run, args=(self.dict_args, self.command, file)) for
                             file in self.dict_args["inputFiles"]]
            self.totalFileNum = len(self.dict_args["inputFiles"])
            self.finishedFileNum = 0 #进度条用
            self.pool.close()  # 关闭进程池，防止进一步操作。如果所有操作持续挂起，它们将在工作进程终止前完成
            map(ApplyResult.wait, async_results)
            lst_results = [r.get() for r in async_results]
            # 判断比对是否成功
            HmmCleaner_results = glob.glob(self.exportPath + os.sep + "*_hmm.*")
            empty_files = [os.path.basename(file) for file in HmmCleaner_results if os.stat(file).st_size == 0]
            has_error = False
            if (not self.checkBox_3.isChecked()) and (not HmmCleaner_results or empty_files):
                # log_only不管
                has_error = True
                log = self.textEdit_log.toPlainText()
                if "Can't locate" in log:
                    country = self.factory.path_settings.value("country", "UK")
                    url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/#2-4-HmmCleaner-configuration" if \
                        country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/#2-4-HmmCleaner-configuration"
                    self.HmmCleaner_exception.emit(
                        "HmmCleaner executes failed, it seems the "
                        "<a href=\"https://cpandeps.grinnz.com/?dist=Bio-MUST-Apps-HmmCleaner&phase=build&perl_version=v5.30.0&style=table\">"
                        "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">dependencies"
                        "</span></a>(e.g. Bio-FastParsers) of HmmCleaner are not installed, "
                        "click <span style=\"color:red\">Show log</span> to see details! <br> You can install HmmCleaner following this " \
                   "<a href=\"%s\">" \
                   "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">instruction</a>." \
                   "</span>"%url)
                else:
                    list_commands = re.findall(r"Command: (.+)\n", log)
                    last_cmd = list_commands[-1] if list_commands else ""
                    self.HmmCleaner_exception.emit(
                        "HmmCleaner executes failed, click <span style=\"color:red\">Show log</span> to see details! "
                        "You can also copy this command to terminal to debug: %s"%last_cmd)
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (
                str(time_start), str(time_end),
                self.time_used)
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(
                    self.description + "\n\nIf you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n"
                                       "If you use HmmCleaner, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
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
        self.HmmCleaner_settings.setValue('size', self.size())
        # self.HmmCleaner_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.HmmCleaner_settings.setValue(name, index)
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.HmmCleaner_settings.setValue(name, state)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.HmmCleaner_settings.setValue(name, float_)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.HmmCleaner_settings.value('size', QSize(490, 380)))
        self.factory.centerWindow(self)
        # self.move(self.HmmCleaner_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox_6":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.HmmCleaner_settings.value(name, "0")
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
                    index = self.HmmCleaner_settings.value(name, "0")
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
                value = self.HmmCleaner_settings.value(
                    name, "no setting")  # get stored value from registry
                if value != "no setting":
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QDoubleSpinBox):
                ini_float_ = obj.value()
                float_ = self.HmmCleaner_settings.value(name, ini_float_)
                obj.setValue(float(float_))

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
        self.closeSig.emit("HmmCleaner", self.fetchWorkflowSetting())
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
            self.ui_closeSig.emit("HmmCleaner")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            reply = QMessageBox.question(
                self,
                "HmmCleaner",
                "<p style='line-height:25px; height:25px'>HmmCleaner is still running, terminate it?</p>",
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
                self.input(files)
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
        return super(HmmCleaner, self).eventFilter(obj, event)  # 0

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of HmmCleaner:")
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
            with open(self.exportPath + os.sep + "PhyloSuite_HmmCleaner.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "HmmCleaner", "log", "text Format(*.txt)")
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
                                             initializer=pool_init, initargs=(self.queue,)) #\
                # if platform.system().lower() == "windows" else multiprocessing.Pool(processes=thread,
                #                                                         initializer=pool_init, initargs=(self.queue,))
            # # Check for progress periodically
            self.timer = QTimer()
            self.timer.timeout.connect(self.updateProcess)
            self.timer.start(1)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

    def judgeCmdText(self):
        text = self.textEdit_cmd.toPlainText()
        if " $alignment$" not in text:
            QMessageBox.information(
                self,
                "HmmCleaner",
                "<p style='line-height:25px; height:25px'>\"$alignment$\" cannot be changed!</p>")
            self.textEdit_cmd.undo()

    def fetchCommands(self):
        if self.isFileIn():
            self.interrupt = False
            self.error_has_shown = False
            self.dict_args = {}
            self.dict_args["workPath"] = self.workPath
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath + \
                                                      os.sep + "HmmCleaner_results" + os.sep + self.output_dir_name)
            self.dict_args["exportPath"] = self.exportPath
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                # 提醒是否删除旧结果，如果用户取消，就不执行
                return
            costs = "\"%.2f\" \"%.2f\" \"%.2f\" \"%.2f\""%(self.doubleSpinBox.value(), self.doubleSpinBox_2.value(),
                                                           self.doubleSpinBox_3.value(), self.doubleSpinBox_4.value())
            self.dict_args["costs"] = " -costs %s"%costs if costs != '"-0.15" "-0.08" "0.15" "0.45"' else ""
            self.dict_args["noX"] = " --noX" if self.checkBox_5.isChecked() else ""
            self.dict_args["specificity"] = " --specificity" if self.checkBox.isChecked() else ""
            self.dict_args["large"] = " --large" if self.checkBox_2.isChecked() else ""
            self.dict_args["log_only"] = " --log_only" if self.checkBox_3.isChecked() else ""
            self.dict_args["ali"] = " --ali" if self.checkBox_4.isChecked() else ""
            self.dict_args["changeID"] = " --changeID" if self.checkBox_6.isChecked() else ""
            self.dict_args["profile"] = " -profile=%s"%self.comboBox_3.currentText()
            self.dict_args["symfrac"] = " -symfrac %s" %self.doubleSpinBox_6.value() if self.doubleSpinBox_6.value() != 0.50 else ""
            self.dict_args["verbosity"] = " -v=%s"%self.comboBox_5.currentText() if self.comboBox_5.currentText() != "0" else ""
            self.dict_args["perl"] = "\"%s\" "%self.perl if self.HmmCleanerPath != "HmmCleaner.pl" else "" #如果是用的环境变量的脚本，就不用perl
            self.dict_args["HmmCleaner"] = self.HmmCleanerPath
            ##输入文件
            self.dict_args["inputFiles"] = []
            try:
                for aln_file in self.comboBox_4.fetchListsText():
                    with open(aln_file, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    copy_path = self.exportPath + os.sep + os.path.basename(aln_file)
                    with open(copy_path, "w", encoding="utf-8") as f1:
                        f1.write(content.replace("\r\n", "\n"))
                    self.dict_args["inputFiles"].append(copy_path)
            except:
                QMessageBox.information(
                    self,
                    "HmmCleaner",
                    "<p style='line-height:25px; height:25px'>File copying failed, please check your input files!</p>")
            command = "{perl}\"{HmmCleaner}\" $alignment${costs}{noX}{specificity}{large}{log_only}{ali}" \
                      "{changeID}{profile}{symfrac}{verbosity}".format(**self.dict_args)
            self.reference = "Di Franco A, Poujol R, Baurain D, Philippe H. 2019. Evaluating the usefulness of " \
                             "alignment filtering methods to reduce the impact of errors on evolutionary " \
                             "inferences. BMC Evol Biol. 19: 21. doi: 10.1186/s12862-019-1350-2."
            cmd_used = "{costs}{specificity}{large}{log_only}{ali}{changeID}{profile}{symfrac}".format(**self.dict_args).strip()
            self.description = "Low similarity segments within the alignment were removed with HmmCleaner (Di Franco et al., 2019) using \"%s\" command."%cmd_used
            self.textEdit_log.clear()  # 清空
            return command
        else:
            QMessageBox.critical(
                self,
                "HmmCleaner",
                "<p style='line-height:25px; height:25px'>Please input files first!</p>")

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
            self.on_pushButton_2_clicked(quiet=True) #杀掉进程
            self.HmmCleaner_exception.emit(
                "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!")
            self.error_has_shown = True
        elif info[0] == "popen finished":
            if info[1] in self.list_pids:
                self.list_pids.remove(info[1])

    def popup_HmmCleaner_exception(self, text):
        if not self.error_has_shown:
            QMessageBox.critical(
                self,
                "HmmCleaner",
                "<p style='line-height:25px; height:25px'>%s</p>" % text)
            if "Show log" in text:
                self.on_pushButton_9_clicked()

    def popupAliWarning(self, bool_):
        if bool_:
            QMessageBox.warning(
                self,
                "HmmCleaner",
                "<p style='line-height:25px; height:25px'>\"Ali\" format cannot be used by the downstream programs "
                "(e.g. IQ-TREE), please uncheck it if you are going to use this result for other functions.</p>")

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("HmmCleaner", self.workPath, self.auto_popSig, self)

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

    def fetchWorkflowSetting(self):
        '''* Alignment Mode
          * Code table(if codon mode)
          * strategy
          * export format'''
        settings = '''<p class="title">***HmmCleaner***</p>'''
        c1 = self.doubleSpinBox.value()
        c2 = self.doubleSpinBox_2.value()
        c3 = self.doubleSpinBox_3.value()
        c4 = self.doubleSpinBox_4.value()
        settings += '<p>costs: \"<a href="self.HmmCleaner_exe doubleSpinBox.setFocus() doubleSpinBox.selectAll() ' \
                    'factory.highlightWidgets(x.doubleSpinBox)">%s</a>\" ' \
                    '\"<a href="self.HmmCleaner_exe doubleSpinBox_2.setFocus() doubleSpinBox_2.selectAll() ' \
                    'factory.highlightWidgets(x.doubleSpinBox_2)">%s</a>\" ' \
                    '\"<a href="self.HmmCleaner_exe doubleSpinBox_3.setFocus() doubleSpinBox_3.selectAll() ' \
                    'factory.highlightWidgets(x.doubleSpinBox_3)">%s</a>\" ' \
                    '\"<a href="self.HmmCleaner_exe doubleSpinBox_4.setFocus() doubleSpinBox_4.selectAll() ' \
                    'factory.highlightWidgets(x.doubleSpinBox_4)">%s</a>\"</p>' % (c1, c2, c3, c4)
        verbosity = self.comboBox_5.currentText()
        settings += '<p>verbosity: <a href="self.HmmCleaner_exe comboBox_5.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_5)">%s</a></p>' % verbosity
        profile = self.comboBox_3.currentText()
        settings += '<p>profile: <a href="self.HmmCleaner_exe comboBox_3.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_3)">%s</a></p>' % profile
        thread = self.comboBox_6.currentText()
        settings += '<p>Thread: <a href="self.HmmCleaner_exe comboBox_6.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_6)">%s</a></p>' % thread
        specificity = "Yes" if self.checkBox.isChecked() else "No"
        settings += '<p>specificity: <a href="self.HmmCleaner_exe' \
                    ' factory.highlightWidgets(x.checkBox)">%s</a></p>' % specificity
        large = "Yes" if self.checkBox_2.isChecked() else "No"
        settings += '<p>large: <a href="self.HmmCleaner_exe' \
                    ' factory.highlightWidgets(x.checkBox_2)">%s</a></p>' % large
        changeID = "Yes" if self.checkBox_6.isChecked() else "No"
        settings += '<p>changeID: <a href="self.HmmCleaner_exe' \
                    ' factory.highlightWidgets(x.checkBox_6)">%s</a></p>' % changeID
        noX = "Yes" if self.checkBox_5.isChecked() else "No"
        settings += '<p>noX: <a href="self.HmmCleaner_exe' \
                    ' factory.highlightWidgets(x.checkBox_5)">%s</a></p>' % noX
        return settings

    def isFileIn(self):
        return self.comboBox_4.count()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = HmmCleaner()
    ui.show()
    sys.exit(app.exec_())