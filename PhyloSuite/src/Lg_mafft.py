#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

import re
import signal
from collections import OrderedDict

import datetime
from Bio.Data import CodonTable
from Bio.Seq import _translate_str
import subprocess

from src.Lg_seqViewer import Seq_viewer
from uifiles.Ui_mafft import Ui_mafft
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from src.factory import Factory, WorkThread
import sys
import inspect
import traceback
import multiprocessing
import platform


class CodonAlign(object):  # 读取fasta文件

    def __init__(self, **kargs):
        self.factory = Factory()
        self.dict_args = kargs
        self.rdfas_codetable = int(self.dict_args["codon"])
        self.vessel = self.dict_args["vessel"]
        self.vessel_aalign = self.dict_args["vessel_aalign"]
        self.vessel_aaseq = self.dict_args["vessel_aaseq"]
        self.exportPath = self.dict_args["exportPath"]
        self.filenames = self.dict_args["filenames"]
        self.dict_file = {}  # 键为每个文件名，值为列表，列表内含元组；全局输出文件
        self.DictInterstop = OrderedDict()
        num = 0
        sums = len(self.filenames)
        for self.each_file in self.filenames:
            num += 1
            self.file_base = os.path.basename(self.each_file)
            self.read_fas(self.each_file)  # 生成dict_fas,循环一次就丢
            if self.dict_args["progressSig"]:
                self.dict_args["progressSig"].emit(
                    10 * (num / sums) * (1 / 5))  # read_fas占五分之一
                self.dict_args["workflow_progress"].emit(
                    10 * (num / sums) * (1 / 5))  # read_fas占五分之一
            self.dict_file[self.file_base] = {}
            self.translate()  # 翻译氨基酸，生成映射，存翻译后的AA文件
            if self.dict_args["progressSig"]:
                self.dict_args["progressSig"].emit(
                    10 * (num / sums))  # read_fas占五分之一
                self.dict_args["workflow_progress"].emit(
                    10 * (num / sums))  # read_fas占五分之一

    def read_fas(self, file):
        self.dict_fas = {}  # 实例化以后，用另一个变量替换这个,当读取多个文件的时候，这个字典会被刷新，解决这个问题
        with open(file, encoding="utf-8", errors='ignore') as File:
            line = File.readline()
            while line != '':
                while not line.startswith('>'):
                    line = File.readline()
                name = line
                seq = []
                line = File.readline()
                while not line.startswith('>') and line != '':
                    seq.append(line.strip().replace(' ', ''))
                    line = File.readline()
                name = ">" + \
                    self.factory.refineName(
                        name.strip().replace(">", "")) + "\n"
                self.dict_fas[name] = "".join(seq)

    def mapping(self, spe, nuc, pro):
        self.dict_file[self.file_base][spe] = []  # 字典里面套字典
        # num = 1
        for num, each_aa in enumerate(pro):
            num += 1
            self.dict_file[self.file_base][spe].append(
                (each_aa, nuc[(num - 1) * 3:num * 3]))
            # num += 1

    def trim_ter(self, spe, seq):
        '''
        比对前，预先去除终止密码子
        Parameters
        ----------
        spe
        seq

        Returns
        -------

        '''
        self.table = CodonTable.ambiguous_dna_by_id[self.rdfas_codetable]
        # 这里写一个在序列内部发现了gap，askquestion是否删除gap继续比对
        seq = seq.replace("-", "")  # 如果用户传入已经比对过的序列，则需要将其还原，否则biopython会报错
        size = len(seq)
        self.muti3 = True  # 预设这个值，因为当所有序列的值都是3的倍数的时候，会没有这个值
        if size % 3 == 0:
            if _translate_str(seq[-3:], self.table) == "*":  # 判定是否是终止子，是就去除
                self.trim_seq = seq[:-3]
            else:
                self.trim_seq = seq
        elif size % 3 == 1:
            if self.muti3:
                self.trim_seq = seq[:-1]
        elif size % 3 == 2:
            if self.muti3:
                self.trim_seq = seq[:-2]

    def translate(self):
        aa_fas = []
        for i in self.dict_fas:
            self.trim_ter(i, self.dict_fas[i])  # 生成self.trim_seq
            # myargs.table需要转换为table对象
            protein = _translate_str(self.trim_seq, self.table)
            # protein.rstrip("*") ?
            if "*" in protein:
                for num, aa in enumerate(protein):
                    if aa == "*":
                        initIndex = ((num + 1) * 3 - 3)
                        self.DictInterstop.setdefault(os.path.normpath(self.each_file),
                                                      []).append([i.strip().replace(">", ""), initIndex])
            aa_fas.append(i + protein + os.linesep)
            self.mapping(i, self.trim_seq, protein)
        with open(self.vessel_aaseq + os.sep + self.file_base, "w", encoding="utf-8") as f:
            f.write("".join(aa_fas))

    def locate(self):
        for i in self.aa_align:
            if i != "-":
                mapping = self.list_mapping.pop(0)  # 取出('M', 'atg')
                while mapping[0] == "*":
                    # 终止密码子会在比对的时候被mafft删除,因此需要跳过
                    mapping = self.list_mapping.pop(0)  # 取出('M', 'atg')
                assert i == mapping[0], mapping
                self.codon_seq.append(mapping[1])
            if i == "-":
                self.codon_seq.append("---")
        self.codon_seq.append("\n")

    def tocodon(self):
        # list_keys = sorted(list(self.dict_fas.keys()))
        self.codon_seq = []
        for i in self.dict_fas:  # >Benedenia_hoshinai
            self.codon_seq.append(i)
            self.aa_align = self.dict_fas[i]  # MI-NNILFYSYN-NQITNLVDS-
            # 得到映射的列表[('M', 'atg'), ('L', 'cta'), ('I', 'ata')]
            self.list_mapping = self.dict_file[self.each_aa_align][i]
            self.locate()
        split_ext = os.path.splitext(self.each_aa_align)  # 为了加后缀
        with open(self.exportPath + os.sep + "_mafft".join(split_ext), "w", encoding="utf-8") as f:
            f.write("".join(self.codon_seq))

    def back_trans(self):
        files = os.listdir(self.vessel_aalign)
        num = 0
        sums = len(files)
        for self.each_aa_align in files:
            num += 1
            # 生成dict_fas,循环一次就丢
            self.read_fas(self.vessel_aalign + os.sep + self.each_aa_align)
            if self.dict_args["progressSig"]:
                self.dict_args["progressSig"].emit(
                    90 + 10 * (num / sums) * (1 / 5))  # read_fas占五分之一
                self.dict_args["workflow_progress"].emit(
                    90 + 10 * (num / sums) * (1 / 5))  # read_fas占五分之一
            self.tocodon()  # 执行剩下的4/5
            if self.dict_args["progressSig"]:
                self.dict_args["progressSig"].emit(90 + 10 * (num / sums))
                self.dict_args["workflow_progress"].emit(90 + 10 * (num / sums))
        return [self.exportPath + os.sep + i for i in files]


