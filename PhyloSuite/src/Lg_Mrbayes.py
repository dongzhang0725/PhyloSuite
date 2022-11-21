#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import multiprocessing
import re

import datetime
import signal

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import subprocess
from src.CustomWidget import MyPartDisplayTableModel
from src.Lg_settings import Setting
from uifiles.Ui_dirichlet_mrbayes import Ui_Dirichlet
from uifiles.Ui_nexViewer import Ui_nexViewer
from uifiles.Ui_partition_defination import Ui_PartDefine
from src.factory import Factory, WorkThread, Find, Convertfmt
from uifiles.Ui_MrBayes import Ui_MrBayes
from src.factory import Parsefmt
import inspect
import os
import sys
import traceback
import platform
import glob


class PartDefine(QDialog, Ui_PartDefine, object):
    guiCloseSig = pyqtSignal()

    def __init__(self, parent=None):
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        super(PartDefine, self).__init__(parent)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.resize(800, 600)
        self.setupUi(self)

    @pyqtSlot()
    def on_pushButton_blk_clicked(self):
        """
        generate cmd block
        """
        currentModel = self.tableView_partition.model()
        # 生成[['GTR+I+G', 'Subset1', '=', '790', '-', '1449\\3']]
        if currentModel:
            currentData = currentModel.arraydata
            zip_data = list(zip(*currentData))
            list_filter_data = []
            for i in currentData:
                copy_i = copy.deepcopy(i)
                if i[0] and i[1]:
                    list_remove_rows = []
                    for num, j in enumerate(i):
                        if j == "-":
                            if i[num - 1] and i[num + 1]:
                                continue
                            else:
                                list_remove_rows.extend(
                                    [num - 2, num - 1, num, num + 1])
                    for k in sorted(list_remove_rows, reverse=True):
                        copy_i.pop(k)
                    if len(copy_i) > 2:
                        list_filter_data.append(copy_i)
            # 生成block
            if list_filter_data:
                zip_data = list(zip(*list_filter_data))
                charset_block = ""
                lset_block = ""
                partition_block = ""
                isAA = False
                for num, subset in enumerate(list_filter_data):
                    # charset
                    charset_block += "charset " + \
                        "".join(subset[1:]).replace("=", " = ") + ";\n"
                    # lset
                    model = subset[0]
                    # Rate var
                    if "+G" in model.upper() and "+I" in model:
                        rates = " rates=invgamma"
                    elif "+G" in model.upper():
                        rates = " rates=gamma"
                    elif "+I" in model.upper():
                        rates = " rates=propinv"
                    else:
                        rates = ""
                    dict_models = {"JC": "1", "F81": "1", "K80": "2", "HKY": "2", "": "6", "TrN": "6", "K81": "6",
                                   "K81uf": "6", "K2P": "2", "JC69": "1", "HKY85": "2", "K3P": "6",
                                   "TIMef": "6", "TIM": "6", "TVMef": "6", "TVM": "6", "SYM": "6", "GTR": "6", "TPM2": "6",
                                   "TPM2uf": "6", "TPM3": "6", "TPM3uf": "6", "TIM2ef": "6", "TIM2": "6", "TIM3ef": "6",
                                   "TIM3": "6"}
                    model_name = model.split("+")[0]
                    if model_name in dict_models:
                        lset_block += "lset applyto=(%d) nst=%s%s;\n" % (
                            num + 1, dict_models[model_name], rates)
                    else:
                        # AA序列
                        lset_block += "lset applyto=(%d)%s;\n" % (
                            num + 1, rates)
                        lset_block += "prset applyto=(%d) aamodelpr=fixed(%s);\n" % (
                            num + 1, model_name.lower())
                        if "+F" in model.upper():
                            lset_block += "prset applyto=(%d) statefreqpr=fixed(empirical);\n" % (
                                num + 1)
                        isAA = True
                # partition
                partition_block += "partition Names = %d:%s;\nset partition=Names;" % (
                    len(zip_data[1]), ", ".join(zip_data[1]))
                last_block = "prset applyto=(all) ratepr=variable;\nunlink statefreq=(all) revmat=(all) shape=(all) pinvar=(all) tratio=(all)"
                last_block = last_block + \
                    ";\nunlink brlens=(all)" if isAA else last_block
                last_block = "" if num == 0 else last_block  # 只有1个分区
                block = "\n".join(
                    [charset_block.strip(), partition_block, lset_block.strip(), last_block])
                block = block.replace(
                    "amodelpr=fixed(jtt)", "amodelpr=fixed(jones)")  # 替换为贝叶斯支持的模型
                self.textEdit.setText(block)

    @pyqtSlot()
    def on_pushButton_close_clicked(self):
        """
        close
        """
        self.close()

    def closeEvent(self, e):
        text = self.textEdit.toPlainText()
        if "############Auto Input############\n" not in text:
            self.on_pushButton_blk_clicked()  # 生成命令
        self.guiCloseSig.emit()


class NexView(QDialog, Ui_nexViewer, object):

    def __init__(self, parent=None):
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        super(NexView, self).__init__(parent)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.resize(800, 600)
        self.setupUi(self)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        modifiers = QApplication.keyboardModifiers()
        if event.type() == QEvent.KeyPress:  # 首先得判断type
            if (modifiers == Qt.ControlModifier) and (event.key() == Qt.Key_F):
                self.popUpFandR()
                return True
        return super(NexView, self).eventFilter(obj, event)

    def popUpFandR(self):
        f = Find(parent=self.textEdit)
        f.show()


