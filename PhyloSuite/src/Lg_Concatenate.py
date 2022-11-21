#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from itertools import chain

from uifiles.Ui_Concatenate import Ui_Matrix
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import os
import sys
import re
import inspect
from src.factory import Factory, WorkThread, Parsefmt
import traceback
from collections import OrderedDict
import platform
# from Bio.SeqFeature import SeqFeature, FeatureLocation
# from Bio.Graphics import GenomeDiagram
# from reportlab.lib.units import cm

# class Partition2fig(object):
#     def __init__(self, **kwargs):
#         super(Partition2fig, self).__init__()
#         self.dict_args = kwargs
#         self.readpartFile()
#         self.drawFig()
#
#     def readpartFile(self):
#         self.list_name_start_stop = []
#         with open(self.dict_args["partition_file"], encoding="utf-8", errors='ignore') as f:
#             line = f.readline()
#             while ("***codon style***" not in line) and (line):
#                 if "=" in line:
#                     name, indices = line.strip(";\n").split("=")
#                     # name = name.split("_")[0]
#                     start, stop = indices.split("-")
#                     self.list_name_start_stop.append([name, start.strip(), stop.strip()])
#                 line = f.readline()
#
#     def drawFig(self):
#         gdd = GenomeDiagram.Diagram('linear figure')
#         gdt_features = gdd.new_track(1, greytrack=False, scale=0, height=0.4)
#         gds_features = gdt_features.new_set()
#         for name, start, stop in self.list_name_start_stop:
#             if "COX" in name.upper():
#                 color = "#81CEEA"
#             elif "NAD" in name.upper():
#                 color = "#F9C997"
#             elif "ATP" in name.upper():
#                 color = "#E97E8D"
#             elif ("CYTB" in name.upper()) or ("COB" in name.upper()):
#                 color = "#E2E796"
#             elif "RRN" in name.upper():
#                 color = "#94F2DB"
#             # strand = -1 if name in ["nad1", "cytb", "nad4", "nad4L", "rrnL"] else 1
#             feature = SeqFeature(FeatureLocation(int(start), int(stop)), strand=1)
#             gds_features.add_feature(feature, name=name, label=True,
#                                      label_size=self.dict_args["label_size"], label_angle=self.dict_args["Label_angle"],
#                                      color=self.dict_args["Label_color"], label_position=self.dict_args["Label_position"],
#                                      sigil="BIGARROW", arrowshaft_height=0.5,
#                                      arrowhead_length=0.5)
#         gdd.draw(format='linear', pagesize=(self.dict_args["fig_width"] * cm, self.dict_args["fig_height"] * cm), fragments=1,
#                  start=0, end=int(stop))
#         gdd.write(self.dict_args["exportPath"] + os.sep + "linear.pdf", "pdf")

