#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import glob
import re

import multiprocessing
import shutil
import signal
from collections import OrderedDict

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from uifiles.Ui_muscle import Ui_MUSCLE
from src.factory import Factory, WorkThread
import inspect
import os
import sys
import traceback
import subprocess
import platform
from multiprocessing.pool import ApplyResult

from src.Lg_mafft import CodonAlign
from src.Lg_seqViewer import Seq_viewer


factory = Factory()
def run(command, file, log_file_path):
    popen = factory.init_popen(command, stdin_=True)
    run.queue.put(("popen", popen.pid))
    is_error = False
    # 存log文件
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(command + "\n")
        run.queue.put(("log", "%sCommands%s\n%s\n%s" % ("=" * 45, "=" * 45, command, "=" * 98)))
        fileBase = os.path.basename(file)
        # rgx_init_dist = re.compile(
        #     r"compute initial pairwise distances", re.I)  #3
        # rgx_fst_align_with_tree = re.compile(
        #     r"compute first alignment with guide tree", re.I) # 10
        # rgx_fst_align_score = re.compile(
        #     r"first alignment score", re.I) # 25 OR 95
        # rgx_start_refine = re.compile(
        #     r"^start refining", re.I) # 判断一下接下来就是rgx_refine_process了,# 25 OR 95
        # rgx_refine_process = re.compile(r"([.+-]+)\n") # 25 + 70 * (sum-+)/sum
        # rgx_end = re.compile("PROGRAM HAS FINISHED SUCCESSFULLY", re.I) # 100
        while True:
            try:
                out_line = popen.stdout.readline().decode("utf-8", errors='ignore')
            except UnicodeDecodeError:
                out_line = popen.stdout.readline().decode("gbk", errors='ignore')
            if out_line == "" and popen.poll() is not None:
                break
            log_file.write(out_line)
            if re.search(r"\S+", out_line):
                run.queue.put(("log", fileBase + " --- " + out_line.strip()))
            if re.search(r"(?i)ERROR", out_line):
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


