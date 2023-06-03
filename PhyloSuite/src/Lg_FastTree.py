#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 自己调整好一个size，然后再guirestore恢复一下

'''
http://www.microbesonline.org/fasttree
CAT/Gamma20 Likelihoods section
CAT/Gamma20 适用于大于50条的序列，小于50条序列建议用

'''

import datetime
import glob
import re

import multiprocessing
import shutil
import signal

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.Lg_settings import Setting
from uifiles.Ui_FastTree import Ui_FastTree
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
    fileName = os.path.splitext(fileBase)[0]
    work_dir = f"{dict_args['exportPath']}/{fileName}"
    os.makedirs(work_dir, exist_ok=True)
    os.chdir(work_dir)
    shutil.copy(file, work_dir)
    # 判断是否需要选模型
    if dict_args["model"] == "AUTO":
        MF_command = f"\"{dict_args['MF_path']}\" -s \"{fileBase}\" " \
                     f"-mset JTT,WAG,LG -mrate G -nt AUTO -pre ModelFinder"
        MF_popen = Factory().init_popen(MF_command)
        stdout = Factory().getSTDOUT(MF_popen)
        # 找到最优模型
        model_file = glob.glob(f"{work_dir}/*.iqtree")
        if model_file:
            model_file = model_file[0]
        else:
            return
        f = Factory().read_file(model_file)
        content = f.read()
        f.close()
        rgx_model = re.compile(r"Best-fit model according to.+?\: (.+)")
        best_model = rgx_model.search(content).group(1)
        model_split = best_model.split("+")
        model = model_split[0]
        model_cmd = dict_args["dict_model"][model]
        command = command.replace("$model$", model_cmd)
    else:
        MF_command = ""
    # 建树
    if "constraint" in dict_args:
        shutil.copy(dict_args["constraint"], work_dir)
    # command += f" -log \"{work_dir}/FastTree.log\" -out \"{work_dir}/{dict_args['tree_name']}\" " \
    #            f"\"{work_dir}/{fileBase}\" "
    command = command.replace("$alignment$", f"\"{fileBase}\"") # f"\"{work_dir}/{fileBase}\"")
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
    with open(fileName + "_run.log", "a", encoding="utf-8") as log_file:
        commands_des = "%sCommands%s\n%s\n%s" % ("=" * 45, "=" * 45,
                                                 f"cd \"{os.path.normpath(dict_args['exportPath'])}\"\n"
                                                 f"{MF_command}\n"
                                                 f"{command}", "=" * 98)
        run.queue.put(("log", commands_des))
        log_file.write(commands_des + "\n")
        is_error = False
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