class Seq_matrix(object):
    def __init__(self, **kwargs):
        self.factory = Factory()
        self.dict_args = kwargs
        self.outpath = self.dict_args["exportPath"]
        self.dict_species = {}
        self.dict_statistics = dict(prefix=['taxon'])
        self.partition_style = ['***partitionfinder style***\n']
        self.partition_codon = ["\n***codon style***\n"]
        self.bayes_style = ['\n***bayes style***\n']
        self.bayes_codon = ["\n***bayes codon style***\n"]
        self.iqtree_style = ['\n***IQ-TREE style***\n#nexus\nbegin sets;\n']
        self.iqtree_codon = ["\n***IQ-TREE codon style***\n#nexus\nbegin sets;\n"]
        self.parent = self.dict_args["parent"]
        self.dict_args["split_codon"] = list(sorted(self.dict_args["split_codon"])) if \
                                    self.dict_args["split_codon"] else self.dict_args["split_codon"] # [1,2,3]
        self.partition_name = []
        self.partition_codname = []
        self.gene_index = []
        self.dist_warning_message = OrderedDict()
        self.error_message = ""
        self.warning_message = ""
        self.parsefmt = Parsefmt(self.error_message, self.warning_message)
        self.dict_genes_alignments = OrderedDict()
        self.unaligned = False
        self.unaligns = []
        self.not_PCGs = [gene for gene, flag in self.dict_args["PCG_genes"].items() if not flag]
        self.wrong_PCGs = []
        self.exportName = self.dict_args["export_name"]
        self.interrupt = False
        self.list_empty_files = []
        self.name_mapping = {}
        for num, eachFile in enumerate(self.dict_args["files"]):
            if self.interrupt:
                break
            geneName = os.path.splitext(os.path.basename(eachFile))[0]
            geneName = self.factory.refineName(geneName)
            dict_taxon = self.parsefmt.readfile(eachFile)
            self.name_mapping.update(self.parsefmt.name_mapping)
            set_length = set([len(dict_taxon[i]) for i in dict_taxon])
            if set_length == {0}:
                self.list_empty_files.append(os.path.basename(eachFile))
                continue
            self.error_message += self.parsefmt.error_message
            self.warning_message += self.parsefmt.warning_message
            if self.factory.is_aligned(dict_taxon):
                self.dict_genes_alignments[geneName] = dict_taxon
            else:
                self.unaligned = True
                self.unaligns.append(geneName)
        if self.list_empty_files:
            if len(self.list_empty_files) == 1:
                text = "The empty file \"%s\" will be ignored"%self.list_empty_files[0]
            else:
                file_names = "\", \"".join(self.list_empty_files[:-1]) + "\" and \"%s\""%self.list_empty_files[-1]
                text = "The empty files \"%s will be ignored"%file_names
            QMetaObject.invokeMethod(self.parent, "popupEmptyFileWarning",
                                     Qt.BlockingQueuedConnection,
                                     Q_ARG(str, text))
        if self.unaligned:
            self.dict_args["unaligned_signal"].emit(self.unaligns)
            self.ok = False
            return
        if self.dict_genes_alignments:
            self.supplement()
            self.concatenate()
            self.ok = True
        else:
            self.ok = False

    def concatenate(self):
        total = len(self.dict_args["files"])
        self.dict_args["progressSig"].emit(10)
        self.dict_args["workflow_progress"].emit(10)
        if not self.unaligned:  # 确认比对过
            for num, self.genename in enumerate(self.dict_genes_alignments):
                if self.interrupt:
                    break
                self.dict_taxon = self.dict_genes_alignments[self.genename]
                self.dict_statistics['prefix'].append(f'\t{self.genename}')
                self.append()
                self.addPartition()
                self.dict_args["progressSig"].emit(
                    10 + ((num + 1) * 80 / total))
                self.dict_args["workflow_progress"].emit(
                    10 + ((num + 1) * 80 / total))
            if self.interrupt:
                return
            self.complete()  # 完善
            self.save()  # 存档
            self.dict_args["progressSig"].emit(100)
            self.dict_args["workflow_progress"].emit(100)
            if self.error_message:
                self.dict_args["exception_signal"].emit(self.error_message)
            if self.warning_message:
                QMetaObject.invokeMethod(self.parent, "popupWarning",
                                         Qt.BlockingQueuedConnection,
                                         Q_ARG(list, [self.warning_message]))
            if self.dict_args["split_codon"] and self.wrong_PCGs:
                QMetaObject.invokeMethod(self.parent, "popupWarning",
                                         Qt.BlockingQueuedConnection,
                                         Q_ARG(list, [self.wrong_PCGs]))
        # else:
        #     self.dict_args["unaligned_signal"].emit(self.unaligns)

    def supplement(self):
        # 补全缺失基因的物种
        #         dict_maxTaxa = max(*[self.dict_genes_alignments[i]
        # for i in self.dict_genes_alignments], key=len)  # 物种数最多的基因
        dict_maxTaxa = []
        for k in self.dict_genes_alignments:
            if self.interrupt:
                break
            list_taxon = list(self.dict_genes_alignments[k].keys())
            dict_maxTaxa.extend(list_taxon)
        list_set_dict_maxTaxa = list(set(dict_maxTaxa))
        for i in list_set_dict_maxTaxa:
            if self.interrupt:
                break
            lossingGene = []
            for j in self.dict_genes_alignments:
                if self.interrupt:
                    break
                if i not in self.dict_genes_alignments[j]:
                    keys = list(self.dict_genes_alignments[j].keys())
                    alignmentLenth = len(
                        self.dict_genes_alignments[j][keys[0]])
                    self.dict_genes_alignments[j][i] = self.dict_args["missing_symbol"] * alignmentLenth
                    lossingGene.append(j)
            if lossingGene:
                self.dist_warning_message[i] = lossingGene
        if self.dist_warning_message:
            ##报错
            QMetaObject.invokeMethod(self.parent, "popupWarning",
                                     Qt.BlockingQueuedConnection,
                                     Q_ARG(list, [self.dist_warning_message]))

    def split_codon(self, seq):
        # 如果序列不是3的倍数，则不执行切割
        if len(seq)%3 != 0:
            if self.genename not in self.not_PCGs:
                self.not_PCGs.append(self.genename)
            if self.genename not in self.wrong_PCGs:
                self.wrong_PCGs.append(self.genename)
            return seq
        new_seq = []
        for index in range(0, len(seq), 3):
            sites = self.dict_args["split_codon"] # [1,2,3]
            for site in sites:
                # print(index + site - 1, len(seq))
                new_seq.append(seq[index + site - 1])
        return "".join(new_seq)

    def append(self):
        for self.spe_key, self.seq in self.dict_taxon.items():  # 因为读新的文件会
            self.seq = self.seq.upper()  # 全部改为大写
            self.seq = self.seq if not (self.dict_args["split_codon"] and
                                        self.dict_args["PCG_genes"][self.genename]) else self.split_codon(self.seq)
            lenth = len(self.seq)
            indels = self.seq.count('-')
            self.dict_species[self.spe_key] = f"{self.dict_species.get(self.spe_key, '')}{self.seq}"
            self.dict_statistics[self.spe_key] = [f"{''.join(self.dict_statistics.get(self.spe_key, [self.spe_key]))}\t{lenth} ({indels} indels)"]

    def codon_partition_text(self, span):
        start = span[0] + 1
        stop = span[1]
        if self.genename in self.not_PCGs:
            self.partition_codon.append(f"{self.genename}={start}-{stop};\n")
            self.bayes_codon.append(f'charset {self.genename}={start}-{stop};\n')
            self.iqtree_codon.append(f'\tcharset {self.genename}={start}-{stop};\n')
            self.partition_codname.append(f"{self.genename},")
        else:
            sites_num = len(self.dict_args["split_codon"])
            for num, site in enumerate(self.dict_args["split_codon"]):
                suffix = '\\%d;\n'%sites_num if sites_num>1 else ";\n"
                self.partition_codon.append(f"{self.genename}_codon{site}={start + num}-{stop}{suffix}")
                self.bayes_codon.append(f'charset {self.genename}_codon{site}={start + num}-{stop}{suffix}')
                self.iqtree_codon.append(f'\tcharset {self.genename}_codon{site}={start + num}-{stop}{suffix}')
                self.partition_codname.append(f"{self.genename}_codon{site},")

    def addPartition(self):
        ##替换这些特殊符号，可以让序列更容易被识别
        rgx = re.compile(r"([.^$*+?{}[\]\\|()])")
        matFlag = rgx.sub(r"[\1]", self.seq) + '$'
        span = re.search(matFlag, self.dict_species[self.spe_key]).span()
        start = span[0] + 1
        stop = span[1]
        self.gene_index.append(span)
        self.partition_style.append(f"{self.genename}={start}-{stop};\n")
        self.bayes_style.append(f'charset {self.genename}={start}-{stop};\n')
        self.iqtree_style.append(f'\tcharset {self.genename}={start}-{stop};\n')
        if self.dict_args["split_codon"]:
            self.codon_partition_text(span)
        self.partition_name.append(f"{self.genename},")

    def align(self, seq):
        list_seq = re.findall(r'(.{60})', seq)
        if not list_seq:
            self.align_seq = seq + "\n"
            return self.align_seq
        remainder = len(seq) % 60
        if remainder == 0:
            self.align_seq = '\n'.join(list_seq) + '\n'
        else:
            self.align_seq = '\n'.join(
                list_seq) + '\n' + seq[-remainder:] + '\n'

    def nxs_interleave(self):
        length = len(self.dict_species[self.list_keys[-1]])  # 总长
        integer = length // 60
        num = 1
        if self.dict_args["export_nexi"]:
            while num <= integer:
                for i in self.list_keys:
                    self.nxs_inter.append(f"{i.ljust(self.name_longest)} "
                                          f"{self.dict_species[i][(num - 1) * 60:num * 60]}\n")
                self.nxs_inter.append("\n")
                num += 1
            if length % 60 != 0:
                for i in self.list_keys:
                    self.nxs_inter.append(f"{i.ljust(self.name_longest)} {self.dict_species[i][(num - 1) * 60:length]}\n")
        if self.dict_args["export_nexig"]:
            for each_span in self.gene_index:  # 以gene分界形式的nex
                for i in self.list_keys:
                    self.nxs_gene.append(f"{i.ljust(self.name_longest)} {self.dict_species[i][each_span[0]:each_span[1]]}\n")
                self.nxs_gene.append("\n")

    def get_str(self):  # 只有nex和phy格式需要改序列名字空格
        for i in self.list_keys:
            if self.dict_args["export_stat"]:
                self.dict_statistics[i].append(f'\t{len(self.dict_species[i])}\t{self.count}\n')
            if self.dict_args["export_fas"]:
                self.file.append(f'>{i}\n{self.dict_species[i]}\n')
            if self.dict_args["export_phylip"]:
                self.phy_file.append(f"{i.ljust(self.name_longest)} {self.dict_species[i]}\n")
            if self.dict_args["export_nex"]:
                self.nxs_file.append(f"{i.ljust(self.name_longest)} {self.dict_species[i]}\n")
            self.align(self.dict_species[i])
            if self.dict_args["export_paml"]:
                self.paml_file.append(f"{i}\n{self.align_seq}\n")
            if self.dict_args["export_axt"]:
                self.axt_file.append(f"{self.dict_species[i]}\n")
            if self.dict_args["export_stat"]:
                self.statistics.extend(self.dict_statistics[i])

    def complete(self):
        self.count = len(self.dict_genes_alignments)
        self.partition_name = [f'partition Names = {self.count}:{"".join(self.partition_name).strip(",")}' \
                              f';\nset partition=Names;\n']
        if self.dict_args["split_codon"]:
            self.partition_codname = [f'partition Names = ' \
             f'{(self.count-len(self.not_PCGs)) * len(self.dict_args["split_codon"]) + len(self.not_PCGs)}:' 
             f'{"".join(self.partition_codname).strip(",")};\nset partition=Names;\n']
        if self.dict_args["export_stat"]:
            self.dict_statistics['prefix'].append('\tTotal lenth\tNo of charsets\n')
        self.list_keys = sorted(list(self.dict_species.keys()))
        spe_num = len(self.list_keys)
        seq_num = len(self.dict_species[self.list_keys[-1]])
        self.pattern = self.parsefmt.which_pattern(
            self.dict_species, "Concatenated file")  # 得到pattern
        self.error_message += self.parsefmt.error_message
        self.warning_message += self.parsefmt.warning_message
        self.file = []
        self.phy_file = [f' {spe_num} {seq_num}\n']
        self.nxs_file = [f'#NEXUS\nBEGIN DATA;\ndimensions ntax={spe_num} nchar={seq_num};\n' 
                         f'format missing=?\ndatatype={self.pattern} gap= -;\n\nmatrix\n']
        self.nxs_inter = [f'#NEXUS\nBEGIN DATA;\ndimensions ntax={spe_num} nchar={seq_num};'
                          f'\nformat missing=?\ndatatype={self.pattern} gap= - interleave;\n\nmatrix\n']
        '''nex的interleave模式'''
        self.nxs_gene = [f'#NEXUS\nBEGIN DATA;\ndimensions ntax={spe_num} nchar={seq_num};\n' \
                        f'format missing=?\ndatatype={self.pattern} gap= - interleave;\n\nmatrix\n']
        '''nex的interleave模式，以gene换行'''
        self.paml_file = [f"{spe_num}  {seq_num}\n\n"]
        self.axt_file = [f"{'-'.join(self.list_keys)}\n"]
        self.statistics = self.dict_statistics['prefix'] if self.dict_args["export_stat"] else ""
        list_lenth = [len(i) for i in self.list_keys]
        self.name_longest = max(list_lenth)  # 最长的序列名字
        self.get_str()
        self.nxs_interleave()

    def save(self):
        self.partition_detail = self.outpath + os.sep + 'partition.txt'
        with open(self.partition_detail, 'w', encoding="utf-8") as f4:
            f4.write("".join(list(chain(self.partition_style, self.partition_codon +
                                          self.bayes_style, self.partition_name +
                                          self.bayes_codon, self.partition_codname +
                                          self.iqtree_style, ["end;\n"] +
                                          self.iqtree_codon, ["end;"]))))
        # name mapping file
        with open(self.outpath + os.sep + 'name_mapping.txt', 'w', encoding="utf-8") as f4:
            f4.write("\n".join([f"{i}\t{self.name_mapping[i]}" for i in self.name_mapping]))
        if self.dict_args["export_axt"]:
            with open(self.outpath + os.sep + '%s.axt'%self.exportName, 'w', encoding="utf-8") as f1:
                f1.write("".join(self.axt_file))
        if self.dict_args["export_fas"]:
            with open(self.outpath + os.sep + '%s.fas'%self.exportName, 'w', encoding="utf-8") as f2:
                f2.write("".join(self.file))
        if self.dict_args["export_stat"]:
            with open(self.outpath + os.sep + 'statistics.csv', 'w', encoding="utf-8") as f3:
                f3.write("".join(self.statistics).replace('\t', ','))
        if self.dict_args["export_phylip"]:
            with open(self.outpath + os.sep + '%s.phy'%self.exportName, 'w', encoding="utf-8") as f5:
                f5.write("".join(self.phy_file))
        if self.dict_args["export_nex"]:
            with open(self.outpath + os.sep + '%s.nex'%self.exportName, 'w', encoding="utf-8") as f6:
                f6.write("".join(self.nxs_file) + ';\nEND;\n')
        if self.dict_args["export_paml"]:
            with open(self.outpath + os.sep + '%s.PML'%self.exportName, 'w', encoding="utf-8") as f7:
                f7.write("".join(self.paml_file))
        if self.dict_args["export_nexi"]:
            with open(self.outpath + os.sep + '%s_interleave.nex'%self.exportName, 'w', encoding="utf-8") as f8:
                f8.write("".join(self.nxs_inter) + ';\nEND;\n')
        if self.dict_args["export_nexig"]:
            with open(self.outpath + os.sep + '%s_bygene.nex'%self.exportName, 'w', encoding="utf-8") as f9:
                f9.write("".join(self.nxs_gene) + ';\nEND;\n')

    # def is_aligned(self, dict_taxon):  # 判定序列是否比对过
    #     list_lenth = []
    #     for i in dict_taxon:
    #         list_lenth.append(len(dict_taxon[i]))
    #     if len(set(list_lenth)) == 1:
    #         return True
    #     else:
    #         return False


