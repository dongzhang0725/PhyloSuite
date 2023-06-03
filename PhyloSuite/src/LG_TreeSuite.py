#!/usr/bin/env python
# -*- coding: utf-8 -*-
import itertools
import re
import signal

import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.Lg_settings import Setting
from src.factory import Factory, WorkThread, Parsefmt
import inspect
import os
import sys
import traceback
import statistics as stat
import scipy
from uifiles.Ui_TreeSuite import Ui_TreeSuite
try:
    import plotly.express as px
    import plotly
    import pandas as pd
    import statsmodels.api as sm
except:
    pass

class TreeSuite(QDialog, Ui_TreeSuite, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)
    logCMDSig = pyqtSignal(str)

    def __init__(
            self,
            autoInputs=[[],[]],
            workPath=None,
            focusSig=None,
            parent=None):
        super(TreeSuite, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.parent = parent
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.setupUi(self)
        # 保存设置
        self.TreeSuite_settings = QSettings(
            self.thisPath +
            '/settings/TreeSuite_settings.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.TreeSuite_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        # with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
        #     self.qss_file = f.read()
        # self.setStyleSheet(self.qss_file)
        self.qss_file = self.factory.set_qss(self)
        ## 自动导入树和MSA文件
        if autoInputs:
            trees, alns = autoInputs
            self.input_tree(trees)
            self.input_alignment(alns)
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.comboBox_5.installEventFilter(self)
        self.comboBox_6.installEventFilter(self)
        self.comboBox_6.lineEdit().autoDetectSig.connect(
            self.popupAutoDec)  # 自动识别可用的输入
        # 信号槽
        self.comboBox.activated[str].connect(self.ctrl_input_widget)
        self.comboBox_10.activated[str].connect(self.ctrlOutgroupLable)
        self.comboBox_10.setTopText()
        self.lineEdit_3.clicked.connect(self.setFont)
        self.lineEdit_4.clicked.connect(self.setFont)
        self.comboBox_6.currentTextChanged.connect(self.changePlotParms)
        self.comboBox_5.currentTextChanged.connect(self.changePlotParms)
        self.logCMDSig.connect(self.addCMD2gui)
        ## 绘图相关
        self.groupBox_plot.toggled.connect(self.judge_plot_engine)
        ## 初始化一下
        self.ctrl_input_widget(self.comboBox.currentText())
        ## 命令
        self.log_cmd = self.gui4cmd()
        # 恢复用户的设置
        self.guiRestore()
        self.ctrl_input_widget(self.comboBox.currentText())
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
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        """
        self.analysis = self.comboBox.currentText()
        if self.analysis in ["Treeness", "Signal-to-noise (Treeness over RCV)",
                        "Root-to-tip branch length", "Long branch score",
                        "Spurious species identification", "Evolutionary rate",
                        "Pairwise patristic distance (branch length)"] and not self.comboBox_6.count():
            QMessageBox.critical(
                self,
                "TreeSuite",
                "<p style='line-height:25px; height:25px'>Please input tree(s) first!</p>")
            return
        if self.analysis in ["Signal-to-noise (Treeness over RCV)",
                        "RCV (Relative composition variability)",
                             "Saturation"] and not self.comboBox_5.count():
            QMessageBox.critical(
                self,
                "TreeSuite",
                "<p style='line-height:25px; height:25px'>Please input alignment(s) first!</p>")
            return
        # 创建输出文件夹
        self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
        self.exportPath = self.factory.creat_dirs(self.workPath +
                                                  os.sep + "TreeSuite_results" + os.sep + self.output_dir_name)
        self.sep = self.lineEdit.text()
        self.suffix = self.lineEdit_2.text()
        self.trees = self.comboBox_6.fetchListsText()
        self.msas = self.comboBox_5.fetchListsText()
        self.make_plot = self.groupBox_plot.isChecked()
        d_type = {"Auto detect": "AUTO", "Nucleotide": "NUC", "Amino acid": "AA"}
        self.seq_type = d_type[self.comboBox_4.currentText()]
        self.outgroups = [self.comboBox_10.itemText(i) for i in range(self.comboBox_10.count())
                          if self.comboBox_10.model().item(i).checkState() == Qt.Checked]
        self.factor = self.spinBox.value()
        ## 绘图相关的参数
        if self.analysis == "Saturation":
            self.col_num = self.spinBox_9.value()
            self.col_space = self.doubleSpinBox_10.value()
            self.template = self.comboBox_2.currentText()
            self.height_ = self.spinBox_7.value()
            self.width_ = self.spinBox_8.value()
            self.font_fam = self.lineEdit_3.text() if self.lineEdit_3.text() else "Arial"
            self.font_size = int(self.lineEdit_4.text()) if self.lineEdit_4.text() else 13
        ## 小数点
        self.decimal = self.spinBox_2.value()
        # 先清除内容
        self.textEdit_cmd.clear()
        ok = self.factory.remove_dir(self.exportPath, parent=self)
        if not ok:
            #提醒是否删除旧结果，如果用户取消，就不执行
            return
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
        open alignment files
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input Files", filter="Fasta Format(*.fas *.fasta *.fsa *.fna *.fa *.fsa);;")
        if fileNames[0]:
            self.input_alignment(fileNames[0])

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        """
        open tree files
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input trees", filter="Newick Format(*.nwk *.newick *.tre);;")
        if fileNames[0]:
            self.input_tree(fileNames[0])

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        show command
        """
        self.log_cmd.show()

    def input_alignment(self, files):
        if files:
            self.comboBox_5.refreshInputs(files)
        else:
            self.comboBox_5.refreshInputs([])

    def input_tree(self, files):
        if files:
            self.comboBox_6.refreshInputs(files)
            self.changeOutgroup()
        else:
            self.comboBox_6.refreshInputs([])

    def set_outgroups(self, ete_tre, outgroups):
        if set([i in ete_tre for i in outgroups]) == {True}:
            outgroup_mca = ete_tre.get_common_ancestor(outgroups)
            if outgroup_mca == ete_tre:
                ## 外群的MCA就是根节点
                ### 先置根一个非外群物种
                for node in ete_tre.traverse("postorder"):
                    if node.is_leaf() and (node.name not in outgroups):
                        break
                ete_tre.set_outgroup(node)
                ### 再置根原本的外群
                outgroup_mca = ete_tre.get_common_ancestor(outgroups)
                ete_tre.set_outgroup(outgroup_mca)
            else:
                ete_tre.set_outgroup(outgroup_mca)
        return ete_tre

    def ctrl_input_widget(self, analysis):
        if analysis in ["Signal-to-noise (Treeness over RCV)",
                        "RCV (Relative composition variability)",
                        "Saturation"]:
            for i in [self.label_5, self.comboBox_5, self.pushButton_3,
                      self.label_18, self.comboBox_4]:
                i.setVisible(True)
        else:
            for i in [self.label_5, self.comboBox_5, self.pushButton_3,
                      self.label_18, self.comboBox_4]:
                i.setVisible(False)
        ## 如果是RCV，隐藏树的选项
        if analysis == "RCV (Relative composition variability)":
            for i in [self.label_8, self.comboBox_6, self.pushButton_4,
                      self.label_3, self.comboBox_10]:
                i.setVisible(False)
        else:
            for i in [self.label_8, self.comboBox_6, self.pushButton_4,
                      self.label_3, self.comboBox_10]:
                i.setVisible(True)
        if analysis == "Spurious species identification":
            for j in [self.label_4, self.spinBox, self.label_15]:
                j.setVisible(True)
        else:
            for j in [self.label_4, self.spinBox, self.label_15]:
                j.setVisible(False)
        # 绘图相关
        if analysis in ["Saturation"]:
            self.groupBox_plot.setVisible(True)
        else:
            self.groupBox_plot.setVisible(False)

    def checkIDs(self, trees):
        first_tre_names = []
        list_dup_IDs = []
        for tree in trees:
            if os.path.exists(tree):
                tre = self.factory.read_tree(tree, parent=self)
                names = tre.get_leaf_names()
                if not first_tre_names:
                    first_tre_names = names
                list_names = []
                for name in names:
                    count_ = names.count(name)
                    if (count_ > 1) and (name not in list_names):
                        list_dup_IDs.append([os.path.basename(tree),
                                             name, str(count_)])
                        list_names.append(name)
        if list_dup_IDs:
            self.popupWarning(list_dup_IDs)
        return first_tre_names

    def changeOutgroup(self):
        treeNames = self.checkIDs(self.comboBox_6.fetchListsText())
        if treeNames:
            outgroups = sorted(treeNames)
            model = self.comboBox_10.model()
            self.comboBox_10.clear()
            for num, i in enumerate(outgroups):
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

    def ctrlOutgroupLable(self, text):
        OutgroupNum = len([self.comboBox_10.itemText(i) for i in range(
            self.comboBox_10.count()) if self.comboBox_10.model().item(i).checkState() == Qt.Checked])
        self.label_3.setText("Outgroup(%d):" % OutgroupNum)

    def get_itol_header(self, title):
        return [f'''DATASET_SIMPLEBAR
SEPARATOR TAB
DATASET_LABEL\t{title}
COLOR\t#b3b3ff
WIDTH\t1000
MARGIN\t0
HEIGHT_FACTOR\t0.7
BAR_SHIFT\t0
BAR_ZERO\t0
DATA''']

    def cal_treeness(self, tree):
        ete_tre = self.factory.read_tree(tree, parent=self)
        inter_node_len = []
        all_len = []
        leaf_names = []
        for node in ete_tre.traverse():
            if node.is_leaf():
                all_len.append(node.dist)
                leaf_names.append(node.name)
            else:
                inter_node_len.append(node.dist)
                all_len.append(node.dist)
        return sum(inter_node_len) / sum(all_len), leaf_names

    def treeness(self, trees, export_path, sep="\t", suffix="tsv"):
        if sep=="\\t":
            sep = "\t"
        list_out = [["File", "Treeness"]]
        for tree in trees:
            file_base = os.path.splitext(os.path.basename(tree))[0]
            treeness, leafnames = self.cal_treeness(tree)
            list_out.append([file_base, str(treeness)])
        self.factory.write_csv_file(f"{export_path}{os.sep}treeness.{suffix}",
                                    list_out, parent=self, silence=True, sep=sep)

    def cal_rcv(self, file, seq_type="AUTO", file_base=""):
        # 判断数据类型
        # GAVLIFWYDHNEKQMRSTCPUBXJ
        # 所有氨基酸《O和U是特殊氨基酸》：
        # ACDEFGHIKLMNOPQRSTUVWY   外加特有的简并碱基  B
        ## 所有简并碱基
        # A	Adenine	A
        # C	Cytosine	C
        # G	Guanine	G
        # T	Thymine (DNA)	T
        # U	Uracil (RNA)	U
        # W	Weak	A/T
        # S	Strong	C/G
        # M	Amino	A/C
        # K	Keto	G/T
        # R	Purine	A/G
        # Y	Pyrimidine	C/T
        # B	Not A	C/G/T
        # D	Not C	A/G/T
        # H	Not G	A/C/T
        # V	Not T	A/C/G
        # N	Any	A/C/G/T
        parsefmt = Parsefmt()
        dict_fas = parsefmt.readfile(file)
        if seq_type == "AUTO":
            seqType = parsefmt.which_pattern(dict_fas, file)
        else:
            seqType = seq_type
        # calculate average of all taxa
        allseqs = "".join(list(dict_fas.values())).upper()
        taxa_num = len(dict_fas)
        dict_degen = {"W": ["A", "T"],
                      "S": ["C", "G"],
                      "M": ["A", "C"],
                      "K": ["G", "T"],
                      "R": ["A", "G"],
                      "Y": ["C", "T"],
                      "B": ["C", "G", "T"],
                      "D": ["A", "G", "T"],
                      "H": ["A", "C", "T"],
                      "V": ["A", "C", "G"],
                      "N": ["A", "C", "G", "T"]}
        # 考虑简并碱基的情况
        def get_freq(seq, dict_degen, seq_type="NUC"):
            seq = seq.upper()
            d_ = {i: seq.count(i) for i in set(seq)}
            if seq_type == "NUC":
                for i in list(d_.keys()):
                    # is degenerate nucleotide
                    if i in dict_degen:
                        freq = d_.pop(i)
                        list_nuc = dict_degen[i]
                        avg_freq = freq/len(list_nuc)
                        for nuc in list_nuc:
                            if nuc in d_:
                                d_[nuc] += avg_freq
                            else:
                                d_[nuc] = avg_freq
            return d_

        # print(seqType)
        overall_freq = get_freq(allseqs, dict_degen, seqType)
        dict_spe_freq = {spe: get_freq(seq, dict_degen, seqType) for spe,seq in dict_fas.items()}
        all_values = []
        for i, freq in overall_freq.items():
            # A, T, C, G
            avg_freq = freq/taxa_num
            for spe, spe_freq in dict_spe_freq.items():
                # SPE1, SPE2, SPE3, SPE4, SPE5, SPE6
                if i in spe_freq:
                    value_ = abs(spe_freq[i] - avg_freq)
                    all_values.append(value_)
                else:
                    all_values.append(avg_freq)
        if file_base:
            # 计算每个物种的RCV
            list_itol = []
            list_spe_rcv = []
            for spe, spe_freq in dict_spe_freq.items():
                sum_char_diff = []
                for char, freq in spe_freq.items():
                    if char in overall_freq:
                        sum_char_diff.append(abs(freq - overall_freq[char]/taxa_num))
                    else:
                        sum_char_diff.append(freq)
                rcv = sum(sum_char_diff)/len(dict_fas[spe])
                list_spe_rcv.append([file_base, spe, rcv])
                list_itol.append(f"{spe}\t{round(rcv, self.decimal)}")
            return sum(all_values)/(len(allseqs)), list(dict_fas.keys()), list_spe_rcv, list_itol
        else:
            return sum(all_values)/(len(allseqs)), list(dict_fas.keys())

    def find_diff(self, tree_spe, msa_spe, tree_base, aln_base):
        warning = []
        # 树中有，alin里面没有的
        t_not_aln = list(set(tree_spe).difference(set(msa_spe)))
        if t_not_aln:
            warning.append(f"The species found in tree but not in alignment are:\n {str(t_not_aln)}")
        aln_not_t = list(set(msa_spe).difference(set(tree_spe)))
        if aln_not_t:
            warning.append(f"The species found in alignment but not in tree are:\n {str(t_not_aln)}")
        if warning:
            warning.insert(0, f"{'-'*8}> {tree_base} <{'-'*8}|{'-'*8}> {aln_base} <{'-'*8}")
        return warning

    def signal_to_noise(self, tre_msa, export_path, sep="\t", suffix="tsv",
                        seq_type="AUTO"):
        if sep== "\\t":
            sep = "\t"
        list_out = [["Tree", "Alignment", "Signal-to-noise",
                    "Treeness", "Relative composition variability"]]
        warnings = []
        for tree, msa in tre_msa:
            rcv, aln_spe = self.cal_rcv(msa, seq_type)
            treeness, tree_spe = self.cal_treeness(tree)
            tree_base = os.path.splitext(os.path.basename(tree))[0]
            aln_base = os.path.splitext(os.path.basename(msa))[0]
            list_out.append([tree_base, aln_base, str(treeness/rcv), str(treeness), str(rcv)])
            warnings.extend(self.find_diff(tree_spe, aln_spe, tree_base, aln_base))
        self.factory.write_csv_file(f"{export_path}{os.sep}signal-to-ratio.{suffix}",
                                    list_out, parent=self, silence=True, sep=sep)
        if warnings:
            with open(f"{export_path}{os.sep}signal-to-ratio-warnings.txt", "w", encoding="utf-8") as f2:
                f2.write("\n".join(warnings))
        return warnings

    def rcv(self, msas, export_path, sep="\t", suffix="tsv", seq_type="AUTO"):
        if sep=="\\t":
            sep = "\t"
        list_out = [["File", "Relative composition variability"]]
        list_out_individual = [["File", "Species", "Relative composition variability"]]
        for msa in msas:
            file_base = os.path.splitext(os.path.basename(msa))[0]
            rcv, aln_spe, list_spe_rcv, list_itol = self.cal_rcv(msa, seq_type, file_base)
            list_out.append([file_base, str(rcv)])
            list_out_individual.extend(list_spe_rcv)
            itol = self.get_itol_header("Relative composition variability")
            itol.extend(list_itol)
            with open(f"{export_path}{os.sep}{file_base} relative composition variability itol.txt",
                      "w", encoding="utf-8") as f:
                f.write("\n".join(itol))
        self.factory.write_csv_file(f"{export_path}{os.sep}RCV.{suffix}",
                                    list_out, parent=self, silence=True, sep=sep)
        self.factory.write_csv_file(f"{export_path}{os.sep}Species.RCV.{suffix}",
                                    list_out_individual, parent=self, silence=True, sep=sep)

    def cal_r2t_brl(self, tree, filebase, outgroups=[]):
        ete_tre = self.factory.read_tree(tree, parent=self)
        if outgroups:
            ete_tre = self.set_outgroups(ete_tre, outgroups)
            # if set([i in ete_tre for i in outgroups]) == {True}:
            #     outgroup_mca = ete_tre.get_common_ancestor(outgroups)
            #     ete_tre.set_outgroup(outgroup_mca)
        list_ = []
        list_itol = []
        root_node = ete_tre.get_tree_root()
        for node in ete_tre.traverse():
            if node.is_leaf():
                dist = root_node.get_distance(node)
                list_.append([filebase, node.name, str(dist)])
                list_itol.append(f"{node.name}\t{round(dist, self.decimal)}")
        return list_, list_itol

    def r2t_brl(self, trees, export_path, sep="\t", suffix="tsv", outgroups=[]):
        if sep=="\\t":
            sep = "\t"
        list_out = [["File", "Species", "root-to-tip branch length"]]
        for tree in trees:
            file_base = os.path.splitext(os.path.basename(tree))[0]
            list_, list_itol = self.cal_r2t_brl(tree, file_base, outgroups=outgroups)
            list_out.extend(list_)
            itol = self.get_itol_header("Root to tip length")
            itol.extend(list_itol)
            with open(f"{export_path}{os.sep}{file_base}-root-to-tip-branch-length-itol.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(itol))
        self.factory.write_csv_file(f"{export_path}{os.sep}root-to-tip-branch-length.{suffix}",
                                    list_out, parent=self, silence=True, sep=sep)

    def cal_lbs(self, tree, filebase, outgroups=[]):
        ete_tre = self.factory.read_tree(tree, parent=self)
        if outgroups:
            ete_tre = self.set_outgroups(ete_tre, outgroups)
            # if set([i in ete_tre for i in outgroups]) == {True}:
            #     outgroup_mca = ete_tre.get_common_ancestor(outgroups)
            #     if outgroup_mca == ete_tre:
            #         ## 外群的MCA就是根节点
            #         ### 先置根一个非外群物种
            #         for node in ete_tre.traverse("postorder"):
            #             if node.is_leaf() and (node.name not in outgroups):
            #                 break
            #         ete_tre.set_outgroup(node)
            #         ### 再置根原本的外群
            #         outgroup_mca = ete_tre.get_common_ancestor(outgroups)
            #         ete_tre.set_outgroup(outgroup_mca)
            #     else:
            #         ete_tre.set_outgroup(outgroup_mca)
        # 得到所有叶子
        leaf_nodes = []
        for node in ete_tre.traverse():
            if node.is_leaf():
                leaf_nodes.append(node)

        dict_spe_dists = {}
        all_dists = []

        for leaf_node in leaf_nodes:
            other_leaf_nodes = set(leaf_nodes) - set(leaf_node)
            for other_leaf_node in other_leaf_nodes:
                distance = leaf_node.get_distance(other_leaf_node)
                all_dists.append(distance)
                dict_spe_dists.setdefault(leaf_node.name, []).append(distance)
        avg_all_dist = sum(all_dists)/len(all_dists)
        # print(avg_all_dist)
        list_ = []
        overall_lb_scores = []
        list_itol = []
        for spe, spe_dists in dict_spe_dists.items():
            avg_spe_dist = sum(spe_dists)/len(spe_dists)
            # print(spe, avg_spe_dist)
            lb_score = ((avg_spe_dist/avg_all_dist)-1)*100
            overall_lb_scores.append(lb_score)
            list_.append([filebase, spe, str(lb_score)])
            list_itol.append(f"{spe}\t{round(lb_score, self.decimal)}")
            # print(spe, lb_score) # lb score
        return list_, [filebase, str(stat.mean(overall_lb_scores)), str(stat.median(overall_lb_scores)),
                       str(np.percentile(overall_lb_scores, 25)), str(np.percentile(overall_lb_scores, 75)),
                       str(np.min(overall_lb_scores)), str(np.max(overall_lb_scores)),
                       str(stat.stdev(overall_lb_scores)), str(stat.variance(overall_lb_scores))], list_itol

    def lbs(self, trees, export_path, sep="\t", suffix="tsv", outgroups=[]):
        if sep=="\\t":
            sep = "\t"
        list_out = [["File", "Species", "Long branch score"]]
        list_overall = [["Tree", "Mean", "Median", "25% percentile",
                         "75% percentile", "Minimum", "Maximum",
                         "Standard deviation", "Vriance"]]
        for tree in trees:
            file_base = os.path.splitext(os.path.basename(tree))[0]
            list_, overall, list_itol = self.cal_lbs(tree, file_base, outgroups=outgroups)
            list_out.extend(list_)
            list_overall.append(overall)
            itol = self.get_itol_header("Long branch score")
            itol.extend(list_itol)
            with open(f"{export_path}{os.sep}{file_base} long branch scores itol.txt",
                      "w", encoding="utf-8") as f:
                f.write("\n".join(itol))
        self.factory.write_csv_file(f"{export_path}{os.sep}Long branch scores.{suffix}",
                                    list_out, parent=self, silence=True, sep=sep)
        self.factory.write_csv_file(f"{export_path}{os.sep}Long branch scores overall.{suffix}",
                                    list_overall, parent=self, silence=True, sep=sep)

    def cal_ss(self, tree, filebase, outgroups=[], factor=20):
        ete_tre = self.factory.read_tree(tree, parent=self)
        if outgroups:
            ete_tre = self.set_outgroups(ete_tre, outgroups)
            # if set([i in ete_tre for i in outgroups]) == {True}:
            #     outgroup_mca = ete_tre.get_common_ancestor(outgroups)
            #     ete_tre.set_outgroup(outgroup_mca)

        dict_spe_brl = {}
        all_brl = []

        for node in ete_tre.traverse():
            if node.is_leaf():
                all_brl.append(node.dist)
                dict_spe_brl[node.name] = node.dist
            else:
                all_brl.append(node.dist)

        median = stat.median(all_brl)
        threshold = median*factor
        list_ = []
        for spe, brl in dict_spe_brl.items():
            if brl >= threshold:
                list_.append([filebase, spe, str(brl), str(median), str(threshold)])
        return list_

    def spurious_spe_ident(self, trees, export_path, sep="\t", suffix="tsv",
                           outgroups=[], factor=20):
        if sep == "\\t":
            sep = "\t"
        list_out = [["File", "Species", "Branch length", "Median Branch length", "Threshold"]]
        for tree in trees:
            file_base = os.path.splitext(os.path.basename(tree))[0]
            list_ = self.cal_ss(tree, file_base, outgroups=outgroups, factor=factor)
            list_out.extend(list_)
        self.factory.write_csv_file(f"{export_path}{os.sep}Spurious species.{suffix}",
                                    list_out, parent=self, silence=True, sep=sep)

    def cal_saturation(self, tree, msa, align_base, tree_base):
        ete_tre = self.factory.read_tree(tree, parent=self)
        parsefmt = Parsefmt()
        dict_fas = parsefmt.readfile(msa)
        ## 核验树的物种是不是和aln的完全一致
        aln_spe = list(dict_fas.keys())
        tre_spe = ete_tre.get_leaf_names()

        def get_difference(seq1, seq2):
            seq1, seq2 = seq1.upper(), seq2.upper()
            lenth = len(seq1)
            # list_idt = []
            list_dif = []
            for num, i in enumerate(seq1):
                if i != seq2[num]:
                    list_dif.append(1)
                # else:
                #     list_idt.append(1)
            return sum(list_dif) / lenth

        combos = itertools.combinations(aln_spe, 2)

        list_discances = []
        list_difs = []
        list_all = []
        for spe1, spe2 in combos:
            # partristic distance
            distance = ete_tre.get_distance(ete_tre & spe1, ete_tre & spe2)
            list_discances.append(distance)
            # pairwise diff
            dif = get_difference(dict_fas[spe1], dict_fas[spe2])
            list_difs.append(dif)
            list_all.append([align_base, tree_base, spe1, spe2,
                                      str(distance), str(dif), str(1 - dif)])

        # 计算slop
        # calculate linear regression
        y = list_difs
        x = list_discances
        res = sm.OLS(
            y, sm.add_constant(x), missing="drop"
        ).fit()
        if self.make_plot:
            slope, intercept, r2, r2_adj, fvalue, f_pvalue, llihood, aic, bic = self.get_statsmodels_stats(res)
        else:
            slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(list_discances, list_difs)
        # print(
        #     f"slope is {slope}, intercept is {intercept}, r_value is {r_value}, p_value is {p_value}, std_err is {std_err}")
        # print("\n".join(list_all))
        reg = [tree_base, align_base, str(slope), str(intercept), str(r2),
                        str(r2_adj), str(fvalue), str(f_pvalue), str(llihood),
                        str(aic), str(bic)] if self.make_plot else \
            [tree_base, align_base, str(slope), str(intercept), str(r_value**2),
             str(p_value), str(std_err)]
        return list_all, aln_spe, tre_spe, reg

    def get_statsmodels_stats(self, res):
        r2 = res.rsquared
        r2_adj = res.rsquared_adj
        intercept, slope = res.params
        fvalue = res.fvalue
        f_pvalue = res.f_pvalue
        aic = res.aic
        bic = res.bic
        llihood = res.llf
        return slope, intercept, r2, r2_adj, fvalue, f_pvalue, llihood, aic, bic

    def saturation_cmd(self):
        cmd = f'''
import plotly.express as px
import pandas as pd

df = pd.read_csv(r"{self.exportPath}{os.sep}plot_data.tsv", sep="\\t")
df = df.assign(file=df.loc[:, "Tree"] + " & " + df.loc[:, "Alignment"])
fig = px.scatter(df, x="Patristic distance", y="Pairwise difference",
                 facet_col="file", trendline="ols",
                 facet_col_wrap={self.kwargs["col_num"]},
                 facet_col_spacing={self.kwargs["col_space"]},
                 facet_row_spacing={self.kwargs["col_space"]})
fig.update_xaxes(matches=None, showticklabels=True)
fig.update_yaxes(matches=None, showticklabels=True)
# change regression line color and width
fig.update_traces(line_color="red", line_width=2)
# layout
fig.update_layout(
    template="{self.kwargs["template"]}",
    autosize=False,
    width={self.kwargs["width"]},
    height={self.kwargs["height"]}
)
# add annotations
results = px.get_trendline_results(fig)
for num, a in enumerate(fig.layout.annotations):
    text = a.text
    identifier = text.split("=")[1]
    stat_reg_model = results.loc[results["file"]==identifier,:]["px_fit_results"].iloc[0]
    r2 = round(stat_reg_model.rsquared, {self.decimal})
    intercept, coef = stat_reg_model.params
    ols = 'y = ' + str(round(coef, {self.decimal})) + 'x' + ' + ' + str(round(intercept, {self.decimal}))
    a.text = f"{{a.text}}<br>{{ols}}; R square = {{r2}}"
fig.for_each_annotation(lambda x: x.update(font={{"size": {self.kwargs["font_size"]},
                                                "family": "{self.kwargs["font_fam"]}"}}))
plotly.io.write_image(fig, r"{self.kwargs["pdf"]}", format='pdf')
fig.write_html(r"{self.kwargs["html"]}")
        '''
        return cmd

    def plot_saturation(self, **kwargs):
        '''

        Parameters
        ----------
        kwargs
            array: data
            col_num: 列数-->2
            col_space: 列间距-->0.05
            # line_color: 回归线颜色 --> red
            # trend_line_width: 回归线宽度 --> 2
            template: 画图的模板 --> simple_white
            width: 宽度 --> 900
            height: 高度 --> 1000

        Returns
        -------

        '''
        # 存数据用于画图
        df = pd.DataFrame(kwargs["array"][1:], columns=kwargs["array"][0])
        df.to_csv(f"{self.exportPath}{os.sep}plot_data.tsv", index=False, sep="\t")
        self.kwargs = kwargs
        draw_cmd = self.saturation_cmd()
        with open(f"{self.exportPath}{os.sep}plot_data.cmd.py", "w", encoding="utf-8") as f:
            f.write(draw_cmd)
        if draw_cmd:
            self.logCMDSig.emit(draw_cmd)
            exec(draw_cmd)

    def saturation(self, tre_msa, export_path, sep="\t", suffix="tsv"):
        if sep== "\\t":
            sep = "\t"
        list_out = [["Tree", "Alignment", "Species1", "Species2", "Patristic distance",
                              "Pairwise difference", "Pairwise identity"]]
        if not self.make_plot:
            list_regression = [["Tree", "Alignment", "Slope", "Intercept", "r square",
                                        "p value", "Standard error"]]
        else:
            list_regression = [["Tree", "Alignment", "Slope", "Intercept", "r square",
                            "r square adjusted", "F-statistic", "Prob (F-statistic)",
                            "Log-Likelihood", "AIC", "BIC"]]
        warnings = []
        for tree, msa in tre_msa:
            tree_base = os.path.splitext(os.path.basename(tree))[0]
            aln_base = os.path.splitext(os.path.basename(msa))[0]
            list_, tree_spe, aln_spe, reg = self.cal_saturation(tree, msa, aln_base, tree_base)
            list_out.extend(list_)
            list_regression.append(reg)
            warnings.extend(self.find_diff(tree_spe, aln_spe, tree_base, aln_base))
        self.factory.write_csv_file(f"{export_path}{os.sep}saturation.{suffix}",
                                    list_out, parent=self, silence=True, sep=sep)
        self.factory.write_csv_file(f"{export_path}{os.sep}saturation.regression.{suffix}",
                                    list_regression, parent=self, silence=True, sep=sep)
        if self.make_plot:
            self.plot_saturation(array=list_out, col_num=self.col_num, col_space=self.col_space,
                                 template=self.template, font_fam=self.font_fam, font_size=self.font_size,
                                 height=self.height_, width=self.width_,
                                 pdf=f"{export_path}{os.sep}saturation.regression.pdf",
                                 html=f"{export_path}{os.sep}saturation.regression.html")
        if warnings:
            with open(f"{export_path}{os.sep}saturation-warnings.txt", "w", encoding="utf-8") as f2:
                f2.write("\n".join(warnings))
        return warnings

    def cal_evo_rate(self, tree, outgroups):
        ete_tre = self.factory.read_tree(tree, parent=self)
        if outgroups:
            ete_tre = self.set_outgroups(ete_tre, outgroups)
            # if set([i in ete_tre for i in outgroups]) == {True}:
            #     outgroup_mca = ete_tre.get_common_ancestor(outgroups)
            #     ete_tre.set_outgroup(outgroup_mca)
        list_brls = []
        list_leafs = []
        for node in ete_tre.traverse():
            if node.is_leaf():
                list_leafs.append(1)
            list_brls.append(node.dist)
        return sum(list_brls)/sum(list_leafs)

    def evo_rate(self, trees, export_path, sep="\t", suffix="tsv", outgroups=""):
        if sep=="\\t":
            sep = "\t"
        list_out = [["File", "Evolution rate"]]
        for tree in trees:
            file_base = os.path.splitext(os.path.basename(tree))[0]
            evo_rate = self.cal_evo_rate(tree, outgroups)
            list_out.append([file_base, str(evo_rate)])
        self.factory.write_csv_file(f"{export_path}{os.sep}Evolution rate.{suffix}",
                                        list_out, parent=self, silence=True, sep=sep)

    def cal_pair_dist(self, tree, outgroups, tree_base):
        ete_tre = self.factory.read_tree(tree, parent=self)
        if outgroups:
            ete_tre = self.set_outgroups(ete_tre, outgroups)
            # if set([i in ete_tre for i in outgroups]) == {True}:
            #     outgroup_mca = ete_tre.get_common_ancestor(outgroups)
            #     ete_tre.set_outgroup(outgroup_mca)
        list_leaf_names = ete_tre.get_leaf_names()
        list_matrix = []
        list_pairs = []
        list_ = []
        for leaf1 in list_leaf_names:
            if not list_matrix:
                list_matrix.append(["", leaf1])
            else:
                list_matrix[0].append(leaf1)
            for num, leaf2 in enumerate(list_leaf_names):
                # 如果某一行还没有
                if len(list_matrix) < num+2:
                    list_matrix.append([leaf2])
                if leaf1 != leaf2:
                    distance = ete_tre.search_nodes(name=leaf1)[0].get_distance(
                        ete_tre.search_nodes(name=leaf2)[0])
                    list_matrix[num+1].append(str(distance))
                    if not (([leaf1, leaf2] in list_pairs) or ([leaf2, leaf1] in list_pairs)):
                        list_.append([tree_base, leaf1, leaf2, str(distance)])
                else:
                    list_matrix[num+1].append("")
                list_pairs.append([leaf1, leaf2])
        return list_matrix, list_

    def pair_dist(self, trees, export_path, sep="\t", suffix="tsv", outgroups=""):
        if sep=="\\t":
            sep = "\t"
        list_out = [["File", "Species1", "Species2", "Patristic distance (branch length)"]]
        for tree in trees:
            file_base = os.path.splitext(os.path.basename(tree))[0]
            matrix, list_ = self.cal_pair_dist(tree, outgroups, file_base)
            list_out.extend(list_)
            self.factory.write_csv_file(f"{export_path}{os.sep}{file_base} patristic distance matrix.{suffix}",
                                            matrix, parent=self, silence=True, sep=sep)
        self.factory.write_csv_file(f"{export_path}{os.sep}Patristic distance.{suffix}",
                                        list_out, parent=self, silence=True, sep=sep)

    def unroot(self, trees, export_path):
        for tree in trees:
            file_base = os.path.splitext(os.path.basename(tree))[0]
            ete_tre = self.factory.read_tree(tree, parent=self)
            if ete_tre:
                ete_tre.unroot()
            ete_tre.write(outfile=f"{export_path}{os.sep}{file_base}_unrooted.nwk", format=1)

    def resolve_polytomy(self, trees, export_path):
        for tree in trees:
            file_base = os.path.splitext(os.path.basename(tree))[0]
            ete_tre = self.factory.read_tree(tree, parent=self)
            if ete_tre:
                ete_tre.resolve_polytomy(recursive=True)
            ete_tre.write(outfile=f"{export_path}{os.sep}{file_base}_non_polytomy.nwk", format=1)

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("tree suite", self.workPath, self.auto_popSig, self)

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
            trees,alns = widget.autoInputs
            self.input_tree(trees)
            self.input_alignment(alns)
        else:
            self.input_tree([])
            self.input_alignment([])

    def is_same_with_msa(self, msa, tree_name):
        for i in msa:
            msa_name = os.path.splitext(os.path.basename(i))[0]
            msa_name_full = os.path.basename(i)
            if tree_name in [msa_name, msa_name_full]:
                return i

    def combine_tree_msa(self, trees, msa):
        '''
        当树文件的名字和msa的名字完全对应的时候，就只会对它们进行统计分析
        当没有1个msa和树文件的名字是一样的时候，将会把这个树文件和所有msa组合
        '''
        if trees and msa:
            list_ = []
            for tree in trees:
                tree_name = os.path.splitext(os.path.basename(tree))[0]
                msa_path = self.is_same_with_msa(msa, tree_name)
                if msa_path:
                    list_.append((tree, msa_path))
                else:
                    list_.extend(list(itertools.product([tree], msa)))
            return list_
        elif trees:
            return trees
        elif msa:
            return msa
        else:
            return []

    def run_command(self):
        try:
            # 清空文件夹，放在这里方便统一报错
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            warnings = []
            if self.analysis == "Treeness":
                self.treeness(self.trees, self.exportPath, sep=self.sep, suffix=self.suffix)
            elif self.analysis == "Signal-to-noise (Treeness over RCV)":
                warnings = self.signal_to_noise(self.combine_tree_msa(self.trees, self.msas),
                                     self.exportPath, sep=self.sep, suffix=self.suffix,
                                     seq_type=self.seq_type)
            elif self.analysis == "RCV (Relative composition variability)":
                self.rcv(self.msas, self.exportPath, sep=self.sep, suffix=self.suffix,
                         seq_type=self.seq_type)
            elif self.analysis == "Root-to-tip branch length":
                self.r2t_brl(self.trees, self.exportPath, sep=self.sep, suffix=self.suffix,
                             outgroups=self.outgroups)
            elif self.analysis == "Long branch score":
                self.lbs(self.trees, self.exportPath, sep=self.sep, suffix=self.suffix,
                             outgroups=self.outgroups)
            elif self.analysis == "Spurious species identification":
                self.spurious_spe_ident(self.trees, self.exportPath, sep=self.sep, suffix=self.suffix,
                         outgroups=self.outgroups, factor=self.factor)
            elif self.analysis == "Saturation":
                warnings = self.saturation(self.combine_tree_msa(self.trees, self.msas),
                                     self.exportPath, sep=self.sep, suffix=self.suffix)
            elif self.analysis == "Evolutionary rate":
                self.evo_rate(self.trees, self.exportPath, sep=self.sep, suffix=self.suffix,
                                        outgroups=self.outgroups)
            elif self.analysis == "Pairwise patristic distance (branch length)":
                self.pair_dist(self.trees, self.exportPath, sep=self.sep, suffix=self.suffix,
                              outgroups=self.outgroups)
            elif self.analysis == "Unroot tree":
                self.unroot(self.trees, self.exportPath)
            elif self.analysis == "Resolve polytomy":
                self.resolve_polytomy(self.trees, self.exportPath)
            elif self.analysis == "plot":
                exec(self.plot_cmd)
            if not warnings:
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
                        f"warnings%s"%"\n".join(warnings),
                        self.exportPath,
                        self.qss_file,
                        self])
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
        self.TreeSuite_settings.setValue('size', self.size())
        # self.TreeSuite_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                if name not in ["comboBox_6", "comboBox_5", "comboBox_10"]:
                    index = obj.currentIndex()
                    self.TreeSuite_settings.setValue(name, index)
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.TreeSuite_settings.setValue(name, state)
            # if isinstance(obj, QGroupBox):
            #     state = obj.isChecked()
            #     self.TreeSuite_settings.setValue(name, state)
            if isinstance(obj, QLineEdit):
                text = obj.text()
                self.TreeSuite_settings.setValue(name, text)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.TreeSuite_settings.value('size', QSize(1000, 700)))
        self.factory.centerWindow(self)
        # self.move(self.TreeSuite_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name not in ["comboBox_6", "comboBox_5", "comboBox_10"]:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.TreeSuite_settings.value(name, "0")
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
            if isinstance(obj, QCheckBox):
                value = self.TreeSuite_settings.value(
                    name, "true")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            # if isinstance(obj, QGroupBox):
            #     value = self.TreeSuite_settings.value(
            #         name, obj.isChecked())  # get stored value from registry
            #     obj.setChecked(
            #         self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QLineEdit):
                if name == "lineEdit":
                    value = self.TreeSuite_settings.value(
                        name, ",")  # get stored value from registry
                elif name == "lineEdit_2":
                    value = self.TreeSuite_settings.value(
                        name, "csv")  # get stored value from registry
                elif name == "lineEdit_3":
                    value = self.TreeSuite_settings.value(
                        name, "Arial")  # get stored value from registry
                elif name == "lineEdit_4":
                    value = self.TreeSuite_settings.value(
                        name, "13")  # get stored value from registry
                else:
                    value = self.TreeSuite_settings.value(
                        name, obj.text())
                obj.setText(value)

    def runProgress(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def popupException(self, exception):
        msg = QMessageBox(self)
        message = 'The program encountered an unforeseen problem, please report the bug at ' \
                  '<a href="https://github.com/dongzhang0725/PhyloSuite/issues">' \
                  'https://github.com/dongzhang0725/PhyloSuite/issues</a> or ' \
                  'send an email with the detailed traceback to dongzhang0725@gmail.com'
        if "plotlyjs argument is not a valid URL or file path" in exception:
            state = self.factory.checkPath(
                self.thisPath.strip("\""), mode="silence", parent=self, allow_space=True)
            if state != True:
                illegalTXT, path_text = state
                message = "Error happened! Check if there are non-standard " \
                          "characters in the installation path of your PhyloSuite. " \
                          "The possible archcriminal characters in the path are shown in red " \
                          "(检查路径是否有中文或特殊符号): <br>" \
                          "%s"%path_text
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    @pyqtSlot(list)
    def popupWarning(self, list_):
        ## 为了统一，统一用的列表
        msg = QMessageBox(self)
        if type(list_) == list:
            ## 有缺失基因的情况，这时候warning是个字典
            msg.setIcon(QMessageBox.Information)
            msg.setText(
                "<p style='line-height:25px; height:25px'>Duplicated IDs found in the tree "
                "(see details)</p>")
            msg.setWindowTitle("Duplicated IDs warning")
            max_file_len = len(max([i[0] for i in list_] + ["File"], key=len))
            max_species_len = len(max([i[1] for i in list_] + ["Species"], key=len))
            list_detail = [f'{"File".ljust(max_file_len)} | {"Species".ljust(max_species_len)} | Count']\
                          + [f'{i[0].ljust(max_file_len)} | {i[1].ljust(max_species_len)} | {i[2]}' for i in list_]
            msg.setDetailedText("\n".join(list_detail))
            msg.setStandardButtons(QMessageBox.Ok)
            # with open(self.dict_args["exportPath"] + os.sep + "missing_genes.txt", "w", encoding="utf-8") as f:
            #     f.write("\n".join(list_detail))
            msg.exec_()

    def closeEvent(self, event):
        self.guiSave()
        # 断开showSig和closeSig的槽函数连接
        try:
            self.showSig.disconnect()
        except:
            pass
        try:
            self.closeSig.disconnect()
        except:
            pass

        # if self.isRunning():
        #     reply = QMessageBox.question(
        #         self,
        #         "TreeSuite",
        #         "<p style='line-height:25px; height:25px'>TreeSuite is still running, terminate it?</p>",
        #         QMessageBox.Yes,
        #         QMessageBox.Cancel)
        #     if reply == QMessageBox.Yes:
        #         try:
        #             self.worker.stopWork()
        #             self.pool.terminate()  # Terminate all processes in the Pool
        #             ## 删除subprocess
        #             if platform.system().lower() == "windows":
        #                 for pid in self.list_pids: os.popen('taskkill /F /T /PID %s' % pid)
        #             else:
        #                 for pid in self.list_pids: os.killpg(os.getpgid(pid), signal.SIGTERM)
        #             self.pool = None
        #             self.interrupt = True
        #         except:
        #             self.pool = None
        #             self.interrupt = True
        #     else:
        #         event.ignore()

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
                if name == "comboBox_6":
                    self.input_tree(files)
                elif name == "comboBox_5":
                    self.input_alignment(files)
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(TreeSuite, self).eventFilter(obj, event)  # 0

    def setFont(self):
        family = self.lineEdit_3.text() if self.lineEdit_3.text() else "Arial"
        size = int(self.lineEdit_4.text()) if self.lineEdit_4.text() else "13"
        font, ok = QFontDialog.getFont(QFont(family, size), self)
        if ok:
            family_ = font.family()
            size_ = str(font.pointSize())
            self.lineEdit_3.setText(family_)
            self.lineEdit_4.setText(size_)

    def gui4cmd(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Plot")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Plotting command:")
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
        pushButton = QPushButton("Draw with current command", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/Save-icon.png"))
        pushButton.setIcon(icon)
        pushButton_2 = QPushButton("Close", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/if_Delete_1493279.png"))
        pushButton_2.setIcon(icon)
        self.textEdit_cmd = QTextEdit(dialog)
        gridLayout.addLayout(horizontalLayout_2, 0, 0, 1, 2)
        gridLayout.addWidget(self.textEdit_cmd, 1, 0, 1, 2)
        gridLayout.addWidget(pushButton, 2, 0, 1, 1)
        gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
        pushButton.clicked.connect(lambda : [self.plot_slot(self.textEdit_cmd.toPlainText()),
                                             dialog.close()])
        pushButton_2.clicked.connect(dialog.close)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def plot_slot(self, cmd):
        self.plot_cmd = cmd
        self.analysis = "plot"
        self.worker = WorkThread(self.run_command, parent=self)
        self.worker.start()

    def setWordWrap(self):
        button = self.sender()
        if button.isChecked():
            button.setChecked(True)
            self.textEdit_cmd.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            button.setChecked(False)
            self.textEdit_cmd.setLineWrapMode(QTextEdit.NoWrap)

    def changePlotParms(self):
        trees = self.comboBox_6.fetchListsText()
        msa = self.comboBox_5.fetchListsText()
        comb = self.combine_tree_msa(trees, msa)
        if not hasattr(self, "comb") or (comb != self.comb):
            self.comb = comb
            # print(self.comb)
            comb_num = len(self.comb)
            if comb_num > 1:
                col_num = self.spinBox_9.value()
                row_num = comb_num//col_num
                row_num = row_num + 1 if comb_num%col_num != 0 else row_num
                self.spinBox_7.setValue(row_num * 333)
                self.spinBox_8.setValue(col_num * 450)
                if row_num == 2:
                    self.doubleSpinBox_10.setValue(0.12)
                else:
                    self.doubleSpinBox_10.setValue(0.05)
            else:
                self.spinBox_7.setValue(333)
                self.spinBox_8.setValue(450)

    def addCMD2gui(self, text):
        if re.search(r"\w+", text):
            self.textEdit_cmd.append(text)

    def judge_plot_engine(self, bool_):
        if bool_:
            try:
                import plotly
                import pandas as pd
                # pd.DataFrame(columns=["1", "2"])
                # print(plotly.__version__)
            except:
                self.groupBox_plot.setChecked(False)
                reply = QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Please install plot engine of PhyloSuite first!</p>",
                    QMessageBox.Ok,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.setting = Setting(self)
                    self.setting.display_table(self.setting.listWidget.item(1))
                    # 隐藏？按钮
                    self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                    self.setting.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = TreeSuite()
    ui.show()
    sys.exit(app.exec_())