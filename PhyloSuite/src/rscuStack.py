#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''给csv文件按照堆积条形图排序,*终止子的会被删掉
导入的格式是mega生成的csv文件
59行代码改了
rgx_mega正则Data\s+改为了Data.*?\s+
20170911新增生成PCA统计的表格
输出结果有stack的统计表，还有氨基酸使用频率统计表，还有用于密码子PCA分析的统计表
新增统计GT结尾密码子个数
20171028新增统计氨基酸个数的功能。未完成功能：本地配置脚本，AA那个ratio变成小数，就是比现在除以100
'''
import re
from collections import OrderedDict


class RSCUstack(object):

    def __init__(self, content, dict_all_rscu, dict_all_codon_count, dict_all_AA_count, dict_all_AA_ratio, species):
        super(RSCUstack, self).__init__()
        self.content = content
        self.dict_all_rscu = dict_all_rscu
        self.dict_all_codon_count = dict_all_codon_count
        self.dict_all_AA_count = dict_all_AA_count
        self.dict_all_AA_ratio = dict_all_AA_ratio
        self.species = species
        self.dict_AA = {"F": "Phe",
                        "L": "Leu",
                        "L1": "Leu1",
                        "L2": "Leu2",
                        "I": "Ile",
                        "M": "Met",
                        "V": "Val",
                        "S": "Ser",
                        "S1": "Ser1",
                        "S2": "Ser2",
                        "P": "Pro",
                        "T": "Thr",
                        "A": "Ala",
                        "Y": "Tyr",
                        "H": "His",
                        "Q": "Gln",
                        "N": "Asn",
                        "K": "Lys",
                        "D": "Asp",
                        "E": "Glu",
                        "C": "Cys",
                        "W": "Trp",
                        "R": "Arg",
                        "G": "Gly",
                        "*": "Ter"}
        self.format_mega()
        self.generateStatAndStack()
#         self.saveFile()

    def format_mega(self):
        rgx_mega = re.compile(
            r"(?is)Domain: Data.*?\s+?(Codon.+)Average# codons=(\d+)")
        # 有时候从xls转CSV的表格会有多余的逗号,如codons=206,,,,,,,,,
        self.content = re.sub(r",{2,}", "", self.content)
#         print(fileContent, rgx_mega.search(fileContent))
        table, self.codonSum = rgx_mega.findall(self.content)[0]
        col_1 = []
        col_2 = []
        col_3 = []
        col_4 = []
        # 统计氨基酸的数目
        self.aaSum = 0
        for i in table.split("\n"):
            if not i.startswith("Codon") and not i == "":
                list_i = i.strip().split(",")
                # 去除一些空值
                list_i = [j for j in list_i if j != ""]
                col_1.append(list_i[:3])
                col_2.append(list_i[3:6])
                col_3.append(list_i[6:9])
                col_4.append(list_i[9:])
                # 筛选掉终止子，不加总
                self.aaSum += int(col_1[-1][1]
                                  ) if "*" not in col_1[-1][0] else 0
                self.aaSum += int(col_2[-1][1]
                                  ) if "*" not in col_2[-1][0] else 0
                self.aaSum += int(col_3[-1][1]
                                  ) if "*" not in col_3[-1][0] else 0
                self.aaSum += int(col_4[-1][1]
                                  ) if "*" not in col_4[-1][0] else 0
        self.list_mega = col_1 + col_2 + col_3 + col_4

    def leu_ser(self, codon, abbre):
        codon = codon.upper().replace("T", "U")
        if (abbre.upper() == "L" and codon.startswith("C")) or (abbre.upper() == "S" and codon.startswith("A")):
            return abbre + "1"
        elif (abbre.upper() == "L" and codon.startswith("U")) or (abbre.upper() == "S" and codon.startswith("U")):
            return abbre + "2"
        else:
            return abbre

    def generateStatAndStack(self):
        self.stack = "AA,Codon,Count,RSCU,Fill,Equality,%AT,aaRatio\n"
        self.stat = "AA,Count,%\n"
        self.aaStack = ""
        self.AT_end = 0
        self.GT_end = 0
        last_abbre = ""
        # 先计算总共多少个codon
        # for list_line in self.list_mega:
        aaNumber = 0
        # 排一下序，把相同的氨基酸放在一起
        self.list_mega = sorted(self.list_mega, key=lambda x:
                                                  re.search(r"\((.)\)", x[0]).group(1)
                                                    if re.search(r"\((.)\)", x[0]) else "1")
        for list_line in self.list_mega:
            abbre = re.search(r"\((.)\)", list_line[0]).group(1)
            codon = re.sub(r"\((.)\)", "", list_line[0])
            abbre = self.leu_ser(codon, abbre)  # 处理L1、L2
            number = int(list_line[-2])
            # 计算以AT结尾的密码子个数
            if codon[-1] == "U" or codon[-1] == "A":
                self.AT_end += number
            # 计算以GT结尾的密码子个数
            if codon[-1] == "U" or codon[-1] == "G":
                self.GT_end += number
            # 判断是否与上一个AA相同
            # if last_abbre != "":
            #     print(self.dict_AA[abbre], self.dict_AA[last_abbre])
            #     print(self.stack[-50:])
            if abbre == last_abbre:
                count += 1
                aaNumber += number
                if last_abbre != "" and last_abbre != "*":
                    self.stack = self.stack.strip("\n") + ",\n"
            else:
                count = 1
                if last_abbre != "" and last_abbre != "*":
                    aaRatio = '%.2f' % ((aaNumber / self.aaSum) * 100)
                    self.stat += self.dict_AA[last_abbre] + \
                        "(" + last_abbre + ")" + "," + str(aaNumber) + \
                        "," + aaRatio + "\n"
                    self.dict_all_AA_count.setdefault(
                        self.dict_AA[last_abbre], []).append(str(aaNumber))
                    self.dict_all_AA_ratio.setdefault(
                        self.dict_AA[last_abbre], []).append(aaRatio)
                    self.aaStack += ",".join([self.species,
                                              self.dict_AA[last_abbre], aaRatio]) + "\n"
                    self.stack = self.stack.strip("\n") + ",%s\n" % aaRatio
                aaNumber = number
            ratio = '%.2f' % (int(list_line[1]) * 100 / int(self.codonSum))
            if abbre in list(self.dict_AA.keys()) and abbre != "*":
                self.stack += self.dict_AA[abbre] + "," + codon + "," + \
                    list_line[-2] + "," + list_line[-1] + \
                    "," + str(count) + ",-0.5,%s\n" % ratio
                self.dict_all_rscu.setdefault(codon, []).append(list_line[-1])
                self.dict_all_codon_count.setdefault(
                    codon, []).append(list_line[-2])
            elif abbre != "*":
                self.stack += abbre + "," + codon + "," + \
                    list_line[-2] + "," + list_line[-1] + \
                    "," + str(count) + ",-0.5,%s\n" % ratio
                self.dict_all_rscu.setdefault(codon, []).append(list_line[-1])
                self.dict_all_codon_count.setdefault(
                    codon, []).append(list_line[-2])
            last_abbre = abbre
        # 最后要加一次
        aaRatio = '%.2f' % (aaNumber * 100 / self.aaSum)
        self.stat += self.dict_AA[last_abbre] + "(" + last_abbre + ")" + "," + \
            str(aaNumber) + ',' + aaRatio + \
            "\n"   + "codon end in A or T," + \
            str(self.AT_end) + \
            ",%.2f" % ((self.AT_end / self.aaSum) * 100) + "\n" + "codon end in G or T," + \
            str(self.GT_end) + \
            ",%.2f" % ((self.GT_end / self.aaSum) * 100) + "\n"  + \
            "Total," + str(self.aaSum) + "\n"
        self.dict_all_AA_count.setdefault(
            self.dict_AA[last_abbre], []).append(str(aaNumber))
        self.dict_all_AA_ratio.setdefault(
            self.dict_AA[last_abbre], []).append(aaRatio)
        # 最后执行一次
        self.aaStack += ",".join([self.species,
                                  self.dict_AA[last_abbre], aaRatio]) + "\n"
        self.stack = self.stack.strip("\n") + ",%s\n" % aaRatio
#     def saveFile(self):
#         input_path = os.path.dirname(
#             self.targetFile) if os.path.dirname(
#             self.targetFile) else '.'
#         base = os.path.splitext(os.path.basename(self.targetFile))[0]
#         with open(input_path + os.sep + "%s_stack.stack" % base, "w", encoding="utf-8") as f:
#             f.write(self.stack)
#         with open(input_path + os.sep + "%s_stat.stack" % base, "w", encoding="utf-8") as f1:
#             f1.write(self.stat)
if __name__ == "__main__":

    import os
    import sys
    import argparse
    import glob

    scriptPath = os.path.dirname(os.path.realpath(__file__))
    listFiles = glob.glob(scriptPath + os.sep + "*.csv")

    def parameter():
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            prog='csvStack.py',
            description='Sorting MEGA RSCU results so as to draw RSCU figure',
            epilog=r'''
