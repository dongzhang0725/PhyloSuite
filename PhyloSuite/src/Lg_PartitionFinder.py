#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import signal

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.Lg_PartitionEditer import PartitionEditor
from src.factory import Factory, WorkThread
from uifiles.Ui_partitionfinder import Ui_PartitionFinder
from src.CustomWidget import MyModelTableModel, MyPartEditorTableModel
import inspect
import os
import sys
import traceback
import multiprocessing
import csv
import decimal
import re
import copy
import shutil
import glob
import platform


class PartitionFinder(QDialog, Ui_PartitionFinder, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    PF2_exception = pyqtSignal(str)
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
            autoPartFindPath=None,
            workPath=None,
            focusSig=None,
            partitionFinderFolder=None,
            pythonEXE=None,
            workflow=False,
            parent=None):
        super(PartitionFinder, self).__init__(parent)
        self.parent = parent
        self.function_name = "PartitionFinder2"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig if focusSig else pyqtSignal(
            str)  # 为了方便workflow
        self.workflow = workflow
        self.pythonEXE = pythonEXE if (type(pythonEXE)==str and pythonEXE) else ""
        self.autoPartFindPath = autoPartFindPath
        self.interrupt = False
        self.PF2_exception.connect(self.popup_PF2_exception)
        self.setupUi(self)
        # 保存设置
        if not workflow:
            self.partitionfinder_settings = QSettings(
                self.thisPath + '/settings/partitionfinder_settings.ini', QSettings.IniFormat)
        else:
            self.partitionfinder_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.partitionfinder_settings.beginGroup("Workflow")
            self.partitionfinder_settings.beginGroup("temporary")
            self.partitionfinder_settings.beginGroup('PartitionFinder')
        # File only, no fallback to registry or or.
        self.partitionfinder_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 读取模型
        self.partitionFinderFolder = partitionFinderFolder
        model = partitionFinderFolder + os.sep + "partfinder/models.csv"
        self.nuc_model_array = []
        self.aa_model_array = []
        self.morph_model_array = []
        self.model_header = []
        if os.path.exists(model):
            with open(model, encoding="utf-8", errors='ignore') as f:
                reader = csv.reader(f, delimiter=',', quotechar='"')
                for num, list_i in enumerate(reader):
                    if num == 0:
                        list_i.pop(0)  # 不要ID
                        self.model_header = list_i
                    else:
                        list_i.pop(0)  # 不要ID
                        if "DNA" == list_i[6].upper():
                            self.nuc_model_array.append(list_i)
                        elif "PROTEIN" == list_i[6].upper():
                            self.aa_model_array.append(list_i)
                        elif "MORPHOLOGY" == list_i[6].upper():
                            self.morph_model_array.append(list_i)
        # 恢复用户的设置
        self.partitioneditor = PartitionEditor(mode="PF2", parent=self)
        self.partitioneditor.guiCloseSig.connect(self.refreshPartitionText)
        self.guiRestore()
        self.textEdit.buttonEdit.clicked.connect(self.popupPartitionEditor)
        self.textEdit_2.buttonEdit.clicked.connect(self.popupPartitionEditor)
        self.textEdit.dblclicked.connect(self.popupPartitionEditor)
        self.textEdit_2.dblclicked.connect(self.popupPartitionEditor)
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.logGuiSig.connect(self.addText2Log)
        self.lineEdit.installEventFilter(self)
        self.lineEdit_2.installEventFilter(self)
        self.textEdit.installEventFilter(self)
        self.textEdit_2.installEventFilter(self)
        self.comboBox_4.highlighted.connect(self.getOldIndex_c4)
        self.comboBox_5.highlighted.connect(self.getOldIndex_c5)
        # self.toolButton.clicked.connect(self.setWordWrap_nuc)
        # self.toolButton_2.clicked.connect(self.setWordWrap_aa)
        self.log_gui = self.gui4Log()
        self.lineEdit_2.setLineEditNoChange(True)
        self.lineEdit.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        self.lineEdit.autoDetectSig.connect(self.popupAutoDec)
        self.lineEdit_2.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        # 给开始按钮添加菜单
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        self.work_action = QAction(QIcon(":/picture/resourses/work.png"), "", menu)
        self.work_action.triggered.connect(lambda: self.factory.swithWorkPath(self.work_action, parent=self))
        self.dir_action = QAction(QIcon(":/picture/resourses/folder.png"), "Output Dir: ", menu)
        self.dir_action.triggered.connect(lambda: self.factory.set_direct_dir(self.dir_action, self))
        menu.addAction(self.work_action)
        menu.addAction(self.dir_action)
        self.pushButton_5.toolButton.setMenu(menu)
        self.pushButton_5.toolButton.menu().installEventFilter(self)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-10-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-10-1-Brief-example"
        self.label_12.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)

    @pyqtSlot()
    def on_pushButton_5_clicked(self):
        """
        execute program
        """
        PFcmd = self.getCMD()
        # 检查是否有data blocks
        if (not hasattr(self, "dataBlocks")) or (not re.search(r".+?\=.+?;", self.dataBlocks)):
            QMessageBox.critical(
                self,
                "PartitionFinder2",
                "<p style='line-height:25px; height:25px'>Please configure 'DATA BLOCKS' first!</p>")
            return
        if PFcmd:
            # 有数据才执行
            self.interrupt = False  # 如果是终止以后重新运行要刷新
            self.commands = PFcmd
            self.textEdit_log.clear()  # 清空log
            self.PF2_popen = self.factory.init_popen(self.commands)
            self.factory.emitCommands(self.logGuiSig, self.commands)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        """
        show configuration
        """
        self.getCFG()
        # 检查是否有data blocks
        if (not hasattr(self, "dataBlocks")) or (not re.search(r".+?\=.+?;", self.dataBlocks)):
            QMessageBox.critical(
                self,
                "PartitionFinder2",
                "<p style='line-height:25px; height:25px'>Please configure 'DATA BLOCKS' first!</p>")
            return
        dialog = QDialog(self)
        dialog.resize(500, 500)
        dialog.setWindowTitle("Configuration")
        gridLayout = QGridLayout(dialog)
        label = QLabel(dialog)
        label.setText("Current configuration:")
        pushButton = QPushButton("Save to file", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/Save-icon.png"))
        pushButton.setIcon(icon)
        pushButton_2 = QPushButton("Close", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/if_Delete_1493279.png"))
        pushButton_2.setIcon(icon)
        self.textEdit_cfg = QTextEdit(dialog)
        self.textEdit_cfg.setLineWrapMode(QTextEdit.NoWrap)
        self.textEdit_cfg.setText(self.cfg_content)
        gridLayout.addWidget(label, 0, 0, 1, 2)
        gridLayout.addWidget(self.textEdit_cfg, 1, 0, 1, 2)
        gridLayout.addWidget(pushButton, 2, 0, 1, 1)
        gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
        pushButton.clicked.connect(self.save_cfg_to_file)
        pushButton_2.clicked.connect(dialog.close)
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        dialog.exec_()

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        """
        show command
        """
        PFcmd = self.getCMD() if self.pushButton_5.isEnabled(
        ) else self.commands
        if PFcmd:
            dialog = QDialog(self)
            dialog.resize(600, 200)
            dialog.setWindowTitle("Command")
            gridLayout = QGridLayout(dialog)
            label = QLabel(dialog)
            label.setText("Current Command:")
            pushButton = QPushButton("Save to file", dialog)
            icon = QIcon()
            icon.addPixmap(QPixmap(":/picture/resourses/Save-icon.png"))
            pushButton.setIcon(icon)
            pushButton_2 = QPushButton("Close", dialog)
            icon = QIcon()
            icon.addPixmap(
                QPixmap(":/picture/resourses/if_Delete_1493279.png"))
            pushButton_2.setIcon(icon)
            self.textEdit_cmd = QTextEdit(dialog)
            # self.textEdit_cmd.setLineWrapMode(QTextEdit.NoWrap)
            self.textEdit_cmd.setText(PFcmd)
            gridLayout.addWidget(label, 0, 0, 1, 2)
            gridLayout.addWidget(self.textEdit_cmd, 1, 0, 1, 2)
            gridLayout.addWidget(pushButton, 2, 0, 1, 1)
            gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
            pushButton.clicked.connect(self.save_cmd_to_file)
            pushButton_2.clicked.connect(dialog.close)
            dialog.setWindowFlags(
                dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
            dialog.exec_()

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        alignment file
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input alignment file", filter="Phylip Format(*.phy *.phylip);;")
        if fileName[0]:
            if os.path.splitext(fileName[0])[1].upper() in [".PHY", ".PHYLIP"]:
                base = os.path.basename(fileName[0])
                self.lineEdit.setText(base)
                self.lineEdit.setToolTip(fileName[0])
            else:
                QMessageBox.information(
                    self,
                    "PartitionFinder2",
                    "<p style='line-height:25px; height:25px'>Only \"phylip\" format are allowed!</p>")

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

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        stop
        """
        if self.isRunning():
            if not self.workflow:
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "<p style='line-height:25px; height:25px'>PartitionFinder2 is still running, terminate it?</p>",
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
            else:
                reply = QMessageBox.Yes
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.PF2_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.PF2_popen.pid), signal.SIGTERM)
                    self.PF2_popen = None
                    self.interrupt = True
                except:
                    self.PF2_popen = None
                    self.interrupt = True
                if not self.workflow:
                    QMessageBox.information(
                        self,
                        "PartitionFinder2",
                        "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton_5,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        show log
        """
        self.log_gui.show()

    def run_command(self):
        try:
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton_5,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            self.run_code()
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                           self.time_used)
            # 加上version信息
            with open(self.exportPath + os.sep + "PhyloSuite_PartitionFinder.log") as f:
                content = f.read()
            rgx_version = re.compile(r"-+\s+PartitionFinder.+?(\d+\.\d+\.\d+)")
            if rgx_version.search(content):
                self.version = rgx_version.search(content).group(1)
            else:
                self.version = ""
            self.description = self.description.replace("$version$", self.version)
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(self.description +
                        "\n\nIf you use PhyloSuite v1.2.3 v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n"
                        "If you use PartitionFinder 2, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
            # 生成partition表格
            best_scheme = glob.glob(f"{self.exportPath}{os.sep}*{os.sep}best_scheme.txt")
            if best_scheme:
                list_partition_table = [["Subset partitions", "Sites", "Best model"]]
                best_scheme_file = best_scheme[0]
                with open(best_scheme_file, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                list_ = re.findall(r"(?m)^\d +\| +(.+?) +\| +(\d+) +\|[^\|]+\| (.+)", content)
                for num,i in enumerate(list_):
                    model, sites, name = i
                    list_partition_table.append([f"P{num+1}: ({name.strip(' ')})",
                                                 str(sites),
                                                 model])
                self.factory.write_csv_file(f"{self.exportPath}{os.sep}best_scheme_and_models.csv",
                                            list_partition_table,
                                            silence=True)
            if not self.interrupt:
                if self.workflow:
                    # work flow跑的
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton_5,
                            self.progressBar,
                            "workflow stop",
                            self.exportPath,
                            self.qss_file,
                            self])
                    self.workflow_finished.emit("finished")
                    return
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton_5,
                        self.progressBar,
                        "stop",
                        self.exportPath,
                        self.qss_file,
                        self])
            else:
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton_5,
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
                    self.pushButton_5,
                    self.progressBar,
                    "except",
                    self.exportPath,
                    self.qss_file,
                    self])

    def guiSave(self):
        # Save geometry
        self.partitionfinder_settings.setValue('size', self.size())
        # self.partitionfinder_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                text = obj.currentText()
                if text:
                    allItems = [
                        obj.itemText(i) for i in range(obj.count())]
                    allItems.remove(text)
                    sortItems = [text] + allItems
                    self.partitionfinder_settings.setValue(name, sortItems)
                if name == "comboBox_2":
                    self.partitionfinder_settings.setValue(
                        "nuc_list_model", self.custom_nuc_models)
                if name == "comboBox_8":
                    self.partitionfinder_settings.setValue(
                        "aa_list_model", self.custom_aa_models)
                if name in ["comboBox_5", "comboBox_4"]:
                    self.partitionfinder_settings.setValue(
                        "user_search", self.user_search)
            if isinstance(obj, QCheckBox):
                if name != "checkBox":
                    state = obj.isChecked()
                    self.partitionfinder_settings.setValue(name, state)
            if isinstance(obj, QPushButton):
                if name in ["pushButton_cmd1", "pushButton_cmd2"]:
                    actions = obj.menu().actions()
                    list_state = [i.isChecked() for i in actions]
                    options = [i.text() for i in actions]
                    self.partitionfinder_settings.setValue(
                        name, [options, list_state])
            if isinstance(obj, QTabWidget):
                index = obj.currentIndex()
                self.partitionfinder_settings.setValue(name, index)
            # if isinstance(obj, QLineEdit):
            #     text = obj.text()
            #     tooltip = obj.toolTip()
            #     self.partitionfinder_settings.setValue(name, [text, tooltip])
            if isinstance(obj, QTextEdit):
                if name in ["textEdit_2", "textEdit"]:
                    text = obj.toPlainText()
                    self.partitionfinder_settings.setValue(name, text)

    def guiRestore(self):

        self.factory.centerWindow(self)
        # Restore geometry
        self.resize(self.factory.judgeWindowSize(self.partitionfinder_settings, 769, 578))
        # self.move(self.partitionfinder_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                allItems = [obj.itemText(i) for i in range(obj.count())]
                values = self.partitionfinder_settings.value(name, allItems)
                model = obj.model()
                obj.clear()
                for num, i in enumerate(values):
                    item = QStandardItem(i)
                    # 背景颜色
                    if num % 2 == 0:
                        item.setBackground(QColor(255, 255, 255))
                    else:
                        item.setBackground(QColor(237, 243, 254))
                    model.appendRow(item)
                # self.comboboxRefreshSig.emit()
                if name == "comboBox_2":
                    obj.activated[str].connect(self.nuc_model_act)
                    ini_list_models = [
                        "JC", "JC+G", "HKY", "HKY+G", "GTR", "GTR+G"]
                    self.custom_nuc_models = self.partitionfinder_settings.value(
                        "nuc_list_model", ini_list_models)
                if name == "comboBox_8":
                    obj.activated[str].connect(self.aa_model_act)
                    ini_list_models = [
                        "LG", "LG+G", "LG+G+F", "WAG", "WAG+G", "WAG+G+F"]
                    self.custom_aa_models = self.partitionfinder_settings.value(
                        "aa_list_model", ini_list_models)
                if name in ["comboBox_5", "comboBox_4"]:
                    obj.activated[str].connect(self.user_define_search)
                    ini_user_search = """together = (Gene1_codon1, Gene1_codon2, Gene1_codon3, intron);
intron_123 = (Gene1_codon1, Gene1_codon2, Gene1_codon3) (intron);
intron_12_3 = (Gene1_codon1, Gene1_codon2) (Gene1_codon3) (intron);
separate = (Gene1_codon1) (Gene1_codon2) (Gene1_codon3) (intron);"""
                    self.user_search = self.partitionfinder_settings.value(
                        "user_search", ini_user_search)

            if isinstance(obj, QCheckBox):
                if name != "checkBox":
                    value = self.partitionfinder_settings.value(
                        name, "true")  # get stored value from registry
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QPushButton):
                if name in ["pushButton_cmd1", "pushButton_cmd2"]:
                    list_options = ["--raxml", "--all-states", "--force-restart", "--min-subset-size",
                                    "--no-ml-tree", "--processes", "--quick", "--rcluster-max", "--rcluster-percent",
                                    "--save-phylofiles", "--weights"]
                    ini_state = [False] * len(list_options)
                    options, list_state = self.partitionfinder_settings.value(
                        name, [list_options, ini_state])
                    menu = QMenu(self)
                    for num, i in enumerate(options):
                        action = QAction(
                            i, menu, checkable=True)
                        action.setChecked(list_state[num])
                        menu.addAction(action)
                    menu.triggered.connect(self.fun_options)
                    obj.setMenu(menu)
            if isinstance(obj, QTabWidget):
                index = self.partitionfinder_settings.value(name, 0)
                obj.setCurrentIndex(int(index))
            if isinstance(obj, QLineEdit):
                text, tooltip = self.partitionfinder_settings.value(
                    name, ["", ""])
                if os.path.exists(tooltip):
                    obj.setText(text)
                    obj.setToolTip(tooltip)
                if self.autoPartFindPath and name == "lineEdit":
                    phy = glob.glob(self.autoPartFindPath + os.sep + "*.phy")
                    if phy:  # 确定有phy文件
                        obj.setText(os.path.basename(phy[0]))
                        obj.setToolTip(phy[0])
            if isinstance(obj, QTextEdit):
                # text = self.partitionfinder_settings.value(name, "")
                # obj.setText(text)
                if self.autoPartFindPath:
                    partition = self.autoPartFindPath + \
                        os.sep + "partition.txt"
                    if os.path.exists(partition):
                        with open(partition, encoding="utf-8", errors='ignore') as file1:
                            content = file1.read()
                        search_ = re.search(
                            r"(?s)\*\*\*partitionfinder style\*\*\*(.+?)[\*|$]", content)
                        pf_partition = search_.group(1).strip() if search_ else ""
                        array = self.partitioneditor.readPartition(pf_partition)
                        text = self.partitioneditor.partition2text(array)
                        obj.setText(text)
                        #     line1 = file1.readline()
                        #     rgx = re.compile(r"(.+) *= *(\d+) *\- *(\d+)(\\3)?;")
                        #     while not rgx.search(line1):
                        #         line1 = file1.readline()
                        #     block_content = ""
                        #     while rgx.search(line1):
                        #         name = rgx.search(line1).group(1)
                        #         name_new = self.factory.refineName(name.strip(), remain_words="-")
                        #         line1_new = re.sub(r"(.+) *= *(\d+) *\- *(\d+)(\\3)?;", r"%s=\2-\3\4;"%name_new, line1)
                        #         block_content += line1_new
                        #         line1 = file1.readline()
                        # obj.setText(block_content)

    def runProgress(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        # if done_int > oldValue:
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

    def popup_PF2_exception(self, text):
        QMessageBox.information(
            self,
            "PartitionFinder2",
            "<p style='line-height:25px; height:25px'>%s</p>" % text)
        if "Show log" in text:
            self.on_pushButton_9_clicked()

    def closeEvent(self, event):
        self.guiSave()
        self.log_gui.close()  # 关闭子窗口
        self.closeSig.emit("PartitionFinder", self.fetchWorkflowSetting())
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
            self.ui_closeSig.emit("PartitionFinder")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            # print(self.isRunning())
            reply = QMessageBox.question(
                self,
                "PartitionFinder2",
                "<p style='line-height:25px; height:25px'>PartitionFinder2 is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.PF2_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.PF2_popen.pid), signal.SIGTERM)
                    self.PF2_popen = None
                    self.interrupt = True
                except:
                    self.PF2_popen = None
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
                    if os.path.splitext(files[0])[1].upper() in [".PHY", ".PHYLIP"]:
                        base = os.path.basename(files[0])
                        self.lineEdit.setText(base)
                        self.lineEdit.setToolTip(files[0])
                    else:
                        QMessageBox.information(
                            self,
                            "PartitionFinder2",
                            "<p style='line-height:25px; height:25px'>Only \"phylip\" format are allowed!</p>")
                if name == "lineEdit_2":
                    if os.path.splitext(files[0])[1].upper() in [".NWK", ".NEWICK"]:
                        base = os.path.basename(files[0])
                        self.lineEdit_2.setText(base)
                        self.lineEdit_2.setToolTip(files[0])
                    else:
                        QMessageBox.information(
                            self,
                            "PartitionFinder2",
                            "<p style='line-height:25px; height:25px'>File ends with '.nwk' or '.newick' needed!</p>")
        if isinstance(obj, QTextEdit):
            if event.type() == QEvent.MouseButtonDblClick:
                print(111)
            if name in ["textEdit", "textEdit_2"]:
                if event.type() == QEvent.MouseButtonDblClick:
                    print(111)
                    self.popupPartitionEditor()
        if (event.type() == QEvent.Show) and (obj == self.pushButton_5.toolButton.menu()):
            if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+",
                         self.dir_action.text()) or self.dir_action.text() == "Output Dir: ":
                self.factory.sync_dir(self.dir_action)  ##同步文件夹名字
            menu_x_pos = self.pushButton_5.toolButton.menu().pos().x()
            menu_width = self.pushButton_5.toolButton.menu().size().width()
            button_width = self.pushButton_5.toolButton.size().width()
            pos = QPoint(menu_x_pos - menu_width + button_width,
                         self.pushButton_5.toolButton.menu().pos().y())
            self.pushButton_5.toolButton.menu().move(pos)
            return True
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(PartitionFinder, self).eventFilter(obj, event)  # 0

    def popup_nuc_model(self):
        dialog = QDialog(self)
        dialog.resize(800, 600)
        dialog.setWindowTitle("Nucleotide models")
        gridLayout = QGridLayout(dialog)
        label = QLabel(dialog)
        label.setText("Specify the list of models (separated by a comma):")
        pushButton = QPushButton("Ok", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_ok.png"))
        pushButton.setIcon(icon)
        pushButton_2 = QPushButton("Close", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/if_Delete_1493279.png"))
        pushButton_2.setIcon(icon)
        self.tableView_nuc_model = QTableView(dialog)
        self.tableView_nuc_model.setSortingEnabled(True)
        self.tableView_nuc_model.horizontalHeader().setSortIndicatorShown(True)
        sorted_nuc_model_array = list(sorted(self.nuc_model_array))
        array = copy.deepcopy(sorted_nuc_model_array)
        for num, i in enumerate(sorted_nuc_model_array):
            array[num][0] = QCheckBox(i[0])
        model = MyModelTableModel(
            array, self.model_header, self.custom_nuc_models, parent=self)
        self.tableView_nuc_model.setModel(model)
        gridLayout.addWidget(label, 0, 0, 1, 2)
        gridLayout.addWidget(self.tableView_nuc_model, 1, 0, 1, 2)
        gridLayout.addWidget(pushButton, 2, 0, 1, 1)
        gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
        pushButton.clicked.connect(dialog.accept)
        pushButton.clicked.connect(dialog.close)
        pushButton_2.clicked.connect(dialog.close)
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def popup_aa_model(self):
        dialog = QDialog(self)
        dialog.resize(800, 600)
        dialog.setWindowTitle("Amino acid models")
        gridLayout = QGridLayout(dialog)
        label = QLabel(dialog)
        label.setText("Specify the list of models (separated by a comma):")
        pushButton = QPushButton("Ok", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_ok.png"))
        pushButton.setIcon(icon)
        pushButton_2 = QPushButton("Close", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/if_Delete_1493279.png"))
        pushButton_2.setIcon(icon)
        self.tableView_aa_model = QTableView(dialog)
        self.tableView_aa_model.setSortingEnabled(True)
        self.tableView_aa_model.horizontalHeader().setSortIndicatorShown(True)
        sorted_aa_model_array = list(sorted(self.aa_model_array))
        array = copy.deepcopy(sorted_aa_model_array)
        for num, i in enumerate(sorted_aa_model_array):
            array[num][0] = QCheckBox(i[0])
        model = MyModelTableModel(
            array, self.model_header, self.custom_aa_models, parent=self)
        self.tableView_aa_model.setModel(model)
        gridLayout.addWidget(label, 0, 0, 1, 2)
        gridLayout.addWidget(self.tableView_aa_model, 1, 0, 1, 2)
        gridLayout.addWidget(pushButton, 2, 0, 1, 1)
        gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
        pushButton.clicked.connect(dialog.accept)
        pushButton.clicked.connect(dialog.close)
        pushButton_2.clicked.connect(dialog.close)
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def nuc_model_act(self, text):
        if text == "<list>":
            dialog = self.popup_nuc_model()
            if dialog.exec_() == QDialog.Accepted:
                self.custom_nuc_models = self.tableView_nuc_model.model(
                ).list_checked

    def aa_model_act(self, text):
        if text == "<list>":
            dialog = self.popup_aa_model()
            if dialog.exec_() == QDialog.Accepted:
                self.custom_aa_models = self.tableView_aa_model.model(
                ).list_checked

    def popup_user_define_search(self):
        dialog = QDialog(self)
        dialog.resize(400, 300)
        dialog.setWindowTitle("Partitioning schemes")
        gridLayout = QGridLayout(dialog)
        label = QLabel(dialog)
        label.setText(
            "Specify the partitioning schemes (one scheme on each line):")
        pushButton = QPushButton("Ok", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_ok.png"))
        pushButton.setIcon(icon)
        pushButton_2 = QPushButton("Close", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/if_Delete_1493279.png"))
        pushButton_2.setIcon(icon)
        self.textEdit_user_search = QTextEdit(dialog)
        self.textEdit_user_search.setLineWrapMode(QTextEdit.NoWrap)
        self.textEdit_user_search.setText(self.user_search)
        self.textEdit_user_search.setToolTip("""For example:
together = (Gene1_codon1, Gene1_codon2, Gene1_codon3, intron);
intron_123 = (Gene1_codon1, Gene1_codon2, Gene1_codon3) (intron);
intron_12_3 = (Gene1_codon1, Gene1_codon2) (Gene1_codon3) (intron);
separate = (Gene1_codon1) (Gene1_codon2) (Gene1_codon3) (intron);""")
        gridLayout.addWidget(label, 0, 0, 1, 2)
        gridLayout.addWidget(self.textEdit_user_search, 1, 0, 1, 2)
        gridLayout.addWidget(pushButton, 2, 0, 1, 1)
        gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
        pushButton.clicked.connect(dialog.accept)
        pushButton.clicked.connect(dialog.close)
        pushButton_2.clicked.connect(dialog.close)
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def user_define_search(self, text):
        combobox = self.sender()
        name = combobox.objectName()
        if text == "user define":
            dialog = self.popup_user_define_search()
            if dialog.exec_() == QDialog.Accepted:
                self.user_search = self.textEdit_user_search.toPlainText()
        elif text in ["rclusterf", "rcluster", "hcluster"]:
            if name == "comboBox_4":
                menu = self.pushButton_cmd1.menu()
                raxml_action = [
                    i for i in menu.actions() if "--raxml" in i.text()][0]
                if not raxml_action.isChecked():
                    QMessageBox.information(
                        self,
                        "PartitionFinder2",
                        "<p style='line-height:25px; height:25px'>Please select <span style='font-weight:600; color:#ff0000;'>--raxml</span> in <span style='font-weight:600; text-decoration: underline; color:#0000ff;'>Command line options</span> first!</p>")
                    combobox.setCurrentIndex(self.oldIndex_c4)
            elif name == "comboBox_5":
                menu = self.pushButton_cmd2.menu()
                raxml_action = [
                    i for i in menu.actions() if "--raxml" in i.text()][0]
                if not raxml_action.isChecked():
                    QMessageBox.information(
                        self,
                        "PartitionFinder2",
                        "<p style='line-height:25px; height:25px'>Please select <span style='font-weight:600; color:#ff0000;'>--raxml</span> in <span style='font-weight:600; text-decoration: underline; color:#0000ff;'>Command line options</span> first!</p>")
                    combobox.setCurrentIndex(self.oldIndex_c5)
        if text not in ["kmeans", "rcluster"]:
            if name == "comboBox_4":
                menu = self.pushButton_cmd1.menu()
                for i in menu.actions():
                    if ("--all-states" in i.text()) or ("--min-subset-size" in i.text()):
                        i.setChecked(False)
            elif name == "comboBox_5":
                menu = self.pushButton_cmd2.menu()
                for i in menu.actions():
                    if ("--all-states" in i.text()) or ("--min-subset-size" in i.text()):
                        i.setChecked(False)

    def popup_weights(self):
        dialog = QDialog(self)
        dialog.resize(243, 46)
        dialog.setWindowTitle("Weights")
        gridLayout = QGridLayout(dialog)
        label = QLabel(dialog)
        label.setText("Specify weights:")
        label_2 = QLabel(dialog)
        label_2.setText("Weights:")
        pushButton = QPushButton("Ok", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_ok.png"))
        pushButton.clicked.connect(dialog.accept)
        pushButton.clicked.connect(dialog.close)
        pushButton.setIcon(icon)
        pushButton_2 = QPushButton("Close", dialog)
        pushButton_2.clicked.connect(dialog.close)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/if_Delete_1493279.png"))
        pushButton_2.setIcon(icon)
        self.doubleSpinBox = QDoubleSpinBox(dialog)
        self.doubleSpinBox.setSingleStep(0.1)
        self.doubleSpinBox.setProperty("value", 1.0)
        self.doubleSpinBox_2 = QDoubleSpinBox(dialog)
        self.doubleSpinBox_2.setSingleStep(0.1)
        self.doubleSpinBox_3 = QDoubleSpinBox(dialog)
        self.doubleSpinBox_3.setSingleStep(0.1)
        self.doubleSpinBox_4 = QDoubleSpinBox(dialog)
        self.doubleSpinBox_4.setSingleStep(0.1)
        gridLayout.addWidget(label, 0, 0, 1, 2)
        gridLayout.addWidget(label_2, 1, 0, 1, 1)
        gridLayout.addWidget(self.doubleSpinBox, 1, 1, 1, 1)
        gridLayout.addWidget(self.doubleSpinBox_2, 1, 2, 1, 1)
        gridLayout.addWidget(self.doubleSpinBox_3, 1, 3, 1, 1)
        gridLayout.addWidget(self.doubleSpinBox_4, 1, 4, 1, 1)
        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(pushButton)
        horizontalLayout.addWidget(pushButton_2)
        gridLayout.addLayout(horizontalLayout, 2, 0, 1, 5)
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def get_search_combo(self):
        data_type = self.tabWidget.tabText(self.tabWidget.currentIndex())
        if data_type == "Nucleotide":
            return self.comboBox_4
        elif data_type == "Amino acid":
            return self.comboBox_5

    def fun_options(self, action):
        menu = self.sender()
        self.actionName(menu)
        option = action.text()
        if "--processes" in option and action.isChecked():
            cpu_num = multiprocessing.cpu_count()
            list_cpu = [str(i + 1) for i in range(cpu_num)]
            current = cpu_num // 2
            item, ok = QInputDialog.getItem(
                self, "Specify thread number", "Thread:", list_cpu, current, False)
            if ok and item:
                action.setText("--processes %s" % item)
            else:
                action.setChecked(False)
        elif "--rcluster-max" in option:
            if not self.raxml_action.isChecked() and action.isChecked():
                QMessageBox.information(
                    self,
                    "PartitionFinder2",
                    "<p style='line-height:25px; height:25px'>Please select <span style='font-weight:600; color:#ff0000;'>--raxml</span> first!</p>")
                action.setChecked(False)
            if action.isChecked():
                i, ok = QInputDialog.getInt(self,
                                            "rcluster-max", "rcluster-max:", 1000, min=-1)
                if ok:
                    action.setText("--rcluster-max %d" % i)
                else:
                    action.setChecked(False)
        elif "--rcluster-percent" in option:
            if not self.raxml_action.isChecked() and action.isChecked():
                QMessageBox.information(
                    self,
                    "PartitionFinder2",
                    "<p style='line-height:25px; height:25px'>Please select <span style='font-weight:600; color:#ff0000;'>--raxml</span> first!</p>")
                action.setChecked(False)
            if action.isChecked():
                i, ok = QInputDialog.getInt(self,
                                            "rcluster-percent", "rcluster-percent:", 10, min=1, max=100)
                if ok:
                    action.setText("--rcluster-percent %d" % i)
                else:
                    action.setChecked(False)
        elif "--weights" in option:
            if not self.raxml_action.isChecked() and action.isChecked():
                QMessageBox.information(
                    self,
                    "PartitionFinder2",
                    "<p style='line-height:25px; height:25px'>Please select <span style='font-weight:600; color:#ff0000;'>--raxml</span> first!</p>")
                action.setChecked(False)
            if action.isChecked():
                dialog = self.popup_weights()
                if dialog.exec_() == QDialog.Accepted:
                    one = str(
                        round(decimal.Decimal(self.doubleSpinBox.value()), 4).normalize())
                    two = str(
                        round(decimal.Decimal(self.doubleSpinBox_2.value()), 4).normalize())
                    three = str(
                        round(decimal.Decimal(self.doubleSpinBox_3.value()), 4).normalize())
                    four = str(
                        round(decimal.Decimal(self.doubleSpinBox_4.value()), 4).normalize())
                    action.setText('--weights "%s, %s, %s, %s"' %
                                   (one, two, three, four))
                else:
                    action.setChecked(False)
        elif "--raxml" in option:
            if not action.isChecked():
                self.weights_action.setChecked(False)
                self.rcluster_max_action.setChecked(False)
                self.rcluster_percent_action.setChecked(False)
                search_combo = self.get_search_combo()
                if search_combo.currentText() in ["rcluster", "rclusterf", "hcluster"]:
                    search_combo.setCurrentIndex(
                        search_combo.findText("greedy"))
        elif "--all-states" in option:
            if action.isChecked():
                search_combo = self.get_search_combo()
                if search_combo.currentText() not in ["kmeans", "rcluster"]:
                    QMessageBox.information(
                        self,
                        "PartitionFinder2",
                        "<p style='line-height:25px; height:25px'>Please select <span style='font-weight:600; color:#ff0000;'>kmeans</span> or <span style='font-weight:600; color:#ff0000;'>rcluster</span> in <span style='font-weight:600; text-decoration: underline; color:#0000ff;'>search</span> options first!</p>")
                    action.setChecked(False)
        elif "--min-subset-size" in option:
            search_combo = self.get_search_combo()
            if action.isChecked() and (search_combo.currentText() not in ["kmeans", "rcluster"]):
                QMessageBox.information(
                    self,
                    "PartitionFinder2",
                    "<p style='line-height:25px; height:25px'>Please select <span style='font-weight:600; color:#ff0000;'>kmeans</span> or <span style='font-weight:600; color:#ff0000;'>rcluster</span> in <span style='font-weight:600; text-decoration: underline; color:#0000ff;'>search</span> options first!</p>")
                action.setChecked(False)
            elif action.isChecked():
                i, ok = QInputDialog.getInt(self,
                                            "min-subset-size", "min-subset-size:", 100, min=0)
                if ok:
                    action.setText("--min-subset-size %d" % i)
                else:
                    action.setChecked(False)

    # def partitionConvertor(self, content):
    #     rgx_partition = re.compile(r"(.+?) *\= *(\d+) *\- *(\d+)(\\3)?")
    #     list_partitions = rgx_partition.findall(content)
    #     # print(list_partitions) #[('atp6_mafft_codon1', '1', '597', '\\3'),
    #     # ('atp6_mafft_codon2', '2', '597', '\\3'), ('atp6_mafft_codon3', '3',
    #     # '597', '\\3'), ('cox1_mafft_codon1', '598', '2241', '\\3'),
    #     # ('cox1_mafft_codon2', '599', '2241', '\\3')]
    #     list_new_partitions = []
    #     list_index = []
    #     for i in list_partitions:
    #         name, start, stop = i[:3]
    #         name = self.factory.refineName(name.strip(), remain_words="-")
    #         start = start.strip()
    #         stop = stop.strip()
    #         # 替换掉codon
    #         name = re.sub(r"_codon\d", "", name)
    #         # 重新找start
    #         start = str(((int(start) - 1) // 3) * 3 + 1)
    #         if [start, stop] not in list_index:
    #             list_new_partitions.append([name, start, stop])
    #             list_index.append([start, stop])
    #     # print(list_new_partitions) #[['atp6_mafft', '1', '597'], ['cox1_mafft', '598', '2241']]
    #     # 生成新的文本
    #     list_str_partition = []
    #     for j in list_new_partitions:
    #         if re.search(r"\\3", content):
    #             # 已经是codon mode了
    #             list_str_partition.append(j[0] + "=" + j[1] + "-" + j[2])
    #         else:
    #             list_str_partition.append(
    #                 j[0] + "_codon1=" + j[1] + "-" + j[2] + '\\3')
    #             list_str_partition.append(
    #                 j[0] + "_codon2=" + str(int(j[1]) + 1) + "-" + j[2] + '\\3')
    #             list_str_partition.append(
    #                 j[0] + "_codon3=" + str(int(j[1]) + 2) + "-" + j[2] + '\\3')
    #     return ";\n".join(list_str_partition) + ";"

    # def switch_partition(self, bool_):
    #     cursor = self.textEdit.textCursor()
    #     content = cursor.selectedText()
    #     if "\u2029" in content:
    #         # cursor获得的内容把换行符变成了这个
    #         content = content.replace("\u2029", "\n")
    #     if not content:
    #         QMessageBox.information(
    #             self,
    #             "Concatenate sequence",
    #             "<p style='line-height:25px; height:25px'>Please select contents first!</p>")
    #         return
    #     new_content = self.partitionConvertor(content)
    #     all_content = self.textEdit.toPlainText()
    #     new_all_content = all_content.replace(content, new_content)
    #     self.textEdit.setText(new_all_content)
    #     # print(new_content, new_all_content)
    #     # 正则需要2层转义，new_content里面已经是\\3了，所以需要替换为\\\\3，类似于r'\\3'
    #     start, end = re.search(
    #         new_content.replace("\\", "\\\\"), new_all_content).span()
    #     cursor.setPosition(start)
    #     cursor.movePosition(
    #         QTextCursor.Right,
    #         QTextCursor.KeepAnchor,
    #         end - start)
    #     self.textEdit.setTextCursor(cursor)

    def actionName(self, menu):
        actions = menu.actions()
        for action in actions:
            i = action.text()
            if "--raxml" in i:
                self.raxml_action = action
            elif "--weights" in i:
                self.weights_action = action
            elif "--rcluster-max" in i:
                self.rcluster_max_action = action
            elif "--rcluster-percent" in i:
                self.rcluster_percent_action = action

    def getOldIndex_c4(self):
        self.oldIndex_c4 = self.comboBox_4.currentIndex()

    def getOldIndex_c5(self):
        self.oldIndex_c5 = self.comboBox_5.currentIndex()

    def getCFG(self):
        self.data_type = self.tabWidget.tabText(self.tabWidget.currentIndex())
        self.alnmt_base = self.factory.refineName(self.lineEdit.text(), remain_words=".-")
        self.treepath_base = self.factory.refineName(self.lineEdit_2.text(), remain_words=".-")
        self.alignment = self.lineEdit.toolTip()
        self.tree = self.lineEdit_2.toolTip()
        self.treefile = "user_tree_topology = {self.treepath_base};\n".format(
            self=self) if self.treepath_base else ""
        if self.data_type == "Nucleotide":
            self.branchlengths = self.comboBox.currentText()
            self.model_selection = self.comboBox_3.currentText()
            if self.comboBox_2.currentText() != "<list>":
                self.models = self.comboBox_2.currentText()
            else:
                self.models = ", ".join(self.custom_nuc_models)
            self.dataBlocks = self.textEdit.toPlainText().strip()
            search_algorithm = self.comboBox_4.currentText()
            if search_algorithm != "user define":
                self.search = "search = %s;" % search_algorithm
            else:
                self.search = "search = user;\n%s" % self.user_search
                if not self.search.endswith(";"):
                    self.search = self.search + ";"
        elif self.data_type == "Amino acid":
            self.branchlengths = self.comboBox_6.currentText()
            self.model_selection = self.comboBox_7.currentText()
            if self.comboBox_8.currentText() != "<list>":
                self.models = self.comboBox_8.currentText()
            else:
                self.models = ", ".join(self.custom_aa_models)
            self.dataBlocks = self.textEdit_2.toPlainText().strip()
            search_algorithm = self.comboBox_5.currentText()
            if search_algorithm != "user define":
                self.search = "search = %s;" % search_algorithm
            else:
                self.search = "search = user;\n%s" % self.user_search
                if not self.search.endswith(";"):
                    self.search = self.search + ";"
        self.cfg_content = "## ALIGNMENT FILE ##\nalignment = {self.alnmt_base};\n".format(self=self) + self.treefile + \
            "# BRANCHLENGTHS #\nbranchlengths = {self.branchlengths};\n# MODELS OF EVOLUTION #\n\
models = {self.models};\n# MODEL SELECCTION #\nmodel_selection = {self.model_selection};\n\
# DATA BLOCKS #\n[data_blocks]\n{self.dataBlocks}\n# SCHEMES #\n[schemes]\n\
{self.search}".format(self=self)
        # 描述
        block_num = len(self.dataBlocks.strip().split("\n"))
        self.description = '''Best partitioning scheme and evolutionary models for %d pre-defined partitions were selected using PartitionFinder2 v$version$ (Lanfear et al., 2017), with %s algorithm and %s criterion.''' % (
            block_num, search_algorithm, self.model_selection)
        self.reference = '''Lanfear, R., Frandsen, P. B., Wright, A. M., Senfeld, T., Calcott, B. (2016) PartitionFinder 2: new methods for selecting partitioned models of evolution formolecular and morphological phylogenetic analyses. Molecular biology and evolution. DOI: dx.doi.org/10.1093/molbev/msw260'''

    def getCMD(self):
        self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
        self.exportPath = self.factory.creat_dirs(self.workPath +
                                                  os.sep + "PartFind_results" + os.sep + self.output_dir_name)
        self.getCFG()
        if os.path.exists(self.alignment):
            self.alnmt_base = self.factory.refineName(self.lineEdit.text(), remain_words=".-")
            self.treepath_base = self.factory.refineName(self.lineEdit_2.text(), remain_words=".-")
            pf_compile = False
            if self.data_type == "Nucleotide":
                option_button = self.pushButton_cmd1
                compile_pf2 = self.partitionFinderFolder + \
                              os.sep + "PartitionFinder.exe" if platform.system().lower() == "windows" else \
                    self.partitionFinderFolder + os.sep + "PartitionFinder"
                if os.path.exists(self.partitionFinderFolder + \
                                          os.sep + "PartitionFinder.py"):
                    self.PFexe = self.partitionFinderFolder + \
                        os.sep + "PartitionFinder.py"
                elif os.path.exists(compile_pf2):
                    pf_compile= True
                    self.PFexe = compile_pf2
            elif self.data_type == "Amino acid":
                option_button = self.pushButton_cmd2
                compile_pf2 = self.partitionFinderFolder + \
                              os.sep + "PartitionFinderProtein.exe" if platform.system().lower() == "windows" else \
                    self.partitionFinderFolder + os.sep + "PartitionFinderProtein"
                if os.path.exists(self.partitionFinderFolder + \
                                          os.sep + "PartitionFinderProtein.py"):
                    self.PFexe = self.partitionFinderFolder + \
                        os.sep + "PartitionFinderProtein.py"
                elif os.path.exists(compile_pf2):
                    pf_compile= True
                    self.PFexe = compile_pf2
            self.options = [
                i.text() for i in option_button.menu().actions() if i.isChecked()]
            self.cmd_option = " ".join(self.options)
            if not self.isRunning():  # 程序运行的时候，不能执行下面的
                ok = self.factory.remove_dir(self.exportPath, parent=self)
                if not ok:
                    # 提醒是否删除旧结果，如果用户取消，就不执行
                    return
                with open(self.exportPath + os.sep + "partition_finder.cfg", "w", encoding="utf-8") as f:
                    f.write(self.cfg_content)
                shutil.copy(self.alignment, self.exportPath + os.sep + self.alnmt_base)
                if self.tree:
                    shutil.copy(self.tree, self.exportPath + os.sep + self.treepath_base)
            cmds = "\"%s\" \"%s\" \"%s\" %s" % (self.pythonEXE, self.PFexe, self.exportPath, self.cmd_option)
            if pf_compile:
                cmds = re.sub(r'^\"%s\" '%self.pythonEXE, "", cmds)
            return cmds
        else:
            QMessageBox.warning(
                self,
                "PartitionFinder2",
                "<p style='line-height:25px; height:25px'>Please input file first!</p>")
            return None

    def save_cfg_to_file(self):
        content = self.textEdit_cfg.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "PartitionFinder", "partition_finder", "CFG Format(*.cfg)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    def save_cmd_to_file(self):
        content = self.textEdit_cmd.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "PartitionFinder", "command", "text Format(*.txt)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "PartitionFinder", "log", "text Format(*.txt)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    def run_code(self):
        rgx_step = re.compile(r"\*\*\*.+\*\*\*")
        rgx_subset = re.compile(r"Finished subset.+?, (\d+\.\d+) percent done")
        is_error = False  ##判断是否出了error
        error_text = ""
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = self.PF2_popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = self.PF2_popen.stdout.readline().decode("gbk", errors="ignore")
                if out_line == "" and self.PF2_popen.poll() is not None:
                    break
                if "BEGINNING NEW RUN" in out_line:
                    tree_text = "Estimating Maximum Likelihood tree..." if not self.tree else "Reading tree..."
                    self.label_11.setText(tree_text)
                elif rgx_step.search(out_line):
                    label = rgx_step.search(out_line).group()
                    self.label_11.setText(label)
                    self.progressSig.emit(0)
                elif rgx_subset.search(out_line):
                    # if not rgx_subset.search(list_stdout[-1]):
                    #     label = list_stdout[-1].split("|")[-1].strip()
                    #     if rgx_step.search(list_stdout[-2]):
                    #         label = rgx_step.search(list_stdout[-2]).group() + " (" + label + ")"
                    #     self.label_11.setText(label)
                    percent = float(rgx_subset.search(out_line).group(1))
                    self.progressSig.emit(percent)
                    self.workflow_progress.emit(percent)
                # list_stdout.append(out_line)
                self.logGuiSig.emit(out_line.strip())
                if re.search(r"^ERROR", out_line):
                    is_error = True
                    error_text = "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!"
                if re.search(r"^ImportError", out_line):
                    is_error = True
                    country = self.factory.path_settings.value("country", "UK")
                    url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/#2-3-1-Troubleshooting" if \
                        country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/#2-3-1-Troubleshooting"
                    error_text = "Error! Dependencies not found! Click <span style='font-weight:600; color:#ff0000;'>" \
                                 "Show log</span> to see details! <br>For the solution, please see " \
                                 "<a href=\"%s\">here</a>."%url
            else:
                break
        if is_error:
            self.interrupt = True
            self.PF2_exception.emit(error_text)
        self.PF2_popen = None

    def gui4Log(self):
        self.getCFG()
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of PartitionFinder:")
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
            with open(self.exportPath + os.sep + "PhyloSuite_PartitionFinder.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def setWordWrap(self):
        button = self.sender()
        if button.isChecked():
            button.setChecked(True)
            self.textEdit_log.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            button.setChecked(False)
            self.textEdit_log.setLineWrapMode(QTextEdit.NoWrap)

    # def setWordWrap_nuc(self):
    #     button = self.sender()
    #     if button.isChecked():
    #         button.setChecked(True)
    #         self.textEdit.setLineWrapMode(QTextEdit.WidgetWidth)
    #     else:
    #         button.setChecked(False)
    #         self.textEdit.setLineWrapMode(QTextEdit.NoWrap)
    #
    # def setWordWrap_aa(self):
    #     button = self.sender()
    #     if button.isChecked():
    #         button.setChecked(True)
    #         self.textEdit_2.setLineWrapMode(QTextEdit.WidgetWidth)
    #     else:
    #         button.setChecked(False)
    #         self.textEdit_2.setLineWrapMode(QTextEdit.NoWrap)

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "PF2_popen") and self.PF2_popen and not self.interrupt

    def clear_lineEdit(self):
        sender = self.sender()
        lineEdit = sender.parent()
        lineEdit.setText("")
        lineEdit.setToolTip("")

    def workflow_input(self, MSA=None, partition=None):
        self.lineEdit.setText("")
        self.textEdit.setText("")
        self.textEdit_2.setText("")
        if MSA:
            self.lineEdit.setText(os.path.basename(MSA))
            self.lineEdit.setToolTip(MSA)
        if partition:
            if os.path.exists(partition):
                with open(partition, encoding="utf-8", errors='ignore') as file1:
                    content = file1.read()
                search_ = re.search(
                    r"(?s)\*\*\*partitionfinder style\*\*\*(.+?)[\*|$]", content)
                PF_partition = search_.group(1) if search_ else ""
                array = self.partitioneditor.readPartition(PF_partition)
                text = self.partitioneditor.partition2text(array)
                self.textEdit.setText(text)
                self.textEdit_2.setText(text)

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect(
            "PartitionFinder2", self.workPath, self.auto_popSig, self)

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
            autoPartFindPath = widget.autoInputs
            list_MSA = glob.glob(autoPartFindPath + os.sep + "*.phy")
            if list_MSA:
                MSA = list_MSA[0]
                partition = autoPartFindPath + os.sep + "partition.txt"
                self.workflow_input(MSA, partition)

    def fetchWorkflowSetting(self):
        '''* seq type: aa, nuc
          * branchlength
          * models
          * model selec
          * search'''

        settings = '''<p class="title">***PartitionFinder***</p>'''
        seq_type = self.tabWidget.tabText(self.tabWidget.currentIndex())
        settings += '<p>Sequence type: <a href="self.PartitionFinder_exe' \
                    ' factory.highlightWidgets(x.tabWidget.tabBar())">%s</a></p>' % seq_type
        branchLen = self.comboBox.currentText(
        ) if seq_type == "Nucleotide" else self.comboBox_6.currentText()
        comb_brnLen = "comboBox" if seq_type == "Nucleotide" else "comboBox_6"
        settings += '<p>Branch lengths: <a href="self.PartitionFinder_exe %s.showPopup()' \
                    ' factory.highlightWidgets(x.%s)">%s</a></p>' % (
                        comb_brnLen, comb_brnLen, branchLen)
        models = self.comboBox_2.currentText(
        ) if seq_type == "Nucleotide" else self.comboBox_8.currentText()
        models = models.replace(">", "&gt;").replace("<", "&lt;")
        comb_model = "comboBox_2" if seq_type == "Nucleotide" else "comboBox_8"
        settings += '<p>Models: <a href="self.PartitionFinder_exe %s.showPopup()' \
                    ' factory.highlightWidgets(x.%s)">%s</a></p>' % (
                        comb_model, comb_model, models)
        criterion = self.comboBox_3.currentText(
        ) if seq_type == "Nucleotide" else self.comboBox_7.currentText()
        comb_criton = "comboBox_3" if seq_type == "Nucleotide" else "comboBox_7"
        settings += '<p>Model selection criterion: <a href="self.PartitionFinder_exe %s.showPopup()' \
                    ' factory.highlightWidgets(x.%s)">%s</a></p>' % (
                        comb_criton, comb_criton, criterion)
        search = self.comboBox_4.currentText(
        ) if seq_type == "Nucleotide" else self.comboBox_5.currentText()
        comb_search = "comboBox_4" if seq_type == "Nucleotide" else "comboBox_5"
        settings += '<p>Search: <a href="self.PartitionFinder_exe %s.showPopup()' \
                    ' factory.highlightWidgets(x.%s)">%s</a></p>' % (
                        comb_search, comb_search, search)
        option_button_str = "pushButton_cmd1" if seq_type == "Nucleotide" else "pushButton_cmd2"
        option_button = self.pushButton_cmd1 if seq_type == "Nucleotide" else self.pushButton_cmd2
        options = [i.text()
                   for i in option_button.menu().actions() if i.isChecked()]
        settings += '<p>Command line options: <a href="self.PartitionFinder_exe factory.highlightWidgets(x.%s)' \
                    ' %s.click()">%s</a></p>' % (option_button_str,
                                                 option_button_str, " | ".join(options))
        return settings

    def showEvent(self, event):
        # 用定时器，不让菜单出来太快
        QTimer.singleShot(100, lambda: self.showSig.emit(self))
        # self.showSig.emit(self)

    def isFileIn(self):
        if os.path.exists(self.lineEdit.toolTip()):
            return True
        else:
            return False

    def popupPartitionEditor(self):
        data_type = self.tabWidget.tabText(self.tabWidget.currentIndex())
        if data_type == "Nucleotide":
            textedit = self.textEdit
            self.partitioneditor.pushButton_codon.setEnabled(True)
            self.partitioneditor.pushButton_nocodon.setEnabled(True)
            self.partitioneditor.data_type = "NUC"
        else:
            textedit = self.textEdit_2
            self.partitioneditor.pushButton_codon.setEnabled(False)
            self.partitioneditor.pushButton_nocodon.setEnabled(False)
            self.partitioneditor.data_type = "AA"
        partition_content = textedit.toPlainText().strip()
        array = self.partitioneditor.readPartition(partition_content)
        ini_array = [["", "=", "", "-", ""],
                     ["", "=", "", "-", ""],
                     ["", "=", "", "-", ""],
                     ["", "=", "", "-", ""]
                     ]
        array = ini_array if not array else array
        # header, array = self.MrBayes_settings.value(
        #     "partition defination", [header, ini_array])
        model = MyPartEditorTableModel(array, self.partitioneditor.header, parent=self.partitioneditor)
        model.dataChanged.connect(self.partitioneditor.sortGenes)
        self.partitioneditor.tableView_partition.setModel(model)
        self.partitioneditor.ctrlResizedColumn()  # 先执行一次改变列的宽度
        self.partitioneditor.exec_()

    def refreshPartitionText(self, text):
        data_type = self.tabWidget.tabText(self.tabWidget.currentIndex())
        textedit = self.textEdit if data_type == "Nucleotide" else self.textEdit_2
        textedit.setText(text)
        textedit.setToolTip(text)

    # def judgePartContents(self, content):
    #     rgx_partition = re.compile(r"(.+?) *\= *(\d+) *\- *(\d+)(\\3)?")
    #     list_partitions = rgx_partition.findall(content)
    #     list_new_partitions = []
    #     list_index = []
    #     name_replaced = False
    #     for i in list_partitions:
    #         name, start, stop = i[:3]
    #         rep_name = self.factory.refineName(name, mode="remain minus")
    #         if rep_name != name:
    #             name_replaced = True
    #     ##两个分号

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = PartitionFinder()
    ui.show()
    sys.exit(app.exec_())
