#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import glob
import itertools

import datetime
from io import StringIO

from Bio import SeqIO, Entrez, SeqFeature
from Bio.Alphabet import generic_dna

from src.factory import Factory, SeqGrab
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
from Bio.SeqFeature import FeatureLocation

'''item:
[
['source', '1..402', {'organelle': 'mitochondrion', 'host': 'Bathybates minor', 'country': 'Burundi: Lake Tanganyika,Bujumbura', 'db_xref': 'taxon:1844966', 'mol_type': 'genomic DNA', 'organism': 'Cichlidogyrus casuarinus', 'isolate': 'PB3'}],
 ['gene', '<1..>402', {'gene': 'COX1'}],
 ['CDS', '<1..>402', {'gene': 'COX1', 'codon_start': '1', 'transl_table': '9', 'protein_id': 'ANC98956.1', 'translation': 'FFGHPEVYVLILPGFGAVSHICLSISNNQEPFGYLGLVFAMFSIVCLGCVVWAHHMFTVGMDVKSTIFFSSVTMIIGVPTGIKVFSWLYMLASSNISRGDPIVWWVFAFIILFTMGGVTGIVLSSSVLDSLLHD', 'product': 'cytochrome c oxidase subunit I'}]
 ]'''


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
        self.totalID = self.dict_args["totalID"]
        self.progressSignal = self.dict_args["progressSig"]
        gbManager = GbManager(self.dict_args["outpath"])
        fileHandle = StringIO(self.dict_args["gbContents"])
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
                    individual_gb, line, error_inf = self.get_item(
                        individual_gb, fileHandle, line, error_inf, genome_size)
                    individual_gb, line, self.seq = self.get_sequence(
                        individual_gb, fileHandle, line)
                    # 替换掉<和>,不然html会出错
                    individual_gb = re.sub(
                        r"<(?!span|/span)", "&lt;", individual_gb)
                    individual_gb = re.sub(
                        r"(?<=\d)>", "&gt;", individual_gb)
                    sequences += individual_gb
                    gb_path = gbManager.fetchRecordPath(self.ID)
                    # 得到纯文本
                    Dialog = QDialog()
                    textBrowser = QTextBrowser(Dialog)
                    textBrowser.setHtml("<pre>" + individual_gb + "</pre>")
                    plainContent = textBrowser.toPlainText()
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
                        (num / self.totalID) * 100)
                # 保证读到下个物种的gb文件
                while not line.startswith('LOCUS') and line != '':
                    line = fileHandle.readline()
            self.allContent = '''<html>
                                <head>
                                <title>genbankfile</title>
                                <style type=text/css>
                                .error {color: red}
                                .warning {color: blue}
                                </style>
                                </head>
                                
                                <body bgcolor=#f5f5a3>
                                <pre>''' + sequences + '''</pre>
                                </body>
                                </html>'''
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
        try:
            feature, feature_content, line = next(generator_item)
        except StopIteration:
            ##没有注释的情况，直接到Origin了
            self.errors.append(
                [individual_gb, "No features found, better to remove it"])
            ##"LOCUS%s" % (" " * 7 + self.gb_num)
            individual_gb = '<span class="error">' + \
                            individual_gb + '</span>'
            return individual_gb, line, error_inf
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
                        individual_gb += '<span class="error">' + \
                                         feature_content + '</span>'
                        self.errors.append(
                            [feature_content, "No identifiers (%s) for this gene"%", ".join(included_qualifiers)])
                    else:
                        # +=替换了名字的qualifier
                        if haveWarning:
                            ##tRNA模式，并且S和L都没有注释好
                            individual_gb += '<span class="warning">' + feature_content + '</span>'
                            self.warnings.append([feature_content, "Ambiguous annotation of S1/S2 or L1/L2"])
                        else:
                            individual_gb += feature_content
                else:
                    ##feature_type没有包含
                    individual_gb += feature_content
                last_feature = feature
                feature, feature_content, line = next(generator_item)
                if self.MarkNCR:
                    last_ter = self.position(last_feature[1])[1]
                    now_ini = self.position(feature[1])[0]
                    if last_ter and now_ini:
                        # 这里上一个序号要+1才能拿来判断
                        if (int(now_ini) - (int(last_ter) + 1)) >= self.ncrLenth:
                            individual_gb += 'misc_feature'.ljust(16).rjust(21) + str(int(
                                last_ter) + 1) + '..' + str(int(now_ini) - 1) + '\n' + 21 * ' ' + '/gene="NCR"\n'
            except StopIteration:
                if self.MarkNCR:
                    last_ter = self.position(feature[1])[1]  # 判断最后一部分序列是否为NCR
                    now_ini = genome_size
                    if last_ter and now_ini:
                        if (int(now_ini) - int(last_ter)) >= self.ncrLenth:
                            individual_gb += 'misc_feature'.ljust(16).rjust(21) + str(
                                int(last_ter) + 1) + '..' + str(int(now_ini)) + '\n' + 21 * ' ' + '/gene="NCR"\n'
                break
        return individual_gb, line, error_inf

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