class MUSCLE(QDialog, Ui_MUSCLE, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    MUSCLE_exception = pyqtSignal(str)
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
            focusSig=None,
            workflow=False,
            MUSCLEEXE=None,
            autoInputs=None,
            clearFolderSig=None,
            parent=None):
        super(MUSCLE, self).__init__(parent)
        self.parent = parent
        self.function_name = "MUSCLE"
        self.workflow = workflow
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.MUSCLEEXE = MUSCLEEXE
        self.autoInputs = autoInputs
        self.clearFolderSig = clearFolderSig
        self.setupUi(self)
        # 保存设置
        if not workflow:
            self.MUSCLE_settings = QSettings(
                self.thisPath + '/settings/MUSCLE_settings.ini', QSettings.IniFormat)
        else:
            self.MUSCLE_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.MUSCLE_settings.beginGroup("Workflow")
            self.MUSCLE_settings.beginGroup("temporary")
            self.MUSCLE_settings.beginGroup('MUSCLE')
        # File only, no fallback to registry or or.
        self.MUSCLE_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        self.qss_file = self.factory.set_qss(self)
        # 恢复用户的设置
        self.guiRestore()
        # 判断程序的版本
        self.version = ""
        version_worker = WorkThread(
            lambda : self.factory.get_version("MUSCLE", self),
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
        self.comboBox_3.currentTextChanged.connect(self.cotrol_code_table)
        self.cotrol_code_table(self.comboBox_3.currentText())
        self.checkBox.toggled.connect(lambda bool_: self.spinBox_2.setValue(4) if bool_ else self.spinBox_2.setValue(self.spinBox_2.value()))
        self.checkBox_2.toggled.connect(lambda bool_: self.spinBox_2.setValue(100) if bool_ else self.spinBox_2.setValue(self.spinBox_2.value()))
        self.MUSCLE_exception.connect(self.popup_MUSCLE_exception)
        self.checkBox_6.toggled.connect(self.resolveConflict)
        self.checkBox_2.toggled.connect(self.resolveConflict)
        self.checkBox.toggled.connect(self.resolveConflict)
        self.checkBox_7.toggled.connect(self.resolveConflict)
        self.log_gui = self.gui4Log()
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
            self.queue = multiprocessing.Queue() if platform.system().lower() == "windows" else multiprocessing.Manager().Queue()
            thread = int(self.comboBox_6.currentText())
            thread = thread if len(self.dict_args["filenames"]) > thread else len(self.dict_args["filenames"])
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
            self.on_pushButton_9_clicked()

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
    def on_pushButton_9_clicked(self):
        """
        show log
        """
        self.log_gui.show()

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
                    "<p style='line-height:25px; height:25px'>MUSCLE is still running, terminate it?</p>",
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
                        "MUSCLE",
                        "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        [self.progressBar],
                        "except",
                        self.exportPath,
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
                    self.exportPath,
                    self.qss_file,
                    self])
            def align_seqs(seq_files, exportPath=None):
                exportPath = exportPath if exportPath else self.exportPath
                # 不要_muscle是为了back_trans能执行
                async_results = [self.pool.apply_async(run, args=(self.command.replace("$inputFile$",
                    file).replace("$ouputFile$",
                    f"{exportPath}{os.sep}{self.factory.get_file_name_base(file)}{self.dict_args['suffix'] if not exportPath else ''}.fas"),
                    file, f"{self.exportPath}{os.sep}{self.factory.get_file_name_base(file)}.log")) for
                      num, file in enumerate(seq_files)]
                self.pool.close()  # 关闭进程池，防止进一步操作。如果所有操作持续挂起，它们将在工作进程终止前完成
                map(ApplyResult.wait, async_results)
                lst_results = [r.get() for r in async_results]
                self.pool.join()  # 等待所有进程结束
            runState = "Normal"
            if self.dict_args["codon mode"]:
                self.factory.creat_dir(self.dict_args["vessel"])
                self.factory.creat_dir(self.dict_args["vessel_aaseq"])
                self.factory.creat_dir(self.dict_args["vessel_aalign"])
                # 翻译氨基酸，保存AA文件，映射
                codonAlign = CodonAlign(**self.dict_args)  # 翻译占10%
                if codonAlign.DictInterstop:
                    codonAlign.DictInterstop["code table"] = self.dict_args[
                        "codon"]  # 记录code table信息
                    reply = QMetaObject.invokeMethod(self, "popupInterStopCodon",
                        Qt.BlockingQueuedConnection, Q_RETURN_ARG(
                            bool),
                        Q_ARG(OrderedDict, codonAlign.DictInterstop))
                    if reply:
                        # 如果用户选择了查看终止密码子
                        runState = "internal stop codon"
                if runState == "Normal":
                    # 比对
                    list_files = [f"{self.dict_args['vessel_aaseq']}{os.sep}{aa_file}" for
                                  aa_file in os.listdir(self.dict_args["vessel_aaseq"])]
                    align_seqs(list_files, exportPath=self.dict_args["vessel_aalign"])
                    # 避免关闭窗口了还继续进行下面的
                    if not self.interrupt:
                        self.mafft_output_files = codonAlign.back_trans(
                        )  # 生成codon文件,占10%
                    # 删除文件夹
                    self.clearFolderSig.emit(self.dict_args["vessel"])
            else:
                align_seqs(self.dict_args["filenames"])
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (
            str(time_start), str(time_end),
            self.time_used)
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(
                    self.description + f"\n\nIf you use PhyloSuite v2, please cite:\n{self.factory.get_PS_citation()}\n\n"
                                       "If you use MUSCLE, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
            if (not self.interrupt) and ((runState != "internal stop codon")):
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
                    self.exportPath,
                    self.qss_file,
                    self])
            self.pool = None
            self.interrupt = False

    def guiSave(self):
        # Save geometry
        self.MUSCLE_settings.setValue('size', self.size())
        # self.MUSCLE_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.MUSCLE_settings.setValue(name, index)
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.MUSCLE_settings.setValue(name, state)
            elif isinstance(obj, QSpinBox):
                value = obj.value()
                self.MUSCLE_settings.setValue(name, value)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.factory.judgeWindowSize(self.MUSCLE_settings, 826, 590))
        if platform.system().lower() != "linux":
            self.factory.centerWindow(self)
        # self.move(self.MUSCLE_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                obj.installEventFilter(self)  # 安装事件过滤器，为了取消滚轮事件
                if name in ["comboBox_6", "comboBox_5"]:
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.MUSCLE_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(list_cpu):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2==0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.MUSCLE_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(allItems):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2==0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
            if isinstance(obj, QCheckBox):
                value = self.MUSCLE_settings.value(
                    name, "no setting")  # get stored value from registry
                if value!="no setting":
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QSpinBox):
                obj.installEventFilter(self)  # 安装事件过滤器，为了取消滚轮事件
                ini_value = obj.value()
                value = self.MUSCLE_settings.value(name, ini_value)
                obj.setValue(int(value))

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
        # self.closeSig.emit("MUSCLE", self.fetchWorkflowSetting())
        # 断开showSig和closeSig的槽函数连接
        try: self.showSig.disconnect()
        except: pass
        try: self.closeSig.disconnect()
        except: pass
        self.on_pushButton_2_clicked()

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
        if (isinstance(obj, QDoubleSpinBox) or isinstance(obj, QSpinBox) or isinstance(obj, QComboBox)) and event.type()==QEvent.Wheel:
            return True  # 过滤掉滚轮事件
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(MUSCLE, self).eventFilter(obj, event)  # 0

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of MUSCLE:")
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
            with open(self.exportPath + os.sep + "PhyloSuite_MUSCLE.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "MUSCLE", "log", "text Format(*.txt)")
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

    def fetchCommands(self):
        if self.isFileIn():
            self.interrupt = False
            list_cmds = [f"{self.MUSCLEEXE}"]
            algorithm = self.comboBox_3.currentText().split()[0]
            list_cmds.append(f"-{algorithm.split('-')[0]} $inputFile$")
            if self.checkBox_6.isEnabled() and self.checkBox_6.isChecked():
                perturb = self.spinBox.value()
                list_cmds.append(f"-perturb {perturb}")
            if self.checkBox_3.isEnabled() and self.checkBox_3.isChecked():
                replicates = self.spinBox_2.value()
                list_cmds.append(f"-replicates {replicates}")
            if self.checkBox_4.isEnabled() and self.checkBox_4.isChecked():
                consiters = self.spinBox_3.value()
                list_cmds.append(f"-consiters {consiters}")
            if self.checkBox_5.isEnabled() and self.checkBox_5.isChecked():
                refineiters = self.spinBox_4.value()
                list_cmds.append(f"-refineiters {refineiters}")
            if self.checkBox.isEnabled() and self.checkBox.isChecked():
                list_cmds.append(f"-stratified")
            if self.checkBox_2.isEnabled() and self.checkBox_2.isChecked():
                list_cmds.append(f"-diversified")
            if self.checkBox_7.isEnabled() and self.checkBox_7.isChecked():
                list_cmds.append(F"-perm {self.comboBox_2.currentText()}")
            list_cmds.append(f"-threads {self.comboBox_5.currentText()}")
            list_cmds.append("-output $ouputFile$")
            self.reference = "Edgar RC. " \
                             "Muscle5: High-accuracy alignment ensembles enable unbiased assessments of sequence homology and phylogeny. " \
                             "Nature Communications. " \
                             "13.1 (2022): 6968. doi: 10.1038/s41467-022-34630-w."
            algorithm_name = re.search(r'\w+ algorithm', self.comboBox_3.currentText()).group()
            self.description = f"The sequences were aligned using {algorithm_name}" \
                               f" of MUSCLE v{self.version} (Edgar RC., 2022). "

            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath + \
                                                     os.sep + "MUSCLE_results" + os.sep + self.output_dir_name)
            self.dict_args = {}
            self.dict_args["suffix"] = "_muscle"
            self.dict_args["filenames"] = self.comboBox_4.fetchListsText()
            if self.comboBox_9.isEnabled():
                # 密码子比对模式
                self.dict_args["workPath"] = self.workPath
                self.dict_args["exportPath"] = self.exportPath
                vessel = f"{self.dict_args['exportPath']}/vessel"
                self.factory.remove_dir_directly(vessel, removeRoot=True)
                vessel_aaseq = f"{vessel}/AA_sequence"
                vessel_aalign = f"{vessel}/AA_alignments"
                self.dict_args["vessel"] = vessel
                self.dict_args["vessel_aaseq"] = vessel_aaseq
                self.dict_args["vessel_aalign"] = vessel_aalign
                code = str(self.comboBox_9.currentText()).split(" ")[0]
                self.dict_args["codon"] = code
                # self.dict_args["ignore_prog"] = True
                self.dict_args["codon mode"] = True
            else:
                self.dict_args["codon mode"] = False
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                # 提醒是否删除旧结果，如果用户取消，就不执行
                return
            command = " ".join(list_cmds)
            self.textEdit_log.clear()  # 清空
            return command
        else:
            QMessageBox.critical(
                self,
                "MUSCLE",
                "<p style='line-height:25px; height:25px'>Please input files first!</p>")

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

    def run_with_CMD(self, cmd):
        self.command = cmd
        if self.command:
            self.interrupt = False
            self.list_pids = []
            self.queue = multiprocessing.Queue() if platform.system().lower() == "windows" else multiprocessing.Manager().Queue()
            thread = int(self.comboBox_6.currentText())
            thread = thread if len(self.dict_args["filenames"]) > thread else len(self.dict_args["filenames"])
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
                "MUSCLE",
                "<p style='line-height:25px; height:25px'>\"%s\" cannot be changed!</p>"%judge_text)
            self.textEdit_cmd.undo()

    def updateProcess(self):
        if self.queue.empty(): return
        info = self.queue.get()
        if info[0] == "log":
            message = info[1]
            self.logGuiSig.emit(message)
        elif info[0] == "prog":
            if not self.interrupt:
                self.progressSig.emit(99999)
        elif info[0] == "popen":
            self.list_pids.append(info[1])
        elif info[0] == "popen finished":
            if info[1] in self.list_pids:
                self.list_pids.remove(info[1])
        elif info[0] == "error":
            self.on_pushButton_2_clicked(quiet=True)  # 杀掉进程
            self.MUSCLE_exception.emit(
                "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!")
            self.error_has_shown = True

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "pool") and self.pool and not self.interrupt

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("MUSCLE", self.workPath, self.auto_popSig, self)

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

    def isFileIn(self):
        return self.comboBox_4.count()

    def popup_MUSCLE_exception(self, text):
        QMessageBox.critical(
            self,
            "MUSCLE",
            "<p style='line-height:25px; height:25px'>%s</p>" % text)
        if "Show log" in text:
            self.on_pushButton_9_clicked()

    def cotrol_code_table(self, text):
        if text in ["align-codon -- Align sequences using the PPP algorithm in codon mode",
                    "super5-codon -- Align large datasets using the Super5 algorithm in codon mode"]:
            self.comboBox_9.setEnabled(True)
            self.label_22.setEnabled(True)
        else:
            self.comboBox_9.setEnabled(False)
            self.label_22.setEnabled(False)
        if text in ["super5 -- Align large datasets using the Super5 algorithm",
                    "super5-codon -- Align large datasets using the Super5 algorithm in codon mode"]:
            self.checkBox.setEnabled(False)
            self.checkBox_2.setEnabled(False)
            self.checkBox_3.setEnabled(False)
        else:
            self.checkBox.setEnabled(True)
            self.checkBox_2.setEnabled(True)
            self.checkBox_3.setEnabled(True)


    @pyqtSlot(OrderedDict, result=bool)
    def popupInterStopCodon(self, dictInterStop):
        ## 存为文件
        def save2file(dictInterStop):
            list_ = [["File", "Species", "Site"]]
            # dictInterStop.pop("code table")
            for file, list_codons in dictInterStop.items():
                if file=="code table":
                    continue
                for species, codon_site in list_codons:
                    list_.append([os.path.basename(file), species, f"{codon_site + 1}-{codon_site + 4}"])
            with open(f"{self.exportPath}{os.sep}internal_stop_codons.tsv", "w") as f:
                f.write("\n".join(["\t".join(i) for i in list_]))

        saveFileWorker = WorkThread(lambda: save2file(dictInterStop), parent=self)
        saveFileWorker.start()
        # saveFileWorker.finished.connect(lambda : [])
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "<p style='line-height:25px; height:25px'>Internal stop codons found, view them? "
            "(also see \"internal_stop_codons.tsv\" file)</p>",
            QMessageBox.Yes,
            QMessageBox.Ignore)
        if reply==QMessageBox.Yes:
            self.seqViewer = Seq_viewer(
                self.workPath, dictInterStop, parent=self)
            # 添加最大化按钮
            self.seqViewer.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            self.seqViewer.show()
            return True
        else:
            return False

    def resolveConflict(self):
        perm = self.checkBox_7.isChecked()
        perturb = self.checkBox_6.isChecked()
        stratified = self.checkBox.isChecked()
        diversified = self.checkBox_2.isChecked()
        if (stratified or diversified) and (perm or perturb):
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>Cannot set -perm or -perturb with -stratified or -diversified!</p>")
            self.checkBox_6.setChecked(False)
            self.checkBox_7.setChecked(False)
        if stratified and diversified:
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>Cannot set both -stratified and -diversified!</p>")
            self.checkBox_2.setChecked(False)


if __name__ == "__main__":
    import cgitb
    sys.excepthook = cgitb.Hook(1, None, 5, sys.stderr, 'text')
    app = QApplication(sys.argv)
    ui = MUSCLE()
    ui.show()
    sys.exit(app.exec_())