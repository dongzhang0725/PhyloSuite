#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from src.CustomWidget import MySettingTableModel
from uifiles.Ui_parseANNT_settings import Ui_ParAnnt_settings
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from uifiles.Ui_parseANNT import Ui_parseANNT
from src.factory import Factory, WorkThread
import sys
import os
import re
import traceback
import inspect
from win32com import client as wc
from collections import OrderedDict


class ParANNT_settings(QDialog, Ui_ParAnnt_settings, object):

    def __init__(
            self,
            parent=None):
        super(ParANNT_settings, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.setupUi(self)
        # 保存设置
        self.parseANNT_settings = QSettings(
            self.thisPath +
            '/settings/parseANNT_settings.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.parseANNT_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 设置比例
        self.splitter.setStretchFactor(1, 7)
        items = ["tRNA Abbreviation",
                      "Protein Gene Full Name",
                      "Name From Word"
                      ]
        self.listWidget.addItems(items)
        self.listWidget.itemClicked.connect(self.display_table)
        self.display_table(self.listWidget.item(0))

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        add
        """
        currentModel = self.tableView.model()
        if currentModel:
            currentData = currentModel.arraydata
            header = currentModel.headerdata
            currentModel.layoutAboutToBeChanged.emit()
            length = len(header)
            currentData.append([""] * length)
            currentModel.layoutChanged.emit()
            self.tableView.scrollToBottom()

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        delete
        """
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in indices), reverse=True)
            for row in rows:
                currentModel.layoutAboutToBeChanged.emit()
                currentData.pop(row)
                currentModel.layoutChanged.emit()

    def depositeData(self):
        name = self.listWidget.currentItem().text()
        dict_data = self.parseANNT_settings.value(
                        "extract listed gene")
        currentModel = self.tableView.model()
        array = currentModel.arraydata
        dict_data[name] = array
        self.parseANNT_settings.setValue(
            "extract listed gene", dict_data)

    def display_table(self, listItem):
        listItem.setSelected(True)
        # self.listWidget.setItemSelected(listItem, True)
        name = listItem.text()
        ini_dict_data = {"tRNA Abbreviation": [["tRNA-Ala", "A"],
                                                ["tRNA-Cys", "C"],
                                                ["tRNA-Asp", "D"],
                                                ["tRNA-Glu", "E"],
                                                ["tRNA-Phe", "F"],
                                                ["tRNA-Gly", "G"],
                                                ["tRNA-His", "H"],
                                                ["tRNA-Ile", "I"],
                                                ["tRNA-Lys", "K"],
                                                ["tRNA-Leu", "L"],
                                                ["tRNA-Leu", "L"],
                                                ["tRNA-Met", "M"],
                                                ["tRNA-Asn", "N"],
                                                ["tRNA-Pro", "P"],
                                                ["tRNA-Gln", "Q"],
                                                ["tRNA-Arg", "R"],
                                                ["tRNA-Ser", "S"],
                                                ["tRNA-Ser", "S"],
                                                ["tRNA-Thr", "T"],
                                                ["tRNA-Val", "V"],
                                                ["tRNA-Trp", "W"],
                                                ["tRNA-Tyr", "Y"]],
                         "Protein Gene Full Name": [["atp6", "ATP synthase F0 subunit 6"],
                                                    ["atp8", "ATP synthase F0 subunit 8"],
                                                    ["cox1", "cytochrome c oxidase subunit 1"],
                                                    ["cox2", "cytochrome c oxidase subunit 2"],
                                                    ["cox3", "cytochrome c oxidase subunit 3"],
                                                    ["cytb", "cytochrome b"],
                                                    ["nad1", "NADH dehydrogenase subunit 1"],
                                                    ["nad2", "NADH dehydrogenase subunit 2"],
                                                    ["nad3", "NADH dehydrogenase subunit 3"],
                                                    ["nad4", "NADH dehydrogenase subunit 4"],
                                                    ["nad4L", "NADH dehydrogenase subunit 4L"],
                                                    ["nad5", "NADH dehydrogenase subunit 5"],
                                                    ["nad6", "NADH dehydrogenase subunit 6"]],
                         "Name From Word": [["trnY(gta)", "tRNA-Tyr(gta)"],
                                            ["trnY", "tRNA-Tyr(gta)"],
                                            ["trnW(tca)", "tRNA-Trp(tca)"],
                                            ["trnW", "tRNA-Trp(tca)"],
                                            ["trnV(tac)", "tRNA-Val(tac)"],
                                            ["trnV", "tRNA-Val(tac)"],
                                            ["trnT(tgt)", "tRNA-Thr(tgt)"],
                                            ["trnT", "tRNA-Thr(tgt)"],
                                            ["trnR(tcg)", "tRNA-Arg(tcg)"],
                                            ["trnR", "tRNA-Arg(tcg)"],
                                            ["trnQ(ttg)", "tRNA-Gln(ttg)"],
                                            ["trnQ", "tRNA-Gln(ttg)"],
                                            ["trnP(tgg)", "tRNA-Pro(tgg)"],
                                            ["trnP", "tRNA-Pro(tgg)"],
                                            ["trnN(gtt)", "tRNA-Asn(gtt)"],
                                            ["trnN", "tRNA-Asn(gtt)"],
                                            ["trnM(cat)", "tRNA-Met(cat)"],
                                            ["trnM", "tRNA-Met(cat)"],
                                            ["trnK(ctt)", "tRNA-Lys(ctt)"],
                                            ["trnK", "tRNA-Lys(ctt)"],
                                            ["trnI(gat)", "tRNA-Ile(gat)"],
                                            ["trnI", "tRNA-Ile(gat)"],
                                            ["trnH(gtg)", "tRNA-His(GTG)"],
                                            ["trnH", "tRNA-His(gtg)"],
                                            ["trnG(tcc)", "tRNA-Gly(tcc)"],
                                            ["trnG", "tRNA-Gly(tcc)"],
                                            ["trnF(gaa)", "tRNA-Phe(gaa)"],
                                            ["trnF", "tRNA-Phe(gaa)"],
                                            ["trnE(ttc)", "tRNA-Glu(ttc)"],
                                            ["trnE", "tRNA-Glu(ttc)"],
                                            ["trnD(gtc)", "tRNA-Asp(gtc)"],
                                            ["trnD", "tRNA-Asp(gtc)"],
                                            ["trnC(gca)", "tRNA-Cys(gca)"],
                                            ["trnC", "tRNA-Cys(gca)"],
                                            ["trnA(tgc)", "tRNA-Ala(tgc)"],
                                            ["trnA", "tRNA-Ala(tgc)"],
                                            ["tRNA-Val", "tRNA-Val(tac)"],
                                            ["tRNA-Tyr", "tRNA-Tyr(gta)"],
                                            ["tRNA-Trp", "tRNA-Trp(tca)"],
                                            ["tRNA-Thr", "tRNA-Thr(tgt)"],
                                            ["tRNA-Pro", "tRNA-Pro(tgg)"],
                                            ["tRNA-Phe", "tRNA-Phe(gaa)"],
                                            ["tRNA-Met", "tRNA-Met(cat)"],
                                            ["tRNA-Lys", "tRNA-Lys(ctt)"],
                                            ["tRNA-Ile", "tRNA-Ile(gat)"],
                                            ["tRNA-His", "tRNA-His(GTG)"],
                                            ["tRNA-Gly", "tRNA-Gly(tcc)"],
                                            ["tRNA-Glu", "tRNA-Glu(ttc)"],
                                            ["tRNA-Gln", "tRNA-Gln(ttg)"],
                                            ["tRNA-Cys", "tRNA-Cys(gca)"],
                                            ["tRNA-Asp", "tRNA-Asp(gtc)"],
                                            ["tRNA-Asn", "tRNA-Asn(gtt)"],
                                            ["tRNA-Arg", "tRNA-Arg(tcg)"],
                                            ["tRNA-Ala", "tRNA-Ala(tgc)"],
                                            ["small subunit ribosomal RNA", "12S"],
                                            ["small ribosomal RNA subunit RNA", "12S"],
                                            ["small ribosomal RNA", "12S"],
                                            ["s-rRNA", "12S"],
                                            ["ribosomal RNA small subunit", "12S"],
                                            ["ribosomal RNA large subunit", "16S"],
                                            ["large subunit ribosomal RNA", "16S"],
                                            ["large ribosomal RNA subunit RNA", "16S"],
                                            ["large ribosomal RNA", "16S"],
                                            ["l-rRNA", "16S"],
                                            ["cytochrome c oxidase subunit III", "COX3"],
                                            ["cytochrome c oxidase subunit II", "COX2"],
                                            ["cytochrome c oxidase subunit I", "COX1"],
                                            ["cytochrome c oxidase subunit 3", "COX3"],
                                            ["cytochrome c oxidase subunit 2", "COX2"],
                                            ["cytochrome c oxidase subunit 1", "COX1"],
                                            ["cytochrome b", "CYTB"],
                                            ["ND6", "NAD6"],
                                            ["ND5", "NAD5"],
                                            ["ND4L", "NAD4L"],
                                            ["ND4", "NAD4"],
                                            ["ND3", "NAD3"],
                                            ["ND2", "NAD2"],
                                            ["ND1", "NAD1"],
                                            ["NADH dehydrogenase subunit5", "NAD5"],
                                            ["NADH dehydrogenase subunit 6", "NAD6"],
                                            ["NADH dehydrogenase subunit 5", "NAD5"],
                                            ["NADH dehydrogenase subunit 4L", "NAD4L"],
                                            ["NADH dehydrogenase subunit 4", "NAD4"],
                                            ["NADH dehydrogenase subunit 3", "NAD3"],
                                            ["NADH dehydrogenase subunit 2", "NAD2"],
                                            ["NADH dehydrogenase subunit 1", "NAD1"],
                                            ["CYT B", "CYTB"],
                                            ["COXIII", "COX3"],
                                            ["COXII", "COX2"],
                                            ["COXI", "COX1"],
                                            ["COIII", "COX3"],
                                            ["COII", "COX2"],
                                            ["COI", "COX1"],
                                            ["COB", "CYTB"],
                                            ["CO3", "COX3"],
                                            ["CO2", "COX2"],
                                            ["CO1", "COX1"],
                                            ["ATPase subunit 6", "ATP6"],
                                            ["ATPASE8", "ATP8"],
                                            ["ATPASE6", "ATP6"],
                                            ["ATPASE 8", "ATP8"],
                                            ["ATPASE 6", "ATP6"],
                                            ["ATP synthase F0 subunit 6", "ATP6"],
                                            ["16s rRNA", "16S"],
                                            ["16S subunit RNA", "16S"],
                                            ["16S ribosomal RNA", "16S"],
                                            ["16S rRNA", "16S"],
                                            ["12s rRNA", "12S"],
                                            ["12S subunit RNA", "12S"],
                                            ["12S ribosomal RNA", "12S"],
                                            ["12S rRNA", "12S"],
                                            ["12S Ribosomal RNA", "12S"]],
                         }
        dict_data = self.parseANNT_settings.value(
                        "extract listed gene", None)
        if not dict_data:
            dict_data = ini_dict_data
            self.parseANNT_settings.setValue(
                "extract listed gene", dict_data)
        header = ["Old Name", "New Name"]
        array = dict_data[name]
        tableModel = MySettingTableModel(array, header)
        self.tableView.setModel(tableModel)
        self.tableView.resizeColumnsToContents()
        tableModel.dataChanged.connect(self.depositeData)
        tableModel.layoutChanged.connect(self.depositeData)