class FastTree(QDialog, Ui_FastTree, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    FastTree_exception = pyqtSignal(str)
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    # 用于输入文件后判断用
    ui_closeSig = pyqtSignal(str)
    # 用于flowchart自动popup combobox等操作
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)
    failed_file = pyqtSignal(list)

    def __init__(
            self,
            input_MSA=None,
            model=None,
            workPath=None,
            focusSig=None,
            FastTreePath=None,
            workflow=None,
            parent=None):
        super(FastTree, self).__init__(parent)
        self.parent = parent
        self.function_name = "FastTree"
        self.input_MSA = input_MSA
        self.model = model
        self.workflow = workflow
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.FastTreePath = FastTreePath
        self.setupUi(self)
        # 保存设置
        if not workflow:
            self.FastTree_settings = QSettings(
                self.thisPath + '/settings/FastTree_settings.ini', QSettings.IniFormat)
        else:
            self.FastTree_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.FastTree_settings.beginGroup("Workflow")
            self.FastTree_settings.beginGroup("temporary")
            self.FastTree_settings.beginGroup('FastTree')
        # File only, no fallback to registry or or.
        self.FastTree_settings.setFallbacksEnabled(False)
        # 恢复用户的设置
        self.guiRestore()
        # 判断程序的版本
        self.version = ""
        version_worker = WorkThread(
            lambda : self.factory.get_version("FastTree", self),
            parent=self)
        version_worker.start()
        # 自动导入
        self.workflow_input(input_MSA, model)
        # 开始装载样式表
        # with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
        #     self.qss_file = f.read()
        # self.setStyleSheet(self.qss_file)
        self.qss_file = self.factory.set_qss(self)
        self.interrupt = False
        # 信号槽
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.logGuiSig.connect(self.addText2Log)
        self.lineEdit_2.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        self.comboBox_11.installEventFilter(self)
        self.lineEdit_2.installEventFilter(self)
        self.comboBox_11.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        self.log_gui = self.gui4Log()
        self.FastTree_exception.connect(self.popup_FastTree_exception)
        self.comboBox.currentTextChanged.connect(self.control_boot)
        self.failed_file.connect(self.popupWarning_with_details)
        self.control_boot(self.comboBox.currentText())
        self.comboBox_7.currentTextChanged.connect(self.judgeIQTREEinstalled)
        self.judgeIQTREEinstalled(self.comboBox_7.currentText())
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
        self.label.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
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
            self.input_files = self.comboBox_11.fetchListsText()
            self.list_pids = []
            self.queue = multiprocessing.Queue()
            thread = int(self.comboBox_6.currentText())
            thread = thread if len(self.input_files) > thread else len(self.input_files)
            thread = 1 if not self.input_files else thread  # compare的情况
            self.pool = multiprocessing.get_context("spawn").Pool(processes=thread,
                                                                  initializer=pool_init, initargs=(self.queue,)) #\
                # if platform.system().lower() == "windows" else multiprocessing.Pool(processes=thread,
                #                                                                    initializer=pool_init, initargs=(self.queue,))
            # Check for progress periodically
            self.timer = QTimer()
            self.timer.timeout.connect(self.updateProcess)
            self.timer.start(1)
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
        alignment file
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input alignment file")
        if fileNames[0]:
            self.input(fileNames[0])
    @pyqtSlot()
    def on_pushButton_22_clicked(self):
        """
        constraint file
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input constraint tree file")
        file = fileName[0]
        if file:
            self.input_single_file(file, self.lineEdit_2)

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
                    "<p style='line-height:25px; height:25px'>FastTree is still running, terminate it?</p>",
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
                        "FastTree",
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
            ## 切换到当前路径
            os.chdir(self.exportPath)
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
                             file in self.input_files]
            self.totalFileNum = len(self.input_files)
            self.finishedFileNum = 0 #进度条用
            self.pool.close()  # 关闭进程池，防止进一步操作。如果所有操作持续挂起，它们将在工作进程终止前完成
            map(ApplyResult.wait, async_results)
            lst_results = [r.get() for r in async_results]
            # 判断是否运行成功
            error_files = []
            trees = []
            for file in os.listdir(self.exportPath):
                if not os.path.isfile(file):
                    target_tree = f"{self.exportPath}/{file}/{self.output_fast_tree}"
                    if (not os.path.exists(target_tree)) or (os.stat(target_tree).st_size == 0):
                        error_files.append(file)
                    else:
                        trees.append(target_tree)
            # 存所有基因树
            all_tree_contents = []
            for tree in trees:
                with open(tree) as f:
                    all_tree_contents.append(f.read())
            with open(f"{self.exportPath}/all_gene_trees.nwk", "w") as f:
                f.write("".join(all_tree_contents))
            # 找出所有用到的模型

            # 如果有空文件就报错
            has_error = False
            if error_files:
                # log_only不管
                has_error = True
                self.failed_file.emit(error_files)
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (
                str(time_start), str(time_end),
                self.time_used)
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(
                    self.description + f"\n\nIf you use PhyloSuite v1.2.3, please cite:\n{self.factory.get_PS_citation()}\n\n"
                                       "If you use FastTree, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
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
        self.FastTree_settings.setValue('size', self.size())
        # self.FastTree_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.FastTree_settings.setValue(name, index)
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.FastTree_settings.setValue(name, state)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.FastTree_settings.setValue(name, float_)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.FastTree_settings.value('size', QSize(1000, 750)))
        self.factory.centerWindow(self)
        # self.move(self.FastTree_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox_6":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.FastTree_settings.value(name, "0")
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
                elif name == "comboBox_7":
                    ini_models = ["***Nucleotide***", "GTR",
                                  "***Protein***", "AUTO", "JTT",  "LG", "WAG"]
                    index = self.FastTree_settings.value(name, "1")
                    model = obj.model()
                    for num, i in enumerate(ini_models):
                        item = QStandardItem(i)
                        # 背景颜色
                        if "*" in i:
                            item.setBackground(QColor(245, 105, 87))
                            item.setForeground(QColor("white"))
                        elif num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
                    obj.model().item(0).setSelectable(False)
                    obj.model().item(2).setSelectable(False)
                elif name != "comboBox_11":
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.FastTree_settings.value(name, "0")
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
                value = self.FastTree_settings.value(
                    name, obj.isChecked())  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QDoubleSpinBox):
                ini_float_ = obj.value()
                float_ = self.FastTree_settings.value(name, ini_float_)
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
        # self.closeSig.emit("FastTree", self.fetchWorkflowSetting())
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
            self.ui_closeSig.emit("FastTree")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            reply = QMessageBox.question(
                self,
                "FastTree",
                "<p style='line-height:25px; height:25px'>FastTree is still running, terminate it?</p>",
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
        if isinstance(obj, QComboBox) or isinstance(obj, QLineEdit):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                if isinstance(obj, QComboBox):
                    self.input(files)
                elif isinstance(obj, QLineEdit):
                    self.input_single_file(files, obj)
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
        return super(FastTree, self).eventFilter(obj, event)  # 0

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of FastTree:")
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
            with open(self.exportPath + os.sep + "PhyloSuite_FastTree.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "FastTree", "log", "text Format(*.txt)")
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
            self.comboBox_11.refreshInputs(list_items)
        else:
            self.comboBox_11.refreshInputs([])

    def input_single_file(self, file=None, lineedit=None):
        if type(file) == list:
            file = file[0]
        if file:
            base = os.path.basename(file)
            lineedit.setText(base)
            lineedit.setToolTip(file)
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
            self.input_files = self.comboBox_11.fetchListsText()
            self.list_pids = []
            self.queue = multiprocessing.Queue()
            thread = int(self.comboBox_6.currentText())
            thread = thread if len(self.input_files) > thread else len(self.input_files)
            thread = 1 if not self.input_files else thread # compare的情况
            self.pool = multiprocessing.get_context("spawn").Pool(processes=thread,
                                             initializer=pool_init, initargs=(self.queue,)) #\
                        # if platform.system().lower() == "windows" else multiprocessing.Pool(processes=thread,
                        #                                                                    initializer=pool_init, initargs=(self.queue,))
            # # Check for progress periodically
            self.timer = QTimer()
            self.timer.timeout.connect(self.updateProcess)
            self.timer.start(1)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
            self.on_pushButton_9_clicked()

    def judgeCmdText(self):
        text = self.textEdit_cmd.toPlainText()
        if " $alignment$" not in text:
            QMessageBox.information(
                self,
                "FastTree",
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
                                                      os.sep + "FastTree_results" + os.sep + self.output_dir_name)
            self.dict_args["exportPath"] = self.exportPath
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                # 提醒是否删除旧结果，如果用户取消，就不执行
                return
            list_command = [f"\"{self.FastTreePath}\""]
            # 序列类型
            self.dict_args["seq_type"] = self.comboBox_4.currentText()
            if self.dict_args["seq_type"] == "Nucleotide":
                list_command.append("-nt")
            # constraint
            if self.lineEdit_2.text():
                # shutil.copy(self.lineEdit_2.toolTip(), self.exportPath) # 在run里面copy
                self.dict_args["constraint"] = self.lineEdit_2.toolTip()
                list_command.append(f"-constraints \"{self.lineEdit_2.text()}\"")
            # model
            self.dict_args["dict_model"] = {"LG": "-lg", "WAG": "-wag",
                     "GTR": "-gtr", "JTT": ""}
            self.dict_args["model"] = self.comboBox_7.currentText()
            if self.dict_args["model"] != "AUTO":
                list_command.append(self.dict_args["dict_model"][self.dict_args["model"]])
            else:
                list_command.append("$model$")
                self.dict_args["MF_path"] = self.factory.programIsValid("iq-tree", mode="tool")
            # gamma
            if self.checkBox_3.isChecked():
                list_command.append("-gamma")
            # rate category
            if self.checkBox.isChecked():
                list_command.append(f"-cat {self.spinBox.value()}")
            else:
                list_command.append("-nocat")
            # support
            if self.comboBox.currentText() == "minimum-evolution bootstrap supports":
                list_command.append("-nome")
            elif self.comboBox.currentText() == "none":
                list_command.append("-nosupport")
            # bootstrap
            if self.spinBox_3.isEnabled():
                bootstrap = self.spinBox_3.value()
                if bootstrap != 1000:
                    list_command.append(f"-boot {self.spinBox_3.value()}")
            # search
            list_command.append(f"-{self.comboBox_2.currentText()}")
            # join
            if self.comboBox_3.currentText() == "regular (unweighted) neighbor-joining":
                list_command.append("-nj")
            elif self.comboBox_3.currentText() == "weighted joins as in BIONJ":
                list_command.append("-bionj")
            # log
            list_command.append(f"-log \"FastTree.log\"")
            self.output_fast_tree = self.lineEdit.text() if self.lineEdit.text() else 'FastTree.nwk'
            self.dict_args["tree_name"] = self.output_fast_tree
            list_command.append(f"-out \"{self.output_fast_tree}\"")
            list_command.append("$alignment$")
            command = " ".join(list_command)
            self.reference = "Price, M.N., Dehal, P.S., and Arkin, A.P. (2010) FastTree 2 -- Approximately " \
                             "Maximum-Likelihood Trees for Large Alignments. PLoS ONE, 5(3):e9490. " \
                             "doi:10.1371/journal.pone.0009490"
            cmd_used = ""# "{costs}{specificity}{large}{log_only}{ali}{changeID}{profile}{symfrac}".format(**self.dict_args).strip()
            self.description = f"Maximum likelihood phylogenies were inferred using FastTree v{self.version} " \
                               f"(Price et al., 2010) using \"{cmd_used}\" command."
            self.textEdit_log.clear()  # 清空
            return command
        else:
            QMessageBox.critical(
                self,
                "FastTree",
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
            self.FastTree_exception.emit(
                "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!")
            self.error_has_shown = True
        elif info[0] == "popen finished":
            if info[1] in self.list_pids:
                self.list_pids.remove(info[1])

    def popup_FastTree_exception(self, text):
        if not self.error_has_shown:
            QMessageBox.critical(
                self,
                "FastTree",
                "<p style='line-height:25px; height:25px'>%s</p>" % text)
            if "Show log" in text:
                self.on_pushButton_9_clicked()

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("FastTree", self.workPath, self.auto_popSig, self)

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
            input_MSA, input_model = widget.autoInputs
            self.workflow_input(input_MSA, input_model)

    # def fetchWorkflowSetting(self):
    #     '''* Alignment Mode
    #       * Code table(if codon mode)
    #       * strategy
    #       * export format'''
    #     settings = '''<p class="title">***FastTree***</p>'''
    #     c1 = self.doubleSpinBox.value()
    #     c2 = self.doubleSpinBox_2.value()
    #     c3 = self.doubleSpinBox_3.value()
    #     c4 = self.doubleSpinBox_4.value()
    #     settings += '<p>costs: \"<a href="self.HmmCleaner_exe doubleSpinBox.setFocus() doubleSpinBox.selectAll() ' \
    #                 'factory.highlightWidgets(x.doubleSpinBox)">%s</a>\" ' \
    #                 '\"<a href="self.HmmCleaner_exe doubleSpinBox_2.setFocus() doubleSpinBox_2.selectAll() ' \
    #                 'factory.highlightWidgets(x.doubleSpinBox_2)">%s</a>\" ' \
    #                 '\"<a href="self.HmmCleaner_exe doubleSpinBox_3.setFocus() doubleSpinBox_3.selectAll() ' \
    #                 'factory.highlightWidgets(x.doubleSpinBox_3)">%s</a>\" ' \
    #                 '\"<a href="self.HmmCleaner_exe doubleSpinBox_4.setFocus() doubleSpinBox_4.selectAll() ' \
    #                 'factory.highlightWidgets(x.doubleSpinBox_4)">%s</a>\"</p>' % (c1, c2, c3, c4)
    #     verbosity = self.comboBox_5.currentText()
    #     settings += '<p>verbosity: <a href="self.HmmCleaner_exe comboBox_5.showPopup()' \
    #                 ' factory.highlightWidgets(x.comboBox_5)">%s</a></p>' % verbosity
    #     profile = self.comboBox_3.currentText()
    #     settings += '<p>profile: <a href="self.HmmCleaner_exe comboBox_3.showPopup()' \
    #                 ' factory.highlightWidgets(x.comboBox_3)">%s</a></p>' % profile
    #     thread = self.comboBox_6.currentText()
    #     settings += '<p>Thread: <a href="self.HmmCleaner_exe comboBox_6.showPopup()' \
    #                 ' factory.highlightWidgets(x.comboBox_6)">%s</a></p>' % thread
    #     specificity = "Yes" if self.checkBox.isChecked() else "No"
    #     settings += '<p>specificity: <a href="self.HmmCleaner_exe' \
    #                 ' factory.highlightWidgets(x.checkBox)">%s</a></p>' % specificity
    #     large = "Yes" if self.checkBox_2.isChecked() else "No"
    #     settings += '<p>large: <a href="self.HmmCleaner_exe' \
    #                 ' factory.highlightWidgets(x.checkBox_2)">%s</a></p>' % large
    #     changeID = "Yes" if self.checkBox_6.isChecked() else "No"
    #     settings += '<p>changeID: <a href="self.HmmCleaner_exe' \
    #                 ' factory.highlightWidgets(x.checkBox_6)">%s</a></p>' % changeID
    #     noX = "Yes" if self.checkBox_5.isChecked() else "No"
    #     settings += '<p>noX: <a href="self.HmmCleaner_exe' \
    #                 ' factory.highlightWidgets(x.checkBox_5)">%s</a></p>' % noX
    #     return settings

    def isFileIn(self):
        return self.comboBox_11.count()

    def clear_lineEdit(self):
        sender = self.sender()
        lineEdit = sender.parent()
        lineEdit.setText("")
        lineEdit.setToolTip("")

    def workflow_input(self, MSA=None, model_file=None):
        self.comboBox_11.refreshInputs([])
        self.lineEdit_2.setText("")
        self.input(MSA)
        self.autoModelFile = model_file
        if model_file:
            self.autoModel(model_file)

    def autoModel(self, model_file):
        ##普通模型, modelfinder选出来的所有模型
        f = self.factory.read_file(model_file)
        content = f.read()
        f.close()
        rgx_model = re.compile(r"Best-fit model according to.+?\: (.+)")
        best_model = rgx_model.search(content).group(1)
        model_split = best_model.split("+")
        model = model_split[0]
        index = self.comboBox_7.findText(model, Qt.MatchFixedString)
        if index >= 0:
            self.comboBox_7.setCurrentIndex(index)
        else:
            QMessageBox.information(
                self,
                "MrBayes",
                "<p style='line-height:25px; height:25px'>Model invalid! Only 'GTR', "
                "'JTT', 'LG' and 'WAG' are allowed</p>",
                QMessageBox.Ok)
        has_G = False
        for i in model_split[1:]:
            if "G" in i:
                self.checkBox_3.setChecked(True)
                if re.search(r"G(\d+)", i):
                    category = re.search(r"G(\d+)", i).group(1)
                else:
                    category = "20"
                self.spinBox.setValue(int(category))
                has_G = True
        if not has_G:
            self.checkBox_3.setChecked(False)

    def control_boot(self, text):
        if text == "none":
            self.spinBox_3.setEnabled(False)
        else:
            self.spinBox_3.setEnabled(True)

    @pyqtSlot(list)
    def popupWarning_with_details(self, list_):
        ## 为了统一，统一用的列表
        msg = QMessageBox(self)
        if type(list_) == list:
            ## 有缺失基因的情况，这时候warning是个字典
            msg.setIcon(QMessageBox.Information)
            msg.setText(
                "<p style='line-height:25px; height:25px'>Runs of some file (see details) failed! "
                "</p>")
            msg.setWindowTitle("FastTree run failed")
            msg.setDetailedText("\n".join(list_))
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def judgeIQTREEinstalled(self, text):
        if text == "AUTO":
            IQpath = self.factory.programIsValid("iq-tree", mode="tool")
            if not IQpath:
                reply = QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Please install IQ-TREE (for model selection) first!</p>",
                    QMessageBox.Ok,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.setting = Setting(self.parent)
                    self.setting.display_table(self.setting.listWidget.item(1))
                    # 隐藏？按钮
                    self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                    self.setting.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = FastTree()
    ui.show()
    sys.exit(app.exec_())