class MrBayes(QDialog, Ui_MrBayes, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    partitionDataSig = pyqtSignal(list)
    mrbayes_exception = pyqtSignal(str)
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
            autoMSA=None,
            input_model=None,
            workPath=None,
            focusSig=None,
            MB_exe=None,
            workflow=False,
            parent=None):
        super(MrBayes, self).__init__(parent)
        self.parent = parent
        self.function_name = "MrBayes"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig if focusSig else pyqtSignal(
            str)  # 为了方便workflow
        self.workflow = workflow
        self.MB_exe = MB_exe
        self.autoMSA = autoMSA[0] if type(autoMSA) == list else autoMSA
        self.input_model = input_model
        self.setupUi(self)
        # 保存设置
        if not workflow:
            self.MrBayes_settings = QSettings(
                self.thisPath + '/settings/MrBayes_settings.ini', QSettings.IniFormat)
        else:
            self.MrBayes_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.MrBayes_settings.beginGroup("Workflow")
            self.MrBayes_settings.beginGroup("temporary")
            self.MrBayes_settings.beginGroup('MrBayes')
        # File only, no fallback to registry or or.
        self.MrBayes_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.interrupt = False
        self.run_from_text = False
        self.spinBox_2.valueChanged.connect(self.ctrlBurin)
        self.pushButton_partition.toggled.connect(self.popup_partition)
        self.checkBox_4.toggled.connect(self.judgeMPI)
        # 恢复用户的设置
        self.guiRestore()
        # 判断程序的版本
        self.version = ""
        version_worker = WorkThread(
            lambda : self.factory.get_version("MrBayes", self),
            parent=self)
        version_worker.start()
        #
        # 必须放到恢复界面过后执行
        if self.autoMSA:
            self.input_nex(self.autoMSA)
        if self.input_model:
            self.input_models()
        else:
            if self.autoMSA:
                if "PartFind_results" in self.autoMSA:
                    self.judgePFresults()
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.logGuiSig.connect(self.addText2Log)
        self.lineEdit.installEventFilter(self)
        self.log_gui = self.gui4Log()
        self.checkBox.toggled.connect(self.setBurnin)
        self.checkBox_2.toggled.connect(self.setBurnin)
        self.lineEdit.deleteFile.clicked.connect(
            self.clear_lineEdit)  # 删除了内容，也要把tooltip删掉
        self.lineEdit.autoDetectSig.connect(self.popupAutoDec)
        self.setBurnin(True)
        self.comboBox_6.currentIndexChanged[str].connect(self.ctrlGammaCat)
        self.comboBox_4.activated[str].connect(self.popupDirichlet)
        self.comboBox_5.activated[str].connect(self.ctrlOutgroupLable)
        self.ctrlGammaCat(self.comboBox_6.currentText())
        # self.pushButton_partition.clicked.connect(self.popup_partition)
        self.partitionDataSig.connect(self.ctrlResizedColumn)
        self.mrbayes_exception.connect(self.popup_MrBayes_exception)
        self.comboBox_5.setTopText()
        self.nex_file_name = "input.nex"
        # 控制partition配置窗口是否打开
        self.popup_part_window = True
        # 给开始按钮添加菜单
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        self.work_action = QAction(QIcon(":/picture/resourses/work.png"), "", menu)
        self.work_action.triggered.connect(lambda: self.factory.swithWorkPath(self.work_action, parent=self))
        self.dir_action = QAction(QIcon(":/picture/resourses/folder.png"), "Output Dir: ", menu)
        self.dir_action.triggered.connect(lambda: self.factory.set_direct_dir(self.dir_action, self))
        menu.addAction(self.work_action)
        menu.addAction(self.dir_action)
        self.pushButton.toolButton.setMenu(menu)
        self.pushButton.toolButton.menu().installEventFilter(self)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下
        if platform.system().lower() == "linux":
            self.checkBox_4.setEnabled(True)
            self.configureMPI()  # 初始化MPI
            self.spinBox_7.valueChanged.connect(self.configureMPI)
            self.spinBox_8.valueChanged.connect(self.configureMPI)
        else:
            self.checkBox_4.setEnabled(False)
            self.comboBox_10.setEnabled(False)
        #给结束按钮添加菜单
        menu2 = QMenu(self)
        menu2.setToolTipsVisible(True)
        action_infer = QAction(QIcon(":/picture/resourses/if_Delete_1493279.png"), "Stop the run and infer the tree", menu2,
                         triggered=self.viewResultsEarly)
        menu2.addAction(action_infer)
        self.pushButton_2.toolButton.setMenu(menu2)
        self.pushButton_2.toolButton.menu().installEventFilter(self)
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-12-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-12-1-Brief-example"
        self.label_9.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)

    @pyqtSlot()
    def on_pushButton_clicked(self, fromText=None, nex_name="input.nex", skip=False, workflow=False, haveExportPath=False):
        """
        execute program
        """
        # sumCmdBlock生成nex block
        if self.isRunning():
            QMessageBox.information(
                self,
                "MrBayes",
                "<p style='line-height:25px; height:25px'>MrBayes is running!</p>")
            return
        self.interrupt = False
        self.nex_file_name = nex_name
        # nex内容来源
        if fromText:
            final_nex_content = fromText  # 适用于nexViewer里面的save and run，直接跑导入的文件，以及续跑
        else:
            #由程序生成
            cmd_block = self.sumCmdBlock()
            if not cmd_block:
                return
            self.nex_content = re.sub(
                r"(?si)begin mrbayes;(.+)end;", "", self.nex_content).strip()  # 防止有block在里面
            final_nex_content = self.nex_content + "\n" + cmd_block
        if not haveExportPath:
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath +
                                                      os.sep + "MrBayes_results" + os.sep + self.output_dir_name)
        else:
            self.exportPath = haveExportPath
            # 这里删除文件,必须在这里，否则会报错
        if (not skip) or workflow:
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                # 提醒是否删除旧结果，如果用户取消，就不执行
                return
        self.totbl_generations = int(
            re.search(r"(?i)ngen=(\d+)\b", final_nex_content).group(1))
        # 统一一下log，免得出错
        final_nex_content = re.sub(
            r"log start filename ?\=.+;", "log start filename = log.txt;", final_nex_content)
        os.chdir(self.exportPath)
        with open(nex_name, "w", encoding="utf-8") as f:
            f.write(final_nex_content)
        # 描述
        runs = re.search(r"nruns ?\= ?(\d+)", final_nex_content).group(
            1) if re.search(r"nruns ?\= ?(\d+)", final_nex_content) else "2"
