#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import multiprocessing
import re
import shutil

import datetime
import signal

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.CustomWidget import MyPartEditorTableModel
from src.Lg_PartitionEditer import PartitionEditor
from src.factory import Factory, WorkThread
from uifiles.Ui_ModelFinder import Ui_ModelFinder
import inspect
import os
import sys
import traceback
import platform


class ModelFinder(QDialog, Ui_ModelFinder, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    search_algorithm = pyqtSignal(str)  # 定义所有类都可以使用的信号
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    iq_tree_exception = pyqtSignal(str)  # 定义所有类都可以使用的信号
    # 用于flowchart自动popup combobox等操作
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    # 用于输入文件后判断用
    ui_closeSig = pyqtSignal(str)
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)

    def __init__(
            self,
            autoMFPath=None,
            partFile=None,
            workPath=None,
            focusSig=None,
            IQ_exe=None,
            workflow=False,
            parent=None):
        super(ModelFinder, self).__init__(parent)
        self.parent = parent
        self.function_name = "ModelFinder"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig if focusSig else pyqtSignal(
            str)  # 为了方便workflow
        self.workflow = workflow
        self.modelfinder_exe = IQ_exe
        self.autoMFPath = autoMFPath[0] if type(autoMFPath) == list else autoMFPath
        self.partFile = partFile
        self.interrupt = False
        self.setupUi(self)
        # 保存设置
        if not workflow:
            self.modelfinder_settings = QSettings(
                self.thisPath + '/settings/modelfinder_settings.ini', QSettings.IniFormat)
        else:
            self.modelfinder_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.modelfinder_settings.beginGroup("Workflow")
            self.modelfinder_settings.beginGroup("temporary")
            self.modelfinder_settings.beginGroup('ModelFinder')
        # File only, no fallback to registry or or.
        self.modelfinder_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.textEdit.dblclicked.connect(self.popupPartitionEditor)
        self.partitioneditor = PartitionEditor(mode="MF", parent=self)
        self.partitioneditor.guiCloseSig.connect(lambda text: [self.textEdit.setText(text),
                                                               self.textEdit.setToolTip(text)])
        self.textEdit.buttonEdit.clicked.connect(self.popupPartitionEditor)
        self.guiRestore()
        # 判断IQTREE的版本，以决定要不要加新功能
        self.version = ""
        version_worker = WorkThread(
            lambda : self.factory.get_version("ModelFinder", self),
            parent=self)
        version_worker.start()
        self.exception_signal.connect(self.popupException)
        self.iq_tree_exception.connect(self.popup_IQTREE_exception)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.logGuiSig.connect(self.addText2Log)
        self.comboBox_4.installEventFilter(self)
        self.log_gui = self.gui4Log()
        self.lineEdit.installEventFilter(self)
        self.lineEdit.autoDetectSig.connect(self.popupAutoDec)
        self.lineEdit_2.installEventFilter(self)
        # self.lineEdit_3.installEventFilter(self)
        self.comboBox_3.activated[str].connect(self.controlCodonTable)
        self.comboBox_5.activated[str].connect(self.ctrl_ratehet)
        self.ctrl_ratehet(self.comboBox_5.currentText())
        self.lineEdit_2.setLineEditNoChange(True)
        # self.lineEdit_3.setLineEditNoChange(True)
        self.lineEdit.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        self.lineEdit_2.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        # self.lineEdit_3.deleteFile.clicked.connect(
        #     self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        # rcluster
        self.checkBox.toggled.connect(self.judgeMergeOn)
        # 初始化codon table的选择
        self.controlCodonTable(self.comboBox_3.currentText())
        # self.checkBox.stateChanged.connect(self.switchPart)
        # self.switchPart(self.checkBox.isChecked())
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
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-9-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-9-1-Brief-example"
        self.label_2.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)

    @pyqtSlot()
    def on_pushButton_clicked(self, cmd_directly=False):
        """
        execute program
        """
        try:
            self.command = self.getCMD() if not cmd_directly else cmd_directly[0]
            if cmd_directly:
                self.exportPath = cmd_directly[1] if cmd_directly[1] else self.exportPath
                os.chdir(self.exportPath)  # 因为用了-pre，所以要先切换目录到该文件夹
            self.cmd_directly = cmd_directly
            if self.command:
                self.MF_popen = self.factory.init_popen(self.command)
                self.factory.emitCommands(self.logGuiSig, f"cd {os.path.normpath(self.exportPath)}\n{self.command}")
                self.worker = WorkThread(self.run_command, parent=self)
                self.worker.start()
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        alignment file
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input alignment file", filter="Phylip Format(*.phy *.phylip);;Fasta Format(*.fas *.fasta);;Nexus Format(*.nex *.nexus *.nxs);;Clustal Format(*.aln)")
        if fileName[0]:
            base = os.path.basename(fileName[0])
            self.lineEdit.setText(base)
            self.lineEdit.setToolTip(fileName[0])

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        """
        tree file
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input tree file", filter="Newick Format(*.nwk *.newick);;")
        if fileName[0]:
            base = os.path.basename(fileName[0])
            self.lineEdit_2.setText(base)
            self.lineEdit_2.setToolTip(fileName[0])

    # @pyqtSlot()
    # def on_pushButton_22_clicked(self):
    #     """
    #     partition file
    #     """
    #     fileName = QFileDialog.getOpenFileName(
    #         self, "Input partition file", filter="All(*);;")
    #     if fileName[0]:
    #         base = os.path.basename(fileName[0])
    #         self.lineEdit_3.setText(base)
    #         self.lineEdit_3.setToolTip(fileName[0])

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
                    "<p style='line-height:25px; height:25px'>ModelFinder is still running, terminate it?</p>",
                    QMessageBox.Yes,
                QMessageBox.Cancel)
            else:
                reply = QMessageBox.Yes
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.MF_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.MF_popen.pid), signal.SIGTERM)
                    self.MF_popen = None
                    self.interrupt = True
                except:
                    self.MF_popen = None
                    self.interrupt = True
                if not self.workflow:
                    QMessageBox.information(
                        self,
                        "ModelFinder",
                        "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])

    @pyqtSlot()
    def on_pushButton_continue_clicked(self):
        """
        continue
        """
        if self.isRunning():
            QMessageBox.information(
                self,
                "ModelFinder",
                "<p style='line-height:25px; height:25px'>ModelFinder is running!</p>")
            return
        resultsPath = None
        ##choose work folder
        if os.path.exists(self.workPath + os.sep + "ModelFinder_results"):
            list_result_dirs = sorted([i for i in os.listdir(self.workPath + os.sep + "ModelFinder_results")
                                       if os.path.isdir(self.workPath + os.sep + "ModelFinder_results" + os.sep + i)],
                                       key=lambda x: os.path.getmtime(
                                          self.workPath + os.sep + "ModelFinder_results" + os.sep + x), reverse=True)
            if list_result_dirs:
                item, ok = QInputDialog.getItem(self, "Choose previous results",
                                                "Previous results:", list_result_dirs, 0, False)
                if ok and item:
                    resultsPath = self.workPath + os.sep + "ModelFinder_results" + os.sep + item
        else:
            QMessageBox.information(
                self,
                "ModelFinder",
                "<p style='line-height:25px; height:25px'>No previous ModelFinder analysis found in %s!</p>" % os.path.normpath(
                    self.workPath))
            return
        if not resultsPath: return
        has_cmd = False
        if os.path.exists(resultsPath + os.sep + "PhyloSuite_ModelFinder.log"):
            with open(resultsPath + os.sep + "PhyloSuite_ModelFinder.log", encoding="utf-8", errors='ignore') as f:
                rgx = re.compile(r"(?s)\=+?Commands\=+?\n(.+?)\n\={3,}")
                rgx_search = rgx.search(f.read())
                if rgx_search:
                    cmd = rgx_search.group(1)
                    cmd = cmd.replace("\n", " ")
                    has_cmd = True
        else:
            ## 用IQTREE自带的log文件来获取
            list_log_files = glob.glob(resultsPath + os.sep + "*.log")
            for i in list_log_files:
                with open(i) as f1:
                    content = f1.read()
                    rgx_search = re.search(r"^Command: (.+?)\n", content)
                    if rgx_search:
                        cmd = rgx_search.group(1)
                        has_cmd = True
        if has_cmd:
            self.interrupt = False
            self.on_pushButton_clicked(cmd_directly=[cmd, resultsPath])
        else:
            QMessageBox.information(
                self,
                "ModelFinder",
                "<p style='line-height:25px; height:25px'>No ModelFinder command found in %s!</p>" % os.path.normpath(
                    resultsPath))

    def run_command(self):
        try:
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            if hasattr(self, "cmd_directly") and self.cmd_directly:
                self.description = ""
                self.reference = "Kalyaanamoorthy, S., Minh, B.Q., Wong, T.K.F., von Haeseler, A., Jermiin, L.S., 2017. ModelFinder: fast model selection for accurate phylogenetic estimates. Nat. Methods 14, 587-589."
                self.continue_MF()
            else:
                self.run_MF()
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                           self.time_used)
            softWare = self.comboBox_5.currentText()
            # 如果有partition结果，就保存一下
            # (?sm)charpartition.+\r\n(^ +.+?\: .+)^end;
            best_scheme = glob.glob(f"{self.exportPath}{os.sep}*best_scheme.nex")
            if best_scheme:
                list_partition_table = [["Subset partitions", "Best model"]]
                best_scheme_file = best_scheme[0]
                with open(best_scheme_file, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                list_ = re.findall(r"(?m)^ +(.+?)\: (.+)[,;]", content)
                for num,i in enumerate(list_):
                    model, name = i
                    list_partition_table.append([f"P{num+1}: ({name.strip(' ')})",
                                                 model])
                self.factory.write_csv_file(f"{self.exportPath}{os.sep}best_scheme_and_models.csv",
                                            list_partition_table,
                                            silence=True)
            if softWare in ["BEAST1 (NUC)", "BEAST2 (NUC)", "BEAST (AA)"]:
                str1 = self.description + " " + self.parseResults() +\
                    "\n\nIf you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n" \
                    "If you use ModelFinder, please cite:\n" + self.reference + \
                    "\n\nhttps://justinbagley.rbind.io/2016/10/11/setting-dna-substitution-models-beast/\nDetails for setting substitution models in %s\n" % softWare
                array = [[i] for i in str1.split(
                    "\n")] + self.model2beast_des() + [[j] for j in ("\n\n" + self.time_used_des).split("\n")]
                self.factory.write_csv_file(
                    self.exportPath + os.sep + "summary.csv", array, self, silence=True)
            else:
                with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                    f.write(self.description + " " + self.parseResults() +
                            "\n\nIf you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n"
                            "If you use ModelFinder, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
            if not self.interrupt:
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
            else:
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])
            if not self.workflow:
                self.focusSig.emit(self.exportPath)
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

    def guiSave(self):
        # Save geometry
        self.modelfinder_settings.setValue('size', self.size())
        # self.modelfinder_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.modelfinder_settings.setValue(name, index)
            # if isinstance(obj, QLineEdit):
            #     text = obj.text()
            #     tooltip = obj.toolTip()
            #     self.modelfinder_settings.setValue(name, [text, tooltip])
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.modelfinder_settings.setValue(name, state)
            if isinstance(obj, QRadioButton):
                state = obj.isChecked()
                self.modelfinder_settings.setValue(name, state)
            if isinstance(obj, QGroupBox):
                state = obj.isChecked()
                self.modelfinder_settings.setValue(name, state)

    def guiRestore(self):

        # Restore geometry
        size = self.factory.judgeWindowSize(self.modelfinder_settings, 840, 505)
        self.resize(size)
        self.factory.centerWindow(self)
        # self.move(self.modelfinder_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox_6":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = ["AUTO"] + [str(i + 1) for i in range(cpu_num)]
                    index = self.modelfinder_settings.value(name, "0")
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
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.modelfinder_settings.value(name, "0")
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
            if isinstance(obj, QLineEdit):
                #     text, tooltip = self.modelfinder_settings.value(name, ["", ""])
                #     if os.path.exists(tooltip):
                #         if os.path.exists(tooltip):
                #             obj.setText(text)
                #             obj.setToolTip(tooltip)
                if self.autoMFPath and name == "lineEdit":
                    if os.path.exists(self.autoMFPath):
                        obj.setText(os.path.basename(self.autoMFPath))
                        obj.setToolTip(self.autoMFPath)
            if isinstance(obj, QTextEdit):
                if self.partFile and name == "textEdit":
                    self.inputPartition(self.partFile)
            if isinstance(obj, QCheckBox):
                value = self.modelfinder_settings.value(
                    name, "true")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QRadioButton):
                value = self.modelfinder_settings.value(
                    name, obj.isChecked())  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QGroupBox):
                value = self.modelfinder_settings.value(
                    name, "false")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox

    def runProgress(self, num):
        if num == 99999:
            self.progressBar.setMaximum(0)
            self.progressBar.setMinimum(0)
        else:
            oldValue = self.progressBar.value()
            done_int = int(num)
            if done_int > oldValue:
                self.progressBar.setProperty("value", done_int)
                QCoreApplication.processEvents()

    def popupException(self, exception):
        print(exception)
        rgx = re.compile(r'Permission.+?[\'\"](.+\.csv)[\'\"]')
        if rgx.search(exception):
            csvfile = rgx.search(exception).group(1)
            reply = QMessageBox.critical(
                self,
                "Extract sequence",
                "<p style='line-height:25px; height:25px'>Please close '%s' file first!</p>" % os.path.basename(
                    csvfile),
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes and platform.system().lower() == "windows":
                os.startfile(csvfile)
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(
                'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
            msg.setWindowTitle("Error")
            msg.setDetailedText(exception)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def popup_IQTREE_exception(self, text):
        if text.endswith("redo"):
            reply = QMessageBox.question(
                self,
                "ModelFinder",
                "<p style='line-height:25px; height:25px'>%s. Do you want to redo the analysis and overwrite all output files?</p>" % text.replace(
                    "redo", ""),
                QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.interrupt = False
                self.on_pushButton_clicked(cmd_directly=[self.command + " -redo", self.exportPath])
                # self.run_with_CMD(self.command + " -redo")
        elif text.endswith("-safe"):
            reply = QMessageBox.question(
                self,
                "IQ-TREE",
                "<p style='line-height:25px; height:25px'>An error happened! Do you want to run again with the "
                "safe likelihood kernel via '-safe' option</p>",
                QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.interrupt = False
                self.run_with_CMD(self.command + " -safe")
        else:
            QMessageBox.information(
                self,
                "ModelFinder",
                "<p style='line-height:25px; height:25px'>%s</p>" % text)
            if "Show log" in text:
                self.on_pushButton_9_clicked()

    def closeEvent(self, event):
        self.guiSave()
        self.log_gui.close()  # 关闭子窗口
        self.closeSig.emit("ModelFinder", self.fetchWorkflowSetting())
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
            self.ui_closeSig.emit("ModelFinder")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            # print(self.isRunning())
            reply = QMessageBox.question(
                self,
                "ModelFinder",
                "<p style='line-height:25px; height:25px'>ModelFinder is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.MF_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.MF_popen.pid), signal.SIGTERM)
                    self.MF_popen = None
                    self.interrupt = True
                except:
                    self.MF_popen = None
                    self.interrupt = True
            else:
                event.ignore()

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        name = obj.objectName()
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
                if name == "lineEdit":
                    if os.path.splitext(files[0])[1].upper() in [".PHY", ".PHYLIP", ".FAS", ".FASTA", ".NEX", ".NEXUS", ".NXS", ".ALN"]:
                        base = os.path.basename(files[0])
                        self.lineEdit.setText(base)
                        self.lineEdit.setToolTip(files[0])
                    else:
                        QMessageBox.information(
                            self,
                            "ModelFinder",
                            "<p style='line-height:25px; height:25px'>Unsupported file!</p>",
                            QMessageBox.Ok)
                elif name == "lineEdit_2" and os.path.splitext(files[0])[1].upper() in [".NWK", ".NEWICK"]:
                    base = os.path.basename(files[0])
                    self.lineEdit_2.setText(base)
                    self.lineEdit_2.setToolTip(files[0])
                # elif name == "lineEdit_3":
                #     base = os.path.basename(files[0])
                #     self.lineEdit_3.setText(base)
                #     self.lineEdit_3.setToolTip(files[0])
        if (event.type() == QEvent.Show) and (obj == self.pushButton.toolButton.menu()):
            if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+", self.dir_action.text()) or self.dir_action.text() == "Output Dir: ":
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
        return super(ModelFinder, self).eventFilter(obj, event)  # 0

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of ModelFinder:")
        horizontalLayout_2.addWidget(label)
        spacerItem = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        horizontalLayout_2.addItem(spacerItem)
        toolButton = QToolButton(dialog)
        icon2 = QIcon()
        icon2.addPixmap(
            QPixmap(":/picture/resourses/interface-controls-text-wrap-512.png"))
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
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def addText2Log(self, text):
        if re.search(r"\w+", text):
            self.textEdit_log.append(text)
            with open(self.exportPath + os.sep + "PhyloSuite_ModelFinder.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "ModelFinder", "log", "text Format(*.txt)")
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

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "MF_popen") and self.MF_popen and not self.interrupt

    def controlCodonTable(self, text):
        if text in ["Codon", "DNA-->AA"]:
            self.comboBox_9.setEnabled(True)
        else:
            self.comboBox_9.setEnabled(False)
        if text == "Codon":
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>If you choose \"Codon\" sequence type, "
                "only \"IQ-TREE\" is allowed as the \"Model for\" option!</p>")
            self.comboBox_5.setCurrentText("IQ-TREE")

    def run_MF(self):
        rgx_test_model = re.compile(r"^ModelFinder will test (\d+) \w+ models")
        rgx_part_model = re.compile(r"^Loading (\d+) partitions\.\.\.")
        rgx_finished = re.compile(r"^Date and Time:")
        self.totleModels = None
        self.totlePartitions_2 = None
        list_partition_names = []  # 存放partition的名字
        num = 0  # partition出现的次数，当num等于2倍partition的个数的时候，就完成
        is_error = False  ##判断是否出了error
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = self.MF_popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = self.MF_popen.stdout.readline().decode("gbk", errors="ignore")
                if out_line == "" and self.MF_popen.poll() is not None:
                    break
                list_outline = out_line.strip().split()
                if rgx_test_model.search(out_line):
                    self.totleModels = int(
                        rgx_test_model.search(out_line).group(1))
                    self.progressSig.emit(5)
                    self.workflow_progress.emit(5)
                elif rgx_part_model.search(out_line):
                    self.totlePartitions_2 = 2 * \
                        int(rgx_part_model.search(out_line).group(1))
                    self.progressSig.emit(5)
                    self.workflow_progress.emit(5)
                elif self.totleModels and (len(list_outline) == 7) and list_outline[0].isdigit() and list_outline[3].isdigit():
                    # 普通模式
                    model_num = int(list_outline[0])
                    self.progressSig.emit(
                        5 + model_num * 90 / self.totleModels)
                    self.workflow_progress.emit(
                        5 + model_num * 90 / self.totleModels)
                # 下面2个是partition mode
                elif self.totlePartitions_2 and re.search(r"^\d", out_line) and len(out_line.strip().split("\t")) == 8:
                    # partition模式, Subset     Type    Seqs    Sites   Infor
                    # Invar   Model   Name
                    list_partition_names.append(
                        out_line.strip().split("\t")[-1])
                elif list_partition_names and self.totlePartitions_2 and (num <= self.totlePartitions_2) and re.search(r"^ +\d+|^Optimizing", out_line):
                    for i in list_partition_names:
                        if i in out_line:
                            num += 1
                            self.progressSig.emit(
                                5 + num * 90 / self.totlePartitions_2)
                            self.workflow_progress.emit(
                                5 + num * 90 / self.totlePartitions_2)
                    # print(num, self.totlePartitions_2)
                elif rgx_finished.search(out_line):
                    self.progressSig.emit(100)
                    self.workflow_progress.emit(100)
                text = out_line.strip() if re.search(r"\w", out_line) else "\n"
                self.logGuiSig.emit(text)
                if re.search(r"^ERROR", out_line):
                    is_error = True
                    # self.on_pushButton_9_clicked()
                # redo
                if re.search(r"(?m)(^Checkpoint.+?a previous run successfully finished)", out_line):
                    self.interrupt = True
                    text = re.search(
                        r"(?m)(^Checkpoint.+?a previous run successfully finished)", out_line).group(1)
                    self.iq_tree_exception.emit(text + "redo")
                # safe
                if re.search(r"via '?-safe'? option", out_line):
                    self.interrupt = True
                    text = "error"
                    self.iq_tree_exception.emit(text + "-safe")
            else:
                break
        if is_error:
            self.interrupt = True
            self.iq_tree_exception.emit(
                "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!")
        self.MF_popen = None

    def continue_MF(self):
        is_error = False  ##判断是否出了error
        self.progressSig.emit(99999)
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = self.MF_popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = self.MF_popen.stdout.readline().decode("gbk", errors="ignore")
                if out_line == "" and self.MF_popen.poll() is not None:
                    break
                text = out_line.strip() if out_line != "\n" else "\n"
                # print(text)
                self.logGuiSig.emit(text)
                if re.search(r"^ERROR", out_line):
                    is_error = True
                # redo
                if re.search(r"(?m)(^Checkpoint.+?a previous run successfully finished)", out_line):
                    self.interrupt = True
                    text = re.search(
                        r"(?m)(^Checkpoint.+?a previous run successfully finished)", out_line).group(1)
                    self.iq_tree_exception.emit(text + "redo")
            else:
                break
        if is_error:
            self.interrupt = True
            self.iq_tree_exception.emit(
                "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!")
        self.MF_popen = None

    def clear_lineEdit(self):
        sender = self.sender()
        lineEdit = sender.parent()
        lineEdit.setText("")
        lineEdit.setToolTip("")

    def ctrl_ratehet(self, text):
        if text == "IQ-TREE":
            self.checkBox_2.setEnabled(True)
        else:
            self.checkBox_2.setEnabled(False)
        if self.comboBox_3.currentText() == "Codon" and text != "IQ-TREE":
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>If you choose \"Codon\" sequence type, "
                "only \"IQ-TREE\" is allowed as the \"Model for\" option!</p>")
            self.comboBox_5.setCurrentText("IQ-TREE")

    def workflow_input(self, MSA=None, partition=None):
        self.lineEdit.setText("")
        self.lineEdit_2.setText("")
        self.textEdit.setText("")
        if MSA:
            MSA = MSA[0] if type(MSA) == list else MSA
            self.lineEdit.setText(os.path.basename(MSA))
            self.lineEdit.setToolTip(MSA)
        if partition:
            self.inputPartition(partition)

    def inputPartition(self, partition):
        if os.path.exists(partition):
            with open(partition, encoding="utf-8", errors='ignore') as f:
                partition_txt = f.read()
            search_ = re.search(
                r"(?s)\*\*\*IQ-TREE style\*\*\*(.+?)[\*|$]", partition_txt)
            iq_partition = search_.group(1).strip() if search_ else ""
            array = self.partitioneditor.readPartition(iq_partition, mode="MF")
            text = self.partitioneditor.partition2text(array, mode="MF")
            # path = os.path.dirname(partition) + os.sep + "MF_partition.txt"
            # with open(path, "w", encoding="utf-8") as f1:
            #     f1.write(text)
            self.textEdit.setText(text)
            self.textEdit.setToolTip(text)

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect(
            "ModelFinder", self.workPath, self.auto_popSig, self)

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
            input_file, partition_file = widget.autoInputs
            self.workflow_input(input_file, partition_file)

    def fetchWorkflowSetting(self):
        '''* if partition mode, partition style:
          * seq type:
          * code table(if codon)
          * criterion
          * model for: '''
        settings = '''<p class="title">***ModelFinder***</p>'''
        ifPartition = "Yes" if self.groupBox_2.isChecked() else "No"
        settings += '<p>Partition mode: <a href="self.ModelFinder_exe' \
                    ' factory.highlightWidgets(x.groupBox_2)">%s</a></p>' % ifPartition
        if ifPartition == "Yes":
            partStyle = "Edge-linked" if self.radioButton.isChecked() else "Edge-unlinked"
            settings += '<p>Partition style: <a href="self.ModelFinder_exe' \
                        ' factory.highlightWidgets(x.radioButton,x.radioButton_2)">%s</a></p>' % partStyle
        seq_type = self.comboBox_3.currentText()
        settings += '<p>Sequence type: <a href="self.ModelFinder_exe comboBox_3.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_3)">%s</a></p>' % seq_type
        threads = self.comboBox_6.currentText()
        settings += '<p>Threads: <a href="self.ModelFinder_exe comboBox_6.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_6)">%s</a></p>' % threads
        if seq_type == "Codon":
            code_table = self.comboBox_9.currentText()
            settings += '<p>Code table: <a href="self.ModelFinder_exe comboBox_9.showPopup()' \
                        ' factory.highlightWidgets(x.comboBox_9)">%s</a></p>' % code_table
        criterion = self.comboBox_4.currentText()
        settings += '<p>Criterion: <a href="self.ModelFinder_exe comboBox_4.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_4)">%s</a></p>' % criterion
        modelFor = self.comboBox_5.currentText()
        settings += '<p>Model used for: <a href="self.ModelFinder_exe comboBox_5.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_5)">%s</a></p>' % modelFor
        return settings

    def showEvent(self, event):
        QTimer.singleShot(100, lambda: self.showSig.emit(self))
        # self.showSig.emit(self)

    def isFileIn(self):
        alignment = self.lineEdit.toolTip()
        if os.path.exists(alignment):
            return alignment
        else:
            return False

    def parseResults(self):
        # 非partition模式
        list_input_model_file = [self.exportPath + os.sep + i for i in os.listdir(self.exportPath) if
                                 os.path.splitext(i)[1].upper() == ".IQTREE"]
        input_model_file = list_input_model_file[
            0] if list_input_model_file else ""
        if input_model_file:
            f = self.factory.read_file(input_model_file)
            # with open(input_model_file, encoding="utf-8", errors='ignore') as f: #"rb",
            model_content = f.read()
            # f.close()
            rgx_model = re.compile(r"(Best-fit model according to.+?\: )(.+)")
            # softWare = self.comboBox_5.currentText()
            # if softWare in ["BEAST1", "BEAST2"]:
            #     prefix = rgx_model.search(model_content).group(1)
            #     model = rgx_model.search(model_content).group(2)
            #     version = softWare[-1]
            #     model_split = model.split("+")[0]
            #     model4beast, addSpecify = self.convertModel2beast(softWare, model_split)
            #     best_model = model.replace(model_split, model4beast)
            #     best_model = prefix + best_model + " [Additional specifications in BEAUti%s: %s]"%(version, addSpecify) \
            #         if addSpecify else prefix + best_model
            # else:
            best_model = rgx_model.search(model_content).group()
        else:
            best_model = ""
        return best_model + "."

    # def convertModel2beast(self, softWare, model):
    #     '''作废'''
    #     if softWare == "BEAST1":
    #         model_replace = {"JC69": ["JC69", ""],
    #                          "TrN": ["TN93", ""],
    #                          "TrNef": ["TN93", 'base Frequencies set to "All Equal"'],
    #                          "K80": ["HKY", 'base Frequencies set to "All Equal"'],
    #                          "K2P": ["HKY", 'base Frequencies set to "All Equal"'],
    #                          "F81": ["GTR", 'turn off operators for all rate parameters'],
    #                          "HKY": ["HKY", ''],
    #                          "SYM": ["GTR", 'base Frequencies set to "All Equal"'],
    #                          "TIM": ["GTR", 'edit XML file by hand so that all other rates are equal to the AG rate'],
    #                          "TVM": ["GTR", 'unchecking AG rate operator'],
    #                          "TVMef": ["GTR", 'unchecking AG rate operator and setting base Frequencies to "All Equal"'],
    #                          "GTR": ["GTR", '']}
    #         if model in model_replace:
    #             return model_replace[model]
    #         else:
    #             return [model, '']
    #     else:
    #         #BEAST2
    #         model_replace = {"JC69": ["JC69", ""],
    #                          "TrN": ["TN93", ""],
    #                          "TrNef": ["TN93", 'base Frequencies set to "All Equal"'],
    #                          "K80": ["HKY", 'base Frequencies set to "All Equal"'],
    #                          "K2P": ["HKY", 'base Frequencies set to "All Equal"'],
    #                          "F81": ["GTR", 'fix all rate parameters to 1.0 (uncheck the "estimate" box)'],
    #                          "HKY": ["HKY", ''],
    #                          "SYM": ["GTR", 'base Frequencies set to "All Equal"'],
    #                          "TIM": ["GTR", 'fix CT and AG rate parameters to 1.0 (uncheck the "estimate" box)'],
    #                          "TVM": ["GTR", 'fix the AG rate parameter to 1.0 (uncheck the "estimate" box)'],
    #                          "TVMef": ["GTR", 'fix the AG rate parameter to 1.0 (uncheck the "estimate" box), '
    #                                         'and also set base Frequencies to "All Equal"'],
    #                          "GTR": ["GTR", '']}
    #         if model in model_replace:
    #             return model_replace[model]
    #         else:
    #             return [model, '']

    def model2beast_des(self):
        softWare = self.comboBox_5.currentText()
        if softWare == "BEAST1 (NUC)":
            return [['Best-fit substitution model', '(Base) Model to select in BEAUti', 'Additional specifications in BEAUti'],
                    ['JC69', 'JC69', 'None '],
                    ['TrN', 'TN93', 'None '],
                    ['TrNef', 'TN93', 'base Frequencies set to "All Equal"'],
                    ['K80 (K2P)', 'HKY',
                     'base Frequencies set to "All Equal"'],
                    ['F81', 'GTR',
                        'turn off operators for all rate parameters'],
                    ['HKY', 'HKY', 'None'],
                    ['SYM', 'GTR', 'base Frequencies set to "All Equal"'],
                    ['TIM', 'GTR',
                     'edit XML file by hand so that all other rates are equal to the AG rate'],
                    ['TVM', 'GTR', 'unchecking AG rate operator'],
                    ['TVMef', 'GTR',
                     'unchecking AG rate operator and setting base Frequencies to "All Equal"'],
                    ['GTR', 'GTR', 'None']]
        elif softWare == "BEAST2 (NUC)":
            return [['Best-fit substitution model', '(Base) Model to select in BEAUti 2', 'Additional specifications in BEAUti 2'],
                    ['JC69', 'JC69', 'None '],
                    ['TrN', 'TN93', 'None'],
                    ['TrNef', 'TN93', 'base Frequencies set to "All Equal"'],
                    ['K80 (K2P)', 'HKY',
                     'base Frequencies set to "All Equal"'],
                    ['F81', 'GTR',
                     'fix all rate parameters to 1.0 (uncheck the "estimate" box)'],
                    ['HKY', 'HKY', ' None'],
                    ['SYM', 'GTR', 'base Frequencies set to "All Equal"'],
                    ['TIM', 'GTR',
                     'fix CT and AG rate parameters to 1.0 (uncheck the "estimate" box)'],
                    ['TVM', 'GTR',
                     'fix the AG rate parameter to 1.0 (uncheck the "estimate" box)'],
                    ['TVMef', 'GTR',
                     'fix the AG rate parameter to 1.0 (uncheck the "estimate" box), and also set base Frequencies to "All Equal"'],
                    ['GTR', 'GTR', ' None']]
        else:
            return []

    # def switchPart(self, state):
    #     if state:
    #         if not self.workflow:
    #             self.lineEdit_3.setEnabled(True)
    #             self.pushButton_22.setEnabled(True)
    #     else:
    #         if not self.workflow:
    #             self.lineEdit_3.setEnabled(False)
    #             self.pushButton_22.setEnabled(False)

    def getCMD(self):
        alignment = self.isFileIn()
        if alignment:
            # 有数据才执行
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.interrupt = False
            self.exportPath = self.factory.creat_dirs(self.workPath +
                                                     os.sep + "ModelFinder_results" + os.sep + self.output_dir_name)
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                # 提醒是否删除旧结果，如果用户取消，就不执行
                return
            os.chdir(self.exportPath)  # 因为用了-pre，所以要先切换目录到该文件夹
            inputFile = os.path.basename(
                shutil.copy(alignment, self.exportPath))
            pre = " -pre \"%s\""%self.factory.refineName(inputFile + "." + self.comboBox_5.currentText().lower().replace("-", "_"))
            # use_model_for = " -m MF" if self.comboBox_5.currentText() == "IQ-TREE" else " -m TESTONLY -mset %s"%self.comboBox_5.currentText().lower()
            if self.comboBox_5.currentText() == "IQ-TREE":
                if self.checkBox_2.isChecked():
                    if self.groupBox_2.isChecked() and self.textEdit.toPlainText() and self.checkBox_3.isChecked():  # partition
                        #确保勾选了partition以及输入了文件
                        use_model_for = " -m TESTNEWMERGEONLY"
                    else:
                        use_model_for = " -m TESTNEWONLY"
                else:
                    if self.groupBox_2.isChecked() and self.textEdit.toPlainText() and self.checkBox_3.isChecked():  # partition
                        use_model_for = " -m TESTMERGEONLY"
                    else:
                        use_model_for = " -m TESTONLY"
            elif self.comboBox_5.currentText() in ["BEAST1 (NUC)", "BEAST2 (NUC)"]:
                use_model_for = " -mset JC69,TrN,TrNef,K80,K2P,F81,HKY,SYM,TIM,TVM,TVMef,GTR -mrate E,G"
            elif self.comboBox_5.currentText() in ["BEAST (AA)"]:
                use_model_for = " -mset Blosum62,cpREV,JTT,mtREV,WAG,LG,Dayhoff -mrate E,G"
            elif self.comboBox_5.currentText() in ["FastTree (AA)"]:
                use_model_for = " -mset JTT,WAG,LG -mrate G"
            else:
                use_model_for = " -m TESTONLY -mset %s" % self.comboBox_5.currentText().lower() \
                    if ((not self.groupBox_2.isChecked()) or (not self.textEdit.toPlainText()) or
                        (not self.checkBox_3.isChecked())) else " -m TESTMERGEONLY -mset %s" % self.comboBox_5.currentText().lower()
            use_model_for = f"{use_model_for} -rcluster {self.spinBox.value()}" if \
                (self.checkBox.isChecked() and self.groupBox_2.isChecked()) else use_model_for
            criterion_org = re.search(
                r"\((\w+)\)", self.comboBox_4.currentText()).group(1)
            criterion = " -%s" % criterion_org if criterion_org != "BIC" else ""
            dict_seq = {"DNA": "DNA", "Protein": "AA", "Codon": "CODON", "Binary": "BIN", "Morphology": "MORPH",
                        "DNA-->AA": "NT2AA"}
            seqType = " -st %s" % dict_seq[
                self.comboBox_3.currentText()] if self.comboBox_3.currentText() != "Auto detect" else ""
            codon_table_index = self.comboBox_9.currentText().split(" ")[0]
            seqType = seqType + \
                codon_table_index if seqType in [
                    " -st CODON", " -st NT2AA"] else seqType
            treeFile = " -te %s" % shutil.copy(self.lineEdit_2.toolTip(),
                                               self.exportPath) if self.lineEdit_2.toolTip() else ""
            partitionCMD = "-spp" if self.radioButton.isChecked() else "-sp"
            if (self.groupBox_2.isChecked() and self.textEdit.toPlainText()):
                path = self.exportPath + os.sep + "MF_partition.txt"
                with open(path, "w", encoding="utf-8") as f1:
                    f1.write(self.textEdit.toPlainText())
                partFile = " %s \"%s\"" % (partitionCMD, path)
            else: partFile = ""
            threads = " -nt %s" % self.comboBox_6.currentText()
            command = f"\"{self.modelfinder_exe}\" -s \"%s\"" % inputFile + \
                use_model_for + criterion + seqType + \
                treeFile + partFile + threads + pre
            # print(self.command)
            self.textEdit_log.clear()  # 清空
            # 描述
            type = "Edge-linked" if self.radioButton.isChecked() else "Edge-unlinked"
            model = "best-fit model" if not partFile else "best-fit partition model (%s)" % type
            self.description = '''ModelFinder v%s (Kalyaanamoorthy et al., 2017) was used to select the %s using %s criterion.''' % (
                self.version, model, criterion_org)
            self.reference = "Kalyaanamoorthy, S., Minh, B.Q., Wong, T.K.F., von Haeseler, A., Jermiin, L.S., 2017. ModelFinder: fast model selection for accurate phylogenetic estimates. Nat. Methods 14, 587-589."
            return command
        else:
            QMessageBox.critical(
                self,
                "ModelFinder",
                "<p style='line-height:25px; height:25px'>Please input alignment file first!</p>")
            return None

    def showCMD(self):
        """
        show command
        """
        self.command = self.getCMD()
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
            self.MF_popen = self.factory.init_popen(self.command)
            self.factory.emitCommands(self.logGuiSig, self.command)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

    def popupPartitionEditor(self):
        partition_content = self.textEdit.toPlainText().strip()
        array = self.partitioneditor.readPartition(partition_content, mode="MF")
        ini_array = [["", "=", "", "-", ""],
                     ["", "=", "", "-", ""],
                     ["", "=", "", "-", ""],
                     ["", "=", "", "-", ""]
                     ]
        array = ini_array if not array else array
        model = MyPartEditorTableModel(array, self.partitioneditor.header, parent=self.partitioneditor)
        model.dataChanged.connect(self.partitioneditor.sortGenes)
        self.partitioneditor.tableView_partition.setModel(model)
        self.partitioneditor.ctrlResizedColumn()  # 先执行一次改变列的宽度
        self.partitioneditor.exec_()

    def judgeMergeOn(self, bool_):
        pass
        # if bool_ and not self.


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = ModelFinder()
    ui.show()
    sys.exit(app.exec_())