class Mafft(QDialog, Ui_mafft, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    progressSig_each = pyqtSignal(int)
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    # interStopCodonSig = pyqtSignal(OrderedDict)
    # 用于flowchart自动popup combobox等操作
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    # 用于输入文件后判断用
    ui_closeSig = pyqtSignal(str)
    # 比对完有空文件报错
    emptySig = pyqtSignal(list)
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)

    def __init__(
            self,
            autoInputs=None,
            workPath=None,
            mafft_exe=None,
            clearFolderSig=None,
            focusSig=None,
            workflow=False,
            parent=None):
        super(Mafft, self).__init__(parent)
        self.parent = parent
        self.function_name = "MAFFT"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.clearFolderSig = clearFolderSig
        self.workflow = workflow
        self.mafft_interrupt = False
        self.workflowFinished = False
        self.mafft_exe = mafft_exe
        self.focusSig = focusSig if focusSig else pyqtSignal(
            str)  # 为了方便workflow
        self.setupUi(self)
        # 保存设置
        if not workflow:
            self.mafft_settings = QSettings(
                self.thisPath + '/settings/mafft_settings.ini', QSettings.IniFormat)
        else:
            self.mafft_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.mafft_settings.beginGroup("Workflow")
            self.mafft_settings.beginGroup("temporary")
            self.mafft_settings.beginGroup('MAFFT')
        # File only, no fallback to registry or or.
        self.mafft_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        # 判断程序的版本
        self.version = ""
        version_worker = WorkThread(
            lambda : self.factory.get_version("MAFFT", self),
            parent=self)
        version_worker.start()
        #
        self.sortAutoInputs(autoInputs)
        self.PCG_radioButton_2.toggled.connect(self.input)
        self.AA_radioButton_2.toggled.connect(self.input)
        self.RNAs_radioButton_2.toggled.connect(self.input)
        self.checkBox_2.toggled.connect(self.input)
        self.checkBox_2.toggled.connect(self.changeRadio)
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress_sums)
        self.progressSig_each.connect(self.runProgress_each)
        self.logGuiSig.connect(self.addText2Log)
        # self.interStopCodonSig.connect(self.popupInterStopCodon)
        self.comboBox_4.installEventFilter(self)
        self.comboBox_4.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        self.log_gui = self.gui4Log()
        self.emptySig.connect(self.popUpEmptyError)
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
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-2-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-2-1-Brief-example"
        self.label_7.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        """
        if self.isFileIn():
            # 有数据才执行
            self.mafft_interrupt = False
            self.dict_args = {}
            self.dict_args["mafft_exe"] = self.mafft_exe
            self.dict_args["exception_signal"] = self.exception_signal
            self.dict_args["progressSig"] = self.progressSig
            self.dict_args["progressSig_each"] = self.progressSig_each
            self.dict_args["workflow_progress"] = self.workflow_progress
            self.dict_args["PCG_NUC_files"] = self.PCG_NUC_files
            self.dict_args["PCG_AA_files"] = self.PCG_AA_files
            self.dict_args["RNAs_files"] = self.RNAs_files
            # if self.checkBox_2.isChecked() and self.checkBox_2.isEnabled():
            #     if self.AA_radioButton_2.isChecked():
            #         self.dict_args["filenames"] = self.PCG_AA_files
            #     elif self.PCG_radioButton_2.isChecked():
            #         self.dict_args["filenames"] = self.PCG_NUC_files
            #     elif self.RNAs_radioButton_2.isChecked():
            #         self.dict_args["filenames"] = self.RNAs_files
            # else:
            #     # 没有选中线粒体比对，按输入文件来，待写
            AllItems = self.comboBox_4.fetchListsText()
            self.dict_args["filenames"] = AllItems
            self.dict_args["workPath"] = self.workPath
            # 创建输出文件夹
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath +
                                                      os.sep + "mafft_results" + os.sep + self.output_dir_name)
            self.dict_args["exportPath"] = self.exportPath
            self.dict_args["codon"] = str(
                self.comboBox_9.currentText()).split(" ")[0]
            args = " " + \
                " ".join(
                    [i.text() for i in self.pushButton_par.menu().actions() if i.isChecked()])
            self.dict_args["arguments"] = args
            currentText1 = self.comboBox_3.currentText()
            if currentText1[0] == '1':
                strategy = ' --auto'
            elif currentText1[0] == '2':
                strategy = ' --retree 1'
            elif currentText1[0] == '3':
                strategy = ' --retree 2'
            elif currentText1[0] == '4':
                strategy = ' --globalpair --maxiterate 16'
            elif currentText1[0] == '5':
                strategy = ' --localpair --maxiterate 16'
            elif currentText1[0] == '6':
                strategy = ' --genafpair --maxiterate 16'
            self.dict_args["strategy"] = strategy
            currentText2 = self.comboBox_2.currentText()
            if currentText2[0] == '1':
                ch_out = ' --clustalout --reorder '
            elif currentText2[0] == '2':
                ch_out = ' --clustalout --inputorder '
            elif currentText2[0] == '3':
                ch_out = ' --reorder '
            elif currentText2[0] == '4':
                ch_out = ' --inputorder '
            elif currentText2[0] == '5':
                ch_out = ' --phylipout --reorder '
            elif currentText2[0] == '6':
                ch_out = ' --phylipout --inputorder '
            self.dict_args["exportfmt"] = ch_out
            if self.normal_radioButton.isChecked():
                mode = "normal"
            elif self.codon_radioButton.isChecked():
                mode = "codon"
            elif self.N2P_radioButton.isChecked():
                mode = "n2p"
            self.dict_args["mode"] = mode
            # codon模式只用fasta格式输出
            if mode == "codon" and ch_out not in [" --reorder ", " --inputorder "]:
                QMessageBox.information(
                    self,
                    "MAFFT",
                    "<p style='line-height:25px; height:25px'>Codon mode requires FASTA to be set as the export format (set automatically)</p>")
                self.comboBox_2.setCurrentIndex(3)
                self.dict_args["exportfmt"] = ' --inputorder '
            vessel = f"{self.dict_args['exportPath']}/mftvessel"
            if os.path.exists(vessel):
                # 如果有这个文件夹，就删掉
                self.clearFolderSig.emit(vessel)
            vessel_aaseq = f"{vessel}/AA_sequence"
            vessel_aalign = f"{vessel}/AA_alignments"
            self.dict_args["vessel"] = vessel
            self.dict_args["vessel_aaseq"] = vessel_aaseq
            self.dict_args["vessel_aalign"] = vessel_aalign
            # 运行描述
            sequence = "%d sequences were aligned in batches" % self.comboBox_4.count(
            ) if self.comboBox_4.count() > 1 else "1 sequence was aligned"
            if self.normal_radioButton.isChecked():
                mode = "normal"
            elif self.codon_radioButton.isChecked():
                mode = "codon"
            elif self.N2P_radioButton.isChecked():
                mode = "N2P"
            self.description = '''%s with MAFFT v%s (Katoh and Standley, 2013) using '%s' strategy and %s alignment mode.''' % (sequence,
                                                                                                                                self.version,
                                                                                                                            self.comboBox_3.currentText().split(
                                                                                                                                ". ")[1],
                                                                                                                            mode)
            self.reference = "Katoh, K., Standley, D.M., 2013. MAFFT multiple sequence alignment software version 7: improvements in performance and usability. Mol. Biol. Evol. 30, 772-780."

            ok = self.factory.remove_dir(
                self.dict_args["exportPath"], parent=self)
            if not ok:
                # 提醒是否删除旧结果，如果用户取消，就不执行
                return
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
        else:
            QMessageBox.critical(
                self,
                "MAFFT",
                "<p style='line-height:25px; height:25px'>Please input files first!</p>")

    def run_command(self):
        try:
            # 先清空文件夹
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    [self.progressBar, self.progressBar_2],
                    "start",
                    self.dict_args["exportPath"],
                    self.qss_file,
                    self])
            runState = self.align()
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                           self.time_used)
            with open(self.dict_args["exportPath"] + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(self.description +
                        "\n\nIf you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n"
                        "If you use MAFFT, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
            # 判断比对是否成功
            mafft_results = [self.dict_args["exportPath"] + os.sep + result for result in
                             os.listdir(self.dict_args["exportPath"]) if "_mafft" in result]
            empty_files = [os.path.basename(file) for file in mafft_results if os.stat(file).st_size == 0]
            if empty_files:
                self.emptySig.emit(empty_files)
            if (not self.mafft_interrupt) and (runState != "internal stop codon") and (not empty_files):
                if self.workflow:
                    # work flow跑的
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton,
                            [self.progressBar, self.progressBar_2],
                            "workflow stop",
                            self.dict_args["exportPath"],
                            self.qss_file,
                            self])
                    self.workflow_finished.emit("finished")
                    return
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        [self.progressBar, self.progressBar_2],
                        "stop",
                        self.dict_args["exportPath"],
                        self.qss_file,
                        self])
            else:
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        [self.progressBar, self.progressBar_2],
                        "except",
                        self.dict_args["exportPath"],
                        self.qss_file,
                        self])
            if not self.workflow:
                self.focusSig.emit(self.dict_args["exportPath"])
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    [self.progressBar, self.progressBar_2],
                    "except",
                    self.dict_args["exportPath"],
                    self.qss_file,
                    self])

    def align(self):
        ch_out = self.dict_args["exportfmt"]
        strategy = self.dict_args["strategy"]
        arg = self.dict_args["arguments"]
        # 尝试去除cmd窗口
        startupINFO = None
        if platform.system().lower() == "windows":
            startupINFO = subprocess.STARTUPINFO()
            startupINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupINFO.wShowWindow = subprocess.SW_HIDE
        if self.dict_args["mode"] == "codon":  # codon比对
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
                    return "internal stop codon"
            # if self.muti3:  # 用户选择继续再继续
            # 比对
            list_files = os.listdir(self.dict_args["vessel_aaseq"])
            file_sum = len(list_files)
            # 每个比对的有10个地方要检查
            # 比对环节占80%
            sums = file_sum
            num = 0
            file_num = 0
            for each_fas in list_files:
                file_num += 1
                self.label_3.setText(
                    str(file_num) + "/" + str(file_sum) + " file:")
                align_file = os.path.join(
                    self.dict_args["vessel_aaseq"], each_fas)
                commands = f'"{self.dict_args["mafft_exe"]}"{arg}{strategy}{ch_out}' \
                           f'"{align_file}" > "{self.dict_args["vessel_aalign"] + os.sep + each_fas}"'
                # commands = self.dict_args["mafft_exe"] + arg + strategy + ch_out + '"' + align_file + \
                #     '"' + ' > ' + '"' + \
                #     self.dict_args["vessel_aalign"] + os.sep + each_fas + '"'
                if platform.system().lower() == "windows":
                    self.mafft_popen = subprocess.Popen(
                        commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO)
                else:
                    self.mafft_popen = subprocess.Popen(
                        commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        startupinfo=startupINFO, shell=True, preexec_fn=os.setsid)
                stdout, num = self.run_mafft(
                    commands, self.mafft_popen, self.dict_args["progressSig"], self.dict_args["progressSig_each"], sums, num, proportion=80, base=10)
                self.progressSig_each.emit(0)
                if self.mafft_interrupt:
                    break
            self.factory.ctrl_file_label(self.label_3, "finished")
            # 避免关闭窗口了还继续进行下面的
            if not self.mafft_interrupt:
                self.mafft_output_files = codonAlign.back_trans(
                )  # 生成codon文件,占10%
            # 删除文件夹
            self.clearFolderSig.emit(self.dict_args["vessel"])

        elif self.dict_args["mode"] == "n2p":  # 核苷酸翻译为氨基酸比对模式
            self.factory.creat_dir(self.dict_args["vessel"])
            self.factory.creat_dir(self.dict_args["vessel_aaseq"])
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
                    return "internal stop codon"
                # codonAlign.DictInterstop["code table"] = self.dict_args["codon"]  # 记录code table信息
                # self.interStopCodonSig.emit(codonAlign.DictInterstop)
                # return "internal stop codon"
            list_files = os.listdir(self.dict_args["vessel_aaseq"])
            file_sum = len(list_files)
            sums = file_sum
            num = 0
            file_num = 0
            for each_fas in list_files:
                file_num += 1
                self.label_3.setText(
                    str(file_num) + "/" + str(file_sum) + " file:")
                align_file = os.path.join(
                    self.dict_args["vessel_aaseq"], each_fas)
                split_ext = os.path.splitext(each_fas)
                commands = f'"{self.dict_args["mafft_exe"]}"{arg}{strategy}{ch_out}' \
                           f'"{align_file}" > "{self.dict_args["exportPath"]}{os.sep}{"_mafft".join(split_ext)}"'
                # commands = self.dict_args["mafft_exe"] + arg + strategy + ch_out + '"' + align_file + \
                #     '"' + ' > ' + '"' + self.dict_args["exportPath"] + os.sep + \
                #     '_mafft'.join(split_ext) + '"'
                # if platform.system().lower() == "windows":
                #     self.mafft_popen = subprocess.Popen(
                #         commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO)
                # else:
                if platform.system().lower() == "windows":
                    self.mafft_popen = subprocess.Popen(
                        commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO)
                else:
                    self.mafft_popen = subprocess.Popen(
                        commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO,
                        shell=True, preexec_fn=os.setsid)

                stdout, num = self.run_mafft(
                    commands, self.mafft_popen, self.dict_args["progressSig"], self.dict_args["progressSig_each"], sums, num, proportion=90, base=10)
                self.progressSig_each.emit(0)
                if self.mafft_interrupt:
                    break
            self.factory.ctrl_file_label(self.label_3, "finished")
            self.clearFolderSig.emit(self.dict_args["vessel"])
            self.mafft_output_files = [
                self.dict_args["exportPath"] +
                os.sep +
                i for i in list_files]  # 返回输出文件的全路径
        else:  # 进行非codon比对模式
            list_files = self.dict_args["filenames"]
            file_sum = len(list_files)
            sums = file_sum
            num = 0
            file_num = 0
            for align_file in list_files:
                file_num += 1
                self.label_3.setText(
                    str(file_num) + "/" + str(file_sum) + " file:")
                each_fas = os.path.basename(align_file)
                split_ext = os.path.splitext(each_fas)
                commands = f'"{self.dict_args["mafft_exe"]}"{arg}{strategy}{ch_out}' \
                           f'"{align_file}" > "{self.dict_args["exportPath"]}{os.sep}{"_mafft".join(split_ext)}"'
                # commands = self.dict_args["mafft_exe"] + arg + strategy + ch_out + '"' + align_file + \
                #     '"' + ' > ' + '"' + self.dict_args["exportPath"] + os.sep + \
                #     '_mafft'.join(split_ext) + '"'
                # if platform.system().lower() == "windows":
                #     self.mafft_popen = subprocess.Popen(
                #         commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO)
                # else:
                if platform.system().lower() == "windows":
                    self.mafft_popen = subprocess.Popen(
                        commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO)
                else:
                    self.mafft_popen = subprocess.Popen(
                        commands, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=startupINFO,
                        shell=True, preexec_fn=os.setsid)
                stdout, num = self.run_mafft(
                    commands, self.mafft_popen, self.dict_args["progressSig"], self.dict_args["progressSig_each"], sums, num)
                self.progressSig_each.emit(0)
                if self.mafft_interrupt:
                    break
            self.factory.ctrl_file_label(self.label_3, "finished")
            # 返回输出文件的全路径
            self.mafft_output_files = [
                self.dict_args["exportPath"] +
                os.sep +
                os.path.basename(i) for i in list_files]

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
                    "<p style='line-height:25px; height:25px'>MAFFT is still running, terminate it?</p>",
                    QMessageBox.Yes,
                    QMessageBox.Cancel)
            else:
                reply = QMessageBox.Yes
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.mafft_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.mafft_popen.pid), signal.SIGTERM)
                    self.mafft_popen = None
                    self.mafft_interrupt = True
                except:
                    self.mafft_popen = None
                    self.mafft_interrupt = True
                if not self.workflow:
                    QMessageBox.information(
                        self,
                        "MAFFT",
                        "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton,
                        [self.progressBar, self.progressBar_2],
                        "except",
                        self.dict_args["exportPath"],
                        self.qss_file,
                        self])
#         if hasattr(self, "mafft_popen") and not self.mafft_popen.poll():
#             try:  # 运行过一次，再打开，如果没有运行，关闭窗口会报错
#                 self.mafft_interrupt = True
#                 # 可以杀死它和它的child进程
#                 try:
#                     if platform.system().lower() == "windows":
#                         subprocess.call(
#                             'taskkill /F /T /PID ' + str(self.mafft_popen.pid), shell=True)
#                     else:
#                         os.killpg(
#                             os.getpgid(self.mafft_popen.pid), signal.SIGTERM)
#                 except:
#                     pass
#                 if not self.workflow:
#                     QMessageBox.information(
#                         self,
#                         "MAFFT",
#                         "<p style='line-height:25px; height:25px'>Program has been terminated!</p>")
#                 self.startButtonStatusSig.emit(
#                     [
#                         self.pushButton,
#                         self.progressBar,
#                         "except",
#                         self.dict_args["exportPath"],
#                         self.qss_file,
#                         self])
#             except PermissionError:
#                 pass

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        open files
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input Files", filter="Fasta Format(*.fas *.fasta *.fsa);;")
        if fileNames[0]:
            self.checkBox_2.setChecked(False)
            self.input(fileNames[0])

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        show log
        """
        self.log_gui.show()

    def changeRadio(self, bool_):
        if bool_:
            if self.AA_radioButton_2.isChecked():
                self.normal_radioButton.setDisabled(False)
                self.codon_radioButton.setDisabled(True)
                self.N2P_radioButton.setDisabled(True)
            elif self.PCG_radioButton_2.isChecked():
                self.normal_radioButton.setDisabled(True)
                self.codon_radioButton.setDisabled(False)
                self.N2P_radioButton.setDisabled(False)
            elif self.RNAs_radioButton_2.isChecked():
                self.normal_radioButton.setDisabled(False)
                self.codon_radioButton.setDisabled(True)
                self.N2P_radioButton.setDisabled(True)
        else:
            self.normal_radioButton.setDisabled(False)
            self.codon_radioButton.setDisabled(False)
            self.N2P_radioButton.setDisabled(False)

    def input(self, list_items=None):
        if self.checkBox_2.isChecked() and self.checkBox_2.isEnabled():
            if self.AA_radioButton_2.isEnabled() and self.AA_radioButton_2.isChecked():
                self.comboBox_4.refreshInputs(self.PCG_AA_files, judge=False)
            elif self.PCG_radioButton_2.isEnabled() and self.PCG_radioButton_2.isChecked():
                self.comboBox_4.refreshInputs(self.PCG_NUC_files, judge=False)
            elif self.RNAs_radioButton_2.isEnabled() and self.RNAs_radioButton_2.isChecked():
                self.comboBox_4.refreshInputs(self.RNAs_files, judge=False)
        elif list_items:
            self.comboBox_4.refreshInputs(list_items)
        else:
            self.comboBox_4.refreshInputs([])

    def guiSave(self):
        # Save geometry
        self.mafft_settings.setValue('size', self.size())
        # self.mafft_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                if name != "comboBox_4":
                    index = obj.currentIndex()
                    self.mafft_settings.setValue(name, index)
                    # text = obj.currentText()
                    # if text:
                    #     allItems = [
                    #         obj.itemText(i) for i in range(obj.count())]
                    #     allItems.remove(text)
                    #     sortItems = [text] + allItems
                    #     self.mafft_settings.setValue(name, sortItems)
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.mafft_settings.setValue(name, state)
            if isinstance(obj, QRadioButton):
                state = obj.isChecked()
                self.mafft_settings.setValue(name, state)
            if isinstance(obj, QPushButton):
                if name == "pushButton_par":
                    actions = obj.menu().actions()
                    list_state = [i.isChecked() for i in actions]
                    options = [i.text() for i in actions]
                    self.mafft_settings.setValue(name, [options, list_state])

    def guiRestore(self):

        # Restore geometry
        self.resize(self.factory.judgeWindowSize(self.mafft_settings, 647, 483))
        self.factory.centerWindow(self)
        # self.move(self.mafft_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name != "comboBox_4":
                    # allItems = [obj.itemText(i) for i in range(obj.count())]
                    # values = self.mafft_settings.value(name, allItems)
                    # model = obj.model()
                    # obj.clear()
                    # for num, i in enumerate(values):
                    #     item = QStandardItem(i)
                    #     # 背景颜色
                    #     if num % 2 == 0:
                    #         item.setBackground(QColor(255, 255, 255))
                    #     else:
                    #         item.setBackground(QColor(237, 243, 254))
                    #     model.appendRow(item)
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.mafft_settings.value(name, "0") if name != "comboBox_2" \
                        else self.mafft_settings.value(name, "3")
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
                    if name == "comboBox_3":
                        obj.activated[str].connect(self.refreshPar)
            if isinstance(obj, QCheckBox):
                value = self.mafft_settings.value(
                    name, "true")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QRadioButton):
                value = self.mafft_settings.value(
                    name, "true")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QPushButton):
                if name == "pushButton_par":
                    list_options = ["--leavegappyregion", "--adjustdirection", "--adjustdirectionaccurately", "--thread 1", "--op 1.53",
                                    "--ep 0.123", "--kappa 2", "--lop -2.00", "--lep 0.1", "--lexp -0.1",
                                    "--LOP -6.00", "--LEXP 0.00", "--bl 62", "--jtt 1", "--tm 1", "--fmodel"]
                    ini_state = [False] * (len(list_options))
                    options, list_state = self.mafft_settings.value(
                        name, [list_options, ini_state])
                    # 更新以后，需要同步用户的参数
                    options = list_options if len(
                        list_options) > len(options) else options
                    list_state = ini_state if len(ini_state) > len(
                        list_state) else list_state
                    menu = QMenu(self)
                    menu.setToolTipsVisible(True)
                    for num, i in enumerate(options):
                        action = QAction(
                            i, menu, checkable=True)
                        action.setChecked(list_state[num])
                        menu.addAction(action)
                        if i == "--adjustdirection":
                            action.setToolTip("This function checks automatically whether any of the sequences in your "
                                              "alignment should be reverse-complemented")
                        elif i == "--adjustdirectionaccurately":
                            action.setToolTip(
                                "This is more accurate than \"--adjustdirection\", but slower")
                    menu.triggered.connect(self.fun_options)
                    obj.setMenu(menu)

    def runProgress_sums(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def runProgress_each(self, num):
        oldValue = self.progressBar_2.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar_2.setProperty("value", done_int)
            QCoreApplication.processEvents()
        if done_int == 0:
            self.progressBar_2.setProperty("value", 0)

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
        self.closeSig.emit("MAFFT", self.fetchWorkflowSetting())
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
            self.ui_closeSig.emit("MAFFT")
            # 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            reply = QMessageBox.question(
                self,
                "MAFFT",
                "<p style='line-height:25px; height:25px'>MAFFT is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                try:
                    self.worker.stopWork()
                    if platform.system().lower() in ["windows", "darwin"]:
                        self.mafft_popen.kill()
                    else:
                        os.killpg(os.getpgid(self.mafft_popen.pid), signal.SIGTERM)
                    self.mafft_popen = None
                    self.mafft_interrupt = True
                except:
                    self.mafft_popen = None
                    self.mafft_interrupt = True
            else:
                event.ignore()

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
                self.checkBox_2.setChecked(False)
                self.normal_radioButton.setDisabled(False)
                self.codon_radioButton.setDisabled(False)
                self.N2P_radioButton.setDisabled(False)
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
        return super(Mafft, self).eventFilter(obj, event)  # 0

    # 子线程run
    def run_mafft(self, commands, popen, progressSig, progressSig_each, sums, num, proportion=100, base=0):
        stdout = commands + "\n"
        num += 1
        progress_count = 0  # 有时候会有多个Progressive alignment
        base = base + (num - 1) * proportion / sums  # 当前文件到哪个base了
        each_file_proportion = proportion / sums
        self.factory.emitCommands(self.logGuiSig, commands)
        rgx_Progress = re.compile(
            r"Progressive alignment (\d+? *\/ *\d+?)?\.\.\.", re.I)
        rgx_Progress_step = re.compile(r"STEP +(\d+?) *\/ *(\d+?) ", re.I)
        rgx_Segment = re.compile(r"Segment +(\d+?) *\/ *(\d+?) ", re.I)
        rgx_Segment_sub = re.compile(r"\d+?\-\d+?\-\d+? ", re.I)
        rgx_finish = re.compile(r"^Strategy:")
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = popen.stdout.readline().decode("utf-8", errors='ignore')
                except UnicodeDecodeError:
                    out_line = popen.stdout.readline().decode("gbk", errors='ignore')
                if out_line == "" and popen.poll() is not None:
                    break
                if rgx_Progress.search(out_line):
                    if progress_count == 0:  # 首次出现的时候才执行
                        progressSig_each.emit(3)
                        progressSig.emit(base + each_file_proportion * 3 / 100)
                        self.workflow_progress.emit(
                            base + each_file_proportion * 3 / 100)
                    progress_num_str = rgx_Progress.search(out_line).group(1)
                    if progress_num_str:
                        progress_current_num = int(
                            progress_num_str.split("/")[0].strip())
                        progress_num = int(
                            progress_num_str.split("/")[-1].strip())
                    else:
                        progress_current_num = 0
                        progress_num = 0
                    progress_count += 1
                elif rgx_Progress_step.search(out_line):
                    # Progressive alignment占20
                    currentSTEP, totalSTEP = rgx_Progress_step.search(
                        out_line).groups()
                    currentSTEP, totalSTEP = int(currentSTEP), int(totalSTEP)
                    if progress_num:
                        # 有多个Progressive alignment情况
                        each_progress_proportion = 20 / progress_num
                        current_value = ((progress_current_num - 1) * 20 / progress_num) +\
                                        (each_progress_proportion * currentSTEP) / \
                            totalSTEP
                    else:
                        current_value = (20 * currentSTEP) / totalSTEP
                    progressSig_each.emit(3 + current_value)
                    progressSig.emit(
                        base + each_file_proportion * (3 + current_value) / 100)
                    self.workflow_progress.emit(
                        base + each_file_proportion * (3 + current_value) / 100)
                elif rgx_Segment.search(out_line):
                    # Progressive alignment占75
                    currentSEG, totalSEG = rgx_Segment.search(
                        out_line).groups()
                    currentSEG, totalSEG = int(currentSEG), int(totalSEG)
                    each_SEG_value = 75 / totalSEG
                    segment_count = 0  # 计算segment的个数
                elif rgx_Segment_sub.search(out_line):
                    # Progressive alignment占75
                    segment_count += 1
                    if segment_count <= (totalSTEP * 2):
                        # 每个segment都允许只统计2倍totalSTEP次
                        current_value = (
                            (currentSEG - 1) * 75 / totalSEG) + segment_count * each_SEG_value / (totalSTEP * 2)
                        progressSig_each.emit(23 + current_value)
                        progressSig.emit(
                            base + each_file_proportion * (23 + current_value) / 100)
                        self.workflow_progress.emit(
                            base + each_file_proportion * (23 + current_value) / 100)
                elif rgx_finish.search(out_line):
                    progressSig_each.emit(100)
                    progressSig.emit(base + each_file_proportion)
                    self.workflow_progress.emit(base + each_file_proportion)
                if out_line != "\n":
                    self.logGuiSig.emit(out_line.strip())
                # print(out_line)
                    #                     print(num_each)
                # stdout += out_line
                #         print(stdout)
            else:
                break
        self.mafft_popen = None
        return stdout, num

    def checkRadio(self):
        if self.PCG_radioButton_2.isChecked():
            self.codon_radioButton.setChecked(True)
        elif self.AA_radioButton_2.isChecked() or self.RNAs_radioButton_2.isChecked():
            self.normal_radioButton.setChecked(True)

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "mafft_popen") and self.mafft_popen and not self.mafft_interrupt
#         try:
#             out_line = self.mafft_popen.stdout.readline().decode("utf-8", errors="ignore")
#         except UnicodeDecodeError:
#             out_line = self.mafft_popen.stdout.readline().decode("gbk", errors="ignore")
#         if out_line == "" and self.mafft_popen.poll() is not None:
#             return False
#         else:
#             return True

    def fun_options(self, action):
        menu = self.sender()
        # self.actionName(menu)
        option = action.text()
        if "--thread" in option and action.isChecked():
            cpu_num = multiprocessing.cpu_count()
            list_cpu = [str(i + 1) for i in range(cpu_num)]
            current = cpu_num // 2
            item, ok = QInputDialog.getItem(
                self, "Specify thread number", "Thread:", list_cpu, current, False)
            if ok and item:
                action.setText("--thread %s" % item)
            else:
                action.setChecked(False)
        elif "--bl" in option and action.isChecked():
            opt, value = option.split(" ")
            item, ok = QInputDialog.getItem(
                self, "Custom value", "Choose value:", ["30", "45", "62", "80"])
            if ok and item:
                action.setText("--bl %s" % item)
            else:
                action.setChecked(False)
        elif action.isChecked() and (option not in ["--leavegappyregion", "--fmodel",
                                                    "--adjustdirection",
                                                    "--adjustdirectionaccurately"]):
            opt, value = option.split(" ")
            strategy = self.comboBox_3.currentText()[0]
            if opt in ["--lop", "--lep", "--lexp"] and strategy not in ["5", "6"]:
                QMessageBox.information(
                    self,
                    "MAFFT",
                    "<p style='line-height:25px; height:25px'>Please select <span style='font-weight:600; color:#ff0000;'>5. L-INS-i  (accurate)</span> or <span style='font-weight:600; color:#ff0000;'>6. E-INS-i  (accurate)</span> in <span style='font-weight:600; text-decoration: underline; color:#0000ff;'>Strategy</span> options first!</p>")
                action.setChecked(False)
            elif opt in ["--LOP", "--LEXP"] and strategy != "6":
                QMessageBox.information(
                    self,
                    "MAFFT",
                    "<p style='line-height:25px; height:25px'>Please select <span style='font-weight:600; color:#ff0000;'>6. E-INS-i  (accurate)</span> in <span style='font-weight:600; text-decoration: underline; color:#0000ff;'>Strategy</span> options first!</p>")
                action.setChecked(False)
            else:
                text, ok = QInputDialog.getText(self, "Custom value",
                                                "Set value:", QLineEdit.Normal, value)
                if ok and text:
                    action.setText(opt + " " + text)
                else:
                    action.setChecked(False)
        elif action.isChecked() and option == "--adjustdirection":
            list_ad_accur = [
                i for i in menu.actions() if i.text() == "--adjustdirectionaccurately"]
            ad_accur = list_ad_accur[0] if list_ad_accur else None
            if ad_accur:
                if ad_accur.isChecked():
                    ad_accur.setChecked(False)
        elif action.isChecked() and option == "--adjustdirectionaccurately":
            list_ad_accur = [
                i for i in menu.actions() if i.text() == "--adjustdirection"]
            ad_accur = list_ad_accur[0] if list_ad_accur else None
            if ad_accur:
                if ad_accur.isChecked():
                    ad_accur.setChecked(False)

    def refreshPar(self, text):
        if text not in ["6. E-INS-i  (accurate)"]:
            menu = self.pushButton_par.menu()
            for i in menu.actions():
                if ("--LOP" in i.text()) or ("--LEXP" in i.text()):
                    i.setChecked(False)
        if text not in ["6. E-INS-i  (accurate)", "5. L-INS-i  (accurate)"]:
            menu = self.pushButton_par.menu()
            for i in menu.actions():
                if ("--lop" in i.text()) or ("--lep" in i.text()) or ("--lexp" in i.text()):
                    i.setChecked(False)

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of MAFFT:")
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
            # print(text)
            self.textEdit_log.append(text)
            with open(self.exportPath + os.sep + "PhyloSuite_MAFFT.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "MAFFT", "log", "text Format(*.txt)")
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

    def workflow_input(self, inputs):
        # 如果没有导入序列，就设置非mt模式
        self.PCG_NUC_files, self.PCG_AA_files, self.RNAs_files = "", "", ""
        self.checkBox_2.setDisabled(True)
        self.AA_radioButton_2.setDisabled(True)
        self.PCG_radioButton_2.setDisabled(True)
        self.RNAs_radioButton_2.setDisabled(True)
        self.normal_radioButton.setDisabled(False)
        self.codon_radioButton.setDisabled(False)
        self.N2P_radioButton.setDisabled(False)
        self.input(inputs)

    @pyqtSlot(OrderedDict, result=bool)
    def popupInterStopCodon(self, dictInterStop):
        ## 存为文件
        def save2file(dictInterStop):
            list_ = [["File", "Species", "Site"]]
            # dictInterStop.pop("code table")
            for file, list_codons in dictInterStop.items():
                if file == "code table":
                    continue
                for species, codon_site in list_codons:
                    list_.append([os.path.basename(file), species, f"{codon_site+1}-{codon_site+4}"])
            with open(f"{self.exportPath}{os.sep}internal_stop_codons.tsv", "w") as f:
                f.write("\n".join(["\t".join(i) for i in list_]))
        saveFileWorker = WorkThread(lambda : save2file(dictInterStop), parent=self)
        saveFileWorker.start()
        # saveFileWorker.finished.connect(lambda : [])
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "<p style='line-height:25px; height:25px'>Internal stop codons found, view them? "
            "(also see \"internal_stop_codons.tsv\" file)</p>",
            QMessageBox.Yes,
            QMessageBox.Ignore)
        if reply == QMessageBox.Yes:
            self.seqViewer = Seq_viewer(
                self.workPath, dictInterStop, parent=self)
            # 添加最大化按钮
            self.seqViewer.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            self.seqViewer.show()
            return True
        else:
            return False

    def sortAutoInputs(self, autoInputs):
        if type(autoInputs) == tuple:
            # 证明是导入的提取的序列
            self.PCG_NUC_files, self.PCG_AA_files, self.RNAs_files = autoInputs
            if self.PCG_NUC_files or self.PCG_AA_files or self.RNAs_files:
                self.checkBox_2.setDisabled(False)
                self.checkBox_2.setChecked(True)
            if self.PCG_AA_files:
                self.AA_radioButton_2.setDisabled(False)
                self.AA_radioButton_2.setChecked(True)
            if self.PCG_NUC_files:
                self.PCG_radioButton_2.setDisabled(False)
                self.PCG_radioButton_2.setChecked(True)
            if self.RNAs_files:
                self.RNAs_radioButton_2.setDisabled(False)
                self.RNAs_radioButton_2.setChecked(True)
            self.input()
            self.checkRadio()
        elif autoInputs:
            self.PCG_NUC_files, self.PCG_AA_files, self.RNAs_files = "", "", ""
            self.checkBox_2.setDisabled(True)
            self.AA_radioButton_2.setDisabled(True)
            self.PCG_radioButton_2.setDisabled(True)
            self.RNAs_radioButton_2.setDisabled(True)
            self.normal_radioButton.setDisabled(False)
            self.codon_radioButton.setDisabled(False)
            self.N2P_radioButton.setDisabled(False)
            self.input(autoInputs)
        else:
            # 如果没有导入序列，就设置非mt模式
            self.PCG_NUC_files, self.PCG_AA_files, self.RNAs_files = "", "", ""
            self.checkBox_2.setDisabled(True)
            self.AA_radioButton_2.setDisabled(True)
            self.PCG_radioButton_2.setDisabled(True)
            self.RNAs_radioButton_2.setDisabled(True)
            self.normal_radioButton.setDisabled(False)
            self.codon_radioButton.setDisabled(False)
            self.N2P_radioButton.setDisabled(False)
            self.input()

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("MAFFT", self.workPath, self.auto_popSig, self)

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
            self.sortAutoInputs(autoInputs)

    def fetchWorkflowSetting(self):
        '''* Alignment Mode
          * Code table(if codon mode)
          * strategy
          * export format'''
        settings = '''<p class="title">***MAFFT***</p>'''
        if self.normal_radioButton.isChecked():
            algn_mode = "Normal"
        elif self.codon_radioButton.isChecked():
            algn_mode = "Codon"
        elif self.N2P_radioButton.isChecked():
            algn_mode = "N2P"
        settings += '<p>Alignment mode: <a href="self.MAFFT_exe factory.highlightWidgets(x.normal_radioButton,' \
                    'x.codon_radioButton,x.N2P_radioButton)">%s</a></p>' % algn_mode
        if algn_mode == "Codon":
            code_table = self.comboBox_9.currentText()
            settings += '<p>Code table: <a href="self.MAFFT_exe comboBox_9.showPopup()' \
                        ' factory.highlightWidgets(x.comboBox_9)">%s</a></p>' % code_table
        strategy = self.comboBox_3.currentText().split(maxsplit=1)[1]
        settings += '<p>Strategy: <a href="self.MAFFT_exe comboBox_3.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_3)">%s</a></p>' % strategy
        export_fmt = self.comboBox_2.currentText().split(maxsplit=1)[1]
        settings += '<p>Export Format: <a href="self.MAFFT_exe comboBox_2.showPopup()' \
                    ' factory.highlightWidgets(x.comboBox_2)">%s</a></p>' % export_fmt
        options = [i.text()
                   for i in self.pushButton_par.menu().actions() if i.isChecked()]
        if options:
            settings += '<p>Command line options: <a href="self.MAFFT_exe factory.highlightWidgets(x.pushButton_par)' \
                        ' pushButton_par.click()">%s</a></p>' % " | ".join(options)
        return settings

    def showEvent(self, event):
        QTimer.singleShot(100, lambda: self.showSig.emit(self))
        # self.showSig.emit(self)

    def isFileIn(self):
        return self.comboBox_4.count()

    def popUpEmptyError(self, files):
        input_files = self.comboBox_4.fetchListsText()
        error_input_files = [j for j in input_files if '_mafft'.join(os.path.splitext(os.path.basename(j))) in files]
        mafft_error, file_errors = "", ""
        base_files = [os.path.basename(i) for i in error_input_files]
        mafft_state = self.factory.checkPath(
            self.mafft_exe.strip("\""), mode="silence", parent=self, allow_space=True)
        if mafft_state != True:
            illegalTXT, path_text = mafft_state
            mafft_error += path_text + "<br>"
        message_files = error_input_files[:2] if len(error_input_files) > 2 else error_input_files
        for i in message_files:
            state = self.factory.checkPath(
                i, mode="silence", parent=self, allow_space=True)
            if state != True:
                illegalTXT, path_text = state
                file_errors += path_text + "<br>"
        file_errors = file_errors + " ..." if len(error_input_files) > 2 else file_errors
        list_errors = []
        if mafft_error:
            list_errors.append("MAFFT")
        if file_errors:
            list_errors.append("input files")
        if list_errors and ("color:red" in (mafft_error+file_errors)):
            text = " and ".join(list_errors)
            error_message = "<br>PhyloSuite guesses it was caused by non-standard characters in the path of %s. The archcriminal characters in the path are shown in red (MAFFT不接受路径中有中文或特殊符号):<br> \"<br>%s\""%(text, mafft_error+file_errors)
        else:
            error_message = ""
        QMessageBox.critical(
            self,
            "MAFFT",
            "<p style='line-height:25px; height:25px'>%s alignments failed, click <span style=\"color:red\">Show log</span> to see details! %s</p>" % (
                ", ".join(base_files), error_message),
            QMessageBox.Ok)
        self.on_pushButton_9_clicked()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Mafft()
    ui.show()
    sys.exit(app.exec_())