#         generations = re.search(r"ngen ?\= ?(\d+)", final_nex_content).group(
#             1) if re.search(r"ngen ?\= ?(\d+)", final_nex_content) else ""
        generations = "xxxx"
        if "relburnin" in final_nex_content:
            frac = float(
                re.search(r"burninfrac ?\= ?(0\.\d+)", final_nex_content).group(1)) * 100
            burnin = '%.0f' % frac + \
                "% of" if re.search(
                    r"burninfrac ?\= ?(0\.\d+)", final_nex_content) else ""
        else:
            burnin = re.search(r"burnin ?\= ?(\d+)", final_nex_content).group(
                1) if re.search(r"burnin ?\= ?(\d+)", final_nex_content) else ""
        if ("charset" in final_nex_content) and ("partition" in final_nex_content) and ("applyto" in final_nex_content):
            model_des = "partition"
        else:
            if hasattr(self, "model4des"):
                model_des = self.model4des
            else:
                model_des = "N/A"
        self.description = '''Bayesian Inference phylogenies were inferred using MrBayes v%s (Ronquist et al., 2012) under %s model (%s parallel runs, %s generations), in which the initial %s sampled data were discarded as burn-in.''' % (
            self.version, model_des, runs, generations, burnin)
        self.reference = "Ronquist, F., Teslenko, M., van der Mark, P., Ayres, D.L., Darling, A., Höhna, S., Larget, B., Liu, L., Suchard, M.A., Huelsenbeck, J.P., 2012. MrBayes 3.2: efficient Bayesian phylogenetic inference and model choice across a large model space. Syst. Biol. 61, 539-542."
        if self.checkBox_4.isEnabled() and self.checkBox_4.isChecked():
            ##MPI方式运行
            MPIpath = self.factory.programIsValid("mpi", mode="tool")
            threads = self.comboBox_10.currentText()
            self.commands = "\"%s\" -n %s \"%s\" \"%s\""%(MPIpath, threads, self.MB_exe, nex_name)
        else:
            self.commands = f"\"{self.MB_exe}\" \"{nex_name}\""
        self.mb_popen = self.factory.init_popen(self.commands)
        self.factory.emitCommands(self.logGuiSig, "cd %s\n%s"%(self.exportPath, self.commands))
        self.worker = WorkThread(self.run_command, parent=self)
        self.worker.start()

    @pyqtSlot()
    def on_pushButton_continue_clicked(self):
        """
        continue
        """
        if self.isRunning():
            QMessageBox.information(
                self,
                "MrBayes",
                "<p style='line-height:25px; height:25px'>MrBayes is running!</p>")
            return
        resultsPath = None
        ##choose work folder
        if os.path.exists(self.workPath + os.sep + "MrBayes_results"):
            list_result_dirs = sorted([i for i in os.listdir(self.workPath + os.sep + "MrBayes_results")
                                       if os.path.isdir(self.workPath + os.sep + "MrBayes_results" + os.sep + i)],
                                      key=lambda x: os.path.getmtime(self.workPath + os.sep + "MrBayes_results" + os.sep + x), reverse=True)
            if list_result_dirs:
                item, ok = QInputDialog.getItem(self, "Choose previous results",
                                                "Previous results:", list_result_dirs, 0, False)
                if ok and item:
                    resultsPath = self.workPath + os.sep + "MrBayes_results" + os.sep + item
        else:
            QMessageBox.information(
                self,
                "MrBayes",
                "<p style='line-height:25px; height:25px'>No previous MrBayes analysis found in %s!</p>"%os.path.normpath(self.workPath))
            return
        previous_run = self.havePreviousRun(resultsPath)
        if previous_run == "addition":
            i, ok = QInputDialog.getInt(self,
                                        "Specify generation to run", "Additional Generation:", 1000000, 0, 99999999, 1000)
            if ok:
                # 统一一下log，免得出错
                self.previous_nex_content = re.sub(r"log start filename ?\=.+;", "log start filename = log.txt;",
                                                   self.previous_nex_content)
                total_gen = self.nex_gen + i
                previous_nex_content_add = re.sub(
                    r"(?i)(?<=ngen\=)\d+\b", str(total_gen), self.previous_nex_content)
                if "append=yes" not in previous_nex_content_add:
                    previous_nex_content_add = re.sub(r"(mcmcp[^;]+);", "\\1 append=yes;", previous_nex_content_add)
                # previous_nex_content_add.replace(
                #     "checkpoint=yes checkfreq=5000", "checkpoint=yes checkfreq=5000 append=yes")
                self.on_pushButton_clicked(
                    previous_nex_content_add, os.path.basename(self.previous_nex_file), skip=True, haveExportPath=resultsPath)
        elif previous_run == "unfinished":
            # 统一一下log，免得出错
            self.previous_nex_content = re.sub(r"log start filename ?\=.+;", "log start filename = log.txt;",
                                               self.previous_nex_content)

            previous_nex_content_unfinished = re.sub(r"(mcmcp[^;]+);", "\\1 append=yes;",
                                                     self.previous_nex_content) if "append=yes" not in \
                                                            self.previous_nex_content else self.previous_nex_content
            # previous_nex_content_unfinished = self.previous_nex_content.replace(
            #     "checkpoint=yes checkfreq=5000", "checkpoint=yes checkfreq=5000 append=yes")
            self.on_pushButton_clicked(previous_nex_content_unfinished, os.path.basename(
                self.previous_nex_file), skip=True, haveExportPath=resultsPath)
        # else:
        #     path2 = os.path.normpath(resultsPath) if resultsPath \
        #         else os.path.normpath(self.workPath + os.sep + "MrBayes_results")
        #     QMessageBox.information(
        #         self,
        #         "MrBayes",
        #         "<p style='line-height:25px; height:25px'>No previous analysis found in %s!</p>"%path2)

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
        fileName = QFileDialog.getOpenFileName(
            self, "Input alignment file",
            filter="Nexus Format(*.nex *.nexus *.nxs);;")
        if fileName[0]:
            self.input_nex(fileName[0])

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
            # self.comboBox_5.setEnabled(True)

    @pyqtSlot()
    def on_pushButton_2_clicked(self, silence=False):
        """
        Stop
        """
        if self.isRunning():
            if (not silence) and (not self.workflow):
                country = self.factory.path_settings.value("country", "UK")
                url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-12-1-Brief-example" if \
                    country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-12-1-Brief-example"
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    "<p style='line-height:25px; height:25px'>MrBayes is still running, terminate it? <br>Tips:<br>"
                    "--You can infer the tree via the \"red down arrow\".<br>"
                    "--You can continue this analysis via the \"Continue Previous Analysis\" Button.<br>"
                    "--For a brief example, please click <a href=\"%s\">here</a></p>"%url,
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
            else:
                reply = QMessageBox.Yes
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.mb_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.mb_popen.pid), signal.SIGTERM)
                    self.mb_popen = None
                    self.interrupt = True
                except:
                    # print("stop failed")
                    self.mb_popen = None
                    self.interrupt = True
            if not silence and reply == QMessageBox.Yes:
                if not self.workflow:
                    QMessageBox.information(
                        self,
                        "MrBayes",
                        "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])
            return True
        else:
            return False

    @pyqtSlot()
    def on_pushButton_10_clicked(self):
        """
        show nex
        """
        self.showNEX = NexView()
        self.showNEX.toolButton.clicked.connect(self.setWordWrap_nex)
        self.showNEX.pushButton.clicked.connect(self.save_nex_to_file)
        self.showNEX.pushButton_2.clicked.connect(self.save_and_run)
        self.showNEX.pushButton_cancel.clicked.connect(self.showNEX.close)
        cmd_block = self.sumCmdBlock()
        if cmd_block:
            self.nex_content = re.sub(
                r"(?si)begin mrbayes;(.+)end;", "", self.nex_content).strip()  # 防止有block在里面
            self.showNEX.textEdit.setText(self.nex_content + "\n" + cmd_block)
            self.showNEX.setWindowFlags(
                self.showNEX.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.showNEX.exec_()

    def run_command(self):
        try:
            # 清空文件夹，放在这里方便统一报错
            self.time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            self.run_MB()  # 线程读取输出
            self.summary()
            if not self.interrupt:
                ok = self.judgeFinish()
                if not ok:
                    country = self.factory.path_settings.value("country", "UK")
                    url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#7-3-MrBayes-does-not-work" if \
                        country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#7-3-MrBayes-does-not-work"
                    self.mrbayes_exception.emit("MrBayes stopped abnormally. Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail! You may copy the command (%s)"
                                                " to the terminal to debug it. For details, please visit"
                                                " <a href=\"%s\">here</a>."%(self.MB_exe, url))
                    status = "except"
                else:
                    status = "stop"
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
                    self.workflow_finished.emit("MrBayes finished")
                    return
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        self.progressBar,
                        status,
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
        self.MrBayes_settings.setValue('size', self.size())
        # self.MrBayes_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.MrBayes_settings.setValue(name, index)
            elif isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.MrBayes_settings.setValue(name, state)
            elif isinstance(obj, QSpinBox):
                value = obj.value()
                self.MrBayes_settings.setValue(name, value)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.MrBayes_settings.setValue(name, float_)
            elif isinstance(obj, QPushButton):
                if name == "pushButton_partition":
                    state = obj.isChecked()
                    self.MrBayes_settings.setValue(name, state)

    def guiRestore(self):

        # Restore geometry
        height = 750 if platform.system().lower() == "darwin" else 594
        size = self.factory.judgeWindowSize(self.MrBayes_settings, 896, height)
        self.resize(size)
        self.factory.centerWindow(self)
        # self.move(self.MrBayes_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox) and name not in ["comboBox_7", "comboBox_5", "comboBox_10"]:
                allItems = [obj.itemText(i) for i in range(obj.count())]
                index = self.MrBayes_settings.value(name, "0")
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
            elif isinstance(obj, QCheckBox):
                value = self.MrBayes_settings.value(
                    name, None)  # get stored value from registry
                if value:
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QSpinBox):
                ini_value = obj.value()
                value = self.MrBayes_settings.value(name, ini_value)
                obj.setValue(int(value))
            elif isinstance(obj, QDoubleSpinBox):
                ini_float_ = obj.value()
                float_ = self.MrBayes_settings.value(name, ini_float_)
                obj.setValue(float(float_))
            elif isinstance(obj, QPushButton):
                if name == "pushButton_partition":
                    value = self.MrBayes_settings.value(
                        name, None)  # get stored value from registry
                    if value:
                        self.popup_part_window = False
                        obj.setChecked(
                            self.factory.str2bool(value))
            # elif isinstance(obj, QLineEdit):
            #     if self.autoMSA and name == "lineEdit":
            #         self.input_nex(self.autoMSA)
            #         if self.input_model:
            #             self.input_models()

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
        self.closeSig.emit("MrBayes", self.fetchWorkflowSetting())
        # 取消选中文字
        self.checkBox_3.setFocus()
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
            self.ui_closeSig.emit("MrBayes")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            # print(self.isRunning())
            reply = QMessageBox.question(
                self,
                "MrBayes",
                "<p style='line-height:25px; height:25px'>MrBayes is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.mb_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.mb_popen.pid), signal.SIGTERM)
                    self.mb_popen = None
                    self.interrupt = True
                except:
                    self.mb_popen = None
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
                    if os.path.splitext(files[0])[1].upper() in [".NEX", ".NEXUS", "NXS"]:
                        self.input_nex(files[0])
                    else:
                        QMessageBox.information(
                            self,
                            "MrBayes",
                            "<p style='line-height:25px; height:25px'>File should end with '.nex', 'nxs' or '.nexus'</p>",
                            QMessageBox.Ok)
        if (event.type() == QEvent.Show):
            if obj == self.pushButton.toolButton.menu():
                if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+",
                             self.dir_action.text()) or self.dir_action.text() == "Output Dir: ":
                    self.factory.sync_dir(self.dir_action)  ##同步文件夹名字
                menu_x_pos = self.pushButton.toolButton.menu().pos().x()
                menu_width = self.pushButton.toolButton.menu().size().width()
                button_width = self.pushButton.toolButton.size().width()
                pos = QPoint(menu_x_pos - menu_width + button_width,
                             self.pushButton.toolButton.menu().pos().y())
                self.pushButton.toolButton.menu().move(pos)
            if obj == self.pushButton_2.toolButton.menu():
                menu_x_pos = self.pushButton_2.toolButton.menu().pos().x()
                menu_width = self.pushButton_2.toolButton.menu().size().width()
                button_width = self.pushButton_2.toolButton.size().width()
                pos = QPoint(menu_x_pos - menu_width + button_width,
                             self.pushButton_2.toolButton.menu().pos().y())
                self.pushButton_2.toolButton.menu().move(pos)
            return True
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(MrBayes, self).eventFilter(obj, event)  # 0

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of MrBayes:")
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
            with open(self.exportPath + os.sep + "PhyloSuite_MrBayes.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "MrBayes", "log", "text Format(*.txt)")
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

    def setBurnin(self, bool_):
        if self.checkBox.isChecked():
            self.doubleSpinBox_2.setEnabled(True)
            self.spinBox_10.setEnabled(False)
        elif self.checkBox_2.isChecked():
            self.spinBox_10.setEnabled(True)
            self.doubleSpinBox_2.setEnabled(False)

    def getOutgroups(self, file):
        # outgroup
        command = f"\"{self.MB_exe}\" \"{file}\""
        popen = self.factory.init_popen(command)
        # 自己读序列，读到标志性的位置就退出
        self.outgroups = []
        try:
            while True:
                try:
                    out_line = popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = popen.stdout.readline().decode("gbk", errors="ignore")
                rgx = re.compile(r"Taxon\s+\d+\s+->\s+([^\n]+)\n")
                if rgx.search(out_line.rstrip()):
                    self.outgroups.append(rgx.search(out_line.rstrip()).group(1))
                if out_line == "" and popen.poll() is not None:
                    break
        except:
            pass
        if not self.outgroups:
            # print("read from alignment")
            parseFmt = Parsefmt()
            parseFmt.readfile(file)
            dict_taxon = parseFmt.dict_taxon
            self.outgroups = sorted(dict_taxon)

    def changeOutgroup(self):
        model = self.comboBox_5.model()
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
        self.comboBox_5.setTopText()

    def input_nex(self, file):
        base = os.path.basename(file)
        self.lineEdit.setText(base)
        self.lineEdit.setToolTip(file)
        with open(file, encoding="utf-8", errors="ignore") as f:
            self.nex_content = f.read()

        # outgroups
        outgroup_worker = WorkThread(
            lambda : self.getOutgroups(file),
            parent=self)
        outgroup_worker.finished.connect(self.changeOutgroup)
        outgroup_worker.start()

        if re.search(r"(?si)begin mrbayes;(.+)end;", self.nex_content):
            reply = QMessageBox.information(
                self,
                "MrBayes",
                "<p style='line-height:25px; height:25px'>MrBayes command block found, run directly?</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.pushButton_10.setEnabled(False)
                self.run_from_text = True  # 从导入的文件开跑
                self.nex_content = self.nex_content.replace(" append=yes", "") #去除续跑标记
                self.on_pushButton_clicked(self.nex_content)
                return
            else:
                self.nex_content = re.sub(
                    r"(?si)begin mrbayes;(.+)end;", "", self.nex_content)

        # Model
        self.seq_type = re.search(
            r"datatype=(\w+)", self.nex_content, re.I).group(1)
        list_nuc_models = ["JC", "F81", "K80 (K2P)", "HKY", "TrNef", "TrN", "K81", "K81uf", "TIMef", "TIM", "TVMef", "TVM",
                           "SYM", "GTR", "TPM2", "TPM2uf", "TPM3", "TPM3uf", "TIM2ef", "TIM2", "TIM3ef", "TIM3"]
        list_aa_models = ["Blosum62", "Blosum", "Cprev", "Dayhoff", "Equalin", "GTR", "Jones", "Jones (JTT)", "Mixed", "Mtmam", "Mtrev", "Poisson",
                          "Rtrev", "Vt", "Wag", "LG"]
        self.comboBox_7.clear()
        model = self.comboBox_7.model()
        if self.seq_type.upper() == "PROTEIN":
            for num, i in enumerate(list_aa_models):
                item = QStandardItem(i)
                # 背景颜色
                if num % 2 == 0:
                    item.setBackground(QColor(255, 255, 255))
                else:
                    item.setBackground(QColor(237, 243, 254))
                model.appendRow(item)
        elif self.seq_type.upper() in ["DNA", "RNA"]:
            for num, i in enumerate(list_nuc_models):
                item = QStandardItem(i)
                # 背景颜色
                if num % 2 == 0:
                    item.setBackground(QColor(255, 255, 255))
                else:
                    item.setBackground(QColor(237, 243, 254))
                model.appendRow(item)

    def input_models(self):
        if "partition PartitionFinder" in self.input_model:
            # partition finder结果
            self.input_model = re.sub(
                r"^partitionfinder ", "", self.input_model)
            self.pushButton_partition.setChecked(True)
            self.popup_partition(True, auto=True)
            self.partDefine.textEdit.setHtml(
                "<font color='red'>############Auto Input############<br></font>" + self.input_model.replace("\n",
                                                                                                             "<br>"))
        elif self.input_model:
            # ModelFinder finder结果
            self.input_model = re.sub(r"^modelfinder ", "", self.input_model)
            # print(self.input_model)
            # if "+ASC" in self.input_model:
            #     self.input_model = self.input_model.replace("+ASC", "")
            if ":" in self.input_model:
                # partition
                # re.search(r"(?s)begin sets;(.+)charpartition", self.input_model).group(1).strip()
                charset_block = ""
                dict_name_replace = {}
                rgx_charset = re.compile(r"(charset (.+?) = [^\n]+?;)")
                if rgx_charset.search(self.input_model):
                    for num, i in enumerate(rgx_charset.findall(self.input_model)):
                        #('charset cox1_mafft_gb = 478-2001;', 'cox1_mafft_gb')
                        dict_name_replace[i[1]] = "subset%d" % (num + 1)
                        charset_block += i[0].replace(i[1],
                                                      dict_name_replace[i[1]]) + "\n"
                else:
                    charset_block = re.search(
                        r"(?s)begin sets;(.+)charpartition", self.input_model).group(1).strip()
                charset_block = charset_block.strip()
                list_model_sub = re.findall(
                    r"([^ ]+?)\: ([^ ]+?)[,|;]", self.input_model)
                lset_block = ""
                partition_block = ""
                isAA = False
                list_names = []
                for num, subset in enumerate(list_model_sub):
                    # lset
                    model, name = subset
                    name = dict_name_replace[
                        name] if name in dict_name_replace else name
                    list_names.append(name)
                    # Rate var
                    if "+G" in model.upper() and "+I" in model:
                        rates = " rates=invgamma"
                    elif "+G" in model.upper():
                        rates = " rates=gamma"
                    elif "+I" in model.upper():
                        rates = " rates=propinv"
                    else:
                        rates = ""
                    dict_models = {"JC": "1", "F81": "1", "K80": "2", "HKY": "2", "TrNef": "6", "TrN": "6", "K81": "6",
                                   "K81uf": "6", "K2P": "2", "JC69": "1", "HKY85": "2", "K3P": "6",
                                   "TIMef": "6", "TIM": "6", "TVMef": "6", "TVM": "6", "SYM": "6", "GTR": "6",
                                   "TPM2": "6",
                                   "TPM2uf": "6", "TPM3": "6", "TPM3uf": "6", "TIM2ef": "6", "TIM2": "6", "TIM3ef": "6",
                                   "TIM3": "6"}
                    model_name = model.split("+")[0]
                    if model_name in dict_models:
                        lset_block += "lset applyto=(%d) nst=%s%s;\n" % (
                            num + 1, dict_models[model_name], rates)
                    else:
                        # AA序列
                        lset_block += "lset applyto=(%d)%s;\n" % (
                            num + 1, rates)
                        lset_block += "prset applyto=(%d) aamodelpr=fixed(%s);\n" % (
                            num + 1, model_name.lower())
                        if "+F" in model.upper():
                            lset_block += "prset applyto=(%d) statefreqpr=fixed(empirical);\n" % (
                                num + 1)
                        isAA = True
                # partition
                partition_block += "partition Names = %d:%s;\nset partition=Names;" % (
                    len(list_names), ", ".join(list_names))
                last_block = "prset applyto=(all) ratepr=variable;\nunlink statefreq=(all) revmat=(all) shape=(all) pinvar=(all) tratio=(all)"
                last_block = last_block + \
                    ";\nunlink brlens=(all)" if isAA else last_block
                last_block = "" if num == 0 else last_block  # 只有1个分区
                block = "\n".join(
                    [charset_block, partition_block, lset_block.strip(), last_block])
                self.pushButton_partition.setChecked(True)
                self.popup_partition(True, auto=True)
                block = block.replace(
                    "amodelpr=fixed(jtt)", "amodelpr=fixed(jones)")
                self.partDefine.textEdit.setHtml(
                    "<font color='red'>############Auto Input############<br></font>" + block.replace("\n", "<br>"))
            else:
                self.pushButton_partition.setEnabled(False)
                model_split = self.input_model.split("+")
                dict_1 = {"K80": "K2P", "Jones": "JTT"}  # 替换名字
                model = model_split[0]
                if model in dict_1:
                    rgx = r"%s \(%s\)" % (model, dict_1[model])
                    index = self.comboBox_7.findText(rgx, Qt.MatchRegExp)
                elif model in list(dict_1.values()):
                    rgx = r"%s \(%s\)" % (
                        list(dict_1.keys())[list(dict_1.values()).index(model)], model)
                    index = self.comboBox_7.findText(rgx, Qt.MatchRegExp)
                else:
                    index = self.comboBox_7.findText(
                        model, Qt.MatchFixedString)
                if index >= 0:
                    self.comboBox_7.setCurrentIndex(index)
                else:
                    QMessageBox.information(
                        self,
                        "MrBayes",
                        "<p style='line-height:25px; height:25px'>Model invalid!</p>",
                        QMessageBox.Ok)
                    return
                if re.search(r"\+F\b", self.input_model):
                    self.comboBox_4.setCurrentIndex(2)
                else:
                    self.comboBox_4.setCurrentIndex(0)
                if "+G" in self.input_model:
                    if re.search(r"G(\d+)", self.input_model):
                        category = re.search(
                            r"G(\d+)", self.input_model).group(1)
                    else:
                        category = "4"
                    self.spinBox.setValue(int(category))
                # Rate var
                if "+G" in self.input_model and "+I" in self.input_model:
                    self.comboBox_6.setCurrentIndex(4)
                elif "+G" in self.input_model:
                    self.comboBox_6.setCurrentIndex(1)
                elif "+I" in self.input_model:
                    self.comboBox_6.setCurrentIndex(3)
                else:
                    self.comboBox_6.setCurrentIndex(0)
                self.pushButton_partition.setChecked(False)

    def ctrlBurin(self, value):
        sampleFreq = self.spinBox_6.value()
        self.spinBox_10.setValue(value / sampleFreq / 4)

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "mb_popen") and self.mb_popen and not self.interrupt

    def clear_lineEdit(self):
        sender = self.sender()
        lineEdit = sender.parent()
        lineEdit.setText("")
        lineEdit.setToolTip("")
        self.comboBox_5.clear()
        self.ctrlOutgroupLable("")
        self.comboBox_5.setTopText()

    def ctrlGammaCat(self, text):
        if "gamma" not in text:
            self.spinBox.setEnabled(False)
            self.label_28.setEnabled(False)
        else:
            self.spinBox.setEnabled(True)
            self.label_28.setEnabled(True)

    def popup_partition(self, bool_, auto=False):
        self.ctrl_model_par_state(bool_)
        if self.pushButton_partition.isChecked():
            if not hasattr(self, "partDefine"):
                self.partDefine = PartDefine(self)
                header = ["Model", "Subset Name", "", "Start", "", "Stop"]
                ini_array = [["", "", "=", "", "-", ""],
                             ["", "", "=", "", "-", ""],
                             ["", "", "=", "", "-", ""],
                             ["", "", "=", "", "-", ""]
                             ]
                header, array = self.MrBayes_settings.value(
                    "partition defination", [header, ini_array])
                model = MyPartDisplayTableModel(array, header, parent=self)
                self.partDefine.tableView_partition.setModel(model)
                self.ctrlResizedColumn(array)  # 先执行一次改变列的宽度
                self.partDefine.pushButton_2.clicked.connect(self.addRow)
                self.partDefine.pushButton.clicked.connect(self.deleteRow)
                self.partDefine.pushButton_adp.clicked.connect(
                    self.addPartition)
                self.partDefine.pushButton_delp.clicked.connect(
                    self.delPartition)
                self.partDefine.guiCloseSig.connect(self.savePartDefine)
                self.partDefine.setWindowFlags(
                    self.partDefine.windowFlags() | Qt.WindowMinMaxButtonsHint)
            if (not auto) and hasattr(self, "popup_part_window") and self.popup_part_window:
                if self.input_model:
                    for i in [self.partDefine.tableView_partition, self.partDefine.pushButton_2,
                              self.partDefine.pushButton, self.partDefine.pushButton_adp,
                              self.partDefine.pushButton_delp, self.partDefine.pushButton_blk]:
                        i.setEnabled(False)
                self.partDefine.show()
            else:
                #刷新这个变量
                self.popup_part_window = True

    def addRow(self):
        """
        add row
        """
        currentModel = self.partDefine.tableView_partition.model()
        if currentModel:
            currentData = currentModel.arraydata
            currentModel.layoutAboutToBeChanged.emit()
            list_data = []
            for i in currentData[-1]:
                if i in ["=", "-", " "]:
                    list_data.append(i)
                else:
                    list_data.append("")
            currentData.append(list_data)
            currentModel.layoutChanged.emit()
            self.partitionDataSig.emit(currentData)
            self.partDefine.tableView_partition.scrollToBottom()

    def deleteRow(self):
        """
        delete row
        """
        indices = self.partDefine.tableView_partition.selectedIndexes()
        currentModel = self.partDefine.tableView_partition.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in indices), reverse=True)
            for row in rows:
                currentModel.layoutAboutToBeChanged.emit()
                currentData.pop(row)
                currentModel.layoutChanged.emit()
            self.partitionDataSig.emit(currentData)

    def addPartition(self):
        """
        add column
        """
        currentModel = self.partDefine.tableView_partition.model()
        if currentModel:
            currentData = currentModel.arraydata
            header = currentModel.header
            header += [" ", "Start", "", "Stop"]
            currentModel.layoutAboutToBeChanged.emit()
            for i in currentData:
                i += [" ", "", "-", ""]
            currentModel.layoutChanged.emit()
            self.partitionDataSig.emit(currentData)
            self.partDefine.tableView_partition.scrollToBottom()

    def delPartition(self):
        currentModel = self.partDefine.tableView_partition.model()
        if currentModel:
            currentData = currentModel.arraydata
            header = currentModel.header
            if header[-4:] == [' ', 'Start', '', 'Stop'] and header[-5] != "Subset Name":
                currentModel.layoutAboutToBeChanged.emit()
                del header[-4:]
                for num, i in enumerate(currentData):
                    currentData[num] = i[:-4]
                currentModel.layoutChanged.emit()
                self.partitionDataSig.emit(currentData)

    def ctrlResizedColumn(self, array):
        # array = self.partDefine.tableView_partition.model().arraydata
        resizeColums = [
            num for num, i in enumerate(array[0]) if i in ["=", "-", " "]]
        for j in resizeColums:
            self.partDefine.tableView_partition.horizontalHeader().setSectionResizeMode(
                j, QHeaderView.ResizeToContents)

    def savePartDefine(self):
        currentData = self.partDefine.tableView_partition.model().arraydata
        header = self.partDefine.tableView_partition.model().header
        self.MrBayes_settings.setValue(
            "partition defination", [header, currentData])

    def popupDirichlet(self, curentText):
        if "dirichlet" in curentText:
            dialog = QDialog(self)
            self.dirichlet = Ui_Dirichlet()
            self.dirichlet.setupUi(dialog)
            self.dirichlet.lineEdit.setInputMask('9.9,9.9,9.9,9.9;_')
            self.dirichlet.lineEdit.setText("1.0,1.0,1.0,1.0")
            self.dirichlet.toolButton.clicked.connect(self.addDirichlet)
            self.dirichlet.toolButton_2.clicked.connect(self.delDirichlet)
            self.dirichlet.pushButton.clicked.connect(dialog.accept)
            self.dirichlet.pushButton.clicked.connect(dialog.close)
            self.dirichlet.pushButton_2.clicked.connect(dialog.close)
            if dialog.exec_() == QDialog.Accepted:
                text = self.dirichlet.lineEdit.text().replace(",.", "")
                self.comboBox_4.setItemText(0, "dirichlet(%s)" % text)

    def addDirichlet(self):
        text = self.dirichlet.lineEdit.text()
        number = text.count(",") + 1
        self.dirichlet.lineEdit.setInputMask(
            '%s;_' % ("9.9," * (number + 1)).strip(","))

    def delDirichlet(self):
        text = self.dirichlet.lineEdit.text()
        number = text.count(",") + 1
        self.dirichlet.lineEdit.setInputMask(
            '%s;_' % ("9.9," * (number - 1)).strip(","))

    def sumCmdBlock(self):
        if (not hasattr(self, "partDefine")) and self.pushButton_partition.isChecked():
            QMessageBox.critical(
                self,
                "MrBayes",
                "<p style='line-height:25px; height:25px'>Please configure partitions first!</p>")
            self.popup_partition(True)
            return
        alignment = self.isFileIn()
        if alignment:
            if re.search(r"(?si)begin mrbayes;(.+)end;", self.nex_content):
                return re.search(r"(?si)begin mrbayes;(.+)end;", self.nex_content).group()
            # 有数据才执行
            # self.exportPath = self.factory.creat_dir(self.workPath + \
            #                                          os.sep + "MrBayes_results")
            # self.factory.remove_dir(self.exportPath)
            list_blocks = ["begin mrbayes"]
            if self.checkBox_3.isChecked():
                list_blocks += ["log start filename = log.txt"]
            # input
            outgroups = [self.comboBox_5.itemText(i) for i in range(self.comboBox_5.count())
                         if self.comboBox_5.model().item(i).checkState() == Qt.Checked]
            if outgroups:
                list_blocks += ["outgroup " + j for j in outgroups]
            # lset
            if not self.pushButton_partition.isChecked():
                rate_var = self.comboBox_6.currentText().split()[0]
                dict_rate_abbre = {
                    "gamma": "+G", "propinv": "+I", "invgamma": "+I+G", "equal": "", "lnorm": "", "adgamma": ""}
                f = "+F" if "empirical" in self.comboBox_4.currentText() else ""
                model_text = self.comboBox_7.currentText().split(" ")[0]
                self.model4des = model_text + dict_rate_abbre[rate_var] + f
                Ngammacat = " Ngammacat=%d" % self.spinBox.value(
                ) if self.spinBox.isEnabled() else ""
                if self.seq_type.upper() == "DNA":
                    dict_models = {"JC": "1", "F81": "1", "K80": "2", "HKY": "2", "TrNef": "6", "TrN": "6", "K81": "6", "K81uf": "6",
                                   "TIMef": "6", "TIM": "6", "TVMef": "6", "TVM": "6", "SYM": "6", "GTR": "6", "TPM2": "6",
                                   "K2P": "2", "JC69": "1", "HKY85": "2", "K3P": "6", "TPM2uf": "6", "TPM3": "6",
                                   "TPM3uf": "6", "TIM2ef": "6", "TIM2": "6", "TIM3ef": "6", "TIM3": "6"}
                    list_blocks += ["lset nst=%s rates=%s" %
                                    (dict_models[model_text], rate_var) + Ngammacat]
                elif self.seq_type.upper() == "PROTEIN":
                    list_blocks += ["lset rates=%s" % rate_var + Ngammacat]
                    list_blocks += [
                        "prset Aamodelpr=fixed(%s)" % model_text.lower()]
                # prset
                stateFreq = "" if self.comboBox_4.currentText() == "dirichlet(1.0,1.0,1.0,1.0)" \
                    else "prset statefreqpr = %s" % self.comboBox_4.currentText()
                list_blocks += [stateFreq]
            else:
                part_blk = self.partDefine.textEdit.toPlainText().replace(
                    "############Auto Input############\n", "")
                list_blocks += part_blk.split(";\n")
            # mcmc
            list_blocks += ["mcmcp ngen=%d printfreq=1000 samplefreq=%d nchains=%d nruns=%d savebrlens=yes checkpoint=yes checkfreq=5000" %
                            (self.spinBox_2.value(), self.spinBox_6.value(), self.spinBox_8.value(), self.spinBox_7.value())]
            list_blocks += ["mcmc"]
            # sumt
            burin = "relburnin=yes burninfrac=%.2f" % self.doubleSpinBox_2.value(
            ) if self.checkBox.isChecked() else "burnin=%d" % self.spinBox_10.value()
            list_blocks += ["sumt conformat=%s contype=%s %s" %
                            (self.comboBox_9.currentText(), self.comboBox_8.currentText(), burin)]
            # sump
            list_blocks += ["sump %s" % burin]
            list_blocks += ["end;"]
            while "" in list_blocks:
                # 清空 空白项
                list_blocks.remove("")
            cmd_blk = ";\n".join(list_blocks)
            cmd_blk = cmd_blk.replace(
                "amodelpr=fixed(jtt)", "amodelpr=fixed(jones)")
            return re.sub(r";{2,}", ";", cmd_blk)  # 替换掉多个分号
        else:
            QMessageBox.critical(
                self,
                "MrBayes",
                "<p style='line-height:25px; height:25px'>Please input files first!</p>")
            return None

    def setWordWrap_nex(self):
        button = self.sender()
        if button.isChecked():
            button.setChecked(True)
            self.showNEX.textEdit.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            button.setChecked(False)
            self.showNEX.textEdit.setLineWrapMode(QTextEdit.NoWrap)

    def save_nex_to_file(self):
        content = self.showNEX.textEdit.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "MrBayes", "input", "Nexus Format(*.nex)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    def save_and_run(self):
        content = self.showNEX.textEdit.toPlainText()
        self.showNEX.close()
        self.on_pushButton_clicked(content)

    def ctrlOutgroupLable(self, text):
        OutgroupNum = len([self.comboBox_5.itemText(i) for i in range(
            self.comboBox_5.count()) if self.comboBox_5.model().item(i).checkState() == Qt.Checked])
        self.label_31.setText("Outgroup(%d):" % OutgroupNum)

    def run_MB(self):
        # 用线程读取输出
        rgx_start_chain = re.compile(
            r"Chain results \((\d+) generations requested\)")
        rgx_generation = re.compile(r"(\d+) \-\- [([]")
        rgx_asdsf = re.compile(
            r"Average standard deviation of split frequencies:[^\n]+")
        is_error = False  ##判断是否出了error
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = self.mb_popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = self.mb_popen.stdout.readline().decode("gbk", errors="ignore")
                if out_line == "" and self.mb_popen.poll() is not None:
                    break
                if rgx_start_chain.search(out_line):
                    self.progressSig.emit(5)
                    self.workflow_progress.emit(5)
                elif rgx_generation.search(out_line):
                    generation_current = int(
                        rgx_generation.search(out_line).group(1))
                    self.progressSig.emit(
                        5 + generation_current * 95 / self.totbl_generations)
                    self.workflow_progress.emit(
                        5 + generation_current * 95 / self.totbl_generations)
                elif rgx_asdsf.search(out_line):
                    self.label_8.setText(rgx_asdsf.search(out_line).group())
                self.logGuiSig.emit(out_line.strip())
                if re.search(r"(?i)^ +Error in command", out_line):
                    is_error = True
                    # self.on_pushButton_9_clicked()
            else:
                break
        if is_error:
            self.interrupt = True
            self.mrbayes_exception.emit(
                "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!")
        self.mb_popen = None  # 运行完赋值none，方便判断是否在运行

    def popup_MrBayes_exception(self, text):
        QMessageBox.information(
            self,
            "MrBayes",
            "<p style='line-height:25px; height:25px'>%s</p>" % text)
        if "Show log" in text:
            self.on_pushButton_9_clicked()

    def havePreviousRun(self, path=None):
        if not path:
            return None
        have_ckp, have_nex = False, False
        for i in os.listdir(path):
            if os.path.splitext(i)[1].upper() in [".CKP", ".CKP~"]:
                if not have_ckp:
                    ckp_file = os.path.normpath(path + os.sep + i)
                    have_ckp = True
            elif os.path.splitext(i)[1].upper() in [".NEX", ".NEXUS", "NXS"]:
                if i != "stop_run.nex":
                    self.previous_nex_file = path + os.sep + i
                    have_nex = True
        if have_ckp and have_nex:
            f1 = self.factory.read_file(ckp_file)
            ckp_content = f1.read()
            f1.close()
            f2 = self.factory.read_file(self.previous_nex_file)
            self.previous_nex_content = f2.read()
            f2.close()
            if re.search(r"\[generation: (\d+)\]", ckp_content) and re.search(r"(?i)ngen=(\d+)\b", self.previous_nex_content):
                ckp_gen = int(
                    re.search(r"\[generation: (\d+)\]", ckp_content).group(1))
                self.nex_gen = int(
                    re.search(r"(?i)ngen=(\d+)\b", self.previous_nex_content).group(1))
                if (self.nex_gen - ckp_gen) < 10000:
                    # 跑完了
                    return "addition"
                else:
                    return "unfinished"
            else:
                return None
        return None

    def workflow_input(self, input_MSA=None, model=None):
        self.lineEdit.setText("")
        if input_MSA:
            input_MSA = input_MSA[0] if type(input_MSA) == list else input_MSA
            if ("PartFind_results" in input_MSA) and not (model): #判断PF2是否有结果
                self.judgePFresults()
            if not (os.path.splitext(input_MSA)[1].upper() in [".NEX", ".NXS", ".NEXUS"]):
                convertfmt = Convertfmt(
                    **{"export_path": os.path.dirname(input_MSA), "files": [input_MSA], "export_nexi": True})
                convertfmt.exec_()
                input_MSA = convertfmt.f3
            self.input_nex(input_MSA)
        if model:
            self.input_model = model
            self.input_models()

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect(
            "MrBayes", self.workPath, self.auto_popSig, self)

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

    def fetchWorkflowSetting(self):
        '''* models: auto detect from last step
          * if partition model
          * state freq
          * rate Var
          * Gamma catergory (if +G select)
          * generation, sample freq, runs, chains
          * burnin: fraction or number
          * contype
          * conformat'''
        settings = '''<p class="title">***MrBayes***</p>'''
        ifPartition = 'Yes <span style="font-weight:600; color:green;">(auto configure according to the results of previous step)</span>' \
            if self.pushButton_partition.isChecked() else "No"
        settings += '<p>Partition mode: <a href="self.MrBayes_exe' \
                    ' factory.highlightWidgets(x.pushButton_partition)">%s</a></p>' % ifPartition
        if ifPartition == "No":
            settings += '<p>Models: <span style="font-weight:600; color:green;">auto detect from previous step</span></p>'
        # state_freq = self.comboBox_4.currentText()
        settings += '<p>State frequency: <span style="font-weight:600; color:green;">auto detect from previous step' \
                    '</span><</p>'
        # rate_var = self.comboBox_6.currentText()
        settings += '<p>Rate variation: <span style="font-weight:600; color:green;">auto detect from previous step' \
                    '</span></p>'
        if self.label_28.isEnabled():
            # category = self.spinBox.value()
            settings += '<p>Rate categories for the gamma distribution: ' \
                        '<span style="font-weight:600; color:green;">auto detect from previous step</span></p>'
        generation = self.spinBox_2.value()
        settings += '<p>Generations: <a href="self.MrBayes_exe spinBox_2.setFocus() spinBox_2.selectAll()' \
                    ' factory.highlightWidgets(x.spinBox_2)">%s</a></p>' % generation
        sample_freq = self.spinBox_6.value()
        settings += '<p>Sample frequency: <a href="self.MrBayes_exe spinBox_6.setFocus() spinBox_6.selectAll()' \
                    ' factory.highlightWidgets(x.spinBox_6)">%s</a></p>' % sample_freq
        runs = self.spinBox_7.value()
        settings += '<p>Number of Runs: <a href="self.MrBayes_exe spinBox_7.setFocus() spinBox_7.selectAll()' \
                    ' factory.highlightWidgets(x.spinBox_7)">%s</a></p>' % runs
        chains = self.spinBox_8.value()
        settings += '<p>Number of Chains: <a href="self.MrBayes_exe spinBox_8.setFocus() spinBox_8.selectAll()' \
                    ' factory.highlightWidgets(x.spinBox_8)">%s</a></p>' % chains
        if self.checkBox.isChecked():
            burin_frac = self.doubleSpinBox_2.value()
            settings += '<p>Burnin Fraction: <a href="self.MrBayes_exe doubleSpinBox_2.setFocus()' \
                        ' doubleSpinBox_2.selectAll() factory.highlightWidgets(x.doubleSpinBox_2)">%s</a></p>' % burin_frac
        if self.checkBox_2.isChecked():
            burin = self.spinBox_10.value()
            settings += '<p>Burnin: <a href="self.MrBayes_exe spinBox_10.setFocus() spinBox_10.selectAll()' \
                        ' factory.highlightWidgets(x.spinBox_10)">%s</a></p>' % burin
        contype = "50% majority rule tree" if self.comboBox_8.currentText() == "Halfcompat"\
            else "majority rule consensus tree with all compatible clades added"
        settings += '<p>Type of consensus tree: <a href="self.MrBayes_exe comboBox_8.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_8)">%s</a></p>' % contype
        comformat = "consensus tree formatted for the program FigTree" if self.comboBox_9.currentText() == "Figtree"\
            else "simple consensus tree"
        settings += '<p>Consensus tree format: <a href="self.MrBayes_exe comboBox_9.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_9)">%s</a></p>' % comformat
        if self.comboBox_10.isEnabled():
            threads = self.comboBox_10.currentText()
            settings += '<p>Threads: <a href="self.MrBayes_exe comboBox_10.showPopup()' \
                        ' factory.highlightWidgets(x.comboBox_10)">%s</a></p>' % threads
        return settings

    def showEvent(self, event):
        QTimer.singleShot(100, lambda: self.showSig.emit(self))

    def isFileIn(self):
        alignment = self.lineEdit.toolTip()
        if os.path.exists(alignment):
            return alignment
        else:
            return False

    def viewResultsEarly(self):
        ok = self.on_pushButton_2_clicked(silence=True) #先结束线程
        if not ok: return
        if not self.workflow:
            QMessageBox.information(
                self,
                "MrBayes",
                "<p style='line-height:25px; height:25px'>If the results are not converged, "
                "you can continue the analysis via \"Continue Previous Analysis\" button!</p>")
        self.summary()  # 统计结果
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "reading trees...", busy=True, parent=self)
        self.progressDialog.show()
        QApplication.processEvents()
        self.worker = WorkThread(
            self.viewResultsEarly_workFun, parent=self)
        self.worker.finished.connect(lambda:
                                         [self.progressDialog.close(), self.stop_early_message(),
                                          self.focusSig.emit(self.exportPath),
                                          self.on_pushButton_2_clicked(silence=True)])
        self.worker.start()

    def viewResultsEarly_workFun(self):
        run_t_files = glob.glob("./*.t")
        print(run_t_files)
        # 添加end给树文件
        if run_t_files:
            for i in run_t_files:
                with open(i, "a", encoding="utf-8") as f:
                    f.write("\nend;")
        else:
            self.progressDialog.close()
            return
