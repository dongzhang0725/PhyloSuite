#!/usr/bin/env python

import pickle as cPickle
import re
import sys
import os
import math

from src.factory import Parsefmt
from src.tiger_rate import run_rates
from src.tiger_output import run_output
# from collections import OrderedDict

def check_opts(opts):
    if opts.input is None:
        die_with_help()
    if not file_exists(opts.input):
        die_with_message("Cannot find file '%s'" % opts.input)
    if opts.unknowns is not None:
        if len(opts.unknowns) < 1:
            die_with_message("Invalid -u option.")
    if opts.split is not None:
        try:
            int(opts.split)
        except ValueError:
            die_with_message(
                "Please provide an integer value for --split option")


def file_exists(f):
    return os.path.exists(os.path.realpath(f))


def check_aln(seqs):
    base = len(seqs[0])
    for s in seqs:
        if len(s) != base:
            die_with_message(
                "Sequences are not of even lengths. Please ensure the data is aligned.")
    return base


def parse_fasta(input):
    data = []
    fa_str = "\n".join(open(input).readlines())
    parts = fa_str.split(">")
    parts = parts[1:]

    for p in parts:
        spl = p.split("\n")
        name = spl.pop(0)
        seq = ""
        for s in spl:
            if re.search(r"\w", s):
                seq += s.rstrip()
        data.append([name, seq])

    return data


def patterns(data):
    seqs = [i[1] for i in data]

    l = len(seqs[0])
    sites = []
    for x in range(l):
        s = [y[x] for y in seqs]
        sites.append(s)

    return [site_pattern(s) for s in sites]


def site_pattern(site):
    pat = {}
    order = []
    for i, base in enumerate(site):
        try:
            pat[base].append(i)
        except KeyError:
            pat[base] = [i]
            order.append(base)

    return "|".join([",".join([str(x) for x in pat[o]]) for o in order])


def pattern_counts_sets(pats):
    uniq = {}
    for x, p in enumerate(pats):
        try:
            uniq[p]["count"] += 1
        except KeyError:
            uniq[p] = {"count": 1}

        try:
            uniq[p]["sites"].append(x)
        except KeyError:
            uniq[p]["sites"] = [x]

    return uniq

# @profile
def run_index(input_, exportPath, reference_,
              rate_list_yes, format_, mask,
               bin_n, excluded_bins, included_bins, split_=1):
    fileBase = os.path.basename(input_)
    # check_opts(opts)
    parsefmt = Parsefmt()
    dict_taxon = parsefmt.readfile(input_)
    run_index.queue.put((fileBase, 3))
    seq_data = [[taxon, dict_taxon[taxon]] for taxon in dict_taxon]
    seq_len = check_aln(seq_data)
    pats = patterns(seq_data)
    run_index.queue.put((fileBase, 7))

    uniq_pats = pattern_counts_sets(pats)

    prefix = os.path.splitext(os.path.basename(input_))[0]
    out = exportPath + os.sep + "%s.ref.ti" % prefix
    with open(out, 'wb') as fh:
        #cPickle.dump(seq_data, fh)
        cPickle.dump(uniq_pats, fh)

    if split_ > 1:
        write_subsets(uniq_pats, int(split_), prefix, exportPath)
    run_index.queue.put((fileBase, 12))
    ## rates
    gr_file = run_rates(out, exportPath, reference_, rate_list_yes, fileBase, run_index.queue)
    ## output
    run_output(gr_file, input_, exportPath, format_, mask, bin_n, excluded_bins, included_bins)
    run_index.queue.put((fileBase, 100))

def write_subsets(pats, num, prefix, exportPath):
    step = math.ceil(float(len(pats)) / num)
    c = 1
    subs = []

    pat_keys = list(pats.keys())
    while len(pat_keys) > 0:
        subs.append({})

        for x in range(int(step)):
            try:
                pat = pat_keys.pop()
                subs[-1][pat] = pats[pat]
                if len(pat_keys) < step:
                    pat = pat_keys.pop()
                    subs[-1][pat] = pats[pat]
            except IndexError:
                break

    for i in range(len(subs)):
        with open(exportPath + os.sep + "%s.%d.ti" % (prefix, i), 'wb') as fh:
            cPickle.dump(subs[i], fh)


def die_with_help():
    print("""
****************
TIGER  v2.0 Help:
****************

tiger index Options:

    -i|input    Specify input file. File must be in FastA format and must be aligned prior.
                Datasets with uneven sequence lengths will return an error.

    -s|split    Split dataset across multiple files to run simultaneously. Takes int argument.

    -o|output   Specify the prefix name of output files.

    -u|unknowns Specify unknown characters in the alignment. Unknown characters are omitted from
                site patterns and so are not considered in the analysis.
                -u ?,-,*: defines ?, - and * as unknown characters. (*Be sure to put only a comma
                between characters, NO SPACE!!)

                Default is ? only

    Examples:
        1. Generate a .tgr file for complete sequence named full_seq.tgr & set unknowns to ? and - :
                tiger index -i my_file.aln -o full_seq -u ?,-

        2. Generate 10 subsets of the data with an output prefix of tiger_split and a reference:
                tiger index -i my_file.aln -o tiger_split -s 10
            ** Results in files named tiger_split.1.tgr, tiger_split.2,tgr, and so on, along with
               tiger_split.ref.tgr

     """)
    sys.exit(1)


def die_with_message(message):
    print(message)
    sys.exit(1)

if __name__ == "__main__":
    # from factory import Parsefmt
    # from tiger_rate import run_rates
    # from tiger_output import run_output
    run_index(r"F:\G\desktop\新建文件夹\新建文件夹\ND5_mafft_NT_removed_chars_gb.fasta",
              r"F:\G\desktop\新建文件夹\新建文件夹",
              "", True, 0, True,
               10, [9,10], [], split_=1)