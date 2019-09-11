#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
This script extracts codonusage from CDS input FASTA file and writes a table containing the number of codons used for each sequence in the input FASTA file. In addition to the raw codon counts global ACTG counts, ACTG counts for the first, second and thrid codon position and Relative Synonymous Codon Usage (RSCU) is written to a file. Optional different methods can be applied to calculate Effective Number of Codons (ENC) can be choosen and calculated.

Author: Krisian Ullrich
date: Dec 2014
email: kristian.ullrich@biologie.uni-marburg.de
License: MIT

The MIT License (MIT)

Copyright (c) 2014 Kristian Ullrich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

有空的时候完善这个功能：six2fourtwo，以及加上其他密码表
"""

import sys

import argparse
from collections import OrderedDict

from Bio import SeqIO

codontable1 = {
        'GCT': ['A', 'four', 0],
        'GCC': ['A', 'four', 0],
        'GCA': ['A', 'four', 0],
        'GCG': ['A', 'four', 0],
        'CGT': ['R', 'six', 0],
        'CGC': ['R', 'six', 0],
        'CGG': ['R', 'six', 0],
        'CGA': ['R', 'six', 0],
        'AGA': ['R', 'six', 0],
        'AGG': ['R', 'six', 0],
        'AAT': ['N', 'two', 0],
        'AAC': ['N', 'two', 0],
        'GAT': ['D', 'two', 0],
        'GAC': ['D', 'two', 0],
        'TGT': ['C', 'two', 0],
        'TGC': ['C', 'two', 0],
        'CAA': ['Q', 'two', 0],
        'CAG': ['Q', 'two', 0],
        'GAA': ['E', 'two', 0],
        'GAG': ['E', 'two', 0],
        'GGT': ['G', 'four', 0],
        'GGC': ['G', 'four', 0],
        'GGA': ['G', 'four', 0],
        'GGG': ['G', 'four', 0],
        'CAT': ['H', 'two', 0],
        'CAC': ['H', 'two', 0],
        'ATT': ['I', 'three', 0],
        'ATC': ['I', 'three', 0],
        'ATA': ['I', 'three', 0],
        'ATG': ['M', 'one', 0],
        'TTA': ['L', 'six', 0],
        'TTG': ['L', 'six', 0],
        'CTT': ['L', 'six', 0],
        'CTC': ['L', 'six', 0],
        'CTA': ['L', 'six', 0],
        'CTG': ['L', 'six', 0],
        'AAA': ['K', 'two', 0],
        'AAG': ['K', 'two', 0],
        'TTT': ['F', 'two', 0],
        'TTC': ['F', 'two', 0],
        'CCT': ['P', 'four', 0],
        'CCC': ['P', 'four', 0],
        'CCA': ['P', 'four', 0],
        'CCG': ['P', 'four', 0],
        'TCT': ['S', 'six', 0],
        'TCC': ['S', 'six', 0],
        'TCA': ['S', 'six', 0],
        'TCG': ['S', 'six', 0],
        'AGT': ['S', 'six', 0],
        'AGC': ['S', 'six', 0],
        'ACT': ['T', 'four', 0],
        'ACC': ['T', 'four', 0],
        'ACA': ['T', 'four', 0],
        'ACG': ['T', 'four', 0],
        'TGG': ['W', 'one', 0],
        'TAT': ['Y', 'two', 0],
        'TAC': ['Y', 'two', 0],
        'GTT': ['V', 'four', 0],
        'GTC': ['V', 'four', 0],
        'GTA': ['V', 'four', 0],
        'GTG': ['V', 'four', 0],
        'TAA': ['*', 'three', 0],
        'TGA': ['*', 'three', 0],
        'TAG': ['*', 'three', 0],
        'XXX': ['_missing', 'none', 0]
    }
codontable1_s2ft = {
        'GCT': ['A', 'four', 0],
        'GCC': ['A', 'four', 0],
        'GCA': ['A', 'four', 0],
        'GCG': ['A', 'four', 0],
        'CGT': ['R', 'four', 0],
        'CGC': ['R', 'four', 0],
        'CGG': ['R', 'four', 0],
        'CGA': ['R', 'dour', 0],
        'AGA': ['R_', 'two', 0],
        'AGG': ['R_', 'two', 0],
        'AAT': ['N', 'two', 0],
        'AAC': ['N', 'two', 0],
        'GAT': ['D', 'two', 0],
        'GAC': ['D', 'two', 0],
        'TGT': ['C', 'two', 0],
        'TGC': ['C', 'two', 0],
        'CAA': ['Q', 'two', 0],
        'CAG': ['Q', 'two', 0],
        'GAA': ['E', 'two', 0],
        'GAG': ['E', 'two', 0],
        'GGT': ['G', 'four', 0],
        'GGC': ['G', 'four', 0],
        'GGA': ['G', 'four', 0],
        'GGG': ['G', 'four', 0],
        'CAT': ['H', 'two', 0],
        'CAC': ['H', 'two', 0],
        'ATT': ['I', 'three', 0],
        'ATC': ['I', 'three', 0],
        'ATA': ['I', 'three', 0],
        'ATG': ['M', 'one', 0],
        'TTA': ['L_', 'two', 0],
        'TTG': ['L_', 'two', 0],
        'CTT': ['L', 'four', 0],
        'CTC': ['L', 'four', 0],
        'CTA': ['L', 'four', 0],
        'CTG': ['L', 'four', 0],
        'AAA': ['K', 'two', 0],
        'AAG': ['K', 'two', 0],
        'TTT': ['F', 'two', 0],
        'TTC': ['F', 'two', 0],
        'CCT': ['P', 'four', 0],
        'CCC': ['P', 'four', 0],
        'CCA': ['P', 'four', 0],
        'CCG': ['P', 'four', 0],
        'TCT': ['S', 'four', 0],
        'TCC': ['S', 'four', 0],
        'TCA': ['S', 'four', 0],
        'TCG': ['S', 'four', 0],
        'AGT': ['S_', 'two', 0],
        'AGC': ['S_', 'two', 0],
        'ACT': ['T', 'four', 0],
        'ACC': ['T', 'four', 0],
        'ACA': ['T', 'four', 0],
        'ACG': ['T', 'four', 0],
        'TGG': ['W', 'one', 0],
        'TAT': ['Y', 'two', 0],
        'TAC': ['Y', 'two', 0],
        'GTT': ['V', 'four', 0],
        'GTC': ['V', 'four', 0],
        'GTA': ['V', 'four', 0],
        'GTG': ['V', 'four', 0],
        'TAA': ['*', 'three', 0],
        'TGA': ['*', 'three', 0],
        'TAG': ['*', 'three', 0],
        'XXX': ['_missing', 'none', 0]
    }
codontable2 = {
        'GCT': ['A', 'four', 0],
        'GCC': ['A', 'four', 0],
        'GCA': ['A', 'four', 0],
        'GCG': ['A', 'four', 0],
        'CGT': ['R', 'four', 0],
        'CGC': ['R', 'four', 0],
        'CGG': ['R', 'four', 0],
        'CGA': ['R', 'four', 0],
        'AAT': ['N', 'two', 0],
        'AAC': ['N', 'two', 0],
        'GAT': ['D', 'two', 0],
        'GAC': ['D', 'two', 0],
        'TGT': ['C', 'two', 0],
        'TGC': ['C', 'two', 0],
        'CAA': ['Q', 'two', 0],
        'CAG': ['Q', 'two', 0],
        'GAA': ['E', 'two', 0],
        'GAG': ['E', 'two', 0],
        'GGT': ['G', 'four', 0],
        'GGC': ['G', 'four', 0],
        'GGA': ['G', 'four', 0],
        'GGG': ['G', 'four', 0],
        'CAT': ['H', 'two', 0],
        'CAC': ['H', 'two', 0],
        'ATT': ['I', 'two', 0],
        'ATC': ['I', 'two', 0],
        'ATA': ['M', 'two', 0],
        'ATG': ['M', 'two', 0],
        'TTA': ['L', 'six', 0],
        'TTG': ['L', 'six', 0],
        'CTT': ['L', 'six', 0],
        'CTC': ['L', 'six', 0],
        'CTA': ['L', 'six', 0],
        'CTG': ['L', 'six', 0],
        'AAA': ['K', 'two', 0],
        'AAG': ['K', 'two', 0],
        'TTT': ['F', 'two', 0],
        'TTC': ['F', 'two', 0],
        'CCT': ['P', 'four', 0],
        'CCC': ['P', 'four', 0],
        'CCA': ['P', 'four', 0],
        'CCG': ['P', 'four', 0],
        'TCT': ['S', 'six', 0],
        'TCC': ['S', 'six', 0],
        'TCA': ['S', 'six', 0],
        'TCG': ['S', 'six', 0],
        'AGT': ['S', 'six', 0],
        'AGC': ['S', 'six', 0],
        'ACT': ['T', 'four', 0],
        'ACC': ['T', 'four', 0],
        'ACA': ['T', 'four', 0],
        'ACG': ['T', 'four', 0],
        'TGG': ['W', 'two', 0],
        'TGA': ['W', 'two', 0],
        'TAT': ['Y', 'two', 0],
        'TAC': ['Y', 'two', 0],
        'GTT': ['V', 'four', 0],
        'GTC': ['V', 'four', 0],
        'GTA': ['V', 'four', 0],
        'GTG': ['V', 'four', 0],
        'AGA': ['*', 'four', 0],
        'AGG': ['*', 'four', 0],
        'TAA': ['*', 'four', 0],
        'TAG': ['*', 'four', 0],
        'XXX': ['_missing', 'none', 0]
    }
codontable5 = {
        'GCT': ['A', 'four', 0],
        'GCC': ['A', 'four', 0],
        'GCA': ['A', 'four', 0],
        'GCG': ['A', 'four', 0],
        'CGT': ['R', 'four', 0],
        'CGC': ['R', 'four', 0],
        'CGG': ['R', 'four', 0],
        'CGA': ['R', 'four', 0],
        'AAT': ['N', 'two', 0],
        'AAC': ['N', 'two', 0],
        'GAT': ['D', 'two', 0],
        'GAC': ['D', 'two', 0],
        'TGT': ['C', 'two', 0],
        'TGC': ['C', 'two', 0],
        'CAA': ['Q', 'two', 0],
        'CAG': ['Q', 'two', 0],
        'GAA': ['E', 'two', 0],
        'GAG': ['E', 'two', 0],
        'GGT': ['G', 'four', 0],
        'GGC': ['G', 'four', 0],
        'GGA': ['G', 'four', 0],
        'GGG': ['G', 'four', 0],
        'CAT': ['H', 'two', 0],
        'CAC': ['H', 'two', 0],
        'ATT': ['I', 'two', 0],
        'ATC': ['I', 'two', 0],
        'ATA': ['M', 'two', 0],
        'ATG': ['M', 'two', 0],
        'TTA': ['L', 'six', 0],
        'TTG': ['L', 'six', 0],
        'CTT': ['L', 'six', 0],
        'CTC': ['L', 'six', 0],
        'CTA': ['L', 'six', 0],
        'CTG': ['L', 'six', 0],
        'AAA': ['K', 'two', 0],
        'AAG': ['K', 'two', 0],
        'TTT': ['F', 'two', 0],
        'TTC': ['F', 'two', 0],
        'CCT': ['P', 'four', 0],
        'CCC': ['P', 'four', 0],
        'CCA': ['P', 'four', 0],
        'CCG': ['P', 'four', 0],
        'TCT': ['S', 'eight', 0],
        'TCC': ['S', 'eight', 0],
        'TCA': ['S', 'eight', 0],
        'TCG': ['S', 'eight', 0],
        'AGT': ['S', 'eight', 0],
        'AGC': ['S', 'eight', 0],
        'AGA': ['S', 'eight', 0],
        'AGG': ['S', 'eight', 0],
        'ACT': ['T', 'four', 0],
        'ACC': ['T', 'four', 0],
        'ACA': ['T', 'four', 0],
        'ACG': ['T', 'four', 0],
        'TGG': ['W', 'two', 0],
        'TGA': ['W', 'two', 0],
        'TAT': ['Y', 'two', 0],
        'TAC': ['Y', 'two', 0],
        'GTT': ['V', 'four', 0],
        'GTC': ['V', 'four', 0],
        'GTA': ['V', 'four', 0],
        'GTG': ['V', 'four', 0],
        'TAA': ['*', 'two', 0],
        'TAG': ['*', 'two', 0],
        'XXX': ['_missing', 'none', 0]
    }
codontable9 = {
        'GCT': ['A', 'four', 0],
        'GCC': ['A', 'four', 0],
        'GCA': ['A', 'four', 0],
        'GCG': ['A', 'four', 0],
        'CGT': ['R', 'four', 0],
        'CGC': ['R', 'four', 0],
        'CGG': ['R', 'four', 0],
        'CGA': ['R', 'four', 0],
        'AAT': ['N', 'three', 0],
        'AAC': ['N', 'three', 0],
        'AAA': ['N', 'three', 0],
        'GAT': ['D', 'two', 0],
        'GAC': ['D', 'two', 0],
        'TGT': ['C', 'two', 0],
        'TGC': ['C', 'two', 0],
        'CAA': ['Q', 'two', 0],
        'CAG': ['Q', 'two', 0],
        'GAA': ['E', 'two', 0],
        'GAG': ['E', 'two', 0],
        'GGT': ['G', 'four', 0],
        'GGC': ['G', 'four', 0],
        'GGA': ['G', 'four', 0],
        'GGG': ['G', 'four', 0],
        'CAT': ['H', 'two', 0],
        'CAC': ['H', 'two', 0],
        'ATT': ['I', 'three', 0],
        'ATC': ['I', 'three', 0],
        'ATA': ['I', 'three', 0],
        'ATG': ['M', 'one', 0],
        'TTA': ['L', 'six', 0],
        'TTG': ['L', 'six', 0],
        'CTT': ['L', 'six', 0],
        'CTC': ['L', 'six', 0],
        'CTA': ['L', 'six', 0],
        'CTG': ['L', 'six', 0],
        'AAG': ['K', 'one', 0],
        'TTT': ['F', 'two', 0],
        'TTC': ['F', 'two', 0],
        'CCT': ['P', 'four', 0],
        'CCC': ['P', 'four', 0],
        'CCA': ['P', 'four', 0],
        'CCG': ['P', 'four', 0],
        'TCT': ['S', 'eight', 0],
        'TCC': ['S', 'eight', 0],
        'TCA': ['S', 'eight', 0],
        'TCG': ['S', 'eight', 0],
        'AGT': ['S', 'eight', 0],
        'AGC': ['S', 'eight', 0],
        'AGA': ['S', 'eight', 0],
        'AGG': ['S', 'eight', 0],
        'ACT': ['T', 'four', 0],
        'ACC': ['T', 'four', 0],
        'ACA': ['T', 'four', 0],
        'ACG': ['T', 'four', 0],
        'TGG': ['W', 'two', 0],
        'TGA': ['W', 'two', 0],
        'TAT': ['Y', 'two', 0],
        'TAC': ['Y', 'two', 0],
        'GTT': ['V', 'four', 0],
        'GTC': ['V', 'four', 0],
        'GTA': ['V', 'four', 0],
        'GTG': ['V', 'four', 0],
        'TAA': ['*', 'two', 0],
        'TAG': ['*', 'two', 0],
        'XXX': ['_missing', 'none', 0]
    }

def ENC_calc(cds, gcode):
    '''
    Calculate ENC value for a CDS sequence

    :param cds: coding sequence
    :param gcode: genetic code [int]: 1. Universal Genetic code; 2. Vertebrate Mitochondrial code; 5. Invertebrate Mitochondrial Code; 9. Echinoderm and Flatworm Mitochondrial Code
    :return: {"eq4Wright": 59.0038788051573, "eq2Sun": 52.18830453244027, "eq5Sun": 53.892713592316206}
    :rtype: dict
    '''
    dict_table = {
        1: codontable1,
        2: codontable2,
        5: codontable5,
        9: codontable9
    }
    codontable = dict_table[gcode]
    cds = cds.upper() #转换为大写的序列
    tmp_len = len(cds)
    tmp_enc = OrderedDict([('eq4Wright', "N/A"), ('eq2Sun', "N/A"), ('eq5Sun', "N/A")])
    if tmp_len % 3 != 0:
        print("The sequence is not the multiple of three")
        return tmp_enc
    for i in range(0, tmp_len, 3):
        codon = cds[i: i+3]
        if len(codon) != 3:
            continue
        if codon in codontable:
            codontable[codon][2] += 1
        else:
            codontable['XXX'][2] += 1
    tmp_gcbypos = gcbypos(codontable, False)
    tmp_enc["eq4Wright"] = str(calc_eq4wright(tmp_gcbypos[2]))
    tmp_enc["eq2Sun"] = str(calc_eq2sun(codontable, False))
    tmp_enc["eq5Sun"] = str(calc_eq5sun(codontable, False))
    return tmp_enc

def inversetable():
    inversetablecount = {
        'A': {'GCT': 0, 'GCC': 0, 'GCA': 0, 'GCG': 0},
        'R': {'CGT': 0, 'CGC': 0, 'CGA': 0, 'CGG': 0, 'AGA': 0, 'AGG': 0},
        'N': {'AAT': 0, 'AAC': 0},
        'D': {'GAT': 0, 'GAC': 0},
        'C': {'TGT': 0, 'TGC': 0},
        'Q': {'CAA': 0, 'CAG': 0},
        'E': {'GAA': 0, 'GAG': 0},
        'G': {'GGT': 0, 'GGC': 0, 'GGA': 0, 'GGG': 0},
        'H': {'CAT': 0, 'CAC': 0},
        'I': {'ATT': 0, 'ATC': 0, 'ATA': 0},
        'M': {'ATG': 0},
        'L': {'TTA': 0, 'TTG': 0, 'CTT': 0, 'CTC': 0, 'CTA': 0, 'CTG': 0},
        'K': {'AAA': 0, 'AAG': 0},
        'F': {'TTT': 0, 'TTC': 0},
        'P': {'CCT': 0, 'CCC': 0, 'CCA': 0, 'CCG': 0},
        'S': {'TCT': 0, 'TCC': 0, 'TCA': 0, 'TCG': 0, 'AGT': 0, 'AGC': 0},
        'T': {'ACT': 0, 'ACC': 0, 'ACA': 0, 'ACG': 0},
        'W': {'TGG': 0},
        'Y': {'TAT': 0, 'TAC': 0},
        'V': {'GTT': 0, 'GTC': 0, 'GTA': 0, 'GTG': 0},
        '*': {'TAA': 0, 'TGA': 0, 'TAG': 0}
    }
    return inversetablecount

def actgtable():
    actgtablecount = {
        'A': ['A', 0],
        'C': ['C', 0],
        'T': ['T', 0],
        'G': ['G', 0],
        'X': ['_missing', 0]
    }
    return actgtablecount


# Wright 1990 eqautions
def calc_fa(tmp):
    counts = [x[2] for x in tmp]
    na = sum(counts)
    return [((na * sum([(x / float(na)) ** 2 for x in counts])) - 1) / (na - 1), sum(counts)]


def calc_frc(fa, nrc):
    return 1 / float(nrc) * float(sum(fa))


# Latex function
# \widehat{N}_{c} = 2 + GC_{(3)} + (\frac{29}{GC^{2}_{(3)} + (1 - GC^{2}_{(3)})})
def calc_eq4wright(fgc):
    return 2 + float(fgc) + (29 / ((fgc ** 2) + ((1 - fgc) ** 2)))


# Sun 2012 equations
# FCF according to equation (2) without pseudocounts for eq2Sun
# F_{CF} = \sum_{i=1}^{m} (\frac {n_{i}}{n})^{2}
def calc_fcf(tmp):
    counts = [x[2] for x in tmp]
    na = sum(counts)
    if na == 0:
        return 'NA', 0
    return sum([(x / float(na)) ** 2 for x in counts]), sum(counts)


# FCF according to equation (3) using pseudocounts for eq5Sun
# F_{CF} = \sum_{i=1}^{m} (\frac {n_{i}+1}{n+m})^{2}
def calc_fcf_(tmp):
    counts = [x[2] for x in tmp]
    pseudocounts = [x + 1 for x in counts]
    na = sum(pseudocounts)
    return sum([(x / float(na)) ** 2 for x in pseudocounts]), sum(pseudocounts)


def calc_eq2sun(codoncounts, six2fourtwo):
    six_fcf = []
    six_nrc = []
    four_fcf = []
    four_nrc = []
    three_fcf = []
    three_nrc = []
    two_fcf = []
    two_nrc = []
    one_fcf = []
    one_nrc = []
    four_aa = []
    three_aa = []
    two_aa = []
    one_aa = []
    ncsix = None
    nc = None
    if not six2fourtwo:
        six_aa = ['S', 'R', 'L']
        four_aa = ['A', 'P', 'T', 'G', 'V']
        three_aa = ['I']
        two_aa = ['C', 'E', 'D', 'F', 'H', 'K', 'N', 'Q', 'Y']
        one_aa = ['M', 'W']
        for aa in six_aa:
            tmp_six = [codoncounts[x] for x in codoncounts.keys() if codoncounts[x][0] == aa]
            #print(tmp_six) #[['S', 'six', 18], ['S', 'six', 10], ['S', 'six', 7], ['S', 'six', 6], ['S', 'six', 8], ['S', 'six', 4]]
            six = calc_fcf(tmp_six)
            six_fcf.append(six[0])
            six_nrc.append(six[1])
        # setting codons with no counts to average value 1/6
        six_fcf = [float(1) / float(6) if x == 'NA' else x for x in six_fcf]
        ncsix = len(six_fcf) / (sum(six_fcf) / len(six_fcf))
    if six2fourtwo:
        four_aa = ['A', 'P', 'T', 'G', 'V', 'S', 'R', 'L']
        three_aa = ['I']
        two_aa = ['C', 'E', 'D', 'F', 'H', 'K', 'N', 'Q', 'Y', 'S_', 'R_', 'L_']
        one_aa = ['M', 'W']
    for aa in four_aa:
        tmp_four = [codoncounts[x] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        four = calc_fcf(tmp_four)
        four_fcf.append(four[0])
        four_nrc.append(four[1])
    # setting codons with no counts to average value 1/4
    four_fcf = [float(1) / float(4) if x == 'NA' else x for x in four_fcf]
    ncfour = len(four_fcf) / (sum(four_fcf) / len(four_fcf))
    for aa in three_aa:
        tmp_three = [codoncounts[x] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        three = calc_fcf(tmp_three)
        three_fcf.append(three[0])
        three_nrc.append(three[1])
    # setting codons with no counts to average value 1/3
    three_fcf = [float(1) / float(3) if x == 'NA' else x for x in three_fcf]
    ncthree = len(three_fcf) / (sum(three_fcf) / len(three_fcf))
    for aa in two_aa:
        tmp_two = [codoncounts[x] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        two = calc_fcf(tmp_two)
        two_fcf.append(two[0])
        two_nrc.append(two[1])
    # setting codons with no counts to average value 1/2
    two_fcf = [float(1) / float(2) if x == 'NA' else x for x in two_fcf]
    nctwo = len(two_fcf) / (sum(two_fcf) / len(two_fcf))
    for aa in one_aa:
        tmp_one = [codoncounts[x] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        one = calc_fcf(tmp_one)
        one_fcf.append(one[0])
        one_nrc.append(one[1])
    # setting codons with no counts to average value 1/1
    one_fcf = [float(1) / float(1) if x == 'NA' else x for x in one_fcf]
    ncone = len(one_fcf) / (sum(one_fcf) / len(one_fcf))
    if not six2fourtwo:
        nc = ncone + nctwo + ncthree + ncfour + ncsix
    if six2fourtwo:
        nc = ncone + nctwo + ncthree + ncfour
    return nc


# N_{c} = \frac {K_{1} \times \sum_{i}^{K_{1}} n_{i}}{\sum_{i=1}^{K_{i}}(n_{i} \times F_{CF_{i}})}
#  + \frac {K_{2} \times \sum_{i}^{K_{2}} n_{i}}{\sum_{i=1}^{K_{2}}(n_{i} \times F_{CF_{i}})}
#  + \frac {K_{3} \times \sum_{i}^{K_{3}} n_{i}}{\sum_{i=1}^{K_{3}}(n_{i} \times F_{CF_{i}})}
#  + \frac {K_{4} \times \sum_{i}^{K_{4}} n_{i}}{\sum_{i=1}^{K_{4}}(n_{i} \times F_{CF_{i}})}
#  + \frac {K_{6} \times \sum_{i}^{K_{6}} n_{i}}{\sum_{i=1}^{K_{6}}(n_{i} \times F_{CF_{i}})}
def calc_eq5sun(codoncounts, six2fourtwo):
    six_fcf_nrc = []
    four_fcf_nrc = []
    three_fcf_nrc = []
    two_fcf_nrc = []
    one_fcf_nrc = []
    four_aa = []
    three_aa = []
    two_aa = []
    one_aa = []
    ncsix = None
    nc = None
    if not six2fourtwo:
        six_aa = ['S', 'R', 'L']
        four_aa = ['A', 'P', 'T', 'G', 'V']
        three_aa = ['I']
        two_aa = ['C', 'E', 'D', 'F', 'H', 'K', 'N', 'Q', 'Y']
        one_aa = ['M', 'W']
        for aa in six_aa:
            tmp_six = [codoncounts[x] for x in codoncounts.keys() if codoncounts[x][0] == aa]
            six = calc_fcf_(tmp_six)
            six_fcf_nrc.append(six)
        ncsix = len(six_fcf_nrc) / (sum([x[0] * x[1] for x in six_fcf_nrc]) / (sum([x[1] for x in six_fcf_nrc])))
    if six2fourtwo:
        four_aa = ['A', 'P', 'T', 'G', 'V', 'S', 'R', 'L']
        three_aa = ['I']
        two_aa = ['C', 'E', 'D', 'F', 'H', 'K', 'N', 'Q', 'Y', 'S_', 'R_', 'L_']
        one_aa = ['M', 'W']
    for aa in four_aa:
        tmp_four = [codoncounts[x] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        four = calc_fcf_(tmp_four)
        four_fcf_nrc.append(four)
    ncfour = len(four_fcf_nrc) / (sum([x[0] * x[1] for x in four_fcf_nrc]) / (sum([x[1] for x in four_fcf_nrc])))
    for aa in three_aa:
        tmp_three = [codoncounts[x] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        three = calc_fcf_(tmp_three)
        three_fcf_nrc.append(three)
    ncthree = len(three_fcf_nrc) / (sum([x[0] * x[1] for x in three_fcf_nrc]) / (sum([x[1] for x in three_fcf_nrc])))
    for aa in two_aa:
        tmp_two = [codoncounts[x] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        two = calc_fcf_(tmp_two)
        two_fcf_nrc.append(two)
    nctwo = len(two_fcf_nrc) / (sum([x[0] * x[1] for x in two_fcf_nrc]) / (sum([x[1] for x in two_fcf_nrc])))
    for aa in one_aa:
        tmp_one = [codoncounts[x] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        one = calc_fcf_(tmp_one)
        one_fcf_nrc.append(one)
    ncone = len(one_fcf_nrc) / (sum([x[0] * x[1] for x in one_fcf_nrc]) / (sum([x[1] for x in one_fcf_nrc])))
    if not six2fourtwo:
        nc = ncone + nctwo + ncthree + ncfour + ncsix
    if six2fourtwo:
        nc = ncone + nctwo + ncthree + ncfour
    return nc


# Relative Synonymous Codon Usage
# RSCU_{i,j} = \frac{X_{i,j}}{\frac{1}{n_{i}} \times \sum_{j=1}^{n_{i}} X_{i,j}}
def calc_rscu(codoncounts, codontable):
    rscutable = codontable()
    for codon in rscutable.keys():
        aa = rscutable[codon][0]
        tmp_aa = [[x, codoncounts[x][2]] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        counts = [x[1] for x in tmp_aa]
        na = sum(counts)
        if na == 0:
            rscutable[codon][2] = 'NA'
        else:
            tmp_codon_na = [x[1] for x in tmp_aa if x[0] == codon][0]
            tmp_codon_freq = tmp_codon_na / float(na)
            tmp_codon_rscu = tmp_codon_freq * len(counts)
            rscutable[codon][2] = tmp_codon_rscu
    return rscutable


def gcbypos(codoncounts, six2fourtwo):
    aminoacids = ['A', 'C', 'E', 'D', 'G', 'F', 'I', 'H', 'K', 'M', 'L', 'N', 'Q', 'P', 'S', 'R', 'T', 'W', 'V', 'Y']
    if six2fourtwo:
        aminoacids = ['A', 'C', 'E', 'D', 'G', 'F', 'I', 'H', 'K', 'M', 'L', 'L_', 'N', 'Q', 'P', 'S', 'S_', 'R', 'R_',
                      'T', 'W', 'V', 'Y']
    gcone_gc = []
    gcone_sum = []
    gctwo_gc = []
    gctwo_sum = []
    gcthree_gc = []
    gcthree_sum = []
    gcone = None
    gctwo = None
    gcthree = None
    for aa in aminoacids:
        tmp_aa_one = [[x[0], codoncounts[x][2]] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        tmp_aa_two = [[x[1], codoncounts[x][2]] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        tmp_aa_three = [[x[2], codoncounts[x][2]] for x in codoncounts.keys() if codoncounts[x][0] == aa]
        tmp_aa_one_sum = sum([x[1] for x in tmp_aa_one])
        tmp_aa_two_sum = sum([x[1] for x in tmp_aa_two])
        tmp_aa_three_sum = sum([x[1] for x in tmp_aa_three])
        gc_one = sum([x[1] for x in tmp_aa_one if x[0] == 'G' or x[0] == 'C'])
        gcone_sum.append(tmp_aa_one_sum)
        gcone_gc.append(gc_one)
        gc_two = sum([x[1] for x in tmp_aa_two if x[0] == 'G' or x[0] == 'C'])
        gctwo_sum.append(tmp_aa_two_sum)
        gctwo_gc.append(gc_two)
        gc_three = sum([x[1] for x in tmp_aa_two if x[0] == 'G' or x[0] == 'C'])
        gcthree_sum.append(tmp_aa_three_sum)
        gcthree_gc.append(gc_three)
    if float(sum(gcone_gc)) == 0 and float(sum(gcone_sum)) == 0:
        print('GCone_gc and GCone_sum zero\n')
        gcone = 0
    if float(sum(gcone_gc)) != 0 or float(sum(gcone_sum)) != 0:
        gcone = float(sum(gcone_gc)) / float(sum(gcone_sum))
    if float(sum(gctwo_gc)) == 0 and float(sum(gctwo_sum)) == 0:
        print('GCtwo_gc and GCtwo_sum zero\n')
        gctwo = 0
    if float(sum(gctwo_gc)) != 0 or float(sum(gctwo_sum)) != 0:
        gctwo = float(sum(gctwo_gc)) / float(sum(gctwo_sum))
    if float(sum(gcthree_gc)) == 0 and float(sum(gcthree_sum)) == 0:
        print('GCthree_gc and GCthree_sum zero\n')
        gcthree = 0
    if float(sum(gcthree_gc)) != 0 or float(sum(gcthree_sum)) != 0:
        gcthree = float(sum(gcthree_gc)) / float(sum(gcthree_sum))
    return [gcone, gctwo, gcthree]


if __name__ == '__main__':
    ENC_calc('''ATGCAGAAGCGAATAGCCTTGTCGTTTCCAGAAGAGGTACTAGAGCATGTGTTCTCGTTTATTCAGCTGGATAAGGATAGGAACTCAGTCTCTCTGGTGTGCAAGTCATGGTACGAGATCGAGCGGTGGTGCAGGAGGAAAGTCTTCATCGGGAACTGCTACGCCGTGAGTCCAGCGACGGTGATTAGGAGGTTCCCGAAAGTGAGATCCGTGGAGCTTAAAGGAAAACCTCACTTTGCTGACTTTAATTTGGTACCTGACGGATGGGGAGGTTACGTGTATCCATGGATTGAGGCCATGTCTTCGTCTTACACGTGGCTTGAAGAGATAAGGCTGAAGAGGATGGTGGTCACCGACGATTGCTTGGAGCTCATAGCCAAGTCTTTTAAGAATTTTAAGGTTCTTGTGCTTTCTTCCTGCGAAGGCTTCTCCACCGATGGTCTCGCTGCTATCGCTGCCACTTGCAGGAATCTGAAAGAGCTTGACTTACGAGAGAGTGATGTTGACGACGTTAGTGGCCACTGGCTTAGCCATTTCCCAGATACATACACTTCTTTGGTATCACTCAATATATCTTGCTTAGCATCTGAGGTCAGTTTCTCTGCTCTGGAAAGGCTGGTGACTAGGTGTCCCAATCTCAAGTCTCTCAAGCTTAACCGAGCTGTTCCACTTGAAAAATTGGCTACTTTACTTCAAAGAGCACCTCAATTGGAGGAATTGGGCACTGGTGGGTACACTGCAGAAGTGCGACCAGATGTTTACTCTGGTTTATCTGTAGCGCTCTCTGGGTGCAAGGAATTGAGGTGCTTATCTGGATTTTGGGATGCTGTTCCTGCCTATCTTCCAGCAGTTTATTCGGTTTGCAGTCGGCTTACAACTTTGAATCTGAGTTATGCAACAGTCCAGAGCTATGATCTTGTCAAGCTTCTTTGTCAATGCCCTAAACTGCAGCGCCTCTGGGTGCTTGACTACATCGAGGATGCTGGTCTTGAGGTGCTTGCTTCAACCTGCAAGGACCTACGCGAGCTGAGAGTGTTTCCGTCCGAGCCTTTTGTCATGGAACCAAATGTGGCATTGACGGAACAGGGGCTTGTCTCCGTCTCCATGGGCTGTCCAAAACTCGAGTCGGTTCTCTACTTCTGCCGTCAAATGACCAATGCTGCATTGATAACCATTGCTAGGAACCGTCCCAACATGACTCGCTTCCGTTTGTGCATCATTGAGCCAAAAGCCCCAGACTATCTGACTCTAGAGCCACTGGATATTGGATTTGGAGCCATAGTAGAGCACTGCAAGGATCTCCGTCGCCTCTCTCTATCTGGCCTCTTGACCGACAAGGTTTTTGAATACATTGGGACATATGCCAAGAAGATGGAAATGCTCTCAGTGGCATTTGCAGGAGACAGTGACTTAGGCATGCATCATGTTTTGTCCGGGTGCGATAGCTTGAGGAAACTAGAGATAAGGGACTGCCCGTTTGGAGACAAGGCGCTTTTGGCCAATGCTTCAAAGCTGGAGACAATGCGATCCCTTTGGATGTCTTCTTGTTCCGTGAGTTTTGGAGCCTGCAAGTTACTAGGACAGAAGATGCCAAAGCTGAATGTGGAAGTCATCGATGAACGGGGTGCACCGGACTCGAGACCAGAGAGCTGCCCTGTTGAGAGAGTCTTCATATACCGAACAGTGGCTGGTCCTCGATTTGACATGCCTGGCTTCGTCTGGAACATGGACCAAGACTCAACAATGAGGTTTTCCAGGCAAATCATTACTACTAACGGATTATAA''', 1)