#         self.stop_run_progress(2)
        # 复制一份nex文件
        with open(self.nex_file_name, encoding="utf-8", errors='ignore') as f1:
            nex_content = f1.read()
        # rgx_outgroup = re.compile(r"(?ism)^(outgroup.+?;)")
        # rgx_charset = re.compile(r"(?ism)^(charset[^;]+?;)")
        # rgx_partition = re.compile(r"(?ism)^(partition[^;]+?;)")
        # rgx_set = re.compile(r"(?ism)^(set\s+partition=.+?;)")
        # rgx_lset = re.compile(r"(?ism)^(lset[^;]+?;)")
        # rgx_prset = re.compile(r"(?ism)^(prset[^;]+?;)")
        # rgx_unlink = re.compile(r"(?ism)^(unlink[^;]+?;)")
        # rgx_sumt = re.compile(r"(?ism)\s*sumt(.+?;)")
        # rgx_sump = re.compile(r"(?ism)\s*sump(.+?;)")
        # rgx_mb_block = re.compile(r"(?is)[^\n]*begin mrbayes.+?end;")
        # outgroups = rgx_outgroup.findall(nex_content) if rgx_outgroup.search(nex_content) else []
        # charsets = rgx_charset.findall(nex_content) if rgx_charset.search(nex_content) else []
        # partitions = rgx_partition.findall(nex_content) if rgx_partition.search(nex_content) else []
        # sets = rgx_set.findall(nex_content) if rgx_set.search(nex_content) else []
        # sumt = rgx_sumt.search(nex_content).group(1)
        # sump = rgx_sump.search(nex_content).group(1)
        # nex_content = [rgx_mb_block.sub("", nex_content)]
        # nex_content.append("begin mrbayes;\nlog start filename = log_stop.txt;")
        # if outgroups:
        #     nex_content.extend(outgroups)
        # if charsets:
        #     nex_content.extend(charsets)
        # if partitions:
        #     nex_content.extend(partitions)
        # if sets:
        #     nex_content.extend(sets)
        # nex_content.append("sumt filename=%s" % self.nex_file_name + sumt)
        # nex_content.append("sump filename=%s" % self.nex_file_name + sump)
        # nex_content.append("end;\n")
        rgx_mcmc = re.compile(r"(?ism)(mcmc[^p;]*?;)\n")
        rgx_mb_block = re.compile(r"(?is)[^\n]*begin mrbayes.+?end;")
        rgx_sumt = re.compile(r"(?ism)(sumt)(.+?;)")
        rgx_sump = re.compile(r"(?ism)(sump)(.+?;)")
        rgx_log = re.compile(r"(?ism)(log start filename = )(.+?);")
        if rgx_mb_block.search(nex_content):
            mb_block = rgx_mb_block.search(nex_content).group()
            mb_block = rgx_log.sub(r"\1log_stop.txt;", mb_block)
            mb_block = rgx_mcmc.sub("\n", mb_block)
            mb_block = rgx_sumt.sub(r"\1 filename=%s\2"%self.nex_file_name, mb_block)
            mb_block = rgx_sump.sub(r"\1 filename=%s\2"%self.nex_file_name, mb_block)
        else:
            return
        nex_content = f"{rgx_mb_block.sub('', nex_content)}\n{mb_block}\n"
        with open("stop_run.nex", "w") as f2:
            f2.write(nex_content)
        sum_commands = f"\"{self.MB_exe}\" stop_run.nex"