class CodonBias(object):
    '''
    未解决的问题是aa_stat_fun里面那个n=1的时候；
    '''

    def __init__(self, seq, codeTable=1, codonW=r"E:\BioSoftware\CodonW\Win32CodonW\Win32\CodonW.exe", path=None):
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
    def __init__(self, order, dict_args):
        self.dict_args = dict_args
        self.order = order
        self.dict_order = OrderedDict()
        self.read_order()
        self.align_order()
        self.number_NCR()
        self.markDomain()

    def read_order(self):
        list_orders = self.order.split("\n")
        list_orders.remove("")  # 删除空项
        flag = False
        for line in list_orders:
            if line.startswith('>'):
                name = line.strip(">")
            else:
                list_order = line.strip().split(" ")
                flag = True
            if flag:
                self.dict_order[name] = list_order

    def align_order(self):
        list_dict_order = list(self.dict_order.keys())
        for i in list_dict_order:
            list_order = self.dict_order[i]
            for num, j in enumerate(list_order):
                if "cox1" in j:
                    self.dict_order[i] = list_order[num:] + list_order[:num]

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

    def addPCGs(self):
        rgxNAD = re.compile(r'NAD4L|NAD[1-6]|ND[1-6]', re.I)
        rgxCOX = re.compile(r'COX[1-3]', re.I)
        rgxCOB = re.compile(r'COB|CYTB', re.I)
        rgxATP = re.compile(r'ATP[68]', re.I)
        #         self.orderName = self.orderName.strip("-")
        haveItem = True
        if rgxNAD.search(self.orderName) and self.dict_args["nadchecked"]:
            self.secondNum = self.endNum + int(self.dict_args["nadlength"])
            self.firstNum = self.endNum if self.endNum == 0 else self.endNum + \
                                                                 self.dict_args["gene interval"]
            self.secondNum = self.secondNum + 5 if "NAD4L" in self.orderName.upper() else self.secondNum
            shape = self.dict_args["nadshape"]
            shape = self.chainShape(shape)
            self.itol_each_domain += ",%s|%.1f|%.1f|%s|%s" % (
                shape, self.firstNum, self.secondNum, self.dict_args["nadcolour"], self.orderName)
        elif rgxCOX.search(self.orderName) and self.dict_args["coxchecked"]:
            self.secondNum = self.endNum + int(self.dict_args["coxlength"])
            self.firstNum = self.endNum if self.endNum == 0 else self.endNum + \
                                                                 self.dict_args["gene interval"]
            shape = self.dict_args["coxshape"]
            shape = self.chainShape(shape)
            self.itol_each_domain += ",%s|%.1f|%.1f|%s|%s" % (
                shape, self.firstNum, self.secondNum, self.dict_args["coxcolour"], self.orderName)
        elif rgxCOB.search(self.orderName) and self.dict_args["cytbchecked"]:
            self.secondNum = self.endNum + int(self.dict_args["cytblength"])
            self.firstNum = self.endNum if self.endNum == 0 else self.endNum + \
                                                                 self.dict_args["gene interval"]
            shape = self.dict_args["cytbshape"]
            shape = self.chainShape(shape)
            self.itol_each_domain += ",%s|%.1f|%.1f|%s|%s" % (
                shape, self.firstNum, self.secondNum, self.dict_args["cytbcolour"], self.orderName)
        elif rgxATP.search(self.orderName) and self.dict_args["atpchecked"]:
            self.secondNum = self.endNum + int(self.dict_args["atplength"])
            self.firstNum = self.endNum if self.endNum == 0 else self.endNum + \
                                                                 self.dict_args["gene interval"]
            shape = self.dict_args["atpshape"]
            shape = self.chainShape(shape)
            self.itol_each_domain += ",%s|%.1f|%.1f|%s|%s" % (
                shape, self.firstNum, self.secondNum, self.dict_args["atpcolour"], self.orderName)
        else:
            '''
            不确定怎么执行
            '''
            haveItem = False
            # self.itol_each_domain += ",RE|%.1f|%.1f|red|%s" % (
            #     self.firstNum, self.secondNum, self.orderName)
        self.endNum = self.secondNum if haveItem else self.endNum

    def addRNAs(self):
        self.secondNum = self.endNum + int(self.dict_args["rRNAlength"])
        self.firstNum = self.endNum + \
                        0 if self.endNum == 0 else self.endNum + self.dict_args["gene interval"]
        shape = self.dict_args["rRNAshape"]
        shape = self.chainShape(shape)
        #         self.orderName = self.orderName.strip("-")
        self.itol_each_domain += ",%s|%.1f|%.1f|%s|%s" % (
            shape, self.firstNum, self.secondNum, self.dict_args["rRNAcolour"], self.orderName)
        self.endNum = self.secondNum

    def addNCRs(self):
        self.secondNum = self.endNum + int(self.dict_args["NCRlength"])
        self.firstNum = self.endNum + \
                        0 if self.endNum == 0 else self.endNum + self.dict_args["gene interval"]
        shape = self.dict_args["NCRshape"]
        shape = self.chainShape(shape)
        #         self.orderName = self.orderName.strip("-")
        self.itol_each_domain += ",%s|%.1f|%.1f|%s|%s" % (
            shape, self.firstNum, self.secondNum, self.dict_args["NCRcolour"], self.orderName)
        self.endNum = self.secondNum

    def addtRNAs(self):
        self.secondNum = self.endNum + int(self.dict_args["tRNAlength"])
        self.firstNum = self.endNum + \
                        0 if self.endNum == 0 else self.endNum + self.dict_args["gene interval"]
        shape = self.dict_args["tRNAshape"]
        shape = self.chainShape(shape)
        #         self.orderName = self.orderName.strip("-")
        self.itol_each_domain += ",%s|%.1f|%.1f|%s|%s" % (
            shape, self.firstNum, self.secondNum, self.dict_args["tRNAcolour"], self.orderName)

        self.endNum = self.secondNum

    def markDomain(self):
        rgxPCGs = re.compile(
            r'COX[1-3]|NAD4L|NAD[1-6]|ND[1-6]|COB|CYTB|ATP[68]', re.I)
        rgxRNA = re.compile(r"rrnS|rrnL", re.I)
        rgxNCR = re.compile(r"NCR", re.I)
        listtRNAs = [
            "T",
            "C",
            "E",
            "Y",
            "L",
            "S",
            "R",
            "G",
            "H",
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
            "S1",
            "S2",
            "L1",
            "L2"]
        self.itol_domain = ""
        list_dict_order = list(self.dict_order.keys())
        for i in list_dict_order:
            self.itol_each_domain = ""
            list_order = self.dict_order[i]
            self.endNum = 0
            for self.orderName in list_order:
                self.orderName = self.orderName.split("_copy")[0] #预防有copy的基因
                pcgFlag = [self.dict_args[i + "checked"]
                           for i in ["atp", "nad", "cytb", "cox"]]
                if rgxPCGs.search(self.orderName) and (True in pcgFlag):
                    self.addPCGs()
                elif rgxRNA.search(self.orderName) and self.dict_args["rRNAchecked"]:
                    self.addRNAs()
                elif rgxNCR.search(self.orderName) and self.dict_args["NCRchecked"]:
                    self.addNCRs()
                # 增加判断了负链的基因
                elif ((self.orderName.strip("-") in listtRNAs) or ("tRNA" in self.orderName)) and self.dict_args[
                    "tRNAchecked"]:
                    self.addtRNAs()
            self.itol_domain += i + "," + \
                                str(self.endNum) + self.itol_each_domain + "\n"


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
                organism = gb_record.annotations["organism"]
                if findLineage:
                    ## 自动从NCBI识别分类群
                    requiredLineageNames = self.factory.getCurrentTaxSetData()[0]
                    if database == "NCBI":
                        self.update_NCBI_lineages(requiredLineageNames, organism, source_feature)
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
                    # errorInfo = ''.join(
                    #     traceback.format_exception(*sys.exc_info())) + "\n"
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

    def update_NCBI_lineages(self, LineageNames, query_name, source_feature):
        tax_id = self.get_tax_id(query_name)
        if tax_id: #有时候有些名字不能被识别，就是None
            data = self.get_tax_data(tax_id)
            LineageNames = [i.upper() for i in LineageNames]
            source_qualifiers = list(source_feature.qualifiers.keys())
            for d in data[0]['LineageEx']:
                if d['Rank'].upper() in LineageNames:
                    key = self.get_key_in_source(d['Rank'].upper(), source_qualifiers)
                    if key:
                        source_feature.qualifiers[key] = d['ScientificName']
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
        # self.fetchTerCodon()
        if self.extract_list_gene:
            ##只提取指定基因
            self.all_list_gene = list(set(self.dict_replace.keys()).union(set(self.dict_replace.values())))
        # 信号
        self.progressSig = self.dict_args["progressSig"]
        self.totleID = self.dict_args["totleID"]
        ###初始化各个属性###
        self.absence = '="ID",Organism,Feature,Strand,Start,Stop\n'
        #只提取指定基因模式，把未提取的基因列出来
        self.unextract_name = "This is the list of names not included in the 'Names unification' table\n=\"ID\",Organism,Feature,Name,Strand,Start,Stop\n"
        self.species_info = '="ID",Organism,{},Full length (bp),A (%),T (%),C (%),G (%),A+T (%),G+C (%),AT skew,GC skew\n'.format(
            ",".join(self.included_lineages))
        self.taxonomy_infos = 'Tree name,ID,Organism,{}\n'.format(
            ",".join(self.included_lineages))
        self.Error_ID = ""
        self.dict_feature_fas = OrderedDict()  # 存放feature及其所有序列
        self.dict_name_replace = OrderedDict()  # 存放名字及其替换后的名字
        self.dict_itol_name = OrderedDict()
        self.dict_itol_gb = OrderedDict()
        self.dict_all_stat = OrderedDict()
        ####itol###
        #         基因组长度条形图
        self.itolLength = "DATASET_SIMPLEBAR\nSEPARATOR COMMA\nDATASET_LABEL,genome length bar\nCOLOR,#ffff00\nWIDTH,1000\nMARGIN,0\nHEIGHT_FACTOR,0.7\nBAR_SHIFT,0\nBAR_ZERO,12000\nDATA\n"
        #         基因组AT含量条形图
        self.itolAT = "DATASET_SIMPLEBAR\nSEPARATOR COMMA\nDATASET_LABEL,AT content bar\nCOLOR,#ffff00\nWIDTH,1000\nMARGIN,0\nHEIGHT_FACTOR,0.7\nBAR_SHIFT,0\nBAR_ZERO,50\nDATA\n"
        #         基因组GC skew条形图
        self.itolGCskew = "DATASET_SIMPLEBAR\nSEPARATOR COMMA\nDATASET_LABEL,GC skew bar\nCOLOR,#ffff00\nWIDTH,1000\nMARGIN,0\nHEIGHT_FACTOR,0.7\nBAR_SHIFT,0\nBAR_ZERO,0\nDATA\n"
        #         基因组ATCG数量堆积图
        self.itolLength_stack = "DATASET_MULTIBAR\nSEPARATOR COMMA\nDATASET_LABEL,ATCG multi bar chart\nCOLOR,#ff0000\nWIDTH,1000\nMARGIN,0\nSHOW_INTERNAL,0\nHEIGHT_FACTOR,0.7\nBAR_SHIFT,0\nALIGN_FIELDS,0\nFIELD_LABELS,A,T,C,G\nFIELD_COLORS,#2a9087,#5c2936,#913e40,#2366a1\nDATA\n"
        self.colours = []
        # 存itol的各种文件
        self.dict_itol_info = OrderedDict()
        for lineage in self.included_lineages:
            for num, item in enumerate(
                    ["Colour", "Text", "ColourStrip", "ColourRange", "colourUsed1", "colourUsed2"]):
                if num == 0:
                    self.dict_itol_info["itol_%s_%s" % (
                        lineage, item)] = "TREE_COLORS\nSEPARATOR COMMA\nDATA\n"
                elif num == 1:
                    self.dict_itol_info["itol_%s_%s" % (
                        lineage,
                        item)] = "DATASET_TEXT\nSEPARATOR COMMA\nDATASET_LABEL,%s text\nCOLOR,#ff0000\nMARGIN,0\nSHOW_INTERNAL,0\nLABEL_ROTATION,0\nALIGN_TO_TREE,0\nSIZE_FACTOR,1\nDATA\n" % lineage
                elif num == 2:
                    self.dict_itol_info["itol_%s_%s" % (
                        lineage,
                        item)] = "DATASET_COLORSTRIP\nSEPARATOR SPACE\nDATASET_LABEL color_strip\nCOLOR #ff0000\nCOLOR_BRANCHES 1\nSTRIP_WIDTH 25\nDATA\n"
                elif num == 3:
                    self.dict_itol_info["itol_%s_%s" % (
                        lineage, item)] = "TREE_COLORS\nSEPARATOR COMMA\nDATA\n"
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
        ##用于统计非编码区和重叠区
        self.dict_NCR_regions = OrderedDict()
        self.dict_overlapping_regions = OrderedDict()

    def _exec(self):
        ####执行###
        try:
            self.init_args_all()
            self.progressSig.emit(5) #5
            if self.dict_args["extract_entire_seq"]:
                self.entire_sequences = ""
                self.extract_entire_seq() #90
                with open(self.exportPath + os.sep + self.dict_args["entire_seq_name"] + ".fas", "w", encoding="utf-8") as f:
                    f.write(self.entire_sequences)
                self.saveStatFile()
            else:
                self.extract() #70
                self.gene_sort_save() #20
                self.saveGeneralFile()
                self.saveStatFile()
            if self.dict_args["if itol"]:
                self.saveItolFiles()  # 存itol的文件
            else:
                self.progressSig.emit(100)
        except:
            print(''.join(
                traceback.format_exception(
                    *sys.exc_info())))

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

    def fetchGeneName(self):
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
            self.absence += ",".join([self.ID, self.organism, self.feature_type,
                                      self.strand, str(self.start), str(self.end)]) + "\n"
            return
        if self.extract_list_gene:
            ###只提取指定基因的模式，不符合就返回
            if not old_name in self.all_list_gene:
                self.unextract_name += ",".join([self.ID, self.organism, self.feature_type, old_name,
                                      self.strand, str(self.start), str(self.end)]) + "\n"
                return
        ##重复基因的名字加编号
        new_name, self.dict_type_genes[self.feature_type] = self.factory.numbered_Name(self.dict_type_genes.setdefault(self.feature_type, []),
                                                                       self.replace_name(old_name), omit=True)
        if old_name not in self.dict_name_replace:
            self.dict_name_replace[old_name] = new_name
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
                self.dict_itol_info["itol_%s_Text" % class_] += "%s,%s,-1,%s,bold,2,0\n" % (
                    self.usedName, lineage, colour1)
                # range的颜色
                colour2 = self.colourPicker(class_, Range=True)
                self.dict_itol_info["itol_%s_colourUsed2" %
                                    class_][lineage] = colour2
            for num, item in enumerate(
                    ["Colour", "ColourStrip", "ColourRange"]):
                if num == 0:
                    self.dict_itol_info["itol_%s_%s" % (class_, item)] += "%s,label,%s,normal,1\n" % (
                        self.usedName, self.dict_itol_info["itol_%s_colourUsed1" % class_][lineage])
                elif num == 1:
                    self.dict_itol_info["itol_%s_%s" % (class_, item)] += "%s %s %s\n" % (
                        self.usedName, self.dict_itol_info["itol_%s_colourUsed1" % class_][lineage], lineage)
                elif num == 2:
                    self.dict_itol_info["itol_%s_%s" % (class_, item)] += "%s,range,%s,%s\n" % (
                        self.usedName, self.dict_itol_info["itol_%s_colourUsed2" % class_][lineage], lineage)

    def replace_name(self, old_name):
        return self.dict_replace[old_name] if old_name in self.dict_replace else old_name

    def parseSource(self):
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
            self.itolAT += self.usedName + "," + seqStat.AT_percent + "\n"
            self.itolGCskew += self.usedName + "," + seqStat.GC_skew + "\n"
            self.itolLength += self.usedName + "," + seqStat.size + "\n"
            A, T, C, G = str(
                self.str_seq.upper().count('A')), str(
                self.str_seq.upper().count('T')), str(
                self.str_seq.upper().count('C')), str(
                self.str_seq.upper().count('G'))
            self.itolLength_stack += ",".join([self.usedName, A, T, C, G]) + "\n"
            # 标记颜色
            self.colourTree()

    def parseFeature(self):
        new_name = self.fetchGeneName()
        if not new_name:
            return
        feature_name = "CDS_NUC" if self.feature_type.upper() == "CDS" else self.feature_type
        self.dict_feature_fas.setdefault(feature_name, OrderedDict())[new_name + '>' + self.organism + '_' +
                                                 self.name] = '>' + self.usedName + '\n' + str(
            self.feature.extract(self.seq)) + '\n'
        self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
        if "translation" in self.qualifiers:
            aa_seq = self.qualifiers["translation"][0]
            self.dict_feature_fas.setdefault("CDS_AA", OrderedDict())[new_name + '>' + self.organism + '_' +
                                                 self.name] = '>' + self.usedName + '\n' + aa_seq + '\n'
        ##间隔区提取
        self.refresh_pairwise_feature(new_name)

    def gb_record_stat(self):
        ###used_species###
        seqStat = SeqGrab(self.str_seq)
        list_spe_stat = self.list_lineages + [
            self.organism,
            self.ID,
            seqStat.size,
            seqStat.AT_percent,
            seqStat.AT_skew,
            seqStat.GC_skew]
        self.dict_all_stat["_".join(
            self.list_lineages + [self.organism + "_" + self.ID])] = list_spe_stat
        ###species_info###
        # ID",Organism,%s,Full length (bp),A (%),T (%),C (%),G (%),A+T (%),G+C (%),AT skew,GC skew
        list_species_info = [self.ID, self.organism] + self.list_lineages + \
                            [str(len(self.str_seq)), seqStat.A_percent, seqStat.T_percent,
                             seqStat.C_percent, seqStat.G_percent, seqStat.AT_percent,
                             seqStat.GC_percent, seqStat.AT_skew, seqStat.GC_skew]
        self.species_info += ",".join(list_species_info) + "\n"
        self.taxonomy_infos += ",".join([self.usedName, self.ID, self.organism] + self.list_lineages) + "\n"

    def extract_entire_seq(self):
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
                for self.feature in features:
                    self.qualifiers = self.feature.qualifiers
                    # self.start = int(self.feature.location.start) + 1
                    # self.end = int(self.feature.location.end)
                    # self.strand = "+" if self.feature.location.strand == 1 else "-"
                    if self.feature.type == "source":
                        self.parseSource()
                self.entire_sequences += ">%s\n%s\n" % (self.usedName, self.str_seq)
                self.gb_record_stat()
                self.input_file.write(gb_record.format("genbank"))
            except:
                self.Error_ID += self.name + ":\n" + \
                                 ''.join(
                                     traceback.format_exception(*sys.exc_info())) + "\n"
            num += 1
            self.progressSig.emit(num * 90 / self.totleID)
        self.input_file.close()

    def extract(self):
        # gb_records = SeqIO.parse(self.gbContentIO, "genbank")
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
                self.description = gb_record.description
                self.date = annotations["date"]
                self.ID = gb_record.id
                self.seq = gb_record.seq
                self.str_seq = str(self.seq)
                self.dict_type_genes = OrderedDict()
                ok = self.check_records(features)
                if not ok: continue
                has_feature = False
                has_source = False
                for self.feature in features:
                    self.qualifiers = self.feature.qualifiers
                    self.start = int(self.feature.location.start) + 1
                    self.end = int(self.feature.location.end)
                    self.strand = "+" if self.feature.location.strand == 1 else "-"
                    self.feature_type = self.feature.type
                    if self.feature_type not in (self.list_features + ["source"]):
                        self.list_features.append(self.feature_type)
                    if self.feature_type == "source":
                        self.parseSource()
                        has_source = True
                    elif self.included_features == "All" or (self.feature_type.upper() in included_features):
                        self.parseFeature()
                        self.getNCR()
                        has_feature = True
                self.getNCR(mode="end") ##判断最后的间隔区
                if not has_feature:
                    ##ID里面没有找到任何对应的feature的情况
                    name = self.usedName if has_source else self.ID
                    self.list_none_feature_IDs.append(name)
                self.gb_record_stat()
                self.input_file.write(gb_record.format("genbank"))
            except:
                self.Error_ID += self.name + ":\n" + \
                                 ''.join(
                                     traceback.format_exception(*sys.exc_info())) + "\n"
            num += 1
            self.progressSig.emit(num * 70 / self.totleID)
        self.input_file.close()

    def save2file(self, content, name, featurePath):
        name = self.factory.refineName(name, remain_words=".-", limit=(254-len(featurePath)))  # 替换名字里面的不识别符号
        with open(os.path.normpath(featurePath) + os.sep + name + '.fas', 'w', encoding="utf-8") as f:
            f.write(content)

    def save_each_feature(self, dict_gene_fas, featurePath, base, proportion):
        list_gene_fas = sorted(list(dict_gene_fas.keys()))
        previous = ''
        gene_seq = ''
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
                    gene_seq += dict_gene_fas[i]
                    previous = gene
                if gene != previous:
                    self.save2file(gene_seq, previous, featurePath)
                    gene_seq = ''
                    gene_seq += dict_gene_fas[i]
                    previous = re.match('^[^>]+', i).group()
            except StopIteration:
                self.save2file(gene_seq, gene, featurePath)
                num += 1
                self.progressSig.emit(base + num * proportion / total)
                break
        num += 1
        self.progressSig.emit(base + num * proportion / total)
        return base + proportion

    def gene_sort_save(self):
        # open(r"C:\Users\Administrator\Desktop\dict.txt", "w").write(str(self.dict_feature_fas))
        total = len(self.dict_feature_fas)
        if not total:
            return
        base = 75
        proportion = 20 / total
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
        itol_labels = 'LABELS\nSEPARATOR COMMA\nDATA\n'
        itol_ori_labels = itol_labels
        itol_gb_labels = itol_labels
        for i in list_name:
            itol_labels += i + ',' + self.dict_itol_name[i] + '\n'
            itol_ori_labels += i + "," + i + "\n"
            itol_gb_labels += i + ',' + self.dict_itol_gb[i] + '\n'
        with open(itolPath + os.sep + 'itol_labels.txt', 'w', encoding="utf-8") as f:
            f.write(itol_labels)
        with open(itolPath + os.sep + 'itol_ori_labels.txt', 'w', encoding="utf-8") as f:
            f.write(itol_ori_labels)
        with open(itolPath + os.sep + 'itol_gb_labels.txt', 'w', encoding="utf-8") as f:
            f.write(itol_gb_labels)
        with open(itolPath + os.sep + 'itolAT.txt', 'w', encoding="utf-8") as f2:
            f2.write(self.itolAT)
        with open(itolPath + os.sep + 'itolGCskew.txt', 'w', encoding="utf-8") as f2:
            f2.write(self.itolGCskew)
        with open(itolPath + os.sep + 'itolLength.txt', 'w', encoding="utf-8") as f3:
            f3.write(self.itolLength)
        with open(itolPath + os.sep + 'itolLength_stack.txt', 'w', encoding="utf-8") as f4:
            f4.write(self.itolLength_stack)
        # colour
        for lineage in self.included_lineages:
            for num, item in enumerate(
                    ["Colour", "Text", "ColourStrip", "ColourRange"]):
                name = "itol_%s_%s" % (lineage, item)
                with open(itolPath + os.sep + '%s.txt' % name, 'w', encoding="utf-8") as f5:
                    f5.write(self.dict_itol_info[name])
        self.progressSig.emit(100)

    # def saveGeneralFile(self):
    #     if self.absence != '="ID",Organism,Feature,Strand,Start,Stop\n':
    #         gfilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'files')
    #         with open(gfilePath + os.sep + 'feature_unrecognized.csv', 'w', encoding="utf-8") as f4:
    #             f4.write(self.absence)
    #     if self.unextract_name != "This is the list of names not included in the 'Names unification' table\n=\"ID\",Organism,Feature,Name,Strand,Start,Stop\n":
    #         gfilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'files')
    #         with open(gfilePath + os.sep + 'name_not_included.csv', 'w', encoding="utf-8") as f4:
    #             f4.write(self.unextract_name)

    def saveStatFile(self):
        # self.factory.creat_dirs(self.exportPath + os.sep + 'rRNA')
        # self.factory.creat_dirs(self.exportPath + os.sep + 'tRNA')
        statFilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'StatFiles')
        # allStat = self.fetchAllStatTable()
        # with open(statFilePath + os.sep + 'used_species.csv', 'w', encoding="utf-8") as f4:
        #     f4.write(allStat)
        with open(statFilePath + os.sep + 'species_info.csv', 'w', encoding="utf-8") as f4:
            if (self.dict_args["seq type"] == "Mitogenome") and (not self.dict_args["extract_entire_seq"]):
                f4.write(self.species_info + "+: major strand; -: minus strand\n")
            else:
                f4.write(self.species_info)
        with open(statFilePath + os.sep + 'taxonomy.csv', 'w', encoding="utf-8") as f5:
            f5.write(self.taxonomy_infos)
        if self.dict_args["extract_entire_seq"]:
            return
        ##名字及其替换后的名字
        name_replace = "Old Name,New Name\n" + "\n".join(
            [",".join([i, self.dict_name_replace[i]]) for i in self.dict_name_replace])
        with open(statFilePath + os.sep + 'name_for_unification.csv', 'w', encoding="utf-8") as f4:
            f4.write(name_replace)
        # if self.absence != '="ID",Organism,Feature,Strand,Start,Stop\n':
        #     # gfilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'files')
        #     with open(statFilePath + os.sep + 'feature_unrecognized.csv', 'w', encoding="utf-8") as f4:
        #         f4.write(self.absence)
        if self.unextract_name != "This is the list of names not included in the 'Names unification' table\n" \
                                  "=\"ID\",Organism,Feature,Name,Strand,Start,Stop\n":
            # gfilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'files')
            with open(statFilePath + os.sep + 'name_not_included.csv', 'w', encoding="utf-8") as f4:
                f4.write(self.unextract_name)
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

    def saveGeneralFile(self):
        # overview表
        overview = "Extraction overview:\n\nVisit here to see how to customize the extraction: " \
                   "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/customize_extraction/\n\n"
        ## species in total
        overview += "%d species in total\n\n" % self.totleID
        list_ = []
        for k in self.dict_qualifiers:
            try:
                feature = re.search(r"\((.+)\)", k).group(1)
                list_.append("%s (%s)"%(feature, " & ".join(self.dict_qualifiers[k])))
            except:
                pass
        included_features = self.included_features if self.included_features != "All" else ["All"]
        overview += "Data type setting used to extract: %s\n  included features: %s\n" \
                    "  qualifiers of each feature: %s\n\n" % (self.dict_args["seq type"],
                                                     " & ".join(included_features), " | ".join(list_))
        overview += "Features found in sequences: %s\n\n" % " & ".join(self.list_features)
        # overview += "Features set to extract: %s\n\n" % ", ".join(self.included_features)
        ###
        if self.absence != '="ID",Organism,Feature,Strand,Start,Stop\n':
            overview += "Qualifiers set in the settings were not found in these features:\n %s\n" % self.absence.replace('="ID"', "ID")
        ###
        if self.list_none_feature_IDs:
            overview += "Features (%s) set in the settings were not found in these species: %s\n\n" %(" & ".join(included_features), " & ".join(
                self.list_none_feature_IDs))
        if self.source_feature_IDs:
            overview += "No features could be found in these IDs: %s\n\n" % " | ".join(self.source_feature_IDs)
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
        name_genes = ",".join(["Species"] + sorted_keys) + "\n"
        for i in self.list_used_names:
            list_states = []
            for j in sorted_keys:
                if i in self.dict_gene_names[j]:
                    list_states.append("yes")
                else:
                    list_states.append("no")
            name_genes += ",".join([i] + list_states) + "\n"
        overview += "Genes found in species:\n %s\n\n" % name_genes
        with open(self.exportPath + os.sep + 'overview.csv', 'w', encoding="utf-8") as f4:
            f4.write(overview)

    def compareLineage(self, lineage1, lineage2, list_stat):
        string = ""
        for num, i in enumerate(lineage1):
            if i != lineage2[num]:  # 出现不一致的分类阶元
                string += num * "    " + i + "\n"
        if lineage1[-1] == lineage2[-1]:  # 同一个物种，不同登录号
            string += num * "    " + i + "\n"
        string = string.strip("\n") + "," + ",".join(list_stat) + "\n"
        return string

    def fetchAllStatTable(self):
        allStat = "Taxon,Accession number,Size(bp),AT%,AT-Skew,GC-Skew\n"
        list_dict_sorted = sorted(list(self.dict_all_stat.keys()))
        lineage_count = len(self.included_lineages) + 1
        last_lineage = [1] * lineage_count
        for i in list_dict_sorted:
            lineage1 = self.dict_all_stat[i][:lineage_count]
            content = self.compareLineage(
                lineage1, last_lineage, self.dict_all_stat[i][lineage_count:])
            allStat += content
            last_lineage = lineage1
        return allStat

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


