#!/usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import multiprocessing
import re
import shutil

import datetime
import signal
import subprocess
import uuid

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from src.factory import Factory, WorkThread, Parsefmt
from uifiles.Ui_IQ_TREE import Ui_IQTREE
import inspect
import os
import sys
import traceback
import platform


class IQTREE(QDialog, Ui_IQTREE, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    iq_tree_exception = pyqtSignal(str)  # 定义所有类都可以使用的信号
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
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
            autoModelFile=["", None],
            workPath=None,
            focusSig=None,
            IQ_exe=None,
            workflow=False,
            parent=None):
        super(IQTREE, self).__init__(parent)
        self.parent = parent
        self.function_name = "IQ-TREE"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig if focusSig else pyqtSignal(
            str)  # 为了方便workflow
        self.workflow = workflow
        self.iqtree_exe = IQ_exe
        self.autoMFPath = autoMFPath
        self.autoModelFile = autoModelFile
        self.interrupt = False
        self.setupUi(self)
        # self.have_part_model = 1
        self.checkBox_8.stateChanged.connect(self.switchPart)
        state = 2 if self.checkBox_8.isChecked() else 0
        self.switchPart(state)
        # 保存设置
        if not workflow:
            self.iqtree_settings = QSettings(
                self.thisPath + '/settings/iqtree_settings.ini', QSettings.IniFormat)
        else:
            self.iqtree_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.iqtree_settings.beginGroup("Workflow")
            self.iqtree_settings.beginGroup("temporary")
            self.iqtree_settings.beginGroup('IQ-TREE')
        # File only, no fallback to registry or or.
        self.iqtree_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.lineEdit_3.installEventFilter(self)
        self.comboBox_3.activated[str].connect(self.controlCodonTable)
        self.comboBox_8.currentIndexChanged[str].connect(self.ctrlBootstrap)
        self.comboBox_7.currentIndexChanged[str].connect(self.ctrlModel)
        self.ctrlBootstrap(self.comboBox_8.currentText())
        self.ctrlModel(self.comboBox_7.currentText())
        self.spinBox_3.valueChanged.connect(self.judgeBootStrap) # 判断不同模式下的bootstrap
        # 恢复用户的设置
        self.guiRestore()
        self.judgePFresults() #判断partitionfinder2是否有结果
        # 判断IQTREE的版本，以决定要不要加新功能
        self.version = ""
        version_worker = WorkThread(
            lambda : self.factory.get_version("IQ-TREE", self),
            parent=self)
        version_worker.finished.connect(self.switchNewOptions)
        version_worker.start()
        if self.autoModelFile[1]:
            self.autoModel()
        self.exception_signal.connect(self.popupException)
        self.iq_tree_exception.connect(self.popup_IQTREE_exception)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.logGuiSig.connect(self.addText2Log)
        self.comboBox_4.installEventFilter(self)
        self.log_gui = self.gui4Log()
        # self.lineEdit.installEventFilter(self)
        self.checkBox_2.stateChanged.connect(self.ctrlCategory)
        self.checkBox_3.stateChanged.connect(self.ctrlCategory)
        self.checkBox_2.toggled.connect(self.ctrl_ratehet)
        self.ctrlCategory(0)
        self.lineEdit_3.setLineEditNoChange(True)
        self.comboBox_11.installEventFilter(self)
        self.comboBox_11.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        self.comboBox_11.itemRemovedSig.connect(self.judgeFileNum)
        self.comboBox_10.activated[str].connect(self.ctrlOutgroupLable)
        self.comboBox_10.setTopText()
        # self.lineEdit.deleteFile.clicked.connect(
        #     self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        # self.lineEdit.autoDetectSig.connect(self.popupAutoDec)
        self.lineEdit_3.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        # 初始化codon table的选择
        self.controlCodonTable(self.comboBox_3.currentText())
        # 给开始按钮添加菜单
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        action = QAction(QIcon(":/picture/resourses/terminal-512.png"), "View | Edit command", menu,
                         triggered=self.showCMD)
        self.work_action = QAction(QIcon(":/picture/resourses/work.png"), "", menu)
        self.work_action.triggered.connect(lambda: self.factory.swithWorkPath(self.work_action, parent=self))
        self.dir_action = QAction(QIcon(":/picture/resourses/folder.png"), "Output Dir: ", menu)
        self.dir_action.triggered.connect(lambda :self.factory.set_direct_dir(self.dir_action, self))
        menu.addAction(action)
        menu.addAction(self.work_action)
        menu.addAction(self.dir_action)
        self.pushButton.toolButton.setMenu(menu)
        self.pushButton.toolButton.menu().installEventFilter(self)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-11-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-11-1-Brief-example"
        self.label.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)

    @pyqtSlot()
    def on_pushButton_clicked(self, cmd_directly=False):
        """
        execute program
        """
        self.command = self.getCMD() if not cmd_directly else cmd_directly[0]
        self.cmd_directly = cmd_directly
        if self.command:
            # self.IQ_popen = self.factory.init_popen(self.command)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        alignment file
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input alignment file", filter="Phylip Format(*.phy *.phylip);;Fasta Format(*.fas *.fasta);;Nexus Format(*.nex *.nexus *.nxs);;Clustal Format(*.aln)")
        if fileNames[0]:
            self.input(fileNames[0])

    @pyqtSlot()
    def on_pushButton_22_clicked(self):
        """
        partition file
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input partition file", filter="All(*);;")
        if fileName[0]:
            base = os.path.basename(fileName[0])
            self.lineEdit_3.setText(base)
            self.lineEdit_3.setToolTip(fileName[0])
            # self.comboBox_5.setEnabled(True)

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
                    "<p style='line-height:25px; height:25px'>IQ-TREE is still running, terminate it?</p>",
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
            else:
                reply = QMessageBox.Yes
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.IQ_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.IQ_popen.pid), signal.SIGTERM)
                    self.IQ_popen = None
                    self.interrupt = True
                except:
                    self.IQ_popen = None
                    self.interrupt = True
                if not self.workflow:
                    QMessageBox.information(
                        self,
                        "IQ-TREE",
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
                "IQ-TREE",
                "<p style='line-height:25px; height:25px'>IQ-TREE is running!</p>")
            return
        resultsPath = None
        ##choose work folder
        if os.path.exists(self.workPath + os.sep + "IQtree_results"):
            list_result_dirs = sorted([i for i in os.listdir(self.workPath + os.sep + "IQtree_results")
                                       if os.path.isdir(self.workPath + os.sep + "IQtree_results" + os.sep + i)],
                                      key=lambda x: os.path.getmtime(
                                          self.workPath + os.sep + "IQtree_results" + os.sep + x), reverse=True)
            if list_result_dirs:
                item, ok = QInputDialog.getItem(self, "Choose previous results",
                                                "Previous results:", list_result_dirs, 0, False)
                if ok and item:
                    resultsPath = self.workPath + os.sep + "IQtree_results" + os.sep + item
        else:
            QMessageBox.information(
                self,
                "IQ-TREE",
                "<p style='line-height:25px; height:25px'>No previous IQ-TREE analysis found in %s!</p>" % os.path.normpath(
                    self.workPath))
            return
        if not resultsPath: return
        has_cmd = False
        if os.path.exists(resultsPath + os.sep + "PhyloSuite_IQ-TREE.log"):
            with open(resultsPath + os.sep + "PhyloSuite_IQ-TREE.log", encoding="utf-8", errors='ignore') as f:
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
                "IQ-TREE",
                "<p style='line-height:25px; height:25px'>No IQ-TREE command found in %s!</p>" % os.path.normpath(
                    resultsPath))

    def run_command(self):
        try:
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "start",
                    None,
                    self.qss_file,
                    self])
            files = self.comboBox_11.fetchListsText()
            if hasattr(self, "cmd_directly") and self.cmd_directly:
                self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
                self.exportPath = self.factory.creat_dirs(self.workPath +
                                                          os.sep + "IQtree_results" + os.sep + self.output_dir_name)\
                                  if not self.cmd_directly[1] else self.cmd_directly[1]
                self.description = ""
                self.reference = "Nguyen, L.T., Schmidt, H.A., von Haeseler, A., Minh, B.Q., 2015. IQ-TREE: a fast and effective stochastic algorithm for estimating maximum-likelihood phylogenies. Mol. Biol. Evol. 32, 268-274.\n" \
                                 "Minh, B.Q., Nguyen, M.A., von Haeseler, A., 2013. Ultrafast approximation for phylogenetic bootstrap. Mol. Biol. Evol. 30, 1188-1195."
                ok = QMetaObject.invokeMethod(self, "fetchPopen",
                                              Qt.BlockingQueuedConnection, Q_RETURN_ARG(bool),
                                              Q_ARG(str, self.command))
                self.factory.emitCommands(self.logGuiSig, self.command)
                self.continue_IQ()
            elif len(files) == 1:
                if ("-safe" not in self.command) or (not hasattr(self, "exportPath")):
                    self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
                    self.exportPath = self.factory.creat_dirs(self.workPath +
                                                              os.sep + "IQtree_results" + os.sep + self.output_dir_name)
                ok1 = QMetaObject.invokeMethod(self, "rmvDir",
                                               Qt.BlockingQueuedConnection, Q_RETURN_ARG(bool),
                                               Q_ARG(str, self.exportPath))
                if not ok1:
                    # 提醒是否删除旧结果，如果用户取消，就不执行
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton,
                            self.progressBar,
                            "except",
                            self.exportPath,
                            self.qss_file,
                            self])
                    return
                # input
                inputFile = shutil.copy(files[0], self.exportPath)
                # partition 因为在这里创建输出文件夹，所以partition搬到这里
                partitionCMD = "-sp" if self.comboBox_5.currentText() == "Edge-unlinked" else "-spp"
                partFile = " %s \"%s\"" % (
                    partitionCMD, shutil.copy(self.lineEdit_3.toolTip(), self.exportPath)) if (
                    self.checkBox_8.isChecked() and self.lineEdit_3.toolTip()) else ""
                self.command = self.command.replace("-s inputFile", "-s \"%s\""%inputFile) + partFile
                ok = QMetaObject.invokeMethod(self, "fetchPopen",
                                          Qt.BlockingQueuedConnection, Q_RETURN_ARG(bool),
                                          Q_ARG(str, self.command))
                self.factory.emitCommands(self.logGuiSig, self.command)
                self.run_IQ(0, 100)
            else:
                each_pro = 100/len(files)
                # gt_id = f"gene-tree-{uuid.uuid4()}"
                self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
                self.exportPath = self.factory.creat_dirs(self.workPath +
                                                          os.sep + "IQtree_results" + os.sep + self.output_dir_name)
                ok1 = QMetaObject.invokeMethod(self, "rmvDir",
                                               Qt.BlockingQueuedConnection, Q_RETURN_ARG(bool),
                                               Q_ARG(str, self.exportPath))
                if not ok1:
                    # 提醒是否删除旧结果，如果用户取消，就不执行
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton,
                            self.progressBar,
                            "except",
                            self.exportPath,
                            self.qss_file,
                            self])
                    return
                for num, i in enumerate(files):
                    if self.interrupt:
                        return
                    gene_tree_path = self.factory.creat_dirs(self.exportPath +
                                        os.sep + os.path.splitext(os.path.basename(i))[0])
                    # 创建一个文件作为单基因建树批次的标记（每一批要不一样的ID
                    # with open(f"{gene_tree_path}/{gt_id}", "w") as f:
                    #     f.write("This file is used as identifier")
                    # input
                    inputFile = shutil.copy(i, gene_tree_path)
                    command = self.command.replace("-s inputFile", "-s \"%s\"" % inputFile)
                    ok = QMetaObject.invokeMethod(self, "fetchPopen",
                                                  Qt.BlockingQueuedConnection, Q_RETURN_ARG(bool),
                                                  Q_ARG(str, command))
                    self.factory.emitCommands(self.logGuiSig, command)
                    self.run_IQ(each_pro*num, each_pro, path=gene_tree_path)
                trees = glob.glob(f"{self.exportPath}/*/*.treefile")
                all_tree_contents = []
                for tree in trees:
                    with open(tree) as f:
                        all_tree_contents.append(f.read())
                with open(f"{self.exportPath}/all_gene_trees.nwk", "w") as f:
                    f.write("".join(all_tree_contents))
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                           self.time_used)

            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(self.description + "\n\nIf you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n"
                        "If you use IQ-TREE and Ultrafast bootstrap, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
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
                    self.workflow_finished.emit("IQ-TREE finished")
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
        self.iqtree_settings.setValue('size', self.size())
        # self.iqtree_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.iqtree_settings.setValue(name, index)
            # elif isinstance(obj, QLineEdit):
            #     text = obj.text()
            #     tooltip = obj.toolTip()
            #     self.iqtree_settings.setValue(name, [text, tooltip])
            elif isinstance(obj, QSpinBox):
                value = obj.value()
                self.iqtree_settings.setValue(name, value)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.iqtree_settings.setValue(name, float_)
            elif isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.iqtree_settings.setValue(name, state)

    def guiRestore(self):

        # Restore geometry
        height = 700 if platform.system().lower() == "darwin" else 568
        size = self.factory.judgeWindowSize(self.iqtree_settings, 859, height)
        self.resize(size)
        self.factory.centerWindow(self)
        # self.move(self.iqtree_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                obj.setMaxVisibleItems(10)
                if name == "comboBox_6":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = ["AUTO"] + [str(i + 1) for i in range(cpu_num)]
                    index = self.iqtree_settings.value(name, "0")
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
                    ini_models = ["Auto", "***Binary***", "JC2", "GTR2", "***DNA***", "JC (JC69)", "F81", "K80 (K2P)", "HKY (HKY85)",
                                  "TNe (TN93e)",  "TN (TN93)",  "K81 (K3P)",  "K81u (K3Pu)",  "TPM2",  "TPM2u",  "TPM3",  "TPM3u",  "TIMe",
                                  "TIM",  "TIM2e",  "TIM2",  "TIM3e",  "TIM3",  "TVMe",  "TVM",  "SYM",  "GTR",
                                  "***Protein***", "Blosum62",  "cpREV",  "Dayhoff",  "DCMut",  "FLU",  "HIVb",
                                  "HIVw",  "JTT",  "JTTDCMut",  "LG",  "mtART",  "mtMAM",  "mtREV",
                                  "mtZOA",  "PMB",  "rtREV",  "VT",  "WAG", 'mtVer', 'mtMet', 'mtInv', "***Mixture model***",
                                  "LG4M",  "LG4X",  "JTT+CF4",  "C10",  "C20",  "EX2",  "EX3",  "EHO",
                                  "UL2",  "UL3",  "EX_EHO", "***Codon***", "GY",  "MG",  "MGK",  "GY0K",
                                  "GY1KTS",  "GY1KTV",  "GY2K",  "MG1KTS",  "MG1KTV",  "MG2K",  "KOSI07",
                                  "SCHN05", "***Morphology***", "MK", "ORDERED"]
                    index = self.iqtree_settings.value(name, "0")
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
                    obj.model().item(1).setSelectable(False)
                    obj.model().item(4).setSelectable(False)
                    obj.model().item(27).setSelectable(False)
                    obj.model().item(49).setSelectable(False)
                    obj.model().item(61).setSelectable(False)
                    obj.model().item(74).setSelectable(False)
                elif name == "comboBox_11":
                    self.input(self.autoMFPath)
                elif name == "comboBox_10":
                    pass
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.iqtree_settings.value(name, "0")
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
            # elif isinstance(obj, QLineEdit):
            #     value = self.iqtree_settings.value(name, ini_value)
            #     obj.setValue(int(value))
            elif isinstance(obj, QSpinBox):
                ini_value = obj.value()
                value = self.iqtree_settings.value(name, ini_value)
                obj.setValue(int(value))
            elif isinstance(obj, QDoubleSpinBox):
                ini_float_ = obj.value()
                float_ = self.iqtree_settings.value(name, ini_float_)
                obj.setValue(float(float_))
            elif isinstance(obj, QCheckBox):
                state = "true" if obj.isChecked() else "false"
                value = self.iqtree_settings.value(
                    name, state)  # get stored value from registry
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
                "IQ-TREE",
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
                "IQ-TREE",
                "<p style='line-height:25px; height:25px'>%s</p>" % text)
            if "Show log" in text:
                self.on_pushButton_9_clicked()
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])

    def closeEvent(self, event):
        self.guiSave()
        self.log_gui.close()  # 关闭子窗口
        self.closeSig.emit("IQ-TREE", self.fetchWorkflowSetting())
        # 取消选中文字
        self.checkBox_8.setFocus()
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
            self.ui_closeSig.emit("IQ-TREE")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            # print(self.isRunning())
            reply = QMessageBox.question(
                self,
                "IQ-TREE",
                "<p style='line-height:25px; height:25px'>IQ-TREE is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.IQ_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.IQ_popen.pid), signal.SIGTERM)
                    self.IQ_popen = None
                    self.interrupt = True
                except:
                    self.IQ_popen = None
                    self.interrupt = True
            else:
                event.ignore()

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
                if name == "comboBox_11":
                    files = [i for i in files if os.path.splitext(i)[1].upper() in [".PHY", ".PHYLIP", ".FAS", ".FASTA", ".NEX", ".NEXUS", ".NXS", ".ALN"]]
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
                if name == "lineEdit_3":
                    base = os.path.basename(files[0])
                    self.lineEdit_3.setText(base)
                    self.lineEdit_3.setToolTip(files[0])
                    # self.comboBox_5.setEnabled(True)
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
        # 其他情况会返回系统默认的事件处理方法。
        return super(IQTREE, self).eventFilter(obj, event)  # 0

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of IQ-TREE:")
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
            with open(self.exportPath + os.sep + "PhyloSuite_IQ-TREE.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "IQ-TREE", "log", "text Format(*.txt)")
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
        return hasattr(self, "IQ_popen") and self.IQ_popen and not self.interrupt

    def controlCodonTable(self, text):
        if text in ["Codon", "DNA-->AA"]:
            self.comboBox_9.setEnabled(True)
        else:
            self.comboBox_9.setEnabled(False)

    def run_IQ(self, base, proportion, path=None):
        isStandBP = True if self.bootstrap_method == "Standard" else False
        isAutoModel = True if self.model_text == "Auto" else False
        rgx_1st = re.compile(r"^\*\*\*\*  TOTAL")  # 1%
        rgx_2nd = re.compile(
            r"\| {13}INITIALIZING CANDIDATE TREE SET {22}\|")  # 9%
        rgx_3rd = re.compile(
            r"Computing log-likelihood of \d+? initial trees \.\.\. .+? seconds")  # 15%
        rgx_4th = re.compile(r"^Iteration (\d+) \/ ")  # 60%
        rgx_5th = re.compile(r"BEST SCORE FOUND \: ")  # 10%
        rgx_finished = re.compile(r"^Date and Time:")  # 5%
        rgx_test_model = re.compile(r"^ModelFinder will test (\d+) \w+ models")
        rgx_repl_num = re.compile(
            r"===> START BOOTSTRAP REPLICATE NUMBER (\d+)")
        rgx_repl_last = re.compile(
            r"===> START ANALYSIS ON THE ORIGINAL ALIGNMENT")
        rgx_part_model = re.compile(r"^Loading (\d+) partitions\.\.\.")
        totleModels = None
        totlePartitions_2 = None
        list_partition_names = []  # 存放partition的名字
        num = 0  # partition出现的次数，当num等于2倍partition的个数的时候，就完成
        if isStandBP:
            bp_num = self.spinBox_3.value()
            # 每个BP所占的比例,多一个是因为最后会多一次重复
            bp_each_count = 96 / \
                (bp_num + 1) if not isAutoModel else 86 / (bp_num + 1)
            bp_current_count = 0
            # value = 0
        is_error = False ##判断是否出了error
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = self.IQ_popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = self.IQ_popen.stdout.readline().decode("gbk", errors="ignore")
                if out_line == "" and self.IQ_popen.poll() is not None:
                    break
                if isStandBP and isAutoModel:
                    list_outline = out_line.strip().split()
                    if rgx_1st.search(out_line):
                        self.progressSig.emit(base + 1*proportion/100)
                        self.workflow_progress.emit(base + 1*proportion/100)
                    # model selection
                    elif rgx_test_model.search(out_line):
                        totleModels = int(
                            rgx_test_model.search(out_line).group(1))
                    elif totleModels and (len(list_outline) == 7) and list_outline[0].isdigit() and list_outline[3].isdigit():
                        model_num = int(list_outline[0])
                        self.progressSig.emit(base + (1 + model_num * 10 / totleModels)*proportion/100)
                        self.workflow_progress.emit(base + (1 + model_num * 10 / totleModels)*proportion/100)
                    # partition
                    elif rgx_part_model.search(out_line):
                        totlePartitions_2 = 2 * \
                            int(rgx_part_model.search(out_line).group(1))
                    elif totlePartitions_2 and re.search(r"^\d", out_line) and len(
                            out_line.strip().split("\t")) == 8:
                        # partition模式, Subset     Type    Seqs    Sites   Infor
                        # Invar   Model   Name
                        list_partition_names.append(
                            out_line.strip().split("\t")[-1])
                    elif list_partition_names and totlePartitions_2 and (num <= totlePartitions_2) and re.search(
                            r"^ +\d+|^Optimizing", out_line):
                        for i in list_partition_names:
                            if i in out_line:
                                num += 1
                                self.progressSig.emit(base +
                                    (1 + num * 10 / totlePartitions_2)*proportion/100)
                                self.workflow_progress.emit(base +
                                    (1 + num * 10 / totlePartitions_2) * proportion / 100)
                    # bootstrap procedure
                    elif rgx_repl_num.search(out_line):
                        bp_current_num = int(
                            rgx_repl_num.search(out_line).group(1))
                        bp_current_count = 11 + \
                            bp_each_count * (bp_current_num - 1)
                    elif rgx_repl_last.search(out_line):
                        bp_current_count = 11 + bp_each_count * bp_num
                    elif rgx_2nd.search(out_line):
                        value = bp_current_count + 8 * bp_each_count / 100
                        self.progressSig.emit(base + value*proportion/100)
                        self.workflow_progress.emit(base + value*proportion/100)
                    elif rgx_3rd.search(out_line):
                        value = bp_current_count + 25 * bp_each_count / 100
                        self.progressSig.emit(base + value*proportion/100)
                        self.workflow_progress.emit(base + value*proportion/100)
                    elif rgx_4th.search(out_line):
                        current_iter = int(rgx_4th.search(out_line).group(1))
                        if current_iter <= 100:  # current_iter大于100的不考虑
                            value = bp_current_count + 25 * bp_each_count / 100 + \
                                (65 * current_iter * bp_each_count) / \
                                (100 * 100)
                            self.progressSig.emit(base + value*proportion/100)
                            self.workflow_progress.emit(base + value*proportion/100)
                    elif rgx_5th.search(out_line):
                        value = bp_current_count + bp_each_count
                        self.progressSig.emit(base + value*proportion/100)
                        self.workflow_progress.emit(base + value*proportion/100)
                    # finish
                    elif rgx_finished.search(out_line):
                        self.progressSig.emit(base + proportion)
                        self.workflow_progress.emit(base + proportion)
                    # print(out_line, value)
                elif isStandBP:
                    if rgx_1st.search(out_line):
                        self.progressSig.emit(base + 1*proportion/100)
                        self.workflow_progress.emit(base + 1*proportion/100)
                    elif rgx_repl_num.search(out_line):
                        bp_current_num = int(
                            rgx_repl_num.search(out_line).group(1))
                        bp_current_count = 1 + \
                            bp_each_count * (bp_current_num - 1)
                    elif rgx_repl_last.search(out_line):
                        bp_current_count = 1 + bp_each_count * bp_num
                    elif rgx_2nd.search(out_line):
                        value = bp_current_count + 8 * bp_each_count / 100
                        self.progressSig.emit(base + value*proportion/100)
                        self.workflow_progress.emit(base + value*proportion/100)
                    elif rgx_3rd.search(out_line):
                        value = bp_current_count + 25 * bp_each_count / 100
                        self.progressSig.emit(base + value*proportion/100)
                        self.workflow_progress.emit(base + value*proportion/100)
                    elif rgx_4th.search(out_line):
                        current_iter = int(rgx_4th.search(out_line).group(1))
                        if current_iter <= 100:  # current_iter大于100的不考虑
                            value = bp_current_count + 25 * bp_each_count / 100 + \
                                (65 * current_iter * bp_each_count) / \
                                (100 * 100)
                            self.progressSig.emit(base + value*proportion/100)
                            self.workflow_progress.emit(base + value*proportion/100)
                    elif rgx_5th.search(out_line):
                        value = bp_current_count + bp_each_count
                        self.progressSig.emit(base + value*proportion/100)
                        self.workflow_progress.emit(base + value*proportion/100)
                    # finish
                    elif rgx_finished.search(out_line):
                        self.progressSig.emit(base + proportion)
                        self.workflow_progress.emit(base + proportion)
                    # print(out_line, value)
                elif isAutoModel:
                    list_outline = out_line.strip().split()
                    if rgx_1st.search(out_line):
                        self.progressSig.emit(base + 1*proportion/100)
                        self.workflow_progress.emit(base + 1*proportion/100)
                    # model selection
                    elif rgx_test_model.search(out_line):
                        totleModels = int(
                            rgx_test_model.search(out_line).group(1))
                    elif totleModels and (len(list_outline) == 7) and list_outline[0].isdigit() and list_outline[3].isdigit():
                        model_num = int(list_outline[0])
                        self.progressSig.emit(base + (1 + model_num * 20 / totleModels)*proportion/100)
                        self.workflow_progress.emit(
                            base + (1 + model_num * 20 / totleModels) * proportion / 100)
                    # partition
                    elif rgx_part_model.search(out_line):
                        totlePartitions_2 = 2 * \
                            int(rgx_part_model.search(out_line).group(1))
                    elif totlePartitions_2 and re.search(r"^\d", out_line) and len(
                            out_line.strip().split("\t")) == 8:
                        # partition模式, Subset     Type    Seqs    Sites   Infor
                        # Invar   Model   Name
                        list_partition_names.append(
                            out_line.strip().split("\t")[-1])
                    elif list_partition_names and totlePartitions_2 and (num <= totlePartitions_2) and re.search(
                            r"^ +\d+|^Optimizing", out_line):
                        for i in list_partition_names:
                            if i in out_line:
                                num += 1
                                self.progressSig.emit(
                                    base + (1 + num * 20 / totlePartitions_2)*proportion/100)
                                self.workflow_progress.emit(
                                    base + (1 + num * 20 / totlePartitions_2) * proportion / 100)
                    # tree reconstruction
                    elif rgx_2nd.search(out_line):
                        self.progressSig.emit(base + 27*proportion/100)
                        self.workflow_progress.emit(base + 27*proportion/100)
                    elif rgx_3rd.search(out_line):
                        self.progressSig.emit(base + 37*proportion/100)
                        self.workflow_progress.emit(base + 37*proportion/100)
                    elif rgx_4th.search(out_line):
                        current_iter = int(rgx_4th.search(out_line).group(1))
                        if current_iter <= 100:  # current_iter大于100的不考虑
                            self.progressSig.emit(base + (37 + 50 * current_iter / 100)*proportion/100)
                            self.workflow_progress.emit(
                                base + (37 + 50 * current_iter / 100) * proportion / 100)
                    elif rgx_5th.search(out_line):
                        self.progressSig.emit(base + 95*proportion/100)
                        self.workflow_progress.emit(base + 95*proportion/100)
                    elif rgx_finished.search(out_line):
                        self.progressSig.emit(base + proportion)
                        self.workflow_progress.emit(base + proportion)
                else:
                    if rgx_1st.search(out_line):
                        self.progressSig.emit(base + 1*proportion/100)
                        self.workflow_progress.emit(base + 1*proportion/100)
                    elif rgx_2nd.search(out_line):
                        self.progressSig.emit(base + 10*proportion/100)
                        self.workflow_progress.emit(base + 10*proportion/100)
                    elif rgx_3rd.search(out_line):
                        self.progressSig.emit(base + 25*proportion/100)
                        self.workflow_progress.emit(base + 25*proportion/100)
                    elif rgx_4th.search(out_line):
                        current_iter = int(rgx_4th.search(out_line).group(1))
                        self.progressSig.emit(base + (25 + 60 * current_iter / 100)*proportion/100)
                        self.workflow_progress.emit(
                            base + (25 + 60 * current_iter / 100) * proportion / 100)
                    elif rgx_5th.search(out_line):
                        self.progressSig.emit(base + 95*proportion/100)
                        self.workflow_progress.emit(base + 95*proportion/100)
                    elif rgx_finished.search(out_line):
                        self.progressSig.emit(base + proportion)
                        self.workflow_progress.emit(base + proportion)
                text = out_line.strip() if out_line != "\n" else "\n"
                self.logGuiSig.emit(text)
                if re.search(r"^ERROR", out_line):
                    is_error = True
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
        self.IQ_popen = None

    def continue_IQ(self):
        is_error = False  ##判断是否出了error
        self.progressSig.emit(99999)
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = self.IQ_popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = self.IQ_popen.stdout.readline().decode("gbk", errors="ignore")
                if out_line == "" and self.IQ_popen.poll() is not None:
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
        self.IQ_popen = None

    def clear_lineEdit(self):
        sender = self.sender()
        lineEdit = sender.parent()
        lineEdit.setText("")
        lineEdit.setToolTip("")

    def ctrlBootstrap(self, text):
        if text == "None":
            for i in [self.spinBox_3, self.doubleSpinBox, self.spinBox_4, self.checkBox_5, self.label_35, self.label_37, self.label_36]:
                i.setEnabled(False)
        elif text == "Ultrafast":
            for i in [self.spinBox_3, self.doubleSpinBox, self.spinBox_4, self.checkBox_5, self.label_35, self.label_37, self.label_36]:
                i.setEnabled(True)
            self.spinBox_3.setMinimum(1000)
            if self.spinBox_3.value() < 1000:
                self.spinBox_3.setValue(5000)
        elif text == "Standard":
            self.spinBox_3.setEnabled(True)
            self.checkBox_5.setEnabled(True)
            self.label_35.setEnabled(True)
            self.doubleSpinBox.setEnabled(False)
            self.spinBox_4.setEnabled(False)
            self.label_36.setEnabled(False)
            self.label_37.setEnabled(False)
            self.spinBox_3.setMinimum(1)
            if self.spinBox_3.value() > 1000:
                self.spinBox_3.setValue(1000)
            # self.spinBox_3.setValue(100)

    def ctrlModel(self, text):
        if text == "Auto":
            for i in [self.spinBox, self.checkBox_3, self.checkBox_4,
                      self.comboBox_4, self.label_29, self.label_28, self.label_26]:
                i.setEnabled(False)
            # # 如果是partition模式，提醒一下
            # if self.isPartitionCalculated() and (not self.workflow):
            #     QMessageBox.information(
            #         self,
            #         "PhyloSuite",
            #         "<p style='line-height:25px; height:25px'>When select \"Auto\", IQ-TREE will calculate the best-fit partition model by itself."
            #         " If you intend to use the partition model in the partition file, please choose a non-\"Auto\" model!</p>")
        else:
            self.label_26.setEnabled(True)
            self.comboBox_4.setEnabled(True)
            self.ctrlCategory(0)
            if not self.checkBox_2.isChecked():
                self.checkBox_3.setEnabled(True)
                self.checkBox_4.setEnabled(True)
                self.label_29.setEnabled(True)
        if text in ["GY",  "MG",  "MGK",  "GY0K", "GY1KTS",  "GY1KTV",
                    "GY2K",  "MG1KTS",  "MG1KTV",  "MG2K",  "KOSI07", "SCHN05"]:
            self.comboBox_3.setCurrentText("Codon")

    def ctrlCategory(self, value):
        if self.comboBox_7.currentText() != "Auto" and (self.checkBox_3.isChecked() or self.checkBox_2.isChecked()):
            self.spinBox.setEnabled(True)
            self.label_28.setEnabled(True)
        else:
            self.spinBox.setEnabled(False)
            self.label_28.setEnabled(False)

    def autoModel(self):
        if self.autoModelFile[0] == "MB_MF_part":
            # model要选auto,而且也要导入partition文件，auto在ifFinished里面选好了
            with open(self.autoModelFile[1], encoding="utf-8", errors='ignore') as f:
                content = f.read()
            path = os.path.dirname(
                self.autoModelFile[1]) + os.sep + "IQ_partition.nex"
            with open(path, "w", encoding="utf-8") as f1:
                f1.write(
                    re.sub(r"(?s) +charpartition mymodels.+(?=end;)", "", content))
            self.lineEdit_3.setText(os.path.basename(path))
            self.lineEdit_3.setToolTip(path)
            self.checkBox_8.setChecked(True)
            self.comboBox_7.setCurrentIndex(0)  # 设为auto模式
        elif self.autoModelFile[0] == "MB_MF":
            self.comboBox_7.setCurrentIndex(0)  # 设为auto模式
        elif self.autoModelFile[0] == "CAT":
            # 从concatenation导入的
            with open(self.autoModelFile[1], encoding="utf-8", errors='ignore') as f:
                partition_txt = f.read()
            iq_partition = re.search(
                r"(?s)\*\*\*IQ-TREE style\*\*\*(.+?)[\*|$]", partition_txt).group(1).strip()
            path = os.path.dirname(
                self.autoModelFile[1]) + os.sep + "IQ_partition.txt"
            with open(path, "w", encoding="utf-8") as f1:
                f1.write(iq_partition)
            self.lineEdit_3.setText(os.path.basename(path))
            self.lineEdit_3.setToolTip(path)
        elif self.autoModelFile[0] == "mf_part_model":
            # 直接把mf_part_model的模型导入即可
            self.lineEdit_3.setText(os.path.basename(self.autoModelFile[1]))
            self.lineEdit_3.setToolTip(self.autoModelFile[1])
            self.checkBox_8.setChecked(True)
            # self.have_part_model = True  # 表明有partmodel的结果
        elif self.autoModelFile[0] == "PF":
            # partitionfinder的结果
            with open(self.autoModelFile[1], encoding="utf-8", errors='ignore') as f:
                content = f.read()
            path = os.path.dirname(
                self.autoModelFile[1]) + os.sep + "IQ_partition.nex"
            with open(path, "w", encoding="utf-8") as f1:
                f1.write(
                    re.search(r"(?s)character sets for IQtree.+?(\#nexus.+?end;)", content).group(1))
            self.lineEdit_3.setText(os.path.basename(path))
            self.lineEdit_3.setToolTip(path)
            self.checkBox_8.setChecked(True)
            # self.have_part_model = True  # 表明有partmodel的结果
        elif self.autoModelFile[0] == "MB_normal":
            ##普通模型, modelfinder选出来的所有模型
            f = self.factory.read_file(self.autoModelFile[1])
            content = f.read()
            f.close()
            rgx_model = re.compile(r"Best-fit model according to.+?\: (.+)")
            best_model = rgx_model.search(content).group(1)
            model_split = best_model.split("+")
            dict_1 = {"K81u": "K3Pu", "JC": "JC69", "K80": "K2P", "HKY": "HKY85",
                      "TNe": "TN93e", "TN": "TN93", "K81": "K3P"}
            model = model_split[0]
            if model in dict_1:
                rgx = r"%s \(%s\)" % (model, dict_1[model])
                index = self.comboBox_7.findText(rgx, Qt.MatchRegExp)
            elif model in list(dict_1.values()):
                rgx = r"%s \(%s\)" % (
                    list(dict_1.keys())[list(dict_1.values()).index(model)], model)
                index = self.comboBox_7.findText(rgx, Qt.MatchRegExp)
            else:
                index = self.comboBox_7.findText(model, Qt.MatchFixedString)
            if index >= 0:
                self.comboBox_7.setCurrentIndex(index)
            else:
                QMessageBox.information(
                    self,
                    "MrBayes",
                    "<p style='line-height:25px; height:25px'>Model invalid!</p>",
                    QMessageBox.Ok)
            dict_state_freq_rev = {"F": "Empirical (from data)", "FO": "ML-optimized",
                                   "F1X4": "Codon F1X4", "F3X4": "Codon F3X4"}
            has_F, has_R, has_G, has_I = False, False, False, False
            for i in model_split[1:]:
                if i == "F":
                    text = dict_state_freq_rev[i.upper()]
                    index = self.comboBox_4.findText(text, Qt.MatchFixedString)
                    if index >= 0:
                        self.comboBox_4.setCurrentIndex(index)
                        has_F = True
                elif "R" in i:
                    self.checkBox_2.setChecked(True)
                    if re.search(r"R(\d+)", i):
                        category = re.search(r"R(\d+)", i).group(1)
                    else:
                        category = "4"
                    self.spinBox.setValue(int(category))
                    has_R = True
                elif "G" in i:
                    self.checkBox_3.setChecked(True)
                    if re.search(r"G(\d+)", i):
                        category = re.search(r"G(\d+)", i).group(1)
                    else:
                        category = "4"
                    self.spinBox.setValue(int(category))
                    has_G = True
                elif "I" in i:
                    self.checkBox_4.setChecked(True)
                    has_I = True
            if not has_F:
                self.comboBox_4.setCurrentIndex(1)
            if not has_G:
                self.checkBox_3.setChecked(False)
            if not has_R:
                self.checkBox_2.setChecked(False)
            if not has_I:
                self.checkBox_4.setChecked(False)

    def workflow_input(self, MSA=None, model_file=None):
        self.comboBox_11.refreshInputs([])
        self.lineEdit_3.setText("")
        if MSA:
            self.input(MSA)
        self.autoModelFile = model_file
        self.judgePFresults() #判断partitionfinder2是否有结果
        if model_file[1]:
            self.autoModel()

    def ctrl_ratehet(self, bool_):
        if (not bool_) and self.comboBox_7.currentText() != "Auto":
            self.label_29.setEnabled(True)
            self.checkBox_3.setEnabled(True)
            self.checkBox_4.setEnabled(True)
        else:
            self.label_29.setEnabled(False)
            self.checkBox_3.setEnabled(False)
            self.checkBox_4.setEnabled(False)

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("IQ-TREE", self.workPath, self.auto_popSig, self)

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
            input_MSA, model = widget.autoInputs
            self.workflow_input(input_MSA, model)

    def fetchWorkflowSetting(self):
        '''* if partition mode, partition style:
          * seq type
          * code table (if codon mode)
          * models: auto detect from last step
          * rate heter (灰色的时候就不写， +I+G与+R选其一):
          * rate category
          * state freq
          * bootstrap, number
          * if do SH, replicates'''
        settings = '''<p class="title">***IQ-TREE***</p>'''
        ifPartition = "Yes" if self.checkBox_8.isChecked() else "No"
        settings += '<p>Partition mode: <a href="self.IQ_TREE_exe' \
                    ' factory.highlightWidgets(x.checkBox_8)">%s</a></p>' % ifPartition
        if ifPartition == "Yes":
            partStyle = self.comboBox_5.currentText()
            settings += '<p>Partition style: <a href="self.IQ_TREE_exe comboBox_5.showPopup()' \
                        ' factory.highlightWidgets(x.comboBox_5)">%s</a></p>' % partStyle
        seq_type = self.comboBox_3.currentText()
        settings += '<p>Sequence type: <a href="self.IQ_TREE_exe comboBox_3.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_3)">%s</a></p>' % seq_type
        if seq_type == "Codon":
            code_table = self.comboBox_9.currentText()
            settings += '<p>Code table: <a href="self.IQ_TREE_exe comboBox_9.showPopup()' \
                        ' factory.highlightWidgets(x.comboBox_9)">%s</a></p>' % code_table
        if self.comboBox_7.currentText() == "Auto":
            settings += '<p>Models: <a href="self.IQ_TREE_exe comboBox_7.showPopup()' \
                ' factory.highlightWidgets(x.comboBox_7)">Auto <span style="font-weight:600; color:green;">(calculate the best-fit model and reconstruct phylogeny)</span></a></p>'
        else:
            settings += '<p>Models: <a href="self.IQ_TREE_exe comboBox_7.showPopup()' \
                ' factory.highlightWidgets(x.comboBox_7)"><span style="font-weight:600; color:green;">auto detect from previous step</span></a></p>'
        # if self.label_29.isEnabled():
        #     list_addition_models = []
        #     if self.checkBox_3.isChecked():
        #         list_addition_models.append("Discrete Gamma model [+G]")
        #     if self.checkBox_4.isChecked():
        #         list_addition_models.append("Invariable site [+I]")
        #     if list_addition_models:
        #         settings += '<p>Rate heterogeneity: <a href="self.IQ_TREE_exe' \
        #                     ' factory.highlightWidgets(x.checkBox_3,x.checkBox_4)">%s</a></p>' % ", ".join(list_addition_models)
        if self.comboBox_7.currentText() == "Auto" and self.checkBox_2.isChecked():
            settings += '<p>FreeRate heterogeneity [+R]: <a href="self.IQ_TREE_exe' \
                        ' factory.highlightWidgets(x.checkBox_2)">Yes</a></p>'
        # if self.label_28.isEnabled():
        #     category = self.spinBox.value()
        #     settings += '<p>Rate categories: <a href="self.IQ_TREE_exe spinBox.setFocus() spinBox.selectAll()' \
        #                 ' factory.highlightWidgets(x.spinBox)">%s</a></p>' % category
        # if self.label_26.isEnabled():
        #     state_freq = self.comboBox_4.currentText()
        #     settings += '<p>State frequencies: <a href="self.IQ_TREE_exe comboBox_4.showPopup()' \
        #                 ' factory.highlightWidgets(x.comboBox_4)">%s</a></p>' % state_freq
        threads = self.comboBox_6.currentText()
        settings += '<p>Threads: <a href="self.IQ_TREE_exe comboBox_6.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_6)">%s</a></p>' % threads
        bootstrap = self.comboBox_8.currentText()
        settings += '<p>Bootstrap: <a href="self.IQ_TREE_exe comboBox_8.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_8)">%s</a></p>' % bootstrap
        bp_num = self.spinBox_3.value()
        settings += '<p>Number of bootstrap: <a href="self.IQ_TREE_exe spinBox_3.setFocus() spinBox_3.selectAll()' \
                    ' factory.highlightWidgets(x.spinBox_3)">%s</a></p>' % bp_num
        ifSH_test = "Yes" if self.checkBox_6.isChecked() else "No"
        settings += '<p>Do a SH-aLRT branch test: <a href="self.IQ_TREE_exe' \
                    ' factory.highlightWidgets(x.checkBox_6)">%s</a></p>' % ifSH_test
        if ifSH_test == "Yes":
            replicate = self.spinBox_5.value()
            settings += '<p>Replicates of SH-aLRT: <a href="self.IQ_TREE_exe spinBox_5.setFocus() spinBox_5.selectAll()' \
                        ' factory.highlightWidgets(x.spinBox_5)">%s</a></p>' % replicate
        return settings

    def showEvent(self, event):
        QTimer.singleShot(100, lambda: self.showSig.emit(self))

    def isFileIn(self):
        return self.comboBox_11.count()

    def switchPart(self, state):
        # self.have_part_model = state
        if state:
            if not self.workflow:
                self.lineEdit_3.setEnabled(True)
                self.pushButton_22.setEnabled(True)
            self.groupBox.setVisible(False)
        else:
            if not self.workflow:
                self.lineEdit_3.setEnabled(False)
                self.pushButton_22.setEnabled(False)
            self.groupBox.setVisible(True)

    def getCMD(self):
        alignments = self.isFileIn()
        if alignments:
            # 有数据才执行
            self.interrupt = False
            dict_seq = {"DNA": "DNA", "Protein": "AA", "Codon": "CODON", "Binary": "BIN", "Morphology": "MORPH",
                        "DNA-->AA": "NT2AA"}
            seqType = " -st %s" % dict_seq[
                self.comboBox_3.currentText()] if self.comboBox_3.currentText() != "Auto detect" else ""
            codon_table_index = self.comboBox_9.currentText().split(" ")[0]
            seqType = seqType + \
                codon_table_index if seqType in [
                    " -st CODON", " -st NT2AA"] else seqType
            # partitionCMD = "-sp" if self.comboBox_5.currentText() == "Edge-unlinked" else "-spp"
            # partFile = " %s %s" % (
            #     partitionCMD, shutil.copy(self.lineEdit_3.toolTip(), self.exportPath)) if (
            #     self.checkBox_8.isChecked() and self.lineEdit_3.toolTip() and self.lineEdit_3.isEnabled()) else ""
            # model
            self.model_text = self.comboBox_7.currentText().split(" ")[0]
            if self.isPartitionChecked():
                # if not self.workflow:
                #     QMessageBox.information(
                #         self,
                #         "IQ-TREE",
                #         "<p style='line-height:25px; height:25px'>As you selected \"Partition Mode\", "
                #         "\"Models\" argument will be ignored!</p>")
                if self.isPartitionCalculated():
                    # 其他分区软件计算好模型了
                    model = ""
                else:
                    # 计算分区模型，然后建树
                    model = " -m TESTNEWMERGE" if self.checkBox_2.isChecked() else " -m TESTMERGE"
            elif self.model_text == "Auto":
                model = " -m TESTNEW" if self.checkBox_2.isChecked() else " -m TEST"
                # if self.checkBox_2.isChecked():
                #     if self.checkBox_8.isChecked() and self.lineEdit_3.toolTip() and self.lineEdit_3.isEnabled():  # partition
                #         # 确保勾选了partition以及输入了文件
                #         model = " -m TESTNEWMERGE"
                #     else:
                #         model = " -m TESTNEW"
                # else:
                #     if self.checkBox_8.isChecked() and self.lineEdit_3.toolTip() and self.lineEdit_3.isEnabled():  # partition
                #         model = " -m TESTMERGE"
                #     else:
                #         model = " -m TEST"
                        # auto_model = "TESTNEW" if self.checkBox_2.isChecked() else "TEST"
                        # model = " -m %s"%auto_model
            else:
                dict_state_freq = {"Empirical (from data)": "F", "AA model (from matrix)": "",
                                   "ML-optimized": "FO", "Codon F1X4": "F1X4", "Codon F3X4": "F3X4"}
                if self.checkBox_2.isChecked():
                    # +R
                    freeRate = "+R%d" % self.spinBox.value()
                    state_freq = "+%s" % dict_state_freq[self.comboBox_4.currentText()] if dict_state_freq[
                        self.comboBox_4.currentText()] else ""
                    model = " -m %s" % (self.model_text +
                                        freeRate + state_freq)
                else:
                    gamma = "+G%d" % self.spinBox.value() if self.checkBox_3.isChecked() else ""
                    invar = "+I" if self.checkBox_4.isChecked() else ""
                    state_freq = "+%s" % dict_state_freq[
                        self.comboBox_4.currentText()] if dict_state_freq[self.comboBox_4.currentText()] else ""
                    model = " -m %s" % (self.model_text +
                                        invar + gamma + state_freq)
            model_final = model + \
                "+ASC" if self.checkBox.isChecked() else model
            # branch support
            self.bootstrap_method = self.comboBox_8.currentText()
            if self.bootstrap_method == "Ultrafast":
                bp = " -bb %d" % self.spinBox_3.value()
                max_ter = " -nm %d" % self.spinBox_4.value() if self.spinBox_4.value() != 1000 else ""
                min_cc = " -bcor %.2f" % self.doubleSpinBox.value(
                ) if self.doubleSpinBox.value() != 0.99 else ""
                bootstrap = bp + max_ter + min_cc
            elif self.bootstrap_method == "Standard":
                bootstrap = " -b %d" % self.spinBox_3.value()
            else:
                bootstrap = ""
            SH_aLrt = " -alrt %d" % self.spinBox_5.value() if self.checkBox_6.isChecked() else ""
            abayes = " -abayes" if self.checkBox_7.isChecked() else ""
            wbt = " -wbt" if self.checkBox_5.isChecked() else ""
            branch_support = SH_aLrt + bootstrap + abayes + wbt
            # outgroup
            outgroups = [self.comboBox_10.itemText(i) for i in range(self.comboBox_10.count())
                         if self.comboBox_10.model().item(i).checkState() == Qt.Checked]
            outgroup = " -o " + ",".join(outgroups) if (self.checkBox_9.isChecked() and self.comboBox_10.isEnabled()
                      and outgroups) else ""
            # search parameter
            # pers = " -pers %.1f"%self.doubleSpinBox_2.value() if self.doubleSpinBox_2.value() != 0.5 else ""
            # numstop = " -numstop %d"%self.spinBox_2.value() if self.spinBox_2.value() != 100 else ""
            # search_par = pers + numstop
            # fasttree
            if self.checkBox_10.isVisible() and self.checkBox_10.isChecked():
                fasttree = " --fast"
            else:
                fasttree = ""
            threads = " -nt %s" % self.comboBox_6.currentText()
            command = f"\"{self.iqtree_exe}\" -s inputFile" + seqType + \
                model_final + branch_support + fasttree + outgroup + threads
            self.textEdit_log.clear()  # 清空
            # 描述
            if self.checkBox_8.isChecked() and self.lineEdit_3.toolTip() and self.lineEdit_3.isEnabled():
                # partition
                model_des = "under %s partition model" % self.comboBox_5.currentText()
            elif self.model_text == "Auto":
                model_des = "under the model automatically selected by IQ-TREE ('Auto' option in IQ-TREE)"
            else:
                model_des = "under the %s model" % model.replace(" -m ", "")
            AB_test = ", approximate Bayes test (Anisimova et al., 2011)" if self.checkBox_7.isChecked(
            ) else ""
            AB_test_ref = "\nAnisimova, M., Gil, M., Dufayard, J.F., Dessimoz, C., Gascuel, O., 2011. Survey of branch support methods demonstrates accuracy, power, and robustness of fast likelihood-based approximation schemes. Syst. Biol. 60, 685-699." if self.checkBox_7.isChecked() else ""
            SH = "%s, as well as the Shimodaira–Hasegawa–like approximate likelihood-ratio test (Guindon et al., 2010)" % AB_test if self.checkBox_6.isChecked(
            ) else ""
            sh_ref = "\nGuindon, S., Dufayard, J.F., Lefort, V., Anisimova, M., Hordijk, W., Gascuel, O., 2010. New algorithms and methods to estimate maximum-likelihood phylogenies: assessing the performance of PhyML 3.0. Syst. Biol. 59, 307-321." if self.checkBox_6.isChecked() else ""
            bootstrap_method_des = self.bootstrap_method.lower(
            ) + " (Minh et al., 2013)" if self.bootstrap_method.lower() == "ultrafast" else self.bootstrap_method.lower()
            bootstrap_method_ref = "\nMinh, B.Q., Nguyen, M.A., von Haeseler, A., 2013. Ultrafast approximation for phylogenetic bootstrap. Mol. Biol. Evol. 30, 1188-1195." if self.bootstrap_method.lower(
            ) == "ultrafast" else ""
            self.description = '''Maximum likelihood phylogenies were inferred using IQ-TREE v%s (Nguyen et al., 2015) %s for %d %s bootstraps%s.''' % (
                self.version,
                model_des,
                self.spinBox_3.value(),
                bootstrap_method_des,
                SH)
            self.reference = "Nguyen, L.T., Schmidt, H.A., von Haeseler, A., Minh, B.Q., 2015. IQ-TREE: a fast and effective stochastic algorithm for estimating maximum-likelihood phylogenies. Mol. Biol. Evol. 32, 268-274." + \
                AB_test_ref + sh_ref + bootstrap_method_ref
            return command
        else:
            QMessageBox.critical(
                self,
                "IQ-TREE",
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
            self.textEdit_cmd.textChanged.connect(self.judgeCmdText)
            gridLayout.addWidget(label, 0, 0, 1, 2)
            gridLayout.addWidget(self.textEdit_cmd, 1, 0, 1, 2)
            gridLayout.addWidget(pushButton, 2, 0, 1, 1)
            gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
            pushButton.clicked.connect(
                # lambda: [self.on_pushButton_clicked(cmd_directly=[self.textEdit_cmd.toPlainText(), None]), dialog.close()])
                lambda: [self.run_with_CMD(self.textEdit_cmd.toPlainText()), dialog.close()])
            pushButton_2.clicked.connect(dialog.close)
            dialog.setWindowFlags(
                dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
            dialog.exec_()

    def judgeCmdText(self):
        text = self.textEdit_cmd.toPlainText()
        if "-s inputFile" not in text:
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>\"inputFile\" cannot be changed!</p>")
            self.textEdit_cmd.undo()

    def run_with_CMD(self, cmd):
        self.command = cmd
        if self.command:
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

    def getOutgroups(self):
        alinmentPath = self.comboBox_11.fetchListsText()[0]
        if os.path.exists(alinmentPath):
            command = f"\"{self.iqtree_exe}\" -s \"{alinmentPath}\""
            popen = self.factory.init_popen(command)
            # 自己读序列，读到标志性的位置就退出
            self.outgroups = []
            try:
                while True:
                    try:
                        out_line = popen.stdout.readline().decode("utf-8", errors="ignore")
                    except UnicodeDecodeError:
                        out_line = popen.stdout.readline().decode("gbk", errors="ignore")
                    rgx = re.compile(r"^ +\d+ +(.+?) +\d+\.\d+% +\w+ +\d+\.\d+%")
                    rgx_end = re.compile(r"^\*\*\*\*  TOTAL")
                    if rgx.search(out_line.rstrip()):
                        self.outgroups.append(rgx.search(out_line.rstrip()).group(1))
                    if rgx_end.search(out_line):
                        break
                    if out_line == "" and popen.poll() is not None:
                        break
            except:
                pass
            if not self.outgroups:
                # print("read by alignment")
                parseFmt = Parsefmt()
                parseFmt.readfile(alinmentPath)
                dict_taxon = parseFmt.dict_taxon
                self.outgroups = list(dict_taxon.keys())
        else:
            self.outgroups = []

    def changeOutgroup(self):
        if self.outgroups:
            model = self.comboBox_10.model()
            self.comboBox_10.clear()
            for num, i in enumerate(self.outgroups):
                item = QStandardItem(i)
                item.setCheckState(Qt.Unchecked)
                # 背景颜色
                if num % 2 == 0:
                    item.setBackground(QColor(255, 255, 255))
                else:
                    item.setBackground(QColor(237, 243, 254))
                item.setToolTip(i)
                model.appendRow(item)
            self.comboBox_10.setTopText()
        else:
            self.comboBox_10.clear()
            self.comboBox_10.setTopText()

    def input(self, list_items=None):
        if list_items:
            self.comboBox_11.refreshInputs(list_items)
        else:
            self.comboBox_11.refreshInputs([])
        self.judgeFileNum()

    def judgeFileNum(self):
        files = self.comboBox_11.fetchListsText()
        if len(files) == 1:
            self.comboBox_10.setDisabled(False)
            self.checkBox_9.setDisabled(False)
            # outgroups
            outgroup_worker = WorkThread(
                self.getOutgroups,
                parent=self)
            outgroup_worker.finished.connect(self.changeOutgroup)
            outgroup_worker.start()
            # self.changeOutgroup()
            self.checkBox_8.setDisabled(False)
            if hasattr(self, "dir_action"):
                self.dir_action.setDisabled(False)
        else:
            self.comboBox_10.setDisabled(True)
            self.checkBox_8.setDisabled(True)
            self.checkBox_9.setDisabled(True)
            # self.checkBox_8.setChecked(False)
            # if hasattr(self, "dir_action"):
            #     self.dir_action.setDisabled(True)
        if not files:
            self.checkBox_8.setDisabled(False)
            self.checkBox_9.setDisabled(False)
            if hasattr(self, "dir_action"):
                self.dir_action.setDisabled(False)

    @pyqtSlot(str, result=bool)
    def fetchPopen(self, command):
        self.IQ_popen = self.factory.init_popen(command)
        return True

    @pyqtSlot(str, result=bool)
    def rmvDir(self, dir_path):
        ok = self.factory.remove_dir(dir_path, parent=self)
        return True if ok else False

    def isPartitionCalculated(self):
        '''
        判断是不是已经计算好partition模型了
        :return:
        '''
        # if len(self.comboBox_11.fetchListsText()) == 1:
        #     if self.checkBox_8.isChecked():
        #         if self.lineEdit_3.toolTip():
                    ##输入了partition文件
        with open(self.lineEdit_3.toolTip()) as f:
            content = f.read()
        if "charpartition" in content:
            return True
        return False

    def ctrlOutgroupLable(self, text):
        OutgroupNum = len([self.comboBox_10.itemText(i) for i in range(
            self.comboBox_10.count()) if self.comboBox_10.model().item(i).checkState() == Qt.Checked])
        self.checkBox_9.setText("Outgroup(%d):" % OutgroupNum)

    def isPartitionChecked(self):
        return True if len(self.comboBox_11.fetchListsText()) == 1 and self.checkBox_8.isChecked() and\
                       self.lineEdit_3.toolTip() else False

    def judgePFresults(self):
        if (self.autoModelFile[0] == "PF") and (not self.autoModelFile[1]):
            QMessageBox.information(
                self,
                "IQ-TREE",
                "<p style='line-height:25px; height:25px'>Cannot find \"<span style='font-weight:600; color:#ff0000;'>best_scheme.txt</span>\" in \"<span style='font-weight:600; color:#ff0000;'>analysis</span>\" folder, "
                "PartitionFinder analysis seems to be unfinished!</p>")

    def judgeBootStrap(self, value):
        if self.comboBox_8.currentText() == "Standard":
            if value > 1000:
                QMessageBox.information(
                    self,
                    "IQ-TREE",
                    "<p style='line-height:25px; height:25px'>Note that \"<span style='font-weight:600; color:#ff0000;'>Standard bootstrap</span>\" "
                    "generally uses \"<span style='font-weight:600; color:#ff0000;'>100 to 1000</span>\" bootstraps!"
                    " More bootstraps will be time-consuming!</p>")

    # def judgeIQTREEversion(self):
    #     command = f"{self.iqtree_exe} -h"
    #     popen = self.factory.init_popen(command)
    #     stdout = self.factory.getSTDOUT(popen)
    #     rgx_version = re.compile(r"version (\d\.\d+\.\d+)")
    #     self.version = rgx_version.search(stdout).group(1)

    def switchNewOptions(self):
        if self.version.startswith("2"):
            self.checkBox_10.setVisible(True)
        else:
            self.checkBox_10.setVisible(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = IQTREE()
    ui.show()
    sys.exit(app.exec_())
