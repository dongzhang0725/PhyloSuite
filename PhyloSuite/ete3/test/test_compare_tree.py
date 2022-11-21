#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
description goes here
'''
from ete3 import Tree

def read_tree(file):
    flag = False
    for format in list(range(10)) + [100]:
        try:
            tre = Tree(file, format=format)
            flag=True
            break
        except: pass
        try:
            tre = Tree(file, format=format, quoted_node_names=True)
            flag=True
            break
        except: pass
    if not flag:
        return
    return tre

ref_tree = read_tree(r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\myWorkPlace\GenBank_File\test_extract\trees\compare_trees\iqtree.treefile")
tree = read_tree(r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\myWorkPlace\GenBank_File\test_extract\trees\compare_trees\iqtree2.treefile")

result = ref_tree.compare(tree, unrooted=True)

print(list(result.keys()), result)