class Parse_annotation(Factory):  # 解析线粒体注释文件

    def __init__(self, **kargs):
        self.dict_args = kargs
        self.outpath = kargs["exportPath"]
        self.workPath = kargs["workPath"]
        self.usernota_file = kargs["file"]
        self.latin_name = kargs["name"]
        self.template = kargs["temp"]
        self.tbl2asn = kargs["t2n"]
        codon = kargs["codon"]
        self.codon_table = " [mgcode=%s]" % codon if codon != "" else ""
        self.completeness = " [completeness=%s]" % kargs[
            "complete"] if kargs["complete"] != "" else ""
        self.strain = " [strain=%s]" % kargs[
            "strain"] if kargs["strain"] != "" else ""
        self.isolate = " [isolate=%s]" % kargs[
            "isolate"] if kargs["isolate"] != "" else ""
        self.synonym = " [synonym=%s]" % kargs[
            "synonym"] if kargs["synonym"] != "" else ""
        self.host = " [host=%s]" % kargs["host"] if kargs["host"] != "" else ""
        self.country = " [country=%s]" % kargs[
            "country"] if kargs["country"] != "" else ""
        self.others = " " + kargs["others"] if kargs["others"] != "" else ""
        self.lineage = " [lineage=%s]" % kargs[
            "lineage"] if kargs["lineage"] != "" else ""
        self.release_date = r" -H %s" % kargs[
            "release_date"] if kargs["release_date"] != "" else ""
        # 生成替换文件
        self.dict_tRNA = kargs["dict_tRNA"]
        self.dict_replace = kargs["dict_replace"]
        self.dict_product = kargs["dict_product"]
        # 执行
        sequence, table_csv, feature_tbl = self.main_table()
        self.sequence = sequence
        self.latin_ = self.latin_name.replace(' ', '_')
        #         self.Log_Show("Saving results...\n", self.log_show)
        genome = '>{self.latin_} [topology=circular] [location=mitochondrion] \
        [organism={self.latin_name}]{self.codon_table}{self.completeness}{self.strain}\
        {self.isolate}{self.synonym}{self.host}{self.country}{self.lineage}{self.others}\n{self.sequence}\n'.format(
            self=self)
        with open(self.outpath + os.sep + self.latin_name + '_PCGs_each.fas', 'w', encoding="utf-8") as f:
            f.write(self.pro)
        with open(self.outpath + os.sep + self.latin_name + '_PCGs_all.fas', 'w', encoding="utf-8") as f1:
            f1.write(self.PCGs_all)
        with open(self.outpath + os.sep + 'geneCounter.txt', 'w', encoding="utf-8") as f2:
            output = "genes not found:\n" + \
                     "\t".join(
                         self.allGenes) + "\nSuperfluous genes\n" + "\t".join(self.superfluousGene)
            f2.write(output)
        # 存全基因组的fas文件
        with open(self.outpath + os.sep + self.latin_name + '.fsa', 'w', encoding="utf-8") as f3:
            f3.write(genome)
        with open(self.outpath + os.sep + self.latin_name + '.csv', 'w', encoding="utf-8") as f:
            f.write(table_csv.replace('\t', ','))
        with open(self.outpath + os.sep + self.latin_name + '.tbl', 'w', encoding="utf-8") as f2:
            f2.write(feature_tbl)
        template_line = " -t " + \
                        "\"%s\""%self.template if self.template != "" else ""
        commands = self.tbl2asn + template_line + \
            " -p " + self.outpath + " -a s -a b -V vb" + self.release_date
        with open(self.outpath + os.sep + "commands.txt", "w", errors="ignore") as f:
            f.write(commands)
        os.system(commands)
        self.dict_args["progressSig"].emit(100)
        os.remove(self.xml_11)

    def match_genes(self, each_gene):
        flag = False
        for j in self.allGenes:
            rgx = each_gene.replace("(", "\(").replace(")", "\)")
            if re.search(rgx + "$", j, re.I):
                flag = True
                self.allGenes.remove(j)
        if not flag:
            self.superfluousGene.append(each_gene)

    # 判断是否该基因复制了,标志是基因名后面加了-*，如"cytb-1","cytb-2","cytb-3"
    def if_duplicated(self, name):
        flag, dupl, cleanName = False, "", name
        rgx = re.compile(r"-\d+$")
        search_ = rgx.search(name)
        if search_:
            flag = True
            dupl = search_.group()
            cleanName = rgx.sub("", name)
        # 如果用户标记的是-1，不被识别为重复基因
        if dupl == "-1":
            flag = False
        return flag, dupl, cleanName  # (True, '-2', 'cytb')

    def TableReplace(self, name, size, seq, pro):
        seq = seq.strip()  # 有换行符
        p = re.compile(
            r'COX[1-3]|NAD4L|NAD[1-6]|ND[1-6]|COB|CYTB|ATP[68]', re.I)  # 忽略大小写
        match = p.search(name)
        sign = 'H'
        print(name, size, seq, pro)
        assert name
        flag, dupl, cleanName = self.if_duplicated(name)
        if name[0] == '-':
            name = name.strip('-')
            sign = 'L'
            dict1 = {"a": "t", "t": "a", "c": "g", "g": "c"}
            # 将序列反转,注意这里必须将序列小写才能完成转换，因为字典是小写的，这样也可以区分互补与没互补的
            seq1 = seq[::-1].lower()
            seq = ''
            for i in seq1:
                if i in 'atcg':
                    seq += dict1[i]  # 互补序列
                else:
                    seq += i  # 遇到兼并碱基就原样返回
        if name.startswith('tRNA') or name.startswith('-tRNA'):  # tRNA基因
            self.match_genes(name)
            regular = re.search(r'(tRNA-\w+)[(](\w+)[)]', name)
            if regular:
                new_name, inv_codon = regular.groups()
                inv_codon = inv_codon.upper()
            else:  # 如果用户没有提供反密码子，就返回空
                new_name = name.strip('-')  # 负号去掉
                inv_codon = ''
            return new_name + dupl if flag else new_name, '', '', inv_codon, sign, seq, pro
        elif match:  # None就不会执行， 这里是蛋白基因
            new_name = match.group().lower()  # 明天看看这里有没有错
            if new_name == 'nad4l':  # nad4l情况的处理
                new_name = 'nad4L'
            self.match_genes(new_name)
            ini = seq[0:3]
            if int(size) % 3 == 0:
                ter = seq[-3:]
                self.PCGs_all += seq
            elif int(size) % 3 == 1:
                ter = seq[-1]
                self.PCGs_all += seq[:-1]
            elif int(size) % 3 == 2:
                ter = seq[-2:]
                self.PCGs_all += seq[:-2]
            pro += '>' + new_name + \
                dupl + '\n' + seq + '\n' if flag else '>' + \
                new_name + '\n' + seq + '\n'
            # 蛋白基因的时候，反密码子返回一个空,互补是，反密码子返回大写的
            return new_name + dupl if flag else new_name, ini.upper(), ter.upper(), '', sign, seq, pro
        else:
            self.match_genes(name)
            return name, '', '', '', sign, seq, pro  # 序列也要返回

    def ser_leu(self, feature, i):  # 处理LEU，SER的简写
        if re.search(r'\s[TU]AG\s', i, re.I):
            feature = 'L1'
            cr = 'CUN'
        elif re.search(r'\s[TU]AA\s', i, re.I):
            feature = 'L2'
            cr = 'UUR'
        elif re.search(r'\s[GTUA]C[TU]\s', i, re.I):
            feature = 'S1'
            cr = 'AGN'
        elif re.search(r'\s[TU]GA\s', i, re.I):
            feature = 'S2'
            cr = 'UCN'
        else:
            feature = feature
            cr = None
        return feature, cr

    def add_table(self, name, item):  # 处理join的情况
        list_dict = list(self.dict_tbl.keys())

        def is_index_start(list_):
            return len(list_) == 2 and list_[0].isdigit() and list_[1].isdigit()
        if not self.dict_tbl.get(name):
            self.dict_tbl[name] = item
        else:
            insert_ = "\t".join(item[0].split("\t")[:2])  # 前面2个索引12025\t12850
            index = []
            if list_dict.index(name) == 0:  # 如果是第一个item，就要特殊处理
                if self.count_1st_item == 0:  # 第一次
                    self.first_index = "\t".join(
                        self.dict_tbl[name][0].split("\t")[:2])
                    for num, i in enumerate(self.dict_tbl[name]):  # 遍历找插入位置的索引
                        # 如果读到了索引行且下一行接着的是注释
                        if i[0].isdigit() and self.dict_tbl[name][num + 1].startswith("\t"):
                            new = self.dict_tbl[name][num].replace(
                                self.first_index, insert_)  # 替换为新的起始
                            self.dict_tbl[name][num] = new  # 换掉
                            index.append(num + 1)
                    for numb, each_index in enumerate(index):
                        # 必须加上数字，因为之前添加内容以后索引就变了
                        self.dict_tbl[name].insert(
                            each_index + numb, self.first_index)
                else:
                    for num, i in enumerate(self.dict_tbl[name]):  # 遍历找插入位置的索引
                        list_i = i.split("\t")
                        # 如果读到了索引行且下一行接着的是self.first_index
                        if i[0].isdigit() and self.dict_tbl[name][num + 1] == self.first_index:
                            index.append(num + 1)
                        elif is_index_start(list_i) and self.dict_tbl[name][num + 1] == self.first_index:
                            index.append(num + 1)
                    for numb, each_index in enumerate(index):
                        self.dict_tbl[name].insert(each_index + numb, insert_)
                self.count_1st_item += 1
            else:
                for num, i in enumerate(self.dict_tbl[name]):  # 遍历找插入位置的索引
                    # 如果读到了索引行且下一行接着的是注释
                    if i[0].isdigit() and self.dict_tbl[name][num + 1].startswith("\t"):
                        index.append(num + 1)
                    else:
                        list_i = i.split("\t")
                        # 如果已经有加过索引了,并且找到最下面的索引
                        if is_index_start(list_i) and not is_index_start(self.dict_tbl[name][num + 1].split("\t")):
                            index.append(num + 1)
                for numb, each_index in enumerate(index):
                    # 必须加上数字，因为之前添加内容以后索引就变了
                    self.dict_tbl[name].insert(each_index + numb, insert_)

    def forSqn(self, i, flag, cleanName):
        # 只识别蛋白基因、tRNA和rRNA到gb文件
        #i = 'cox1    1    1644    1644        ATG    TAA        +    sequence'
        match = re.match(
            r'COX[1-3]|NAD4L|NAD[1-6]|ND[1-6]|COB|CYTB|ATP[68]', i, re.IGNORECASE)
        list_line = i.split('\t')
        if i.startswith('tRNA'):
            if list_line[8] == 'L':  # 写进tbl文件
                if re.match(r'tRNA-Leu|tRNA-Ser', i, re.I):
                    feature = ''
                    item_tbl = '%s\t%s\ttRNA\n\t\t\tproduct\t%s\n\t\t\tcodon_recognized\t%s\n'\
                        % (list_line[2], list_line[1], cleanName, self.ser_leu(feature, i)[1])
                    self.add_table(
                        self.ser_leu(feature, i)[0], item_tbl.split("\n")[:-1])
                else:
                    item_tbl = '%s\t%s\ttRNA\n\t\t\tproduct\t%s\n'\
                        % (list_line[2], list_line[1], cleanName)
                    self.add_table(
                        list_line[0], item_tbl.split("\n")[:-1])
            else:
                if re.match(r'tRNA-Leu|tRNA-Ser', i, re.I):
                    feature = ''
                    item_tbl = '%s\t%s\ttRNA\n\t\t\tproduct\t%s\n\t\t\tcodon_recognized\t%s\n'\
                        % (list_line[1], list_line[2], cleanName, self.ser_leu(feature, i)[1])
                    self.add_table(
                        self.ser_leu(feature, i)[0], item_tbl.split("\n")[:-1])
                else:
                    item_tbl = '%s\t%s\ttRNA\n\t\t\tproduct\t%s\n'\
                        % (list_line[1], list_line[2], cleanName)
                    self.add_table(
                        list_line[0], item_tbl.split("\n")[:-1])
        elif match:  # 匹配上了蛋白基因
            name_ = cleanName.lower() if not re.search(
                r"nad4l", cleanName, re.I) else "nad4L"
            if list_line[8] == 'L':
                # 这一步的or是否会存在问题
                if list_line[6] == 'T' or list_line[6] == 'TA':
                    item_tbl = "%s\t%s\tgene\n\t\t\tgene\t%s\n%s\t%s\tCDS\n\t\t\tproduct\t%s\n\t\t\ttransl_except\t(pos:complement(%s),aa:TERM)\n\t\t\tnote\tTAA stop codon is completed by the addition of 3' A residues to the mRNA\n"\
                        % (list_line[2], list_line[1], name_, list_line[2], list_line[1], self.dict_product[cleanName], list_line[1])
                    self.add_table(
                        list_line[0], item_tbl.split("\n")[:-1])
                else:
                    item_tbl = "%s\t%s\tgene\n\t\t\tgene\t%s\n%s\t%s\tCDS\n\t\t\tproduct\t%s\n"\
                        % (list_line[2], list_line[1], name_, list_line[2], list_line[1], self.dict_product[cleanName])
                    self.add_table(
                        list_line[0], item_tbl.split("\n")[:-1])
            else:
                # 这一步的or是否会存在问题
                if list_line[6] == 'T' or list_line[6] == 'TA':
                    item_tbl = "%s\t%s\tgene\n\t\t\tgene\t%s\n%s\t%s\tCDS\n\t\t\tproduct\t%s\n\t\t\ttransl_except\t(pos:%s,aa:TERM)\n\t\t\tnote\tTAA stop codon is completed by the addition of 3' A residues to the mRNA\n"\
                        % (list_line[1], list_line[2], name_, list_line[1], list_line[2], self.dict_product[cleanName], list_line[2])
                    self.add_table(
                        list_line[0], item_tbl.split("\n")[:-1])
                else:
                    item_tbl = "%s\t%s\tgene\n\t\t\tgene\t%s\n%s\t%s\tCDS\n\t\t\tproduct\t%s\n"\
                        % (list_line[1], list_line[2], name_, list_line[1], list_line[2], self.dict_product[cleanName])
                    self.add_table(
                        list_line[0], item_tbl.split("\n")[:-1])
        elif i.startswith('12S') or i.startswith('16S'):
            if list_line[8] == 'L':
                if cleanName == '12S':
                    item_tbl = '%s\t%s\trRNA\n\t\t\tproduct\t12S ribosomal RNA\n'\
                        % (list_line[2], list_line[1])
                    self.add_table(
                        list_line[0], item_tbl.split("\n")[:-1])
                elif cleanName == '16S':
                    item_tbl = '%s\t%s\trRNA\n\t\t\tproduct\t16S ribosomal RNA\n'\
                        % (list_line[2], list_line[1])
                    self.add_table(
                        list_line[0], item_tbl.split("\n")[:-1])
            else:
                if cleanName == '12S':
                    item_tbl = '%s\t%s\trRNA\n\t\t\tproduct\t12S ribosomal RNA\n'\
                        % (list_line[1], list_line[2])
                    self.add_table(
                        list_line[0], item_tbl.split("\n")[:-1])
                elif cleanName == '16S':
                    item_tbl = '%s\t%s\trRNA\n\t\t\tproduct\t16S ribosomal RNA\n'\
                        % (list_line[1], list_line[2])
                    self.add_table(
                        list_line[0], item_tbl.split("\n")[:-1])

        # 如果是L1\S1等，就要判断一下
        dict_key = self.ser_leu(feature, i)[0] if re.match(
            r'tRNA-Leu|tRNA-Ser', i, re.I) else list_line[0]
        # 重复基因加一个note
        if flag:
            for i in self.dict_tbl[dict_key]:  # 删除其他note和transexcept注释
                if "note" in i:
                    self.dict_tbl[dict_key].remove(i)
            for i in self.dict_tbl[dict_key]:  # 前面删除过，所以要重新读
                if "transl_except" in i:
                    self.dict_tbl[dict_key].remove(i)
            self.dict_tbl[dict_key].append("\t\t\tnote\tduplicated")

    def str_table(self, table_dict):
        list_star = list(table_dict.keys())  # 将字典的键生成列表,是数字的列表
        list_star = sorted(list_star)  # 对字典的键排序
        previous = 0  # 定义上一个基因的stop
        # 这是用于生成gb文件的
        table = '''Gene\tPosition\t\tSize\tIntergenic nucleotides\tCodon\t\tAnti-codon
\tFrom\tTo\t\t\tStart\tStop\t\tStrand\tSequence\n'''
        # 生成表格用的table
        table_csv = table
        self.pro = ''
        self.PCGs_all = ">PCGs\n"
        self.allGenes = ["tRNA-His(gtg)", "tRNA-Gln(ttg)", "tRNA-Phe(gaa)", "tRNA-Met(cat)",
                         "tRNA-Val(tac)", "tRNA-Ala(tgc)", "tRNA-Asp(gtc)", "tRNA-Asn(gtt)",
                         "tRNA-Pro(tgg)", "tRNA-Ile(gat)", "tRNA-Lys(ctt)", "tRNA-Ser(gct)",
                         "tRNA-Trp(tca)", "tRNA-Thr(tgt)", "tRNA-Cys(gca)", "tRNA-Leu(tag)",
                         "tRNA-Ser(tga)", "tRNA-Leu(taa)", "tRNA-Glu(ttc)", "tRNA-Tyr(gta)",
                         "tRNA-Arg(tcg)", "tRNA-Gly(tcc)", "ATP6", "ATP8", "COX1", "COX2",
                         "COX3", "CYTB", "NAD1", "NAD2", "NAD3", "NAD4", "NAD5", "NAD4L",
                         "NAD6", "12S", "16S"]
        self.superfluousGene = []
        feature_tbl = '>Feature %s\n' % self.latin_name.replace(' ', '_')
        self.dict_tbl = OrderedDict()
        self.count_1st_item = 0  # 计算遇到多少个第一个item了,add_table函数里面
        gapCount = 0
        overlapCount = 0
        num = 60
        each = 30 / len(list_star)
        for j in list_star:
            list1 = table_dict[j].split('\t')
            name, size, seq = list1[0], list1[3], list1[4]
            start, stop = j, int(list1[2])
            if stop > previous:
                space = str(start - previous - 1)
                previous = stop  # 将previous赋值为该基因的stop位置
            else:  # 如果一个基因在另一个基因内部
                space = "0"
            if int(space) > 0:
                gapCount += 1
            if int(space) < 0:
                overlapCount += 1
            if space == '0':
                space = ''  # space = 0时，变为None
            new_name, ini, ter, inv_codon, sign, seq1, self.pro = self.TableReplace(
                name, size, seq, self.pro)
            flag, dupl, cleanName = self.if_duplicated(new_name)
            list_ = [new_name, str(start), str(
                stop), size, space, ini, ter, inv_codon, sign, seq1]
            # 用于生成SQN文件的
            self.forSqn("\t".join(list_), flag, cleanName)
            # 生成csv  table
            if cleanName.startswith("tRNA"):
                if re.match(r'tRNA-Leu|tRNA-Ser', cleanName, re.I):
                    csv_name = "trn" + self.ser_leu("", "\t".join(list_))[0]
                else:
                    csv_name = "trn" + self.dict_tRNA[cleanName]
            elif cleanName == "12S":
                csv_name = "rrnS"
            elif cleanName == "16S":
                csv_name = "rrnL"
            else:
                csv_name = cleanName
            list_[0] = csv_name
            table_csv += "\t".join(list_) + '\n'
            num += each
            self.dict_args["progressSig"].emit(num)
        list_feature_tbl = []
        for key in self.dict_tbl.keys():
            list_feature_tbl += self.dict_tbl[key]
        feature_tbl += "\n".join(list_feature_tbl)
        # 统计gap和重叠有多少个
        table_csv += "Gap:,%d,Overlap:%d\n" % (gapCount, overlapCount)
        return table_csv, feature_tbl

    def save_docx_as(self):
        import pythoncom
        pythoncom.CoInitialize()  # 多线程编程，必须加上这2句才能用win32com模块
        word = wc.Dispatch('Word.Application')
        doc = word.Documents.Open(self.usernota_file)
        sequence = re.sub(r'\[.+?\]|\n| |\t|\r', '', doc.Content.Text).upper()
        self.xml_11 = self.workPath + os.sep + "xml_11.xml"
        doc.SaveAs(self.xml_11, 11)
        doc.Close()
        return sequence

    def Replace(self, name):
        if name in list(self.dict_replace.keys()):
            new_name = self.dict_replace[name]
        else:
            new_name = name
        return new_name

    # def fetch_sequence(self):  # 得到全部序列
    #     docxfile = docx.Document(self.usernota_file)
    #     docxText = ""
    #     for para in docxfile.paragraphs:
    #         docxText += para.text.strip()
    #     docxText = re.sub(r'\[.+?\]|\n| |\t|\r', '', docxText)
    #     return docxText.upper()

    def fetch_name_seq(self):
        f = self.read_file(self.xml_11)
        content = f.read()
        f.close()
        rgx_content = re.compile(
            r'(<aml:annotation aml:id="(\d+)" w:type="Word\.Comment)\.Start"/>(.+)\1\.End"/><w:r.+\1(.+?)</aml:content></aml:annotation></w:r>', re.S | re.I)
        # group(2)是id，group(3)是文本内容，group(4)是注释内容
        rgx_text = re.compile(r"<w:t>(.+?)</w:t>", re.I | re.S)
        # fetch文本内容,包括comment的文本内容
        rgx_comment = re.compile(
            r'''<aml:annotation aml:id="\d+" w:type="Word.Comment".+?</aml:annotation>''', re.I | re.S)
        # 找出注释那部分的内容，如果嵌入文本内容内部，将其替换为空
        ini_pos = 0
        list_name_seq = []
        while rgx_content.search(content, ini_pos):
            match = rgx_content.search(content, ini_pos)
            text, comment, ini_pos = match.group(3), match.group(
                4), match.span()[0] + 56  # 要跳过start的位置必须加上56
            text = rgx_comment.sub("", text)  # 将其他ID的注释内容替换为空(有些ID的注释嵌入另一个的内部)
            sequence = "".join(rgx_text.findall(text))
            comment_text = "".join(
                rgx_text.findall(comment)).strip()  # 去掉前面单独的空格
            if re.match(r" *\- +", comment_text):  # 用户标记-号带空格的情况
                comment_text = re.sub(r" *\- +", "", comment_text)  # 把负号都替换掉
                comment_text = "-" + \
                    re.split(
                        r" +|\r+|\n+|\t+", comment_text)[0]  # 只保留空白字符前面的注释
            else:
                comment_text = re.split(
                    r" +|\r+|\n+|\t+", comment_text)[0]  # 只保留空白字符前面的注释
            sequence = re.sub(r'\n| |\t|\r', '', sequence)  # 去除了空格、换行符和用户信息等
            ##找到序列的起始位置
            text_before = content[:match.span(3)[0]] # Word.Comment.Start 之前的所有文本
            text_before = rgx_comment.sub("", text_before)  # 将其他ID的注释内容替换为空(有些ID的注释嵌入另一个的内部)
            sequence_before = "".join(rgx_text.findall(text_before))
            sequence_before = re.sub(r'\n| |\t|\r', '', sequence_before)
            seq_start = len(sequence_before) + 1
            list_name_seq.append((comment_text, sequence.upper(), seq_start))
        return list_name_seq

    def main_table(self):
        sequence = self.save_docx_as()  # 先将docx文件另存, 并得到序列
        # self.dict_args["progressSig"].emit(10)
        # sequence = self.fetch_sequence()  # 生成存序列
        self.dict_args["progressSig"].emit(10)
        list_name_seq = self.fetch_name_seq()
        self.dict_args["progressSig"].emit(30)
        table_dict = OrderedDict()
        start = 0
        num = 30
        each = 30 / len(list_name_seq)
        for i in list_name_seq:
            name, seq, start = i
            stop = start + len(seq) - 1
            name = self.Replace(name)
            size = str(len(seq))
            assert (seq in sequence), seq
            # rgx_span = re.compile(seq, re.I)
            # # 从上一个的起始位置开始搜索,必须先编译
            # span = rgx_span.search(sequence, int(start)).span()
            # start, stop = str(span[0] + 1), str(span[1])
            table_dict[start] = name + '\t' + str(start) + \
                '\t' + str(stop) + '\t' + size + '\t' + seq + '\n'
            num += each
            self.dict_args["progressSig"].emit(num)
        table_csv, feature_tbl = self.str_table(table_dict)
        return sequence, table_csv, feature_tbl


