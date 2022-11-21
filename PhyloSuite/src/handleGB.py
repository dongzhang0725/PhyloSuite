#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import csv
import glob
import itertools

import datetime
import pickle
import subprocess
import time
import uuid
from io import StringIO
from multiprocessing import Pool, Queue, Manager
# 解决有时候一直卡着的问题
from multiprocessing import set_start_method, get_context
# set_start_method("spawn", force=True)

from Bio import SeqIO, Entrez, SeqFeature, AlignIO
from Bio.Alphabet import generic_dna
from Bio.Phylo.TreeConstruction import DistanceCalculator

from src.Lg_mafft import CodonAlign
from src.factory import Convertfmt, Factory, SeqGrab
import re
import os
import traceback
import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from collections import OrderedDict, Counter
import random
from src.rscuSum import RSCUsum
from src.rscuStack import RSCUstack
from Bio.Seq import _translate_str, Seq
from Bio.Data import CodonTable
from suds.client import Client
from Bio.SeqFeature import FeatureLocation, CompoundLocation
from ete3 import NCBITaxa
import platform

'''item:
[
['source', '1..402', {'organelle': 'mitochondrion', 'host': 'Bathybates minor', 'country': 'Burundi: Lake Tanganyika,Bujumbura', 'db_xref': 'taxon:1844966', 'mol_type': 'genomic DNA', 'organism': 'Cichlidogyrus casuarinus', 'isolate': 'PB3'}],
 ['gene', '<1..>402', {'gene': 'COX1'}],
 ['CDS', '<1..>402', {'gene': 'COX1', 'codon_start': '1', 'transl_table': '9', 'protein_id': 'ANC98956.1', 'translation': 'FFGHPEVYVLILPGFGAVSHICLSISNNQEPFGYLGLVFAMFSIVCLGCVVWAHHMFTVGMDVKSTIFFSSVTMIIGVPTGIKVFSWLYMLASSNISRGDPIVWWVFAFIILFTMGGVTGIVLSSSVLDSLLHD', 'product': 'cytochrome c oxidase subunit I'}]
 ]'''

class LabelNCR(object):

    def __init__(self):
        pass

    def exec_(self, gbContent, intergene_length, totalID, base, process, progressSignal):
        newContent = ""
        for gb_record in SeqIO.parse(StringIO(gbContent), "genbank"):
            features = gb_record.features
            features = self.remove_join_associated_feature(features)
            sequence = gb_record.seq
            record_length = len(sequence)
            new_features = []
            reach_first_feature = False
            for num, this_feature in enumerate(features):
                if this_feature.type in ["source"]:
                    new_features.append(this_feature)
                    continue
                before_feature = features[num - 1]
                if str(this_feature.location) == str(before_feature.location):
                    # 上面是gene，下面是CDS的情况
                    new_features.append(this_feature)
                    continue
                this_start = self.get_start(this_feature)
                if not reach_first_feature:
                    # 第一个feature，在这个位置把开始和最后都以join的情况给考虑了？最后有join的情况可能得单独考虑
                    last_feature = features[-1]
                    last_end = self.get_end(last_feature)
                    # print(this_start, last_end)
                    ## 必须加上下面的条件判断，否则     gene            complement(join(15133..15415,1..11))会搞错
                    if this_feature.location_operator != "join":
                        # 如果不是join，那么肯定是从小数字开始的，而最后个feature的索引肯定大，所以是跨环
                        new_features = self.location_cross_circle(record_length,
                                                             intergene_length,
                                                             this_start,
                                                             last_end,
                                                             new_features,
                                                             features)
                    else:
                        # 如果是join，除了在下面单独判断join外，还要判断join的起始位置与上一个feature的结束位置
                        if this_start > last_end:
                            if (this_start - last_end) >= intergene_length:
                                my_feature_location = SeqFeature.FeatureLocation(last_end, this_start, strand=+1)
                                my_feature = SeqFeature.SeqFeature(my_feature_location,
                                                                   type="misc_feature",
                                                                   qualifiers={"gene": "NCR",
                                                                               "note": "Added by PhyloSuite"})
                                if not self.feature_existed(my_feature, new_features): new_features.append(my_feature)
                        else:
                            # 证明是cross circle的情况
                            new_features = self.location_cross_circle(record_length,
                                                                 intergene_length,
                                                                 this_start,
                                                                 last_end,
                                                                 new_features,
                                                                 features)
                    reach_first_feature = True
                else:
                    if (this_start - last_end) >= intergene_length:
                        my_feature_location = SeqFeature.FeatureLocation(last_end, this_start, strand=+1)
                        my_feature = SeqFeature.SeqFeature(my_feature_location,
                                                           type="misc_feature",
                                                           qualifiers={"gene": "NCR",
                                                                       "note": "Added by PhyloSuite"})
                        if not self.feature_existed(my_feature, new_features): new_features.append(my_feature)
                ## 处理 this_feature 有join的情况
                if this_feature.location_operator == "join":
                    if re.search(r"\[(\d+):(\d+)\]", str(this_feature.location)):
                        list_index = re.findall(r"\[(\d+):(\d+)\]", str(this_feature.location))
                        list_index = list_index if this_feature.strand == 1 else list(reversed(list_index))
                        # 这里的list_index要反转一下吗
                        for num1, tuple_index in enumerate(list_index):
                            if (num1 + 1) < len(list_index):
                                gap_start = int(tuple_index[1])
                                gap_end = int(list_index[num1 + 1][0])
                                if gap_end < gap_start:
                                    # 证明是跨环的情况 {[1301:20896](+), [0:4](+)}。改为它们之间的差距比整个基因组还大？ 会不会也被overlap影响？
                                    new_features = self.location_cross_circle(record_length,
                                                                         intergene_length,
                                                                         gap_end,
                                                                         gap_start,
                                                                         new_features,
                                                                         features,
                                                                         join=True)
                                else:
                                    if (gap_end - gap_start) >= intergene_length:
                                        my_feature_location = SeqFeature.FeatureLocation(gap_start, gap_end,
                                                                                         strand=+1)
                                        if my_feature_location not in [feat.location for feat in features]:
                                            # 有时候已经添加过这个feature了，但是还是重复判定了
                                            my_feature = SeqFeature.SeqFeature(my_feature_location,
                                                                               type="misc_feature",
                                                                               qualifiers={"gene": "NCR",
                                                                                           "note": "Added by PhyloSuite",
                                                                                           "note2": "join associated"})
                                            if not self.feature_existed(my_feature, new_features): new_features.append(
                                                my_feature)
                new_features.append(this_feature)
                last_end = self.get_end(this_feature)
            gb_record.features = new_features
            newContent += gb_record.format("genbank")
            num += 1
            progressSignal.emit(
                base + (num / totalID) * process)
        return newContent

    def remove_join_associated_feature(self, features):
        ## 删除join的feature
        new_features = []
        for feat in features:
            if "note2" in feat.qualifiers:
                if (type(feat.qualifiers["note2"]) != str and feat.qualifiers["note2"][0] == "join associated") or \
                        (type(feat.qualifiers["note2"]) == str and feat.qualifiers["note2"] == "join associated"):
                    continue
            else:
                new_features.append(feat)
        index_not_include = []
        ## 删除起始位置的那个misc_feature，
        for num, feature in enumerate(new_features):
            if feature.type == "misc_feature":
                if "note" in feature.qualifiers:
                    if (type(feature.qualifiers["note"]) != str and feature.qualifiers["note"][
                        0] == "Added by PhyloSuite") or \
                            (type(feature.qualifiers["note"]) == str and feature.qualifiers[
                                "note"] == "Added by PhyloSuite"):
                        index_not_include.append(num)
            if feature.type not in ["misc_feature", "source"]: break
        new_features = [feature for index, feature in enumerate(new_features) if index not in index_not_include]
        ## 删除最后的那个misc_feature，
        index_not_include = []
        for num, feature in enumerate(reversed(features)):
            if feature.type == "misc_feature":
                if "note" in feature.qualifiers:
                    if (type(feature.qualifiers["note"]) != str and feature.qualifiers["note"][
                        0] == "Added by PhyloSuite") or \
                            (type(feature.qualifiers["note"]) == str and feature.qualifiers[
                                "note"] == "Added by PhyloSuite"):
                        index_not_include.append(len(features) - num)
            if feature.type != "misc_feature": break
        new_features = [feature for index, feature in enumerate(new_features) if index not in index_not_include]
        return new_features

    def get_start(self, this_feature):
        if this_feature.location_operator == "join":
            if re.search(r"\[(\d+):(\d+)\]", str(this_feature.location)):
                list_index = re.findall(r"\[(\d+):(\d+)\]", str(this_feature.location))
                list_index = list_index if this_feature.strand == 1 else list(reversed(list_index))
                this_start = int(list_index[0][0])
            else:
                this_start = this_feature.location.start
        else:
            this_start = this_feature.location.start
        return this_start

    def get_end(self, this_feature):
        if this_feature.location_operator == "join":
            if re.search(r"\[(\d+):(\d+)\]", str(this_feature.location)):
                list_index = re.findall(r"\[(\d+):(\d+)\]", str(this_feature.location))
                list_index = list_index if this_feature.strand == 1 else list(reversed(list_index))
                end = int(list_index[-1][1])
            else:
                end = this_feature.location.end
        else:
            end = this_feature.location.end
        return end

    def feature_existed(self, feature, features):
        flag = False
        if "note" in feature.qualifiers:
            if (type(feature.qualifiers["note"]) != str and feature.qualifiers["note"][0] == "Added by PhyloSuite") or \
                    (type(feature.qualifiers["note"]) == str and feature.qualifiers["note"] == "Added by PhyloSuite"):
                for feat in features:
                    if str(feat.location) == str(feature.location):
                        flag = True
        return flag

    def not_include_any_features(self, tested_feature, features):
        ## 有时候得到这种错误的 misc_feature    join(15140..15415,1..15132)。NCR不应该包含任何feature
        flag = True
        for feature in features:
            if set(list(feature.location)).issubset(set(list(tested_feature.location))):
                flag = False
                break
        return flag

    def location_cross_circle(self, record_length,
                                  intergene_length,
                                  this_start,
                                  last_end,
                                  new_features,
                                  features,
                                  join=False):
        if (record_length - last_end) + this_start >= intergene_length:
            init_location = SeqFeature.FeatureLocation(0, this_start, strand=+1) if this_start > 0 else None
            end_location = SeqFeature.FeatureLocation(last_end, record_length,
                                                      strand=+1) if last_end < record_length else None
            qualifier = {"gene": "NCR", "note": "Added by PhyloSuite"} if not join else {"gene": "NCR",
                                                                                         "note": "Added by PhyloSuite",
                                                                                         "note2": "join associated"}
            if init_location and end_location:
                my_feature_location = SeqFeature.CompoundLocation([end_location, init_location])
                my_feature = SeqFeature.SeqFeature(my_feature_location,
                                                   type="misc_feature",
                                                   qualifiers=qualifier)
                if (not self.feature_existed(my_feature, new_features)) and \
                        self.not_include_any_features(my_feature, features): new_features.append(my_feature)
            elif init_location:
                my_feature_location = init_location
                my_feature = SeqFeature.SeqFeature(my_feature_location,
                                                   type="misc_feature",
                                                   qualifiers=qualifier)
                if (not self.feature_existed(my_feature, new_features)) and \
                        self.not_include_any_features(my_feature, features): new_features.append(my_feature)
            elif end_location:
                my_feature_location = end_location
                my_feature = SeqFeature.SeqFeature(my_feature_location,
                                                   type="misc_feature",
                                                   qualifiers=qualifier)
                if (not self.feature_existed(my_feature, new_features)) and \
                        self.not_include_any_features(my_feature, features): new_features.append(my_feature)
        return new_features  # , my_last_feature



class Normalize_MT(Factory):
    '''当有序列完全一样的，如果有errors,虽然加了2个，但是只能定位到第一个'''

    def __init__(self, **dict_args):
        self.factory = Factory()
        self.dict_args = dict_args
        self.included_features = self.dict_args["Features to be extracted"]
        self.included_features = "All" if self.dict_args["extract_all_features"] else self.included_features
        self.dict_replace = {i[0]: i[1] for i in self.dict_args["Names unification"]}
        self.MarkNCR = self.dict_args["MarkNCR"] if "MarkNCR" in self.dict_args else False
        self.ncrLenth = self.dict_args["ncrLenth"] if "ncrLenth" in self.dict_args else 200
        # [item, description]
        self.errors = []
        self.warnings = []
        self.no_annotation_IDs = []
        self.no_annotation_GBs = []
        self.totalID = self.dict_args["totalID"]
        self.progressSignal = self.dict_args["progressSig"]
        if self.MarkNCR:
            self.lableNCR = LabelNCR()
            gbContents = self.lableNCR.exec_(self.dict_args["gbContents"], self.ncrLenth,
                                             self.totalID, 10, 30, self.progressSignal)
        else: gbContents = self.dict_args["gbContents"]
        gbManager = GbManager(self.dict_args["outpath"])
        fileHandle = StringIO(gbContents)
        try:
            line = fileHandle.readline()
            error_inf = ''
            self.unRecognisetRNA = ""
            while not line.startswith('LOCUS'):
                line = fileHandle.readline()
            sequences = ''
            num = 0  # 进度条
            while line != '':
                while not line.startswith('//') and line != '':
                    self.list_tRNA_index = []
                    individual_gb = line
                    self.gb_num = self.get_ids(fileHandle, line)
                    individual_gb, latin, line = self.get_latin(
                        individual_gb, fileHandle, line)  ##这一步获得ID，补足gb_num
                    while not line.startswith('FEATURES'):
                        line = fileHandle.readline()
                        individual_gb += line
                    individual_gb, line, value, genome_size = self.source(
                        individual_gb, line, fileHandle)
                    latin = latin + value.replace(' ', '_')
                    individual_gb, line, error_inf, found_no_annotation = self.get_item(
                        individual_gb, fileHandle, line, error_inf, genome_size)
                    individual_gb, line, self.seq = self.get_sequence(
                        individual_gb, fileHandle, line)
                    # # 替换掉<和>,不然html会出错
                    # individual_gb = re.sub(
                    #     r"<(?!span|/span)", "&lt;", individual_gb)
                    # individual_gb = re.sub(
                    #     r"(?<=\d)>", "&gt;", individual_gb)
                    if found_no_annotation:
                        gb = SeqIO.read(StringIO(individual_gb), "genbank")
                        self.no_annotation_IDs.append(gb.id)
                        self.no_annotation_GBs.append(individual_gb)
                    sequences += individual_gb
                    gb_path = gbManager.fetchRecordPath(self.ID)
                    # 得到纯文本
                    # Dialog = QDialog()
                    # textBrowser = QTextBrowser(Dialog)
                    # textBrowser.setHtml("<pre>" + individual_gb + "</pre>")
                    plainContent = individual_gb # textBrowser.toPlainText()
                    with open(gb_path, 'w', encoding="utf-8") as f1:
                        f1.write(plainContent)
                    # 生成为识别的tRNA
                    if self.list_tRNA_index:
                        for i in self.list_tRNA_index:
                            tRNA_seq = self.index2seq(i)
                            name = ">" + \
                                   self.factory.refineName(
                                       "_".join([latin, self.gb_num, i])) + "\n"
                            self.unRecognisetRNA += name + tRNA_seq + "\n"
                    num += 1
                    self.progressSignal.emit(
                        40 + (num / self.totalID) * 60)
                # 保证读到下个物种的gb文件
                while not line.startswith('LOCUS') and line != '':
                    line = fileHandle.readline()
            self.allContent = sequences
            # '''<html>
            #                     <head>
            #                     <title>genbankfile</title>
            #                     <style type=text/css>
            #                     .error {color: red}
            #                     .warning {color: blue}
            #                     </style>
            #                     </head>
            #
            #                     <body bgcolor=#f5f5a3>
            #                     <pre>''' + sequences + '''</pre>
            #                     </body>
            #                     </html>'''
        except BaseException:
            if "exception_signal" in self.dict_args:
                self.dict_args["exception_signal"].emit(''.join(
                traceback.format_exception(*sys.exc_info())) + "\n")
            print(''.join(
                traceback.format_exception(*sys.exc_info())) + "\n")

    def is_feature_start(self, line):
        return line and line[5] != ' '# and line.startswith(" ")

    def is_attribute_start(self, line):
        attribute_prefix = 21 * ' ' + '/'
        return line and line.startswith(attribute_prefix)

    def source(self, individual_gb, line, f):
        line = f.readline()
        assert line.startswith('     source'), line
        # ['', '', '', '', '', 'source', '', '', '', '', '', '', '', '', '', '1..13709']
        genome_size = re.split(r"[^\d]", line.strip().split(" ")[-1])[-1]
        individual_gb += line
        line = f.readline()
        while not self.is_feature_start(line):
            individual_gb += line
            value = '_' + line.strip()[1:].split('=')[1].strip('"') if 'isolate' in line else ''
            line = f.readline()
        return individual_gb, line, value, genome_size

    def get_value(self, feature_content, f, line, value):
        attribute_prefix = 21 * ' ' + '/'
        feature_content += line
        line = f.readline()
        while (not line.startswith(attribute_prefix)
               and not self.is_feature_start(line)):
            feature_content += line
            value += line.strip()
            line = f.readline()
        fullvalue = value.strip('"')
        return fullvalue, line, feature_content

    def read_feature(self, f, line, feature_content):
        feature_content += line
        feature = line.split()
        # 预防join有换行的情况join(249619..249850,250264..250414,250807..250956,\n251109..2
        while True:
            line = f.readline()  # 先向下读一行
            if line.startswith("ORIGIN") and line.startswith('BASE'):
                feature_content += line
                break
            # 有时候一个feature下面紧接着另一个feature
            elif not self.is_feature_start(line) and not self.is_attribute_start(line):
                feature[1] += line.strip()
                feature_content += line
            else:
                break
        assert feature
        # 避免 3'UTR           1327..1654\nORIGIN
        if not line.startswith("ORIGIN") and not line.startswith('BASE'):
            props = {}
            while not self.is_feature_start(line):
                try:
                    assert 2 == len(line.split('=')), line.split('=')
                    key, value = line.strip()[1:].split('=')
                    fullvalue, line, feature_content = self.get_value(
                        feature_content, f, line, value)
                    props[key] = fullvalue
                except AssertionError:  # 这里必须向下读一行，否则陷入死循环！！！
                    line = f.readline()
                    while (not self.is_attribute_start(line)
                           and not self.is_feature_start(line)):
                        line = f.readline()
            feature.append(props)
        return feature, line, feature_content

    def next_item(self, f, line):
        while not line.startswith('ORIGIN') and not line.startswith('BASE') and not line.startswith('CONTIG'):
            assert self.is_feature_start(line), line
            feature_content = ''
            feature, line, feature_content = self.read_feature(
                f, line, feature_content)
            yield feature, feature_content, line

    def replace(self, old_name):
        if old_name in self.dict_replace:
            old_name = self.dict_replace[old_name]
        match = re.match(
            r'COX[1-3]|NAD4L|NAD[1-6]|ND[1-6]|COB|CYTB|ATP[68]',
            old_name,
            re.IGNORECASE)
        old_name = old_name.lower() if match else old_name
        old_name = "nad4L" if old_name == "nad4l" else old_name
        old_name = "rrnS" if old_name == "12S" else old_name
        old_name = "rrnL" if old_name == "16S" else old_name
        return old_name

    def judge(self, new_name, values, error_inf):
        haveWarning = False
        if new_name == 'L' or new_name == 'S':
            if re.search(
                    r'(?<=[^1-9a-z_])(CUA|CUN|[tu]ag|L1|trnL1|Leu1)(?=[^1-9a-z_])',
                    values,
                    re.I):
                new_name = 'L1'
            elif re.search(r'(?<=[^1-9a-z_])(UUA|UUR|[tu]aa|L2|trnL2|Leu2)(?=[^1-9a-z_])', values, re.I):
                new_name = 'L2'
            elif re.search(r'(?<=[^1-9a-z_])(UCA|UCN|[tu]ga|S2|trnS2|Ser2)(?=[^1-9a-z_])', values, re.I):
                new_name = 'S2'
            elif re.search(r'(?<=[^1-9a-z_])(AGC|AGN|AGY|gc[tu]|[tu]c[tu]|S1|trnS1|Ser1)(?=[^1-9a-z_])', values, re.I):
                new_name = 'S1'
            else:
                # complement(14859..14922)
                position = values.split('\n')[0].split()[1]
                self.list_tRNA_index.append(position)
                error_inf += 'Ambiguous annotation about S1, S2, L1 and L2 in %s for %s\n' % (
                    position, self.gb_num)
                haveWarning = True
        else:
            new_name = new_name
        return new_name, error_inf, haveWarning

    def get_item(
            self,
            individual_gb,
            f,
            line,
            error_inf,
            genome_size):
        generator_item = self.next_item(f, line)
        found_no_annotation = False
        try:
            feature, feature_content, line = next(generator_item)
        except StopIteration:
            ##没有注释的情况，直接到Origin了
            self.errors.append(
                [individual_gb, "No features found, better to remove it"])
            ##"LOCUS%s" % (" " * 7 + self.gb_num)
            # individual_gb = '<span class="error">' + \
            #                 individual_gb + '</span>'
            found_no_annotation = True
            return individual_gb, line, error_inf, found_no_annotation
        included_features = [i.upper() for i in self.included_features]
        while True:
            try:
                feature_type = feature[0] if self.included_features != "All" else "all"
                has_qualifier = False
                haveWarning = False
                if self.included_features == "All" or (feature_type.upper() in included_features): # [tRNA, rRNA, CDS]
                    absent_qualifier = True if len(feature) < 3 else False #有时候根本没有qualifier  ['misc_feature', 'complement(15280..15387)']
                    if not absent_qualifier:
                        qualifiers = feature[2]
                        included_qualifiers = self.dict_args["Qualifiers to be recognized (%s):" % feature_type]
                        for qualifier in included_qualifiers:  # [gene, product]
                            if qualifier in qualifiers:
                                has_qualifier = True
                                ##先把该qualifier的名字替换了
                                old_name = qualifiers[qualifier]
                                new_name = self.replace(old_name)
                                ## 开始判断tRNA
                                if feature[0].upper() == "TRNA":
                                    new_name, error_inf, haveWarning = self.judge(
                                        new_name, feature_content, error_inf)
                                if old_name != new_name:
                                    try:
                                        rgx_text = r"(/%s\s*=\s*\")[^\"]+?\"(?=\n)" % qualifier
                                        new_text = re.search(rgx_text, feature_content).group(1) + new_name + '"'
                                        feature_content = re.sub(rgx_text, new_text, feature_content) ##替换新名字
                                    except:
                                        print(rgx_text)
                                        print(feature_content)
                    if not has_qualifier or absent_qualifier:
                        # no recognization indentifier
                        individual_gb += feature_content
                                        # '<span class="error">' + \
                                        #  feature_content + '</span>'
                        self.errors.append(
                            [feature_content, "No identifiers (%s) for this gene"%", ".join(included_qualifiers)])
                    else:
                        # +=替换了名字的qualifier
                        if haveWarning:
                            ##tRNA模式，并且S和L都没有注释好
                            individual_gb += feature_content # '<span class="warning">' + feature_content + '</span>'
                            self.warnings.append([feature_content, "Ambiguous annotation of S1/S2 or L1/L2"])
                        else:
                            individual_gb += feature_content
                else:
                    ##feature_type没有包含
                    individual_gb += feature_content
                # last_feature = feature
                feature, feature_content, line = next(generator_item)
                # if self.MarkNCR:
                #     # print(last_feature, feature, feature_content, line)
                #     last_ter = self.position(last_feature[1])[1]
                #     now_ini = self.position(feature[1])[0]
                #     if last_ter and now_ini:
                #         # 这里上一个序号要+1才能拿来判断
                #         if (int(now_ini) - (int(last_ter) + 1)) >= self.ncrLenth:
                #             individual_gb += 'misc_feature'.ljust(16).rjust(21) + str(int(
                #                 last_ter) + 1) + '..' + str(int(now_ini) - 1) + '\n' + 21 * ' ' + '/gene="NCR"\n'
            except StopIteration:
                # if self.MarkNCR:
                #     last_ter = self.position(feature[1])[1]  # 判断最后一部分序列是否为NCR
                #     now_ini = genome_size
                #     if last_ter and now_ini:
                #         if (int(now_ini) - int(last_ter)) >= self.ncrLenth:
                #             individual_gb += 'misc_feature'.ljust(16).rjust(21) + str(
                #                 int(last_ter) + 1) + '..' + str(int(now_ini)) + '\n' + 21 * ' ' + '/gene="NCR"\n'
                break
        return individual_gb, line, error_inf, found_no_annotation

    def position(self, subject):
        list1 = re.findall(r'[0-9]+', subject)
        if 'join' in subject:
            ini = list1[0]
            if len(list1) > 3:
                ter = list1[3]
            else:
                ter = list1[2]
        elif "order" in subject:
            ini = list1[0]
            ter = list1[-1]
        elif len(list1) == 1:  # 当只有1个位置时，需要这个来过滤
            ini = list1[0]
            ter = list1[0]
        elif len(list1) == 0:
            print(subject)
            return None, None
        else:
            ini, ter = list1
        return ini.strip('<'), ter

    def get_sequence(self, individual_gb, f, line):
        individual_gb += line
        seq = ''
        while not re.search(r'[atcg]{10}', line) and not line.startswith('//'):
            line = f.readline()
            individual_gb += line
        if line.startswith('//'):
            ##有可能出现根本没有序列的情况，直接就是//
            return individual_gb + '\n', line, ""
        seq += line[10:-1].replace(' ', '')
        while not line.startswith('//'):
            line = f.readline()
            seq += line[10:-1].replace(' ', '')
            individual_gb += line
        return individual_gb + '\n', line, seq

    def get_ids(self, src, line):
        while not line.startswith('LOCUS'):
            line = src.readline()
        self.gb_num = line.split()[1]
        assert self.gb_num != '', self.gb_num
        return self.gb_num

    def get_latin(self, individual_gb, src, line):
        while not line.startswith('  ORGANISM'):
            line = src.readline()
            individual_gb += line
        rgx_version = re.compile(r"(?sm)LOCUS {7}(\S+).+?^VERSION {5}(\S+)")  ##version识别ID
        self.ID = rgx_version.search(individual_gb).group(2) if rgx_version.search(individual_gb) else self.gb_num
        try:
            name = re.search(r'  ORGANISM  (.+)\n', line).group(1)
        except:
            #有些ORGANISM  是一片空白
            name = "NA"
        return individual_gb, name.replace(' ', '_'), line

    def afterTransExcept(self):
        pass

    def index2seq(self, position, transExcpt=False):
        list1 = re.findall(r'[0-9]+', position)
        ini, ter = list1[0], list1[1]
        assert ini.isdigit() and ter.isdigit(), ini
        start, stop = int(ini) - 1, int(ter)

        # 处理join有多个位点的情况
        def muti_join(list1, codon_start=False, complement=False):
            if len(list1) % 2 != 0:  # 提示有这种join情况order(16599,1..1535)
                content = re.search(r"\w+\((.+)\)", position).group(1)
                list_ = content.split(",")
                list1 = []
                for i in list_:
                    list1_ = i.split("..")
                    if len(list1_) > 1:
                        list1 += list1_
                    else:
                        list1 += list1_ + list1_
            seq = ""
            if complement:
                if codon_start:
                    last = self.seq[
                           int(list1[-2]) - 1:int(list1[-1]) - codon_start + 1]
                    for num, i in enumerate(list1[:-2]):
                        if (num + 1) % 2 != 0:  # 奇数
                            start = int(i)
                        else:
                            seq += self.seq[start - 1:int(i)]
                    seq += last
                else:
                    last = self.seq[int(list1[-2]) - 1:int(list1[-1])]
                    for num, i in enumerate(list1[:-2]):
                        if (num + 1) % 2 != 0:  # 奇数
                            start = int(i)
                        else:
                            seq += self.seq[start - 1:int(i)]
                    seq += last
            else:
                if codon_start:
                    init = self.seq[
                           int(list1[0]) - 1 + codon_start - 1:int(list1[1])]
                    for num, i in enumerate(list1[2:]):
                        if (num + 1) % 2 != 0:  # 奇数
                            start = int(i)
                        else:
                            seq += self.seq[start - 1:int(i)]
                    seq = init + seq
                else:
                    init = self.seq[int(list1[0]) - 1:int(list1[1])]
                    for num, i in enumerate(list1[2:]):
                        if (num + 1) % 2 != 0:  # 奇数
                            start = int(i)
                        else:
                            seq += self.seq[start - 1:int(i)]
                    seq = init + seq
            return seq

        if position.startswith('complement'):
            if 'join' in position or 'order' in position:
                try:
                    codon_start = False
                    seq = muti_join(
                        list1, codon_start=codon_start, complement=True)
                except KeyError:
                    seq = muti_join(list1, complement=True)
            else:
                try:
                    codon_start = 1
                    if transExcpt:
                        seq = self.afterTransExcept(
                            ini, str(int(ter) - codon_start + 1))
                    else:
                        seq = self.seq[start:stop - codon_start + 1]
                except KeyError:
                    if transExcpt:
                        seq = self.afterTransExcept(ini, ter)
                    else:
                        seq = self.seq[start:stop]
            seq = seq[::-1].upper()
            gene_seq = ''
            dict1 = {"A": "T", "T": "A", "C": "G", "G": "C"}
            for i in seq:
                if i in 'ATGC':
                    gene_seq += dict1[i]
                else:
                    gene_seq += i
            return gene_seq
        else:
            if 'join' in position or 'order' in position:
                try:
                    codon_start = False
                    seq = muti_join(list1, codon_start=codon_start)
                    return seq
                except KeyError:
                    # self.seq[start:stop] + self.seq[int(list1[2]) - 1:int(list1[3])]
                    return muti_join(list1)
            else:
                try:
                    codon_start = 1
                    if transExcpt:
                        # 这里要保持ini的状态
                        return self.afterTransExcept(str(int(ini) - 1 + codon_start), ter)
                    else:
                        return self.seq[int(list1[0]) - 1 + codon_start - 1:int(list1[1])]
                except KeyError:
                    if transExcpt:
                        return self.afterTransExcept(ini, ter)
                    else:
                        return self.seq[start:stop]


class SeqGrab(object):  # 统计序列

    def __init__(self, sequence, decimal=1):
        self.sequence = sequence.upper()
        if sequence:
            # 如果传入的序列有效
            self.length = len(self.sequence)
            self.size = str(self.length)
            self.decimal = "%." + "%df" % decimal
            self.A = self.sequence.count("A")
            self.T = self.sequence.count("T")
            self.C = self.sequence.count("C")
            self.G = self.sequence.count("G")
            self.A_percent = self.decimal % (self.A * 100 / self.length)
            self.T_percent = self.decimal % (self.T * 100 / self.length)
            self.C_percent = self.decimal % (self.C * 100 / self.length)
            self.G_percent = self.decimal % (self.G * 100 / self.length)
            self.AT_percent = self.decimal % (
                float(self.A_percent) + float(self.T_percent))
            self.GC_percent = self.decimal % (
                float(self.C_percent) + float(self.G_percent))
            self.GT_percent = self.decimal % (
                float(self.G_percent) + float(self.T_percent))
            if self.A != 0 or self.T != 0:  # 避免不包含AT的序列
                self.AT_skew = "%.3f" % ((self.A - self.T) / (self.A + self.T))
            else:
                self.AT_skew = "N/A"
            if self.G != 0 or self.C != 0:
                self.GC_skew = "%.3f" % ((self.G - self.C) / (self.G + self.C))
            else:
                self.GC_skew = "N/A"
        else:
            self.length = "N/A"
            self.size = "N/A"
            self.A = "N/A"
            self.T = "N/A"
            self.C = "N/A"
            self.G = "N/A"
            self.A_percent = "N/A"
            self.T_percent = "N/A"
            self.C_percent = "N/A"
            self.G_percent = "N/A"
            self.AT_percent = "N/A"
            self.GC_percent = "N/A"
            self.GT_percent = "N/A"
            self.AT_skew = "N/A"
            self.GC_skew = "N/A"

    def splitCodon(self):
        first, second, third = "", "", ""
        for num, i in enumerate(self.sequence):
            if num % 3 == 0:
                first += i
            elif num % 3 == 1:
                second += i
            else:
                third += i
        return first, second, third

    def judge_ddfs(self, list_codon, code_table):
        nuc = ["A", "T", "C", "G"]
        codon_ffds_site = []
        # judge first codon site
        AAs = [str(Seq("".join([i, list_codon[1], list_codon[2]])).translate(table=code_table)) for i in nuc]
        if len(set(AAs)) == 1: codon_ffds_site.append(0)
        # judge second codon site
        AAs = [str(Seq("".join([list_codon[0], i, list_codon[2]])).translate(table=code_table)) for i in nuc]
        if len(set(AAs)) == 1: codon_ffds_site.append(1)
        # judge third codon site
        AAs = [str(Seq("".join([list_codon[0], list_codon[1], i])).translate(table=code_table)) for i in nuc]
        if len(set(AAs)) == 1: codon_ffds_site.append(2)
        return codon_ffds_site

    def extract_ffds1(self, code_table):
        '''
        Extract fourfold degenerate sequences from a codon sequence (obsolete)
        :param seq: nucleotide sequences
        :param code_table: NCBI code table, like Vertebrate Mitochondrial or 2
        :return: fourfold degenerate sequences
        '''
        ffds = ""
        if len(self.sequence)%3 == 0:
            for a, b, c in zip(*[iter(self.sequence)]*3):
                ffds += self.judge_ddfs([a, b, c], code_table)
        return ffds

    def extract_ffds(self, code_table):
        '''
        Extract fourfold degenerate sequences from a codon sequence
        :param seq: nucleotide sequences
        :param code_table: NCBI code table, like Vertebrate Mitochondrial or 2
        :return: fourfold degenerate sequences
        '''
        bases = ['T', 'C', 'A', 'G']
        codons = [a + b + c for a in bases for b in bases for c in bases]
        dict_ffds = {} # {'TCT': [3], 'TCC': [3]}
        for codon in codons:
            codon_ffds_site = self.judge_ddfs(list(codon), code_table)
            if codon_ffds_site: dict_ffds[codon] = codon_ffds_site
        # print(dict_ffds)
        ffds = ""
        if len(self.sequence)%3 == 0:
            for a, b, c in zip(*[iter(self.sequence)]*3):
                codon_ = "".join([a, b, c])
                if codon_ in dict_ffds: ffds += "".join([codon_[site] for site in dict_ffds[codon_]])
        return ffds


class CodonBias(object):
    '''
    未解决的问题是aa_stat_fun里面那个n=1的时候；
    '''

    def __init__(self, seq, codeTable=1, codonW=None, path=None):
        self.seq = seq
        self.codeTable = codeTable
        self.codonW = codonW
        self.path = path
        self.factory = Factory()

    def getCodonBias(self):
        first, second, third = SeqGrab(self.seq).splitCodon()
        GC1 = str(float(SeqGrab(first).GC_percent)/100)
        GC2 = str(float(SeqGrab(second).GC_percent)/100)
        GC12 = str((float(GC1) + float(GC2)) / 2) #SeqGrab(first + second).GC_percent
        GC3 = str(float(SeqGrab(third).GC_percent)/100)
        ##ENC
        self.GetCodeTable()
        # enc = self.getENC() #自己实现的，好像有点儿问题
        list_bias = self.fetchCBS()
        return [GC1, GC2, GC12, GC3] + list_bias

    def fetchCBS(self):
        dict_ = {"1":"0", "2":"1", "5":"4", "9":"7"}
        out = ["NA", "NA", "NA", "NA", "NA", "NA", "NA", "NA"]
        if str(self.codeTable) not in dict_: return out  ##记得改
        code = dict_[str(self.codeTable)]
        os.chdir(self.path)
        infile = "codonW_infile.fas"
        outfile = "codonW_outfile.txt"
        blkfile = "codonW_blk.txt"
        errorfile = "codonW_error.fas"
        with open(self.path + os.sep + infile, "w", encoding="utf-8") as f:
            f.write(">seq\n%s\n"%self.seq)
        command = '"%s" "%s" "%s" "%s" -all_indices -nomenu -silent -noblk -code %s'%(self.codonW, infile, outfile, blkfile, code)
        # print(command)
        popen = self.factory.init_popen(command)
        try:
            while True:
                try:
                    out_line = popen.stdout.readline().decode("utf-8", errors='ignore')
                except UnicodeDecodeError:
                    out_line = popen.stdout.readline().decode("gbk", errors='ignore')
                if out_line == "" and popen.poll() is not None:
                    break
        except: pass
        ## 读取输出结果
        if not os.path.exists(self.path + os.sep + outfile):
            with open(errorfile, "a", encoding="utf-8") as f2:
                f2.write(command + "\n" + self.seq + "\n")
            # print("error seq.:", self.seq)
        else:
            with open(self.path + os.sep + outfile, encoding="utf-8", errors="ignore") as f1:
                content = f1.read()
            try:
                list_ = content.split("\n")[1].split("\t")
                out = list_[5:9] + list_[11:15]
            except IndexError:
                with open(errorfile, "a", encoding="utf-8") as f2:
                    f2.write(command + "\n" + self.seq + "\n")
        for num, i in enumerate(out):
            if (not self.is_float(i)) and (not self.is_int(i)): out[num] = "NA"
        return out

    def is_float(self, input):
        try:
            num = float(input)
        except ValueError:
            return False
        return True

    def is_int(self, input):
        try:
            num = int(input)
        except ValueError:
            return False
        return True

    def GetCodeTable(self):
        #这里必须深拷贝，不然pop了以后会影响原来的
        self.dict_CodeTable = copy.deepcopy(CodonTable.generic_by_id[
            int(self.codeTable)].forward_table)   #{'TTT': 'F', 'UUU': 'F', 'TTC': 'F', 'UUC': 'F', 'TTA': 'L', 'UUA': 'L', 'TTG': 'L', 'UUG':...
        # list_stopCodons = CodonTable.generic_by_id[
        #     int(self.codeTable)].stop_codons
        # dict_stopCodons = {}.fromkeys(list_stopCodons, "*")
        # # 把终止子也加上去
        # self.dict_CodeTable.update(dict_stopCodons) #{'TTT': 'F', 'UUU': 'F', 'TTC': 'F', 'UUC': 'F', 'TTA': 'L', 'UUA': 'L', 'TTG': 'L', 'UUG':...
        # 删除带U的密码子
        list_keys = list(self.dict_CodeTable.keys())
        for i in list_keys:
            if "U" in i:
                self.dict_CodeTable.pop(i)

    def getENC(self):
        self.amino_acids = set(self.dict_CodeTable.values())
        codon_freq_in_seq = self.getCodonFreq(self.seq) # #{'TTT': 16, 'TTC': 10, 'TTA': 8, 'TTG': 16,...
        aa_stat = {} # hz{'H': 0.42857142857142844, 'V': 0.2774822695035461, 'G': 0.2408602150537634, ...
        for aa in self.amino_acids:
           aa_stat[aa] = self.aa_stat_fun(codon_freq_in_seq, aa)
        ##得到没有stop codon的时候，各个氨基酸的fold数
        self.dict_fold_codons = self.getFoldNum()  # {2: 9, 3: 1, 4: 5, 6: 3}
        enc = self.calc_enc(aa_stat)
        # print(enc)
        return enc

    def getCodonFreq(self, seq):
        seq_len = len(seq)
        seq = seq.upper().replace("U", "T") #标准化序列
        dict_codonFreq = {}.fromkeys(list(self.dict_CodeTable.keys()), 0)
        for i in range(0, seq_len, 3):
            codon = seq[i: i + 3]
            if len(codon) != 3:
                continue
            if codon in dict_codonFreq:
                dict_codonFreq[codon] += 1
            # else:
            #     codontable['XXX'][2] += 1
        return dict_codonFreq

    def aa_stat_fun(self, codon_freq_in_seq, aa):
        aa_codons = self.get_aa_codons(aa)  # 这个氨基酸的所有密码子
        if len(aa_codons) == 1:
            return 1
        n = sum(codon_freq_in_seq[codon] for codon in aa_codons)  # 有时候这个n会是1或者0,这种情况怎么办（看看codonW怎么处理的）？
        if n in [0, 1]:
            return 0
        sum_ = 0
        for i in aa_codons:
            p = float(codon_freq_in_seq[i]) / n
            sum_ += p * p
        return (n * sum_ - 1) / (n - 1)

    def aa_codon_num_fun(self, aa):
        # 废弃
        return len(list(filter(lambda it: it[1] == aa, self.dict_CodeTable.items())))

    def get_aa_codons(self, aa):
        return [it[0] for it in self.dict_CodeTable.items() if it[1] == aa]

    def getFoldNum(self):
        list_aas = list(self.dict_CodeTable.values())
        dict_fold_codons = {}
        for aa in self.amino_acids:
            fold = list_aas.count(aa)
            dict_fold_codons.setdefault(fold, []).append(aa)
        # print(dict_fold_codons)
        return dict_fold_codons

    def calc_enc(self, aa_stat):
        avg = {}
        enc = 0
        for fold in self.dict_fold_codons:
            hzs = list(aa_stat[aa] for aa in self.dict_fold_codons[fold])
            avg[fold] = sum(hzs) / len(hzs)
            enc += (len(self.dict_fold_codons[fold]) / avg[fold])
        return enc


class Order2itol(object):
    def __init__(self, dict_order, dict_args):
        self.dict_args = dict_args
        self.dict_order = dict_order
        self.align_order()
        self.number_NCR()
        self.exec()
        self.make_header()

    def align_order(self):
        for i in self.dict_order:
            list_order = self.dict_order[i]
            for num, j in enumerate(list_order):
                if self.dict_args["start_gene_with"] in j:
                    self.dict_order[i] = list_order[num:] + list_order[:num]
                    break

    def number_NCR(self):
        list_dict_order = list(self.dict_order.keys())
        for i in list_dict_order:
            list_order = self.dict_order[i]
            count = 1
            for num, j in enumerate(list_order):
                if j.startswith("NCR") or j.startswith("-NCR"):
                    part = list(j.partition("("))
                    part.insert(1, str(count))
                    list_order[num] = "".join(part)
                    count += 1
            self.dict_order[i] = list_order

    def chainShape(self, shape):
        if shape == "PL" or shape == "PR":
            shape = "PL" if self.orderName.startswith("-") else "PR"
        elif shape == "TL" or shape == "TR":
            shape = "TL" if self.orderName.startswith("-") else "TR"
        else:
            shape = shape
        return shape

    def exec(self):
        self.itol_domain = ""
        list_dict_order = list(self.dict_order.keys())
        self.gene_itol_info = {} # {name: [shape, color]}
        self.list_count = []
        for i in list_dict_order:
            self.itol_each_domain = ""
            list_order = self.dict_order[i]
            self.endNum = 0
            count = 0
            for self.orderName in list_order:
                self.orderName = self.orderName.split("_copy")[0]  # 预防有copy的基因
                # 是否有该基因对应的设置
                match = False
                for gene_name in self.dict_args["itol gene display"]:
                    if gene_name not in ["PCGs", "rRNAs", "tRNAs", "NCR"]:
                        rgx_gene_name = "-?" + "$|-?".join(gene_name.split("|")) + "$"
                        num_range = re.findall(r"(\d+)\-(\d+)", gene_name)
                        if num_range:
                            nums = f'({"|".join([str(num) for num in range(int(num_range[0][0]), int(num_range[0][1])+1)])})'
                            rgx_gene_name = re.sub(r"\d+\-\d+", nums, rgx_gene_name) # COX1-3 --> COX(1|2|3)
                        rgx = re.compile(rgx_gene_name, re.I)
                        # print(rgx)
                        if rgx.match(self.orderName):
                            color, size, shape = self.dict_args["itol gene display"][gene_name]
                            self.secondNum = self.endNum + int(size)
                            self.firstNum = self.endNum + \
                                            0 if self.endNum == 0 else\
                                self.endNum + self.dict_args["gene interval"]
                            shape = self.chainShape(shape)
                            self.itol_each_domain += ",%s|%.1f|%.1f|%s|%s" % (
                                shape, self.firstNum, self.secondNum, color, self.orderName)
                            self.endNum = self.secondNum
                            if gene_name not in self.gene_itol_info:
                                self.gene_itol_info[gene_name] = [shape, color]
                            count += 1
                            match = True
                            break
                if not match:
                    # 如果单个基因没有设置，就看PCGs、tRNA等是否匹配
                    judge_name = re.sub("^NCR\d+$", "NCR", self.orderName.lstrip("-"), re.I) # 用于判断用的名字
                    for feature in ["PCGs", "rRNAs", "tRNAs", "NCR"]:
                        if (feature in self.dict_args["itol gene display"]) and \
                                (judge_name in self.dict_args[f"{feature} names"]):
                            color, size, shape = self.dict_args["itol gene display"][feature]
                            self.secondNum = self.endNum + int(size)
                            self.firstNum = self.endNum + \
                                            0 if self.endNum == 0 else self.endNum + self.dict_args["gene interval"]
                            shape = self.chainShape(shape)
                            self.itol_each_domain += ",%s|%.1f|%.1f|%s|%s" % (
                                shape, self.firstNum, self.secondNum, color, self.orderName)
                            self.endNum = self.secondNum
                            if feature not in self.gene_itol_info:
                                self.gene_itol_info[feature] = [shape, color]
                            count += 1
            self.list_count.append(count)
            self.itol_domain += i + "," + \
                                str(self.endNum) + self.itol_each_domain + "\n"

    def make_header(self):
        list_names, list_shapes, list_colors = [], [], []
        for name in sorted(self.gene_itol_info.keys()):
            shape, color = self.gene_itol_info[name]
            list_names.append(name)
            list_shapes.append(shape)
            list_colors.append(color)
        width = max(self.list_count)*35
        gene_order_header = f"DATASET_DOMAINS\nSEPARATOR COMMA\nDATASET_LABEL,Gene order\n" \
                      f"COLOR,#ff00aa\nWIDTH,{width}\nBACKBONE_COLOR,black\nHEIGHT_FACTOR,0.8\n" \
                      f"LEGEND_TITLE,Regions\n" \
                      f"LEGEND_SHAPES,{','.join(list_shapes)}\n" \
                      f"LEGEND_COLORS,{','.join(list_colors)}\n" \
                      f"LEGEND_LABELS,{','.join(list_names)}\n" \
                      f"#SHOW_INTERNAL,0\nSHOW_DOMAIN_LABELS,1\nLABELS_ON_TOP,1\nDATA\n"
        self.itol_gene_order = gene_order_header + self.itol_domain


class ArrayManager(object):
    def __init__(self, array):
        self.array = array
        self.header = array[0]
        self.data = array[1:]

    def get_index_by_IDs(self, IDs):
        return [num for num, row in enumerate(self.data) if row and ((row[0] in IDs) or (row[0].split(".")[0] in IDs))]

    def remove_by_row_Indice(self, indice, base=None, proportion=None, processSig=None):
        sorted_indice = sorted(indice, reverse=True)
        for num, index in enumerate(sorted_indice):
            self.data.pop(index)
            if processSig:
                num += 1
                processSig.emit(base + (num / len(sorted_indice)) * proportion)
        return [self.header] + self.data

    def remove_by_row_IDs(self, IDs, base=None, proportion=None, processSig=None):
        indice = self.get_index_by_IDs(IDs)
        if not indice:
            return [self.header] + self.data
        if processSig:
            processSig.emit(base + (1 / 10) * proportion)
            base = base + (1 / 10) * proportion
            return self.remove_by_row_Indice(indice, base, (9 / 10) * proportion, processSig)
        else:
            return self.remove_by_row_Indice(indice)

    def remove_by_col_IDs(self, IDs):
        ##比较耗时，可以考虑重写
        zip_array = self.zip_an_array(self.array)
        indice = [num for num, colH in enumerate(self.header) if colH in IDs]
        for index in sorted(indice, reverse=True):
            zip_array.pop(index)
        return self.zip_an_array(zip_array)

    def zip_an_array(self, array):
        return list(map(list, zip(*array)))

    def convertArray2DictCol(self, array):
        '''将矩阵转变为列表头为键，下面的data为值的字典'''
        zip_array = self.zip_an_array(array)
        return OrderedDict((k[0], k[1:]) for k in zip_array)

    def convertDictCol2Array(self, dict_col_array):
        col_array = [[i] + list(dict_col_array[i]) for i in dict_col_array]
        return self.zip_an_array(col_array)

    def updateArrayByColheader(self, colheader):
        '''根据列表头来更新自己的数据, 没有的表头就补充空项'''
        dict_col_data = self.convertArray2DictCol(self.array)
        for col in colheader:
            if col not in dict_col_data:
                dict_col_data[col] = ["none"] * len(self.data)
        array_by_col = [[col] + list(dict_col_data[col]) for col in colheader]
        new_array = self.zip_an_array(array_by_col)
        return new_array

    def fetchUnextractInfo(self):
        '''判断哪些信息没有被提取'''
        zip_array = self.zip_an_array(self.array)
        return [i[0] for i in zip_array if list(i[1:]) == ["none"] * len(i[1:])]

    def complementUnextractInfo(self, new_extract_array):
        '''把没有提取的信息补足，常常和上一个方法连用'''
        dict_new_array = self.convertArray2DictCol(new_extract_array)
        dict_col_array = self.convertArray2DictCol(self.array)
        for i in dict_col_array:
            if i in dict_new_array:
                dict_col_array[i] = dict_new_array[i]
        return self.convertDictCol2Array(dict_col_array)

    def fetchRowHeader(self):
        return [i[0] for i in self.array[1:]]

    def fetchIdTime(self):
        indice = [num for num, i in enumerate(self.header) if i in ["ID", "Latest modified"]]
        if len(indice) < 2:
            return OrderedDict()
        else:
            return OrderedDict((row_data[indice[0]], row_data[indice[1]]) for row_data in self.data)


class GbManager(QObject, object):
    ##改类的parent必须有一个exception_signal信号
    # messageSig = pyqtSignal(str, str)

    def __init__(self, filePath, exceptSig=None, parent=None):
        super(GbManager, self).__init__(parent)
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.filePath = filePath
        self.parent = parent
        if exceptSig:
            self.exception_signal = exceptSig
        elif parent:
            self.exception_signal = parent.exception_signal
        # self.factory = Factory()
        # self.messageSig.connect(lambda message, type: self.factory.popupMessage(self.parent, message, type))
        self.data_settings = QSettings(
            self.factory.workPlaceSettingPath + os.sep + 'data_settings.ini', QSettings.IniFormat)
        self.interrupt = False

    def merge_gbRecords(self, genbanks=None, byHandle=False):
        if byHandle:
            # 传入的是文件句柄，就像with open打开的f
            gb_records = itertools.chain()
            for gbHandle in genbanks:
                gb_records = itertools.chain(gb_records, SeqIO.parse(gbHandle, "genbank"))
        else:
            gb_records = itertools.chain()
            for gbPath in genbanks:
                gb_records = itertools.chain(gb_records, SeqIO.parse(gbPath, "genbank"))
        return gb_records

    def merge_gbIndex(self, genbanks):
        ##耗时，而且容易卡死
        merged_index = OrderedDict()
        for gb in genbanks:
            gb_index = SeqIO.index(gb, "genbank")
            merged_index.update(gb_index)
        return merged_index

    def merge_file_contents(self, files, base=None, proportion=None, processSig=None):
        all_content = ""
        for num, file in enumerate(files):
            with open(file, encoding="utf-8", errors='ignore') as f:
                all_content += f.read()
            if processSig:
                processSig.emit(base + (num+1)*proportion/len(files))
        return all_content

    def fetchLineages(self, list_taxonomy, organism, source_feature, updateMode=False):
        ##update是更新界面数据，这种情况下，不能以source的分类群注释为准
        lineages_name, array = self.factory.getCurrentTaxSetData()
        array1 = copy.deepcopy(array)
        array1.insert(0, lineages_name)
        zip_array = list(zip(*array1))
        dict_taxonomy = {i[0]: i[1:] for i in zip_array}
        ###taxonomy
        dict_lineages = OrderedDict().fromkeys(lineages_name, "N/A")
        # ida是针对绦虫的,如果有[family]这类似的注释，就先提取这个,这种现在一般没人这样注释
        # rgx_tax_tag = re.compile(r"(.+?)\[(.+?)\]")
        # if rgx_tax_tag.search(taxonomy):
        #     name, lineage = rgx_tax_tag.findall(taxonomy)[0]
        #     if lineage in dict_lineages:
        #         dict_lineages[lineage] = name
        #     continue
        for lineage in lineages_name:
            if (not updateMode) and (lineage in source_feature.qualifiers) \
                    and (source_feature.qualifiers[lineage][0] not in ["N/A", ""]): #如果不是刷新界面，就以source里面的注释为准
                dict_lineages[lineage] = source_feature.qualifiers[lineage]
                continue
            if lineage.upper() == "GENUS":
                dict_lineages[lineage] = organism.split()[0]
                continue
            list_names = list(dict_taxonomy[lineage])
            for taxonomy in list_taxonomy:
                # 去除空项
                while "" in list_names:
                    list_names.remove("")
                exclude_names = [exl_name.lstrip("-") for exl_name in list_names if exl_name.strip().startswith("-")]
                remain_names = [val for val in list_names if val not in exclude_names]
                is_exclude = [
                    True for l in exclude_names if taxonomy.lower().endswith(
                    l.strip().strip("*").lower())]
                if is_exclude:
                    ##说明这个名字是exclude的
                    continue
                ok = [
                    True for l in remain_names if taxonomy.lower().endswith(
                        l.strip().strip("*").lower())]
                if ok:
                    ##这里代表已经找到这个lineage的对应的名字,所以应该跳出
                    dict_lineages[lineage] = taxonomy
                    break
        return dict_lineages

    def fetch_name_key_mapping(self):
        return {
            "Date": "date",
            "Keywords": "keywords",
            "Organism": "organism",
            "Molecule type": "molecule_type",
            "Topology": "topology",
            "Accessions": "accessions",
            "Sequence version": "sequence_version",
            "Source": "source",
        }

    def fetch_references(self, annotations):
        dict_references = {}
        if "references" in annotations:
            REFERENCEs = annotations["references"]
            authors = ""
            title = ""
            journal = ""
            pubmed = ""
            comment = ""
            for num_ref, reference in enumerate(REFERENCEs):
                authors += str(num_ref + 1) + ". " + reference.authors + " " if reference.authors else ""
                title += str(num_ref + 1) + ". " + reference.title + " " if reference.title else ""
                journal += str(num_ref + 1) + ". " + reference.journal + " " if reference.journal else ""
                pubmed += str(num_ref + 1) + ". " + reference.pubmed_id + " " if reference.pubmed_id else ""
                comment += str(num_ref + 1) + ". " + reference.comment + " " if reference.comment else ""
            # ["author(s)", "title(s)", "journal(s)", "pubmed ID(s)", "comment(s)"]
            authors = "N/A" if not authors else authors
            title = "N/A" if not title else title
            journal = "N/A" if not journal else journal
            pubmed = "N/A" if not pubmed else pubmed
            comment = "N/A" if not comment else comment
            dict_references = {
                "author(s)": authors,
                "title(s)": title,
                "journal(s)": journal,
                "pubmed ID(s)": pubmed,
                "comment(s)": comment
            }
        else:
            dict_references = {
                "author(s)": "N/A",
                "title(s)": "N/A",
                "journal(s)": "N/A",
                "pubmed ID(s)": "N/A",
                "comment(s)": "N/A"
            }
        return dict_references

    def fetch_source_feature(self, gb_record):
        source_feature = None
        has_source = False
        for i in gb_record.features:
            if i.type == "source":
                source_feature = i
                has_source = True
                break
        if not has_source:
            ##加一个source feature
            my_start_pos = SeqFeature.ExactPosition(0)
            my_end_pos = SeqFeature.ExactPosition(len(gb_record.seq))
            my_feature_location = FeatureLocation(my_start_pos, my_end_pos)
            my_feature_type = "source"
            source_feature = SeqFeature.SeqFeature(my_feature_location, type=my_feature_type)
            gb_record.features.insert(0, source_feature)
        return source_feature

    def fetch_array(self):
        default_info = ["ID", "Organism", "Length", "AT%", "Latest modified"]
        requiredTaxonomy = self.factory.getCurrentTaxSetData()[0]
        default_info[
        2:2] = requiredTaxonomy  # 将分类信息插入到列表中间  ["ID", "Organism", list_of_taxonomy, "Length", "AT%", "Latest modified"]
        name = re.sub(r"/|\\", "_", self.filePath) + "_displayedArray"
        displayedArray = self.data_settings.value(name, [default_info])  # 界面展示的，header+array
        if not displayedArray:
            ##有时候是none的时候
            displayedArray = [default_info]
        return displayedArray

    def fetchAllGBpath(self):
        return glob.glob(self.filePath + os.sep + ".data" + os.sep + "*.gb")

    def fetchAllGBpathMTime(self):
        '''获取所有gb文件的修改时间'''
        allGBPath = self.fetchAllGBpath()
        return OrderedDict((self.fetchIDbyPath(path),
                            datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S'))
                           for path in allGBPath)

    def fetchAllRecords(self):
        listGB_paths = self.fetchAllGBpath()
        return self.merge_gbRecords(listGB_paths)

    def fetchAllIndex(self):
        listGB_paths = self.fetchAllGBpath()
        return self.merge_gbIndex(listGB_paths)

    def fetchVerifiedIDs(self, base=None, proportion=None, processSig=None):
        '''已废弃'''
        all_gb_contents = self.merge_file_contents(self.fetchAllGBpath(), base, 95*proportion/100, processSig)
        rgx = re.compile(r"\/State=\"(\S+) (\S+)\"")
        verifiedIDs = []
        list_matches = rgx.findall(all_gb_contents)
        total = len(list_matches)
        for num, i in enumerate(list_matches):
            if i[-1] == "verified":
                verifiedIDs.append(i[0])
            if processSig:
                processSig.emit(base + 95*proportion/100 + (num+1)*(5/100)*proportion/total)
        return verifiedIDs

    # def fetchUnverifiedIDsbyIDs(self, list_IDs):
    #     '''extracter判断用'''
    #     list_ID_path = [self.fetchRecordPath(ID) for ID in list_IDs]
    #     allcontent = self.merge_file_contents(list_ID_path)
    #     rgx = re.compile(r"\/State=\"(\S+) (\S+)\"")
    #     return [i[0] for i in rgx.findall(allcontent) if i[-1] == "unverified"]

    def fetchModifiedTime(self, gb_record, byFile=None):
        file = self.fetchRecordPath(gb_record.id) if not byFile else byFile
        if os.path.exists(file):
            return datetime.datetime.fromtimestamp(os.path.getmtime(file)).strftime('%Y-%m-%d %H:%M:%S')
        else:
            # 返回当前时间
            return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def fetchRecordPath(self, ID):
        return self.filePath + os.sep + ".data" + os.sep + ID + ".gb"

    def fetchRecordsByIDs(self, IDs):
        listGB_paths = [self.fetchRecordPath(ID) for ID in IDs]
        return self.merge_gbRecords(listGB_paths)

    def fetchRecordByID(self, ID):
        path = self.fetchRecordPath(ID)
        return SeqIO.read(path, "genbank")

    # def fetchRecordPathByName(self, name):
    #     allGBpath = self.fetchAllGBpath()
    #     return [gb for gb in allGBpath if os.path.splitext(os.path.basename(gb))[0].split(".")[0] == name][0]

    def fetchAvailableInfo(self):
        # 存的时候用路径作为键
        name = re.sub(r"/|\\", "_", self.filePath) + "_availableInfo"
        array4tree = self.data_settings.value(name, None)
        if not array4tree:
            ##没有的时候就初始化一个
            requiredTaxonomy = self.factory.getCurrentTaxSetData()[0]
            list_source = []
            list_reference = ["author(s)", "title(s)", "journal(s)", "pubmed ID(s)", "comment(s)"]
            list_annotations = ["ID", "Length", "AT%", "Name", "Organism", "Definition", "Date", "Keywords",
                                "Molecule type", "Topology",
                                "Accessions", "Sequence version", "Source", "Latest modified"]
            array4tree = [
                ["Annotations", list_annotations],
                ["Lineages", requiredTaxonomy],
                ["Reference", list_reference],
                ["Sources", list_source]
            ]
            self.data_settings.setValue(name, array4tree)
        return array4tree

    def fetchContentsByIDs(self, IDs, base=None, proportion=None, processSig=None):
        contents = ""
        for num, ID in enumerate(IDs):
            ID_path = self.fetchRecordPath(ID)
            with open(ID_path, encoding="utf-8", errors='ignore') as f:
                contents += f.read()
            if processSig:
                processSig.emit(base + (num+1)*proportion/len(IDs))
        return contents

    # def fetchIDsByContents(self, contents):
    #     '''注意这个ID是locus的ID'''
    #     rgx = re.compile(r"(?sm)LOCUS {7}(\S+).+?^//\s*?(?=LOCUS|$)")
    #     return rgx.findall(contents)

    def fetchIDbyPath(self, path):
        return os.path.splitext(os.path.basename(path))[0]

    # def fetchIDbyNames(self, names):
    #     gbPaths = self.fetchAllGBpath()
    #     list_IDs = []
    #     for name in names:
    #         for path in gbPaths:
    #             if os.path.splitext(os.path.basename(path))[0].split(".")[0]
    #     return list_IDs

    def fetchInfo4extracter(self, list_IDs):
        '''已废弃'''
        list_ID_path = [self.fetchRecordPath(ID) for ID in list_IDs]
        list_indice = self.merge_gbIndex(list_ID_path)
        allcontent = self.merge_file_contents(list_ID_path)
        rgx = re.compile(r"\/State=\"(\S+) (\S+)\"")
        unverifiedIDs = [i[0] for i in rgx.findall(allcontent) if i[-1] == "unverified"]
        names4extracter = [list_indice[index].annotations["organism"] + " " + list_indice[index].name for index in
                           list_indice]
        return names4extracter, allcontent, unverifiedIDs

    def extractRequiredInfo(self, gb_record, requiredInfos):
        ## 三大部分，1是最外面的ID，name,description,和dbxrefs，2是annotation里面的，3是source里面的，首先判断各个需要提取的部分属于哪里
        annotations = gb_record.annotations
        ###用于判断各个信息属于哪一类###
        name = re.sub(r"/|\\", "_", self.filePath) + "_availableInfo"
        arrar4tree = self.data_settings.value(name, self.fetchAvailableInfo())
        # print(arrar4tree)
        ###得到键和信息名字的映射关系###
        name_key_mapping = self.fetch_name_key_mapping()
        ###得到source注释信息###
        dict_sources = self.fetch_source_feature(gb_record).qualifiers
        ###得到参考文献信息###
        dict_references = self.fetch_references(annotations)
        list_info = []
        for requiredInfo in requiredInfos:
            if requiredInfo == "ID":
                list_info.append(gb_record.id) if hasattr(gb_record, "id") else list_info.append("N/A")
            elif requiredInfo == "Definition":
                list_info.append(gb_record.description) if hasattr(gb_record, "description") else list_info.append(
                    "N/A")
            elif requiredInfo == "Name":
                list_info.append(gb_record.name) if hasattr(gb_record, "name") else list_info.append(
                    "N/A")
            elif requiredInfo == "Length":
                list_info.append(len(gb_record.seq)) if hasattr(gb_record, "seq") else list_info.append(
                    "N/A")
                # list_info.append(str(len(gb_record.seq))) if hasattr(gb_record, "seq") else list_info.append(
                #     "N/A")
            elif requiredInfo == "AT%":
                if hasattr(gb_record, "seq"):
                    seq = str(gb_record.seq)
                    seqStat = SeqGrab(seq)
                    list_info.append(float(seqStat.AT_percent))
                else:
                    list_info.append("N/A")
            elif requiredInfo == "Latest modified":
                modifiedTime = self.fetchModifiedTime(gb_record)
                list_info.append(modifiedTime)
            elif requiredInfo in arrar4tree[0][1]:
                # Annotations
                annotation_key = name_key_mapping[requiredInfo] if requiredInfo in name_key_mapping else requiredInfo
                if annotation_key in annotations:
                    text = ", ".join(annotations[annotation_key]) if type(annotations[annotation_key]) == list else \
                        annotations[annotation_key]
                    list_info.append(text)
                else:
                    list_info.append("N/A")
            elif requiredInfo in arrar4tree[1][1] or (requiredInfo in arrar4tree[3][1]):
                # Lineages与Sources合并了
                if requiredInfo in dict_sources:
                    text = ", ".join(dict_sources[requiredInfo]) if type(dict_sources[requiredInfo]) == list else \
                        dict_sources[requiredInfo]
                    list_info.append(text)
                else:
                    list_info.append("N/A")
            elif (requiredInfo in arrar4tree[2][1]):
                # Reference
                list_info.append(
                    dict_references[requiredInfo]) if requiredInfo in dict_references else list_info.append("N/A")
            else:
                # unkown annotation
                list_info.append("unknown annoation")
        ##清除未知注释的界面展示
        return list_info

    def updateAvailableInfo(self, list_added_records=None, base=None, proportion=None, processSig=None):
        '''主要更新用于展示的source feature'''
        array4tree = self.fetchAvailableInfo()  # 初始化
        requiredTaxonomy = self.factory.getCurrentTaxSetData()[0]  ##如果分类群有变化，可以在这里更新
        if list_added_records:
            # merged_index = self.merge_gbIndex(genbank, base=base, proportion=None, processSig=None) ##前面的步骤好像也花了不少时间
            length = len(list_added_records)
            list_source = array4tree[3][1]
            for num, gb_record in enumerate(list_added_records):   #检测出是这个循环的问题
                # gb_record = merged_index[each_index]
                source_feature = self.fetch_source_feature(gb_record)  ##没有source的时候是None
                if source_feature:
                    list_source = list(set(list_source).union(set(source_feature.qualifiers.keys())))
                ##进度条
                if processSig:
                    num += 1
                    processSig.emit(base + (num / length) * proportion)
            array4tree[3][1] = list_source
        # else:
        #     # 没有文件就设置为空
        #     array4tree[3][1] = []
        array4tree[1][1] = requiredTaxonomy
        # 存的时候用路径作为键
        name = re.sub(r"/|\\", "_", self.filePath) + "_availableInfo"
        self.data_settings.setValue(name, array4tree)

    def updateAvailableInfo_2(self, genbank=None, base=None, proportion=None, processSig=None):
        ##导入的是文件名字, 删除模式专用
        array4tree = self.fetchAvailableInfo()  # 初始化
        requiredTaxonomy = self.factory.getCurrentTaxSetData()[0]  ##如果分类群有变化，可以在这里更新
        if genbank:
            merged_index = self.merge_gbIndex(genbank)
            list_source = []  # 如果是删除模式，就要重新读source
            for num, each_index in enumerate(merged_index):
                gb_record = merged_index[each_index]
                source_feature = self.fetch_source_feature(gb_record)  ##没有source的时候是None
                if source_feature:
                    list_source = list(set(list_source).union(set(source_feature.qualifiers.keys())))
                ##进度条
                if processSig:
                    num += 1
                    processSig.emit(base + (num / len(merged_index)) * proportion)
            array4tree[3][1] = list_source
        else:
            # 没有文件就设置为空
            array4tree[3][1] = []
        array4tree[1][1] = requiredTaxonomy
        # 存的时候用路径作为键
        name = re.sub(r"/|\\", "_", self.filePath) + "_availableInfo"
        self.data_settings.setValue(name, array4tree)

    def updateArrayByInfo(self, base=None, proportion=None, processSig=None):
        '''扫描矩阵，如果发现有信息没有被提取，就补充提取然后保存'''
        array = self.fetch_array()
        arrayMan = ArrayManager(array)
        list_unextract_info = arrayMan.fetchUnextractInfo()  # 如果发现有没有提取的就提取
        if not list_unextract_info:
            if processSig:
                processSig.emit(base + proportion)
            return
        gb_indice = self.fetchAllIndex()
        if processSig:
            processSig.emit(base + (5 / 100) * proportion)
        list_addition_array = [list_unextract_info]
        row_header = arrayMan.fetchRowHeader()
        for num, ID in enumerate(row_header):
            if processSig:
                num += 1
                processSig.emit(base + (5 / 100) * proportion + (num / len(gb_indice)) * (4 / 5) * proportion)
            if ID not in gb_indice:
                # 如果没有找到这个ID，就加空项
                list_addition_array.append([""] * len(list_unextract_info))
                continue
            gb_record = gb_indice[ID]
            ###提取需要的信息
            addition_array = self.extractRequiredInfo(gb_record, list_unextract_info)
            list_addition_array.append(addition_array)
        newArray = arrayMan.complementUnextractInfo(list_addition_array)
        self.saveArray(newArray)
        return newArray

    def updateModifiedRecord(self, base=None, proportion=None, processSig=None):
        array = self.fetch_array()
        arrayManager = ArrayManager(array)
        IDs_in_table = arrayManager.fetchRowHeader()
        # dict_ID_time = arrayManager.fetchIdTime()
        gbIndata = self.fetchAllGBpath() ##有时候只有.data里面有数据，也要考虑
        if (not IDs_in_table) and (not gbIndata):
            if processSig:
                processSig.emit(base+proportion)
            return
        IDs_in_data = [os.path.splitext(os.path.basename(gb))[0] for gb in gbIndata]
        haveUpdate = False
        # dict_ID_newest_time = self.fetchAllGBpathMTime()
        # .data里面没有，但是表格里面有的情况（要不要提供一个下载该数据的功能）
        Records_need_remove = [ID for ID in IDs_in_table if ID not in IDs_in_data] #界面有，.data文件里面没有
        # print("Records_need_remove", Records_need_remove)
        if Records_need_remove:
            self.deleteRecords(Records_need_remove, base, 10*proportion/100, processSig)  #进度条
            haveUpdate = True
        ## .data有，表格里面没有；以及.data的数据被改了，要实时更新
        # Records_need_update = [self.fetchRecordPath(ID) for ID in dict_ID_newest_time if
        #                        (ID not in dict_ID_time) or (dict_ID_newest_time[ID] != dict_ID_time[ID])]
        IDs_need_update = [ID for ID in IDs_in_data if ID not in IDs_in_table]
        # print("IDs_need_update", IDs_need_update)
        if IDs_need_update:
            # IDs_need_remove = [self.fetchIDbyPath(path) for path in IDs_need_update]
            newArray = arrayManager.remove_by_row_IDs(IDs_need_update, base + 10*proportion/100, 5*proportion/100, processSig)
            self.saveArray(newArray)
            gb_records = self.fetchRecordsByIDs(IDs_need_update)
            self.addRecordsSubFunc(gb_records, len(IDs_need_update), base + 15*proportion/100, 85*proportion/100, processSig)
            haveUpdate = True
        ##不论如何，都发送进度
        if processSig:
            processSig.emit(base + proportion)
        return haveUpdate

    def updateNewRecords(self, base, proportion, processSig, list_gbPath=None, byContent=False):
        '''比如说普通序列标准化以后更新'''
        if not byContent:
            # 暂时只实现内容导入
            return
        tempFile = self.filePath + os.sep + "new.gb"
        with open(tempFile, "w", encoding="utf-8") as f:
            f.write(byContent)
        dict_index = self.merge_gbIndex([tempFile])
        gb_records = dict_index.values()
        list_IDs = list(dict_index.keys())
        processSig.emit(base + (1 / 5) * proportion)
        ##先删除记录
        self.deleteRecords(list_IDs)
        self.addRecordsSubFunc(gb_records, len(list_IDs), base + (1 / 5) * proportion, (4 / 5) * proportion,
                               processSig)
        os.remove(tempFile)

    def updateRecords(self, base, proportion, processSig, removedTaxmy=None, reidentLineage=False):
        '''重新读一遍界面的数据，适用于分类群信息更新后'''
        try:
            gb_records = self.fetchAllRecords()
            totleLen = len(self.fetchAllGBpath())
            requiredInfos = self.fetch_array()[0]
            ##如果有类群被删除，就对应删掉
            # print(requiredInfos)
            if removedTaxmy:
                for i in removedTaxmy:
                    if i in requiredInfos:
                        requiredInfos.remove(i)
                # arrayMAN = ArrayManager(array)
                # array = arrayMAN.remove_by_col_IDs(colIDs)
            # print(requiredInfos)
            array = [requiredInfos]
            list_added_records = []
            for num, gb_record in enumerate(gb_records):
                ID = gb_record.id
                ##新增注释
                source_feature = self.fetch_source_feature(gb_record)
                if "User_Note" not in source_feature.qualifiers:
                    source_feature.qualifiers["User_Note"] = ""
                qualif_copy = copy.deepcopy(source_feature.qualifiers)
                taxonomy = gb_record.annotations["taxonomy"]
                organism = gb_record.annotations["organism"]
                dict_lineages = self.fetchLineages(taxonomy, organism, source_feature, updateMode=True)
                for lineage in dict_lineages:
                    if reidentLineage or (lineage not in source_feature.qualifiers):
                        source_feature.qualifiers[lineage] = dict_lineages[lineage]
                ##如果有类群被删除，就对应删掉
                # if removedTaxmy:
                #     for j in removedTaxmy:
                #         if j in source_feature.qualifiers:
                #             source_feature.qualifiers.pop(j)
                ###存序列
                if qualif_copy != source_feature.qualifiers:
                    ##有改变才存
                    SeqIO.write(gb_record, self.fetchRecordPath(ID), "genbank")
                    list_added_records.append(gb_record)
                # print(3, self.factory.getCurrentTaxSetData())
                ###提取需要的信息
                gb_record_array = self.extractRequiredInfo(gb_record, requiredInfos)
                # gb_record_array.append(str(gb_record.seq))
                array.append(gb_record_array)
                # print(4, self.factory.getCurrentTaxSetData())
                # self.list_Names.append(ID)
                if processSig:
                    num += 1
                    processSig.emit(base + (num / totleLen) * (9 / 10) * proportion)
            # 这样更新才能把最新的信息更新进去
            if processSig:
                self.updateAvailableInfo(list_added_records, base + (91 / 100) * proportion, (9 / 100) * proportion,
                                         processSig)
            else:
                self.updateAvailableInfo(list_added_records)
            self.saveArray(array)
            # print(6, self.factory.getCurrentTaxSetData())
        except:
            try:
                if os.path.exists(self.fetchRecordPath(ID)):
                    ##把报错这个序列删掉
                    os.remove(self.fetchRecordPath(ID))
            except:
                pass
            errorInfo = ''.join(
                traceback.format_exception(*sys.exc_info())) + "\n"
            self.exception_signal.emit(errorInfo + "GenBank file parse failed")

    def updateArrayByRow(self, ID, list_row, array):
        for index, row in enumerate(array):
            #先找到对应ID
            if ID == row[0]:
                break
        array[index] = list_row
        return array

    def updateRecords_tax(self, base, proportion, processSig, findLineage=False, IDs=[], database="NCBI"):
        '''更新界面的数据，适用于自动识别分类群'''
        try:
            gb_records = self.fetchRecordsByIDs(IDs)
            totleLen = len(IDs)
            # requiredInfos = self.fetch_array()[0]
            # array = self.fetch_array()
            list_added_records = []
            for num, gb_record in enumerate(gb_records):
                ID = gb_record.id
                ##新增注释
                source_feature = self.fetch_source_feature(gb_record)
                if "User_Note" not in source_feature.qualifiers:
                    source_feature.qualifiers["User_Note"] = ""
                organism = gb_record.annotations["organism"].split()[0]
                record_tax = gb_record.annotations["taxonomy"]
                if findLineage:
                    ## 自动从NCBI识别分类群
                    requiredLineageNames = self.factory.getCurrentTaxSetData()[0]
                    if database == "NCBI":
                        self.update_NCBI_lineages(requiredLineageNames, organism, source_feature, record_tax)
                    elif database == "WoRMS":
                        self.update_WoRMS_lineages(requiredLineageNames, organism, source_feature)
                ###存序列
                SeqIO.write(gb_record, self.fetchRecordPath(ID), "genbank")
                list_added_records.append(gb_record)
                ###提取需要的信息
                # gb_record_array = self.extractRequiredInfo(gb_record, requiredInfos)
                # array = self.updateArrayByRow(ID, gb_record_array, array)
                # array.append(gb_record_array)
                if processSig:
                    num += 1
                    processSig.emit(base + (num / totleLen) * (4/5) * proportion)
            # 这样更新才能把最新的信息更新进去
            if processSig:
                self.updateAvailableInfo(list_added_records, base + (4/5) * proportion,
                                         (1 / 10) * proportion,
                                         processSig)
            else:
                self.updateAvailableInfo(list_added_records)
            self.updateRecords(base + (9/10) * proportion, (1/10) * proportion, processSig)
            # self.saveArray(array)
        except Exception as ex:
            exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            if ex.__class__.__name__ == "URLError":
                exceptionInfo += "Update: please check network connection"
            else:
                try:
                    if os.path.exists(self.fetchRecordPath(ID)):
                        ##把报错这个序列删掉
                        os.remove(self.fetchRecordPath(ID))
                except:
                    pass
                exceptionInfo += "GenBank file parse failed"
            self.exception_signal.emit(exceptionInfo)

    def fetch_records_by_tax(self, base, proportion, processSig, taxonomy=""):
        '''更新界面的数据，适用于自动识别分类群'''
        try:
            gb_records = self.fetchAllRecords()
            totleLen = len(self.fetchAllGBpath())
            selected_ids = []
            self.tax_error_ids = []
            for num, gb_record in enumerate(gb_records):
                ID = gb_record.id
                ##新增注释
                source_feature = self.fetch_source_feature(gb_record)
                if "User_Note" not in source_feature.qualifiers:
                    source_feature.qualifiers["User_Note"] = ""
                organism = gb_record.annotations["organism"]
                record_tax = gb_record.annotations["taxonomy"]
                genus = organism.split()[0]
                if self.is_in_tax(organism, taxonomy, ID, genus, record_tax):
                    selected_ids.append(ID)
                if processSig:
                    num += 1
                    processSig.emit(base + (num / totleLen) * proportion)
            if self.tax_error_ids:
                list_id_str = '\n'.join(['\t'.join(j) for j in self.tax_error_ids])
                exceptionInfo = f"The following IDs get taxonomy failed: \n" \
                                f"ID\tSpecies\tGenus" \
                                f"{list_id_str}\n" \
                                f"part of IDs failed taxonomy"
                self.exception_signal.emit(exceptionInfo)
            return selected_ids
            # self.saveArray(array)
        except Exception as ex:
            exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            if ex.__class__.__name__ == "URLError":
                exceptionInfo += "Update: please check network connection"
            else:
                # try:
                #     if os.path.exists(self.fetchRecordPath(ID)):
                #         ##把报错这个序列删掉
                #         os.remove(self.fetchRecordPath(ID))
                # except:
                #     pass
                exceptionInfo += f"Error when parsing {ID}; Organism: {organism}\n"
                exceptionInfo += "GenBank file parse failed"
            self.exception_signal.emit(exceptionInfo)

    def is_in_tax(self, organism, taxonomy, ID, genus, record_tax):
        ncbi = NCBITaxa()
        tax_id = ncbi.get_name_translator([taxonomy])
        if taxonomy in tax_id:
            tax_id = tax_id[taxonomy][0]
        else:
            return
        for tax_ in reversed(record_tax + [genus, organism]):
            query_id = ncbi.get_name_translator([tax_])
            if tax_ in query_id:
                if len(query_id[tax_]) == 1:
                    id = query_id[tax_][0]
                else:
                    # 分类名对应了多个id的情况，如{'Brachycladium': [570638, 630351]}
                    dict_id_lineages = {}
                    for id_ in query_id[tax_]:
                        dict_id_lineages[id_] = self.get_lineages(id_)
                    # 哪个lineage和物种本身的lineage交集多，就用哪个id
                    max_inter = 0
                    for temp_id in dict_id_lineages:
                        inter_num = len(list(set(record_tax).intersection(dict_id_lineages[temp_id])))
                        # print(temp_id, inter_num)
                        if inter_num >= max_inter:
                            max_inter = inter_num
                            id = temp_id
                lineage_ids = ncbi.get_lineage(id)
                return tax_id in lineage_ids
        self.tax_error_ids.append([ID, organism, str(record_tax)])
        return

    def get_lineages(self, query_id):
        ncbi = NCBITaxa()
        # query_id = ncbi.get_name_translator([tax_])[tax_][0]
        lineage_ids = ncbi.get_lineage(query_id)
        dict_id_rank = ncbi.get_rank(lineage_ids)
        dict_id_name = ncbi.get_taxid_translator(lineage_ids)
        # print(dict_id_rank)
        # print({dict_id_name[id]: dict_id_rank[id] for id in dict_id_name})
        return list(dict_id_name.values())

    def updateLineageOfAllWorDir(self):
        requiredTaxonomy = self.factory.getCurrentTaxSetData()[0]
        array = self.fetchAvailableInfo()
        # 更新lineage
        array[1][1] = requiredTaxonomy
        name = re.sub(r"/|\\", "_", self.filePath) + "_availableInfo"
        self.data_settings.setValue(name, array)  # lineage settings里面的

    def saveArray(self, array):
        name = re.sub(r"/|\\", "_", self.filePath) + "_displayedArray"
        self.data_settings.setValue(name, array)  # 界面展示的，header+array

    def highlightRepeatIDs(self):
        allIndex = self.fetchAllIndex()
        dict_seq_IDs = {}
        for ID in allIndex:
            gb_record = allIndex[ID]
            dict_seq_IDs.setdefault(str(gb_record.seq), []).append(ID)
        dict_gb_color = OrderedDict()
        self.colours = []
        self.default_color = ["#00FFFF", "#FF7F00", "#9932CD", "#871F78", "#238E23",
                              "#7F00FF", "#3232CD", "#BC1717", "#FF0000", "#0000FF", "#00FF00", "#FF00FF"]
        list_repeat_index = [dict_seq_IDs[j]
                             for j in dict_seq_IDs if
                             len(dict_seq_IDs[j]) > 1]  # [[MF187612, KR013001], [GU130256, KX289584]]
        for k in list_repeat_index:
            color = self.colourPicker()
            for l in k:
                dict_gb_color[l] = color
        return dict_gb_color, list_repeat_index  # {"MF187612":"red"}

    def prepareGB(self, genbanks, base=None, proportion=None, processSig=None, byContent=False):
        ##删除导入序列的一样的ID，并得到与已有序列一样的ID, 并且只留下符合要求的gb文件
        '''[(all_ID_content, 'NC_021145', '     NC_021145.1', 'NC_021145.1'),(all_ID_content,'NC_021142', '', '')]'''
        try:
            all_gb_content = self.merge_file_contents(genbanks) if not byContent else genbanks
            rgx = re.compile(r"(?sm)(LOCUS {7}(\S+).+?^//\s*?(?=LOCUS|$))")
            list_Names = []
            all_content = ""
            exsistIndex = self.fetchAllIndex()
            exsistIDs = list(exsistIndex.keys())
            repeatIDs = []
            newIDs = []
            list_gbRecords = []
            New_gbRecords = []
            list_rgx_contents = rgx.findall(all_gb_content)
            total = len(list_rgx_contents)
            error_contents = ""
            for num, each_content in enumerate(list_rgx_contents):
                try:
                    gb_content = each_content[0]
                    name = each_content[-1]
                    if name not in list_Names:
                        ##替换长名字，LOCUS       Ichthyoxenus_japonensis15440 bp    DNA
                        if re.search(r"(?m)^LOCUS {7}(\S+?) bp", gb_content):
                            large_name = re.search(r"(?m)^LOCUS {7}(\S+?) bp", gb_content).group(1)
                            length = re.search(r"source +\d+\.\.(\d+)\n", gb_content).group(1)
                            new_name = large_name.strip(length)[:7] + "_" + large_name.strip(length)[-7:] + " " * 8 + "%s" % length
                            gb_content = gb_content.replace(large_name, new_name)
                        elif len(name) > 15:
                            ##替换超过15个字符的长名字
                            new_name = name[:7] + "_" + name[-7:]
                            gb_content = gb_content.replace(name, new_name)
                        ##替换不标准的REFERENCE注释
                        rgx_ref = re.compile(r"(?sm)((^REFERENCE[^\(]+?\([^\(]+?\)\n)^ {3,}(\w+?[^\n]+?\n))")
                        # 匹配：[('REFERENCE   2  (bases 1 to 15441)\n            CONSRTM   NCBI Genome Project\n', 'REFERENCE   2  (bases 1 to 15441)\n', 'CONSRTM   NCBI Genome Project\n')]
                        if rgx_ref.search(gb_content):
                            for i in rgx_ref.findall(gb_content):
                                whole, reference, subContent = i #rgx_ref.findall(gb_content)[0]
                                gb_content = gb_content.replace(whole, reference + "  " + subContent)
                        ###替换缩进
                        gb_content = gb_content.replace("\t", "    ")
                        ###替換不標準的comment
                        gb_content = re.sub(r"(?sm)(##[^#]+##)(.+?)(##[^#]+##)",
                                            lambda x: x.group(1) +
                                                      x.group(2).replace(":", " ::") +
                                                      x.group(3), gb_content)
                        ###保存
                        gb_handle = StringIO(gb_content)
                        gb_record = next(self.merge_gbRecords([gb_handle], byHandle=True))  # 由于只有1个record，所以可以这样获取
                        ID = gb_record.id
                        all_content += gb_content + "\n\n"
                        list_Names.append(name)
                        list_gbRecords.append(gb_record)
                        ##check repeat
                        if ID in exsistIDs:
                            repeatIDs.append(ID)
                        else:
                            newIDs.append(ID)
                            New_gbRecords.append(gb_record)
                except:
                    error_contents += ''.join(
                        traceback.format_exception(*sys.exc_info())) + "\n"
                    # print(errorInfo)
                    error_contents += gb_content + "\n\n"
                ##进度条
                if processSig:
                    num += 1
                    processSig.emit(base + (num / total) * proportion)
            if error_contents:
                self.exception_signal.emit(error_contents + "partial GenBank file failed")
            return all_content, list_gbRecords, New_gbRecords, repeatIDs, newIDs
        except:
            errorInfo = ''.join(
                traceback.format_exception(*sys.exc_info())) + "\n"
            self.exception_signal.emit(errorInfo + "GenBank file parse failed")

    # def delete_file_records(self, file, IDs, byContent=False):
    #     ###
    #     if byContent:
    #         file_content = file
    #         for ID in IDs:
    #             rgx = re.compile(r"(?sm)LOCUS {7}%s.+?^//\s*?(?=LOCUS|$)" % ID.split(".")[0])
    #             file_content = rgx.sub("", file_content)
    #         return StringIO(file_content)
    #     else:
    #         # 删除指定文件里面的records
    #         with open(file, encoding="utf-8") as f:
    #             file_content = f.read()
    #         for ID in IDs:
    #             rgx = re.compile(r"(?sm)LOCUS {7}%s.+?^//\s*?(?=LOCUS|$)" % ID.split(".")[0])
    #             file_content = rgx.sub("", file_content)
    #         with open(file, "w", encoding="utf-8") as f1:
    #             f1.write(file_content)
    #     return

    def addRecordsSubFunc(self, gb_records, totleLen, base, proportion, processSig):
        '''addRecords的亚函数,新加入序列'''
        try:
            array = self.fetch_array()
            requiredInfos = array[0]
            list_added_records = []
            for num, gb_record in enumerate(gb_records):
                ID = gb_record.id
                ##新增注释
                source_feature = self.fetch_source_feature(gb_record)
                if "User_Note" not in source_feature.qualifiers:
                    source_feature.qualifiers["User_Note"] = ""
                if "taxonomy" not in gb_record.annotations: gb_record.annotations["taxonomy"] = ["taxonomy"]
                taxonomy = gb_record.annotations["taxonomy"]
                if "organism" not in gb_record.annotations: gb_record.annotations["organism"] = "organism name"
                organism = gb_record.annotations["organism"]
                dict_lineages = self.fetchLineages(taxonomy, organism, source_feature)
                for lineage in dict_lineages:
                    source_feature.qualifiers[lineage] = dict_lineages[lineage]
                ###存序列
                SeqIO.write(gb_record, self.fetchRecordPath(ID), "genbank")
                list_added_records.append(gb_record)
                ###提取需要的信息
                gb_record_array = self.extractRequiredInfo(gb_record, requiredInfos)
                # gb_record_array.append(str(gb_record.seq))
                array.append(gb_record_array)
                # self.list_Names.append(ID)
                if processSig:
                    num += 1
                    processSig.emit(base + (num / totleLen) * (9 / 10) * proportion)
            # 这样更新才能把最新的信息更新进去
            if processSig:
                self.updateAvailableInfo(list_added_records, base + (91 / 100) * proportion, (9 / 100) * proportion,
                                         processSig)
            else:
                self.updateAvailableInfo(list_added_records)
            self.saveArray(array)
        except:
            try:
                if os.path.exists(self.fetchRecordPath(ID)):
                    ##把报错这个序列删掉
                    os.remove(self.fetchRecordPath(ID))
            except:
                pass
            errorInfo = ''.join(
                traceback.format_exception(*sys.exc_info())) + "\n"
            self.exception_signal.emit(errorInfo + "GenBank file parse failed")
            return None
            ##先清空这个文件夹，免得后续再报错。
            # self.factory.remove_dir(self.filePath + os.sep + ".data")

    def addRecords(self, list_gbPath, base, proportion, processSig, parent, byContent=False):
        '''base是已经有多少proportion了
        proportion是还需要多少proportion'''
        list_ = self.prepareGB(list_gbPath, 0,
                               (1 / 10) * proportion,
                               processSig,
                               byContent=byContent)  ##删除一样的ID以及标准化gb内容，避免后续报错
        # if self.interrupt: return
        if not list_: return
        gb_Contents, self.list_gbRecords, self.New_gbRecords, self.repeatIDs, self.newIDs = list_
        ###得到需要提取的信息### ##此时矩阵已经生成了，在进入这个工作区的时候
        if self.repeatIDs:
            ###这个方法可以在子线程block代码，等其他线程的东西执行完以后再继续
            if len(self.repeatIDs) > 10:
                repeatIDs = self.repeatIDs[:10]
                text = ", ".join(repeatIDs) + " (and %d more)"%(len(self.repeatIDs) - 10)
            else:
                text = ", ".join(self.repeatIDs)
            replace_repeat = QMetaObject.invokeMethod(self, "popupMessage",
                                Qt.BlockingQueuedConnection, Q_RETURN_ARG(bool),
                                Q_ARG(list, [self.parent, "<p style='line-height:25px; height:25px'>%s already exist,"
                                            " replace them?</p>" % text, "question"]))
            if replace_repeat:
                ##先删除记录
                self.deleteRecords(self.repeatIDs)
                # if self.interrupt: return
                self.addRecordsSubFunc(self.list_gbRecords, len(self.repeatIDs + self.newIDs), base + (1 / 10) * proportion,
                                       (9 / 10) * proportion, processSig)
                # if self.interrupt: return
            else:
                # 只提取新加入的ID
                if self.newIDs:
                    self.addRecordsSubFunc(self.New_gbRecords, len(self.newIDs), base + (1 / 10) * proportion,
                                           (9 / 10) * proportion,
                                           processSig)
        else:
            # 所有记录都加入
            self.addRecordsSubFunc(self.list_gbRecords, len(self.repeatIDs + self.newIDs), base + (1 / 10) * proportion,
                                   (9 / 10) * proportion,
                                   processSig)

    def modifyRecords(self, newArray, row, column):
        ##待完善，某些可以修改的项目加上
        header = newArray[0]
        data = newArray[1:]
        ID = data[row][0]
        new_text = data[row][column]
        # print("ID: %s, new text: %s"%(ID, new_text))
        gbPath = self.fetchRecordPath(ID)
        gb_record = SeqIO.read(gbPath, "genbank")
        # gb_record.
        header_title = header[column]
        ###用于判断各个信息属于哪一类###
        name = re.sub(r"/|\\", "_", self.filePath) + "_availableInfo"
        arrar4tree = self.data_settings.value(name, [])
        ###得到键和信息名字的映射关系###
        name_key_mapping = self.fetch_name_key_mapping()
        # print(ID, new_text, header_title, row, column, arrar4tree[0][1])
        ##修改矩阵##
        self.saveArray(newArray)
        # print(arrar4tree)
        if header_title == "Definition":
            gb_record.description = new_text
        elif header_title == "Name":
            gb_record.name = new_text
        elif header_title in arrar4tree[0][1]:
            # Annotations，仅仅可以改organism，通过header_title来控制
            annotation_key = name_key_mapping[header_title] if header_title in name_key_mapping else header_title
            gb_record.annotations[annotation_key] = new_text
        elif (header_title in arrar4tree[1][1]) or (header_title in arrar4tree[3][1]):
            # Lineages与Sources合并了
            ###得到source注释###
            source_feature = self.fetch_source_feature(gb_record)
            source_feature.qualifiers[header_title] = [new_text]
            # print("Lineages and Sources", ID, header_title, new_text)
            # message = "\n".join([": ".join([i, source_feature.qualifiers[i][0]]) for i in source_feature.qualifiers])
            # QMessageBox.information(None,
            #     "PhyloSuite",
            #     "source after modified:\n %s"%message,
            #     QMessageBox.Yes,
            #     QMessageBox.Cancel)
            # print("source after modified: ", source_feature.qualifiers)
        SeqIO.write(gb_record, gbPath, "genbank")
        self.parent.modify_table_finished.emit()

    def deleteRecords(self, IDs, base=None, proportion=None, processSig=None):
        try:
            ##先删除矩阵
            arrayManager = ArrayManager(self.fetch_array())
            if processSig:
                array = arrayManager.remove_by_row_IDs(IDs, base, (90 / 100) * proportion, processSig)
            else:
                array = arrayManager.remove_by_row_IDs(IDs)
            self.saveArray(array)
            ##删除文件
            for ID in IDs:
                if os.path.exists(self.fetchRecordPath(ID)):
                    os.remove(self.fetchRecordPath(ID))
            # 删除以后，要更新一下可以展示的信息
            allGBpath = self.fetchAllGBpath()
            if processSig:
                self.updateAvailableInfo_2(allGBpath, base + (90 / 100) * proportion, (10 / 100) * proportion, processSig)
            else:
                self.updateAvailableInfo_2(allGBpath)
            return array
        except:
            errorInfo = ''.join(
                traceback.format_exception(*sys.exc_info())) + "\n"
            self.exception_signal.emit(errorInfo)

    def colourPicker(self):
        # 生成不重复的随机颜色
        if self.default_color:
            colour = self.default_color.pop()
        else:
            colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
            while colour in self.colours:
                colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
        self.colours.append(colour)
        return colour

    def isValidGB(self, contents):
        rgx = re.compile(r"(?sm)(LOCUS {7}(\S+).+?^//\s*?(?=LOCUS|$))")
        return rgx.search(contents)

    @pyqtSlot(list, result=bool)
    def popupMessage(self, args):
        parent, message, type = args
        if type == "question":
            reply = QMessageBox.question(
                parent,
                "PhyloSuite",
                message,
                QMessageBox.Yes,
                QMessageBox.Cancel)
        elif type == "information":
            reply = QMessageBox.information(
                parent,
                "PhyloSuite",
                message,
                QMessageBox.Yes,
                QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            return True
        else:
            return False

    def get_tax_id(self, query_name):
        """to get data from ncbi taxomomy, we need to have the taxid. we can
        get that by passing the species name to esearch, which will return
        the tax id"""
        query_name = query_name.replace(' ', "+").strip()
        Entrez.email = 'A.N.Other@example.com'
        search = Entrez.esearch(term=query_name, db="taxonomy", retmode="xml")
        record = Entrez.read(search)
        return record['IdList'][0] if record['IdList'] else None

    def get_tax_data(self, taxid):
        """once we have the taxid, we can fetch the record"""
        Entrez.email = 'A.N.Other@example.com'
        search = Entrez.efetch(id=taxid, db="taxonomy", retmode="xml")
        return Entrez.read(search)

    def get_key_in_source(self, upperName, qualifiers):
        for i in qualifiers:
            if i.upper() == upperName:
                return i
        return None

    def update_NCBI_lineages(self, LineageNames, query_name, source_feature, record_tax):
        '''
        :todo: there maybe many ids in dict_name_id, how to choose?
        :param LineageNames:
        :param query_name:
        :param source_feature:
        :return: source_feature
        '''
        LineageNames = [i.upper() for i in LineageNames]
        db_file = f"{self.thisPath}{os.sep}db{os.sep}NCBI{os.sep}taxa.sqlite"
        db_path = f"{self.thisPath}{os.sep}db{os.sep}NCBI"
        ncbi = NCBITaxa(dbfile=db_file,
                        taxdump_file=None,
                        taxdump_path=db_path)
        dict_name_id = ncbi.get_name_translator([query_name])
        # print(query_name, dict_name_id)
        if dict_name_id:
            if len(dict_name_id[query_name]) == 1:
                query_id = dict_name_id[query_name][0]
            else:
                # 分类名对应了多个id的情况，如{'Brachycladium': [570638, 630351]}
                dict_id_lineages = {}
                for id_ in dict_name_id[query_name]:
                    dict_id_lineages[id_] = self.get_lineages(id_)
                # 哪个lineage和物种本身的lineage交集多，就用哪个id
                max_inter = 0
                for temp_id in dict_id_lineages:
                    inter_num = len(list(set(record_tax).intersection(dict_id_lineages[temp_id])))
                    # print(temp_id, inter_num)
                    if inter_num >= max_inter:
                        max_inter = inter_num
                        query_id = temp_id
            lineage_ids = ncbi.get_lineage(query_id)
            dict_id_rank = ncbi.get_rank(lineage_ids)
            # print(query_name, lineage_ids, dict_id_rank)
            source_qualifiers = list(source_feature.qualifiers.keys())
            for id in dict_id_rank:
                if dict_id_rank[id].upper() in LineageNames:
                    key = self.get_key_in_source(dict_id_rank[id].upper(), source_qualifiers)
                    if key:
                        source_feature.qualifiers[key] = ncbi.get_taxid_translator([id])[id]
        # tax_id = self.get_tax_id(query_name)
        # if tax_id: #有时候有些名字不能被识别，就是None
        #     data = self.get_tax_data(tax_id)
        #     LineageNames = [i.upper() for i in LineageNames]
        #     source_qualifiers = list(source_feature.qualifiers.keys())
        #     for d in data[0]['LineageEx']:
        #         if d['Rank'].upper() in LineageNames:
        #             key = self.get_key_in_source(d['Rank'].upper(), source_qualifiers)
        #             if key:
        #                 source_feature.qualifiers[key] = d['ScientificName']
        return source_feature

    def update_WoRMS_lineages(self, LineageNames, query_name, source_feature):
        cl = Client('http://www.marinespecies.org/aphia.php?p=soap&wsdl=1')
        scinames = cl.factory.create('scientificnames')
        scinames["_arrayType"] = "string[]"
        scinames["scientificname"] = [query_name]
        array_of_results_array = cl.service.matchAphiaRecordsByNames(scinames, like="true", fuzzy="true",
                                                                     marine_only="false")
        # 有时一个名字会搜出来几个，存在列表中[[<suds.sudsobject.AphiaRecord object at 0x0000000003EF35C0>, <suds.sudsobject.AphiaRecord object at 0x0000000003EF34E0>], [<suds.sudsobject.AphiaRecord object at 0x0000000003EF3748>]]
        if not array_of_results_array[0]:
            ##没搜到就直接返回
            return source_feature
        aphia_object = array_of_results_array[0][0]
        for lineage in LineageNames:
            tax_name = lineage.lower() if lineage.lower() != "class" else "cls"
            if hasattr(aphia_object, tax_name):
                exec("source_feature.qualifiers[lineage] = aphia_object.%s"%tax_name)
        return source_feature

    def reorder(self, list_IDs, base, proportion, processSig, target=None, start=None, warning_signal=None):
        ###提取的设置
        self.GenBankExtract_settings = QSettings(
            self.thisPath + '/settings/GenBankExtract_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.GenBankExtract_settings.setFallbacksEnabled(False)
        self.dict_gbExtract_set = self.GenBankExtract_settings.value("set_version")
        listGB_paths = [self.fetchRecordPath(ID) for ID in list_IDs]
        total = len(listGB_paths)
        has_send_warning = False
        for num, file_path in enumerate(listGB_paths):
            try:
                new_record = None
                gb = SeqIO.parse(file_path, "genbank")
                gb_record = next(gb)
                features = gb_record.features
                if target:
                    # 如果不是指定的起始位置
                    for feature in features:
                        # 得到qualifiers
                        key = "Qualifiers to be recognized (%s):" % feature.type
                        included_qualifiers = self.dict_gbExtract_set[key] if key in self.dict_gbExtract_set \
                            else ["product", "gene", "note"]
                        name = None
                        for i in included_qualifiers:
                            if i in feature.qualifiers:
                                name = feature.qualifiers[i][0]
                                break
                        if name == target:
                            start = int(feature.location.start) + 1
                            break
                    if start:
                        new_record = gb_record[start - 1:] + gb_record[:start - 1]
                        new_record.dbxrefs = gb_record.dbxrefs[:]
                        new_record.annotations = gb_record.annotations.copy()
                        ##加上source
                        new_record.features.insert(0, gb_record.features[0])
                elif start:
                    # 指定起始位置
                    start_positions = [int(feature_.location.start) + 1 for feature_ in features]
                    if start in start_positions:
                        new_record = gb_record[start - 1:] + gb_record[:start - 1]
                        new_record.dbxrefs = gb_record.dbxrefs[:]
                        new_record.annotations = gb_record.annotations.copy()
                        ##加上source
                        new_record.features.insert(0, gb_record.features[0])
                    else:
                        if not has_send_warning:
                            warning_signal.emit("Selected position must correspond to a start position of a gene!")
                            has_send_warning = True
                            # 给个提示
                if new_record: SeqIO.write(new_record, file_path, "genbank")
                processSig.emit(base + ((num+1)/total)*proportion)
            except: pass


class GBextract(object):
    def __init__(self, **dict_args):
        super(GBextract, self).__init__()
        self.factory = Factory()
        self.dict_args = dict_args

    def init_args_all(self):
        '''
        gb_files: all GenBank files
        dict_replace: 用户设置的替换基因名字的信息
        included_features： 所有需要提取的features
        name_contents: 输出时的物种名的情况
        included_lineages： 需要包括的分类群信息
        exportPath： 输出文件夹名
        input_file： 保存提取的GenBank原始文件
        extract_list_gene： 只提取列出来的这些基因
        selected_code_table： 用户选择的密码表
        progressSig： 发送提取进度的信号
        totleID： 总共有多少个序列
        absence： 用于记录没有提取到的ID
        unextract_name： 提取指定基因模式，未提取的基因列出来
        taxonomy_infos： 记录分类群信息
        Error_ID： 报错的ID
        dict_feature_fas： 存放feature及其所有序列
        dict_name_replace： 存放基因名及其替换后的名字
        dict_itol_name： {used name： 物种名}
        dict_itol_gb: {used name： ID}
        list_none_feature_IDs： 没有找到feature的ID
        list_features： 记录有哪些feature
        dict_gene_names： {基因名： [used name]}
        list_used_names: [used name]
        source_feature_IDs: 记录只有source这一个feature的ID
        dict_pairwise_features： 用于寻找非编码区
        dict_NCR_regions、dict_NCR_regions： 用于统计非编码区和重叠区
        dict_pro： 存放PCGs的fas序列
        dict_PCG： 存放PCGs的长度信息，生成geneStat.csv
        dict_start： 存放PCGs的起始密码子信息，生成geneStat.csv
        dict_stop： 存放PCGs的终止密码子信息，生成geneStat.csv
        dict_AA: 存放PCGs的fas序列（AA）
        PCGsCodonSkew： 所有PCGs的skew
        firstCodonSkew： 1密码子位点的skew
        secondCodonSkew: 2密码子位点的skew
        thirdCodonSkew： 3密码子位点的skew
        firstSecondCodonSkew: 1\2密码子位点的skew
        dict_RSCU：存放RSCU表
        dict_RSCU_stack： 存放RSCU stack的结果
        dict_AAusage： 存放AA使用情况信息
        dict_all_spe_RSCU： 存放所有物种的RSCU
        dict_all_codon_COUNT： 存放所有物种codon统计的信息
        dict_all_AA_RATIO： 存放所有物种AA比率
        dict_all_AA_COUNT： 存放所有物种AA的统计信息
        dict_AA_stack： 存放所有物种AA的stack
        dict_rRNA： 存放rRNA的fas序列
        dict_RNA： 存放rRNA的长度信息
        dict_tRNA： 存放tRNA的fas序列
        dict_spe_stat： 单个物种的统计表
        dict_orgTable: 单个物种的组成表
        list_name_gb： [(物种名， ID)]
        dict_order: 存放基因顺序
        gene_order： 每个物种的基因顺序
        complete_seq： 整个序列的fas
        PCG_seq: PCGs的fas，去除不标准终止密码子后的
        tRNA_seqs: tRNA的fas
        rRNA_seqs: rRNA的fas
        dict_geom_seq: {id: 序列}
        name_gb: 生成gbAccNum.csv
        dict_all_stat: 生成 used_species.csv
        species_info: 生成species_info.csv文件
        line_spe_stat： 生成data_for_plot.csv
        codon_bias： 生成codon_bias.csv
        list_all_taxonmy: 存放所有分类群的信息
        dict_gene_ATskews： 各基因的ATskew，生成geneStat.csv
        dict_gene_GCskews： 各基因GCskew，生成geneStat.csv
        dict_gene_ATCont： 各基因AT含量，生成geneStat.csv
        dict_gene_GCCont： 各基因GC含量，生成geneStat.csv
        # map ID and tree name
        dict_ID_treeName： {ID： used name}
        '''
        self.gb_files = self.dict_args["gb_files"]
        self.dict_replace = self.dict_args["replace"]
        self.included_features = self.dict_args["features"]
        self.dict_qualifiers = self.dict_args[
            "qualifiers"]  # OrderedDict([('Qualifiers to be recognized (rRNA):', ['gene', 'product'])])
        self.name_contents = self.dict_args["Name Type"]
        self.included_lineages = self.dict_args["included_lineages"]
        self.exportPath = self.dict_args["exportPath"]
        ##存放输入文件
        if os.path.exists(self.exportPath + os.sep + 'input.gb'):
            try:
                os.remove(self.exportPath + os.sep + 'input.gb')
            except:
                pass
        self.input_file = open(self.exportPath + os.sep + 'input.gb', 'a', encoding="utf-8")
        self.extract_list_gene = self.dict_args["extract_list_gene"]
        self.selected_code_table = int(self.dict_args["codon"]) #如果注释里面没找到，就用这个
        self.code_table = self.selected_code_table
        # self.fetchTerCodon()
        if self.extract_list_gene:
            ##只提取指定基因
            self.all_list_gene = list(set(self.dict_replace.keys()).union(set(self.dict_replace.values())))
        # 信号
        self.progressSig = self.dict_args["progressSig"]
        self.totleID = self.dict_args["totleID"]
        ###初始化各个属性###
        self.absence = ['="ID",Organism,Feature,Strand,Start,Stop']
        #只提取指定基因模式，把未提取的基因列出来
        self.unextract_name = ["This is the list of names not included in the 'Names unification' "
                               "table\n=\"ID\",Organism,Feature,Name,Strand,Start,Stop"]
        self.taxonomy_infos = ['Tree name,ID,Organism,{}\n'.format(
            ",".join(self.included_lineages))]
        self.Error_ID = []
        self.dict_feature_fas = OrderedDict()
        self.dict_name_replace = OrderedDict()
        self.dict_itol_name = OrderedDict()
        self.dict_itol_gb = OrderedDict()
        ####itol###
        #         基因组长度条形图
        self.itolLength = ["DATASET_SIMPLEBAR\nSEPARATOR COMMA\nDATASET_LABEL,genome length bar\nCOLOR,#ffff00\n" \
                          "WIDTH,1000\nMARGIN,0\nHEIGHT_FACTOR,0.7\nBAR_SHIFT,0\nBAR_ZERO,12000\nDATA\n"]
        #         基因组AT含量条形图
        self.itolAT = ["DATASET_SIMPLEBAR\nSEPARATOR COMMA\nDATASET_LABEL,AT content bar\nCOLOR,#ffff00\nWIDTH,1000\n"
                       "MARGIN,0\nHEIGHT_FACTOR,0.7\nBAR_SHIFT,0\nBAR_ZERO,50\nDATA\n"]
        #         基因组GC skew条形图
        self.itolGCskew = ["DATASET_SIMPLEBAR\nSEPARATOR COMMA\nDATASET_LABEL,GC skew bar\nCOLOR,#ffff00\nWIDTH,1000\n"
                           "MARGIN,0\nHEIGHT_FACTOR,0.7\nBAR_SHIFT,0\nBAR_ZERO,0\nDATA\n"]
        #         基因组ATCG数量堆积图
        self.itolLength_stack = ["DATASET_MULTIBAR\nSEPARATOR COMMA\nDATASET_LABEL,ATCG multi bar chart\nCOLOR,#ff0000\n" \
                                "WIDTH,1000\nMARGIN,0\nSHOW_INTERNAL,0\nHEIGHT_FACTOR,0.7\nBAR_SHIFT,0\nALIGN_FIELDS,0\n" \
                                "FIELD_LABELS,A,T,C,G\nFIELD_COLORS,#2a9087,#5c2936,#913e40,#2366a1\nDATA\n"]
        self.colours = []
        # 存itol的各种文件
        self.dict_itol_info = OrderedDict()
        for lineage in self.included_lineages:
            for num, item in enumerate(
                    ["Colour", "Text", "ColourStrip", "ColourRange", "colourUsed1", "colourUsed2"]):
                if num == 0:
                    self.dict_itol_info["itol_%s_%s" % (
                        lineage, item)] = ["TREE_COLORS\nSEPARATOR COMMA\nDATA\n"]
                elif num == 1:
                    self.dict_itol_info["itol_%s_%s" % (
                        lineage,
                        item)] = ["DATASET_TEXT\nSEPARATOR COMMA\nDATASET_LABEL,%s text\nCOLOR,#ff0000\nMARGIN,0\n"
                                  "SHOW_INTERNAL,0\nLABEL_ROTATION,0\nALIGN_TO_TREE,0\nSIZE_FACTOR,1\nDATA\n" % lineage]
                elif num == 2:
                    self.dict_itol_info["itol_%s_%s" % (
                        lineage,
                        item)] = ["DATASET_COLORSTRIP\nSEPARATOR SPACE\nDATASET_LABEL color_strip\nCOLOR #ff0000\n" 
                                 "COLOR_BRANCHES 1\nSTRIP_WIDTH 25\nLEGEND_TITLE,None\nLEGEND_SHAPES\nLEGEND_COLORS\n" 
                                 "LEGEND_LABELS\nDATA\n"]
                elif num == 3:
                    self.dict_itol_info["itol_%s_%s" % (
                        lineage, item)] = ["TREE_COLORS\nSEPARATOR COMMA\nDATA\n"]
                elif num == 4:
                    self.dict_itol_info["itol_%s_%s" % (
                        lineage, item)] = OrderedDict()
                elif num == 5:
                    self.dict_itol_info["itol_%s_%s" % (
                        lineage, item)] = OrderedDict()
        self.list_none_feature_IDs = []
        self.list_features = []
        self.dict_gene_names = OrderedDict()
        self.list_used_names = []
        ##统计有错误的ID
        self.source_feature_IDs = []
        ##用于寻找非编码区
        self.dict_pairwise_features = {
            "last_end": None,
            "last_name": None,
            "now_ini": None,
            "now_name": None,
            "last_end_temp": None
        }
        ## 用于统计非编码区和重叠区
        self.dict_NCR_regions = OrderedDict()
        self.dict_overlapping_regions = OrderedDict()

        ## 新增分析及统计
        self.dict_pro = {}
        self.dict_AA = OrderedDict()
        self.dict_rRNA = {}
        self.dict_tRNA = {}
        self.dict_start = {}
        self.dict_stop = {}
        self.dict_PCG = {}
        self.dict_RNA = {}
        self.dict_spe_stat = {}
        self.list_name_gb = []
        # self.linear_order = ''
        self.dict_order = {}
        self.complete_seq = []
        self.dict_geom_seq = {}
        self.name_gb = ["Species name,Accession number"]  # 名字和gb num对照表
        # 保存没有注释好的L和S
        self.leu_ser = []
        #         skewness
        self.PCGsCodonSkew = ["Tree_name,species,Strand,AT skew,GC skew," +
                             ",".join(self.included_lineages) + "\n"]
        self.firstCodonSkew = ["Tree_name,species,Strand,AT skew,GC skew," +
                              ",".join(self.included_lineages) + "\n"]
        self.secondCodonSkew = ["Tree_name,species,Strand,AT skew,GC skew," +
                               ",".join(self.included_lineages) + "\n"]
        self.thirdCodonSkew = ["Tree_name,species,Strand,AT skew,GC skew," +
                              ",".join(self.included_lineages) + "\n"]
        self.firstSecondCodonSkew = ["Tree_name,species,Strand,AT skew,GC skew," +
                                    ",".join(self.included_lineages) + "\n"]
        #         统计图
        self.dict_all_stat = OrderedDict()
        #         PCG的串联序列
        self.PCG_seq = []
        self.tRNA_seqs = []
        self.rRNA_seqs = []
        #         新增统计物种组成表功能
        self.dict_orgTable = OrderedDict()
        # 新增RSCU相关
        self.dict_RSCU = OrderedDict()  # RSCU table
        self.dict_RSCU_stack = OrderedDict()
        self.dict_AAusage = OrderedDict()
        self.dict_all_spe_RSCU = OrderedDict()
        self.dict_all_spe_RSCU["title"] = ["codon"]
        self.dict_all_codon_COUNT = OrderedDict()
        self.dict_all_codon_COUNT["title"] = ["codon"]
        self.dict_all_AA_RATIO = OrderedDict()
        self.dict_all_AA_RATIO["title"] = ["AA"]
        self.dict_all_AA_COUNT = OrderedDict()
        self.dict_all_AA_COUNT["title"] = ["AA"]
        self.dict_AA_stack = OrderedDict()
        self.dict_AA_stack["title"] = ["species,aa,ratio"]
        self.species_info = [
                            ["ID", "Organism", "Tree_Name"] + self.included_lineages + ["Code table"] + \
                            ["Full length (bp)", "Coding region length (exclude NCR)", "GC skew (plus strand coding)",
                             "GC skew (plus strand genes only)", "GC skew (fourfold degenerate sites)",
                             "GC skew (fourfold degenerate sites on plus strand)", "GC skew (all NCR)", "NCR ratio"] + \
                             (["A (%) (+)"] if self.dict_args["analyze + sequence"] else ["A (%)"]) + \
                             (["T (%) (+)"] if self.dict_args["analyze + sequence"] else ["T (%)"]) + \
                             (["C (%) (+)"] if self.dict_args["analyze + sequence"] else ["C (%)"]) + \
                             (["G (%) (+)"] if self.dict_args["analyze + sequence"] else ["G (%)"]) + \
                             (["A+T (%) (+)"] if self.dict_args["analyze + sequence"] else ["A+T (%)"]) + \
                            (["G+C (%) (+)"] if self.dict_args["analyze + sequence"] else ["G+C (%)"]) + \
                            (["G+T (%) (+)"] if self.dict_args["analyze + sequence"] else ["G+T (%)"]) + \
                            (["AT skew (+)"] if self.dict_args["analyze + sequence"] else ["AT skew"]) + \
                             (["GC skew (+)"] if self.dict_args["analyze + sequence"] else ["GC skew"]) + \
                             (["AT skew (-)"] if self.dict_args["analyze - sequence"] else []) + \
                             (["GC skew (-)"] if self.dict_args["analyze - sequence"] else [])
                             ]
        # 新增折线图的绘制
        self.line_spe_stat = ["Regions,Strand,Size (bp),T(U),C,A,G,AT(%),GC(%),GT(%)," \
                                "AT skewness,GC skewness,ID,Species," + ",".join(
                                    list(reversed(self.included_lineages))) + "\n"]
        # 密码子偏倚分析
        self.codon_bias = ["Tree_name,Genes,GC1,GC2,GC12,GC3,CAI,CBI,Fop,ENC,L_sym,L_aa,Gravy,Aromo,Species," + ",".join(
            list(reversed(self.included_lineages))) + "\n"]
        self.list_all_taxonmy = []  # [[genus1, family1], [genus2, family2]]
        self.dict_gene_ATskews = {}
        self.dict_gene_GCskews = {}
        self.dict_gene_ATCont = {}
        self.dict_gene_GCCont = {}
        # map ID and tree name
        self.dict_ID_treeName = {}
        # save gene names of each type
        self.PCGs_names = []
        self.rRNA_names = []
        self.tRNA_names = []
        # save all sequences
        self.gb2fas = OrderedDict()
        # NCR ratio
        self.NCR_features = self.dict_args["NCR_features"]
        self.cal_NCR_ratio = self.dict_args["cal_NCR_ratio"]

    def init_args_each(self):
        '''
        PCGs_strim： 各物种的PCGs序列，去除不标准的终止密码子的
        PCGs_strim_plus：正链——各物种的PCGs序列，去除不标准的终止密码子的
        PCGs_strim_minus： 负链——各物种的PCGs序列，去除不标准的终止密码子的
        tRNAs： 各物种tRNAs序列
        tRNAs_plus： 正链——各物种tRNAs序列
        tRNAs_minus: 负链——各物种tRNAs序列
        rRNAs: 各物种rRNAs序列
        rRNAs_plus: 正链——各物种rRNAs序列
        rRNAs_minus: 负链——各物种rRNAs序列
        NCR_seq: 存放所有非编码的序列
        dict_genes: 存放基因的各种统计信息
        orgTable： 刷新组成表的表头
        lastEndIndex:0
        overlap, gap:0, 0
        dict_repeat_name_num: 存放一些带有重复名字的
        list_feature_pos: 索引列表，用于统计NCR ratio # [0,1,2,3,4,...]
        :return:
        '''
        self.PCGs_strim = []
        self.PCGs_strim_plus = []
        self.PCGs_strim_minus = []
        self.tRNAs = []
        self.tRNAs_plus = []
        self.tRNAs_minus = []
        self.rRNAs = []
        self.rRNAs_plus = []
        self.rRNAs_minus = []
        self.NCR_seq = []
        self.dict_genes = {}
        self.dict_geom_seq[self.ID] = self.str_seq
        self.list_name_gb.append((self.organism, self.ID))
        self.name_gb.append(self.organism + "," + self.ID)
        # self.igs = ""
        # self.NCR = ''
        # 刷新这个table
        self.orgTable = ['Gene,Position,,Size,Intergenic nucleotides,Codon,,\n,From,To,,,Start,Stop,Strand,Sequence\n']
        self.lastEndIndex = 0
        self.overlap, self.gap = 0, 0
        self.dict_repeat_name_num = OrderedDict()
        self.list_feature_pos = [] # [0,1,2,3,4,...]

    def _exec(self):
        ####执行###
        try:
            self.init_args_all()
            self.progressSig.emit(5) #5
            if self.dict_args["resolve duplicates"]:
                progress_extract = 50
                progress_sort_save = 70
            else:
                progress_extract = 70
                progress_sort_save = 95
            if self.dict_args["extract_entire_seq"]:
                output_path = self.factory.creat_dirs(self.exportPath + os.sep + 'individual_seqs')
                self.entire_sequences = []
                self.extract_entire_seq(output_path) #90
                with open(self.exportPath + os.sep + self.dict_args["entire_seq_name"] + ".fas", "w", encoding="utf-8") as f:
                    f.write("".join(self.entire_sequences))
                self.saveStatFile()
            else:
                self.extract(progress_extract) #70
                self.gene_sort_save(progress_sort_save) #20
                self.saveGeneralFile()
                self.saveStatFile()
            if self.dict_args["if itol"]:
                self.saveItolFiles()  # 存itol的文件
            if self.dict_args["resolve duplicates"]:
                rsl_dupl_worker = DetermineCopyGeneParallel()
                rsl_dupl_worker.exec2_(
                    self.exportPath,
                    f"{self.exportPath}/resolve_duplicates",
                    # None,
                    self.dict_args["rsdpl_queue"],
                    mafft_exe=self.dict_args["mafft_exe"],
                    threads=self.dict_args["rsl_dupl threads"],
                    exception_signal= self.dict_args["exception_signal"]
                )
            self.progressSig.emit(100)
        except:
            exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            print(exceptionInfo)
            self.dict_args["exception_signal"].emit(exceptionInfo)  # 激发这个信号


    def fetchTerCodon(self):
        if self.code_table in [1, 11, 12]:
            self.stopCodon = ["TAA", "TAG", "TGA"]
        elif self.code_table == 2:
            self.stopCodon = ["TAA", "TAG", "AGA", "AGG"]
        elif self.code_table in [3, 4, 5, 9, 10, 13, 21]:
            self.stopCodon = ["TAA", "TAG"]
        elif self.code_table == 6:
            self.stopCodon = ["TGA"]
        elif self.code_table == 14:
            self.stopCodon = ["TAG"]
        elif self.code_table == 16:
            self.stopCodon = ["TAA", "TGA"]
        elif self.code_table == 22:
            self.stopCodon = ["TAA", "TGA", "TCA"]
        elif self.code_table == 23:
            self.stopCodon = ["TAA", "TGA", "TTA", "TAG"]

    def fetchUsedName(self):
        usedName = []
        for i in self.name_contents:
            if i == "Organism":
                usedName.append(self.organism)
            elif i == "ID":
                usedName.append(self.ID)
            elif i == "Name":
                usedName.append(self.name)
            elif i == "Length":
                usedName.append(str(len(self.seq)))
            elif i == "Description":
                usedName.append(self.description)
            elif i == "Date":
                usedName.append(self.date)
            else:
                if i in self.qualifiers:
                    usedName.append(self.qualifiers[i][0].replace("/", ""))
                else:
                    usedName.append("NA")
        # self.breviary = self.organism.split()[0][0] + '_' + '_'.join(self.organism.split()[1:])
        # self.latin_gb = self.organism + ' ' + self.ID
        # if self.name_type == "organism":
        #     usedName = self.organism
        # if self.name_type == "GenBank ID":
        #     usedName = self.ID
        # if self.name_type == "Concise organism":
        #     usedName = self.breviary
        # if self.name_type == "organism+ID":
        #     usedName = self.latin_gb
        used_name = self.factory.refineName("_".join(usedName))
        self.list_used_names.append(used_name)
        return used_name

    def fetchGeneName(self, seq=None, tRNA=False):
        feature_type = self.feature_type if self.included_features != "All" else "all"
        included_qualifiers = self.dict_qualifiers["Qualifiers to be recognized (%s):" % feature_type]
        hasQualifier = False
        for qualifier in included_qualifiers:
            if qualifier in self.qualifiers:
                old_name = self.qualifiers[qualifier][0]
                hasQualifier = True
                break
        if not hasQualifier:
            ##没有找到指定的qualifier，返回
            self.absence.append(",".join([self.ID, self.organism, self.feature_type,
                                      self.strand, str(self.start), str(self.end)]))
            return
        if self.extract_list_gene:
            ###只提取指定基因的模式，不符合就返回
            if not old_name in self.all_list_gene:
                self.unextract_name.append(",".join([self.ID, self.organism, self.feature_type, old_name,
                                      self.strand, str(self.start), str(self.end)]))
                return
        name4num = self.replace_name(old_name)
        ## tRNA 要替换名字的情况
        if tRNA:
            values = ':' + ':'.join([i[0] for i in self.qualifiers.values()]) + ':'
            name4num = self.judge(name4num, values, seq, old_name=old_name)
        ##重复基因的名字加编号
        # print(self.replace_name(old_name), self.dict_type_genes)
        new_name, self.dict_type_genes[self.feature_type] = self.factory.numbered_Name(self.dict_type_genes.setdefault(self.feature_type, []),
                                                                                        name4num, omit=True)
        if old_name not in self.dict_name_replace:
            self.dict_name_replace[old_name] = new_name # [new_name, self.usedName]
        # else:
        #     self.dict_name_replace[old_name].append(self.usedName)
        return new_name

    def colourPicker(self, class_=None, Range=False):
        if Range:
            # 生成不重复的随机颜色
            colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
            while (colour in self.colours) and (colour in self.dict_args["lineage color"][class_]):
                # 不让range用自定义的颜色
                colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
        else:
            if (class_ in self.dict_args["lineage color"]) and self.dict_args["lineage color"][class_]:
                colour = self.dict_args["lineage color"][class_].pop()
                while colour in self.colours:
                    colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
            else:
                # 生成不重复的随机颜色
                colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
                while colour in self.colours:
                    colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
        self.colours.append(colour)
        return colour

    def colourTree(self):
        for class_ in self.included_lineages:
            lineage = self.dict_lineage[class_]
            if lineage not in self.dict_itol_info["itol_%s_colourUsed1" % class_]:
                # colour, text, strip的颜色
                colour1 = self.colourPicker(class_)
                self.dict_itol_info["itol_%s_colourUsed1" %
                                    class_][lineage] = colour1
                self.dict_itol_info["itol_%s_Text" % class_].append("%s,%s,-1,%s,bold,2,0\n" % (
                    self.usedName, lineage, colour1))
                self.dict_itol_info["itol_%s_ColourStrip" % class_][0] = re.sub(r"(LEGEND_SHAPES.*)\n", "\\1 RE\n",
                                                                             self.dict_itol_info["itol_%s_ColourStrip" % class_][0])
                self.dict_itol_info["itol_%s_ColourStrip" % class_][0] = re.sub(r"(LEGEND_COLORS.*)\n", "\\1 %s\n"%colour1,
                                                                             self.dict_itol_info[
                                                                                 "itol_%s_ColourStrip" % class_][0])
                self.dict_itol_info["itol_%s_ColourStrip" % class_][0] = re.sub(r"(LEGEND_LABELS.*)\n", "\\1 %s\n"%lineage,
                                                                             self.dict_itol_info[
                                                                                 "itol_%s_ColourStrip" % class_][0])
                if "LEGEND_TITLE,None" in self.dict_itol_info["itol_%s_ColourStrip" % class_][0]:
                    self.dict_itol_info["itol_%s_ColourStrip" % class_][0] = re.sub(r"(LEGEND_TITLE.*)\n",
                                                                                 "LEGEND_TITLE %s\n" % class_,
                                                                                 self.dict_itol_info[
                                                                                     "itol_%s_ColourStrip" % class_][0])
                if "DATASET_LABEL color_strip\n" in self.dict_itol_info["itol_%s_ColourStrip" % class_][0]:
                    self.dict_itol_info["itol_%s_ColourStrip" % class_][0] = re.sub(r"(DATASET_LABEL.*)\n",
                                                                                 "DATASET_LABEL color_strip_%s\n" % class_,
                                                                                 self.dict_itol_info[
                                                                                     "itol_%s_ColourStrip" % class_][0])
                # range的颜色
                colour2 = self.colourPicker(class_, Range=True)
                self.dict_itol_info["itol_%s_colourUsed2" %
                                    class_][lineage] = colour2
            for num, item in enumerate(
                    ["Colour", "ColourStrip", "ColourRange"]):
                if num == 0:
                    self.dict_itol_info["itol_%s_%s" % (class_, item)].append("%s,label,%s,normal,1\n" % (
                        self.usedName, self.dict_itol_info["itol_%s_colourUsed1" % class_][lineage]))
                elif num == 1:
                    self.dict_itol_info["itol_%s_%s" % (class_, item)].append("%s %s %s\n" % (
                        self.usedName, self.dict_itol_info["itol_%s_colourUsed1" % class_][lineage], lineage))
                elif num == 2:
                    self.dict_itol_info["itol_%s_%s" % (class_, item)].append("%s,range,%s,%s\n" % (
                        self.usedName, self.dict_itol_info["itol_%s_colourUsed2" % class_][lineage], lineage))

    def replace_name(self, old_name):
        return self.dict_replace.get(old_name, old_name)

    def parseSource(self):
        # try:
        self.usedName = self.fetchUsedName()
        self.org_gb = self.organism + " " + self.name
        ###加了下面的就报错
        self.dict_lineage = OrderedDict()
        self.list_lineages = []
        ##更新lineage
        for lineage in self.included_lineages:
            if lineage in self.qualifiers:
                lineaName = self.qualifiers[lineage][0]
                self.dict_lineage[lineage] = lineaName
            else:
                lineaName = "N/A"
                self.dict_lineage[lineage] = "N/A"
            self.list_lineages.append(lineaName)
        # # 分类信息
        # list_taxonmy = [self.dict_lineage[i]
        #                 for i in reversed(self.included_lineages)]
        # self.taxonmy = ",".join(
        #     [self.tree_name] + list_taxonmy)
        # ITOL相关代码
        if self.dict_args["if itol"]:
            self.dict_itol_name[self.usedName] = self.organism
            self.dict_itol_gb[self.usedName] = self.name
            seqStat = SeqGrab(self.str_seq)
            self.itolAT.append(self.usedName + "," + seqStat.AT_percent + "\n")
            self.itolGCskew.append(self.usedName + "," + seqStat.GC_skew + "\n")
            self.itolLength.append(self.usedName + "," + seqStat.size + "\n")
            A, T, C, G = str(
                self.str_seq.upper().count('A')), str(
                self.str_seq.upper().count('T')), str(
                self.str_seq.upper().count('C')), str(
                self.str_seq.upper().count('G'))
            self.itolLength_stack.append(",".join([self.usedName, A, T, C, G]) + "\n")
            # 标记颜色
            self.colourTree()

        list_taxonmy = list(reversed(self.list_lineages))
        self.list_all_taxonmy.append(list_taxonmy)
        self.taxonmy = ",".join(
            [self.organism] + list_taxonmy)
        # self.gene_order = '>' + self.usedName + '\n'
        self.complete_seq.append('>' + self.usedName + '\n' + self.str_seq + '\n')
        # except:
        #     print(''.join(
        #         traceback.format_exception(*sys.exc_info())))

    def parseFeature(self):
        new_name = self.fetchGeneName()
        if not new_name:
            return
        seq = str(self.feature.extract(self.seq))
        self.gb2fas[self.usedName] = self.gb2fas.get(self.usedName, "") + f">{new_name}\n{seq}\n"
        feature_name = "CDS_NUC" if self.feature_type.upper() == "CDS" else self.feature_type
        self.dict_feature_fas.setdefault(feature_name, OrderedDict())[new_name + '>' + self.organism + '_' +
                                                                      self.name] = '>' + self.usedName + '\n' + seq + '\n'
        self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
        if "translation" in self.qualifiers:
            aa_seq = self.qualifiers["translation"][0]
            self.dict_feature_fas.setdefault("CDS_AA", OrderedDict())[new_name + '>' + self.organism + '_' +
                                                                      self.name] = '>' + self.usedName + '\n' + aa_seq + '\n'
        self.fun_orgTable(new_name, len(seq), "", "", seq)
        # 基因顺序
        if new_name.upper().startswith("NCR"):
            if self.gene_is_included(new_name, self.dict_args["checked gene names"], "NCR"):
                self.dict_order.setdefault(self.usedName, []).append(f'{self.omit_strand}NCR')
        else:
            if self.gene_is_included(new_name, self.dict_args["checked gene names"], ""):
                self.dict_order.setdefault(self.usedName, []).append(f'{self.omit_strand}{new_name}')
        ## 间隔区提取
        self.refresh_pairwise_feature(new_name)
        ## 基因统计
        seqStat = SeqGrab(seq.upper())
        self.dict_genes[new_name] = ",".join([new_name,
                                              self.strand,
                                              seqStat.size,
                                              seqStat.T_percent,
                                              seqStat.C_percent,
                                              seqStat.A_percent,
                                              seqStat.G_percent,
                                              seqStat.AT_percent,
                                              seqStat.GC_percent,
                                              seqStat.GT_percent,
                                              seqStat.AT_skew,
                                              seqStat.GC_skew]) + "\n"

    def gb_record_stat(self):
        '''

        :return:
        '''
        #         whole genome
        seq = self.str_seq.upper()
        seqStat = SeqGrab(seq)
        all_seq_name = 'Full genome' if  self.dict_args["seq type"] == "Mitogenome" else "Full sequence"
        geom_stat = ",".join([all_seq_name,
                              "+",
                              seqStat.size,
                              seqStat.T_percent,
                              seqStat.C_percent,
                              seqStat.A_percent,
                              seqStat.G_percent,
                              seqStat.AT_percent,
                              seqStat.GC_percent,
                              seqStat.GT_percent,
                              seqStat.AT_skew,
                              seqStat.GC_skew]) + "\n"
        # 物种的大统计表
        self.list_spe_stat = self.list_lineages + [
            self.organism,
            self.ID,
            seqStat.size,
            seqStat.AT_percent,
            seqStat.AT_skew,
            seqStat.GC_skew]
        ###species_info###
        rvscmp_seq = self.rvscmp_seq.upper()
        seqStat_rvscmp = SeqGrab(rvscmp_seq)
        self.plus_coding_seq = "".join(self.plus_coding_seq)
        seqCoding = SeqGrab(self.plus_coding_seq)
        self.plus_coding_gene_only = "".join(self.plus_coding_gene_only)
        seqCodingOnly = SeqGrab(self.plus_coding_gene_only)
        self.PCGs_strim = "".join(self.PCGs_strim)
        self.PCGs_strim_plus = "".join(self.PCGs_strim_plus)
        self.PCGs_strim_minus = "".join(self.PCGs_strim_minus)
        ffds = SeqGrab(self.PCGs_strim).extract_ffds(self.code_table) # extract fourfold degenerate sites
        ffds_seq = SeqGrab(ffds)
        ffds_plus = SeqGrab(self.PCGs_strim_plus).extract_ffds(self.code_table)  # extract fourfold degenerate sites only for PCGs on plus strand
        ffds_seq_plus = SeqGrab(ffds_plus)
        # self.NCR_seq = "".join(self.NCR_seq)
        if self.cal_NCR_ratio:
            NCR_ratio, NCR_seq = self.get_NCR_ratio(self.list_feature_pos, len(self.str_seq))
            NCR_seq_grab = SeqGrab(NCR_seq)
            ncr_gc_skew = NCR_seq_grab.GC_skew
        else:
            ncr_gc_skew, NCR_ratio = "N/A", "N/A"
        self.species_info.append([self.ID, self.organism, self.usedName] + self.list_lineages + [self.code_table] + \
                            [str(len(self.str_seq)), str(seqCoding.length),
                             seqCoding.GC_skew, seqCodingOnly.GC_skew,
                             ffds_seq.GC_skew, ffds_seq_plus.GC_skew,
                             ncr_gc_skew, NCR_ratio,
                             seqStat.A_percent, seqStat.T_percent,
                             seqStat.C_percent, seqStat.G_percent,
                             seqStat.AT_percent, seqStat.GC_percent,
                             seqStat.GT_percent,
                             seqStat.AT_skew, seqStat.GC_skew] + \
                             ([seqStat_rvscmp.AT_skew] if self.dict_args["analyze - sequence"] else []) + \
                             ([seqStat_rvscmp.GC_skew] if self.dict_args["analyze - sequence"] else []))
        self.taxonomy_infos.append(",".join([self.usedName, self.ID, self.organism] + self.list_lineages) + "\n")

        # 统计单个物种
        list_genes = [
            value for (key, value) in sorted(self.dict_genes.items())]

        #         PCG
        PCGs_stat_plus, first_stat_plus, second_stat_plus, third_stat_plus = self.stat_PCG_sub(self.PCGs_strim_plus, "+") \
                                                    if (self.PCGs_strim_plus and self.dict_args["analyze + sequence"] and self.dict_args["analyze all PCGs"]) \
                                                    else ["", "", "", ""]
        PCGs_stat_minus, first_stat_minus, second_stat_minus, third_stat_minus = self.stat_PCG_sub(self.PCGs_strim_minus, "-") \
                                                    if (self.PCGs_strim_minus and self.dict_args["analyze - sequence"] and self.dict_args["analyze all PCGs"]) \
                                                    else ["", "", "", ""]
        PCGs_stat, first_stat, second_stat, third_stat = self.stat_PCG_sub(self.PCGs_strim, "all") \
                                                    if (self.PCGs_strim and self.dict_args["analyze all PCGs"]) \
                                                    else ["", "", "", ""]
        #         rRNA
        self.rRNAs = "".join(self.rRNAs)
        self.rRNAs_plus = "".join(self.rRNAs_plus)
        self.rRNAs_minus = "".join(self.rRNAs_minus)
        rRNA_stat = self.stat_other_sub(self.rRNAs, "all", "rRNAs") if \
            (self.rRNAs and self.dict_args["analyze all rRNAs"]) else ""
        if not self.rRNAs and self.dict_args["analyze all rRNAs"]:
            self.geneStat_sub("rRNAs(all)", "N/A")  ##要补个NA
        rRNA_stat_plus = self.stat_other_sub(self.rRNAs_plus, "+", "rRNAs") if \
            (self.rRNAs_plus and self.dict_args["analyze + sequence"] and self.dict_args["analyze all rRNAs"]) else ""
        if not self.rRNAs_plus and self.dict_args["analyze + sequence"] and self.dict_args["analyze all rRNAs"]:
            self.geneStat_sub("rRNAs(+)", "N/A") ##要补个NA
        rRNA_stat_minus = self.stat_other_sub(self.rRNAs_minus, "-", "rRNAs") if \
            (self.rRNAs_minus and self.dict_args["analyze - sequence"] and self.dict_args["analyze all rRNAs"]) else ""
        if not self.rRNAs_minus and self.dict_args["analyze - sequence"] and self.dict_args["analyze all rRNAs"]:
            self.geneStat_sub("rRNAs(-)", "N/A")  ##要补个NA
        #         tRNA
        self.tRNAs = "".join(self.tRNAs)
        self.tRNAs_plus = "".join(self.tRNAs_plus)
        self.tRNAs_minus = "".join(self.tRNAs_minus)
        tRNA_stat = self.stat_other_sub(self.tRNAs, "all", "tRNAs") if \
            (self.tRNAs and self.dict_args["analyze all tRNAs"]) else ""
        if not self.tRNAs and self.dict_args["analyze all tRNAs"]:
            self.geneStat_sub("tRNAs(all)", "N/A")  ##要补个NA
        tRNA_stat_plus = self.stat_other_sub(self.tRNAs_plus, "+", "tRNAs") if \
            (self.tRNAs_plus and self.dict_args["analyze + sequence"] and self.dict_args["analyze all tRNAs"]) else ""
        if not self.tRNAs_plus and self.dict_args["analyze + sequence"] and self.dict_args["analyze all tRNAs"]:
            self.geneStat_sub("tRNAs(+)", "N/A")  ##要补个NA
        tRNA_stat_minus = self.stat_other_sub(self.tRNAs_minus, "-", "tRNAs") if \
            (self.tRNAs_minus and self.dict_args["analyze - sequence"] and self.dict_args["analyze all tRNAs"]) else ""
        if not self.tRNAs_minus and self.dict_args["analyze - sequence"] and self.dict_args["analyze all tRNAs"]:
            self.geneStat_sub("tRNAs(-)", "N/A")  ##要补个NA
        stat = 'Regions,Strand,Size (bp),T(U),C,A,G,AT(%),GC(%),GT(%),AT skew,GC skew\n' + PCGs_stat + PCGs_stat_plus + \
               PCGs_stat_minus + first_stat + first_stat_plus + first_stat_minus + second_stat + second_stat_plus + second_stat_minus +\
               third_stat + third_stat_plus + third_stat_minus + ''.join(list_genes) + \
               rRNA_stat + rRNA_stat_plus + rRNA_stat_minus + tRNA_stat + tRNA_stat_plus + tRNA_stat_minus + geom_stat
        self.dict_spe_stat[self.ID] = stat + "PCGs: protein-coding genes; +: major strand; -: minus strand\n"
        # 生成折线图分类信息
        list_genes_line = [
            value for (
                key, value) in sorted(
                self.dict_genes.items()) if not key.startswith("zNCR")]
        p_spe = PCGs_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if PCGs_stat else ""
        p_spe_plus = PCGs_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if PCGs_stat_plus else ""
        p_spe_minus = PCGs_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if PCGs_stat_minus else ""
        t_spe = tRNA_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if tRNA_stat else ""
        t_spe_plus = tRNA_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if tRNA_stat_plus else ""
        t_spe_minus = tRNA_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if tRNA_stat_minus else ""
        r_spe = rRNA_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if rRNA_stat else ""
        r_spe_plus = rRNA_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if rRNA_stat_plus else ""
        r_spe_minus = rRNA_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if rRNA_stat_minus else ""
        fst_spe = first_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if first_stat else ""
        fst_spe_plus = first_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if first_stat_plus else ""
        fst_spe_minus = first_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if first_stat_minus else ""
        scd_spe = second_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if second_stat else ""
        scd_spe_plus = second_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if second_stat_plus else ""
        scd_spe_minus = second_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if second_stat_minus else ""
        trd_spe = third_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if third_stat else ""
        trd_spe_plus = third_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if third_stat_plus else ""
        trd_spe_minus = third_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if third_stat_minus else ""
        self.line_spe_stat.append(geom_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" + p_spe + p_spe_plus + p_spe_minus + \
                              t_spe + t_spe_plus + t_spe_minus + r_spe + r_spe_plus + r_spe_minus + fst_spe + fst_spe_plus + fst_spe_minus + \
                              scd_spe + scd_spe_plus + scd_spe_minus + trd_spe + trd_spe_plus + trd_spe_minus + \
                              "".join([i.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" for i in list_genes_line]))
        if self.dict_pro and self.dict_args["analyze RSCU"]:
            rscu_sum = RSCUsum(self.organism_1, self.PCGs_strim, str(self.code_table))
            rscu_table = rscu_sum.table
            self.dict_RSCU[self.ID] = rscu_table
            self.dict_all_spe_RSCU["title"].append(self.usedName)
            self.dict_all_codon_COUNT["title"].append(self.usedName)
            self.dict_all_AA_COUNT["title"].append(self.usedName)
            self.dict_all_AA_RATIO["title"].append(self.usedName)
            rscu_stack = RSCUstack(
                rscu_table,
                self.dict_all_spe_RSCU,
                self.dict_all_codon_COUNT,
                self.dict_all_AA_COUNT,
                self.dict_all_AA_RATIO,
                self.numbered_Name(
                    self.organism,
                    omit=True))
            self.dict_all_spe_RSCU = rscu_stack.dict_all_rscu
            self.dict_all_codon_COUNT = rscu_stack.dict_all_codon_count
            self.dict_all_AA_COUNT = rscu_stack.dict_all_AA_count
            self.dict_all_AA_RATIO = rscu_stack.dict_all_AA_ratio
            self.dict_AAusage[self.ID] = rscu_stack.stat
            self.dict_RSCU_stack[self.ID] = rscu_stack.stack
            self.dict_AA_stack[self.ID] = rscu_stack.aaStack
        # 存放基因间隔区序列
        # self.dict_igs[self.ID] = self.igs
        # self.list_spe_stat.append(self.reference_)
        self.dict_all_stat["_".join(
            self.list_lineages + [self.organism + "_" + self.ID])] = self.list_spe_stat
        #         生成PCG串联序列
        self.PCG_seq.append('>' + self.usedName + '\n' + self.PCGs_strim + '\n' if self.PCGs_strim else "")
        self.tRNA_seqs.append('>' + self.usedName + '\n' + self.tRNAs + '\n' if self.tRNAs else "")
        self.rRNA_seqs.append('>' + self.usedName + '\n' + self.rRNAs + '\n' if self.rRNAs else "")
        #         组成表
        self.orgTable.append("Overlap:," + \
                         str(self.overlap) + "," + "gap:," + str(self.gap))
        self.dict_orgTable[self.ID] = self.orgTable
        # 密码子偏倚分析
        if self.dict_args["cal_codon_bias"] and self.dict_pro:
            codonBias = CodonBias(self.PCGs_strim,
                                  codeTable=self.code_table,
                                  codonW=self.dict_args["CodonW_exe"],
                                  path=self.exportPath)
            list_cBias = codonBias.getCodonBias()
            self.codon_bias.append(",".join([self.usedName, "PCGs"] + list_cBias) + "," + self.taxonmy + "\n")
        # map ID to tree name
        self.dict_ID_treeName[self.ID] = self.usedName

    def extract_entire_seq(self, output_path):
        # gb_records = SeqIO.parse(self.gbContentIO, "genbank")
        for num, gb_file in enumerate(self.gb_files):
            try:
                gb = SeqIO.parse(gb_file, "genbank")
                gb_record = next(gb)
                self.name = gb_record.name
                features = gb_record.features
                annotations = gb_record.annotations
                self.organism = annotations["organism"]
                self.description = gb_record.description
                self.date = annotations["date"]
                self.ID = gb_record.id
                self.seq = gb_record.seq
                self.str_seq = str(self.seq)
                source_parsed = False
                for self.feature in features:
                    self.qualifiers = self.feature.qualifiers
                    # self.start = int(self.feature.location.start) + 1
                    # self.end = int(self.feature.location.end)
                    # self.strand = "+" if self.feature.location.strand == 1 else "-"
                    if (self.feature.type == "source") and (not source_parsed):
                        self.parseSource()
                        source_parsed = True
                self.entire_sequences.append(">%s\n%s\n" % (self.usedName, self.str_seq))
                # 存每个文件
                with open(os.path.join(output_path, self.usedName + ".fas"),
                          "w", encoding="utf-8", errors='ignore') as f:
                    f.write(">%s\n%s\n" % (self.usedName, self.str_seq))
                self.input_file.write(gb_record.format("genbank"))
            except:
                self.Error_ID.append(self.name + ":\n" + \
                                 ''.join(
                                     traceback.format_exception(*sys.exc_info())) + "\n")
            self.progressSig.emit((num + 1) * 90 / self.totleID)
        self.input_file.close()

    def extract(self, progress):
        self.init_args_all()
        # 专门用于判断
        included_features = [i.upper() for i in self.included_features]
        for num, gb_file in enumerate(self.gb_files):
            try:
                gb = SeqIO.parse(gb_file, "genbank")
                gb_record = next(gb)
                self.name = gb_record.name
                features = gb_record.features
                annotations = gb_record.annotations
                self.organism = annotations["organism"]
                self.organism_1 = self.organism.replace(" ", "_")
                self.description = gb_record.description
                self.date = annotations["date"]
                self.ID = gb_record.id
                self.seq = gb_record.seq
                self.str_seq = str(self.seq)
                self.rvscmp_seq = str(Seq(self.str_seq, generic_dna).reverse_complement())
                self.dict_type_genes = OrderedDict()
                self.init_args_each()
                self.plus_coding_seq = []  # 正链编码的序列，负链编码基因的序列会被反向互补并与这个一起
                self.plus_coding_gene_only = []  # 仅在正链编码基因的序列
                ok = self.check_records(features)
                if not ok: continue
                has_feature = False
                has_source = False
                source_parsed = False
                # print(features)
                for self.feature in features:
                    self.qualifiers = self.feature.qualifiers
                    self.start = int(self.feature.location.start) + 1
                    self.end = int(self.feature.location.end)
                    self.strand = "+" if self.feature.location.strand == 1 else "-"
                    self.omit_strand = "" if self.strand == "+" else "-"
                    # # 用于生成organization表
                    # self.positionFrom, self.positionTo = list1[0], list1[-1]
                    self.feature_type = self.feature.type
                    ## 用于计算 NCR ratio
                    if self.feature_type not in ["source"] + self.NCR_features:
                        if not ((self.start == 1) and (self.end == len(self.str_seq))):
                            # 有些物种的gene注释涵盖了整个序列，如 NC_044850
                            self.list_feature_pos.extend(list(self.feature.location))
                    if self.feature_type not in (self.list_features + ["source"]):
                        self.list_features.append(self.feature_type)
                    if (self.feature.type == "source") and (not source_parsed):
                        self.parseSource()
                        has_source = True
                        source_parsed = True
                    elif (("CDS" in included_features) or (self.included_features == "All")) and \
                            self.feature_type == 'CDS':
                        self.code_table = int(self.qualifiers["transl_table"][0]) if ("transl_table" in self.qualifiers) \
                                                                                     and \
                                                                                     self.qualifiers["transl_table"][
                                                                                         0].isnumeric() else self.selected_code_table
                        self.fetchTerCodon()  # 得到终止密码子
                        self.CDS_()
                        self.getNCR()
                        has_feature = True
                    elif (("RRNA" in included_features) or (self.included_features == "All")) and \
                            self.feature_type == 'rRNA':
                        self.rRNA_()
                        self.getNCR()
                        has_feature = True
                    elif (("TRNA" in included_features) or (self.included_features == "All")) and \
                            self.feature_type == 'tRNA':
                        self.tRNA_()
                        self.getNCR()
                        has_feature = True
                    elif self.included_features == "All" or (self.feature_type.upper() in included_features):
                        # 剩下的按照常规的来提取
                        self.parseFeature()
                        self.getNCR()
                        has_feature = True
                if not has_feature:
                    ##ID里面没有找到任何对应的feature的情况
                    name = self.usedName if has_source else self.ID
                    self.list_none_feature_IDs.append(name)
                self.gb_record_stat()
                self.getNCR(mode="end")  ##判断最后的间隔区
                self.input_file.write(gb_record.format("genbank"))
            except:
                self.Error_ID.append(self.name + ":\n" + \
                                 ''.join(
                                     traceback.format_exception(*sys.exc_info())) + "\n")
            self.progressSig.emit((num + 1) * progress / self.totleID)
        self.input_file.close()

    def trim_ter(self, raw_sequence):
        size = len(raw_sequence)
        if size % 3 == 0:
            if raw_sequence[-3:].upper() in self.stopCodon:
                trim_sequence = raw_sequence[:-3]
            else:
                trim_sequence = raw_sequence
        elif size % 3 == 1:
            trim_sequence = raw_sequence[:-1]
        elif size % 3 == 2:
            trim_sequence = raw_sequence[:-2]
        else:
            trim_sequence = raw_sequence
        return trim_sequence

    def CDS_(self):
        seq = str(self.feature.extract(self.seq))
        new_name = self.fetchGeneName()
        self.gb2fas[self.usedName] = self.gb2fas.get(self.usedName, "") + f">{new_name}\n{seq}\n"
        codon_start = self.qualifiers['codon_start'][0] if "codon_start" in self.qualifiers else "1"
        seq = seq[int(codon_start)-1:] if codon_start != "1" else seq
        def codon(seq):
            seq = seq.upper()
            size = len(seq)
            ini = seq[0:3]
            if size % 3 == 0:
                if seq[-3:].upper() in self.stopCodon:
                    trim_sequence = seq[:-3]
                    ter = seq[-3:]
                else:
                    ter = "---"
                    trim_sequence = seq
                # 计算RSCU用的，保留终止密码子，但是不保留不完整的终止密码子
                RSCU_seq = seq
            elif size % 3 == 1:
                ter = seq[-1]
                trim_sequence = seq[:-1]
                RSCU_seq = seq[:-1]
            elif size % 3 == 2:
                ter = seq[-2:]
                trim_sequence = seq[:-2]
                RSCU_seq = seq[:-2]
            return ini, ter, size, seq, trim_sequence, RSCU_seq

        # trim_sequence是删除终止子以后的
        ini, ter, size, seq, trim_sequence, RSCU_seq = codon(seq)

        if not new_name:
            return
        self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
        self.dict_pro[new_name + '>' + self.usedName] = '>' + \
                                                          self.usedName + '\n' + seq + \
                                                          '\n'  # 这里不能用seq代替，因为要用大小写区分正负链
        translation = self.qualifiers['translation'][0] if 'translation' in self.qualifiers else ""  # 有时候没有translation
        self.dict_AA[new_name + '>' + self.usedName] = '>' + self.usedName + '\n' + translation + "\n"
        if self.gene_is_included(new_name, self.dict_args["checked gene names"], "PCGs"):
            self.dict_order.setdefault(self.usedName, []).append(f'{self.omit_strand}{new_name}')
        seqStat = SeqGrab(seq)
        self.dict_genes[new_name] = ",".join(
            [
                new_name,
                self.strand,
                seqStat.size,
                seqStat.T_percent,
                seqStat.C_percent,
                seqStat.A_percent,
                seqStat.G_percent,
                seqStat.AT_percent,
                seqStat.GC_percent,
                seqStat.GT_percent,
                seqStat.AT_skew,
                seqStat.GC_skew]) + "\n"
        self.dict_PCG.setdefault(new_name, {}).setdefault(self.usedName, str(size))  # {"atp6": {"spe1": "15610", "spe2": "15552"}}
        self.dict_start.setdefault(new_name, {}).setdefault(self.usedName, ini)
        self.dict_stop.setdefault(new_name, {}).setdefault(self.usedName, ter)
        self.dict_gene_ATskews.setdefault(new_name, {}).setdefault(self.usedName, seqStat.AT_skew)
        self.dict_gene_GCskews.setdefault(new_name, {}).setdefault(self.usedName, seqStat.GC_skew)
        self.dict_gene_ATCont.setdefault(new_name, {}).setdefault(self.usedName, seqStat.AT_percent)
        self.dict_gene_GCCont.setdefault(new_name, {}).setdefault(self.usedName, seqStat.GC_percent)
        self.PCGs_strim.append(RSCU_seq)
        if self.strand == "+":
            self.PCGs_strim_plus.append(RSCU_seq)
        else:
            self.PCGs_strim_minus.append(RSCU_seq)
        # 生成组成表相关
        self.fun_orgTable(new_name, size, ini, ter, seq)
        ##间隔区提取
        self.refresh_pairwise_feature(new_name)
        ##密码子偏倚分析
        if self.dict_args["cal_codon_bias"]:
            codonBias = CodonBias(RSCU_seq,
                                  codeTable=self.code_table,
                                  codonW=self.dict_args["CodonW_exe"],
                                  path=self.exportPath)
            list_cBias = codonBias.getCodonBias()
            self.codon_bias.append(",".join([self.usedName, new_name] + list_cBias) + "," + self.taxonmy + "\n")
        # 存PCGs基因名字
        if new_name not in self.PCGs_names:
            self.PCGs_names.append(new_name)

    def rRNA_(self):
        new_name = self.fetchGeneName()
        if not new_name:
            return
        seq = str(self.feature.extract(self.seq))
        self.gb2fas[self.usedName] = self.gb2fas.get(self.usedName, "") + f">{new_name}\n{seq}\n"
        self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
        self.dict_rRNA[new_name + '>' + self.usedName] = '>' + self.usedName + '\n' + seq + '\n'
        if self.gene_is_included(new_name, self.dict_args["checked gene names"], "rRNAs"):
            self.dict_order.setdefault(self.usedName, []).append(f'{self.omit_strand}{new_name}')
        seqStat = SeqGrab(seq.upper())
        self.dict_genes[new_name] = ",".join([new_name,
                                              self.strand,
                                              seqStat.size,
                                              seqStat.T_percent,
                                              seqStat.C_percent,
                                              seqStat.A_percent,
                                              seqStat.G_percent,
                                              seqStat.AT_percent,
                                              seqStat.GC_percent,
                                              seqStat.GT_percent,
                                              seqStat.AT_skew,
                                              seqStat.GC_skew]) + "\n"
        self.dict_RNA.setdefault(new_name, {}).setdefault(self.usedName,str(len(seq)))  # {"atp6": {"spe1": "15610", "spe2": "15552"}}
        self.dict_gene_ATskews.setdefault(new_name, {}).setdefault(self.usedName, seqStat.AT_skew)
        self.dict_gene_GCskews.setdefault(new_name, {}).setdefault(self.usedName, seqStat.GC_skew)
        self.dict_gene_ATCont.setdefault(new_name, {}).setdefault(self.usedName, seqStat.AT_percent)
        self.dict_gene_GCCont.setdefault(new_name, {}).setdefault(self.usedName, seqStat.GC_percent)
        self.rRNAs.append(seq)
        if self.strand == "+":
            self.rRNAs_plus.append(seq)
        else:
            self.rRNAs_minus.append(seq)
        # 生成组成表相关
        self.fun_orgTable(new_name, seqStat.length, "", "", seq)
        ##间隔区提取
        self.refresh_pairwise_feature(new_name)
        # 存rRNA基因名字
        if new_name not in self.rRNA_names:
            self.rRNA_names.append(new_name)

    def tRNA_(self):
        seq = str(self.feature.extract(self.seq))
        name = self.fetchGeneName(seq=seq, tRNA=True)
        if not name:
            return
        self.gb2fas[self.usedName] = self.gb2fas.get(self.usedName, "") + f">{name}\n{seq}\n"
        # values = ':' + ':'.join([i[0] for i in self.qualifiers.values()]) + ':'
        # name = self.judge(replace_name, values, seq)
        list_tRNA = [
            "T",
            "C",
            "E",
            "Y",
            "R",
            "G",
            "H",
            "L1",
            "L2",
            "S1",
            "S2",
            "Q",
            "F",
            "M",
            "V",
            "A",
            "D",
            "N",
            "P",
            "I",
            "K",
            "W",
            "S",
            "L"]
        new_name = "trn" + name if name in list_tRNA else name
        self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
        self.dict_tRNA[new_name + '>' + self.usedName] = '>' + self.usedName + '\n' + seq + '\n'
        if self.gene_is_included(name, self.dict_args["checked gene names"], "tRNAs"):
            self.dict_order.setdefault(self.usedName, []).append(f'{self.omit_strand}{name}')
        self.tRNAs.append(seq.upper())
        if self.strand == "+":
            self.tRNAs_plus.append(seq.upper())
        else:
            self.tRNAs_minus.append(seq.upper())
        # 生成组成表相关
        self.fun_orgTable(new_name, len(seq), "", "", seq)
        ##间隔区提取
        self.refresh_pairwise_feature(new_name)
        # 存tRNA基因名字
        if name not in self.tRNA_names:
            self.tRNA_names.append(name)

    def sort_CDS(self):
        list_pro = sorted(list(self.dict_pro.keys()))
        previous = ''
        seq_pro = []
        trans_pro = []
        seq_aa = []  # 存放读取的translation里面的AA序列
        it = iter(list_pro)
        table = CodonTable.ambiguous_dna_by_id[self.code_table]
        while True:
            try:
                i = next(it)
                gene = re.match('^[^>]+', i).group()
                if gene == previous or previous == '':
                    seq_pro.append(self.dict_pro[i])
                    seq_aa.append(self.dict_AA[i])
                    raw_sequence = self.dict_pro[i].split('\n')[1]
                    trim_sequence = self.trim_ter(raw_sequence)
                    try:
                        protein = _translate_str(trim_sequence, table)
                    except:
                        protein = ""
                    trans_pro.append(self.dict_pro[
                        i].replace(raw_sequence, protein))
                    previous = gene
                if gene != previous:
                    self.save2file("".join(seq_pro), previous, self.CDS_nuc_path)
                    self.save2file("".join(seq_aa), previous, self.CDS_aa_path)
                    self.save2file("".join(trans_pro), previous, self.CDS_TrsAA_path)
                    seq_pro = []
                    trans_pro = []
                    seq_aa = []  # 存放读取的translation里面的AA序列
                    seq_pro.append(self.dict_pro[i])
                    seq_aa.append(self.dict_AA[i])
                    raw_sequence = self.dict_pro[i].split('\n')[1]
                    trim_sequence = self.trim_ter(raw_sequence)
                    try:
                        protein = _translate_str(trim_sequence, table)
                    except:
                        protein = ""
                    trans_pro.append(self.dict_pro[
                        i].replace(raw_sequence, protein))
                    previous = gene
            except StopIteration:
                self.save2file("".join(seq_pro), previous, self.CDS_nuc_path)
                self.save2file("".join(seq_aa), previous, self.CDS_aa_path)
                self.save2file("".join(trans_pro), previous, self.CDS_TrsAA_path)
                break

    def sort_rRNA(self):
        list_rRNA = sorted(list(self.dict_rRNA.keys()))
        previous = ''
        seq_rRNA = []
        it = iter(list_rRNA)
        while True:
            try:
                i = next(it)
                gene = re.match('^[^>]+', i).group()
                if gene == previous or previous == '':
                    seq_rRNA.append(self.dict_rRNA[i])
                    previous = gene
                if gene != previous:
                    self.save2file("".join(seq_rRNA), previous, self.rRNA_path)
                    seq_rRNA = []
                    seq_rRNA.append(self.dict_rRNA[i])
                    previous = re.match('^[^>]+', i).group()
            except StopIteration:
                self.save2file("".join(seq_rRNA), previous, self.rRNA_path)
                break

    def sort_tRNA(self):
        list_tRNA = sorted(list(self.dict_tRNA.keys()))
        previous = ''
        seq_tRNA = []
        it = iter(list_tRNA)
        while True:
            try:
                i = next(it)
                gene = re.match('^[^>]+', i).group()
                if gene == previous or previous == '':
                    seq_tRNA.append(self.dict_tRNA[i])
                    previous = gene
                if gene != previous:
                    self.save2file("".join(seq_tRNA), previous, self.tRNA_path)
                    seq_tRNA = []
                    seq_tRNA.append(self.dict_tRNA[i])
                    previous = re.match('^[^>]+', i).group()
            except StopIteration:
                self.save2file("".join(seq_tRNA), previous, self.tRNA_path)
                break

    def save2file(self, content, name, featurePath):
        name = self.factory.refineName(name, remain_words=".-", limit=(254-len(featurePath)))  # 替换名字里面的不识别符号
        with open(os.path.normpath(featurePath) + os.sep + name + '.fas', 'w', encoding="utf-8") as f:
            f.write(content)

    def save_each_feature(self, dict_gene_fas, featurePath, base, proportion):
        list_gene_fas = sorted(list(dict_gene_fas.keys()))
        previous = ''
        gene_seq = []
        # 避免报错
        gene = ""
        it = iter(list_gene_fas)
        total = len(list_gene_fas)
        if not total:
            return base + proportion
        num = 0
        while True:
            try:
                i = next(it)
                gene = re.match('^[^>]+', i).group()
                if gene == previous or previous == '':
                    gene_seq.append(dict_gene_fas[i])
                    previous = gene
                if gene != previous:
                    self.save2file("".join(gene_seq), previous, featurePath)
                    gene_seq = []
                    gene_seq.append(dict_gene_fas[i])
                    previous = re.match('^[^>]+', i).group()
            except StopIteration:
                self.save2file("".join(gene_seq), gene, featurePath)
                num += 1
                self.progressSig.emit(base + num * proportion / total)
                break
        num += 1
        self.progressSig.emit(base + num * proportion / total)
        return base + proportion

    def gene_sort_save(self, progress):
        if self.dict_pro:
            self.CDS_nuc_path = self.factory.creat_dirs(self.exportPath + os.sep + "CDS_NUC")
            self.CDS_aa_path = self.factory.creat_dirs(self.exportPath + os.sep + "CDS_AA")
            self.CDS_TrsAA_path = self.factory.creat_dirs(self.exportPath + os.sep + "self-translated_AA")
            self.sort_CDS()
        self.progressSig.emit(0.86*progress)
        if self.dict_rRNA:
            self.rRNA_path = self.factory.creat_dirs(self.exportPath + os.sep + "rRNA")
            self.sort_rRNA()
        self.progressSig.emit(0.92*progress)
        if self.dict_tRNA:
            self.tRNA_path = self.factory.creat_dirs(self.exportPath + os.sep + "tRNA")
            self.sort_tRNA()
        self.progressSig.emit(0.97*progress)
        keys = list(self.dict_feature_fas.keys())
        # 只保留有效值
        for i in keys:
            if not self.dict_feature_fas[i]:
                del self.dict_feature_fas[i]
        total = len(self.dict_feature_fas)
        if not total:
            self.progressSig.emit(progress)
            return
        base = 0.97*progress
        proportion = 3 / total
        for feature in self.dict_feature_fas:
            feature_fas = self.dict_feature_fas[feature]
            if not feature_fas:
                ##如果没有提取到任何东西就返回
                continue
            featurePath = self.factory.creat_dirs(self.exportPath + os.sep + feature)
            base = self.save_each_feature(feature_fas, featurePath, base, proportion)

    def saveItolFiles(self):
        itolPath = self.factory.creat_dirs(self.exportPath + os.sep + 'itolFiles')
        list_name = sorted(list(self.dict_itol_name.keys()))
        itol_labels = ['LABELS\nSEPARATOR COMMA\nDATA\n']
        itol_ori_labels = itol_labels[:]
        itol_gb_labels = itol_labels[:]
        for i in list_name:
            itol_labels.append(i + ',' + self.dict_itol_name[i] + '\n')
            itol_ori_labels.append(i + "," + i + "\n")
            itol_gb_labels.append(i + ',' + self.dict_itol_gb[i] + '\n')
        with open(itolPath + os.sep + 'itol_labels.txt', 'w', encoding="utf-8") as f:
            f.write("".join(itol_labels))
        with open(itolPath + os.sep + 'itol_ori_labels.txt', 'w', encoding="utf-8") as f:
            f.write("".join(itol_ori_labels))
        with open(itolPath + os.sep + 'itol_gb_labels.txt', 'w', encoding="utf-8") as f:
            f.write("".join(itol_gb_labels))
        with open(itolPath + os.sep + 'itolAT.txt', 'w', encoding="utf-8") as f2:
            f2.write("".join(self.itolAT))
        with open(itolPath + os.sep + 'itolGCskew.txt', 'w', encoding="utf-8") as f2:
            f2.write("".join(self.itolGCskew))
        with open(itolPath + os.sep + 'itolLength.txt', 'w', encoding="utf-8") as f3:
            f3.write("".join(self.itolLength))
        with open(itolPath + os.sep + 'itolLength_stack.txt', 'w', encoding="utf-8") as f4:
            f4.write("".join(self.itolLength_stack))
        # colour
        for lineage in self.included_lineages:
            for num, item in enumerate(
                    ["Colour", "Text", "ColourStrip", "ColourRange"]):
                name = "itol_%s_%s" % (lineage, item)
                with open(itolPath + os.sep + '%s.txt' % name, 'w', encoding="utf-8") as f5:
                    f5.write("".join(self.dict_itol_info[name]))
        # gene order
        if not self.dict_args["extract_entire_seq"]:
            itolPath = self.factory.creat_dirs(self.exportPath + os.sep + 'itolFiles')
            self.dict_args["PCGs names"] = self.PCGs_names
            self.dict_args["rRNAs names"] = self.rRNA_names
            self.dict_args["tRNAs names"] = self.tRNA_names
            self.dict_args["NCR names"] = ["NCR"]
            order2itol = Order2itol(self.dict_order, self.dict_args)
            with open(itolPath + os.sep + 'itol_gene_order.txt', 'w', encoding="utf-8") as f1:
                f1.write(order2itol.itol_gene_order)

    def generateGeneStat(self, dict_gene_stat):
        list_all = []
        list_genes = sorted(dict_gene_stat.keys())
        for gene in list_genes:
            list_ = [gene]
            for species in self.list_used_names:
                list_.append(dict_gene_stat[gene].get(species, "N/A"))
            if (len(set(list_[1:])) == 1) and list(set(list_[1:]))[0] == "N/A":
                continue
            list_all.append(list_)
        return list_all

    def saveStatFile(self):
        if self.dict_args["extract_entire_seq"]:
            return
        # self.factory.creat_dirs(self.exportPath + os.sep + 'rRNA')
        # self.factory.creat_dirs(self.exportPath + os.sep + 'tRNA')
        statFilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'StatFiles')
        # allStat = self.fetchAllStatTable()
        # with open(statFilePath + os.sep + 'used_species.csv', 'w', encoding="utf-8") as f4:
        #     f4.write(allStat)
        if (self.dict_args["seq type"] == "Mitogenome") and (not self.dict_args["extract_entire_seq"]):
            self.factory.write_csv_file(statFilePath + os.sep + 'species_info.csv',
                                        self.species_info +
                                        ([["+: sequences on major strand; -: sequences on minus strand\n"]]
                                        if self.dict_args["analyze + sequence"] or self.dict_args["analyze - sequence"]
                                        else []),
                                        None,
                                        silence=True)
        else:
            self.factory.write_csv_file(statFilePath + os.sep + 'species_info.csv',
                                        self.species_info,
                                        None,
                                        silence=True)
        with open(statFilePath + os.sep + 'taxonomy.csv', 'w', encoding="utf-8") as f5:
            f5.write("".join(self.taxonomy_infos))
        # if self.dict_args["extract_entire_seq"]:
        #     return
        ##名字及其替换后的名字
        name_replace = "Old Name\tNew Name\n" + "\n".join(
            ["\t".join([i] + [self.dict_name_replace[i]])
             for i in self.dict_name_replace])
        with open(statFilePath + os.sep + 'name_for_unification.tsv', 'w', encoding="utf-8") as f4:
            f4.write(name_replace)
        # csv格式的
        name_replace = "Old Name,New Name\n" + "\n".join(
            [",".join([i] + [self.dict_name_replace[i]])
             for i in self.dict_name_replace])
        with open(statFilePath + os.sep + 'name_for_unification.csv', 'w', encoding="utf-8") as f4:
            f4.write(name_replace)
        # if self.absence != '="ID",Organism,Feature,Strand,Start,Stop\n':
        #     # gfilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'files')
        #     with open(statFilePath + os.sep + 'feature_unrecognized.csv', 'w', encoding="utf-8") as f4:
        #         f4.write(self.absence)
        if len(self.unextract_name) > 1:
            # gfilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'files')
            with open(statFilePath + os.sep + 'name_not_included.csv', 'w', encoding="utf-8") as f4:
                f4.write("\n".join(self.unextract_name))
        ##NCR和overlap的统计
        ncr_path = self.exportPath + os.sep + 'intergenic_regions'
        ovlap_path = self.exportPath + os.sep + 'overlapping_regions'
        if self.dict_NCR_regions and os.path.exists(ncr_path):
            list_species = list(set(itertools.chain.from_iterable(self.dict_NCR_regions.values())))
            csv_header = "Summary of intergenic regions among species\nOrganism," + ",".join(self.dict_NCR_regions.keys()) + ",Count\n"
            csv = []
            for spe in list_species:
                list_ = [spe]
                for ncr_region in self.dict_NCR_regions:
                    if spe in self.dict_NCR_regions[ncr_region]:
                        list_.append("Y")
                    else:
                        list_.append("N")
                list_.append(str(list_.count("Y")))
                csv.append(list_)
            with open(ncr_path + os.sep + 'intergenic_regions_summary.csv', 'w', encoding="utf-8") as f4:
                text = csv_header + "\n".join([",".join(i) for i in csv]) + "\nY: Yes; N: No"
                f4.write(text)
        if self.dict_overlapping_regions and os.path.exists(ovlap_path):
            list_species = list(set(itertools.chain.from_iterable(self.dict_overlapping_regions.values())))
            csv_header = "Summary of overlapping regions among species\nOrganism," + ",".join(self.dict_overlapping_regions.keys()) + ",Count\n"
            csv = []
            for spe in list_species:
                list_ = [spe]
                for ovp_region in self.dict_overlapping_regions:
                    if spe in self.dict_overlapping_regions[ovp_region]:
                        list_.append("Y")
                    else:
                        list_.append("N")
                list_.append(str(list_.count("Y")))
                csv.append(list_)
            with open(ovlap_path + os.sep + 'overlapping_regions_summary.csv', 'w', encoding="utf-8") as f4:
                text = csv_header + "\n".join([",".join(i) for i in csv]) + "\nY: Yes; N: No"
                f4.write(text)
        # if self.none_feature_IDs != '="ID",\n':
        #     with open(statFilePath + os.sep + 'ID_with_no_features.csv', 'w', encoding="utf-8") as f4:
        #         f4.write(self.none_feature_IDs)
        statFilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'StatFiles')
        # 生成speciesStat文件夹
        speciesStatPath = self.factory.creat_dirs(statFilePath + os.sep + 'speciesStat')
        if self.dict_pro:
            ## 如果有CDS序列再执行
            # 生成CDS文件夹
            CDSpath = self.factory.creat_dirs(statFilePath + os.sep + 'CDS')
            # skewness
            if (self.dict_args["analyze 1st codon"] and
                    self.dict_args["analyze 2nd codon"] and
                    self.dict_args["analyze 3rd codon"]):
                with open(CDSpath + os.sep + 'PCGsCodonSkew.csv', 'w', encoding="utf-8") as f4:
                    f4.write("".join(self.PCGsCodonSkew))
            if self.dict_args["analyze 1st codon"]:
                with open(CDSpath + os.sep + 'firstCodonSkew.csv', 'w', encoding="utf-8") as f5:
                    f5.write("".join(self.firstCodonSkew))
            if self.dict_args["analyze 2nd codon"]:
                with open(CDSpath + os.sep + 'secondCodonSkew.csv', 'w', encoding="utf-8") as f6:
                    f6.write("".join(self.secondCodonSkew))
            if self.dict_args["analyze 3rd codon"]:
                with open(CDSpath + os.sep + 'thirdCodonSkew.csv', 'w', encoding="utf-8") as f7:
                    f7.write("".join(self.thirdCodonSkew))
            if self.dict_args["analyze 1st codon"] and self.dict_args["analyze 2nd codon"]:
                with open(CDSpath + os.sep + 'firstSecondCodonSkew.csv', 'w', encoding="utf-8") as f8:
                    f8.write("".join(self.firstSecondCodonSkew))
            # # 生成密码子偏倚统计
            if self.dict_args["cal_codon_bias"]:
                with open(CDSpath + os.sep + 'codon_bias.csv', 'w', encoding="utf-8") as f11:
                    f11.write("".join(self.codon_bias))
            if self.dict_args["analyze RSCU"]:
                # 生成RSCU文件夹
                RSCUpath = self.factory.creat_dirs(statFilePath + os.sep + 'RSCU')
                # RSCU  PCA# 生成PCA用的统计表
                title_rscu = [",".join(self.dict_all_spe_RSCU.pop("title")) + "\n"]
                title_rscu.extend([j + "," + ",".join(self.dict_all_spe_RSCU[j]) + "\n"
                                                                for j in self.dict_all_spe_RSCU])
                # for j in self.dict_all_spe_RSCU:
                #     title_rscu += j + "," + \
                #                   ",".join(self.dict_all_spe_RSCU[j]) + "\n"
                # 生成文件
                with open(RSCUpath + os.sep + "all_rscu_stat.csv", "w", encoding="utf-8") as f:
                    f.write("".join(title_rscu))
                # COUNT codon PCA# 生成PCA用的统计表
                title_codon_count = [",".join(self.dict_all_codon_COUNT.pop(
                    "title")) + "\n"]
                title_codon_count.extend([j + "," + ",".join(self.dict_all_codon_COUNT[j]) + "\n"
                                          for j in self.dict_all_codon_COUNT])
                # for j in self.dict_all_codon_COUNT:
                #     title_codon_count += j + "," + \
                #                          ",".join(self.dict_all_codon_COUNT[j]) + "\n"
                # 生成文件
                with open(RSCUpath + os.sep + "all_codon_count_stat.csv", "w", encoding="utf-8") as f:
                    f.write("".join(title_codon_count))
                # COUNT aa PCA# 生成PCA用的统计表
                title_AA_count = [",".join(self.dict_all_AA_COUNT.pop(
                    "title")) + "\n"]
                title_AA_count.extend([j + "," + ",".join(self.dict_all_AA_COUNT[j]) + "\n"
                                       for j in self.dict_all_AA_COUNT])
                # for j in self.dict_all_AA_COUNT:
                #     title_AA_count += j + "," + \
                #                       ",".join(self.dict_all_AA_COUNT[j]) + "\n"
                # 生成文件
                with open(RSCUpath + os.sep + "all_AA_count_stat.csv", "w", encoding="utf-8") as f:
                    f.write("".join(title_AA_count))
                # ratio aa PCA# 生成PCA用的统计表
                title_AA_ratio = [",".join(self.dict_all_AA_RATIO.pop(
                    "title")) + "\n"]
                title_AA_ratio.extend([j + "," + ",".join(self.dict_all_AA_RATIO[j]) + "\n"
                                       for j in self.dict_all_AA_RATIO])
                # for j in self.dict_all_AA_RATIO:
                #     title_AA_ratio += j + "," + \
                #                       ",".join(self.dict_all_AA_RATIO[j]) + "\n"
                # 生成文件
                with open(RSCUpath + os.sep + "all_AA_ratio_stat.csv", "w", encoding="utf-8") as f:
                    f.write("".join(title_AA_ratio))
                # 生成AA stack的文件
                title_aa_stack = [",".join(self.dict_AA_stack.pop(
                                    "title")) + "\n"]
                title_aa_stack.extend([self.dict_AA_stack[k] for k in self.dict_AA_stack])
                # for k in self.dict_AA_stack:
                #     title_aa_stack += self.dict_AA_stack[k]
                with open(RSCUpath + os.sep + "all_AA_stack.csv", "w", encoding="utf-8") as f:
                    f.write("".join(title_aa_stack))
        # 统计单个物种
        for j in self.dict_spe_stat:
            file_name = self.dict_ID_treeName.get(j, j)
            if j in self.dict_spe_stat:
                with open(speciesStatPath + os.sep + file_name + '.csv', 'w', encoding="utf-8") as f:
                    f.write(self.dict_spe_stat[j])
            if j in self.dict_orgTable:
                with open(speciesStatPath + os.sep + file_name + '_org.csv', 'w', encoding="utf-8") as f:
                    f.write("".join(self.dict_orgTable[j]))
            if self.dict_pro and self.dict_args["analyze RSCU"]:
                if j in self.dict_AAusage:
                    with open(RSCUpath + os.sep + file_name + '_AA_usage.csv', 'w', encoding="utf-8") as f:
                        f.write(self.dict_AAusage[j])
                if j in self.dict_RSCU:
                    with open(RSCUpath + os.sep + file_name + '_RSCU.csv', 'w', encoding="utf-8") as f:
                        f.write(self.dict_RSCU[j])
                if j in self.dict_RSCU_stack:
                    with open(RSCUpath + os.sep + file_name + '_RSCU_stack.csv', 'w', encoding="utf-8") as f:
                        f.write(self.dict_RSCU_stack[j])
        list_start = self.generateGeneStat(self.dict_start)
        list_stop = self.generateGeneStat(self.dict_stop)
        list_PCGs = self.generateGeneStat(self.dict_PCG)
        list_RNA = self.generateGeneStat(self.dict_RNA)
        list_ATskew = self.generateGeneStat(self.dict_gene_ATskews)
        list_GCskew = self.generateGeneStat(self.dict_gene_GCskews)
        list_ATCont = self.generateGeneStat(self.dict_gene_ATCont)
        list_GCCont = self.generateGeneStat(self.dict_gene_GCCont)
        list_abbre = self.assignAbbre(self.list_name_gb)
        header_taxonomy, footnote = self.geneStatSlot(list_abbre)
        headers = ['Species'] + list_abbre
        prefix_PCG = ['Length of PCGs (bp)']
        prefix_rRNA = ['Length of rRNA genes (bp)']
        prefix_ini = ['Putative start codon']
        prefix_ter = ['Putative terminal codon']
        prefix_ATskew = ['AT skew']
        prefix_GCskew = ['GC skew']
        prefix_ATCont = ['AT content']
        prefix_GCCont = ['GC content']
        array = header_taxonomy + \
                [headers] + \
                ([prefix_PCG] if list_PCGs else []) + \
                list_PCGs + \
                ([prefix_rRNA] if list_RNA else []) + \
                list_RNA + \
                ([prefix_ini] if list_start else []) + \
                list_start + \
                ([prefix_ter] if list_stop else []) + \
                list_stop + \
                ([prefix_ATskew] if list_ATskew else []) + \
                list_ATskew + \
                ([prefix_GCskew] if list_GCskew else []) + \
                list_GCskew + \
                ([prefix_ATCont] if list_ATCont else []) + \
                list_ATCont + \
                ([prefix_GCCont] if list_GCCont else []) + \
                list_GCCont + \
                [["N/A: Not Available; tRNAs: concatenated tRNA genes; rRNAs: concatenated rRNA genes;"
                 " +: major strand; -: minus strand"]] + \
                footnote
        self.factory.write_csv_file(statFilePath + os.sep + 'geneStat.csv',
                                    array,
                                    None,
                                    silence=True)
        with open(statFilePath + os.sep + 'gbAccNum.csv', 'w', encoding="utf-8") as f8:
            f8.write("\n".join(self.name_gb))
        # # ncr统计
        # self.ncr_stat_fun()
        # with open(statFilePath + os.sep + 'ncrStat.csv', 'w', encoding="utf-8") as f9:
        #     f9.write(self.ncrInfo)
        allStat = self.fetchAllStatTable()
        with open(statFilePath + os.sep + 'used_species.csv', 'w', encoding="utf-8") as f4:
            f4.write(allStat)
        # 生成画图所需原始数据
        with open(statFilePath + os.sep + 'data_for_plot.csv', 'w', encoding="utf-8") as f11:
            f11.write("".join(self.line_spe_stat))
        # 删除ENC的中间文件
        try:
            for file in ["codonW_infile.fas", "codonW_outfile.txt", "codonW_blk.txt"]:
                os.remove(self.exportPath + os.sep + file)
        except:
            pass

    def saveGeneralFile(self):
        # overview表
        overview = ["Extraction overview:\n\nVisit here to see how to customize the extraction: " \
                   "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/customize_extraction/ or " \
                   "http://phylosuite.jushengwu.com/dongzhang0725.github.io/PhyloSuite-demo/customize_extraction/ (China)\n\n"]
        ## species in total
        overview.append("%d species in total\n\n" % self.totleID)
        list_ = []
        for k in self.dict_qualifiers:
            try:
                feature = re.search(r"\((.+)\)", k).group(1)
                list_.append("%s (%s)"%(feature, " & ".join(self.dict_qualifiers[k])))
            except:
                pass
        included_features = self.included_features if self.included_features != "All" else ["All"]
        overview.append("Data type setting used to extract: %s\n  included features: %s\n" \
                    "  qualifiers of each feature: %s\n\n" % (self.dict_args["seq type"],
                                                     " & ".join(included_features), " | ".join(list_)))
        overview.append("Features found in sequences: %s\n\n" % " & ".join(self.list_features))
        # overview.append("Features set to extract: %s\n\n" % ", ".join(self.included_features))
        ###
        if len(self.absence) > 1:
            overview.append("Qualifiers set in the settings were not found in these features:\n %s\n" % \
                        "\n".join(self.absence).replace('="ID"', "ID"))
        ###
        if self.list_none_feature_IDs:
            overview.append("Features (%s) set in the settings were not found in these species: %s\n\n" %(" & ".join(included_features), " & ".join(
                self.list_none_feature_IDs)))
        if self.source_feature_IDs:
            overview.append("No features could be found in these IDs: %s\n\n" % " | ".join(self.source_feature_IDs))
        ##基因情况
        sorted_keys = sorted(self.dict_gene_names.keys())
        # gene_names = ",".join(["Genes"] + self.list_used_names) + "\n"
        # for i in sorted_keys:
        #     list_states = []
        #     for j in self.list_used_names:
        #         if j in self.dict_gene_names[i]:
        #             list_states.append("yes")
        #         else:
        #             list_states.append("no")
        #     gene_names += ",".join([i] + list_states) + "\n"
        # overview += "Genes found in species:\n %s\n\n" % gene_names
        name_genes = [["Species"] + sorted_keys]
        for i in self.list_used_names:
            list_states = []
            for j in sorted_keys:
                if i in self.dict_gene_names[j]:
                    list_states.append("yes")
                else:
                    list_states.append("no")
            name_genes.append([i] + list_states)

        overview.append("Genes found in species:\n %s\n\n" % "\n".join([",".join(i) for i in name_genes]))
        with open(self.exportPath + os.sep + 'overview.csv', 'w', encoding="utf-8") as f4:
            f4.write("".join(overview))

        filesPath = self.factory.creat_dirs(self.exportPath + os.sep + 'files')
        with open(filesPath + os.sep + 'linear_order.txt', 'w', encoding="utf-8") as f:
            t = "\t"
            linear_order = "\n".join([f">{species}\n{t.join(self.dict_order[species])}"
                                      for species in self.dict_order])
            f.write(linear_order)
        with open(filesPath + os.sep + 'complete_seq.fas', 'w', encoding="utf-8") as f:
            f.write("".join(self.complete_seq))
        if self.PCG_seq:
            with open(filesPath + os.sep + 'PCG_seqs.fas', 'w', encoding="utf-8") as f6:
                f6.write("".join(self.PCG_seq))
        if self.tRNA_seqs:
            with open(filesPath + os.sep + 'tRNA_seqs.fas', 'w', encoding="utf-8") as f7:
                f7.write("".join(self.tRNA_seqs))
        if self.rRNA_seqs:
            with open(filesPath + os.sep + 'rRNA_seqs.fas', 'w', encoding="utf-8") as f8:
                f8.write("".join(self.rRNA_seqs))
        # genome fas
        for spe in self.gb2fas:
            gb2fas_path = self.factory.creat_dirs(filesPath + os.sep + "gb2fas")
            with open(gb2fas_path + os.sep + f'{spe}.fas', 'w', encoding="utf-8") as f9:
                f9.write(self.gb2fas[spe])
        # if self.PCGs_names:
        #     import pickle
        #     with open('PCGs_names.pkl', 'wb') as f:
        #         pickle.dump(self.PCGs_names, f)
        # if self.tRNA_names:
        #     import pickle
        #     with open('tRNA_names.pkl', 'wb') as f:
        #         pickle.dump(self.tRNA_names, f)
        # if self.rRNA_names:
        #     import pickle
        #     with open('rRNA_names.pkl', 'wb') as f:
        #         pickle.dump(self.rRNA_names, f)

    def compareLineage(self, lineage1, lineage2, list_stat):
        string = []
        for num, i in enumerate(lineage1):
            if i != lineage2[num]:  # 出现不一致的分类阶元
                string.append(num * "    " + i + "\n")
        if lineage1[-1] == lineage2[-1]:  # 同一个物种，不同登录号
            string.append(num * "    " + i + "\n")
        string = "".join(string).strip("\n") + "," + ",".join(list_stat) + "\n"
        return string

    def fetchAllStatTable(self):
        allStat = ["Taxon,Accession number,Size(bp),AT%,AT-Skew,GC-Skew\n"]
        list_dict_sorted = sorted(list(self.dict_all_stat.keys()))
        lineage_count = len(self.included_lineages) + 1
        last_lineage = [1] * lineage_count
        for i in list_dict_sorted:
            lineage1 = self.dict_all_stat[i][:lineage_count]
            content = self.compareLineage(
                lineage1, last_lineage, self.dict_all_stat[i][lineage_count:])
            allStat.append(content)
            last_lineage = lineage1
        return "".join(allStat)

    def check_records(self, features):
        if len(features) == 1 and features[0].type == "source":
            self.source_feature_IDs.append(self.ID)
            return False
        return True

    def refresh_pairwise_feature(self, name):
        self.dict_pairwise_features["now_ini"] = self.start
        self.dict_pairwise_features["now_name"] = name
        self.dict_pairwise_features["last_end_temp"] = self.end

    def getNCR(self, mode="normal"):
        try:
            now_ini = self.dict_pairwise_features["now_ini"]
            last_end = self.dict_pairwise_features["last_end"]
            now_name = self.dict_pairwise_features["now_name"]
            last_name = self.dict_pairwise_features["last_name"]
            if not last_end:
                # 没有last_end就代表是第一个基因
                ##第一个基因的间隔区
                if self.dict_args["extract_intergenic_regions"] and now_ini and \
                        (now_ini > self.dict_args["intergenic_regions_threshold"]):
                    self.dict_feature_fas.setdefault("intergenic_regions", OrderedDict())["start_%s"%now_name
                                                  + '>' + self.organism + '_' + self.name] = '>' + self.usedName + '\n' + \
                                                                                             str(
                                                                                                 self.seq[
                                                                                                 0:(now_ini - 1)]) + '\n'
                    self.dict_NCR_regions.setdefault("start_%s"%now_name, []).append(self.org_gb)
                ##设置last
                self.dict_pairwise_features["last_name"] = now_name
                self.dict_pairwise_features["last_end"] = self.dict_pairwise_features["last_end_temp"]
                return
            if mode == "end":
                ##最后一个基因下游的间隔区
                final_end = self.dict_pairwise_features["last_end_temp"]
                if self.dict_args["extract_intergenic_regions"] and final_end and\
                        ((len(self.seq) - final_end) >= self.dict_args["intergenic_regions_threshold"]):
                    self.dict_feature_fas.setdefault("intergenic_regions", OrderedDict())["%s_end" % now_name
                                              + '>' + self.organism + '_' + self.name] = '>' + self.usedName + '\n' + \
                                                                                         str(
                                                                                             self.seq[
                                                                                             final_end:]) + '\n'
                    self.dict_NCR_regions.setdefault("%s_end" % now_name, []).append(self.org_gb)
            ncr_name = last_name + "_" + now_name
            ##NCR
            if self.dict_args["extract_intergenic_regions"]:
                if (now_ini - (last_end + 1)) >= self.dict_args["intergenic_regions_threshold"]:
                    self.dict_feature_fas.setdefault("intergenic_regions", OrderedDict())[ ncr_name
                                                + '>' + self.organism + '_' + self.name] = '>' + self.usedName + '\n' + \
                                                                                           str(self.seq[last_end:(now_ini-1)]) + '\n'
                    self.dict_NCR_regions.setdefault(ncr_name, []).append(self.org_gb)
            ##Overlap
            if self.dict_args["extract_overlapping_regions"]:
                if last_end != self.dict_pairwise_features["last_end_temp"]:  ###有时候有gene，又有CDS，last_end与last_end_temp相同
                    diff = now_ini - (last_end + 1)
                    if diff < 0 and (abs(diff) >= self.dict_args["overlapping_regions_threshold"]):
                        self.dict_feature_fas.setdefault("overlapping_regions", OrderedDict())[ ncr_name
                                                    + '>' + self.organism + '_' + self.name] = '>' + self.usedName + '\n' + \
                                                                                           str(self.seq[(now_ini-1):last_end]) + '\n'
                        self.dict_overlapping_regions.setdefault(ncr_name, []).append(self.org_gb)
            ##设置last
            self.dict_pairwise_features["last_name"] = now_name
            self.dict_pairwise_features["last_end"] = self.dict_pairwise_features["last_end_temp"]
        except:
            pass

    def geneStatSlot(self, list_abbre):
        zip_taxonmy = list(zip(
            *self.list_all_taxonmy))  # [('Gyrodactylidae', 'Capsalidae', 'Ancyrocephalidae', 'Chauhaneidae'), ('Gyrodactylidea', 'Capsalidea', 'Dactylogyridea', 'Mazocraeidea'), ('Monogenea', 'Monogenea', 'Monogenea', 'Monogenea')]
        lineage = list(reversed(self.included_lineages))
        header_taxonmy = [[lineage[num]] + list(i) for num, i in enumerate(
            zip_taxonmy)]  # [['Family', 'Gyrodactylidae', 'Capsalidae', 'Ancyrocephalidae'], ['Superfamily', 'Gyrodactylidea', 'Capsalidea', 'Dactylogyridea'], ['Class', 'Monogenea', 'Monogenea', 'Monogenea']]
        # str_taxonmy = [lineage for lineage in header_taxonmy]
        zip_name = list(zip(list_abbre, self.list_name_gb))
        footnote = [[each_name[0] + ": " + " ".join(each_name[1])] for each_name in zip_name]
        return header_taxonmy, footnote

    def stat_PCG_sub(self, seq, strand):
        seqStat = SeqGrab(seq)
        PCGs_stat = ",".join(['PCGs',
                               strand,
                               seqStat.size,
                               seqStat.T_percent,
                               seqStat.C_percent,
                               seqStat.A_percent,
                               seqStat.G_percent,
                               seqStat.AT_percent,
                               seqStat.GC_percent,
                               seqStat.GT_percent,
                               seqStat.AT_skew,
                               seqStat.GC_skew]) + "\n"
        self.PCGsCodonSkew.append(",".join([self.usedName,
                                        self.organism,
                                        strand,
                                        seqStat.AT_skew,
                                        seqStat.GC_skew] + self.list_lineages) + "\n")
        first, second, third = seqStat.splitCodon()
        if self.dict_args["analyze 1st codon"]:
            seq = first
            seqStat = SeqGrab(seq)
            first_stat = ",".join(['1st codon position',
                                   strand,
                                   seqStat.size,
                                   seqStat.T_percent,
                                   seqStat.C_percent,
                                   seqStat.A_percent,
                                   seqStat.G_percent,
                                   seqStat.AT_percent,
                                   seqStat.GC_percent,
                                   seqStat.GT_percent,
                                   seqStat.AT_skew,
                                   seqStat.GC_skew]) + "\n"

            self.firstCodonSkew.append(",".join([self.usedName,
                                             self.organism,
                                             strand,
                                             seqStat.AT_skew,
                                             seqStat.GC_skew] + self.list_lineages) + "\n")
        else:
            first_stat = ""

        if self.dict_args["analyze 2nd codon"]:
            seq = second
            seqStat = SeqGrab(seq)
            second_stat = ",".join(['2nd codon position',
                                    strand,
                                    seqStat.size,
                                    seqStat.T_percent,
                                    seqStat.C_percent,
                                    seqStat.A_percent,
                                    seqStat.G_percent,
                                    seqStat.AT_percent,
                                    seqStat.GC_percent,
                                    seqStat.GT_percent,
                                    seqStat.AT_skew,
                                    seqStat.GC_skew]) + "\n"

            self.secondCodonSkew.append(",".join([self.usedName,
                                              self.organism,
                                              strand,
                                              seqStat.AT_skew,
                                              seqStat.GC_skew] + self.list_lineages) + "\n")
        else:
            second_stat = ""

        if self.dict_args["analyze 3rd codon"]:
            seq = third
            seqStat = SeqGrab(seq)
            third_stat = ",".join(['3rd codon position',
                                   strand,
                                   seqStat.size,
                                   seqStat.T_percent,
                                   seqStat.C_percent,
                                   seqStat.A_percent,
                                   seqStat.G_percent,
                                   seqStat.AT_percent,
                                   seqStat.GC_percent,
                                   seqStat.GT_percent,
                                   seqStat.AT_skew,
                                   seqStat.GC_skew]) + "\n"

            self.thirdCodonSkew.append(",".join([self.usedName,
                                             self.organism,
                                             strand,
                                             seqStat.AT_skew,
                                             seqStat.GC_skew] + self.list_lineages) + "\n")
        else:
            third_stat = ""

        if self.dict_args["analyze 1st codon"] and self.dict_args["analyze 2nd codon"]:
            seq = first + second
            seqStat = SeqGrab(seq)
            firstSecond_stat = ",".join(['1st+2nd codon position',
                                   strand,
                                   seqStat.size,
                                   seqStat.T_percent,
                                   seqStat.C_percent,
                                   seqStat.A_percent,
                                   seqStat.G_percent,
                                   seqStat.AT_percent,
                                   seqStat.GC_percent,
                                   seqStat.GT_percent,
                                   seqStat.AT_skew,
                                   seqStat.GC_skew]) + "\n"

            self.firstSecondCodonSkew.append(",".join([self.usedName,
                                             self.organism,
                                             strand,
                                             seqStat.AT_skew,
                                             seqStat.GC_skew] + self.list_lineages) + "\n")
        else:
            firstSecond_stat = ""
        return [PCGs_stat, first_stat, second_stat, third_stat]

    def geneStat_sub(self, name, seqStat):
        self.dict_gene_ATskews.setdefault(name, {}).setdefault(self.usedName,
                                                               seqStat.AT_skew if seqStat != "N/A" else "N/A")
        self.dict_gene_ATCont.setdefault(name, {}).setdefault(self.usedName,
                                                              seqStat.AT_percent if seqStat != "N/A" else "N/A")
        self.dict_gene_GCskews.setdefault(name, {}).setdefault(self.usedName,
                                                               seqStat.GC_skew if seqStat != "N/A" else "N/A")
        self.dict_gene_GCCont.setdefault(name, {}).setdefault(self.usedName,
                                                              seqStat.GC_percent if seqStat != "N/A" else "N/A")

    def stat_other_sub(self, seq, strand, flag):
        seqStat = SeqGrab(seq)
        stat_ = ",".join([flag,
                          strand,
                          seqStat.size,
                          seqStat.T_percent,
                          seqStat.C_percent,
                          seqStat.A_percent,
                          seqStat.G_percent,
                          seqStat.AT_percent,
                          seqStat.GC_percent,
                          seqStat.GT_percent,
                          seqStat.AT_skew,
                          seqStat.GC_skew]) + "\n"
        name = "%s(%s)"%(flag, strand)
        self.geneStat_sub(name, seqStat)
        return stat_

    def assignAbbre(self, abbreList):
        def abbreName(name, index):
            return name.split(' ')[0][0] + '_' + name.split(' ')[1][0:index] if " " in name else name[0]

        # 挑选可迭代对象里面相同的项
        def pickRepeate(list_):
            count_list_ = Counter(list_)
            # 挑选出不止出现一次的缩写
            return [key for key, value in count_list_.items() if value > 1]

        def assgn_abbre(list_repeate):
            # 种名
            list_name = []
            for i in list_repeate:
                list_org = i.split(" ")
                if len(list_org) <= 1:
                    list_name.append("name")
                else:
                    list_name.append(list_org[1])
            list_lenth = [len(l) for l in list_name]
            minLenth = min(list_lenth)
            # 如果2个物种属名不同，种名一样，那么就保持false
            flag = False
            for j in range(minLenth):
                if j > 0:
                    list_part = [k[0:j + 1] for k in list_name]
                    if len(set(list_part)) > 1:
                        flag = j + 1
                        break
            return flag

        list_abbre = []
        dict_list = OrderedDict()

        for num, i in enumerate(abbreList):
            # 先生成1的abbrevition，以筛选出一部分
            list_abbre.append(abbreName(i[0], 1))
            dict_list[num] = i
        # 挑选有重复的项
        repeate_keys = pickRepeate(list_abbre)
        if repeate_keys != []:
            for j in repeate_keys:
                list_repeate = []
                list_index = []
                for num, k in enumerate(list_abbre):
                    if j == k:
                        list_repeate.append(dict_list[num][0])
                        list_index.append(num)
                # 存在3个名字，其中2个拉丁名完全相同  Margarya monodi，Margarya monodi，Margarya
                # melanioides
                repeateNames = pickRepeate(list_repeate)
                # 如果没有完全一样的拉丁名
                if repeateNames == []:
                    # 找出缩写多少位比较合适
                    flag = assgn_abbre(list_repeate)
                    if flag:
                        # 替换缩写
                        for eachIndex in list_index:
                            list_abbre[eachIndex] = abbreName(
                                dict_list[eachIndex][0], flag)
                    # 如果2个物种属名不同，种名一样，那么就保持false
                    else:
                        for eachIndex in list_index:
                            list_abbre[eachIndex] += "_" + \
                                                     dict_list[eachIndex][1]
                # 2个或多个物种拉丁名完全相同的情况,附带上gb number
                else:
                    for eachIndex in list_index:
                        list_abbre[eachIndex] += "_" + dict_list[eachIndex][1]

        return list_abbre

    def numbered_Name(self, name, omit=False):
        list_names = list(self.dict_repeat_name_num.keys())
        # 如果这个name已经记录在字典里面了
        if name in list_names:
            numbered_name = name + str(self.dict_repeat_name_num[name])
            self.dict_repeat_name_num[name] += 1
        else:
            numbered_name = name + "1" if not omit else name
            self.dict_repeat_name_num[name] = 2
        return numbered_name

    def judge(self, name, values, seq, old_name=""):
        if (name.upper() in ['TRNA-LEU', 'TRNA-SER', "L", "S"]) or \
                (old_name.upper() in ['TRNA-LEU', 'TRNA-SER', "L", "S"]):
            if re.search(
                    r'(?<=[^1-9a-z_])(CUA|CUN|[tu]ag|L1|trnL1|Leu1)(?=[^1-9a-z_])',
                    values,
                    re.I):
                name = 'tRNA-Leu1' if name == 'tRNA-Leu' else "L1"
            elif re.search(r'(?<=[^1-9a-z_])(UUA|UUR|[tu]aa|L2|trnL2|Leu2)(?=[^1-9a-z_])', values, re.I):
                name = 'tRNA-Leu2' if name == 'tRNA-Leu' else "L2"
            elif re.search(r'(?<=[^1-9a-z_])(UCA|UCN|[tu]ga|S2|trnS2|Ser2)(?=[^1-9a-z_])', values, re.I):
                name = 'tRNA-Ser2' if name == 'tRNA-Ser' else "S2"
            elif re.search(r'(?<=[^1-9a-z_])(AGC|AGN|AGY|gc[tu]|[tu]c[tu]|S1|trnS1|Ser1)(?=[^1-9a-z_])', values, re.I):
                name = 'tRNA-Ser1' if name == 'tRNA-Ser' else "S1"
            else:
                # 单独把序列生成出来
                trnaName = self.factory.refineName(self.usedName +
                                                   "_" + str(self.start) + "_" + str(self.end), remain_words=".-")
                self.leu_ser.append(">%s\n%s\n" % (trnaName, seq))
        return name

    def fun_orgTable(self, new_name, size, ini, ter, seq):
        # 生成组成表相关
        orgSize = self.end - self.start + 1
        orgSize = orgSize if self.orgTable[-7:
                             ] != 'Strand\n' else int(size)
        space = self.start - self.lastEndIndex - 1
        if space > 0:
            self.gap += 1
        elif space < 0:
            self.overlap += 1
        overlap_start_index = abs(space) if space < 0 else 0  # 为了去掉重叠区
        space1 = "" if space == 0 or self.orgTable[-7:] == 'Strand\n' else str(
            space)
        chain = "H" if self.strand == "+" else "L"
        # 新增了添加序列功能
        self.orgTable.append(",".join([new_name,
                                   str(self.start),
                                   str(self.end),
                                   str(orgSize),
                                   space1,
                                   ini,
                                   ter,
                                   chain,
                                   seq]) + "\n")
        # if space > 0:
        #     self.NCR_seq.append(self.str_seq[self.lastEndIndex:self.start-1])
        self.lastEndIndex = self.end
        # 编码序列，负链基因反向互补
        if self.feature_type not in self.NCR_features:
            if chain == "H":
                self.plus_coding_seq.append(seq[overlap_start_index:])
                self.plus_coding_gene_only.append(seq[overlap_start_index:])
            # 如果space负的，就是重叠区，如果是正链的基因，就从序列头部减掉overlapping，如果是负链的基因，就从序列的尾部减去
            else:
                self.plus_coding_seq.append(str(Seq(seq, generic_dna).reverse_complement())[overlap_start_index:])
        # else:
        #     self.NCR_seq.append(seq)

    def gene_is_included(self, gene_name, list_genes, macroname="PCGs"):
        gene_name = gene_name.split("_copy")[0]  # 预防有copy的基因
        list_genes_copy = copy.deepcopy(list_genes)
        if macroname in list_genes:
            return True
        for name in ["PCGs", "tRNAs", "rRNAs", "NCR"]:
            if name in list_genes_copy:
                list_genes_copy.remove(name)
        rgx_gene_name = re.sub(r"(\d+\-\d+)", "[\\1]", "|".join(list_genes_copy))
        rgx_gene_name = "$|".join(rgx_gene_name.split("|")) + "$"
        rgx = re.compile(rgx_gene_name, re.I)
        if rgx.match(gene_name):
            return True
        return False

    def get_NCR_ratio(self, list_feature_pos, total_length):
        all_positions = list(FeatureLocation(0, total_length))
        list_ncr = list(set(all_positions).difference(set(list_feature_pos))) # [1,2,4,6,7...]
        # 方案一
        # list_ncr_pos = [FeatureLocation(i, i+1, strand=+1) for i in sorted(list_ncr)]
        # all_ncr_pos = CompoundLocation(list_ncr_pos)
        # all_ncr_seq = str(all_ncr_pos.extract(self.seq))
        # 方案二
        all_ncr_seq = "".join([self.seq[i] for i in sorted(list_ncr)])
        return len(list_ncr)/total_length, all_ncr_seq

class DetermineCopyGene(object):
    '''
            >if duplicated genes present in joint position, randomly remove one
            >remove genes with stop codons
            >align with close species, remove gene with high variability
            >compare GO with close species, retain genes with similar position
            # 计算 kaks
                https://www.biostars.org/p/5817/#google_vignette
                https://github.com/a1ultima/hpcleap_dnds/blob/master/py/scripts/dnds.py
            # 记得记录一下删除的原因啥的，给个文件
            # 测试：
                第一个和最后一个挨着的情况,多挨几个的情况
            # 在存文件之前执行这个方法
        :return:
        TODO: judge install kaks_caculator and mafft
             开始前清空一下路径，结束了也清空一下路径
             判断好以后，替换一下原文件的序列？
             要不要同一个目的都选同一个物种？
             修改对应序列的时候，似乎统计表里面的不好修改
             从gb文件里面删除，让用户再提取一次？
             open给个errors
             如果报错，定位到是哪个物种报错
        '''

    def __init__(self):
        self.factory = Factory()

    def exec_(self, result_path, work_dir, progressSig,
                           # kaks_cal_exe=r"C:\softwares\KaKs_Calculator\KaKs_Calculator.Windows.Command\KaKs_Calculator.exe",
                           mafft_exe=None):
        self.factory.creat_dir(work_dir)
        self.factory.remove_dir_directly(work_dir)
        go_file = f"{result_path}/files/linear_order.txt"
        taxonomy = f"{result_path}/StatFiles/taxonomy.csv"
        def is_consecutive_list(list_):
            list_.sort()
            range_list_=list(range(min(list_), max(list_)+1))
            # 如果不包含最后一个和开始的索引
            if list_ == range_list_:
                return True
            return False

        def is_consecutive(list_, total_list):
            list_total_indices = list(range(len(total_list)))
            # 如果不包含最后一个和开始的索引
            if is_consecutive_list(list_):
                return True
            # 如果最后一个元素和第一个元素在里面
            if (0 in list_) and (list_total_indices[-1] in list_):
                list_head = []
                list_tail = []
                for i in list_:
                    if list_head:
                        if ((i - list_head[-1])==1):
                            list_head.append(i)
                    else:
                        # 第一次
                        list_head.append(i)
                for j in reversed(list_):
                    if list_tail:
                        if (list_tail[-1] - j)==1:
                            list_tail.append(j)
                    else:
                        # 第一次
                        list_tail.append(j)
                if list(sorted(list_head+list_tail)) == list_:
                    return True
            return False

        # read gene order
        dict_gene_order= {}
        with open(go_file) as f2:
            line = f2.readline()
            while line:
                while not line.startswith('>') and line:
                    line = f2.readline()
                fas_name = line.strip().replace(">", "")
                goes = []
                line = f2.readline()
                while not line.startswith('>') and line:
                    goes.extend(line.strip().split("\t"))
                    line = f2.readline()
                dict_gene_order[fas_name] = goes
        progressSig.emit(5)
        if len(dict_gene_order) == 1:
            # 只有一条序列时返回
            progressSig.emit(100)
            return
        # optimize gene order
        result_array = [["Query species", "Reference species", "Reference selection criterion", "Gene name",
                         "Internal stop codons", "Similarity", "Chosen gene",
                         "Gene selection criterion"]]
        new_dict_GO = {}
        #转格式
        # self.progressDialog = self.factory.myProgressDialog(
        #     "Please Wait", "Converting format...", parent=self)
        # self.progressDialog.show()
        total = len(dict_gene_order)
        for num,spe in enumerate(dict_gene_order):
            list_goes = dict_gene_order[spe]
            list_new_GOs = list_goes[:]
            if "_copy" in "".join(list_goes):
                print(spe)
                dict_copied_go = {}
                for go in list_goes:
                    if "_copy" in go:
                        go_key = go.lstrip("-").split("_copy")[0]
                        dict_copied_go.setdefault(go_key, [go_key]).append(go)
                # print(dict_copied_go)
                # 判断GO
                for go_key in dict_copied_go:
                    original_gene_name = go_key if go_key in list_goes else f"-{go_key}"
                    # original_gene_index = list_goes.index(original_gene_name)
                    # list_indices = [original_gene_index] + [list_goes.index(i) for i in dict_copied_go[go_key][1:]]
                    # if is_consecutive(list_indices, list_goes):
                    #     # 如果copy的gene是连续的
                    #     pass
                    # 判断是否有内部终止密码子；以及通过选择压和比对相似度判断
                    # 选一个没有拷贝的参考物种？
                    # 能不能不放到这里无限循环？#######
                    ref_spe, ref_reason = self.pick_ref_spe(spe, taxonomy,
                                                            go_key, dict_gene_order)
                    if not ref_spe:
                        result_array.append([spe, "", "", "", "", "", "", "", ""])
                        continue
                    dict_folder_seqs = {}
                    for copied_gene in dict_copied_go[go_key]:
                        sub_folders = os.listdir(result_path)
                        for sub_folder in sub_folders:
                            if os.path.isdir(f"{result_path}/{sub_folder}"):
                                gene_name = copied_gene.lstrip('-')
                                # tRNA的名字可能不同
                                gene_name2 = f"trn{gene_name}"
                                gene_file = f"{result_path}/{sub_folder}/{gene_name}.fas"
                                gene_file2 = f"{result_path}/{sub_folder}/{gene_name2}.fas"
                                if os.path.exists(gene_file):
                                    dict_folder_seqs.setdefault(sub_folder, []).append(gene_file)
                                elif os.path.exists(gene_file2):
                                    dict_folder_seqs.setdefault(sub_folder, []).append(gene_file2)
                    # 确定一个subfolder，然后提取对应序列出来做分析
                    def get_seq(file, name_):
                        rgx_seq = re.compile(f">{name_}([^>]+)")
                        with open(file) as f:
                            content = f.read()
                        return re.sub(r"\s", "", rgx_seq.search(content).group(1))
                    is_PCG = False
                    if "CDS_NUC" in dict_folder_seqs:
                        # PCGs,可以用内部终止密码子、选择压力、序列相似度来判断
                        is_PCG = True
                        list_seq_files = dict_folder_seqs["CDS_NUC"]
                        ref_seq = get_seq(f"{result_path}/CDS_NUC/{original_gene_name.lstrip('-')}.fas",
                                          ref_spe)
                    else:
                        if not dict_folder_seqs:
                            # 没找到任何序列的时候怎么办？
                            list_seq_files = []
                        # non PCGs
                        elif (len(dict_folder_seqs) > 1):
                            if ("gene" in dict_folder_seqs):
                                dict_folder_seqs.pop("gene")
                            subfolder = random.choice(list(dict_folder_seqs.keys()))
                            list_seq_files = dict_folder_seqs[subfolder]
                            file = f"{result_path}/{subfolder}/{original_gene_name.lstrip('-')}.fas"
                            if subfolder == "tRNA":
                                file1 = f"{result_path}/{subfolder}/trn{original_gene_name.lstrip('-')}.fas"
                                if os.path.exists(file1):
                                    file = file1
                            ref_seq = get_seq(file, ref_spe)
                        else:
                            subfolder = random.choice(list(dict_folder_seqs.keys()))
                            list_seq_files = dict_folder_seqs[subfolder]
                            file = f"{result_path}/{subfolder}/{original_gene_name.lstrip('-')}.fas"
                            if subfolder == "tRNA":
                                file1 = f"{result_path}/{subfolder}/trn{original_gene_name.lstrip('-')}.fas"
                                if os.path.exists(file1):
                                    file = file1
                            ref_seq = get_seq(file, ref_spe)
                    # 提取序列，进行计算
                    def fetch_code_table(species_table, spe):
                        with open(species_table) as f:
                            list_ = list(csv.reader(f, skipinitialspace=True))
                        header = list_.pop(0)
                        code_table_index = header.index("Code table")
                        spe_index = header.index("Tree_Name")
                        for line in list_:
                            spe_ = line[spe_index]
                            if spe_ == spe:
                                return int(line[code_table_index])
                        return 1
                    # 判断哪个才是原本的基因
                    def log(x):
                        n = 1000.0
                        return n * ((x ** (1/n)) - 1)

                    def get_target_gene(dict_inter_stop, dict_omega, dict_similarity):
                        if dict_inter_stop and len(set(dict_inter_stop.values()))>1:
                            return min(dict_inter_stop, key=lambda x: dict_inter_stop[x]), "fewer interal stop codons"
                        elif dict_similarity:
                            if len(set(dict_similarity.values()))>1:
                                return max(dict_similarity, key=lambda x: dict_similarity[x]), "highest similarity to the reference gene"
                            else:
                                return random.choice(list(dict_similarity.keys())), "randomly chosen (selection criteria were the same)"
                        elif dict_omega and len(set(dict_omega.values()))>1:
                            return max(dict_omega, key = lambda x: abs(log(dict_omega[x]))), "stongest selection pressure"
                        else:
                            return "", "No best gene"

                    temp_dir = f"{work_dir}/tmp"
                    os.makedirs(temp_dir, exist_ok=True)
                    dict_inter_stop = {}
                    dict_omega = {}
                    dict_similarity = {}
                    list_spe_array = []
                    list_copied_gene_names = []
                    if list_seq_files:
                        # 比对，如果是PCG，用密码子比对
                        for seq_file in list_seq_files:
                            tmp_seq_file = f"{temp_dir}/{uuid.uuid1()}.fas"
                            seq = get_seq(seq_file, spe)
                            gene_name = os.path.splitext(os.path.basename(seq_file))[0]
                            list_copied_gene_names.append(gene_name)
                            with open(tmp_seq_file, "w") as f:
                                f.write(f">{ref_spe}\n{ref_seq}\n>{spe}\n{seq}\n")
                            if is_PCG:
                                code_table = fetch_code_table(f"{result_path}/StatFiles/species_info.csv", spe)
                                table = CodonTable.ambiguous_dna_by_id[code_table]
                                # 计算内部终止密码子
                                protein = _translate_str(seq, table)
                                # 去除终止密码子再比较
                                protein = protein[:-1] if protein.endswith("*") else protein
                                inter_stop_num = protein.count("*")
                                dict_inter_stop[gene_name] = inter_stop_num
                                # 比对
                                aligned_fas = self.align(mafft_exe, tmp_seq_file, work_dir,
                                                         code_table, is_PCGs=is_PCG)
                                if os.path.getsize(aligned_fas):
                                    # # 计算omega
                                    # omega = self.kaks(kaks_cal_exe, aligned_fas, code_table, work_dir)
                                    # dict_omega[gene_name] = omega
                                    # 计算similarity
                                    similarity = self.similarity(aligned_fas)
                                    dict_similarity[gene_name] = similarity
                                    list_spe_array.append([spe, ref_spe, ref_reason, gene_name, inter_stop_num,
                                                            similarity])
                                else:
                                    # 比对文件是空的
                                    list_spe_array.append([spe, ref_spe, ref_reason, gene_name, inter_stop_num,
                                                           ""])
                            else:
                                # 比对
                                aligned_fas = self.align(mafft_exe, tmp_seq_file, work_dir,
                                                         None, is_PCGs=is_PCG)
                                if os.path.getsize(aligned_fas):
                                    # 计算similarity
                                    similarity = self.similarity(aligned_fas)
                                    dict_similarity[gene_name] = similarity
                                    list_spe_array.append([spe, ref_spe, ref_reason, gene_name, "", similarity])
                                else:
                                    list_spe_array.append([spe, ref_spe, ref_reason, gene_name, "", ""])
                        target_gene, reason = get_target_gene(dict_inter_stop, dict_omega, dict_similarity)
                        for i in list_spe_array:
                            result_array.append(i + [target_gene, reason])
                        # 修改提取的序列，以及gene order等处
                        # 蛋白序列有好几个文件夹，要怎么删？管他三七二十一，循环读每个文件，再来删？
                        # 再删除一下gb文件，生成新的gb文件，with duplicates删除
                        # 加上续删功能？
                        def to_seq_removed(list_names, origin_name, spe, folder, target_gene):
                            dir_removed = f"{folder}/removed_seqs"
                            self.factory.creat_dirs(dir_removed)
                            def remove_gene(gene_name, folder, rmv_folder, spe, origin=False):
                                # 提取序列，加入到原基因文件
                                gene_name = gene_name if os.path.exists(f"{folder}/{gene_name}.fas") else f"trn{gene_name}"
                                gene_file = f"{folder}/{gene_name}.fas"
                                with open(gene_file) as f2:
                                    content = f2.read()
                                # 提取序列，并存到文件
                                # print(gene_file, spe, content)
                                rgx_seq = re.compile(f">{spe}([^>]+)")
                                seq = re.sub(r"\s", "", rgx_seq.search(content).group(1))
                                with open(f"{rmv_folder}/{spe}_{gene_name}_removed.fas", "w") as f:
                                    f.write(f">{spe}\n{seq}\n")
                                # 删除原文件的序列
                                new_content = re.sub(f">{spe}[^>]+", "", content)
                                if ">" not in new_content:
                                    # 如果没有序列了，就删除文件
                                    if not origin:
                                        os.remove(gene_file)
                                else:
                                    with open(gene_file, "w") as f3:
                                        f3.write(new_content)
                                return gene_file, gene_name
                            if origin_name == target_gene:
                                # 只用删除copy_gene
                                list_names.remove(target_gene)
                                for gene in list_names:
                                    remove_gene(gene, folder, dir_removed, spe)
                            else:
                                # 先从原文件提取基因序列出来删掉
                                origin_gene_file, origin_name = remove_gene(origin_name, folder, dir_removed, spe, origin=True)
                                # 再从目标基因提取序列存到原文件，其余序列删掉
                                target_file = f"{folder}/{target_gene}.fas"
                                with open(target_file) as f4:
                                    target_content = f4.read()
                                target_seq = re.sub(r"\s", "", re.search(f">{spe}([^>]+)", target_content).group(1))
                                ## 追加方式存到原文件
                                with open(origin_gene_file, "a") as f:
                                    f.write(f"\n>{spe}\n{target_seq}\n")
                                ## 删除target gene file的序列
                                new_content = re.sub(f">{spe}[^>]+", "", target_content)
                                if ">" not in new_content:
                                    # 如果没有序列了，就删除文件
                                    os.remove(target_file)
                                else:
                                    with open(target_file, "w") as f3:
                                        f3.write(new_content)
                                # 删除其余序列
                                remain_genes = [i for i in list_names if i not in [target_gene, origin_name]]
                                if remain_genes:
                                    for remain_gene in remain_genes:
                                        remove_gene(remain_gene, folder, dir_removed, spe)
                        original_name = target_gene.lstrip("-").split("_copy")[0]
                        sub_folders = os.listdir(result_path)
                        for sub_folder in sub_folders:
                            if os.path.isdir(f"{result_path}/{sub_folder}"):
                                list_ = []
                                for gene in list_copied_gene_names:
                                    file = f"{result_path}/{sub_folder}/{gene}.fas"
                                    if os.path.exists(file):
                                        list_.append(True)
                                    elif (sub_folder=="tRNA") and os.path.exists(f"{result_path}/{sub_folder}/trn{gene}.fas"):
                                        list_.append(True)
                                    else:
                                        list_.append(False)
                                if set(list_) == {True}:
                                    to_seq_removed(list_copied_gene_names[:], original_name,
                                                    spe, f"{result_path}/{sub_folder}",
                                                    target_gene)
                        # 删除gb文件里面的？
                        # 删除gene order文件里面的？
                        # 要等这个物种的序列删完？？？？
                        list_copied_gene_names.remove(target_gene)
                        list_new_GOs = [i for i in list_new_GOs if (i.lstrip("-") not in list_copied_gene_names) and
                                                 (f"trn{i.lstrip('-')}" not in list_copied_gene_names)
                            ]
                        # print(list_copied_gene_names, list_new_GOs)
                    else:
                        result_array.append([spe, ref_spe, ref_reason, "", "", "", "", ""])
            new_dict_GO[spe] = list_new_GOs
            progressSig.emit(5 + ((num+1)/total)*90)
        result_array.append([])
        result_array.append(["Note that duplicated genes in the 'Gene name' column are named in the order they were "
                             "extracted from the genome; for example, if a species has three cox1 genes, the first one "
                             "will be named cox1, the second one cox1_copy2, and the third one cox1_copy3."])
        self.factory.write_csv_file(f"{work_dir}/gene_copy_array.csv", result_array, silence=True)
        # 存 GO
        new_go_file = f"{result_path}/files/linear_order_rmv_duplicates.txt"
        with open(new_go_file, "w") as f:
            go_str = "\n".join([f">{spe}\n" + "\t".join(new_dict_GO[spe]) for spe in new_dict_GO])
            go_str = re.sub("_copy\d+", "", go_str)
            f.write(go_str)
        progressSig.emit(100)
        return result_array

    def run_command(self, commands, popen):
        stdout = [f"{commands}\n"]
        while True:
            try:
                out_line = popen.stdout.readline().decode("utf-8", errors='ignore')
            except UnicodeDecodeError:
                out_line = popen.stdout.readline().decode("gbk", errors='ignore')
            if out_line == "" and popen.poll() is not None:
                break
            stdout.append(out_line)
        return "".join(stdout)

    def align(self, mafft_exe, seq_file, work_dir, code_table, is_PCGs=False):
        dict_args = {}
        dict_args["mafft_exe"] = mafft_exe
        dict_args["vessel"] = f"{work_dir}/mafft_vessel/{uuid.uuid1()}"
        dict_args["exportPath"] = f"{dict_args['vessel']}/mafft_alignment"
        self.factory.creat_dir(dict_args["exportPath"])
        self.factory.remove_dir_directly(dict_args["exportPath"])
        dict_args["filenames"] = [seq_file]
        dict_args["progressSig"] = None
        file_base = os.path.basename(seq_file)
        if is_PCGs:
            dict_args["codon"] = code_table
            dict_args["vessel_aaseq"] = f"{dict_args['vessel']}/AA_sequence"
            dict_args["vessel_aalign"] = f"{dict_args['vessel']}/AA_alignments"
            # 翻译为氨基酸
            self.factory.creat_dir(dict_args["vessel"])
            self.factory.remove_dir_directly(dict_args["vessel"])
            self.factory.creat_dir(dict_args["vessel_aaseq"])
            self.factory.creat_dir(dict_args["vessel_aalign"])
            # 翻译氨基酸，保存AA文件，映射
            codonAlign = CodonAlign(**dict_args)
            # 比对
            align_file = os.path.join(dict_args["vessel_aaseq"], file_base)
            commands = f'"{dict_args["mafft_exe"]}" --auto --inputorder "{align_file}" > ' \
                       f'"{dict_args["vessel_aalign"]}/{file_base}"'
        else:
            commands = f'"{dict_args["mafft_exe"]}" --auto --inputorder "{seq_file}" > ' \
                       f'"{dict_args["exportPath"]}/{file_base}"'
        popen = self.factory.init_popen(commands)
        self.run_command(commands, popen)
        if is_PCGs:
            codonAlign.back_trans()  # 生成回译的codon文件
            split_ext = os.path.splitext(file_base)  # 为了加后缀
            aligned_file = dict_args["exportPath"] + os.sep + "_mafft".join(split_ext)
        else:
            aligned_file = f'{dict_args["exportPath"]}/{file_base}'
        return aligned_file

    def kaks(self, kaks_cal_exe, alignment, code_table, work_dir, method="NG"):
        kaks_dir = f"{work_dir}/kaks"
        self.factory.creat_dir(kaks_dir)
        # 转为AXT格式
        self.convertfmt = Convertfmt(**{"export_path": kaks_dir, "files": [alignment],
                                        "export_axt": True})
        self.convertfmt.exec_()
        axt = self.convertfmt.axt_file
        # 计算kaks
        output_file = f"{kaks_dir}/{os.path.basename(axt)}.kaks"
        commands = f"{kaks_cal_exe} -i {axt} -o {output_file} " \
                   f"-c {code_table} -m {method}"
        popen = self.factory.init_popen(commands)
        log_ = self.run_command(commands, popen)
        # print(log_)
        with open(output_file) as f:
            list_lines = f.readlines()
        headers = list_lines.pop(0).strip().split("\t")
        kaks_index = headers.index("Ka/Ks")
        return float(list_lines[0].strip().split("\t")[kaks_index])

    def similarity(self, alignment):
        # 序列成对，生成相似性矩阵
        aln = AlignIO.read(open(alignment), 'fasta')
        calculator = DistanceCalculator('identity')
        return 1 - calculator.get_distance(aln).matrix[1][0]

    def pick_ref_spe(self, query_spe, taxonomy, gene, dict_gene_order):
        '''
            从同一个属开始找，如果没有就同一个科，再不行就同一个目
            参考物种不能有目标基因的重复
            gene: 基因名字，需要是不带正负号信息以及带copy信息的基因名字
            query_spe：需要tree name
            taxonomy：需要提取出来的分类表
            dict_gene_order：以tree name为键，基因顺序为列表
        :return:
        '''
        tax_list = ["Genus", "Family", "Order", "Class", "Phylum"]
        # 得到所有物种对应的分类
        if not hasattr(self, "dict_spe_tax"):
            with open(taxonomy) as f:
                list_ = list(csv.reader(f, skipinitialspace=True))
            header = list_.pop(0)
            org_index = header.index("Organism")
            tree_name_index = header.index("Tree name")
            spe_list = [[i[org_index], i[tree_name_index]] for num,i in enumerate(list_)]
            self.dict_spe_tax = {}
            for j in spe_list:
                organism, tree_name = j
                taxs = self.get_lineages(organism, tax_list)
                if not taxs:
                    taxs = self.get_lineages(organism.split()[0], tax_list)
                if taxs:
                    self.dict_spe_tax[tree_name] = taxs

        def count_tax(tax, dict_spe_tax):
            list_ = []
            for spe in dict_spe_tax:
                if tax in dict_spe_tax[spe]:
                    list_.append(spe)
            return list_
        if query_spe in self.dict_spe_tax:
            query_spe_tax = self.dict_spe_tax[query_spe]
            for num,tax in enumerate(query_spe_tax):
                tax_name = tax_list[num]
                list_tax_spe = count_tax(tax, self.dict_spe_tax)
                list_tax_spe.remove(query_spe)
                # print(tax_name, list_tax_spe)
                if list_tax_spe:
                    # 判断选出来的物种里面有没有目标基因
                    while list_tax_spe:
                        random_spe = random.choice(list_tax_spe)
                        gos = dict_gene_order[random_spe]
                        if (gene not in gos) and (f"-{gene}" not in gos):
                            list_tax_spe.remove(random_spe)
                        elif gene + "_copy" in "".join(gos):
                            # 有拷贝基因也不行
                            list_tax_spe.remove(random_spe)
                        else:
                            return [random_spe, f"the same {tax_name}"]
            return None, None
        else:
            # 如果query_spe都没有分类
            return None, None

    def get_lineages(self, name, tax_list):
        ncbi = NCBITaxa()
        query_id = ncbi.get_name_translator([name])
        if query_id:
            query_id = query_id[name][0]
            lineage_ids = ncbi.get_lineage(query_id)
            dict_id_rank = ncbi.get_rank(lineage_ids)
            dict_id_name = ncbi.get_taxid_translator(lineage_ids)
            dict_rank_name = {dict_id_rank[id].upper():dict_id_name[id] for id in dict_id_name}
            taxs = []
            for tax in tax_list:
                if tax.upper() in dict_rank_name:
                    taxs.append(dict_rank_name[tax.upper()])
                else:
                    taxs.append("")
            return taxs
        else:
            return False

class DetermineCopyGeneParallel(object):
    '''
            >if duplicated genes present in joint position, randomly remove one
            >remove genes with stop codons
            >align with close species, remove gene with high variability
            >compare GO with close species, retain genes with similar position
            # 计算 kaks
                https://www.biostars.org/p/5817/#google_vignette
                https://github.com/a1ultima/hpcleap_dnds/blob/master/py/scripts/dnds.py
            # 记得记录一下删除的原因啥的，给个文件
            # 测试：
                第一个和最后一个挨着的情况,多挨几个的情况
            # 在存文件之前执行这个方法
        :return:
        TODO: judge install kaks_caculator and mafft
             开始前清空一下路径，结束了也清空一下路径
             判断好以后，替换一下原文件的序列？
             要不要同一个目的都选同一个物种？
             修改对应序列的时候，似乎统计表里面的不好修改
             从gb文件里面删除，让用户再提取一次？
             open给个errors
             如果报错，定位到是哪个物种报错
        '''

    def __init__(self):
        pass

    def exec_(self, result_path, work_dir, # progressSig,
              # kaks_cal_exe=r"C:\softwares\KaKs_Calculator\KaKs_Calculator.Windows.Command\KaKs_Calculator.exe",
              mafft_exe=r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\plugins\mafft-win\mafft.bat",
              threads=8):
        '''
        obseleted!!!

        Parameters
        ----------
        result_path
        work_dir
        mafft_exe
        threads

        Returns
        -------

        '''
        factory = Factory()
        factory.creat_dir(work_dir)
        factory.remove_dir_directly(work_dir)
        go_file = f"{result_path}/files/linear_order.txt"
        taxonomy = f"{result_path}/StatFiles/taxonomy.csv"
        def is_consecutive_list(list_):
            list_.sort()
            range_list_=list(range(min(list_), max(list_)+1))
            # 如果不包含最后一个和开始的索引
            if list_ == range_list_:
                return True
            return False

        def is_consecutive(list_, total_list):
            list_total_indices = list(range(len(total_list)))
            # 如果不包含最后一个和开始的索引
            if is_consecutive_list(list_):
                return True
            # 如果最后一个元素和第一个元素在里面
            if (0 in list_) and (list_total_indices[-1] in list_):
                list_head = []
                list_tail = []
                for i in list_:
                    if list_head:
                        if ((i - list_head[-1])==1):
                            list_head.append(i)
                    else:
                        # 第一次
                        list_head.append(i)
                for j in reversed(list_):
                    if list_tail:
                        if (list_tail[-1] - j)==1:
                            list_tail.append(j)
                    else:
                        # 第一次
                        list_tail.append(j)
                if list(sorted(list_head+list_tail)) == list_:
                    return True
            return False

        # read gene order
        dict_gene_order= {}
        with open(go_file) as f2:
            line = f2.readline()
            while line:
                while not line.startswith('>') and line:
                    line = f2.readline()
                fas_name = line.strip().replace(">", "")
                goes = []
                line = f2.readline()
                while not line.startswith('>') and line:
                    goes.extend(line.strip().split("\t"))
                    line = f2.readline()
                dict_gene_order[fas_name] = goes
        # progressSig.emit(5)
        if len(dict_gene_order) == 1:
            # 只有一条序列时返回
            # progressSig.emit(100)
            return
        # optimize gene order
        result_array = [["Query species", "Reference species", "Reference selection criterion", "Gene name",
                         "Internal stop codons", "Similarity", "Chosen gene",
                         "Gene selection criterion"]]
        new_dict_GO = {}
        #转格式
        # self.progressDialog = factory.myProgressDialog(
        #     "Please Wait", "Converting format...", parent=self)
        # self.progressDialog.show()
        total = len(dict_gene_order)
        pool = Pool(processes=threads)
        try:
            r = [pool.apply_async(self.run_slot, (spe, dict_gene_order, taxonomy,
                                                  result_path, work_dir, mafft_exe)) for spe in dict_gene_order]
            pool.close()
            for num,item in enumerate(r):
                item.wait(timeout=9999)  # Without a timeout, you can't interrupt this.
                list_array, list_new_GOs, spe = item.get()
                new_dict_GO[spe] = list_new_GOs
                result_array.extend(list_array)
                # progressSig.emit(5 + ((num+1)/total)*90)
        except KeyboardInterrupt:
            pool.terminate()
        finally:
            pool.join()

        result_array.append([])
        result_array.append(["Note that duplicated genes in the 'Gene name' column are named in the order they were "
                             "extracted from the genome; for example, if a species has three cox1 genes, the first one "
                             "will be named cox1, the second one cox1_copy2, and the third one cox1_copy3."])
        factory.write_csv_file(f"{work_dir}/duplicates_resolving_details.csv", result_array, silence=True)
        # 存 GO
        new_go_file = f"{result_path}/files/linear_order_rmv_duplicates.txt"
        with open(new_go_file, "w") as f:
            go_str = "\n".join([f">{spe}\n" + "\t".join(new_dict_GO[spe]) for spe in new_dict_GO])
            go_str = re.sub("_copy\d+", "", go_str)
            f.write(go_str)
        # progressSig.emit(100)
        return result_array

    def run_slot(self, spe, dict_gene_order, taxonomy, result_path, work_dir, mafft_exe):
        '''

        obseleted!!!

        Parameters
        ----------
        spe
        dict_gene_order
        taxonomy
        result_path
        work_dir
        mafft_exe

        Returns
        -------

        '''
        factory = Factory()
        list_goes = dict_gene_order[spe]
        list_new_GOs = list_goes[:]
        list_array = []
        if "_copy" in "".join(list_goes):
            print(spe)
            dict_copied_go = {}
            for go in list_goes:
                if "_copy" in go:
                    go_key = go.lstrip("-").split("_copy")[0]
                    dict_copied_go.setdefault(go_key, [go_key]).append(go)
            # print(dict_copied_go)
            # 判断GO
            for go_key in dict_copied_go:
                original_gene_name = go_key if go_key in list_goes else f"-{go_key}"
                # original_gene_index = list_goes.index(original_gene_name)
                # list_indices = [original_gene_index] + [list_goes.index(i) for i in dict_copied_go[go_key][1:]]
                # if is_consecutive(list_indices, list_goes):
                #     # 如果copy的gene是连续的
                #     pass
                # 判断是否有内部终止密码子；以及通过选择压和比对相似度判断
                # 选一个没有拷贝的参考物种？
                # 能不能不放到这里无限循环？#######
                ref_spe, ref_reason = self.pick_ref_spe(spe, taxonomy,
                    go_key, dict_gene_order)
                if not ref_spe:
                    continue
                dict_folder_seqs = {}
                for copied_gene in dict_copied_go[go_key]:
                    sub_folders = os.listdir(result_path)
                    for sub_folder in sub_folders:
                        if os.path.isdir(f"{result_path}/{sub_folder}"):
                            gene_name = copied_gene.lstrip('-')
                            # tRNA的名字可能不同
                            gene_name2 = f"trn{gene_name}"
                            gene_file = f"{result_path}/{sub_folder}/{gene_name}.fas"
                            gene_file2 = f"{result_path}/{sub_folder}/{gene_name2}.fas"
                            if os.path.exists(gene_file):
                                dict_folder_seqs.setdefault(sub_folder, []).append(gene_file)
                            elif os.path.exists(gene_file2):
                                dict_folder_seqs.setdefault(sub_folder, []).append(gene_file2)
                # 确定一个subfolder，然后提取对应序列出来做分析
                def get_seq(file, name_):
                    rgx_seq = re.compile(f">{name_}([^>]+)")
                    with open(file) as f:
                        content = f.read()
                    return re.sub(r"\s", "", rgx_seq.search(content).group(1))
                is_PCG = False
                if "CDS_NUC" in dict_folder_seqs:
                    # PCGs,可以用内部终止密码子、选择压力、序列相似度来判断
                    is_PCG = True
                    list_seq_files = dict_folder_seqs["CDS_NUC"]
                    ref_seq = get_seq(f"{result_path}/CDS_NUC/{original_gene_name.lstrip('-')}.fas",
                        ref_spe)
                else:
                    if not dict_folder_seqs:
                        # 没找到任何序列的时候怎么办？
                        list_seq_files = []
                    # non PCGs
                    elif (len(dict_folder_seqs) > 1):
                        if ("gene" in dict_folder_seqs):
                            dict_folder_seqs.pop("gene")
                        subfolder = random.choice(list(dict_folder_seqs.keys()))
                        list_seq_files = dict_folder_seqs[subfolder]
                        file = f"{result_path}/{subfolder}/{original_gene_name.lstrip('-')}.fas"
                        if subfolder == "tRNA":
                            file1 = f"{result_path}/{subfolder}/trn{original_gene_name.lstrip('-')}.fas"
                            if os.path.exists(file1):
                                file = file1
                        ref_seq = get_seq(file, ref_spe)
                    else:
                        subfolder = random.choice(list(dict_folder_seqs.keys()))
                        list_seq_files = dict_folder_seqs[subfolder]
                        file = f"{result_path}/{subfolder}/{original_gene_name.lstrip('-')}.fas"
                        if subfolder == "tRNA":
                            file1 = f"{result_path}/{subfolder}/trn{original_gene_name.lstrip('-')}.fas"
                            if os.path.exists(file1):
                                file = file1
                        ref_seq = get_seq(file, ref_spe)
                # 提取序列，进行计算
                def fetch_code_table(species_table, spe):
                    with open(species_table) as f:
                        list_ = list(csv.reader(f, skipinitialspace=True))
                    header = list_.pop(0)
                    code_table_index = header.index("Code table")
                    spe_index = header.index("Tree_Name")
                    for line in list_:
                        spe_ = line[spe_index]
                        if spe_ == spe:
                            return int(line[code_table_index])
                    return 1
                # 判断哪个才是原本的基因
                def log(x):
                    n = 1000.0
                    return n * ((x ** (1/n)) - 1)

                def get_target_gene(dict_inter_stop, dict_omega, dict_similarity):
                    if dict_inter_stop and len(set(dict_inter_stop.values()))>1:
                        return min(dict_inter_stop, key=lambda x: dict_inter_stop[x]), "fewer interal stop codons"
                    elif dict_similarity:
                        if len(set(dict_similarity.values()))>1:
                            return max(dict_similarity, key=lambda x: dict_similarity[x]), "highest similarity to the reference gene"
                        else:
                            return random.choice(list(dict_similarity.keys())), "randomly chosen (selection criteria were the same)"
                    elif dict_omega and len(set(dict_omega.values()))>1:
                        return max(dict_omega, key = lambda x: abs(log(dict_omega[x]))), "strongest selection pressure"
                    else:
                        return "", "No best gene"

                temp_dir = f"{work_dir}/tmp"
                os.makedirs(temp_dir, exist_ok=True)
                dict_inter_stop = {}
                dict_omega = {}
                dict_similarity = {}
                list_spe_array = []
                list_copied_gene_names = []
                if list_seq_files:
                    # 比对，如果是PCG，用密码子比对
                    for seq_file in list_seq_files:
                        tmp_seq_file = f"{temp_dir}/{uuid.uuid1()}.fas"
                        seq = get_seq(seq_file, spe)
                        gene_name = os.path.splitext(os.path.basename(seq_file))[0]
                        list_copied_gene_names.append(gene_name)
                        with open(tmp_seq_file, "w") as f:
                            f.write(f">{ref_spe}\n{ref_seq}\n>{spe}\n{seq}\n")
                        if is_PCG:
                            code_table = fetch_code_table(f"{result_path}/StatFiles/species_info.csv", spe)
                            table = CodonTable.ambiguous_dna_by_id[code_table]
                            # 计算内部终止密码子
                            protein = _translate_str(seq, table)
                            # 去除终止密码子再比较
                            protein = protein[:-1] if protein.endswith("*") else protein
                            inter_stop_num = protein.count("*")
                            dict_inter_stop[gene_name] = inter_stop_num
                            # 比对
                            aligned_fas = self.align(mafft_exe, tmp_seq_file, work_dir,
                                code_table, is_PCGs=is_PCG)
                            if os.path.getsize(aligned_fas):
                                # # 计算omega
                                # omega = self.kaks(kaks_cal_exe, aligned_fas, code_table, work_dir)
                                # dict_omega[gene_name] = omega
                                # 计算similarity
                                similarity = self.similarity(aligned_fas)
                                dict_similarity[gene_name] = similarity
                                list_spe_array.append([spe, ref_spe, ref_reason, gene_name, inter_stop_num,
                                                       similarity])
                            else:
                                # 比对文件是空的
                                list_spe_array.append([spe, ref_spe, ref_reason, gene_name, inter_stop_num,
                                                       ""])
                        else:
                            # 比对
                            aligned_fas = self.align(mafft_exe, tmp_seq_file, work_dir,
                                None, is_PCGs=is_PCG)
                            if os.path.getsize(aligned_fas):
                                # 计算similarity
                                similarity = self.similarity(aligned_fas)
                                dict_similarity[gene_name] = similarity
                                list_spe_array.append([spe, ref_spe, ref_reason, gene_name, "", similarity])
                            else:
                                list_spe_array.append([spe, ref_spe, ref_reason, gene_name, "", ""])
                    target_gene, reason = get_target_gene(dict_inter_stop, dict_omega, dict_similarity)
                    for i in list_spe_array:
                        list_array.append(i + [target_gene, reason])
                    # 修改提取的序列，以及gene order等处
                    # 蛋白序列有好几个文件夹，要怎么删？管他三七二十一，循环读每个文件，再来删？
                    # 再删除一下gb文件，生成新的gb文件，with duplicates删除
                    # 加上续删功能？
                    def to_seq_removed(list_names, origin_name, spe, folder, target_gene):
                        dir_removed = f"{folder}/removed_seqs"
                        factory.creat_dirs(dir_removed)
                        def remove_gene(gene_name, folder, rmv_folder, spe, origin=False):
                            # 提取序列，加入到原基因文件
                            gene_name = gene_name if os.path.exists(f"{folder}/{gene_name}.fas") else f"trn{gene_name}"
                            gene_file = f"{folder}/{gene_name}.fas"
                            with open(gene_file) as f2:
                                content = f2.read()
                            # 提取序列，并存到文件
                            # print(gene_file, spe, content)
                            rgx_seq = re.compile(f">{spe}([^>]+)")
                            seq = re.sub(r"\s", "", rgx_seq.search(content).group(1))
                            with open(f"{rmv_folder}/{spe}_{gene_name}_removed.fas", "w") as f:
                                f.write(f">{spe}\n{seq}\n")
                            # 删除原文件的序列
                            new_content = re.sub(f">{spe}[^>]+", "", content)
                            if ">" not in new_content:
                                # 如果没有序列了，就删除文件
                                if not origin:
                                    os.remove(gene_file)
                            else:
                                with open(gene_file, "w") as f3:
                                    f3.write(new_content)
                            return gene_file, gene_name
                        if origin_name == target_gene:
                            # 只用删除copy_gene
                            list_names.remove(target_gene)
                            for gene in list_names:
                                remove_gene(gene, folder, dir_removed, spe)
                        else:
                            # 先从原文件提取基因序列出来删掉
                            origin_gene_file, origin_name = remove_gene(origin_name, folder, dir_removed, spe, origin=True)
                            # 再从目标基因提取序列存到原文件，其余序列删掉
                            target_file = f"{folder}/{target_gene}.fas"
                            with open(target_file) as f4:
                                target_content = f4.read()
                            target_seq = re.sub(r"\s", "", re.search(f">{spe}([^>]+)", target_content).group(1))
                            ## 追加方式存到原文件
                            with open(origin_gene_file, "a") as f:
                                f.write(f"\n>{spe}\n{target_seq}\n")
                            ## 删除target gene file的序列
                            new_content = re.sub(f">{spe}[^>]+", "", target_content)
                            if ">" not in new_content:
                                # 如果没有序列了，就删除文件
                                os.remove(target_file)
                            else:
                                with open(target_file, "w") as f3:
                                    f3.write(new_content)
                            # 删除其余序列
                            remain_genes = [i for i in list_names if i not in [target_gene, origin_name]]
                            if remain_genes:
                                for remain_gene in remain_genes:
                                    remove_gene(remain_gene, folder, dir_removed, spe)
                    original_name = target_gene.lstrip("-").split("_copy")[0]
                    sub_folders = os.listdir(result_path)
                    for sub_folder in sub_folders:
                        if os.path.isdir(f"{result_path}/{sub_folder}"):
                            list_ = []
                            for gene in list_copied_gene_names:
                                file = f"{result_path}/{sub_folder}/{gene}.fas"
                                if os.path.exists(file):
                                    list_.append(True)
                                elif (sub_folder=="tRNA") and os.path.exists(f"{result_path}/{sub_folder}/trn{gene}.fas"):
                                    list_.append(True)
                                else:
                                    list_.append(False)
                            if set(list_) == {True}:
                                to_seq_removed(list_copied_gene_names[:], original_name,
                                    spe, f"{result_path}/{sub_folder}",
                                    target_gene)
                    # 删除gb文件里面的？
                    # 删除gene order文件里面的？
                    # 要等这个物种的序列删完？？？？
                    list_copied_gene_names.remove(target_gene)
                    list_new_GOs = [i for i in list_new_GOs if (i.lstrip("-") not in list_copied_gene_names) and
                                    (f"trn{i.lstrip('-')}" not in list_copied_gene_names)
                                    ]
                else:
                    list_array.append([spe, ref_spe, ref_reason, "", "", "", "", ""])
            return list_array, list_new_GOs, spe
        return [], list_new_GOs, spe


    def exec2_(self, result_path, work_dir,
               queue,
              # kaks_cal_exe=r"C:\softwares\KaKs_Calculator\KaKs_Calculator.Windows.Command\KaKs_Calculator.exe",
              mafft_exe=r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\plugins\mafft-win\mafft.bat",
              threads=8,
              exception_signal=None):
        '''
        修改文件里面的基因拷贝在多进程外面进行
        :param result_path:
        :param work_dir:
        :param mafft_exe:
        :param threads:
        :return:
        '''
        self.last_num = 0
        factory = Factory()
        factory.creat_dir(work_dir)
        # factory.remove_dir_directly(work_dir)
        go_file = f"{result_path}/files/linear_order.txt"
        taxonomy = f"{result_path}/StatFiles/taxonomy.csv"
        def is_consecutive_list(list_):
            list_.sort()
            range_list_=list(range(min(list_), max(list_)+1))
            # 如果不包含最后一个和开始的索引
            if list_ == range_list_:
                return True
            return False

        def is_consecutive(list_, total_list):
            list_total_indices = list(range(len(total_list)))
            # 如果不包含最后一个和开始的索引
            if is_consecutive_list(list_):
                return True
            # 如果最后一个元素和第一个元素在里面
            if (0 in list_) and (list_total_indices[-1] in list_):
                list_head = []
                list_tail = []
                for i in list_:
                    if list_head:
                        if ((i - list_head[-1])==1):
                            list_head.append(i)
                    else:
                        # 第一次
                        list_head.append(i)
                for j in reversed(list_):
                    if list_tail:
                        if (list_tail[-1] - j)==1:
                            list_tail.append(j)
                    else:
                        # 第一次
                        list_tail.append(j)
                if list(sorted(list_head+list_tail)) == list_:
                    return True
            return False

        # read gene order
        dict_gene_order= {}
        with open(go_file) as f2:
            line = f2.readline()
            while line:
                while not line.startswith('>') and line:
                    line = f2.readline()
                fas_name = line.strip().replace(">", "")
                goes = []
                line = f2.readline()
                while not line.startswith('>') and line:
                    goes.extend(line.strip().split("\t"))
                    line = f2.readline()
                dict_gene_order[fas_name] = goes
        # if progressSig:
        #     progressSig.emit(5)
        if len(dict_gene_order) == 1:
            # 只有一条序列时返回
            # if progressSig:
            #     progressSig.emit(100)
            return
        # optimize gene order
        # result_array = [["Query species", "Reference species", "Reference selection criterion", "Gene name",
        #                  "Internal stop codons", "Similarity", "Chosen gene",
        #                  "Gene selection criterion"]]
        # dict_spe_copied_genes_file = f"{work_dir}/tmp/dict_spe_copied_genes.pkl"
        # if (not os.path.exists(dict_spe_copied_genes_file)) or (not os.path.getsize(dict_spe_copied_genes_file)):
        # new_dict_GO = {}
        dict_spe_copied_genes = {}
        #转格式
        # timer = QTimer()
        total = len(dict_gene_order)
        # self.queue = Queue()

        pool = get_context("spawn").Pool(processes=threads) # \
            # if platform.system().lower() == "windows" else Pool(processes=threads)
        # pool = Pool(processes=threads)
        try:
            r = [pool.apply_async(self.run_slot_2, (spe, dict_gene_order, taxonomy,
                                                  result_path, work_dir, mafft_exe,
                                                    total, queue)) for spe in dict_gene_order]
            pool.close()
            # count = 0
            for item in r:
                item.wait(timeout=9999)  # Without a timeout, you can't interrupt this.
                spe, spe_copied_genes = item.get()
                # new_dict_GO[spe] = list_new_GOs
                dict_spe_copied_genes[spe] = spe_copied_genes
                # result_array += list_array
                # count += 1
                # if progressSig:
                #     if timer.elapsed()>500: # 必须过一段时间再发送，不然报错
                #         progressSig.emit(5 + (count/total)*90)
                #         timer.restart()
                # print(f"{spe}, {count}/{total} finished !")
        except:
            exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))
            self.save2log(f"{work_dir}/log.txt", exceptionInfo)
            if exception_signal:
                exception_signal.emit(exceptionInfo)
            pool.terminate()
        finally:
            pool.join()
        # timer.stop()
        # result_array.append([])
        # result_array.append(["Note that duplicated genes in the 'Gene name' column are named in the order they were "
        #                      "extracted from the genome; for example, if a species has three cox1 genes, the first one "
        #                      "will be named cox1, the second one cox1_copy2, and the third one cox1_copy3."])
        # factory.write_csv_file(f"{work_dir}/duplicates_resolving_details.csv", result_array, silence=True)
        list_csvs = glob.glob(f"{work_dir}/tmp/csv/*.csv")
        csv_body = []
        for csv in list_csvs:
            with open(csv) as f:
                csv_content = f.read()
            csv_body.append(csv_content)
        with open(f"{work_dir}/duplicates_resolving_details.csv", "w") as f2:
            header = ",".join(["Query species", "Reference species", "Reference selection criterion", "Gene name",
                               "Internal stop codons", "Similarity", "Chosen gene",
                               "Gene selection criterion"])
            foot = "\"Note that duplicated genes in the 'Gene name' column are named in the order they were " \
                    "extracted from the genome; for example, if a species has three cox1 genes, the first one " \
                    "will be named cox1, the second one cox1_copy2, and the third one cox1_copy3.\""
            f2.write(f"{header}\n{''.join(csv_body)}\n{foot}")
        # 存 GO
        new_go_file = f"{result_path}/files/linear_order_rmv_duplicates.txt"
        list_go_files = glob.glob(f"{work_dir}/tmp/csv/*.go")
        go_str = []
        for go_file in list_go_files:
            with open(go_file) as f:
                go_content = f.read()
                go_str.append(go_content)
        with open(new_go_file, "w") as f:
            f.write("".join(go_str))
        # # 存本地
        # with open(dict_spe_copied_genes_file, "wb") as f:
        #     pickle.dump(dict_spe_copied_genes)
        # else:
        #     with open(dict_spe_copied_genes_file, 'rb') as handle:
        #         dict_spe_copied_genes = pickle.load(handle)
        # 修改文件
        # if progressSig:
        #     # if timer.elapsed()>100:
        #     progressSig.emit(95)
        self.rmv_duplicates_in_files(dict_spe_copied_genes, result_path)
        # 删除tmp文件夹
        factory.remove_dir_directly(f"{work_dir}/tmp", removeRoot=True)
        factory.remove_dir_directly(f"{work_dir}/mafft_vessel", removeRoot=True)
        # if progressSig:
        #     progressSig.emit(100)
        # # return result_array

    def save2log(self, file, text):
        # print(text)
        with open(file, "a") as f:
            f.write(f"{text}\n")

    def run_slot_2(self, spe, dict_gene_order, taxonomy, result_path, work_dir, mafft_exe, total, queue):
        '''
        修改文件里面的基因拷贝在多进程外面进行
        :param spe:
        :param dict_gene_order:
        :param taxonomy:
        :param result_path:
        :param work_dir:
        :param mafft_exe:
        :return:
        TODO: 当有一个注释叫misc_feature的时候，里面如果有很多基因与其它注释（如CDS）的基因相同，如CDS有cox1，misc_feature也有cox1，
              会导致生成的linear order文件有多个cox1，类似cox1	cox1	cox1_copy2	cox1_copy3；但是实际上CDS只有1个cox1，
              这种情况下，如果有第三个物种有多的cox1基因，那么就会有cox1_copy2这个文件，而这个文件里面是没有前面那个物种的，这样就会导致
              出现BUG，即在基因文件里面找不到对应的物种
              新增功能，用这个功能的时候，不能打开misc_feature，或者直接强制性只保留CDS、tRNA等注释？
        '''
        try:
            factory = Factory()
            list_goes = dict_gene_order[spe]
            list_new_GOs = list_goes[:]
            list_array = []
            spe_copied_genes = [] # [[gene1, gene1_copy2], [gene2, gene2_copy2]]
            temp_dir = f"{work_dir}/tmp"
            os.makedirs(temp_dir, exist_ok=True)
            csv_dir = f"{temp_dir}/csv"
            factory.creat_dirs(csv_dir)
            go_file = f"{csv_dir}/{spe}.go"
            log = f"{work_dir}/log.txt"
            if os.path.exists(go_file) and os.path.getsize(go_file):
                self.save2log(log, f"{spe} already finished")
                self.send_progress(work_dir, total, queue)
                return spe, spe_copied_genes

            # 提取序列，进行计算
            def fetch_code_table(species_table, spe):
                with open(species_table) as f:
                    list_ = list(csv.reader(f, skipinitialspace=True))
                header = list_.pop(0)
                code_table_index = header.index("Code table")
                spe_index = header.index("Tree_Name")
                for line in list_:
                    spe_ = line[spe_index]
                    if spe_ == spe:
                        return int(line[code_table_index])
                return 1
            # 判断哪个才是原本的基因
            def log(x):
                n = 1000.0
                return n * ((x ** (1/n)) - 1)

            def get_target_gene(dict_inter_stop, dict_omega, dict_similarity):
                if dict_inter_stop and len(set(dict_inter_stop.values()))>1:
                    return min(dict_inter_stop, key=lambda x: dict_inter_stop[x]), "fewer interal stop codons"
                elif dict_similarity:
                    if len(set(dict_similarity.values()))>1:
                        return max(dict_similarity, key=lambda x: dict_similarity[x]), "highest similarity to the reference gene"
                    else:
                        return random.choice(list(dict_similarity.keys())), "randomly chosen (selection criteria were the same)"
                elif dict_omega and len(set(dict_omega.values()))>1:
                    return max(dict_omega, key = lambda x: abs(log(dict_omega[x]))), "strongest selection pressure"
                else:
                    return "", "No best gene"

            def get_seq(file, name_):
                # print(file, name_)
                rgx_seq = re.compile(f">{name_}([^>]+)")
                with open(file) as f:
                    content = f.read()
                if rgx_seq.search(content):
                    return re.sub(r"\s", "", rgx_seq.search(content).group(1))
                else:
                    print(f"{name_} was not found in {file}!")
                    return

            def spe_in_fas(spe, file):
                rgx_seq = re.compile(f">{spe}([^>]+)")
                with open(file) as f:
                    content = f.read()
                return rgx_seq.search(content)

            def pad_seq(sequence):
                """ Pad sequence to multiple of 3 with N """

                remainder = len(sequence) % 3

                return sequence if remainder == 0 else sequence + Seq('N' * (3 - remainder))

            if "_copy" in "".join(list_goes):
                # print(spe)
                dict_copied_go = {} # {cox1: [cox1, cox1_copy1]}
                for go in list_goes:
                    if "_copy" in go:
                        go_key = go.lstrip("-").split("_copy")[0]
                        dict_copied_go.setdefault(go_key, [go_key]).append(go)
                # print(dict_copied_go)
                # 判断GO
                for go_key in dict_copied_go:
                    original_gene_name = go_key if go_key in list_goes else f"-{go_key}"
                    # original_gene_index = list_goes.index(original_gene_name)
                    # list_indices = [original_gene_index] + [list_goes.index(i) for i in dict_copied_go[go_key][1:]]
                    # if is_consecutive(list_indices, list_goes):
                    #     # 如果copy的gene是连续的
                    #     pass
                    # 判断是否有内部终止密码子；以及通过选择压和比对相似度判断
                    # 选一个没有拷贝的参考物种？
                    # 能不能不放到这里无限循环？#######
                    ref_spe, ref_reason = self.pick_ref_spe(spe, taxonomy,
                        go_key, dict_gene_order)
                    if not ref_spe:
                        continue

                    dict_folder_seqs = {} # {CDS_NUC: ["xx/cox1.fas", "xx/cox1_copy1.fas"]}
                    for copied_gene in dict_copied_go[go_key]:
                        sub_folders = os.listdir(result_path)
                        for sub_folder in sub_folders:
                            if os.path.isdir(f"{result_path}/{sub_folder}"):
                                gene_name = copied_gene.lstrip('-')
                                # tRNA的名字可能不同
                                gene_name2 = f"trn{gene_name}"
                                gene_file = f"{result_path}/{sub_folder}/{gene_name}.fas"
                                gene_file2 = f"{result_path}/{sub_folder}/{gene_name2}.fas"
                                if os.path.exists(gene_file) and spe_in_fas(spe, gene_file):
                                    dict_folder_seqs.setdefault(sub_folder, []).append(gene_file)
                                elif os.path.exists(gene_file2) and spe_in_fas(spe, gene_file2):
                                    dict_folder_seqs.setdefault(sub_folder, []).append(gene_file2)
                    # 确定一个subfolder，然后提取对应序列出来做分析
                    is_PCG = False
                    if "CDS_NUC" in dict_folder_seqs:
                        # PCGs,可以用内部终止密码子、选择压力、序列相似度来判断
                        is_PCG = True
                        list_seq_files = dict_folder_seqs["CDS_NUC"]
                        ref_seq = get_seq(f"{result_path}/CDS_NUC/{original_gene_name.lstrip('-')}.fas",
                            ref_spe)
                    else:
                        if not dict_folder_seqs:
                            # 没找到任何序列的时候怎么办？
                            list_seq_files = []
                        # non PCGs
                        elif (len(dict_folder_seqs) > 1):
                            if ("gene" in dict_folder_seqs):
                                dict_folder_seqs.pop("gene")
                            subfolder = random.choice(list(dict_folder_seqs.keys()))
                            list_seq_files = dict_folder_seqs[subfolder]
                            file = f"{result_path}/{subfolder}/{original_gene_name.lstrip('-')}.fas"
                            if subfolder == "tRNA":
                                file1 = f"{result_path}/{subfolder}/trn{original_gene_name.lstrip('-')}.fas"
                                if os.path.exists(file1):
                                    file = file1
                            ref_seq = get_seq(file, ref_spe)
                        else:
                            subfolder = random.choice(list(dict_folder_seqs.keys()))
                            list_seq_files = dict_folder_seqs[subfolder]
                            file = f"{result_path}/{subfolder}/{original_gene_name.lstrip('-')}.fas"
                            if subfolder == "tRNA":
                                file1 = f"{result_path}/{subfolder}/trn{original_gene_name.lstrip('-')}.fas"
                                if os.path.exists(file1):
                                    file = file1
                            ref_seq = get_seq(file, ref_spe)

                    dict_inter_stop = {}
                    dict_omega = {}
                    dict_similarity = {}
                    list_spe_array = []
                    list_copied_gene_names = []
                    if list_seq_files:
                        # 比对，如果是PCG，用密码子比对
                        for seq_file in list_seq_files:
                            tmp_seq_file = f"{temp_dir}/{uuid.uuid1()}.fas"
                            seq = get_seq(seq_file, spe)
                            if not seq:
                                continue
                            gene_name = os.path.splitext(os.path.basename(seq_file))[0]
                            list_copied_gene_names.append(gene_name)
                            with open(tmp_seq_file, "w") as f:
                                f.write(f">{ref_spe}\n{ref_seq}\n>{spe}\n{seq}\n")
                            if is_PCG:
                                code_table = fetch_code_table(f"{result_path}/StatFiles/species_info.csv", spe)
                                table = CodonTable.ambiguous_dna_by_id[code_table]
                                # 计算内部终止密码子
                                protein = _translate_str(pad_seq(seq), table)
                                # 去除终止密码子再比较
                                protein = protein[:-1] if protein.endswith("*") else protein
                                inter_stop_num = protein.count("*")
                                dict_inter_stop[gene_name] = inter_stop_num
                                # 比对
                                aligned_fas = self.align(mafft_exe, tmp_seq_file, work_dir,
                                    code_table, is_PCGs=is_PCG)
                                if os.path.getsize(aligned_fas):
                                    # # 计算omega
                                    # omega = self.kaks(kaks_cal_exe, aligned_fas, code_table, work_dir)
                                    # dict_omega[gene_name] = omega
                                    # 计算similarity
                                    similarity = self.similarity(aligned_fas)
                                    dict_similarity[gene_name] = similarity
                                    list_spe_array.append([spe, ref_spe, ref_reason, gene_name, inter_stop_num,
                                                           similarity])
                                else:
                                    # 比对文件是空的
                                    list_spe_array.append([spe, ref_spe, ref_reason, gene_name, inter_stop_num,
                                                           ""])
                            else:
                                # 比对
                                aligned_fas = self.align(mafft_exe, tmp_seq_file, work_dir,
                                    None, is_PCGs=is_PCG)
                                if os.path.getsize(aligned_fas):
                                    # 计算similarity
                                    similarity = self.similarity(aligned_fas)
                                    dict_similarity[gene_name] = similarity
                                    list_spe_array.append([spe, ref_spe, ref_reason, gene_name, "", similarity])
                                else:
                                    list_spe_array.append([spe, ref_spe, ref_reason, gene_name, "", ""])
                        target_gene, reason = get_target_gene(dict_inter_stop, dict_omega, dict_similarity)
                        for i in list_spe_array:
                            list_array.append(i + [target_gene, reason])
                        # 删除gene order文件里面的？
                        # 要等这个物种的序列删完？？？？
                        list_copied_gene_names.remove(target_gene)
                        list_new_GOs = [i for i in list_new_GOs if (i.lstrip("-") not in list_copied_gene_names) and
                                        (f"trn{i.lstrip('-')}" not in list_copied_gene_names)
                                        ]
                        rep_name = target_gene.replace("trn", "")
                        target_name = rep_name if rep_name in list_new_GOs else f"-{rep_name}"
                        # print(list_new_GOs, target_name, target_gene)
                        target_gene_index = list_new_GOs.index(target_name)
                        list_new_GOs[target_gene_index] = list_new_GOs[target_gene_index].split("_copy")[0]
                        list_copied_genes = [target_gene] + list_copied_gene_names
                        spe_copied_genes.append(list_copied_genes)
                    else:
                        list_array.append([spe, ref_spe, ref_reason, "", "", "", "", ""])
                # 存CSV
                factory.write_csv_file(f"{csv_dir}/{spe}.csv", list_array, silence=True)
                # 存GO
                with open(go_file, "w") as f:
                    go_str = '\t'.join(list_new_GOs)
                    f.write(f">{spe}\n{go_str}\n")
                self.send_progress(work_dir, total, queue)
                return spe, spe_copied_genes
            # 存GO
            with open(go_file, "w") as f:
                go_str = '\t'.join(list_new_GOs)
                f.write(f">{spe}\n{go_str}\n")
            self.send_progress(work_dir, total, queue)
            return spe, spe_copied_genes
        except:
            exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))
            self.save2log(f"{work_dir}/log.txt", exceptionInfo)

    def send_progress(self, work_dir, total, queue):
        if queue:
            queue.put((total,))
        # go_num = len(glob.glob(f"{work_dir}/tmp/csv/*.go"))
        # if go_num > self.last_num:
        #     self.save2log(f"{work_dir}/log.txt", f'finished {go_num}/{total}!')
        #     self.last_num = go_num
        # return 5 + (go_num/total)*85

    def rmv_duplicates_in_files(self, dict_spe_copied_genes, result_path):
        # 修改提取的序列，以及gene order等处
        # 蛋白序列有好几个文件夹，要怎么删？管他三七二十一，循环读每个文件，再来删？
        # 再删除一下gb文件，生成新的gb文件，with duplicates删除
        # 加上续删功能？
        factory = Factory()
        for spe in dict_spe_copied_genes:
            for list_copied_genes in dict_spe_copied_genes[spe]:
                target_gene = list_copied_genes[0]

                def to_seq_removed(list_names, origin_name, spe, folder, target_gene):
                    dir_removed = f"{folder}/removed_seqs"
                    factory.creat_dirs(dir_removed)
                    def remove_gene(gene_name, folder, rmv_folder, spe, origin=False):
                        # 提取序列，加入到原基因文件
                        gene_name = gene_name if os.path.exists(f"{folder}/{gene_name}.fas") else f"trn{gene_name}"
                        gene_file = f"{folder}/{gene_name}.fas"
                        with open(gene_file) as f2:
                            content = f2.read()
                        # 提取序列，并存到文件
                        # print(gene_file, spe, content)
                        rgx_seq = re.compile(f">{spe}([^>]+)")
                        seq = re.sub(r"\s", "", rgx_seq.search(content).group(1))
                        with open(f"{rmv_folder}/{spe}_{gene_name}_removed.fas", "w") as f:
                            f.write(f">{spe}\n{seq}\n")
                        # 删除原文件的序列
                        new_content = re.sub(f">{spe}[^>]+", "", content)
                        if ">" not in new_content:
                            # 如果没有序列了，就删除文件
                            if not origin:
                                os.remove(gene_file)
                        else:
                            with open(gene_file, "w") as f3:
                                f3.write(new_content)
                        return gene_file, gene_name

                    if origin_name == target_gene:
                        # 只用删除copy_gene
                        list_names.remove(target_gene)
                        for gene in list_names:
                            remove_gene(gene, folder, dir_removed, spe)
                    else:
                        # 先从原文件提取基因序列出来删掉
                        origin_gene_file, origin_name = remove_gene(origin_name, folder, dir_removed, spe, origin=True)
                        # 再从目标基因提取序列存到原文件，其余序列删掉
                        target_file = f"{folder}/{target_gene}.fas"
                        with open(target_file) as f4:
                            target_content = f4.read()
                        target_seq = re.sub(r"\s", "", re.search(f">{spe}([^>]+)", target_content).group(1))
                        ## 追加方式存到原文件
                        with open(origin_gene_file, "a") as f:
                            f.write(f"\n>{spe}\n{target_seq}\n")
                        ## 删除target gene file的序列
                        new_content = re.sub(f">{spe}[^>]+", "", target_content)
                        if ">" not in new_content:
                            # 如果没有序列了，就删除文件
                            os.remove(target_file)
                        else:
                            with open(target_file, "w") as f3:
                                f3.write(new_content)
                        # 删除其余序列
                        remain_genes = [i for i in list_names if i not in [target_gene, origin_name]]
                        if remain_genes:
                            for remain_gene in remain_genes:
                                remove_gene(remain_gene, folder, dir_removed, spe)
                original_name = target_gene.lstrip("-").split("_copy")[0]
                sub_folders = os.listdir(result_path)
                for sub_folder in sub_folders:
                    if os.path.isdir(f"{result_path}/{sub_folder}"):
                        list_ = []
                        for gene in list_copied_genes:
                            file = f"{result_path}/{sub_folder}/{gene}.fas"
                            if os.path.exists(file):
                                list_.append(True)
                            elif (sub_folder=="tRNA") and os.path.exists(f"{result_path}/{sub_folder}/trn{gene}.fas"):
                                list_.append(True)
                            else:
                                list_.append(False)
                        if set(list_) == {True}:
                            to_seq_removed(list_copied_genes[:], original_name,
                                spe, f"{result_path}/{sub_folder}",
                                target_gene)
                # 删除gb文件里面的？

    def run_command(self, commands, popen):
        stdout = [f"{commands}\n"]
        while True:
            try:
                out_line = popen.stdout.readline().decode("utf-8", errors='ignore')
            except UnicodeDecodeError:
                out_line = popen.stdout.readline().decode("gbk", errors='ignore')
            if out_line == "" and popen.poll() is not None:
                break
            stdout.append(out_line)
        return "".join(stdout)

    def align(self, mafft_exe, seq_file, work_dir, code_table, is_PCGs=False):
        factory = Factory()
        dict_args = {}
        dict_args["mafft_exe"] = mafft_exe
        dict_args["vessel"] = f"{work_dir}/mafft_vessel/{uuid.uuid1()}"
        factory.creat_dir(dict_args["vessel"])
        factory.remove_dir_directly(dict_args["vessel"])
        dict_args["exportPath"] = f"{dict_args['vessel']}/mafft_alignment"
        factory.creat_dir(dict_args["exportPath"])
        factory.remove_dir_directly(dict_args["exportPath"])
        dict_args["filenames"] = [seq_file]
        dict_args["progressSig"] = None
        file_base = os.path.basename(seq_file)
        flag = True
        if is_PCGs:
            try:
                dict_args["codon"] = code_table
                dict_args["vessel_aaseq"] = f"{dict_args['vessel']}/AA_sequence"
                dict_args["vessel_aalign"] = f"{dict_args['vessel']}/AA_alignments"
                # 翻译为氨基酸
                factory.creat_dir(dict_args["vessel_aaseq"])
                factory.creat_dir(dict_args["vessel_aalign"])
                # 翻译氨基酸，保存AA文件，映射
                codonAlign = CodonAlign(**dict_args)
                # 比对
                align_file = os.path.join(dict_args["vessel_aaseq"], file_base)
                commands = f'"{dict_args["mafft_exe"]}" --auto --inputorder "{align_file}" > ' \
                           f'"{dict_args["vessel_aalign"]}/{file_base}"'
            except:
                # 如果翻译报错，就用普通方法比对
                self.save2log(f"{work_dir}/log.txt", f"{seq_file} translation error")
                commands = f'"{dict_args["mafft_exe"]}" --auto --inputorder "{seq_file}" > ' \
                           f'"{dict_args["exportPath"]}/{file_base}"'
                flag = False
        else:
            commands = f'"{dict_args["mafft_exe"]}" --auto --inputorder "{seq_file}" > ' \
                       f'"{dict_args["exportPath"]}/{file_base}"'
        popen = factory.init_popen(commands)
        self.run_command(commands, popen)
        if is_PCGs and flag:
            codonAlign.back_trans()  # 生成回译的codon文件
            split_ext = os.path.splitext(file_base)  # 为了加后缀
            aligned_file = dict_args["exportPath"] + os.sep + "_mafft".join(split_ext)
        else:
            aligned_file = f'{dict_args["exportPath"]}/{file_base}'
        return aligned_file

    def kaks(self, kaks_cal_exe, alignment, code_table, work_dir, method="NG"):
        factory = Factory()
        kaks_dir = f"{work_dir}/kaks"
        factory.creat_dir(kaks_dir)
        # 转为AXT格式
        self.convertfmt = Convertfmt(**{"export_path": kaks_dir, "files": [alignment],
                                        "export_axt": True})
        self.convertfmt.exec_()
        axt = self.convertfmt.axt_file
        # 计算kaks
        output_file = f"{kaks_dir}/{os.path.basename(axt)}.kaks"
        commands = f"{kaks_cal_exe} -i {axt} -o {output_file} " \
                   f"-c {code_table} -m {method}"
        popen = factory.init_popen(commands)
        log_ = self.run_command(commands, popen)
        # print(log_)
        with open(output_file) as f:
            list_lines = f.readlines()
        headers = list_lines.pop(0).strip().split("\t")
        kaks_index = headers.index("Ka/Ks")
        return float(list_lines[0].strip().split("\t")[kaks_index])

    def similarity(self, alignment):
        # 序列成对，生成相似性矩阵
        aln = AlignIO.read(open(alignment), 'fasta')
        calculator = DistanceCalculator('identity')
        return 1 - calculator.get_distance(aln).matrix[1][0]

    def pick_ref_spe(self, query_spe, taxonomy, gene, dict_gene_order):
        '''
            从同一个属开始找，如果没有就同一个科，再不行就同一个目
            参考物种不能有目标基因的重复
            gene: 基因名字，需要是不带正负号信息以及带copy信息的基因名字
            query_spe：需要tree name
            taxonomy：需要提取出来的分类表
            dict_gene_order：以tree name为键，基因顺序为列表
        :return:
        '''
        tax_list = ["Genus", "Family", "Order", "Class", "Phylum"]
        # 得到所有物种对应的分类
        if not hasattr(self, "dict_spe_tax"):
            with open(taxonomy) as f:
                list_ = list(csv.reader(f, skipinitialspace=True))
            header = list_.pop(0)
            org_index = header.index("Organism")
            tree_name_index = header.index("Tree name")
            spe_list = [[i[org_index], i[tree_name_index], i[org_index+1:]] for num,i in enumerate(list_)]
            self.dict_spe_tax = {}
            for j in spe_list:
                organism, tree_name, list_spe_tax = j
                taxs = self.get_lineages(organism, tax_list, list_spe_tax)
                if not taxs:
                    taxs = self.get_lineages(organism.split()[0], tax_list, list_spe_tax)
                if taxs:
                    self.dict_spe_tax[tree_name] = taxs

        def count_tax(tax, dict_spe_tax):
            list_ = []
            for spe in dict_spe_tax:
                if tax in dict_spe_tax[spe]:
                    list_.append(spe)
            return list_
        if query_spe in self.dict_spe_tax:
            query_spe_tax = self.dict_spe_tax[query_spe]
            for num,tax in enumerate(query_spe_tax):
                tax_name = tax_list[num]
                list_tax_spe = count_tax(tax, self.dict_spe_tax)
                list_tax_spe.remove(query_spe)
                # print(tax_name, list_tax_spe)
                if list_tax_spe:
                    # 判断选出来的物种里面有没有目标基因
                    while list_tax_spe:
                        random_spe = random.choice(list_tax_spe)
                        gos = dict_gene_order[random_spe]
                        if (gene not in gos) and (f"-{gene}" not in gos):
                            list_tax_spe.remove(random_spe)
                        elif gene + "_copy" in "".join(gos):
                            # 有拷贝基因也不行
                            list_tax_spe.remove(random_spe)
                        else:
                            return [random_spe, f"the same {tax_name}"]
            return None, None
        else:
            # 如果query_spe都没有分类
            return None, None

    def get_lineages_by_ID(self, query_id):
        ncbi = NCBITaxa()
        # query_id = ncbi.get_name_translator([tax_])[tax_][0]
        lineage_ids = ncbi.get_lineage(query_id)
        dict_id_rank = ncbi.get_rank(lineage_ids)
        dict_id_name = ncbi.get_taxid_translator(lineage_ids)
        # print(dict_id_rank)
        # print({dict_id_name[id]: dict_id_rank[id] for id in dict_id_name})
        return list(dict_id_name.values())

    def get_lineages(self, name, tax_list, record_tax):
        ncbi = NCBITaxa()
        query_id = ncbi.get_name_translator([name])
        if query_id:
            if len(query_id[name]) == 1:
                id__ = query_id[name][0]
            else:
                # 分类名对应了多个id的情况，如{'Brachycladium': [570638, 630351]}
                dict_id_lineages = {}
                for id_ in query_id[name]:
                    dict_id_lineages[id_] = self.get_lineages_by_ID(id_)
                # 哪个lineage和物种本身的lineage交集多，就用哪个id
                max_inter = 0
                for temp_id in dict_id_lineages:
                    inter_num = len(list(set(record_tax).intersection(dict_id_lineages[temp_id])))
                    # print(temp_id, inter_num)
                    if inter_num >= max_inter:
                        max_inter = inter_num
                        id__ = temp_id
            lineage_ids = ncbi.get_lineage(id__)
            dict_id_rank = ncbi.get_rank(lineage_ids)
            dict_id_name = ncbi.get_taxid_translator(lineage_ids)
            dict_rank_name = {dict_id_rank[id].upper():dict_id_name[id] for id in dict_id_name}
            taxs = []
            for tax in tax_list:
                if tax.upper() in dict_rank_name:
                    taxs.append(dict_rank_name[tax.upper()])
                else:
                    taxs.append("")
            return taxs
        else:
            return False


# class GBextract_MT(GBextract, object):
#     def __init__(self, **dict_args):
#         super(GBextract_MT, self).__init__(**dict_args)
#
#     def init_args_all(self):
#         super(GBextract_MT, self).init_args_all()
#         self.dict_pro = {}
#         self.dict_AA = OrderedDict()
#         self.dict_rRNA = {}
#         self.dict_tRNA = {}
#         self.dict_name = {}
#         self.dict_gb = {}
#         self.dict_start = {}
#         self.dict_stop = {}
#         self.dict_PCG = {}
#         self.dict_RNA = {}
#         # self.dict_geom = {}
#         self.dict_spe_stat = {}
#         self.list_name_gb = []
#         self.linear_order = ''
#         self.complete_seq = ''
#         self.list_PCGs = [
#             'cox1',
#             'cox2',
#             'nad6',
#             'nad5',
#             'cox3',
#             'cytb',
#             'nad4L',
#             'nad4',
#             'atp6',
#             'nad2',
#             'nad1',
#             'nad3',
#             'atp8',
#             'rrnS',
#             'rrnL']
#         self.dict_unify_mtname = {
#             'COX1': 'cox1',
#             'COX2': 'cox2',
#             'NAD6': 'nad6',
#             'NAD5': 'nad5',
#             'COX3': 'cox3',
#             'CYTB': 'cytb',
#             'NAD4L': 'nad4L',
#             'NAD4': 'nad4',
#             'ATP6': 'atp6',
#             'NAD2': 'nad2',
#             'NAD1': 'nad1',
#             'NAD3': 'nad3',
#             'ATP8': 'atp8',
#             'RRNS': 'rrnS',
#             'RRNL': 'rrnL'
#         }
#         self.dict_geom_seq = {}
#         self.name_gb = "Species name,Accession number\n"  # 名字和gb num对照表
#         # 有物种没有解析成功，保存在这里
#         # self.dict_igs = OrderedDict()  # 存放基因间隔区的序列
#         # self.ncr_stat = OrderedDict()
#         # 保存没有注释好的L和S
#         self.leu_ser = ""
#         #         skewness
#         self.PCGsCodonSkew = "Tree_name,species,Strand,AT skew,GC skew," + \
#                              ",".join(self.included_lineages) + "\n"
#         self.firstCodonSkew = "Tree_name,species,Strand,AT skew,GC skew," + \
#                               ",".join(self.included_lineages) + "\n"
#         self.secondCodonSkew = "Tree_name,species,Strand,AT skew,GC skew," + \
#                                ",".join(self.included_lineages) + "\n"
#         self.thirdCodonSkew = "Tree_name,species,Strand,AT skew,GC skew," + \
#                               ",".join(self.included_lineages) + "\n"
#         self.firstSecondCodonSkew = "Tree_name,species,Strand,AT skew,GC skew," + \
#                               ",".join(self.included_lineages) + "\n"
#         #         统计图
#         self.dict_all_stat = OrderedDict()
#         #         PCG的串联序列
#         self.PCG_seq = ""
#         self.tRNA_seqs = ""
#         self.rRNA_seqs = ""
#         #         新增统计物种组成表功能
#         self.dict_orgTable = OrderedDict()
#         # 新增RSCU相关
#         self.dict_RSCU = OrderedDict()  # RSCU table
#         self.dict_RSCU_stack = OrderedDict()
#         self.dict_AAusage = OrderedDict()
#         self.dict_all_spe_RSCU = OrderedDict()
#         self.dict_all_spe_RSCU["title"] = "codon,"
#         self.dict_all_codon_COUNT = OrderedDict()
#         self.dict_all_codon_COUNT["title"] = "codon,"
#         self.dict_all_AA_RATIO = OrderedDict()
#         self.dict_all_AA_RATIO["title"] = "AA,"
#         self.dict_all_AA_COUNT = OrderedDict()
#         self.dict_all_AA_COUNT["title"] = "AA,"
#         self.dict_AA_stack = OrderedDict()
#         self.dict_AA_stack["title"] = "species,aa,ratio"
#         self.species_info = '="ID",Organism,Tree_Name,{},Full length (bp),Coding region length (exclude NCR),A (%) (+),T (%) (+),C (%) (+),G (%) (+),A+T (%) (+),' \
#                             'G+C (%) (+),AT skew (+),GC skew (+),AT skew (-),GC skew (-),GC skew (plus strand coding),' \
#                             'GC skew (plus strand genes only),GC skew (fourfold degenerate sites),' \
#                             'GC skew (fourfold degenerate sites on plus strand),GC skew (all NCR),NCR ratio\n'.format(
#                             ",".join(self.included_lineages))
#         # 新增折线图的绘制
#         self.line_spe_stat = "Regions,Strand,Size (bp),T(U),C,A,G,AT(%),GC(%),GT(%),AT skewness,GC skewness,ID,Species," + ",".join(
#             list(reversed(self.included_lineages))) + "\n"
#         # 密码子偏倚分析
#         self.codon_bias = "Tree_name,Genes,GC1,GC2,GC12,GC3,CAI,CBI,Fop,ENC,L_sym,L_aa,Gravy,Aromo,Species," + ",".join(
#             list(reversed(self.included_lineages))) + "\n"
#         # self.all_taxonmy = "Species," + \
#         #                    ",".join(list(reversed(self.included_lineages))) + "\n"
#         self.list_all_taxonmy = []  # [[genus1, family1], [genus2, family2]]
#         # {NC_029245:Hymenolepis nana}
#         self.dict_gb_latin = OrderedDict()
#         self.dict_gene_ATskews = {}
#         self.dict_gene_GCskews = {}
#         self.dict_gene_ATCont = {}
#         self.dict_gene_GCCont = {}
#         # map ID and tree name
#         self.dict_ID_treeName = {}
#
#     def init_args_each(self):
#         # self.PCGs = ''
#         self.PCGs_strim = '' #去除不标准的终止密码子的
#         self.PCGs_strim_plus = ""
#         self.PCGs_strim_minus = ""
#         self.tRNAs = ''
#         self.tRNAs_plus = ""
#         self.tRNAs_minus = ""
#         self.rRNAs = ""
#         self.rRNAs_plus = ""
#         self.rRNAs_minus = ""
#         self.NCR_seq = ""
#         self.dict_genes = {}
#         self.dict_geom_seq[self.ID] = self.str_seq
#         self.list_name_gb.append((self.organism, self.ID))
#         self.name_gb += self.organism + "," + self.ID + "\n"
#         # self.igs = ""
#         # self.NCR = ''
#         # 刷新这个table
#         self.orgTable = '''Gene,Position,,Size,Intergenic nucleotides,Codon,,\n,From,To,,,Start,Stop,Strand,Sequence\n'''
#         self.lastEndIndex = 0
#         self.overlap, self.gap = 0, 0
#         self.dict_repeat_name_num = OrderedDict()
#
#     def parseSource(self):
#         super(GBextract_MT, self).parseSource()
#         list_taxonmy = list(reversed(self.list_lineages))
#         self.list_all_taxonmy.append(list_taxonmy)
#         self.taxonmy = ",".join(
#             [self.organism] + list_taxonmy)
#         # self.all_taxonmy += self.taxonmy + "\n"
#         self.gene_order = '>' + self.usedName + '\n'
#         self.complete_seq += '>' + self.usedName + '\n' + self.str_seq + '\n'
#
#     def parseFeature(self):
#         new_name = self.fetchGeneName()
#         if not new_name:
#             return
#         seq = str(self.feature.extract(self.seq))
#         feature_name = "CDS_NUC" if self.feature_type.upper() == "CDS" else self.feature_type
#         self.dict_feature_fas.setdefault(feature_name, OrderedDict())[new_name + '>' + self.organism + '_' +
#                                                  self.name] = '>' + self.usedName + '\n' + seq + '\n'
#         self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
#         if "translation" in self.qualifiers:
#             aa_seq = self.qualifiers["translation"][0]
#             self.dict_feature_fas.setdefault("CDS_AA", OrderedDict())[new_name + '>' + self.organism + '_' +
#                                                  self.name] = '>' + self.usedName + '\n' + aa_seq + '\n'
#         self.fun_orgTable(new_name, len(seq), "", "", seq)
#         if new_name.upper().startswith("NCR") and self.dict_args["NCRchecked"]:
#             self.gene_order += self.omit_strand + 'NCR '
#         ##间隔区提取
#         self.refresh_pairwise_feature(new_name)
#
#     def stat_PCG_sub(self, seq, strand):
#         seqStat = SeqGrab(seq)
#         PCGs_stat = ",".join(['PCGs',
#                                strand,
#                                seqStat.size,
#                                seqStat.T_percent,
#                                seqStat.C_percent,
#                                seqStat.A_percent,
#                                seqStat.G_percent,
#                                seqStat.AT_percent,
#                                seqStat.GC_percent,
#                                seqStat.GT_percent,
#                                seqStat.AT_skew,
#                                seqStat.GC_skew]) + "\n"
#         self.PCGsCodonSkew += ",".join([self.usedName,
#                                         self.organism,
#                                         strand,
#                                         seqStat.AT_skew,
#                                         seqStat.GC_skew] + self.list_lineages) + "\n"
#         first, second, third = seqStat.splitCodon()
#         seq = first
#         seqStat = SeqGrab(seq)
#         first_stat = ",".join(['1st codon position',
#                                strand,
#                                seqStat.size,
#                                seqStat.T_percent,
#                                seqStat.C_percent,
#                                seqStat.A_percent,
#                                seqStat.G_percent,
#                                seqStat.AT_percent,
#                                seqStat.GC_percent,
#                                seqStat.GT_percent,
#                                seqStat.AT_skew,
#                                seqStat.GC_skew]) + "\n"
#
#         self.firstCodonSkew += ",".join([self.usedName,
#                                          self.organism,
#                                          strand,
#                                          seqStat.AT_skew,
#                                          seqStat.GC_skew] + self.list_lineages) + "\n"
#
#         seq = second
#         seqStat = SeqGrab(seq)
#         second_stat = ",".join(['2nd codon position',
#                                 strand,
#                                 seqStat.size,
#                                 seqStat.T_percent,
#                                 seqStat.C_percent,
#                                 seqStat.A_percent,
#                                 seqStat.G_percent,
#                                 seqStat.AT_percent,
#                                 seqStat.GC_percent,
#                                 seqStat.GT_percent,
#                                 seqStat.AT_skew,
#                                 seqStat.GC_skew]) + "\n"
#
#         self.secondCodonSkew += ",".join([self.usedName,
#                                           self.organism,
#                                           strand,
#                                           seqStat.AT_skew,
#                                           seqStat.GC_skew] + self.list_lineages) + "\n"
#
#         seq = third
#         seqStat = SeqGrab(seq)
#         third_stat = ",".join(['3rd codon position',
#                                strand,
#                                seqStat.size,
#                                seqStat.T_percent,
#                                seqStat.C_percent,
#                                seqStat.A_percent,
#                                seqStat.G_percent,
#                                seqStat.AT_percent,
#                                seqStat.GC_percent,
#                                seqStat.GT_percent,
#                                seqStat.AT_skew,
#                                seqStat.GC_skew]) + "\n"
#
#         self.thirdCodonSkew += ",".join([self.usedName,
#                                          self.organism,
#                                          strand,
#                                          seqStat.AT_skew,
#                                          seqStat.GC_skew] + self.list_lineages) + "\n"
#         seq = first + second
#         seqStat = SeqGrab(seq)
#         firstSecond_stat = ",".join(['1st+2nd codon position',
#                                strand,
#                                seqStat.size,
#                                seqStat.T_percent,
#                                seqStat.C_percent,
#                                seqStat.A_percent,
#                                seqStat.G_percent,
#                                seqStat.AT_percent,
#                                seqStat.GC_percent,
#                                seqStat.GT_percent,
#                                seqStat.AT_skew,
#                                seqStat.GC_skew]) + "\n"
#
#         self.firstSecondCodonSkew += ",".join([self.usedName,
#                                          self.organism,
#                                          strand,
#                                          seqStat.AT_skew,
#                                          seqStat.GC_skew] + self.list_lineages) + "\n"
#         return [PCGs_stat, first_stat, second_stat, third_stat]
#
#     def geneStat_sub(self, name, seqStat):
#         if seqStat == "N/A":
#             if name in self.dict_gene_ATskews:
#                 self.dict_gene_ATskews[name] += ",N/A"
#                 self.dict_gene_ATCont[name] += ",N/A"
#                 self.dict_gene_GCskews[name] += ",N/A"
#                 self.dict_gene_GCCont[name] += ",N/A"
#             else:
#                 self.dict_gene_ATskews[name] = name + ",N/A"
#                 self.dict_gene_ATCont[name] = name + ",N/A"
#                 self.dict_gene_GCskews[name] = name + ",N/A"
#                 self.dict_gene_GCCont[name] = name + ",N/A"
#         else:
#             if name in self.dict_gene_ATskews:
#                 self.dict_gene_ATskews[name] += "," + seqStat.AT_skew
#                 self.dict_gene_ATCont[name] += "," + seqStat.AT_percent
#                 self.dict_gene_GCskews[name] += "," + seqStat.GC_skew
#                 self.dict_gene_GCCont[name] += "," + seqStat.GC_percent
#             else:
#                 self.dict_gene_ATskews[name] = name + "," + seqStat.AT_skew
#                 self.dict_gene_ATCont[name] = name + "," + seqStat.AT_percent
#                 self.dict_gene_GCskews[name] = name + "," + seqStat.GC_skew
#                 self.dict_gene_GCCont[name] = name + "," + seqStat.GC_percent
#
#     def stat_other_sub(self, seq, strand, flag):
#         seqStat = SeqGrab(seq)
#         stat_ = ",".join([flag,
#                           strand,
#                           seqStat.size,
#                           seqStat.T_percent,
#                           seqStat.C_percent,
#                           seqStat.A_percent,
#                           seqStat.G_percent,
#                           seqStat.AT_percent,
#                           seqStat.GC_percent,
#                           seqStat.GT_percent,
#                           seqStat.AT_skew,
#                           seqStat.GC_skew]) + "\n"
#         name = "%s(%s)"%(flag, strand)
#         self.geneStat_sub(name, seqStat)
#         return stat_
#
#     def gb_record_stat(self):
#         # 统计单个物种
#         list_genes = [
#             value for (key, value) in sorted(self.dict_genes.items())]
#         #         whole genome
#         seq = self.str_seq.upper()
#         seqStat = SeqGrab(seq)
#         geom_stat = ",".join(['Full genome',
#                               "+",
#                               seqStat.size,
#                               seqStat.T_percent,
#                               seqStat.C_percent,
#                               seqStat.A_percent,
#                               seqStat.G_percent,
#                               seqStat.AT_percent,
#                               seqStat.GC_percent,
#                               seqStat.GT_percent,
#                               seqStat.AT_skew,
#                               seqStat.GC_skew]) + "\n"
#         # 物种的大统计表
#         self.list_spe_stat = self.list_lineages + [
#             self.organism,
#             self.ID,
#             seqStat.size,
#             seqStat.AT_percent,
#             seqStat.AT_skew,
#             seqStat.GC_skew]
#         ###species_info###
#         # ID",Organism,%s,Full length (bp),A (%),T (%),C (%),G (%),A+T (%),G+C (%),AT skew,GC skew
#         rvscmp_seq = self.rvscmp_seq.upper()
#         seqStat_rvscmp = SeqGrab(rvscmp_seq)
#         seqCoding = SeqGrab(self.plus_coding_seq)
#         seqCodingOnly = SeqGrab(self.plus_coding_gene_only)
#         ffds = SeqGrab(self.PCGs_strim).extract_ffds(self.code_table) # extract fourfold degenerate sites
#         ffds_seq = SeqGrab(ffds)
#         ffds_plus = SeqGrab(self.PCGs_strim_plus).extract_ffds(self.code_table)  # extract fourfold degenerate sites only for PCGs on plus strand
#         ffds_seq_plus = SeqGrab(ffds_plus)
#         NCR_seq = SeqGrab(self.NCR_seq)
#         NCR_ratio = str(NCR_seq.length/len(self.str_seq))
#         list_species_info = [self.ID, self.organism, self.usedName] + self.list_lineages + \
#                             [str(len(self.str_seq)), str(seqCoding.length), seqStat.A_percent, seqStat.T_percent,
#                              seqStat.C_percent, seqStat.G_percent, seqStat.AT_percent,
#                              seqStat.GC_percent, seqStat.AT_skew, seqStat.GC_skew,
#                              seqStat_rvscmp.AT_skew, seqStat_rvscmp.GC_skew, seqCoding.GC_skew,
#                              seqCodingOnly.GC_skew, ffds_seq.GC_skew, ffds_seq_plus.GC_skew,
#                              NCR_seq.GC_skew, NCR_ratio]
#                              # seqStat_rvscmp.A_percent, seqStat_rvscmp.T_percent,
#                              # seqStat_rvscmp.C_percent, seqStat_rvscmp.G_percent, seqStat_rvscmp.AT_percent,
#                              # seqStat_rvscmp.GC_percent, seqStat_rvscmp.AT_skew, seqStat_rvscmp.GC_skew]
#         self.species_info += ",".join(list_species_info) + "\n"
#         self.taxonomy_infos += ",".join([self.usedName, self.ID, self.organism] + self.list_lineages) + "\n"
#
#         #         PCG
#         PCGs_stat_plus, first_stat_plus, second_stat_plus, third_stat_plus = self.stat_PCG_sub(self.PCGs_strim_plus, "+") \
#                                                                  if self.PCGs_strim_plus else ["", "", "", ""]
#         PCGs_stat_minus, first_stat_minus, second_stat_minus, third_stat_minus = self.stat_PCG_sub(self.PCGs_strim_minus, "-") \
#                                                                     if self.PCGs_strim_minus else ["", "", "", ""]
#         PCGs_stat, first_stat, second_stat, third_stat = self.stat_PCG_sub(
#                                                                     self.PCGs_strim, "all") \
#                                                                     if self.PCGs_strim else ["", "", "", ""]
#         #         rRNA
#         rRNA_stat = self.stat_other_sub(self.rRNAs, "all", "rRNAs") if self.rRNAs else ""
#         if not self.rRNAs: self.geneStat_sub("rRNAs(all)", "N/A")  ##要补个NA
#         rRNA_stat_plus = self.stat_other_sub(self.rRNAs_plus, "+", "rRNAs") if self.rRNAs_plus else ""
#         if not self.rRNAs_plus: self.geneStat_sub("rRNAs(+)", "N/A") ##要补个NA
#         rRNA_stat_minus = self.stat_other_sub(self.rRNAs_minus, "-", "rRNAs") if self.rRNAs_minus else ""
#         if not self.rRNAs_minus: self.geneStat_sub("rRNAs(-)", "N/A")  ##要补个NA
#         #         tRNA
#         tRNA_stat = self.stat_other_sub(self.tRNAs, "all", "tRNAs") if self.tRNAs else ""
#         if not self.tRNAs: self.geneStat_sub("tRNAs(all)", "N/A")  ##要补个NA
#         tRNA_stat_plus = self.stat_other_sub(self.tRNAs_plus, "+", "tRNAs") if self.tRNAs_plus else ""
#         if not self.tRNAs_plus: self.geneStat_sub("tRNAs(+)", "N/A")  ##要补个NA
#         tRNA_stat_minus = self.stat_other_sub(self.tRNAs_minus, "-", "tRNAs") if self.tRNAs_minus else ""
#         if not self.tRNAs_minus: self.geneStat_sub("tRNAs(-)", "N/A")  ##要补个NA
#         stat = 'Regions,Strand,Size (bp),T(U),C,A,G,AT(%),GC(%),GT(%),AT skew,GC skew\n' + PCGs_stat + PCGs_stat_plus + \
#                PCGs_stat_minus + first_stat + first_stat_plus + first_stat_minus + second_stat + second_stat_plus + second_stat_minus +\
#                third_stat + third_stat_plus + third_stat_minus + ''.join(list_genes) + \
#                rRNA_stat + rRNA_stat_plus + rRNA_stat_minus + tRNA_stat + tRNA_stat_plus + tRNA_stat_minus + geom_stat
#         self.dict_spe_stat[self.ID] = stat + "PCGs: protein-coding genes; +: major strand; -: minus strand\n"
#         # 生成折线图分类信息
#         list_genes_line = [
#             value for (
#                 key, value) in sorted(
#                 self.dict_genes.items()) if not key.startswith("zNCR")]
#         p_spe = PCGs_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if PCGs_stat else ""
#         p_spe_plus = PCGs_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if PCGs_stat_plus else ""
#         p_spe_minus = PCGs_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if PCGs_stat_minus else ""
#         t_spe = tRNA_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if tRNA_stat else ""
#         t_spe_plus = tRNA_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if tRNA_stat_plus else ""
#         t_spe_minus = tRNA_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if tRNA_stat_minus else ""
#         r_spe = rRNA_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if rRNA_stat else ""
#         r_spe_plus = rRNA_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if rRNA_stat_plus else ""
#         r_spe_minus = rRNA_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if rRNA_stat_minus else ""
#         fst_spe = first_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if first_stat else ""
#         fst_spe_plus = first_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if first_stat_plus else ""
#         fst_spe_minus = first_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if first_stat_minus else ""
#         scd_spe = second_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if second_stat else ""
#         scd_spe_plus = second_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if second_stat_plus else ""
#         scd_spe_minus = second_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if second_stat_minus else ""
#         trd_spe = third_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if third_stat else ""
#         trd_spe_plus = third_stat_plus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if third_stat_plus else ""
#         trd_spe_minus = third_stat_minus.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" if third_stat_minus else ""
#         self.line_spe_stat += geom_stat.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" + p_spe + p_spe_plus + p_spe_minus + \
#                               t_spe + t_spe_plus + t_spe_minus + r_spe + r_spe_plus + r_spe_minus + fst_spe + fst_spe_plus + fst_spe_minus + \
#                               scd_spe + scd_spe_plus + scd_spe_minus + trd_spe + trd_spe_plus + trd_spe_minus + \
#                               "".join([i.strip("\n") + "," + self.ID + "," + self.taxonmy + "\n" for i in list_genes_line])
#         rscu_sum = RSCUsum(self.organism_1, self.PCGs_strim, str(self.code_table))
#         rscu_table = rscu_sum.table
#         self.dict_RSCU[self.ID] = rscu_table
#         self.dict_all_spe_RSCU["title"] += self.organism + ","
#         self.dict_all_codon_COUNT["title"] += self.organism + ","
#         self.dict_all_AA_COUNT["title"] += self.organism + ","
#         self.dict_all_AA_RATIO["title"] += self.organism + ","
#         rscu_stack = RSCUstack(
#             rscu_table,
#             self.dict_all_spe_RSCU,
#             self.dict_all_codon_COUNT,
#             self.dict_all_AA_COUNT,
#             self.dict_all_AA_RATIO,
#             self.numbered_Name(
#                 self.organism,
#                 omit=True))
#         self.dict_all_spe_RSCU = rscu_stack.dict_all_rscu
#         self.dict_all_codon_COUNT = rscu_stack.dict_all_codon_count
#         self.dict_all_AA_COUNT = rscu_stack.dict_all_AA_count
#         self.dict_all_AA_RATIO = rscu_stack.dict_all_AA_ratio
#         self.dict_AAusage[self.ID] = rscu_stack.stat
#         self.dict_RSCU_stack[self.ID] = rscu_stack.stack
#         self.dict_AA_stack[self.ID] = rscu_stack.aaStack
#         # 存放基因间隔区序列
#         # self.dict_igs[self.ID] = self.igs
#         # self.list_spe_stat.append(self.reference_)
#         self.dict_all_stat["_".join(
#             self.list_lineages + [self.organism + "_" + self.ID])] = self.list_spe_stat
#         #         生成PCG串联序列
#         self.PCG_seq += '>' + self.usedName + '\n' + self.PCGs_strim + '\n'
#         self.tRNA_seqs += '>' + self.usedName + '\n' + self.tRNAs + '\n'
#         self.rRNA_seqs += '>' + self.usedName + '\n' + self.rRNAs + '\n'
#         #         组成表
#         self.orgTable += "Overlap:," + \
#                          str(self.overlap) + "," + "gap:," + str(self.gap)
#         self.dict_orgTable[self.ID] = self.orgTable
#         self.linear_order += self.gene_order + '\n'
#         # 密码子偏倚分析
#         if self.dict_args["cal_codon_bias"]:
#             codonBias = CodonBias(self.PCGs_strim,
#                                   codeTable=self.code_table,
#                                   codonW=self.dict_args["CodonW_exe"],
#                                   path=self.exportPath)
#             list_cBias = codonBias.getCodonBias()
#             self.codon_bias += ",".join([self.usedName, "PCGs"] + list_cBias) + "," + self.taxonmy + "\n"
#         # map ID to tree name
#         self.dict_ID_treeName[self.ID] = self.usedName
#
#     def check_Absence(self):
#         if len(self.list_pro) != 0:  # 有些物种缺失部分基因
#             for i in self.list_pro:
#                 if i in ["rrnS", "rrnL"]:
#                     if i in list(self.dict_RNA.keys()):  # 如果字典已经有这个键
#                         self.dict_RNA[i] += ',N/A'
#                         self.dict_gene_ATskews[i] += ',N/A'
#                         self.dict_gene_GCskews[i] += ',N/A'
#                         self.dict_gene_ATCont[i] += ',N/A'
#                         self.dict_gene_GCCont[i] += ',N/A'
#                     else:
#                         self.dict_RNA[i] = i + ',N/A'
#                         self.dict_gene_ATskews[i] = i + ',N/A'
#                         self.dict_gene_GCskews[i] = i + ',N/A'
#                         self.dict_gene_ATCont[i] = i + ',N/A'
#                         self.dict_gene_GCCont[i] = i + ',N/A'
#                 else:
#                     if i in list(self.dict_PCG.keys()):
#                         self.dict_PCG[i] += ',N/A'
#                         self.dict_start[i] += ',N/A'
#                         self.dict_stop[i] += ',N/A'
#                         self.dict_gene_ATskews[i] += ',N/A'
#                         self.dict_gene_GCskews[i] += ',N/A'
#                         self.dict_gene_ATCont[i] += ',N/A'
#                         self.dict_gene_GCCont[i] += ',N/A'
#                     else:
#                         self.dict_PCG[i] = i + ',N/A'
#                         self.dict_start[i] = i + ',N/A'
#                         self.dict_stop[i] = i + ',N/A'
#                         self.dict_gene_ATskews[i] = i + ',N/A'
#                         self.dict_gene_GCskews[i] = i + ',N/A'
#                         self.dict_gene_ATCont[i] = i + ',N/A'
#                         self.dict_gene_GCCont[i] = i + ',N/A'
#
#     def fun_orgTable(self, new_name, size, ini, ter, seq):
#         # 生成组成表相关
#         orgSize = self.end - self.start + 1
#         orgSize = orgSize if self.orgTable[-7:
#                              ] != 'Strand\n' else int(size)
#         space = self.start - self.lastEndIndex - 1
#         if space > 0:
#             self.gap += 1
#         elif space < 0:
#             self.overlap += 1
#         overlap_start_index = abs(space) if space < 0 else 0  # 为了去掉重叠区
#         space1 = "" if space == 0 or self.orgTable[-7:] == 'Strand\n' else str(
#             space)
#         chain = "H" if self.strand == "+" else "L"
#         # 新增了添加序列功能
#         self.orgTable += ",".join([new_name,
#                                    str(self.start),
#                                    str(self.end),
#                                    str(orgSize),
#                                    space1,
#                                    ini,
#                                    ter,
#                                    chain,
#                                    seq]) + "\n"
#         if space > 0:
#             self.NCR_seq += self.str_seq[self.lastEndIndex:self.start-1]
#         self.lastEndIndex = self.end
#         # 编码序列，负链基因反向互补
#         if self.feature_type not in ["intergenic_regions", "misc_feature",
#                                  "overlapping_regions", "rep_origin",
#                                  "repeat_region", "stem_loop", "D-loop"]:
#             if chain == "H":
#                 self.plus_coding_seq += seq[overlap_start_index:]
#                 self.plus_coding_gene_only += seq[overlap_start_index:]
#             # 如果space负的，就是重叠区，如果是正链的基因，就从序列头部减掉overlapping，如果是负链的基因，就从序列的尾部减去
#             else:
#                 self.plus_coding_seq += str(Seq(seq, generic_dna).reverse_complement())[overlap_start_index:]
#         else:
#             self.NCR_seq += seq
#
#     def judge(self, name, values, seq):
#         if name == 'tRNA-Leu' or name == 'tRNA-Ser' or name == "L" or name == "S":
#             if re.search(
#                     r'(?<=[^1-9a-z_])(CUA|CUN|[tu]ag|L1|trnL1|Leu1)(?=[^1-9a-z_])',
#                     values,
#                     re.I):
#                 name = 'tRNA-Leu1' if name == 'tRNA-Leu' else "L1"
#             elif re.search(r'(?<=[^1-9a-z_])(UUA|UUR|[tu]aa|L2|trnL2|Leu2)(?=[^1-9a-z_])', values, re.I):
#                 name = 'tRNA-Leu2' if name == 'tRNA-Leu' else "L2"
#             elif re.search(r'(?<=[^1-9a-z_])(UCA|UCN|[tu]ga|S2|trnS2|Ser2)(?=[^1-9a-z_])', values, re.I):
#                 name = 'tRNA-Ser2' if name == 'tRNA-Ser' else "S2"
#             elif re.search(r'(?<=[^1-9a-z_])(AGC|AGN|AGY|gc[tu]|[tu]c[tu]|S1|trnS1|Ser1)(?=[^1-9a-z_])', values, re.I):
#                 name = 'tRNA-Ser1' if name == 'tRNA-Ser' else "S1"
#             else:
#                 # 单独把序列生成出来
#                 trnaName = self.factory.refineName(self.usedName +
#                                                    "_" + str(self.start) + "_" + str(self.end), remain_words=".-")
#                 self.leu_ser += ">%s\n%s\n" % (trnaName, seq)
#         else:
#             name = name
#         return name
#
#     def trim_ter(self, raw_sequence):
#         size = len(raw_sequence)
#         if size % 3 == 0:
#             if raw_sequence[-3:].upper() in self.stopCodon:
#                 trim_sequence = raw_sequence[:-3]
#             else:
#                 trim_sequence = raw_sequence
#         elif size % 3 == 1:
#             trim_sequence = raw_sequence[:-1]
#         elif size % 3 == 2:
#             trim_sequence = raw_sequence[:-2]
#         else:
#             trim_sequence = raw_sequence
#         return trim_sequence
#
#     def CDS_(self):
#         seq = str(self.feature.extract(self.seq))
#         codon_start = self.qualifiers['codon_start'][0] if "codon_start" in self.qualifiers else "1"
#         seq = seq[int(codon_start)-1:] if codon_start != "1" else seq
#         def codon(seq):
#             seq = seq.upper()
#             size = len(seq)
#             ini = seq[0:3]
#             if size % 3 == 0:
#                 if seq[-3:].upper() in self.stopCodon:
#                     trim_sequence = seq[:-3]
#                     ter = seq[-3:]
#                 else:
#                     ter = "---"
#                     trim_sequence = seq
#                 # 计算RSCU用的，保留终止密码子，但是不保留不完整的终止密码子
#                 RSCU_seq = seq
#             elif size % 3 == 1:
#                 ter = seq[-1]
#                 trim_sequence = seq[:-1]
#                 RSCU_seq = seq[:-1]
#             elif size % 3 == 2:
#                 ter = seq[-2:]
#                 trim_sequence = seq[:-2]
#                 RSCU_seq = seq[:-2]
#             return ini, ter, size, seq, trim_sequence, RSCU_seq
#
#         # trim_sequence是删除终止子以后的
#         ini, ter, size, seq, trim_sequence, RSCU_seq = codon(seq)
#         new_name = self.fetchGeneName()
#         if not new_name:
#             return
#         if new_name.upper() in self.dict_unify_mtname:
#             # 换成标准的名字
#             new_name = self.dict_unify_mtname[new_name.upper()]
#         if new_name in self.list_pro:
#             self.list_pro.remove(new_name)
#         self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
#         self.dict_pro[new_name + '>' + self.organism_1 + '_' + self.ID] = '>' + \
#                                                                           self.usedName + '\n' + seq + \
#                                                                           '\n'  # 这里不能用seq代替，因为要用大小写区分正负链
#         translation = self.qualifiers['translation'][0] if 'translation' in self.qualifiers else ""  # 有时候没有translation
#         self.dict_AA[new_name + '>' + self.organism_1 + '_' +
#                      self.ID] = '>' + self.usedName + '\n' + translation + "\n"
#         self.gene_order += self.omit_strand + new_name + ' '
#         seqStat = SeqGrab(seq)
#         self.dict_genes[new_name] = ",".join(
#             [
#                 new_name,
#                 self.strand,
#                 seqStat.size,
#                 seqStat.T_percent,
#                 seqStat.C_percent,
#                 seqStat.A_percent,
#                 seqStat.G_percent,
#                 seqStat.AT_percent,
#                 seqStat.GC_percent,
#                 seqStat.GT_percent,
#                 seqStat.AT_skew,
#                 seqStat.GC_skew]) + "\n"
#         if new_name in self.list_PCGs:  # 确保是属于那14或者15个基因
#             if new_name in self.dict_PCG:  # 看字典是否已经有这个键
#                 self.dict_PCG[new_name] += ',' + str(size)
#                 self.dict_start[new_name] += ',' + ini
#                 self.dict_stop[new_name] += ',' + ter
#                 self.dict_gene_ATskews[new_name] += ',' + seqStat.AT_skew
#                 self.dict_gene_GCskews[new_name] += ',' + seqStat.GC_skew
#                 self.dict_gene_ATCont[new_name] += ',' + seqStat.AT_percent
#                 self.dict_gene_GCCont[new_name] += ',' + seqStat.GC_percent
#             else:
#                 self.dict_PCG[new_name] = new_name + ',' + str(size)
#                 self.dict_start[new_name] = new_name + ',' + ini
#                 self.dict_stop[new_name] = new_name + ',' + ter
#                 self.dict_gene_ATskews[new_name] = new_name + ',' + seqStat.AT_skew
#                 self.dict_gene_GCskews[new_name] = new_name + ',' + seqStat.GC_skew
#                 self.dict_gene_ATCont[new_name] = new_name + ',' + seqStat.AT_percent
#                 self.dict_gene_GCCont[new_name] = new_name + ',' + seqStat.GC_percent
#         self.PCGs_strim += RSCU_seq
#         if self.strand == "+":
#             self.PCGs_strim_plus += RSCU_seq
#         else:
#             self.PCGs_strim_minus += RSCU_seq
#         # self.PCGs += seq
#         # 生成组成表相关
#         self.fun_orgTable(new_name, size, ini, ter, seq)
#         ##间隔区提取
#         self.refresh_pairwise_feature(new_name)
#         ##密码子偏倚分析
#         if self.dict_args["cal_codon_bias"]:
#             codonBias = CodonBias(RSCU_seq,
#                                   codeTable=self.code_table,
#                                   codonW=self.dict_args["CodonW_exe"],
#                                   path=self.exportPath)
#             list_cBias = codonBias.getCodonBias()
#             self.codon_bias += ",".join([self.usedName, new_name] + list_cBias) + "," + self.taxonmy + "\n"
#
#     def rRNA_(self):
#         new_name = self.fetchGeneName()
#         if not new_name:
#             return
#         seq = str(self.feature.extract(self.seq))
#         if new_name.upper() in self.dict_unify_mtname:
#             # 换成标准的名字
#             new_name = self.dict_unify_mtname[new_name.upper()]
#         if new_name in self.list_pro:
#             self.list_pro.remove(new_name)
#         self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
#         self.dict_rRNA[new_name + '>' + self.organism_1 + '_' +
#                        self.ID] = '>' + self.usedName + '\n' + seq + '\n'
#         if self.dict_args["rRNAchecked"]:
#             self.gene_order += self.omit_strand + new_name + ' '
#         seqStat = SeqGrab(seq.upper())
#         self.dict_genes[new_name] = ",".join([new_name,
#                                               self.strand,
#                                               seqStat.size,
#                                               seqStat.T_percent,
#                                               seqStat.C_percent,
#                                               seqStat.A_percent,
#                                               seqStat.G_percent,
#                                               seqStat.AT_percent,
#                                               seqStat.GC_percent,
#                                               seqStat.GT_percent,
#                                               seqStat.AT_skew,
#                                               seqStat.GC_skew]) + "\n"
#         if new_name in self.dict_RNA:  # 如果字典已经有这个键
#             self.dict_RNA[new_name] += ',' + str(len(seq))
#             self.dict_gene_ATskews[new_name] += ',' + seqStat.AT_skew
#             self.dict_gene_GCskews[new_name] += ',' + seqStat.GC_skew
#             self.dict_gene_ATCont[new_name] += ',' + seqStat.AT_percent
#             self.dict_gene_GCCont[new_name] += ',' + seqStat.GC_percent
#         else:
#             self.dict_RNA[new_name] = new_name + \
#                                       ',' + str(len(seq))
#             self.dict_gene_ATskews[new_name] = new_name + ',' + seqStat.AT_skew
#             self.dict_gene_GCskews[new_name] = new_name + ',' + seqStat.GC_skew
#             self.dict_gene_ATCont[new_name] = new_name + ',' + seqStat.AT_percent
#             self.dict_gene_GCCont[new_name] = new_name + ',' + seqStat.GC_percent
#         self.rRNAs += seq
#         if self.strand == "+":
#             self.rRNAs_plus += seq
#         else:
#             self.rRNAs_minus += seq
#         # 生成组成表相关
#         self.fun_orgTable(new_name, seqStat.length, "", "", seq)
#         ##间隔区提取
#         self.refresh_pairwise_feature(new_name)
#
#     def tRNA_(self):
#         replace_name = self.fetchGeneName()
#         if not replace_name:
#             return
#         seq = str(self.feature.extract(self.seq))
#         values = ':' + ':'.join([i[0] for i in self.qualifiers.values()]) + ':'
#         name = self.judge(replace_name, values, seq)
#         list_tRNA = [
#             "T",
#             "C",
#             "E",
#             "Y",
#             "R",
#             "G",
#             "H",
#             "L1",
#             "L2",
#             "S1",
#             "S2",
#             "Q",
#             "F",
#             "M",
#             "V",
#             "A",
#             "D",
#             "N",
#             "P",
#             "I",
#             "K",
#             "W",
#             "S",
#             "L"]
#         new_name = "trn" + name if name in list_tRNA else name
#         self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
#         self.dict_tRNA[new_name + '>' + self.organism_1 + '_' +
#                        self.ID] = '>' + self.usedName + '\n' + seq + '\n'
#         if self.dict_args["tRNAchecked"]:
#             self.gene_order += self.omit_strand + name + ' '
#         self.tRNAs += seq.upper()
#         if self.strand == "+":
#             self.tRNAs_plus += seq.upper()
#         else:
#             self.tRNAs_minus += seq.upper()
#         # 生成组成表相关
#         self.fun_orgTable(new_name, len(seq), "", "", seq)
#         ##间隔区提取
#         self.refresh_pairwise_feature(new_name)
#
#     def extract(self):
#         # gb_records = SeqIO.parse(self.gbContentIO, "genbank")
#         self.init_args_all()
#         # 专门用于判断
#         included_features = [i.upper() for i in self.included_features]
#         for num, gb_file in enumerate(self.gb_files):
#             try:
#                 gb = SeqIO.parse(gb_file, "genbank")
#                 gb_record = next(gb)
#                 self.name = gb_record.name
#                 self.list_pro = self.list_PCGs[:]
#                 features = gb_record.features
#                 annotations = gb_record.annotations
#                 self.organism = annotations["organism"]
#                 self.organism_1 = self.organism.replace(" ", "_")
#                 self.description = gb_record.description
#                 self.date = annotations["date"]
#                 self.ID = gb_record.id
#                 self.seq = gb_record.seq
#                 self.str_seq = str(self.seq)
#                 self.rvscmp_seq = str(Seq(self.str_seq, generic_dna).reverse_complement())
#                 self.dict_type_genes = OrderedDict()
#                 self.init_args_each()
#                 self.plus_coding_seq = ""  # 正链编码的序列，负链编码基因的序列会被反向互补并与这个一起
#                 self.plus_coding_gene_only = "" # 仅在正链编码基因的序列
#                 ok = self.check_records(features)
#                 if not ok: continue
#                 has_feature = False
#                 has_source = False
#                 source_parsed = False
#                 for self.feature in features:
#                     self.qualifiers = self.feature.qualifiers
#                     self.start = int(self.feature.location.start) + 1
#                     self.end = int(self.feature.location.end)
#                     self.strand = "+" if self.feature.location.strand == 1 else "-"
#                     self.omit_strand = "" if self.strand == "+" else "-"
#                     # # 用于生成organization表
#                     # self.positionFrom, self.positionTo = list1[0], list1[-1]
#                     self.feature_type = self.feature.type
#                     if self.feature_type not in (self.list_features + ["source"]):
#                         self.list_features.append(self.feature_type)
#                     if (self.feature.type == "source") and (not source_parsed):
#                         self.parseSource()
#                         has_source = True
#                         source_parsed = True
#                     elif self.feature_type == 'CDS':
#                         self.code_table = int(self.qualifiers["transl_table"][0]) if ("transl_table" in self.qualifiers) \
#                             and self.qualifiers["transl_table"][0].isnumeric() else self.selected_code_table
#                         self.fetchTerCodon() #得到终止密码子
#                         self.CDS_()
#                         self.getNCR()
#                         has_feature = True
#                     elif self.feature_type == 'rRNA':
#                         self.rRNA_()
#                         self.getNCR()
#                         has_feature = True
#                     elif self.feature_type == 'tRNA':
#                         self.tRNA_()
#                         self.getNCR()
#                         has_feature = True
#                     elif self.included_features == "All" or self.feature_type.upper() in included_features:
#                         # 剩下的按照常规的来提取
#                         self.parseFeature()
#                         self.getNCR()
#                         has_feature = True
#                 if not has_feature:
#                     ##ID里面没有找到任何对应的feature的情况
#                     name = self.usedName if has_source else self.ID
#                     self.list_none_feature_IDs.append(name)
#                 self.gb_record_stat()
#                 self.check_Absence()
#                 self.getNCR(mode="end")  ##判断最后的间隔区
#                 self.input_file.write(gb_record.format("genbank"))
#             except:
#                 self.Error_ID += self.name + ":\n" + \
#                                  ''.join(
#                                      traceback.format_exception(*sys.exc_info())) + "\n"
#             num += 1
#             self.progressSig.emit(num * 70 / self.totleID)
#         self.input_file.close()
#
#     def sort_CDS(self):
#         list_pro = sorted(list(self.dict_pro.keys()))
#         previous = ''
#         seq_pro = ''
#         trans_pro = ''
#         seq_aa = ""  # 存放读取的translation里面的AA序列
#         # 避免报错
#         gene = ""
#         it = iter(list_pro)
#         table = CodonTable.ambiguous_dna_by_id[self.code_table]
#         while True:
#             try:
#                 i = next(it)
#                 gene = re.match('^[^>]+', i).group()
#                 if gene == previous or previous == '':
#                     seq_pro += self.dict_pro[i]
#                     seq_aa += self.dict_AA[i]
#                     raw_sequence = self.dict_pro[i].split('\n')[1]
#                     trim_sequence = self.trim_ter(raw_sequence)
#                     try:
#                         protein = _translate_str(trim_sequence, table)
#                     except:
#                         protein = ""
#                     trans_pro += self.dict_pro[
#                         i].replace(raw_sequence, protein)
#                     previous = gene
#                 if gene != previous:
#                     self.save2file(seq_pro, previous, self.CDS_nuc_path)
#                     self.save2file(seq_aa, previous, self.CDS_aa_path)
#                     self.save2file(trans_pro, previous, self.CDS_TrsAA_path)
#                     seq_pro = ''
#                     trans_pro = ''
#                     seq_aa = ""  # 存放读取的translation里面的AA序列
#                     seq_pro += self.dict_pro[i]
#                     seq_aa += self.dict_AA[i]
#                     raw_sequence = self.dict_pro[i].split('\n')[1]
#                     trim_sequence = self.trim_ter(raw_sequence)
#                     try:
#                         protein = _translate_str(trim_sequence, table)
#                     except:
#                         protein = ""
#                     trans_pro += self.dict_pro[
#                         i].replace(raw_sequence, protein)
#                     previous = gene
#             except StopIteration:
#                 self.save2file(seq_pro, previous, self.CDS_nuc_path)
#                 self.save2file(seq_aa, previous, self.CDS_aa_path)
#                 self.save2file(trans_pro, previous, self.CDS_TrsAA_path)
#                 break
#
#     def sort_rRNA(self):
#         list_rRNA = sorted(list(self.dict_rRNA.keys()))
#         previous = ''
#         seq_rRNA = ''
#         # 避免报错
#         gene = ""
#         it = iter(list_rRNA)
#         while True:
#             try:
#                 i = next(it)
#                 gene = re.match('^[^>]+', i).group()
#                 if gene == previous or previous == '':
#                     seq_rRNA += self.dict_rRNA[i]
#                     previous = gene
#                 if gene != previous:
#                     self.save2file(seq_rRNA, previous, self.rRNA_path)
#                     seq_rRNA = ''
#                     seq_rRNA += self.dict_rRNA[i]
#                     previous = re.match('^[^>]+', i).group()
#             except StopIteration:
#                 self.save2file(seq_rRNA, previous, self.rRNA_path)
#                 break
#
#     def sort_tRNA(self):
#         list_tRNA = sorted(list(self.dict_tRNA.keys()))
#         previous = ''
#         seq_tRNA = ''
#         # 避免报错
#         gene = ""
#         it = iter(list_tRNA)
#         while True:
#             try:
#                 i = next(it)
#                 gene = re.match('^[^>]+', i).group()
#                 if gene == previous or previous == '':
#                     seq_tRNA += self.dict_tRNA[i]
#                     previous = gene
#                 if gene != previous:
#                     self.save2file(seq_tRNA, previous, self.tRNA_path)
#                     seq_tRNA = ''
#                     seq_tRNA += self.dict_tRNA[i]
#                     previous = re.match('^[^>]+', i).group()
#             except StopIteration:
#                 self.save2file(seq_tRNA, previous, self.tRNA_path)
#                 break
#
#     def gene_sort_save(self):
#         self.CDS_nuc_path = self.factory.creat_dirs(self.exportPath + os.sep + "CDS_NUC")
#         self.CDS_aa_path = self.factory.creat_dirs(self.exportPath + os.sep + "CDS_AA")
#         self.CDS_TrsAA_path = self.factory.creat_dirs(self.exportPath + os.sep + "self-translated_AA")
#         self.sort_CDS()
#         self.progressSig.emit(82)
#         self.rRNA_path = self.factory.creat_dirs(self.exportPath + os.sep + "rRNA")
#         self.sort_rRNA()
#         self.progressSig.emit(87)
#         self.tRNA_path = self.factory.creat_dirs(self.exportPath + os.sep + "tRNA")
#         self.sort_tRNA()
#         self.progressSig.emit(92)
#         keys = list(self.dict_feature_fas.keys())
#         #只保留有效值
#         for i in keys:
#             if not self.dict_feature_fas[i]:
#                 del self.dict_feature_fas[i]
#         total = len(self.dict_feature_fas)
#         if not total:
#             self.progressSig.emit(95)
#             return
#         base = 92
#         proportion = 3 / total
#         for feature in self.dict_feature_fas:
#             feature_fas = self.dict_feature_fas[feature]
#             if not feature_fas:
#                 ##如果没有提取到任何东西就返回
#                 continue
#             featurePath = self.factory.creat_dirs(self.exportPath + os.sep + feature)
#             base = self.save_each_feature(feature_fas, featurePath, base, proportion)
#
#     def saveGeneralFile(self):
#         super(GBextract_MT, self).saveGeneralFile()
#         filesPath = self.factory.creat_dirs(self.exportPath + os.sep + 'files')
#         with open(filesPath + os.sep + 'linear_order.txt', 'w', encoding="utf-8") as f:
#             f.write(self.linear_order)
#         with open(filesPath + os.sep + 'complete_seq.fas', 'w', encoding="utf-8") as f:
#             f.write(self.complete_seq)
#         with open(filesPath + os.sep + 'PCG_seqs.fas', 'w', encoding="utf-8") as f6:
#             f6.write(self.PCG_seq)
#         with open(filesPath + os.sep + 'tRNA_seqs.fas', 'w', encoding="utf-8") as f7:
#             f7.write(self.tRNA_seqs)
#         with open(filesPath + os.sep + 'rRNA_seqs.fas', 'w', encoding="utf-8") as f8:
#             f8.write(self.rRNA_seqs)
#         # super(GBextract_MT, self).saveGeneralFile()
#
#     def saveItolFiles(self):
#         itolPath = self.factory.creat_dirs(self.exportPath + os.sep + 'itolFiles')
#         itol_domain = "DATASET_DOMAINS\nSEPARATOR COMMA\nDATASET_LABEL,Mito gene order\nCOLOR,#ff00aa\nWIDTH,1250\nBACKBONE_COLOR,black\nHEIGHT_FACTOR,0.8\nLEGEND_TITLE,Regions\nLEGEND_SHAPES,%s,%s,%s,%s,%s,%s,%s\nLEGEND_COLORS,%s,%s,%s,%s,%s,%s,%s\nLEGEND_LABELS,atp6|atp8,nad1-6|nad4L,cytb,cox1-3,rRNA,tRNA,NCR\n#SHOW_INTERNAL,0\nSHOW_DOMAIN_LABELS,1\nLABELS_ON_TOP,1\nDATA\n" % (
#             self.dict_args["atpshape"], self.dict_args["nadshape"], self.dict_args["cytbshape"],
#             self.dict_args["coxshape"], self.dict_args["rRNAshape"], self.dict_args["tRNAshape"],
#             self.dict_args["NCRshape"], self.dict_args["atpcolour"], self.dict_args["nadcolour"],
#             self.dict_args["cytbcolour"], self.dict_args["coxcolour"], self.dict_args["rRNAcolour"],
#             self.dict_args["tRNAcolour"], self.dict_args["NCRcolour"])
#         order2itol = Order2itol(self.linear_order, self.dict_args)
#         itol_domain += order2itol.itol_domain
#         super(GBextract_MT, self).saveItolFiles()
#         with open(itolPath + os.sep + 'itol_gene_order.txt', 'w', encoding="utf-8") as f1:
#             f1.write(itol_domain)
#
#     def saveStatFile(self):
#         super(GBextract_MT, self).saveStatFile()
#         statFilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'StatFiles')
#         # 生成speciesStat文件夹
#         speciesStatPath = self.factory.creat_dirs(statFilePath + os.sep + 'speciesStat')
#         # 生成RSCU文件夹
#         RSCUpath = self.factory.creat_dirs(statFilePath + os.sep + 'RSCU')
#         # 生成CDS文件夹
#         CDSpath = self.factory.creat_dirs(statFilePath + os.sep + 'CDS')
#         # RSCU  PCA# 生成PCA用的统计表
#         title_rscu = self.dict_all_spe_RSCU.pop("title").strip(",") + "\n"
#         for j in list(self.dict_all_spe_RSCU.keys()):
#             title_rscu += j + "," + \
#                           ",".join(self.dict_all_spe_RSCU[j]) + "\n"
#         # 生成文件
#         with open(RSCUpath + os.sep + "all_rscu_stat.csv", "w", encoding="utf-8") as f:
#             f.write(title_rscu)
#         # COUNT codon PCA# 生成PCA用的统计表
#         title_codon_count = self.dict_all_codon_COUNT.pop(
#             "title").strip(",") + "\n"
#         for j in list(self.dict_all_codon_COUNT.keys()):
#             title_codon_count += j + "," + \
#                                  ",".join(self.dict_all_codon_COUNT[j]) + "\n"
#         # 生成文件
#         with open(RSCUpath + os.sep + "all_codon_count_stat.csv", "w", encoding="utf-8") as f:
#             f.write(title_codon_count)
#         # COUNT aa PCA# 生成PCA用的统计表
#         title_AA_count = self.dict_all_AA_COUNT.pop(
#             "title").strip(",") + "\n"
#         for j in list(self.dict_all_AA_COUNT.keys()):
#             title_AA_count += j + "," + \
#                               ",".join(self.dict_all_AA_COUNT[j]) + "\n"
#         # 生成文件
#         with open(RSCUpath + os.sep + "all_AA_count_stat.csv", "w", encoding="utf-8") as f:
#             f.write(title_AA_count)
#         # ratio aa PCA# 生成PCA用的统计表
#         title_AA_ratio = self.dict_all_AA_RATIO.pop(
#             "title").strip(",") + "\n"
#         for j in list(self.dict_all_AA_RATIO.keys()):
#             title_AA_ratio += j + "," + \
#                               ",".join(self.dict_all_AA_RATIO[j]) + "\n"
#         # 生成文件
#         with open(RSCUpath + os.sep + "all_AA_ratio_stat.csv", "w", encoding="utf-8") as f:
#             f.write(title_AA_ratio)
#         # 生成AA stack的文件
#         title_aa_stack = self.dict_AA_stack.pop(
#             "title") + "\n"
#         for k in self.dict_AA_stack:
#             title_aa_stack += self.dict_AA_stack[k]
#         with open(RSCUpath + os.sep + "all_AA_stack.csv", "w", encoding="utf-8") as f:
#             f.write(title_aa_stack)
#         # 统计单个物种
#         for j in self.dict_spe_stat:
#             file_name = self.dict_ID_treeName.get(j, j)
#             if j in self.dict_spe_stat:
#                 with open(speciesStatPath + os.sep + file_name + '.csv', 'w', encoding="utf-8") as f:
#                     f.write(self.dict_spe_stat[j])
#             if j in self.dict_orgTable:
#                 with open(speciesStatPath + os.sep + file_name + '_org.csv', 'w', encoding="utf-8") as f:
#                     f.write(self.dict_orgTable[j])
#             if j in self.dict_AAusage:
#                 with open(RSCUpath + os.sep + file_name + '_AA_usage.csv', 'w', encoding="utf-8") as f:
#                     f.write(self.dict_AAusage[j])
#             if j in self.dict_RSCU:
#                 with open(RSCUpath + os.sep + file_name + '_RSCU.csv', 'w', encoding="utf-8") as f:
#                     f.write(self.dict_RSCU[j])
#             if j in self.dict_RSCU_stack:
#                 with open(RSCUpath + os.sep + file_name + '_RSCU_stack.csv', 'w', encoding="utf-8") as f:
#                     f.write(self.dict_RSCU_stack[j])
#         # with open(statFilePath + os.sep + 'taxonomy.csv', 'w', encoding="utf-8") as f1:
#         #     f1.write(self.all_taxonmy)
#         # list_geom = list(sorted(self.dict_geom.values()))
#         list_start = list(sorted(self.dict_start.values()))
#         list_stop = list(sorted(self.dict_stop.values()))
#         list_PCGs = list(sorted(self.dict_PCG.values()))
#         list_RNA = list(sorted(self.dict_RNA.values()))
#         list_ATskew = list(sorted(self.dict_gene_ATskews.values()))
#         list_GCskew = list(sorted(self.dict_gene_GCskews.values()))
#         list_ATCont = list(sorted(self.dict_gene_ATCont.values()))
#         list_GCCont = list(sorted(self.dict_gene_GCCont.values()))
#         # with open(statFilePath + os.sep + 'genomeStat.csv', 'w', encoding="utf-8") as f2:
#         #     lineages = ",".join(
#         #         self.included_lineages) + "," if self.included_lineages else ""
#         #     prefix = 'Species,' + lineages + \
#         #              'GeneBank accesion no.,Full length (bp),A (%),T (%),C (%),G (%),A+T (%),G+C (%),AT skew,GC skew\n'
#         #     f2.write(prefix + ''.join(list_geom))
#         with open(statFilePath + os.sep + 'geneStat.csv', 'w', encoding="utf-8") as f3:
#             list_abbre = self.assignAbbre(self.list_name_gb)
#             str_taxonmy, footnote = self.geneStatSlot(list_abbre)
#             headers = 'Species,' + ','.join(list_abbre) + '\n'
#             prefix_PCG = 'Length of PCGs (bp)\n'
#             prefix_rRNA = 'Length of rRNA genes (bp)\n'
#             prefix_ini = 'Putative start codon\n'
#             prefix_ter = 'Putative terminal codon\n'
#             prefix_ATskew = 'AT skew\n'
#             prefix_GCskew = 'GC skew\n'
#             prefix_ATCont = 'AT content\n'
#             prefix_GCCont = 'GC content\n'
#             f3.write(str_taxonmy + headers + prefix_PCG + '\n'.join(list_PCGs) + '\n' +
#                      prefix_rRNA + '\n'.join(list_RNA) + '\n' +
#                      prefix_ini + '\n'.join(list_start) + '\n' +
#                      prefix_ter + '\n'.join(list_stop) + '\n' +
#                      prefix_ATskew + '\n'.join(list_ATskew) + '\n' +
#                      prefix_GCskew + '\n'.join(list_GCskew) + '\n' +
#                      prefix_ATCont + '\n'.join(list_ATCont) + '\n' +
#                      prefix_GCCont + '\n'.join(list_GCCont) + '\n' +
#                      "N/A: Not Available; tRNAs: concatenated tRNA genes; rRNAs: concatenated rRNA genes;"
#                      " +: major strand; -: minus strand\n" + footnote)
#         # skewness
#         with open(CDSpath + os.sep + 'PCGsCodonSkew.csv', 'w', encoding="utf-8") as f4:
#             f4.write(self.PCGsCodonSkew)
#
#         with open(CDSpath + os.sep + 'firstCodonSkew.csv', 'w', encoding="utf-8") as f5:
#             f5.write(self.firstCodonSkew)
#
#         with open(CDSpath + os.sep + 'secondCodonSkew.csv', 'w', encoding="utf-8") as f6:
#             f6.write(self.secondCodonSkew)
#
#         with open(CDSpath + os.sep + 'thirdCodonSkew.csv', 'w', encoding="utf-8") as f7:
#             f7.write(self.thirdCodonSkew)
#
#         with open(CDSpath + os.sep + 'firstSecondCodonSkew.csv', 'w', encoding="utf-8") as f8:
#             f8.write(self.firstSecondCodonSkew)
#
#         # # 生成密码子偏倚统计
#         if self.dict_args["cal_codon_bias"]:
#             with open(CDSpath + os.sep + 'codon_bias.csv', 'w', encoding="utf-8") as f11:
#                 f11.write(self.codon_bias)
#
#         with open(statFilePath + os.sep + 'gbAccNum.csv', 'w', encoding="utf-8") as f8:
#             f8.write(self.name_gb)
#         # # ncr统计
#         # self.ncr_stat_fun()
#         # with open(statFilePath + os.sep + 'ncrStat.csv', 'w', encoding="utf-8") as f9:
#         #     f9.write(self.ncrInfo)
#         allStat = self.fetchAllStatTable()
#         with open(statFilePath + os.sep + 'used_species.csv', 'w', encoding="utf-8") as f4:
#             f4.write(allStat)
#         # 生成画图所需原始数据
#         with open(statFilePath + os.sep + 'data_for_plot.csv', 'w', encoding="utf-8") as f11:
#             f11.write(self.line_spe_stat)
#         # 删除ENC的中间文件
#         try:
#             for file in ["codonW_infile.fas", "codonW_outfile.txt", "codonW_blk.txt"]:
#                 os.remove(self.exportPath + os.sep + file)
#         except: pass
#
#     def fetchAllStatTable(self):
#         allStat = "Taxon,Accession number,Size(bp),AT%,AT-Skew,GC-Skew\n"
#         list_dict_sorted = sorted(list(self.dict_all_stat.keys()))
#         lineage_count = len(self.included_lineages) + 1
#         last_lineage = [1] * lineage_count
#         for i in list_dict_sorted:
#             lineage1 = self.dict_all_stat[i][:lineage_count]
#             content = self.compareLineage(
#                 lineage1, last_lineage, self.dict_all_stat[i][lineage_count:])
#             allStat += content
#             last_lineage = lineage1
#         return allStat
#
#     def assignAbbre(self, abbreList):
#         def abbreName(name, index):
#             return name.split(' ')[0][0] + '_' + name.split(' ')[1][0:index] if " " in name else name[0]
#
#         # 挑选可迭代对象里面相同的项
#         def pickRepeate(list_):
#             count_list_ = Counter(list_)
#             # 挑选出不止出现一次的缩写
#             return [key for key, value in count_list_.items() if value > 1]
#
#         def assgn_abbre(list_repeate):
#             # 种名
#             list_name = []
#             for i in list_repeate:
#                 list_org = i.split(" ")
#                 if len(list_org) <= 1:
#                     list_name.append("name")
#                 else:
#                     list_name.append(list_org[1])
#             list_lenth = [len(l) for l in list_name]
#             minLenth = min(list_lenth)
#             # 如果2个物种属名不同，种名一样，那么就保持false
#             flag = False
#             for j in range(minLenth):
#                 if j > 0:
#                     list_part = [k[0:j + 1] for k in list_name]
#                     if len(set(list_part)) > 1:
#                         flag = j + 1
#                         break
#             return flag
#
#         list_abbre = []
#         dict_list = OrderedDict()
#
#         for num, i in enumerate(abbreList):
#             # 先生成1的abbrevition，以筛选出一部分
#             list_abbre.append(abbreName(i[0], 1))
#             dict_list[num] = i
#         # 挑选有重复的项
#         repeate_keys = pickRepeate(list_abbre)
#         if repeate_keys != []:
#             for j in repeate_keys:
#                 list_repeate = []
#                 list_index = []
#                 for num, k in enumerate(list_abbre):
#                     if j == k:
#                         list_repeate.append(dict_list[num][0])
#                         list_index.append(num)
#                 # 存在3个名字，其中2个拉丁名完全相同  Margarya monodi，Margarya monodi，Margarya
#                 # melanioides
#                 repeateNames = pickRepeate(list_repeate)
#                 # 如果没有完全一样的拉丁名
#                 if repeateNames == []:
#                     # 找出缩写多少位比较合适
#                     flag = assgn_abbre(list_repeate)
#                     if flag:
#                         # 替换缩写
#                         for eachIndex in list_index:
#                             list_abbre[eachIndex] = abbreName(
#                                 dict_list[eachIndex][0], flag)
#                     # 如果2个物种属名不同，种名一样，那么就保持false
#                     else:
#                         for eachIndex in list_index:
#                             list_abbre[eachIndex] += "_" + \
#                                                      dict_list[eachIndex][1]
#                 # 2个或多个物种拉丁名完全相同的情况,附带上gb number
#                 else:
#                     for eachIndex in list_index:
#                         list_abbre[eachIndex] += "_" + dict_list[eachIndex][1]
#
#         return list_abbre
#
#     def geneStatSlot(self, list_abbre):
#         zip_taxonmy = list(zip(
#             *self.list_all_taxonmy))  # [('Gyrodactylidae', 'Capsalidae', 'Ancyrocephalidae', 'Chauhaneidae'), ('Gyrodactylidea', 'Capsalidea', 'Dactylogyridea', 'Mazocraeidea'), ('Monogenea', 'Monogenea', 'Monogenea', 'Monogenea')]
#         lineage = list(reversed(self.included_lineages))
#         header_taxonmy = [[lineage[num]] + list(i) for num, i in enumerate(
#             zip_taxonmy)]  # [['Family', 'Gyrodactylidae', 'Capsalidae', 'Ancyrocephalidae'], ['Superfamily', 'Gyrodactylidea', 'Capsalidea', 'Dactylogyridea'], ['Class', 'Monogenea', 'Monogenea', 'Monogenea']]
#         str_taxonmy = "\n".join([",".join(lineage) for lineage in header_taxonmy]) + "\n"
#         zip_name = list(zip(list_abbre, self.list_name_gb))
#         footnote = "\n".join([each_name[0] + ": " + " ".join(each_name[1]) for each_name in zip_name])
#         return str_taxonmy, footnote
#
#     def numbered_Name(self, name, omit=False):
#         list_names = list(self.dict_repeat_name_num.keys())
#         # 如果这个name已经记录在字典里面了
#         if name in list_names:
#             numbered_name = name + str(self.dict_repeat_name_num[name])
#             self.dict_repeat_name_num[name] += 1
#         else:
#             numbered_name = name + "1" if not omit else name
#             self.dict_repeat_name_num[name] = 2
#         return numbered_name
#

class GBnormalize(object):
    def __init__(self, **dict_args):
        self.dict_args = dict_args
        self.included_features = self.dict_args["Features to be extracted"]
        self.included_features = "All" if self.dict_args["extract_all_features"] else self.included_features
        self.dict_replace = {i[0]: i[1] for i in self.dict_args["Names unification"]}
        self.gbManager = self.dict_args["gbManager"]
        self.list_IDs = self.dict_args["list_IDs"]
        self.progressSig = self.dict_args["progressSig"]
        self.standardize()

    def replace_name(self, old_name):
        return self.dict_replace[old_name] if old_name in self.dict_replace else old_name

    def standardize(self):
        included_features = [i.upper() for i in self.included_features]
        base = 0
        proportion = 100 / len(self.list_IDs)
        for num, ID in enumerate(self.list_IDs):
            recordPath = self.gbManager.fetchRecordPath(ID)
            record = SeqIO.read(recordPath, "genbank")
            features = record.features
            feature_len = len(features)
            for num2, feature in enumerate(features):
                if self.included_features == "All" or (feature.type.upper() in included_features):
                    feature_type = feature.type if self.included_features != "All" else "all"
                    qualifiers = feature.qualifiers
                    included_qualifiers = self.dict_args["Qualifiers to be recognized (%s):" % feature_type]
                    for qualifier in included_qualifiers:
                        if qualifier in qualifiers:
                            old_name = qualifiers[qualifier][0]
                            new_name = self.replace_name(old_name)
                            if old_name != new_name:
                                qualifiers[qualifier][0] = new_name
                num2 += 1
                self.progressSig.emit(base * num + num2 * proportion / feature_len)
            ##保存
            SeqIO.write(record, recordPath, "genbank")

# class GBnormalize_MT(GBnormalize):
#
#     def __init__(self, **dict_args):
#         super(GBnormalize_MT, self).__init__(**dict_args)
#         self.warnings = []
#
#     def judge(self, new_name, values, gb_num, error_inf):
#         haveWarning = False
#         if new_name == 'L' or new_name == 'S':
#             if re.search(
#                     r'(?<=[^1-9a-z_])(CUA|CUN|[tu]ag|L1|trnL1|Leu1)(?=[^1-9a-z_])',
#                     values,
#                     re.I):
#                 new_name = 'L1'
#             elif re.search(r'(?<=[^1-9a-z_])(UUA|UUR|[tu]aa|L2|trnL2|Leu2)(?=[^1-9a-z_])', values, re.I):
#                 new_name = 'L2'
#             elif re.search(r'(?<=[^1-9a-z_])(UCA|UCN|[tu]ga|S2|trnS2|Ser2)(?=[^1-9a-z_])', values, re.I):
#                 new_name = 'S2'
#             elif re.search(r'(?<=[^1-9a-z_])(AGC|AGN|AGY|gc[tu]|[tu]c[tu]|S1|trnS1|Ser1)(?=[^1-9a-z_])', values, re.I):
#                 new_name = 'S1'
#             else:
#                 # complement(14859..14922)
#                 position = values.split('\n')[0].split()[1]
#                 self.list_tRNA_index.append(position)
#                 error_inf += 'Ambiguous annotation about S1, S2, L1 and L2 in %s for %s\n' % (
#                     position, gb_num)
#                 haveWarning = True
#         else:
#             new_name = new_name
#         return new_name, error_inf, haveWarning
#
#     def standardize(self):
#         included_features = [i.upper() for i in self.included_features]
#         base = 0
#         proportion = 100 / len(self.list_IDs)
#         for num, ID in enumerate(self.list_IDs):
#             recordPath = self.gbManager.fetchRecordPath(ID)
#             record = SeqIO.read(recordPath, "genbank")
#             features = record.features
#             feature_len = len(features)
#             for num2, feature in enumerate(features):
#                 if feature.type == "source":
#                     feature.qualifiers["State"] = "%s verified" % ID
#                 elif feature.type.upper() in included_features:
#                     feature_type = feature.type
#                     qualifiers = feature.qualifiers
#                     included_qualifiers = self.dict_args["Qualifiers to be recognized (%s):" % feature_type]
#                     for qualifier in included_qualifiers:
#                         if qualifier in qualifiers:
#                             if feature.type.upper() == "TRNA":
#                                 # values =
#                                 pass
#                             old_name = qualifiers[qualifier][0]
#                             new_name = self.replace_name(old_name)
#                             if old_name != new_name:
#                                 qualifiers[qualifier][0] = new_name
#                 num2 += 1
#                 self.progressSig.emit(base * num + num2 * proportion / feature_len)
#             ##保存
#             SeqIO.write(record, recordPath, "genbank")