class GBextract_MT(GBextract, object):
    def __init__(self, **dict_args):
        super(GBextract_MT, self).__init__(**dict_args)

    def init_args_all(self):
        super(GBextract_MT, self).init_args_all()
        self.dict_pro = {}
        self.dict_AA = OrderedDict()
        self.dict_rRNA = {}
        self.dict_tRNA = {}
        self.dict_name = {}
        self.dict_gb = {}
        self.dict_start = {}
        self.dict_stop = {}
        self.dict_PCG = {}
        self.dict_RNA = {}
        # self.dict_geom = {}
        self.dict_spe_stat = {}
        self.list_name_gb = []
        self.linear_order = ''
        self.complete_seq = ''
        self.list_PCGs = [
            'cox1',
            'cox2',
            'nad6',
            'nad5',
            'cox3',
            'cytb',
            'nad4L',
            'nad4',
            'atp6',
            'nad2',
            'nad1',
            'nad3',
            'atp8',
            'rrnS',
            'rrnL']
        self.dict_unify_mtname = {
            'COX1': 'cox1',
            'COX2': 'cox2',
            'NAD6': 'nad6',
            'NAD5': 'nad5',
            'COX3': 'cox3',
            'CYTB': 'cytb',
            'NAD4L': 'nad4L',
            'NAD4': 'nad4',
            'ATP6': 'atp6',
            'NAD2': 'nad2',
            'NAD1': 'nad1',
            'NAD3': 'nad3',
            'ATP8': 'atp8',
            'RRNS': 'rrnS',
            'RRNL': 'rrnL'
        }
        self.dict_geom_seq = {}
        self.name_gb = "Species name,Accession number\n"  # 名字和gb num对照表
        # 有物种没有解析成功，保存在这里
        # self.dict_igs = OrderedDict()  # 存放基因间隔区的序列
        # self.ncr_stat = OrderedDict()
        # 保存没有注释好的L和S
        self.leu_ser = ""
        #         skewness
        self.PCGsCodonSkew = "species,Strand,AT skew,GC skew," + \
                             ",".join(self.included_lineages) + "\n"
        self.firstCodonSkew = "species,Strand,AT skew,GC skew," + \
                              ",".join(self.included_lineages) + "\n"
        self.secondCodonSkew = "species,Strand,AT skew,GC skew," + \
                               ",".join(self.included_lineages) + "\n"
        self.thirdCodonSkew = "species,Strand,AT skew,GC skew," + \
                              ",".join(self.included_lineages) + "\n"
        #         统计图
        self.dict_all_stat = OrderedDict()
        #         PCG的串联序列
        self.PCG_seq = ""
        self.tRNA_seqs = ""
        self.rRNA_seqs = ""
        #         新增统计物种组成表功能
        self.dict_orgTable = OrderedDict()
        # 新增RSCU相关
        self.dict_RSCU = OrderedDict()  # RSCU table
        self.dict_RSCU_stack = OrderedDict()
        self.dict_AAusage = OrderedDict()
        self.dict_all_spe_RSCU = OrderedDict()
        self.dict_all_spe_RSCU["title"] = "codon,"
        self.dict_all_codon_COUNT = OrderedDict()
        self.dict_all_codon_COUNT["title"] = "codon,"
        self.dict_all_AA_RATIO = OrderedDict()
        self.dict_all_AA_RATIO["title"] = "AA,"
        self.dict_all_AA_COUNT = OrderedDict()
        self.dict_all_AA_COUNT["title"] = "AA,"
        self.dict_AA_stack = OrderedDict()
        self.dict_AA_stack["title"] = "species,aa,ratio"
        self.species_info = '="ID",Organism,{},Full length (bp),A (%) (+),T (%) (+),C (%) (+),G (%) (+),A+T (%) (+),' \
                            'G+C (%) (+),AT skew (+),GC skew (+),AT skew (-),GC skew (-)\n'.format(
                            ",".join(self.included_lineages))
        # 新增折线图的绘制
        self.line_spe_stat = "Regions,Strand,Size (bp),T(U),C,A,G,AT(%),GC(%),GT(%),AT skewness,GC skewness,Species," + ",".join(
            list(reversed(self.included_lineages))) + "\n"
        # 密码子偏倚分析
        self.codon_bias = "Genes,GC1,GC2,GC12,GC3,CAI,CBI,Fop,ENC,L_sym,L_aa,Gravy,Aromo,Species," + ",".join(
            list(reversed(self.included_lineages))) + "\n"
        # self.all_taxonmy = "Species," + \
        #                    ",".join(list(reversed(self.included_lineages))) + "\n"
        self.list_all_taxonmy = []  # [[genus1, family1], [genus2, family2]]
        # {NC_029245:Hymenolepis nana}
        self.dict_gb_latin = OrderedDict()
        self.dict_gene_ATskews = {}
        self.dict_gene_GCskews = {}
        self.dict_gene_ATCont = {}
        self.dict_gene_GCCont = {}

    def init_args_each(self):
        # self.PCGs = ''
        self.PCGs_strim = '' #去除不标准的终止密码子的
        self.PCGs_strim_plus = ""
        self.PCGs_strim_minus = ""
        self.tRNAs = ''
        self.tRNAs_plus = ""
        self.tRNAs_minus = ""
        self.rRNAs = ""
        self.rRNAs_plus = ""
        self.rRNAs_minus = ""
        self.dict_genes = {}
        self.dict_geom_seq[self.ID] = self.str_seq
        self.list_name_gb.append((self.organism, self.ID))
        self.name_gb += self.organism + "," + self.ID + "\n"
        # self.igs = ""
        # self.NCR = ''
        # 刷新这个table
        self.orgTable = '''Gene,Position,,Size,Intergenic nucleotides,Codon,,\n,From,To,,,Start,Stop,Strand,Sequence\n'''
        self.lastEndIndex = 0
        self.overlap, self.gap = 0, 0
        self.dict_repeat_name_num = OrderedDict()

    def parseSource(self):
        super(GBextract_MT, self).parseSource()
        list_taxonmy = list(reversed(self.list_lineages))
        self.list_all_taxonmy.append(list_taxonmy)
        self.taxonmy = ",".join(
            [self.organism] + list_taxonmy)
        # self.all_taxonmy += self.taxonmy + "\n"
        self.gene_order = '>' + self.usedName + '\n'
        self.complete_seq += '>' + self.usedName + '\n' + self.str_seq + '\n'

    def parseFeature(self):
        new_name = self.fetchGeneName()
        if not new_name:
            return
        seq = str(self.feature.extract(self.seq))
        feature_name = "CDS_NUC" if self.feature_type.upper() == "CDS" else self.feature_type
        self.dict_feature_fas.setdefault(feature_name, OrderedDict())[new_name + '>' + self.organism + '_' +
                                                 self.name] = '>' + self.usedName + '\n' + seq + '\n'
        self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
        if "translation" in self.qualifiers:
            aa_seq = self.qualifiers["translation"][0]
            self.dict_feature_fas.setdefault("CDS_AA", OrderedDict())[new_name + '>' + self.organism + '_' +
                                                 self.name] = '>' + self.usedName + '\n' + aa_seq + '\n'
        self.fun_orgTable(new_name, len(seq), "", "", seq)
        if new_name.upper().startswith("NCR") and self.dict_args["NCRchecked"]:
            self.gene_order += self.omit_strand + 'NCR '
        ##间隔区提取
        self.refresh_pairwise_feature(new_name)

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
        self.PCGsCodonSkew += ",".join([self.organism,
                                        strand,
                                        seqStat.AT_skew,
                                        seqStat.GC_skew] + self.list_lineages) + "\n"
        first, second, third = seqStat.splitCodon()
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

        self.firstCodonSkew += ",".join([self.organism,
                                         strand,
                                         seqStat.AT_skew,
                                         seqStat.GC_skew] + self.list_lineages) + "\n"

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

        self.secondCodonSkew += ",".join([self.organism,
                                          strand,
                                          seqStat.AT_skew,
                                          seqStat.GC_skew] + self.list_lineages) + "\n"

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

        self.thirdCodonSkew += ",".join([self.organism,
                                         strand,
                                         seqStat.AT_skew,
                                         seqStat.GC_skew] + self.list_lineages) + "\n"
        return [PCGs_stat, first_stat, second_stat, third_stat]

    def geneStat_sub(self, name, seqStat):
        if seqStat == "N/A":
            if name in self.dict_gene_ATskews:
                self.dict_gene_ATskews[name] += ",N/A"
                self.dict_gene_ATCont[name] += ",N/A"
                self.dict_gene_GCskews[name] += ",N/A"
                self.dict_gene_GCCont[name] += ",N/A"
            else:
                self.dict_gene_ATskews[name] = name + ",N/A"
                self.dict_gene_ATCont[name] = name + ",N/A"
                self.dict_gene_GCskews[name] = name + ",N/A"
                self.dict_gene_GCCont[name] = name + ",N/A"
        else:
            if name in self.dict_gene_ATskews:
                self.dict_gene_ATskews[name] += "," + seqStat.AT_skew
                self.dict_gene_ATCont[name] += "," + seqStat.AT_percent
                self.dict_gene_GCskews[name] += "," + seqStat.GC_skew
                self.dict_gene_GCCont[name] += "," + seqStat.GC_percent
            else:
                self.dict_gene_ATskews[name] = name + "," + seqStat.AT_skew
                self.dict_gene_ATCont[name] = name + "," + seqStat.AT_percent
                self.dict_gene_GCskews[name] = name + "," + seqStat.GC_skew
                self.dict_gene_GCCont[name] = name + "," + seqStat.GC_percent

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

    def gb_record_stat(self):
        # 统计单个物种
        list_genes = [
            value for (key, value) in sorted(self.dict_genes.items())]
        #         whole genome
        seq = self.str_seq.upper()
        seqStat = SeqGrab(seq)
        geom_stat = ",".join(['Full genome',
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
        # ID",Organism,%s,Full length (bp),A (%),T (%),C (%),G (%),A+T (%),G+C (%),AT skew,GC skew
        rvscmp_seq = self.rvscmp_seq.upper()
        seqStat_rvscmp = SeqGrab(rvscmp_seq)
        list_species_info = [self.ID, self.organism] + self.list_lineages + \
                            [str(len(self.str_seq)), seqStat.A_percent, seqStat.T_percent,
                             seqStat.C_percent, seqStat.G_percent, seqStat.AT_percent,
                             seqStat.GC_percent, seqStat.AT_skew, seqStat.GC_skew,
                             seqStat_rvscmp.AT_skew, seqStat_rvscmp.GC_skew]
                             # seqStat_rvscmp.A_percent, seqStat_rvscmp.T_percent,
                             # seqStat_rvscmp.C_percent, seqStat_rvscmp.G_percent, seqStat_rvscmp.AT_percent,
                             # seqStat_rvscmp.GC_percent, seqStat_rvscmp.AT_skew, seqStat_rvscmp.GC_skew]
        self.species_info += ",".join(list_species_info) + "\n"
        self.taxonomy_infos += ",".join([self.usedName, self.ID, self.organism] + self.list_lineages) + "\n"

        #         PCG
        PCGs_stat_plus, first_stat_plus, second_stat_plus, third_stat_plus = self.stat_PCG_sub(self.PCGs_strim_plus, "+") \
                                                                 if self.PCGs_strim_plus else ["", "", "", ""]
        PCGs_stat_minus, first_stat_minus, second_stat_minus, third_stat_minus = self.stat_PCG_sub(self.PCGs_strim_minus, "-") \
                                                                    if self.PCGs_strim_minus else ["", "", "", ""]
        #         rRNA
        rRNA_stat_plus = self.stat_other_sub(self.rRNAs_plus, "+", "rRNAs") if self.rRNAs_plus else ""
        if not self.rRNAs_plus: self.geneStat_sub("rRNAs(+)", "N/A") ##要补个NA
        rRNA_stat_minus = self.stat_other_sub(self.rRNAs_minus, "-", "rRNAs") if self.rRNAs_minus else ""
        if not self.rRNAs_minus: self.geneStat_sub("rRNAs(-)", "N/A")  ##要补个NA
        #         tRNA
        tRNA_stat_plus = self.stat_other_sub(self.tRNAs_plus, "+", "tRNAs") if self.tRNAs_plus else ""
        if not self.tRNAs_plus: self.geneStat_sub("tRNAs(+)", "N/A")  ##要补个NA
        tRNA_stat_minus = self.stat_other_sub(self.tRNAs_minus, "-", "tRNAs") if self.tRNAs_minus else ""
        if not self.tRNAs_minus: self.geneStat_sub("tRNAs(-)", "N/A")  ##要补个NA
        stat = 'Regions,Strand,Size (bp),T(U),C,A,G,AT(%),GC(%),GT(%),AT skew,GC skew\n' + PCGs_stat_plus + \
               PCGs_stat_minus + first_stat_plus + first_stat_minus + second_stat_plus + second_stat_minus +\
               third_stat_plus + third_stat_minus + ''.join(list_genes) + \
               rRNA_stat_plus + rRNA_stat_minus + tRNA_stat_plus + tRNA_stat_minus + geom_stat
        self.dict_spe_stat[self.ID] = stat + "PCGs: protein-coding genes; +: major strand; -: minus strand\n"
        # 生成折线图分类信息
        list_genes_line = [
            value for (
                key, value) in sorted(
                self.dict_genes.items()) if not key.startswith("zNCR")]
        p_spe_plus = PCGs_stat_plus.strip("\n") + "," + self.taxonmy + "\n" if PCGs_stat_plus else ""
        p_spe_minus = PCGs_stat_minus.strip("\n") + "," + self.taxonmy + "\n" if PCGs_stat_minus else ""
        t_spe_plus = tRNA_stat_plus.strip("\n") + "," + self.taxonmy + "\n" if tRNA_stat_plus else ""
        t_spe_minus = tRNA_stat_minus.strip("\n") + "," + self.taxonmy + "\n" if tRNA_stat_minus else ""
        r_spe_plus = rRNA_stat_plus.strip("\n") + "," + self.taxonmy + "\n" if rRNA_stat_plus else ""
        r_spe_minus = rRNA_stat_minus.strip("\n") + "," + self.taxonmy + "\n" if rRNA_stat_minus else ""
        fst_spe_plus = first_stat_plus.strip("\n") + "," + self.taxonmy + "\n" if first_stat_plus else ""
        fst_spe_minus = first_stat_minus.strip("\n") + "," + self.taxonmy + "\n" if first_stat_minus else ""
        scd_spe_plus = second_stat_plus.strip("\n") + "," + self.taxonmy + "\n" if second_stat_plus else ""
        scd_spe_minus = second_stat_minus.strip("\n") + "," + self.taxonmy + "\n" if second_stat_minus else ""
        trd_spe_plus = third_stat_plus.strip("\n") + "," + self.taxonmy + "\n" if third_stat_plus else ""
        trd_spe_minus = third_stat_minus.strip("\n") + "," + self.taxonmy + "\n" if third_stat_minus else ""
        self.line_spe_stat += geom_stat.strip("\n") + "," + self.taxonmy + "\n" + p_spe_plus + p_spe_minus + \
                              t_spe_plus + t_spe_minus + r_spe_plus + r_spe_minus + fst_spe_plus + fst_spe_minus + \
                              scd_spe_plus + scd_spe_minus + trd_spe_plus + trd_spe_minus + \
                              "".join([i.strip("\n") + "," + self.taxonmy + "\n" for i in list_genes_line])
        rscu_sum = RSCUsum(self.organism_1, self.PCGs_strim, str(self.code_table))
        rscu_table = rscu_sum.table
        self.dict_RSCU[self.ID] = rscu_table
        self.dict_all_spe_RSCU["title"] += self.organism + ","
        self.dict_all_codon_COUNT["title"] += self.organism + ","
        self.dict_all_AA_COUNT["title"] += self.organism + ","
        self.dict_all_AA_RATIO["title"] += self.organism + ","
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
        self.PCG_seq += '>' + self.usedName + '\n' + self.PCGs_strim + '\n'
        self.tRNA_seqs += '>' + self.usedName + '\n' + self.tRNAs + '\n'
        self.rRNA_seqs += '>' + self.usedName + '\n' + self.rRNAs + '\n'
        #         组成表
        self.orgTable += "Overlap:," + \
                         str(self.overlap) + "," + "gap:," + str(self.gap)
        self.dict_orgTable[self.ID] = self.orgTable
        self.linear_order += self.gene_order + '\n'
        # 密码子偏倚分析
        if self.dict_args["cal_codon_bias"]:
            codonBias = CodonBias(self.PCGs_strim, self.code_table, path=self.exportPath)
            list_cBias = codonBias.getCodonBias()
            self.codon_bias += ",".join(["PCGs"] + list_cBias) + "," + self.taxonmy + "\n"

    def check_Absence(self):
        if len(self.list_pro) != 0:  # 有些物种缺失部分基因
            for i in self.list_pro:
                if i in ["rrnS", "rrnL"]:
                    if i in list(self.dict_RNA.keys()):  # 如果字典已经有这个键
                        self.dict_RNA[i] += ',N/A'
                        self.dict_gene_ATskews[i] += ',N/A'
                        self.dict_gene_GCskews[i] += ',N/A'
                        self.dict_gene_ATCont[i] += ',N/A'
                        self.dict_gene_GCCont[i] += ',N/A'
                    else:
                        self.dict_RNA[i] = i + ',N/A'
                        self.dict_gene_ATskews[i] = i + ',N/A'
                        self.dict_gene_GCskews[i] = i + ',N/A'
                        self.dict_gene_ATCont[i] = i + ',N/A'
                        self.dict_gene_GCCont[i] = i + ',N/A'
                else:
                    if i in list(self.dict_PCG.keys()):
                        self.dict_PCG[i] += ',N/A'
                        self.dict_start[i] += ',N/A'
                        self.dict_stop[i] += ',N/A'
                        self.dict_gene_ATskews[i] += ',N/A'
                        self.dict_gene_GCskews[i] += ',N/A'
                        self.dict_gene_ATCont[i] += ',N/A'
                        self.dict_gene_GCCont[i] += ',N/A'
                    else:
                        self.dict_PCG[i] = i + ',N/A'
                        self.dict_start[i] = i + ',N/A'
                        self.dict_stop[i] = i + ',N/A'
                        self.dict_gene_ATskews[i] = i + ',N/A'
                        self.dict_gene_GCskews[i] = i + ',N/A'
                        self.dict_gene_ATCont[i] = i + ',N/A'
                        self.dict_gene_GCCont[i] = i + ',N/A'

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
        space = "" if space == 0 or self.orgTable[-7:] == 'Strand\n' else str(
            space)
        chain = "H" if self.strand == "+" else "L"
        # 新增了添加序列功能
        self.orgTable += ",".join([new_name,
                                   str(self.start),
                                   str(self.end),
                                   str(orgSize),
                                   space,
                                   ini,
                                   ter,
                                   chain,
                                   seq]) + "\n"
        self.lastEndIndex = self.end

    def judge(self, name, values, seq):
        if name == 'tRNA-Leu' or name == 'tRNA-Ser' or name == "L" or name == "S":
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
                self.leu_ser += ">%s\n%s\n" % (trnaName, seq)
        else:
            name = name
        return name

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
        new_name = self.fetchGeneName()
        if not new_name:
            return
        if new_name.upper() in self.dict_unify_mtname:
            # 换成标准的名字
            new_name = self.dict_unify_mtname[new_name.upper()]
        if new_name in self.list_pro:
            self.list_pro.remove(new_name)
        self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
        self.dict_pro[new_name + '>' + self.organism_1 + '_' + self.ID] = '>' + \
                                                                          self.usedName + '\n' + seq + \
                                                                          '\n'  # 这里不能用seq代替，因为要用大小写区分正负链
        translation = self.qualifiers['translation'][0] if 'translation' in self.qualifiers else ""  # 有时候没有translation
        self.dict_AA[new_name + '>' + self.organism_1 + '_' +
                     self.ID] = '>' + self.usedName + '\n' + translation + "\n"
        self.gene_order += self.omit_strand + new_name + ' '
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
        if new_name in self.list_PCGs:  # 确保是属于那14或者15个基因
            if new_name in self.dict_PCG.keys():  # 看字典是否已经有这个键
                self.dict_PCG[new_name] += ',' + str(size)
                self.dict_start[new_name] += ',' + ini
                self.dict_stop[new_name] += ',' + ter
                self.dict_gene_ATskews[new_name] += ',' + seqStat.AT_skew
                self.dict_gene_GCskews[new_name] += ',' + seqStat.GC_skew
                self.dict_gene_ATCont[new_name] += ',' + seqStat.AT_percent
                self.dict_gene_GCCont[new_name] += ',' + seqStat.GC_percent
            else:
                self.dict_PCG[new_name] = new_name + ',' + str(size)
                self.dict_start[new_name] = new_name + ',' + ini
                self.dict_stop[new_name] = new_name + ',' + ter
                self.dict_gene_ATskews[new_name] = new_name + ',' + seqStat.AT_skew
                self.dict_gene_GCskews[new_name] = new_name + ',' + seqStat.GC_skew
                self.dict_gene_ATCont[new_name] = new_name + ',' + seqStat.AT_percent
                self.dict_gene_GCCont[new_name] = new_name + ',' + seqStat.GC_percent
        self.PCGs_strim += RSCU_seq
        if self.strand == "+":
            self.PCGs_strim_plus += RSCU_seq
        else:
            self.PCGs_strim_minus += RSCU_seq
        # self.PCGs += seq
        # 生成组成表相关
        self.fun_orgTable(new_name, size, ini, ter, seq)
        ##间隔区提取
        self.refresh_pairwise_feature(new_name)
        ##密码子偏倚分析
        if self.dict_args["cal_codon_bias"]:
            codonBias = CodonBias(RSCU_seq, self.code_table, path=self.exportPath)
            list_cBias = codonBias.getCodonBias()
            self.codon_bias += ",".join([new_name] + list_cBias) + "," + self.taxonmy + "\n"

    def rRNA_(self):
        new_name = self.fetchGeneName()
        if not new_name:
            return
        seq = str(self.feature.extract(self.seq))
        if new_name.upper() in self.dict_unify_mtname:
            # 换成标准的名字
            new_name = self.dict_unify_mtname[new_name.upper()]
        if new_name in self.list_pro:
            self.list_pro.remove(new_name)
        self.dict_gene_names.setdefault(new_name, []).append(self.usedName)
        self.dict_rRNA[new_name + '>' + self.organism_1 + '_' +
                       self.ID] = '>' + self.usedName + '\n' + seq + '\n'
        if self.dict_args["rRNAchecked"]:
            self.gene_order += self.omit_strand + new_name + ' '
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
        if new_name in self.dict_RNA:  # 如果字典已经有这个键
            self.dict_RNA[new_name] += ',' + str(len(seq))
            self.dict_gene_ATskews[new_name] += ',' + seqStat.AT_skew
            self.dict_gene_GCskews[new_name] += ',' + seqStat.GC_skew
            self.dict_gene_ATCont[new_name] += ',' + seqStat.AT_percent
            self.dict_gene_GCCont[new_name] += ',' + seqStat.GC_percent
        else:
            self.dict_RNA[new_name] = new_name + \
                                      ',' + str(len(seq))
            self.dict_gene_ATskews[new_name] = new_name + ',' + seqStat.AT_skew
            self.dict_gene_GCskews[new_name] = new_name + ',' + seqStat.GC_skew
            self.dict_gene_ATCont[new_name] = new_name + ',' + seqStat.AT_percent
            self.dict_gene_GCCont[new_name] = new_name + ',' + seqStat.GC_percent
        self.rRNAs += seq
        if self.strand == "+":
            self.rRNAs_plus += seq
        else:
            self.rRNAs_minus += seq
        # 生成组成表相关
        self.fun_orgTable(new_name, seqStat.length, "", "", seq)
        ##间隔区提取
        self.refresh_pairwise_feature(new_name)

    def tRNA_(self):
        replace_name = self.fetchGeneName()
        if not replace_name:
            return
        seq = str(self.feature.extract(self.seq))
        values = ':' + ':'.join([i[0] for i in self.qualifiers.values()]) + ':'
        name = self.judge(replace_name, values, seq)
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
        self.dict_tRNA[new_name + '>' + self.organism_1 + '_' +
                       self.ID] = '>' + self.usedName + '\n' + seq + '\n'
        if self.dict_args["tRNAchecked"]:
            self.gene_order += self.omit_strand + name + ' '
        self.tRNAs += seq.upper()
        if self.strand == "+":
            self.tRNAs_plus += seq.upper()
        else:
            self.tRNAs_minus += seq.upper()
        # 生成组成表相关
        self.fun_orgTable(new_name, len(seq), "", "", seq)
        ##间隔区提取
        self.refresh_pairwise_feature(new_name)

    def extract(self):
        # gb_records = SeqIO.parse(self.gbContentIO, "genbank")
        self.init_args_all()
        # 专门用于判断
        included_features = [i.upper() for i in self.included_features]
        for num, gb_file in enumerate(self.gb_files):
            try:
                gb = SeqIO.parse(gb_file, "genbank")
                gb_record = next(gb)
                self.name = gb_record.name
                self.list_pro = self.list_PCGs[:]
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
                ok = self.check_records(features)
                if not ok: continue
                has_feature = False
                has_source = False
                for self.feature in features:
                    self.qualifiers = self.feature.qualifiers
                    self.start = int(self.feature.location.start) + 1
                    self.end = int(self.feature.location.end)
                    self.strand = "+" if self.feature.location.strand == 1 else "-"
                    self.omit_strand = "" if self.strand == "+" else "-"
                    # # 用于生成organization表
                    # self.positionFrom, self.positionTo = list1[0], list1[-1]
                    self.feature_type = self.feature.type
                    if self.feature_type not in (self.list_features + ["source"]):
                        self.list_features.append(self.feature_type)
                    if self.feature.type == "source":
                        self.parseSource()
                        has_source = True
                    elif self.feature_type == 'CDS':
                        self.code_table = int(self.qualifiers["transl_table"][0]) if "transl_table" in self.qualifiers \
                            else self.selected_code_table
                        self.fetchTerCodon() #得到终止密码子
                        self.CDS_()
                        self.getNCR()
                        has_feature = True
                    elif self.feature_type == 'rRNA':
                        self.rRNA_()
                        self.getNCR()
                        has_feature = True
                    elif self.feature_type == 'tRNA':
                        self.tRNA_()
                        self.getNCR()
                        has_feature = True
                    elif self.included_features == "All" or self.feature_type.upper() in included_features:
                        # 剩下的按照常规的来提取
                        self.parseFeature()
                        self.getNCR()
                        has_feature = True
                if not has_feature:
                    ##ID里面没有找到任何对应的feature的情况
                    name = self.usedName if has_source else self.ID
                    self.list_none_feature_IDs.append(name)
                self.gb_record_stat()
                self.check_Absence()
                self.getNCR(mode="end")  ##判断最后的间隔区
                self.input_file.write(gb_record.format("genbank"))
            except:
                self.Error_ID += self.name + ":\n" + \
                                 ''.join(
                                     traceback.format_exception(*sys.exc_info())) + "\n"
            num += 1
            self.progressSig.emit(num * 70 / self.totleID)
        self.input_file.close()

    def sort_CDS(self):
        list_pro = sorted(list(self.dict_pro.keys()))
        previous = ''
        seq_pro = ''
        trans_pro = ''
        seq_aa = ""  # 存放读取的translation里面的AA序列
        # 避免报错
        gene = ""
        it = iter(list_pro)
        table = CodonTable.ambiguous_dna_by_id[self.code_table]
        while True:
            try:
                i = next(it)
                gene = re.match('^[^>]+', i).group()
                if gene == previous or previous == '':
                    seq_pro += self.dict_pro[i]
                    seq_aa += self.dict_AA[i]
                    raw_sequence = self.dict_pro[i].split('\n')[1]
                    trim_sequence = self.trim_ter(raw_sequence)
                    try:
                        protein = _translate_str(trim_sequence, table)
                    except:
                        protein = ""
                    trans_pro += self.dict_pro[
                        i].replace(raw_sequence, protein)
                    previous = gene
                if gene != previous:
                    self.save2file(seq_pro, previous, self.CDS_nuc_path)
                    self.save2file(seq_aa, previous, self.CDS_aa_path)
                    self.save2file(trans_pro, previous, self.CDS_TrsAA_path)
                    seq_pro = ''
                    trans_pro = ''
                    seq_aa = ""  # 存放读取的translation里面的AA序列
                    seq_pro += self.dict_pro[i]
                    seq_aa += self.dict_AA[i]
                    raw_sequence = self.dict_pro[i].split('\n')[1]
                    trim_sequence = self.trim_ter(raw_sequence)
                    try:
                        protein = _translate_str(trim_sequence, table)
                    except:
                        protein = ""
                    trans_pro += self.dict_pro[
                        i].replace(raw_sequence, protein)
                    previous = gene
            except StopIteration:
                self.save2file(seq_pro, previous, self.CDS_nuc_path)
                self.save2file(seq_aa, previous, self.CDS_aa_path)
                self.save2file(trans_pro, previous, self.CDS_TrsAA_path)
                break

    def sort_rRNA(self):
        list_rRNA = sorted(list(self.dict_rRNA.keys()))
        previous = ''
        seq_rRNA = ''
        # 避免报错
        gene = ""
        it = iter(list_rRNA)
        while True:
            try:
                i = next(it)
                gene = re.match('^[^>]+', i).group()
                if gene == previous or previous == '':
                    seq_rRNA += self.dict_rRNA[i]
                    previous = gene
                if gene != previous:
                    self.save2file(seq_rRNA, previous, self.rRNA_path)
                    seq_rRNA = ''
                    seq_rRNA += self.dict_rRNA[i]
                    previous = re.match('^[^>]+', i).group()
            except StopIteration:
                self.save2file(seq_rRNA, previous, self.rRNA_path)
                break

    def sort_tRNA(self):
        list_tRNA = sorted(list(self.dict_tRNA.keys()))
        previous = ''
        seq_tRNA = ''
        # 避免报错
        gene = ""
        it = iter(list_tRNA)
        while True:
            try:
                i = next(it)
                gene = re.match('^[^>]+', i).group()
                if gene == previous or previous == '':
                    seq_tRNA += self.dict_tRNA[i]
                    previous = gene
                if gene != previous:
                    self.save2file(seq_tRNA, previous, self.tRNA_path)
                    seq_tRNA = ''
                    seq_tRNA += self.dict_tRNA[i]
                    previous = re.match('^[^>]+', i).group()
            except StopIteration:
                self.save2file(seq_tRNA, previous, self.tRNA_path)
                break

    def gene_sort_save(self):
        self.CDS_nuc_path = self.factory.creat_dirs(self.exportPath + os.sep + "CDS_NUC")
        self.CDS_aa_path = self.factory.creat_dirs(self.exportPath + os.sep + "CDS_AA")
        self.CDS_TrsAA_path = self.factory.creat_dirs(self.exportPath + os.sep + "self-translated_AA")
        self.sort_CDS()
        self.progressSig.emit(82)
        self.rRNA_path = self.factory.creat_dirs(self.exportPath + os.sep + "rRNA")
        self.sort_rRNA()
        self.progressSig.emit(87)
        self.tRNA_path = self.factory.creat_dirs(self.exportPath + os.sep + "tRNA")
        self.sort_tRNA()
        self.progressSig.emit(92)
        keys = list(self.dict_feature_fas.keys())
        #只保留有效值
        for i in keys:
            if not self.dict_feature_fas[i]:
                del self.dict_feature_fas[i]
        total = len(self.dict_feature_fas)
        if not total:
            self.progressSig.emit(95)
            return
        base = 92
        proportion = 3 / total
        for feature in self.dict_feature_fas:
            feature_fas = self.dict_feature_fas[feature]
            if not feature_fas:
                ##如果没有提取到任何东西就返回
                continue
            featurePath = self.factory.creat_dirs(self.exportPath + os.sep + feature)
            base = self.save_each_feature(feature_fas, featurePath, base, proportion)

    def saveGeneralFile(self):
        super(GBextract_MT, self).saveGeneralFile()
        filesPath = self.factory.creat_dirs(self.exportPath + os.sep + 'files')
        with open(filesPath + os.sep + 'linear_order.txt', 'w', encoding="utf-8") as f:
            f.write(self.linear_order)
        with open(filesPath + os.sep + 'complete_seq.fas', 'w', encoding="utf-8") as f:
            f.write(self.complete_seq)
        with open(filesPath + os.sep + 'PCG_seqs.fas', 'w', encoding="utf-8") as f6:
            f6.write(self.PCG_seq)
        with open(filesPath + os.sep + 'tRNA_seqs.fas', 'w', encoding="utf-8") as f7:
            f7.write(self.tRNA_seqs)
        with open(filesPath + os.sep + 'rRNA_seqs.fas', 'w', encoding="utf-8") as f8:
            f8.write(self.rRNA_seqs)
        # super(GBextract_MT, self).saveGeneralFile()

    def saveItolFiles(self):
        itolPath = self.factory.creat_dirs(self.exportPath + os.sep + 'itolFiles')
        itol_domain = "DATASET_DOMAINS\nSEPARATOR COMMA\nDATASET_LABEL,Mito gene order\nCOLOR,#ff00aa\nWIDTH,1250\nBACKBONE_COLOR,black\nHEIGHT_FACTOR,0.8\nLEGEND_TITLE,Regions\nLEGEND_SHAPES,%s,%s,%s,%s,%s,%s,%s\nLEGEND_COLORS,%s,%s,%s,%s,%s,%s,%s\nLEGEND_LABELS,atp6|atp8,nad1-6|nad4L,cytb,cox1-3,rRNA,tRNA,NCR\n#SHOW_INTERNAL,0\nSHOW_DOMAIN_LABELS,1\nLABELS_ON_TOP,1\nDATA\n" % (
            self.dict_args["atpshape"], self.dict_args["nadshape"], self.dict_args["cytbshape"],
            self.dict_args["coxshape"], self.dict_args["rRNAshape"], self.dict_args["tRNAshape"],
            self.dict_args["NCRshape"], self.dict_args["atpcolour"], self.dict_args["nadcolour"],
            self.dict_args["cytbcolour"], self.dict_args["coxcolour"], self.dict_args["rRNAcolour"],
            self.dict_args["tRNAcolour"], self.dict_args["NCRcolour"])
        order2itol = Order2itol(self.linear_order, self.dict_args)
        itol_domain += order2itol.itol_domain
        super(GBextract_MT, self).saveItolFiles()
        with open(itolPath + os.sep + 'itol_gene_order.txt', 'w', encoding="utf-8") as f1:
            f1.write(itol_domain)

    def saveStatFile(self):
        super(GBextract_MT, self).saveStatFile()
        statFilePath = self.factory.creat_dirs(self.exportPath + os.sep + 'StatFiles')
        # 生成speciesStat文件夹
        speciesStatPath = self.factory.creat_dirs(statFilePath + os.sep + 'speciesStat')
        # 生成RSCU文件夹
        RSCUpath = self.factory.creat_dirs(statFilePath + os.sep + 'RSCU')
        # 生成CDS文件夹
        CDSpath = self.factory.creat_dirs(statFilePath + os.sep + 'CDS')
        # RSCU  PCA# 生成PCA用的统计表
        title_rscu = self.dict_all_spe_RSCU.pop("title").strip(",") + "\n"
        for j in list(self.dict_all_spe_RSCU.keys()):
            title_rscu += j + "," + \
                          ",".join(self.dict_all_spe_RSCU[j]) + "\n"
        # 生成文件
        with open(RSCUpath + os.sep + "all_rscu_stat.csv", "w", encoding="utf-8") as f:
            f.write(title_rscu)
        # COUNT codon PCA# 生成PCA用的统计表
        title_codon_count = self.dict_all_codon_COUNT.pop(
            "title").strip(",") + "\n"
        for j in list(self.dict_all_codon_COUNT.keys()):
            title_codon_count += j + "," + \
                                 ",".join(self.dict_all_codon_COUNT[j]) + "\n"
        # 生成文件
        with open(RSCUpath + os.sep + "all_codon_count_stat.csv", "w", encoding="utf-8") as f:
            f.write(title_codon_count)
        # COUNT aa PCA# 生成PCA用的统计表
        title_AA_count = self.dict_all_AA_COUNT.pop(
            "title").strip(",") + "\n"
        for j in list(self.dict_all_AA_COUNT.keys()):
            title_AA_count += j + "," + \
                              ",".join(self.dict_all_AA_COUNT[j]) + "\n"
        # 生成文件
        with open(RSCUpath + os.sep + "all_AA_count_stat.csv", "w", encoding="utf-8") as f:
            f.write(title_AA_count)
        # ratio aa PCA# 生成PCA用的统计表
        title_AA_ratio = self.dict_all_AA_RATIO.pop(
            "title").strip(",") + "\n"
        for j in list(self.dict_all_AA_RATIO.keys()):
            title_AA_ratio += j + "," + \
                              ",".join(self.dict_all_AA_RATIO[j]) + "\n"
        # 生成文件
        with open(RSCUpath + os.sep + "all_AA_ratio_stat.csv", "w", encoding="utf-8") as f:
            f.write(title_AA_ratio)
        # 生成AA stack的文件
        title_aa_stack = self.dict_AA_stack.pop(
            "title") + "\n"
        for k in self.dict_AA_stack:
            title_aa_stack += self.dict_AA_stack[k]
        with open(RSCUpath + os.sep + "all_AA_stack.csv", "w", encoding="utf-8") as f:
            f.write(title_aa_stack)
        # 统计单个物种
        for j in self.dict_spe_stat:
            if j in self.dict_spe_stat:
                with open(speciesStatPath + os.sep + j + '.csv', 'w', encoding="utf-8") as f:
                    f.write(self.dict_spe_stat[j])
            if j in self.dict_orgTable:
                with open(speciesStatPath + os.sep + j + '_org.csv', 'w', encoding="utf-8") as f:
                    f.write(self.dict_orgTable[j])
            if j in self.dict_AAusage:
                with open(RSCUpath + os.sep + j + '_AA_usage.csv', 'w', encoding="utf-8") as f:
                    f.write(self.dict_AAusage[j])
            if j in self.dict_RSCU:
                with open(RSCUpath + os.sep + j + '_RSCU.csv', 'w', encoding="utf-8") as f:
                    f.write(self.dict_RSCU[j])
            if j in self.dict_RSCU_stack:
                with open(RSCUpath + os.sep + j + '_RSCU_stack.csv', 'w', encoding="utf-8") as f:
                    f.write(self.dict_RSCU_stack[j])
        # with open(statFilePath + os.sep + 'taxonomy.csv', 'w', encoding="utf-8") as f1:
        #     f1.write(self.all_taxonmy)
        # list_geom = list(sorted(self.dict_geom.values()))
        list_start = list(sorted(self.dict_start.values()))
        list_stop = list(sorted(self.dict_stop.values()))
        list_PCGs = list(sorted(self.dict_PCG.values()))
        list_RNA = list(sorted(self.dict_RNA.values()))
        list_ATskew = list(sorted(self.dict_gene_ATskews.values()))
        list_GCskew = list(sorted(self.dict_gene_GCskews.values()))
        list_ATCont = list(sorted(self.dict_gene_ATCont.values()))
        list_GCCont = list(sorted(self.dict_gene_GCCont.values()))
        # with open(statFilePath + os.sep + 'genomeStat.csv', 'w', encoding="utf-8") as f2:
        #     lineages = ",".join(
        #         self.included_lineages) + "," if self.included_lineages else ""
        #     prefix = 'Species,' + lineages + \
        #              'GeneBank accesion no.,Full length (bp),A (%),T (%),C (%),G (%),A+T (%),G+C (%),AT skew,GC skew\n'
        #     f2.write(prefix + ''.join(list_geom))
        with open(statFilePath + os.sep + 'geneStat.csv', 'w', encoding="utf-8") as f3:
            list_abbre = self.assignAbbre(self.list_name_gb)
            str_taxonmy, footnote = self.geneStatPlus(list_abbre)
            headers = 'Species,' + ','.join(list_abbre) + '\n'
            prefix_PCG = 'Length of PCGs (bp)\n'
            prefix_rRNA = 'Length of rRNA genes (bp)\n'
            prefix_ini = 'Putative start codon\n'
            prefix_ter = 'Putative terminal codon\n'
            prefix_ATskew = 'AT skew\n'
            prefix_GCskew = 'GC skew\n'
            prefix_ATCont = 'AT content\n'
            prefix_GCCont = 'GC content\n'
            f3.write(str_taxonmy + headers + prefix_PCG + '\n'.join(list_PCGs) + '\n' +
                     prefix_rRNA + '\n'.join(list_RNA) + '\n' +
                     prefix_ini + '\n'.join(list_start) + '\n' +
                     prefix_ter + '\n'.join(list_stop) + '\n' +
                     prefix_ATskew + '\n'.join(list_ATskew) + '\n' +
                     prefix_GCskew + '\n'.join(list_GCskew) + '\n' +
                     prefix_ATCont + '\n'.join(list_ATCont) + '\n' +
                     prefix_GCCont + '\n'.join(list_GCCont) + '\n' +
                     "N/A: Not Available; tRNAs: concatenated tRNA genes; rRNAs: concatenated rRNA genes;"
                     " +: major strand; -: minus strand\n" + footnote)
        # skewness
        with open(CDSpath + os.sep + 'PCGsCodonSkew.csv', 'w', encoding="utf-8") as f4:
            f4.write(self.PCGsCodonSkew)

        with open(CDSpath + os.sep + 'firstCodonSkew.csv', 'w', encoding="utf-8") as f5:
            f5.write(self.firstCodonSkew)

        with open(CDSpath + os.sep + 'secondCodonSkew.csv', 'w', encoding="utf-8") as f6:
            f6.write(self.secondCodonSkew)

        with open(CDSpath + os.sep + 'thirdCodonSkew.csv', 'w', encoding="utf-8") as f7:
            f7.write(self.thirdCodonSkew)
        # # 生成密码子偏倚统计
        if self.dict_args["cal_codon_bias"]:
            with open(CDSpath + os.sep + 'codon_bias.csv', 'w', encoding="utf-8") as f11:
                f11.write(self.codon_bias)

        with open(statFilePath + os.sep + 'gbAccNum.csv', 'w', encoding="utf-8") as f8:
            f8.write(self.name_gb)
        # # ncr统计
        # self.ncr_stat_fun()
        # with open(statFilePath + os.sep + 'ncrStat.csv', 'w', encoding="utf-8") as f9:
        #     f9.write(self.ncrInfo)
        allStat = self.fetchAllStatTable()
        with open(statFilePath + os.sep + 'used_species.csv', 'w', encoding="utf-8") as f4:
            f4.write(allStat)
        # 生成折线图
        with open(statFilePath + os.sep + 'geom_line.csv', 'w', encoding="utf-8") as f11:
            f11.write(self.line_spe_stat)
        # 删除ENC的中间文件
        try:
            for file in ["codonW_infile.fas", "codonW_outfile.txt", "codonW_blk.txt"]:
                os.remove(self.exportPath + os.sep + file)
        except: pass

    def fetchAllStatTable(self):
        allStat = "Taxon,Accession number,Size(bp),AT%,AT-Skew,GC-Skew\n"
        list_dict_sorted = sorted(list(self.dict_all_stat.keys()))
        lineage_count = len(self.included_lineages) + 1
        last_lineage = [1] * lineage_count
        for i in list_dict_sorted:
            lineage1 = self.dict_all_stat[i][:lineage_count]
            content = self.compareLineage(
                lineage1, last_lineage, self.dict_all_stat[i][lineage_count:])
            allStat += content
            last_lineage = lineage1
        return allStat

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

    def geneStatPlus(self, list_abbre):
        zip_taxonmy = list(zip(
            *self.list_all_taxonmy))  # [('Gyrodactylidae', 'Capsalidae', 'Ancyrocephalidae', 'Chauhaneidae'), ('Gyrodactylidea', 'Capsalidea', 'Dactylogyridea', 'Mazocraeidea'), ('Monogenea', 'Monogenea', 'Monogenea', 'Monogenea')]
        lineage = list(reversed(self.included_lineages))
        header_taxonmy = [[lineage[num]] + list(i) for num, i in enumerate(
            zip_taxonmy)]  # [['Family', 'Gyrodactylidae', 'Capsalidae', 'Ancyrocephalidae'], ['Superfamily', 'Gyrodactylidea', 'Capsalidea', 'Dactylogyridea'], ['Class', 'Monogenea', 'Monogenea', 'Monogenea']]
        str_taxonmy = "\n".join([",".join(lineage) for lineage in header_taxonmy]) + "\n"
        zip_name = list(zip(list_abbre, self.list_name_gb))
        footnote = "\n".join([each_name[0] + ": " + " ".join(each_name[1]) for each_name in zip_name])
        return str_taxonmy, footnote

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