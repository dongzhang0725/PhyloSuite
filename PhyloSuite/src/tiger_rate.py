import pickle as cPickle
import sys
import os
import re


def check_opts(opts):
    if opts.input is None:
        die_with_help()
    if not os.path.exists(os.path.realpath(opts.input)):
        die_with_message("Cannot find input file '%s'" % opts.input)

    if opts.reference is None:
        opts.reference = opts.input

    if not os.path.exists(os.path.realpath(opts.reference)):
        die_with_message("Cannot find reference file '%s'" % opts.reference)

    # if opts.run_ptp is not None:
    #     if opts.rands is not None:
    #         try:
    #             int(opts.rands)
    #         except ValueError:
    #             die_with_message("Invalid -z option '%s'. Please provide an integer")
    #     if opts.p_value is not None:
    #         try:
    #             float(opts.p_value)
    #         except ValueError:
    #             die_with_message("Invalid -p option '%s'. Please provide a floating point number")

# @profile
def rate_sites(pat_counts, ref_counts, fileBase, queue):
    rate_d = pat_counts.copy()
    keys = pat_counts.keys()
    for num, k in enumerate(keys):
        if "|" not in k:
            rate_d[k]["rate"] = 1.0
        else:
            rate_d[k]["rate"] = site_rate(k, ref_counts)
        progress = 15 + ((num+1)/len(keys))*80
        queue.put((fileBase, progress))

    # rates = []
    # for p in pat_counts.keys():
    #   rates.append(rate_d[p])

    return rate_d


def site_rate(a, ref_counts):
    pat_rates = []
    dividand = 0

    patA = set_pattern(a)

    for p in ref_counts.keys():
        sub = 0
        if '|' in p:       # only score against non-constant sites
            patB = set_pattern(p)
            pr = 1.0 - score(patA, patB)

            reps = ref_counts[p]["count"]
            if a == p:
                reps -= 1

            for i in range(reps):
                # print "%s v %s = %f" % (patA, p, pr)
                pat_rates.append(pr)
                dividand += 1

    # print "%f/%d = %f" % (sum(pat_rates), dividand,
    # (sum(pat_rates)/dividand))
    return 1.0 - (sum(pat_rates) / dividand)


def score(a, b):
    found = 0
    sets = len(b)

    for set_b in b:
        for set_a in a:
            if set_b.issubset(set_a):
                found += 1
                break

    return float(found) / sets


def set_pattern(p):
    return [set([int(y) for y in x.split(',')]) for x in p.split('|')]


def sort(rates, patterns):
    if len(rates) != len(patterns):
        # print "Something's weird here. len(rates) != len(patterns)"
        raise Exception("Something's weird here. len(rates) != len(patterns)")
        sys.exit(1)

    rate_d = {}
    for i, r in enumerate(rates):
        rate_d[i] = r

    sort_order = sorted(rate_d, key=rate_d.get, reverse=True)

    return [[rates[o] for o in sort_order], [patterns[p] for p in sort_order]]


def rate_list(pats):
    rates = {}
    for k in pats.keys():
        r = pats[k]['rate']
        for s in pats[k]['sites']:
            rates[s] = r
    # print(rates)
    # rate_list = []
    # for i in range(len(pats)+1):
    #     rate_list.append(rates[i])

    return rates

# @profile
def run_rates(input_, exportPath, reference_, rate_list_yes, fileBase, queue):
    # check_opts(opts)
    with open(input_, 'rb') as in_h:
        pat_counts = cPickle.load(in_h)
    if not reference_:
        ref_counts = pat_counts.copy()
    else:
        with open(reference_, 'rb') as ref_h:
            ref_counts = cPickle.load(ref_h)
    queue.put((fileBase, 15))

    rates = rate_sites(pat_counts, ref_counts, fileBase, queue)
    prefix = os.path.splitext(os.path.basename(input_))[0]

    # write out .gr pickle
    gr_file = exportPath + os.sep + "%s.gr" % prefix
    with open(gr_file, 'wb') as fh:
        cPickle.dump(rates, fh)

    # write rate list if required
    if rate_list_yes:
        dict_site_rate = rate_list(rates)
        rl = exportPath + os.sep + "%s.rates.csv" % prefix
        rlh = open(rl, 'w')
        rlh.write("\n".join(
            ["%d,%f" % (site + 1, dict_site_rate[site]) for site in dict_site_rate]))
        rlh.close()
    queue.put((fileBase, 98))
    # do PTP test if required
    # if opts.run_ptp:
    #   continue
    return gr_file


def die_with_help():
    print("""
****************
TIGER  v2.0 Help:
****************

tiger rate Options:

    -i|input            Specify input file. File should be in .ti format.

    -r|reference        Specify reference sequence (.ti). -i file is used as default if none is provided.

    -o|output           Specify prefix name for output files.

    -rl|rate_list       A list of the rate at each site may be optionally written to a specified
                        file.
                        -rl <file.txt> : writes list of the rates at each site to file.txt.

    -ptp                Specifies that a PTP test should be run.
                        * Note * this option has a huge effect on running time!

    -z|randomisations   Number of randomisations to be used for the PTP test.
                        -z <int>: each site will be randomised <int> times. <int> is a whole number.

                        Default is 100

    -p|p_value          Specify p-value which denotes significance in PTP test.
                        -p <float>: site will be denoted as significant if p-value is better than <float>.
                        <float> is a floating point number.

                        Default is 0.05

    -pl|pval_list       Write a list of p-values to a specified file.
                        -pl <file.txt>: writes list of p-values for each site to file.txt.

    Examples:
        1. Calculate rates for file test.ref.ti against itself, with a list of rates:
            tiger rate -i test.ref.ti -rl
        2. Calculate rates for file test.0.ti against test.ref.ti with a PTP test and a list of p values
            tiger rate -i test.0.ti -r test.ref.ti -ptp -pl

     """)
    sys.exit(1)


def die_with_message(message):
    print(message)
    sys.exit(1)

if __name__ == "__main__":
    # input_, exportPath, reference_, rate_list_yes
    run_rates(r"F:\G\desktop\新建文件夹\新建文件夹\ND5_mafft_NT_removed_chars_gb.ref.ti",
              r"F:\G\desktop\新建文件夹\新建文件夹",
              "", True)