class Matrix(QDialog, Ui_Matrix, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    # warning_signal = pyqtSignal(dict)
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    unalignedSig = pyqtSignal(list)
    workflow_progress = pyqtSignal(int)
    workflow_finished = pyqtSignal(str)
    ##用于flowchart自动popup combobox等操作
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    ##用于输入文件后判断用
    ui_closeSig = pyqtSignal(str)
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QDialog)

    def __init__(self, files=None, workPath=None, focusSig=None, workflow=False, parent=None):
        super(Matrix, self).__init__(parent)
        self.parent = parent
        self.function_name = "Concatenation"
        self.setupUi(self)
        self.comboBox_4.concatenate = True # 可以选择是否为PCGs
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        # 保存设置
        if not workflow:
            self.concatenate_settings = QSettings(
                self.thisPath + '/settings/concatenate_settings.ini', QSettings.IniFormat)
        else:
            self.concatenate_settings = QSettings(
                self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
            self.concatenate_settings.beginGroup("Workflow")
            self.concatenate_settings.beginGroup("temporary")
            self.concatenate_settings.beginGroup('Concatenate Sequence')
        # File only, no fallback to registry or or.
        self.concatenate_settings.setFallbacksEnabled(False)
        self.files = files
        self.workPath = workPath
        self.focusSig = focusSig if focusSig else pyqtSignal(str)  # 为了方便workflow
        self.workflow = workflow
        # 恢复用户的设置
        self.guiRestore()
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # self.groupBox_top_line.setStyleSheet('''QGroupBox{
        #         border-bottom:none;
        #         border-right:none;
        #         border-left:none;
        #         }
        #         QGroupBox::title{
        #         subcontrol-origin: margin;
        #         subcontrol-position: top left;
        # }''')
        self.groupBox_top_line_2.setStyleSheet('''QGroupBox{
                border-bottom:none;
                border-right:none;
                border-left:none;
                }
                QGroupBox::title{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                }''')
        self.unalignedSig.connect(self.unaligned)
        self.exception_signal.connect(self.popupException)
        # self.warning_signal.connect(self.popupWarning)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.comboBox_4.installEventFilter(self)
        self.comboBox_4.lineEdit().autoDetectSig.connect(self.popupAutoDec)    #自动识别可用的输入
        ##设置拖拽排序
        self.comboBox_4.view().setDragEnabled(True)
        self.comboBox_4.view().setDragDropMode(QAbstractItemView.InternalMove)
        self.comboBox_4.view().setDefaultDropAction(Qt.MoveAction)
        # self.comboBox_4.view().setSelectionMode(QAbstractItemView.MultiSelection)
        self.comboBox_4.view().installEventFilter(self)
        # 设置信号槽
        self.checkBox_6.toggled.connect(lambda : self.input(self.comboBox_4.fetchListsText()))
        self.checkBox_11.toggled.connect(self.comboBox_4.switch_PCGs)
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
        # 给codon添加提示
        self.groupBox_top_line_2.toggled.connect(self.prompt_codon_warning)
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-7-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-7-1-Brief-example"
        self.label_2.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))
        ##自动弹出识别文件窗口
        self.auto_popSig.connect(self.popupAutoDecSub)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        """
        if self.isFileIn():
            self.dict_args = {}
            self.dict_args["parent"] = self
            self.dict_args["exception_signal"] = self.exception_signal
            # self.dict_args["warning_signal"] = self.warning_signal
            self.dict_args["unaligned_signal"] = self.unalignedSig
            self.dict_args["progressSig"] = self.progressSig
            self.dict_args["workflow_progress"] = self.workflow_progress
            self.dict_args["files"] = self.comboBox_4.fetchListsText()
            self.dict_args["workPath"] = self.workPath
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath +
                                                        os.sep + "concatenate_results" + os.sep + self.output_dir_name)
            self.dict_args["exportPath"] = self.exportPath
            self.dict_args["export_phylip"] = self.checkBox.isChecked()
            self.dict_args["export_nex"] = self.checkBox_2.isChecked()
            self.dict_args["export_nexi"] = self.checkBox_3.isChecked()
            self.dict_args["export_nexig"] = self.checkBox_4.isChecked()
            self.dict_args["export_axt"] = self.checkBox_13.isChecked()
            self.dict_args["export_paml"] = self.checkBox_5.isChecked()
            self.dict_args["export_fas"] = self.checkBox_12.isChecked()
            self.dict_args["export_stat"] = self.checkBox_9.isChecked()
            self.dict_args["export_name"] = self.lineEdit.text() if self.lineEdit.text() else "concatenation"
            self.dict_args["missing_symbol"] = self.lineEdit_2.text() if self.lineEdit_2.text() else "?"
            self.dict_args["PCG_genes"] = self.comboBox_4.fetchPCGs()
            # if self.groupBox_top_line.isChecked():
            #     self.dict_args["draw_linear"] = True
            #     self.dict_args["fig_height"] = self.spinBox_5.value()
            #     self.dict_args["fig_width"] = self.spinBox_6.value()
            #     self.dict_args["label_size"] = self.spinBox_7.value()
            #     self.dict_args["Label_angle"] = self.spinBox_8.value()
            #     self.dict_args["Label_position"] = self.comboBox.currentText()
            #     self.dict_args["Label_color"] = self.pushButton_color.text()
            # else:
            #     self.dict_args["draw_linear"] = False
            if self.groupBox_top_line_2.isChecked():
                self.dict_args["split_codon"] = []
                if self.checkBox_7.isChecked(): self.dict_args.setdefault("split_codon", []).append(1)
                if self.checkBox_8.isChecked(): self.dict_args.setdefault("split_codon", []).append(2)
                if self.checkBox_10.isChecked(): self.dict_args.setdefault("split_codon", []).append(3)
            else:
                self.dict_args["split_codon"] = False
            if True not in list(self.dict_args.values()):
                QMessageBox.critical(
                    self,
                    "Concatenate sequence",
                    "<p style='line-height:25px; height:25px'>Please select output format(s) first!</p>")
                self.checkBox.setChecked(True)
                return
            ##描述，方便worfflow使用
            self.description = ""
            self.reference = ""
            ok = self.factory.remove_dir(self.dict_args["exportPath"], parent=self)
            if not ok:
                #提醒是否删除旧结果，如果用户取消，就不执行
                return
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
        else:
            QMessageBox.critical(
                self,
                "Concatenate sequence",
                "<p style='line-height:25px; height:25px'>Please input files first!</p>")

    def run_command(self):
        try:
            # 先清空文件夹
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [self.pushButton, self.progressBar, "start", self.dict_args["exportPath"], self.qss_file, self])
            self.seqMatrix = Seq_matrix(**self.dict_args)
            if not self.seqMatrix.ok:
                self.startButtonStatusSig.emit(
                    [self.pushButton, self.progressBar, "except", self.dict_args["exportPath"], self.qss_file,
                     self])
                self.seqMatrix.interrupt = True
                return
            # if "draw_linear" in self.dict_args and self.dict_args["draw_linear"]:
            #     self.dict_args["partition_file"] = self.seqMatrix.partition_detail
            #     Partition2fig(**self.dict_args)
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                           self.time_used)
            with open(self.dict_args["exportPath"] + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write("If you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n\n" + self.time_used_des)
            if not self.seqMatrix.unaligned and not self.seqMatrix.interrupt:
                if self.workflow:
                    ##work flow跑的
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton,
                            self.progressBar,
                            "workflow stop",
                            self.dict_args["exportPath"],
                            self.qss_file,
                            self])
                    self.workflow_finished.emit("finished")
                    return
                self.startButtonStatusSig.emit(
                    [self.pushButton, self.progressBar, "stop", self.dict_args["exportPath"], self.qss_file, self])
            else:
                self.startButtonStatusSig.emit(
                    [self.pushButton, self.progressBar, "except", self.dict_args["exportPath"], self.qss_file,
                     self])
            if not self.workflow:
                self.focusSig.emit(self.dict_args["exportPath"])
            self.seqMatrix.interrupt = True
            # self.seqMatrix.supplement()
            # if self.seqMatrix.dist_warning_message:
            #     self.dict_args["warning_signal"].emit(
            #         self.seqMatrix.dist_warning_message)
            # else:
            #     # if self.mafft_interrupt is not True:
            #     self.seqMatrix.concatenate()
            #     if not self.seqMatrix.unaligned and not self.seqMatrix.interrupt:
            #         if self.workflow:
            #             ##work flow跑的
            #             self.startButtonStatusSig.emit(
            #                 [
            #                     self.pushButton,
            #                     self.progressBar,
            #                     "workflow stop",
            #                     self.dict_args["exportPath"],
            #                     self.qss_file,
            #                     self])
            #             self.workflow_finished.emit("finished")
            #             return
            #         self.startButtonStatusSig.emit(
            #             [self.pushButton, self.progressBar, "stop", self.dict_args["exportPath"], self.qss_file, self])
            #     else:
            #         self.startButtonStatusSig.emit(
            #             [self.pushButton, self.progressBar, "except", self.dict_args["exportPath"], self.qss_file,
            #              self])
            #     if not self.workflow:
            #         self.focusSig.emit(self.dict_args["exportPath"])
            #     self.seqMatrix.interrupt = True
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.startButtonStatusSig.emit(
                [self.pushButton, self.progressBar, "except", self.dict_args["exportPath"], self.qss_file, self])

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        Stop
        """
        if self.isRunning():
            self.seqMatrix.interrupt = True
            if not self.workflow:
                QMessageBox.information(
                    self,
                    "Concatenate sequence",
                    "<p style='line-height:25px; height:25px'>Concatenation has been terminated!</p>")
            self.startButtonStatusSig.emit(
                [self.pushButton, self.progressBar, "except", self.dict_args["exportPath"], self.qss_file,
                 self])

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        open files
        """
        files = QFileDialog.getOpenFileNames(
            self, "Input Files",
            filter="Supported Format(*.fas *.fasta *.phy *.phylip *.nex *.nxs *.nexus);;")
        if files[0]:
            self.input(files[0])

    def unaligned(self, message):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            "<p style='line-height:25px; height:25px'>Unaligned sequences found, see details</p>")
        msg.setWindowTitle("Error")
        msg.setDetailedText("Unaligned sequences: " + ",".join(message))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def runProgress(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def popupException(self, exception):
        rgx = re.compile(r'Permission.+?[\'\"](.+\.csv)[\'\"]')
        if rgx.search(exception):
            csvfile = rgx.search(exception).group(1)
            reply = QMessageBox.critical(
                self,
                "Concatenate sequence",
                "<p style='line-height:25px; height:25px'>Please close '%s' file first!</p>"%os.path.basename(csvfile),
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

    @pyqtSlot(list)
    def popupWarning(self, warning):
        ## 为了统一，统一用的列表
        msg = QMessageBox(self)
        info = warning[0]
        if type(info) == OrderedDict:
            ## 有缺失基因的情况，这时候warning是个字典
            msg.setIcon(QMessageBox.Information)
            msg.setText(
                "<p style='line-height:25px; height:25px'>Missing genes are replaced with '%s' "
                "(see details or 'missing_genes.txt')</p>"%(self.lineEdit_2.text()))
            msg.setWindowTitle("Concatenation Warning")
            max_len_taxa = len(max(list(info), key=len))
            max_len_taxa = max_len_taxa if max_len_taxa > 7 else 7 #要大于species的占位符
            list_detail = ["Species".ljust(max_len_taxa) + " |Missing genes"] + [str(i).ljust(max_len_taxa) + " |" + str(info[i]) for i in info]
            # html_detail = "<html>" + "\n".join(list_detail).replace(" ", "&nbsp;") + "</html>"
            msg.setDetailedText("\n".join(list_detail))
            msg.setStandardButtons(QMessageBox.Ok)
            with open(self.dict_args["exportPath"] + os.sep + "missing_genes.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(list_detail))
            msg.exec_()
        elif type(info) == str:
            # 序列中DNA和AA混合了
            msg.setIcon(QMessageBox.Warning)
            msg.setText(
                "<p style='line-height:25px; height:25px'>Mixed nucleotide and AA sequences (see details)</p>")
            msg.setWindowTitle("Concatenation Warning")
            msg.setDetailedText(info)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
        elif type(info) == list:
            # 序列不是3的倍数
            msg.setIcon(QMessageBox.Information)
            msg.setText(
                f"<p style='line-height:25px; height:25px'>The length of {len(info)} gene(s) is not a multiple of 3 "
                f"(see details or 'genes_not_PCGs.txt'), they will be ignored when splitting the codons.</p>")
            msg.setWindowTitle("Concatenation Warning")
            msg.setDetailedText("\n".join(info))
            msg.setStandardButtons(QMessageBox.Ok)
            with open(self.dict_args["exportPath"] + os.sep + "genes_not_PCGs.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(info))
            msg.exec_()

    def guiSave(self):
        # Save geometry
        self.concatenate_settings.setValue('size', self.size())
        # self.concatenate_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.concatenate_settings.setValue(name, state)
            if isinstance(obj, QLineEdit):
                text = obj.text()
                self.concatenate_settings.setValue(name, text)
            if isinstance(obj, QSpinBox):
                value = obj.value()
                self.concatenate_settings.setValue(name, value)
            # if isinstance(obj, QPushButton):
            #     if name == "pushButton_color":
            #         color = obj.palette().color(1)
            #         self.concatenate_settings.setValue(name, color.name())
            if isinstance(obj, QComboBox):
                if name == "comboBox":
                    # save combobox selection to registry
                    index = obj.currentIndex()
                    self.concatenate_settings.setValue(name, index)
            if isinstance(obj, QGroupBox):
                state = obj.isChecked()
                self.concatenate_settings.setValue(name, state)

    def guiRestore(self):

        # Restore geometry
        size = self.factory.judgeWindowSize(self.concatenate_settings, 646, 476)
        self.resize(size)
        self.factory.centerWindow(self)
        # self.move(self.concatenate_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox":
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.concatenate_settings.value(name, "0")
                    if type(index) != str:
                        index = "0"
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
                else:
                    if self.files:
                        self.input(self.files)
                    else:
                        self.input([])
            if isinstance(obj, QCheckBox):
                if name != "checkBox_11":
                    value = self.concatenate_settings.value(
                        name, "true")  # get stored value from registry
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
                else:
                    obj.setChecked(False)
            if isinstance(obj, QLineEdit):
                text = self.concatenate_settings.value(name, obj.text())
                obj.setText(text)
            if isinstance(obj, QSpinBox):
                value = self.concatenate_settings.value(name, None)
                if value:
                    obj.setValue(int(value))
            if isinstance(obj, QGroupBox):
                value = self.concatenate_settings.value(
                    name, "false")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            # if isinstance(obj, QPushButton):
            #     if name == "pushButton_color":
            #         color = self.concatenate_settings.value(name, "#F9C997")
            #         obj.setStyleSheet("background-color:%s"%color)
            #         obj.setText(color)
            #         obj.clicked.connect(self.changePbColor)

    def closeEvent(self, event):
        self.guiSave()
        self.closeSig.emit("Concatenation", self.fetchWorkflowSetting())
        self.lineEdit.clearFocus()
        self.lineEdit.deselect()
        ###断开showSig和closeSig的槽函数连接
        try:
            self.showSig.disconnect()
        except:
            pass
        try:
            self.closeSig.disconnect()
        except:
            pass
        if self.workflow:
            self.ui_closeSig.emit("Concatenation")
            ## 自动跑的时候不杀掉程序
            return
        if self.isRunning():
            # print(self.isRunning())
            reply = QMessageBox.question(
                self,
                "Concatenate sequence",
                "<p style='line-height:25px; height:25px'>Concatenation is still running, terminate it?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.seqMatrix.interrupt = True
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
                files = [i for i in files if os.path.splitext(i)[1].upper() in
                         [".FAS", ".FASTA", ".PHY", ".PHYLIP", ".NEX", ".NXS", ".NEXUS"]]
                self.input(files)
        if isinstance(
                obj,
                QListWidget):
            if event.type() == QEvent.ChildRemoved:
                obj.setDragEnabled(True)
                obj.setDragDropMode(QAbstractItemView.InternalMove)
                obj.setDefaultDropAction(Qt.MoveAction)
                list_inputs = self.comboBox_4.fetchListsText()
                self.comboBox_4.refreshInputs(list_inputs, sort=False, judge=False)
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
        return super(Matrix, self).eventFilter(obj, event)  # 0

    def input(self, files):
        empty_files = []
        rest_files = []
        for file in files:
            if os.stat(file).st_size == 0:
                empty_files.append(os.path.basename(file))
            else:
                rest_files.append(file)
        if empty_files:
            if len(empty_files) > 1:
                word1 = "files are"
                word2 = "they will"
            else:
                word1 = "file is"
                word2 = "it will"
            QMessageBox.warning(
                self,
                "Concatenation",
                "<p style='line-height:25px; height:25px'>%s %s empty, %s be ignored!</p>" % (str(
                    empty_files), word1, word2),
                QMessageBox.Ok)
        self.comboBox_4.refreshInputs(rest_files, sort=self.checkBox_6.isChecked())

    def isRunning(self):
        if hasattr(self, "seqMatrix") and (not self.seqMatrix.interrupt):
            return True
        else:
            return False

    def popupAutoDec(self, init=False):
        self.init = init
        self.factory.popUpAutoDetect("Concatenation", self.workPath, self.auto_popSig, self)

    def popupAutoDecSub(self, popupUI):
        if not popupUI:
            if not self.init:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "<p style='line-height:25px; height:25px'>No available file detected!</p>")
            return
        if not self.init:
            popupUI.checkBox.setVisible(False)
        if popupUI.exec_() == QDialog.Accepted:
            widget = popupUI.listWidget_framless.itemWidget(popupUI.listWidget_framless.selectedItems()[0])
            autoInputs = widget.autoInputs
            self.input(autoInputs)

    def fetchWorkflowSetting(self):
        '''
            export format;
            export name
        '''
        settings = '''<p class="title">***Concatenate Sequence***</p>'''
        list_formats = []
        for checkbox in [self.checkBox, self.checkBox_2, self.checkBox_3, self.checkBox_4, self.checkBox_5,
                         self.checkBox_9, self.checkBox_12, self.checkBox_13]:
            if checkbox.isChecked():
                list_formats.append(checkbox.text())
        formats = ", ".join(list_formats) if list_formats else "None"
        settings += '<p>Export formats: <a href="self.Concatenation_exe ' \
                    'factory.highlightWidgets(x.checkBox,x.checkBox_2,x.checkBox_3,x.checkBox_4,x.checkBox_5,' \
                    'x.checkBox_9,x.checkBox_12,x.checkBox_13)">%s</a></p>'%formats
        export_name = self.lineEdit.text()
        settings += '<p>Export file name: <a href="self.Concatenation_exe lineEdit.setFocus()' \
                    ' lineEdit.selectAll() factory.highlightWidgets(x.lineEdit)">%s</a></p>'%export_name
        return settings

    def showEvent(self, event):
        QTimer.singleShot(100, lambda: self.showSig.emit(self))
        # self.showSig.emit(self)

    def isFileIn(self):
        return self.comboBox_4.count()

    def changePbColor(self):
        button = self.sender()
        ini_color = button.palette().color(1)
        color = QColorDialog.getColor(QColor(ini_color), self)
        if color.isValid():
            button.setText(color.name())
            button.setStyleSheet("background-color:%s"%color.name())

    @pyqtSlot(str)
    def popupEmptyFileWarning(self, text):
        QMessageBox.warning(
            self,
            "Concatenation Warning",
            "<p style='line-height:25px; height:25px'>%s!</p>" % text)

    @pyqtSlot(bool)
    def prompt_codon_warning(self, bool_):
        if bool_:
            QMessageBox.information(
                self,
                "Concatenation",
                "<p style='line-height:25px; height:25px'>Please ensure that your sequences that are marked as \"PCGS\" "
                "are protein-coding "
                "and the length of each alignment is a multiple of 3!</p>")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Matrix()
    ui.show()
    sys.exit(app.exec_())