class ParseANNT(QDialog, Ui_parseANNT, Factory):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)

    def __init__(
            self,
            workPath=None,
            t2n_exe=None,
            inputDocxs=None,
            focusSig=None,
            parent=None):
        super(ParseANNT, self).__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.t2n_exe = '"' + t2n_exe + '"'
        self.inputDocxs = inputDocxs
        self.focusSig = focusSig
        # 保存设置
        self.parseANNT_settings = QSettings(
            self.thisPath +
            '/settings/parseANNT_settings.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.parseANNT_settings.setFallbacksEnabled(False)
        dict_data = self.parseANNT_settings.value(
            "extract listed gene")
        self.dict_tRNA_abbre = dict(dict_data["tRNA Abbreviation"])
        self.dict_product = dict(dict_data["Protein Gene Full Name"])
        self.dict_replace = dict(dict_data["Name From Word"])
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        # 信号槽
        self.exception_signal.connect(self.popupException)
        self.comboBox_5.lineEdit().setLineEditNoChange(True)
        self.comboBox_4.installEventFilter(self)
        self.comboBox_5.installEventFilter(self)
        # 恢复用户的设置
        self.guiRestore()
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-14-1-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-14-1-1-Brief-example"
        self.label_5.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        Slot documentation goes here.
        """
        fileNames = QFileDialog.getOpenFileNames(
            self,
            "Choose Word Files",
            filter="Word Documents(*.docx);;Word 97-2003 Documents(*.doc);;Word Macro-Enabled Documents(*.docm);;"
                   "Word Template(*.dotx);;Word 97-2003 Template(*.dot);;Word Macro-Enabled Template(*.dotm);;"
                   "OpenDocument Text(*.odt);;")
        if fileNames[0]:
            self.inputDocx(self.comboBox_4, fileNames[0])

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        """
        Slot documentation goes here.
        """
        fileName = QFileDialog.getOpenFileName(self, "Choose Template File")
        if fileName[0]:
            self.inputDocx(self.comboBox_5, [fileName[0]])

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        Slot documentation goes here.
        """
        self.dict_args = {}
        self.dict_args["t2n"] = self.t2n_exe
        self.dict_args["workPath"] = self.workPath
        self.dict_args["files"] = self.comboBox_4.fetchListsText()
        if not self.dict_args["files"]:
            QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Please input Word file(s) first</p>")
            return
        self.dict_args["temp"] = self.comboBox_5.fetchCurrentText()
        ####
        self.dict_args["dict_tRNA"] = self.dict_tRNA_abbre
        self.dict_args["dict_product"] = self.dict_product
        self.dict_args["dict_replace"] = self.dict_replace
        self.dict_args["name"] = self.lineEdit.text().strip()
        if not self.dict_args["name"]:
            QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Organism name is needed!</p>")
            self.lineEdit.setFocus()
            return
        self.dict_args["codon"] = str(
            self.comboBox_9.currentText()).split(" ")[0]
        self.dict_args["complete"] = str(
            self.comboBox.currentText()).split(" ")[0]
        self.dict_args["strain"] = self.lineEdit_2.text().strip()
        self.dict_args["isolate"] = self.lineEdit_3.text().strip()
        self.dict_args["synonym"] = self.lineEdit_4.text().strip()
        self.dict_args["host"] = self.lineEdit_7.text().strip()
        self.dict_args["country"] = self.lineEdit_8.text().strip()
        self.dict_args["others"] = self.lineEdit_5.text().strip()
        self.dict_args["lineage"] = self.stripName(self.lineEdit_6.text()).replace(";", "; ")
        tuple_date = self.releaseDate() #"2018", "4", "3"
        sort_date = [tuple_date[1], tuple_date[2], tuple_date[0]]
        self.dict_args[
            "release_date"] = "/".join(sort_date) #07/27/2017
        self.dict_args["progressSig"] = self.progressSig
        self.dict_args["file"] = self.dict_args["files"][0]
        base = os.path.splitext(os.path.basename(self.dict_args["file"]))[0]
        self.dict_args["exportPath"] = self.factory.creat_dirs(
            self.workPath + os.sep + base + "_parseANNT_results")
        ok = self.factory.remove_dir(self.dict_args["exportPath"], parent=self)
        if not ok:
            # 提醒是否删除旧结果，如果用户取消，就不执行
            return
        self.worker = WorkThread(self.run_command, parent=self)
        self.worker.start()
        # if self.dict_args["files"]:
        #     for i in self.dict_args["files"]:
        #         base = os.path.basename(i)
        #         self.dict_args["exportPath"] = self.factory.creat_dirs(
        #             self.workPath + os.sep + base + "_parseANNT_results")
        #         self.dict_args["file"] = i
        #         self.worker = WorkThread(self.run_command, parent=self)
        #         self.worker.start()
        # else:
        #     QMessageBox.critical(
        #         self,
        #         "No input file",
        #         "<p style='line-height:25px; height:25px'>Please input file(s) first!</p>",
        #         QMessageBox.Ok)

    @pyqtSlot()
    def on_toolButton_clicked(self):
        setting = ParANNT_settings(self)
        # 隐藏？按钮
        setting.setWindowFlags(setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        setting.exec_()

    def inputDocx(self, combobox, fileNames):
        try:
            list_new_inputs = []
            if fileNames:
                flag = False
                rgx_path = re.compile(r'[^\w_.)(-:\\]')
                rgx_name = re.compile(r'[^\w_.)(-]')
                for num, i in enumerate(fileNames):
                    if os.path.exists(i):
                        dir = os.path.dirname(i)
                        if rgx_path.search(dir):
                            QMessageBox.warning(
                                self,
                                "Parse Annotation",
                                "<p style='line-height:25px; height:25px'>Invalid symbol found in file path, please copy the file to desktop and try again!</p>")
                            continue
                        base = os.path.basename(i)
                        if rgx_name.search(base):
                            base = rgx_name.sub("_", base)
                            flag = True
                        os.rename(i, dir + os.sep + base)
                        list_new_inputs.append(dir + os.sep + base)
                if flag:
                    QMessageBox.information(
                        self,
                        "Parse Annotation",
                        "<p style='line-height:25px; height:25px'>Invalid symbol found in file name, replacing it with '_'!</p>")
            combobox.refreshInputs(list_new_inputs)
        except:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号

    def run_command(self):
        try:
            # 先清空文件夹
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "start",
                    self.dict_args["exportPath"],
                    self.qss_file,
                    self])
            parseANNT = Parse_annotation(**self.dict_args)
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "stop",
                    self.dict_args["exportPath"],
                    self.qss_file,
                    self])
            self.focusSig.emit(self.dict_args["exportPath"])
            time_end = datetime.datetime.now()
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                  str(time_end - time_start))
            with open(self.dict_args["exportPath"] + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write("If you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n\n" + self.time_used_des)
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

    def releaseDate(self):
        text = self.dateEdit.text() #2018/4/3
        return text.split("/")

    def popupException(self, exception):
        rgx = re.compile(r'Permission.+?[\'\"](.+\.(csv|docx|doc|odt|docm|dotx|dotm|dot))[\'\"]')
        # rgxDocx = re.compile(r'Permission.+?[\'\"](.+?\.docx)[\'\"]')
        if rgx.search(exception):
            csvfile = rgx.search(exception).group(1)
            reply = QMessageBox.critical(
                self,
                "Parse Annotation",
                "<p style='line-height:25px; height:25px'>Please close '%s' file first!</p>"%os.path.basename(csvfile),
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                os.startfile(csvfile)
        # elif rgxDocx.search(exception):
        #     docxfile = rgxDocx.search(exception).group(1)
        #     reply = QMessageBox.critical(
        #         self,
        #         "Parse Annotation",
        #         "<p style='line-height:25px; height:25px'>Please close 'docx' file first!</p>",
        #         QMessageBox.Yes,
        #         QMessageBox.Cancel)
        #     if reply == QMessageBox.Yes:
        #         os.startfile(docxfile)
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(
                'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
            msg.setWindowTitle("Error")
            msg.setDetailedText(exception)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def eventFilter(self, obj, event):
        name = obj.objectName()
        if isinstance(obj, QComboBox):
            if name in ["comboBox_4", "comboBox_5"]:
                if (event.type() == QEvent.DragEnter):
                    if event.mimeData().hasUrls():
                        # must accept the dragEnterEvent or else the dropEvent
                        # can't occur !!!
                        event.accept()
                        return True
                if (event.type() == QEvent.Drop):
                    files = [u.toLocalFile() for u in event.mimeData().urls()]
                    self.inputDocx(obj, files)
        return super(ParseANNT, self).eventFilter(obj, event)  # 0

    def guiSave(self):
        # Save geometry
        self.parseANNT_settings.setValue('size', self.size())
        # self.parseANNT_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                if name in ["comboBox_4", "comboBox_5"]:
                    values = obj.fetchListsText()
                    self.parseANNT_settings.setValue(name, values)
                else:
                    text = obj.currentText()
                    if text:
                        allItems = [
                            obj.itemText(i) for i in range(obj.count())]
                        allItems.remove(text)
                        sortItems = [text] + allItems
                        self.parseANNT_settings.setValue(name, sortItems)
            if isinstance(obj, QLineEdit):
                text = obj.text()
                self.parseANNT_settings.setValue(name, text)
            if isinstance(obj, QDateEdit):
                year, month, day = self.releaseDate()
                self.parseANNT_settings.setValue(name, (year, month, day))

    def guiRestore(self):

        # Restore geometry
        size = self.factory.judgeWindowSize(self.parseANNT_settings, 712, 515)
        self.resize(size)
        self.factory.centerWindow(self)
        # self.move(self.parseANNT_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox_4":
                    if self.inputDocxs:
                        self.inputDocx(obj, self.inputDocxs)
                    else:
                        values = self.parseANNT_settings.value(name, [])
                        self.inputDocx(obj, values)
                elif name == "comboBox_5":
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    values = self.parseANNT_settings.value(name, allItems)
                    self.inputDocx(obj, values)
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    values = self.parseANNT_settings.value(name, allItems)
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

            if isinstance(obj, QLineEdit):
                value = self.parseANNT_settings.value(
                    name, "")  # get stored value from registry
                obj.setText(value)  # restore checkbox
            if isinstance(obj, QDateEdit):
                year, month, day = self.parseANNT_settings.value(
                    name, ("2018", "4", "3"))
                obj.setDate(QDate(int(year), int(month), int(day)))

        return False

    def runProgress(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def closeEvent(self, event):
        self.guiSave()

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        Cancel
        """
        self.close()

    def stripName(self, name):
        return re.sub(r"\s", "", name)

    # def resizeEvent(self, event):
    #     self.comboBox_4.view().setMaximumWidth(self.comboBox_4.width())
    #     self.comboBox_5.view().setMaximumWidth(self.comboBox_5.width())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    PhyloSuite = ParseANNT()
    PhyloSuite.show()
    sys.exit(app.exec_())