examples:
python  csvStack.py file_path
              ''')
        listFiles_ = [
            i for i in listFiles if ("_stack" not in os.path.basename(i)) and ("_stat" not in os.path.basename(i))]
        parser.add_argument(
            "files", help='input file', default=listFiles_, nargs='*')
        myargs = parser.parse_args(sys.argv[1:])
        return myargs
    myargs = parameter()
    dict_all_rscu = OrderedDict()
    dict_all_codon_count = OrderedDict()
    dict_all_AA_count = OrderedDict()
    dict_all_AA_ratio = OrderedDict()
    title = "codon,"

    def saveFile(file_name, list_contents, outputPath=scriptPath):
        with open(file_name + "_stack.csv", "w", encoding="utf-8") as f:
            f.write(list_contents[0])
        with open(file_name + "_stat.csv", "w", encoding="utf-8") as f1:
            f1.write(list_contents[1])

    def readFile(file):
        with open(file, encoding="utf-8", errors='ignore') as f:
            content = f.read()
        return content
    for i in myargs.files:
        base = os.path.basename(i)
        prefix_base = os.path.splitext(base)[0]
        title += prefix_base + ","
        content = readFile(i)
        #content, dict_all_rscu, dict_all_codon_count, dict_all_AA_count, dict_all_AA_ratio, species):
        result = RSCUstack(
            content, dict_all_rscu, dict_all_codon_count, dict_all_AA_count, dict_all_AA_ratio, prefix_base)
        dict_all_rscu = result.dict_all_rscu
        dict_all_codon_count = result.dict_all_codon_count
        output_prefix = os.path.splitext(i)[0] if os.path.dirname(
            i) else "./" + os.path.splitext(i)[0]
        saveFile(output_prefix, [result.stack, result.stat])
    # RSCU文件
    title_rscu = title.strip(",") + "\n"
    # 生成PCA用的统计表
    for j in list(dict_all_rscu.keys()):
        title_rscu += j + "," + ",".join(dict_all_rscu[j]) + "\n"
    # 生成文件
    with open(scriptPath + os.sep + "all_rscu_stat.csv", "w", encoding="utf-8") as f:
        f.write(title_rscu)
    # 密码子频率count文件
    title_count = title.strip(",") + "\n"
    # 生成PCA用的统计表
    for j in list(dict_all_codon_count.keys()):
        title_count += j + "," + ",".join(dict_all_codon_count[j]) + "\n"
    # 生成文件
    with open(scriptPath + os.sep + "all_count_stat.csv", "w", encoding="utf-8") as f:
        f.write(title_count)
    print("Done!")
