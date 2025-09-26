#-----------------------------------------------------------------------------
# Pyr8s - Divergence Time Estimation
# Copyright (C) 2021  Patmanidis Stefanos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------


"""
Parse a NEXUS file and execute rate commands.
Is less of a mess right now.
"""

import dendropy
from . import core

_SEPARATOR = '-' * 50

def parse_value(tokenizer):
    token = tokenizer.require_next_token_ucase()
    if token != '=':
        raise ValueError("Expecting '=' token, but instead found '{}'".format(token))
    token = tokenizer.require_next_token_ucase()
    return token

def parse_rates(tokenizer, analysis, run=False):
    results = None
    tokenizer.skip_to_semicolon()
    token = tokenizer.next_token_ucase()
    while not (token == 'END' or token == 'ENDBLOCK') \
        and not tokenizer.is_eof() \
        and not token==None:
        if token == 'BLFORMAT':
            token = tokenizer.require_next_token_ucase()
            format = None
            nsites = None
            while not (token == ';'):
                if token == 'NSITES':
                    token = parse_value(tokenizer)
                    print('* NSITES: {0}'.format(token))
                    nsites = int(float(token))
                elif token == 'LENGTHS':
                    token = parse_value(tokenizer)
                    print('* LENGTHS: {0}'.format(token))
                    if token == 'TOTAL':
                        format = 'total'
                    elif token == 'PERSITE':
                        format = 'persite'
                    elif token == 'GUESS':
                        format = 'guess'
                    else:
                        raise ValueError("BLFORMAT.LENGTHS: Unrecognised vale: '{}'".format(token))
                elif token == 'ROUND':
                    token = parse_value(tokenizer)
                    print('* ROUND: {0}'.format(token))
                    if token == 'NO':
                        analysis.param.branch_length.round = False
                    elif token == 'YES':
                        analysis.param.branch_length.round = True
                    else:
                        raise ValueError("BLFORMAT.ROUND: Unrecognised vale: '{}'".format(token))
                elif token == 'ULTRAMETRIC':
                    token = parse_value(tokenizer)
                    print('* ULTRAMETRIC: {0}'.format(token))
                    if token == 'NO':
                        pass
                    elif token == 'YES':
                        raise ValueError("BLFORMAT.ULTRAMETRIC: YES is not an option")
                    else:
                        raise ValueError("BLFORMAT.ULTRAMETRIC: Unrecognised vale: '{}'".format(token))
                else:
                    raise ValueError("BLFORMAT: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            if format is None:
                raise ValueError("BLFORMAT: Expected parameter LENGTHS not given.")
            elif format == 'persite':
                if nsites is None:
                    raise ValueError("BLFORMAT: Expected parameter NSITES not given.")
            else:
                if nsites is not None:
                    raise ValueError("BLFORMAT: Unexpected parameter NSITES.")
            analysis.param.branch_length.format = format
            analysis.param.branch_length.nsites = nsites

        elif token == 'COLLAPSE':
            print('* COLLAPSE: automatic')
            tokenizer.skip_to_semicolon()
        elif token == 'PRUNE':
            print('* PRUNE: automatic')
            tokenizer.skip_to_semicolon()
        elif token == 'MRCA':
            ancestor = tokenizer.require_next_token()
            children = []
            token = tokenizer.require_next_token()
            while not (token == ';') \
                and not tokenizer.is_eof() \
                and not token==None:
                children.append(token)
                token = tokenizer.require_next_token()
            try:
                analysis.tree.label_mrca(ancestor, children)
            except KeyError:
                raise ValueError("MRCA: Invalid children: {}".format(children))
            print("* MRCA: '{0}' of {1}.".format(ancestor,children))
        elif token == 'FIXAGE':
            token = tokenizer.require_next_token_ucase()
            node, age = None, None
            print('* FIXAGE:', end=' ')
            while not (token == ';'):
                if token == 'TAXON':
                    token = parse_value(tokenizer)
                    node = analysis.tree.find_node_with_taxon(
                        lambda x: x.label.upper() == token)
                    print('TAXON={0}'.format(token), end=' ')
                elif token == 'AGE':
                    token = parse_value(tokenizer)
                    age = int(float(token))
                    print('AGE={0}'.format(token), end=' ')
                else:
                    raise ValueError("FIXAGE: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            if age is not None:
                node.fix = age
            else:
                node.fix = node.age
            node.max = None
            node.min = None
            print('')
        elif token == 'UNFIXAGE':
            token = tokenizer.require_next_token_ucase()
            node = None
            print('* UNFIXAGE:', end=' ')
            while not (token == ';'):
                if token == 'TAXON':
                    token = parse_value(tokenizer)
                    node = analysis.tree.find_node_with_taxon(
                        lambda x: x.label.upper() == token)
                    print('TAXON={0}'.format(token), end=' ')
                else:
                    raise ValueError("UNFIXAGE: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            node.fix = None
            print('')
        elif token == 'CONSTRAIN':
            token = tokenizer.require_next_token_ucase()
            node, min, max = None, None, None
            all = False
            print('* CONSTRAIN:', end=' ')
            while not (token == ';'):
                if token == 'TAXON':
                    token = parse_value(tokenizer)
                    node = analysis.tree.find_node_with_taxon(
                        lambda x: x.label.upper() == token)
                    print('TAXON={0}'.format(token), end=' ')
                elif token == 'MAX AGE' or token == 'MAXAGE':
                    token = parse_value(tokenizer)
                    if token != 'NONE':
                        max = int(float(token))
                    print('MAX_AGE={0}'.format(token), end=' ')
                elif token == 'MIN AGE' or token == 'MINAGE':
                    token = parse_value(tokenizer)
                    if token != 'NONE':
                        min = int(float(token))
                    print('MIN_AGE={0}'.format(token), end=' ')
                elif token == 'REMOVE':
                    token = parse_value(tokenizer)
                    print('REMOVE={0}'.format(token), end=' ')
                    if token != 'ALL':
                        raise ValueError("CONSTRAIN.REMOVE: Expected 'all': '{}'".format(token))
                else:
                    raise ValueError("CONSTRAIN: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            if all:
                for node in analysis.tree.preorder_node_iter():
                    node.max = None
                    node.min = None
            else:
                node.fix = None
                node.max = max
                node.min = min
            print('')
        elif token == 'DIVTIME':
            token = tokenizer.require_next_token_ucase()
            print(_SEPARATOR)
            print('* DIVTIME:', end=' ')
            while not (token == ';'):
                if token == 'METHOD':
                    token = parse_value(tokenizer)
                    if token == 'NPRS' or token == 'NP':
                        analysis.param.method.method = 'nprs'
                    else:
                        raise ValueError("DIVTIME: Unrecognised method: '{}'".format(token))
                    print('METHOD={0}'.format(token), end=' ')
                elif token == 'ALGORITHM':
                    token = parse_value(tokenizer)
                    if token == 'POWELL' or token == 'PL':
                        analysis.param.algorithm.algorithm = 'powell'
                    else:
                        raise ValueError("DIVTIME: Unrecognised algorithm: '{}'".format(token))
                    print('ALGORITHM={0}'.format(token), end=' ')
                else:
                    raise ValueError("DIVTIME: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            print('\n* BEGIN ANALYSIS: \n')
            if run:
                results = analysis.run()
        elif token == 'SET':
            token = tokenizer.require_next_token_ucase()
            while not (token == ';'):
                if token == 'NUM TIME GUESSES':
                    token = parse_value(tokenizer)
                    print('* NUM_TIME_GUESSES: {0}'.format(token))
                    analysis.param.general.number_of_guesses = int(float(token))
                elif token == 'NPEXP':
                    token = parse_value(tokenizer)
                    print('* NPEXP: {0}'.format(token))
                    analysis.param.method.exponent = int(float(token))
                elif token == 'PENALTY':
                    token = parse_value(tokenizer)
                    print('* PENALTY: {0}'.format(token))
                    if token == 'ADD':
                        analysis.param.method.logarithmic = False
                    elif token == 'LOG':
                        analysis.param.method.logarithmic = True
                    else:
                        raise ValueError("PENALTY: Unrecognised option: '{}'".format(token))
                elif token == 'PERTURB_FACTOR':
                    token = parse_value(tokenizer)
                    print('* PERTURB_FACTOR: {0}'.format(token))
                    analysis.param.general.perturb_factor = float(token)
                elif token == 'MAXITER':
                    #! for minimize.powell
                    pass
                elif token == 'MAXBARRIERITER':
                    token = parse_value(tokenizer)
                    print('* MAXBARRIERITER: {0}'.format(token))
                    analysis.param.barrier.max_iterations = int(float(token))
                elif token == 'BARRIERMULTIPLIER':
                    token = parse_value(tokenizer)
                    print('* BARRIERMULTIPLIER: {0}'.format(token))
                    analysis.param.barrier.multiplier = float(token)
                elif token == 'INITBARRIERFACTOR':
                    token = parse_value(tokenizer)
                    print('* INITBARRIERFACTOR: {0}'.format(token))
                    analysis.param.barrier.initial_factor = float(token)
                else:
                    raise ValueError("SET: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
        elif token == 'SHOWAGE':
            tokenizer.skip_to_semicolon()
            if run:
                print('* SHOWAGE:')
                if results is not None:
                    results.print()
                else:
                    raise ValueError("SHOWAGE: Called before DIVTIME, nothing to show.")
        elif token == 'SCALAR':
            tokenizer.skip_to_semicolon()
            print('* SCALAR:')
            analysis.param.general.scalar = True
        elif token == 'DESCRIBE':
            token = tokenizer.require_next_token_ucase()
            while not (token == ';'):
                if token == 'PLOT':
                    token = parse_value(tokenizer)
                    if run:
                        if token == 'CLADOGRAM':
                            print('* {}'.format(token))
                            pass
                        if token == 'PHYLOGRAM':
                            print('* {}'.format(token))
                            pass
                        if token == 'CHRONOGRAM':
                            print('* {} (unweighted branches):'.format(token))
                            core.print_tree(results.chronogram)
                        if token == 'RATOGRAM':
                            print('* {}'.format(token))
                            pass
                        if token == 'TREE DESCRIPTION':
                            print('* {}:'.format(token))
                            print(results.chronogram.as_string(
                                schema="newick",suppress_internal_node_labels=True))
                        if token == 'PHYLO DESCRIPTION':
                            print('* {}'.format(token))
                            pass
                        if token == 'RATO DESCRIPTION':
                            print('* {}'.format(token))
                            pass
                elif token == 'PLOTWIDTH':
                    print('* {}'.format(token))
                    pass
                else:
                    raise ValueError("DESCRIBE: Unrecognised option: '{}'".format(token))
                token = tokenizer.require_next_token_ucase()
            # plot happens here
            pass
        elif token == ';':
            print('OOPS, missed a colon')
        else:
            raise ValueError("RATES: Unrecognised command: '{}'".format(token))
        token = tokenizer.next_token_ucase()


def from_file_nexus(file, run=False):
    """First get the tree and create RateAnalysis, then find and parse RATES commands"""
    treelist = dendropy.TreeList.get(path=file, schema="nexus",
        suppress_internal_node_taxa=True, suppress_leaf_node_taxa=False)
    #! if more than one trees are present: do something
    if len(treelist) > 0:
        tree = treelist[0]
    print("> TREE: from '{}'".format(file))
    # tree.print_plot()
    analysis = core.RateAnalysis(tree)
    file = open(file,'r')
    tokenizer = dendropy.dataio.nexusprocessing.NexusTokenizer(file)
    token = tokenizer.next_token_ucase()
    if not token == '#NEXUS':
        raise ValueError('Not nexus file!')
    while not tokenizer.is_eof():
        token = tokenizer.next_token_ucase()
        while token != None and token != 'BEGIN' and not tokenizer.is_eof():
            token = tokenizer.next_token_ucase()
        token = tokenizer.next_token_ucase()
        if token == 'RATES' or token=='R8S':
            print('> RATES BLOCK:')
            print(_SEPARATOR)
            parse_rates(tokenizer, analysis, run=run)
        else:
            while not (token == 'END' or token == 'ENDBLOCK') \
                    and not tokenizer.is_eof() \
                    and not token==None:
                tokenizer.skip_to_semicolon()
                token = tokenizer.next_token_ucase()
    return analysis

def from_tree(newick):
    analysis = core.RateAnalysis(newick)
    analysis.param.general.scalar = True
    analysis.param.branch_length.format = 'guess'
    return analysis

def from_file_newick(file):
    try:
        newick = dendropy.Tree.get(path=file, schema='newick',
            suppress_internal_node_taxa=True, suppress_leaf_node_taxa=False)
        analysis = from_tree(newick)
    except Exception as exception:
        raise RuntimeError('Error reading Newick file: {0}\n{1}'.
            format(file, str(exception)))
    return analysis

def from_file(file, run=False):
    """Open and parse a Nexus/Newick file, run analysis if `run` is set"""
    with open(file) as input:
        line = input.readline()
        is_nexus = (line.strip() == "#NEXUS")
    if is_nexus:
        # Allow analysis to be run according to nexus rates commands
        analysis = from_file_nexus(file, run=run)
    else:
        analysis = from_file_newick(file)
    # Force analysis if requested
    if run is True and analysis.results is None:
        analysis.run()
    return analysis


def quick(tree=None, file=None, format='guess', nsites=None, scalar=True):
    """
    Run analysis without explicitly setting parameters and calibrations.

    Parameters
    ----------
    Exactly one of the following must be specified:

        tree : string
            The tree to be analyzed in Newick format.
        file : string
            The path of the file to be analyzed in Nexus format.

    If a tree was given, the following optional keywords are supported:

        format: string
            If 'persite' then nsites must be provided.
            If 'total' then assume the branch lengths are given in
            units of total numbers of substitutions.
            If 'guess' then try to guess nsites based on given tree lengths.
        nsites : int
            The number of sites in sequences that branch
            lengths on input trees were calculated from.
        scalar : bool
            If |True| then do a scalar analysis by setting root age to 100.0.
            If |False| then assume the given tree is extended with all
            calibrations needed for convergence.

    If a file was given, ignore all optional arguments and parse the file.

    Returns
    -------
    string
        The calculated chronogram in newick form, that is:
        an ultrametric phylogenetic tree in which branch lengths
        correspond to time durations along branches.

    Example
    -------
    parse.quick(my_tree).print()
    """
    if tree is not None:
        dendrotree = dendropy.Tree.get(data=tree, schema="newick",
            suppress_internal_node_taxa=True, suppress_leaf_node_taxa=False)
        analysis = core.RateAnalysis(dendrotree)
        analysis.param.general.scalar = scalar
        analysis.param.branch_length.format = format
        analysis.param.branch_length.nsites = nsites
    elif file is not None:
        analysis = from_file(file, run=False)
    else:
        raise TypeError("Must specify one of: 'tree' or 'file'")
    res = analysis.run()
    chrono = res.chronogram.as_string(schema='newick', suppress_rooting=True)
    return chrono