#         self.stop_run_progress(5)
        # 执行
        self.interrupt = False
        self.mb_popen = self.factory.init_popen(sum_commands)
        self.mb_popen.stdout.read()
#         rgx_tree_reading = re.compile(r"(?ms)^( +?)v.+?^\1\*+")
#         rgx_mb_end = re.compile(r"(?s)Reached end of file")
#         text = ""
#         while True:
#             QApplication.processEvents()
#             if self.mb_popen:
#                 try:
#                     out_line = self.mb_popen.stdout.readline().decode(
#                         "utf-8", errors="ignore")
#                 except UnicodeDecodeError:
#                     out_line = self.mb_popen.stdout.readline().decode(
#                         "gbk", errors="ignore")
#                 if out_line == "" and self.mb_popen.poll() is not None:
#                     break
#                 if "*" in out_line:
#                     print(out_line)
#                 if rgx_tree_reading.search(text):
#                     stars_text = rgx_tree_reading.search(text).group()
#                     if "*" in stars_text:
#                         stars_num = stars_text.count("*")
#                         print(stars_text, stars_num)
#                         self.stop_run_progress(10 + 80 * (int(stars_num) / 81))
#                 if rgx_mb_end.search(out_line):
#                     self.stop_run_progress(100)
#                 text += out_line

    def stop_early_message(self):
        if not self.workflow:
            reply = QMessageBox.information(
                self,
                "MrBayes",
                "<p style='line-height:25px; height:25px'>Results generated! Open the results folder?        </p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.factory.openPath(self.exportPath, self)
        self.startButtonStatusSig.emit(
            [
                self.pushButton,
                self.progressBar,
                "except",
                self.exportPath,
                self.qss_file,
                self])

#     def stop_run_progress(self, num):
#         oldValue = self.progressDialog.value()
#         done_int = int(num)
#         if done_int > oldValue:
#             self.progressDialog.setProperty("value", done_int)
#             QCoreApplication.processEvents()
#             if done_int == 100:
#                 self.progressDialog.close()

    def ctrl_model_par_state(self, bool_):
        ##partition选中的时候，其他的灰掉
        for i in [self.comboBox_7, self.comboBox_4, self.spinBox, self.comboBox_6, self.label_25, self.label_26, self.label_28, self.label_27]:
            i.setDisabled(bool_)

    def is_mpi_enabled(self):
        self.settings_ini = QSettings(
            self.thisPath + '/settings/setting_settings.ini', QSettings.IniFormat)
        self.settings_ini.setFallbacksEnabled(False)
        mb = self.settings_ini.value('MrBayes', "mb")
        mb = "mb" if not mb else mb  # 有时候路径为空
        try:
            popen = subprocess.Popen("%s -v"%mb, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        except:
            return "uninstall"
        stdout = ""
        while True:
            try:
                out_line = popen.stdout.readline().decode("utf-8", errors='ignore')
            except UnicodeDecodeError:
                out_line = popen.stdout.readline().decode("gbk", errors='ignore')
            if out_line == "" and popen.poll() is not None:
                break
            stdout += out_line
        return True if "(Parallel version)" in stdout else False

    def judgeMPI(self, checked):
        if checked:
            MPIpath = self.factory.programIsValid("mpi", mode="tool")
            # MB_mpi_enabled = self.is_mpi_enabled()
            if not MPIpath:
                reply = QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Please install MPICH2 first!</p>",
                    QMessageBox.Ok,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.setting = Setting(self)
                    self.setting.display_table(self.setting.listWidget.item(1))
                    # 隐藏？按钮
                    self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                    self.setting.exec_()
                self.checkBox_4.setChecked(False)
            # if not MB_mpi_enabled:
            #     QMessageBox.information(
            #         self,
            #         "Information",
            #         "<p style='line-height:25px; height:25px'>You need to enable parallel version of MrBayes first! "
            #         "See section 5.9.2 in the manual (3.2) to reinstall it.")
            #     self.checkBox_4.setChecked(False)

    def configureMPI(self):
        run = self.spinBox_7.value()
        chain = self.spinBox_8.value()
        total_chains = int(run*chain)
        cpu_num = multiprocessing.cpu_count()
        list_cpu = [str(i + 1) for i in range(cpu_num) if total_chains%(i+1) == 0]
        model = self.comboBox_10.model()
        self.comboBox_10.clear()
        for num, i in enumerate(list_cpu):
            item = QStandardItem(i)
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            model.appendRow(item)

    def summary(self):
        self.time_end = datetime.datetime.now()
        self.time_used = str(self.time_end - self.time_start)
        self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (
        str(self.time_start), str(self.time_end),
        self.time_used)
        # 得到到底跑了多少代
        run_t_files = glob.glob("./*.t")
        run_p_files = glob.glob("./*.p")
        ckp_files = glob.glob("./*.ckp") + glob.glob("./*.ckp~")
        if run_t_files or run_p_files:
            # 避免memory error，只读取部分文本
            try:
                with open(run_t_files[0], 'rb') as f2:
                    b_size = os.path.getsize(run_t_files[0])
                    seek_size = -30240 if b_size >= 30240 else -b_size
                    f2.seek(seek_size, os.SEEK_END)
                    run_t_content = str(f2.read(), "utf-8")
            except:
                run_t_content = ""
            try:
                with open(run_p_files[0], 'rb') as f3:
                    b_size = os.path.getsize(run_p_files[0])
                    seek_size = -30240 if b_size >= 30240 else -b_size
                    f3.seek(seek_size, os.SEEK_END) # 实现从末尾向前读
                    run_p_content = str(f3.read(), "utf-8")
            except:
                run_p_content = ""
            try:
                with open(ckp_files[0], encoding="utf-8", errors='ignore') as f4:
                    b_size = os.path.getsize(ckp_files[0])
                    read_size = 10240 if b_size >= 10240 else b_size
                    ckp_content = f4.read(read_size)
            except:
                ckp_content = ""
            if re.search(r"tree gen.(\d+?) = \[\&U\]", run_t_content):
                generation = re.findall(
                    r"tree gen.(\d+?) = \[\&U\]", run_t_content)[-1]
            elif re.search(r"^(\d+)\t", run_p_content):
                generation = re.findall(r"^(\d+)\t", run_p_content)[-1]
            elif re.search(r"\[generation: (\d+)\]", ckp_content):
                generation = re.search(r"\[generation: (\d+)\]", ckp_content).group(1)
            else:
                generation = "N/A"
            self.description = self.description.replace(
                "xxxx generations", "%s generations" % generation)
        else:
            self.description = self.description.replace(
                "xxxx generations", " generations")
        with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
            f.write(self.description +
                    "\n\nIf you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n"
                    "If you use MrBayes, please cite:\n" + self.reference + "\n\n" + self.time_used_des)

    def judgeFinish(self):
        # log = self.textEdit_log.toPlainText()
        tre_file = glob.glob(self.exportPath + os.sep + "*.tre")
        if not tre_file:
            return False
        return True

    def judgePFresults(self):
        QMessageBox.information(
            self,
            "IQ-TREE",
            "<p style='line-height:25px; height:25px'>Cannot find \"<span style='font-weight:600; color:#ff0000;'>best_scheme.txt</span>\" in \"<span style='font-weight:600; color:#ff0000;'>analysis</span>\" folder, "
            "PartitionFinder analysis seems to be unfinished!</p>")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = MrBayes()
    ui.show()
    sys.exit(app.exec_())
