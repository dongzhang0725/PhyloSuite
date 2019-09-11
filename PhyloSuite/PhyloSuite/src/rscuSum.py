#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''有兼并碱基的密码子将被忽略
输入文件为fasta文件，输出文件会以fas文件里面的物种名及其序列的结果单独输出
'''
from Bio.Data import CodonTable
from collections import OrderedDict


class RSCUsum(object):

    def __init__(self, seq_name, seq, codonTable):
        self.seq = seq
        self.codonTable = codonTable
        self.seq_name = seq_name
        self.dict_CodonTable = CodonTable.generic_by_id[
            int(self.codonTable)].forward_table
        list_stopCodons = CodonTable.generic_by_id[
            int(self.codonTable)].stop_codons
        dict_stopCodons = {}.fromkeys(list_stopCodons, "*")
        # 把终止子也加上去
        self.dict_CodonTable.update(dict_stopCodons)
        # print(self.dict_CodonTable)
        self.generate_dict()
        self.countSeq()
        self.generateRSCUandTable()
#         self.saveFile()

    def generate_dict(self):
        self.dict_codon = OrderedDict()  # {'CUU': [密码子总和,RSCU]}
        self.dict_abbre = OrderedDict()  # ｛“L”：[L个数，L对应密码子总和] ｝
        list_1 = ["U", "C", "A", "G"]
        list_2 = ["U", "C", "A", "G"]
        list_3 = ["U", "C", "A", "G"]
        for i in list_1:
            for j in list_2:
                for k in list_3:
                    codon = i + k + j
                    abbre = self.dict_CodonTable[codon]
                    self.dict_codon[codon] = [0, ""]
                    if self.dict_abbre.get(abbre):
                        self.dict_abbre[abbre][0] += 1
                    else:
                        self.dict_abbre[abbre] = [1, 0]

    def countSeq(self):
        # A替换为U
        seq = self.seq.replace("T", "U")
        codon = ""
        self.codonsNum = 0
        for num, i in enumerate(seq):
            if (num + 1) % 3 == 0:
                # 得再加一个，否则这次循环的i就浪费了
                codon += i.upper()
                # 如果codon含有兼并碱基，将不考虑
                if self.dict_CodonTable.get(codon):
                    abbre = self.dict_CodonTable[codon]
                    self.dict_codon[codon][0] += 1
                    self.dict_abbre[abbre][1] += 1
                    self.codonsNum += 1
                codon = ""
            else:
                # 这里统一序列的大小写，方便统计
                codon += i.upper()

    def generateRSCUandTable(self):
        self.table = "Sequences used: %s\n" % self.seq_name
        self.table += "Codon Table: %s\nDomain: Data\n" % self.codonTable
        self.table += "Codon,Count,RSCU,Codon,Count,RSCU,Codon,Count,RSCU,Codon,Count,RSCU\n"
        # print("dict_codon",self.dict_codon)
        # print("dict_abbre", self.dict_abbre)
        # print("dict_CodonTable", self.dict_CodonTable)
        for num, codon in enumerate(self.dict_codon.keys()):
            abbre = self.dict_CodonTable[codon]
            if not self.dict_abbre[abbre][1]:
                #如果某个氨基酸，1个都没有，容易报错
                RSCU = "0"
            else:
                RSCU = "%.2f" % (self.dict_abbre[abbre][
                             0] * self.dict_codon[codon][0] / self.dict_abbre[abbre][1])
            self.dict_codon[codon][1] = str(RSCU)
            # 讲count转为字符串
            self.dict_codon[codon][0] = str(self.dict_codon[codon][0])
            # 每4个codon换一次行
            if (num + 1) % 4 == 0:
                self.table += codon + "(" + abbre + ")" + "," + \
                    ",".join(self.dict_codon[codon]) + "\n"
            else:
                self.table += codon + "(" + abbre + ")" + "," + \
                    ",".join(self.dict_codon[codon]) + ","
        self.table += "Average# codons=%d" % self.codonsNum
#     def saveFile(self):
#         with open(scriptPath + os.sep + "%s_RSCU.csv" % self.seq_name, "w", encoding="utf-8") as f:
#             f.write(self.table)

if __name__ == "__main__":
    import re
    import os
    import sys
    import argparse
    import glob

    # 得到脚本所在位置
    scriptPath = os.path.dirname(os.path.realpath(__file__))
    # 在linux里面，os.getcwd不是得到脚本所在路径，而是运行命令所在的路径

    def parameter():
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            prog='csvSort.py',
            description='',
            epilog=r'''
              ''')
        parser.add_argument('-c', dest='code_table', help='type code table number of NCBI',
                            default="0")
        parser.add_argument(
            "files", help='input file', nargs='*')
        myargs = parser.parse_args(sys.argv[1:])
        return myargs
    myargs = parameter()

    def readFas(file):
        dict_taxon = {}
        with open(file, encoding="utf-8", errors='ignore') as f2:
            line = f2.readline()
            while line != "":
                while not line.startswith('>'):
                    line = f2.readline()
                fas_name = line.strip().replace(">", "")
                fas_seq = ""
                line = f2.readline()
                while not line.startswith('>') and line != "":
                    fas_seq += re.sub(r"\s", "", line)
                    line = f2.readline()
                dict_taxon[fas_name] = fas_seq
        return dict_taxon

    def saveFile(seq_name, content, outputPath=scriptPath):
        with open(outputPath + os.sep + "%s_RSCU.csv" % seq_name, "w", encoding="utf-8") as f:
            f.write(content)
    for i in myargs.files:
        dict_taxon = readFas(i)
        for j in dict_taxon.keys():
            rscuSum = RSCUsum(j, dict_taxon[j], myargs.code_table)
            saveFile(j, rscuSum.table)
    print("Done!")
