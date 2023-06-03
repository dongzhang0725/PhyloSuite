from PyQt5 import QtCore
from collections import OrderedDict

init_sequence_type = OrderedDict([('general', OrderedDict([('Features to be extracted', ['rRNA', 'CDS', 'tRNA', 'misc_feature']),
                                                   ('Qualifiers to be recognized (rRNA):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (CDS):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (tRNA):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (misc_feature):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (all):', [
                                                       'gene', 'product', 'note']),
                                                   ('Names unification', [['Old Name', 'New Name'],
                                                                          ["CO1", "cox1"]
                                                                          ]),
                                                    ('extract all features', True)])),
                                  ('Mitogenome', OrderedDict([('Features to be extracted', ['rRNA', 'CDS', 'tRNA', 'misc_feature']),
                                                              ('Qualifiers to be recognized (rRNA):', [
                                                               'product', 'gene', 'note']),
                                                              ('Qualifiers to be recognized (misc_feature):', [
                                                               'product', 'gene', 'note']),
                                                              ('Names unification', [['Old Name', 'New Name'],
                                                                                     [
                                                                                         '12S Ribosomal RNA', 'rrnS'],
                                                                                     [
                                                                                         '12S ribosomal RNA', 'rrnS'],
                                                                                     ['12S rRNA',
                                                                                         'rrnS'],
                                                                                     ['12s rRNA',
                                                                                         'rrnS'],
                                                                                     [
                                                                                         '12S subunit RNA', 'rrnS'],
                                                                                     [
                                                                                         '16S ribosomal RNA', 'rrnL'],
                                                                                     ['16S rRNA',
                                                                                         'rrnL'],
                                                                                     ['16s rRNA',
                                                                                         'rrnL'],
                                                                                     [
                                                                                         '16S subunit RNA', 'rrnL'],
                                                                                     [
                                                                                         'ATP synthase F0 subunit 6', 'atp6'],
                                                                                     [
                                                                                         'ATP synthase F0 subunit 8', 'atp8'],
                                                                                     ['ATPASE 6',
                                                                                         'atp6'],
                                                                                     ['ATPASE 8',
                                                                                         'atp8'],
                                                                                     [
                                                                                         'ATPase subunit 6', 'atp6'],
                                                                                     ['ATPASE6',
                                                                                         'atp6'],
                                                                                     ['ATPASE8',
                                                                                         'atp8'],
                                                                                     ['CO1',
                                                                                         'cox1'],
                                                                                     ['CO2',
                                                                                         'cox2'],
                                                                                     ['CO3',
                                                                                         'cox3'],
                                                                                     ['COB',
                                                                                         'cytb'],
                                                                                     ['cob',
                                                                                         'cytb'],
                                                                                     ['COI',
                                                                                         'cox1'],
                                                                                     ['COII',
                                                                                         'cox2'],
                                                                                     ['COIII',
                                                                                         'cox3'],
                                                                                     ['COXI',
                                                                                         'cox1'],
                                                                                     ['COXII',
                                                                                         'cox2'],
                                                                                     ['COXIII',
                                                                                         'cox3'],
                                                                                     ['CYT B',
                                                                                         'cytb'],
                                                                                     [
                                                                                         'cytochrome b', 'cytb'],
                                                                                     [
                                                                                         'cytochrome c oxidase subunit 1', 'cox1'],
                                                                                     [
                                                                                         'cytochrome c oxidase subunit 2', 'cox2'],
                                                                                     [
                                                                                         'cytochrome c oxidase subunit 3', 'cox3'],
                                                                                     [
                                                                                         'cytochrome c oxidase subunit I', 'cox1'],
                                                                                     [
                                                                                         'cytochrome c oxidase subunit II', 'cox2'],
                                                                                     [
                                                                                         'cytochrome c oxidase subunit III', 'cox3'],
                                                                                     [
                                                                                         'cytochrome oxidase subunit 1', 'cox1'],
                                                                                     [
                                                                                         'cytochrome oxidase subunit 2', 'cox2'],
                                                                                     [
                                                                                         'cytochrome oxidase subunit 3', 'cox3'],
                                                                                     [
                                                                                         'large ribosomal RNA', 'rrnL'],
                                                                                     [
                                                                                         'large ribosomal RNA subunit RNA', 'rrnL'],
                                                                                     [
                                                                                         'large subunit ribosomal RNA', 'rrnL'],
                                                                                     ['l-rRNA',
                                                                                         'rrnL'],
                                                                                     ['nad4l',
                                                                                         'nad4L'],
                                                                                     [
                                                                                         'NADH dehydrogenase subunit 1', 'nad1'],
                                                                                     [
                                                                                         'NADH dehydrogenase subunit 2', 'nad2'],
                                                                                     [
                                                                                         'NADH dehydrogenase subunit 3', 'nad3'],
                                                                                     [
                                                                                         'NADH dehydrogenase subunit 4', 'nad4'],
                                                                                     [
                                                                                         'NADH dehydrogenase subunit 4L', 'nad4L'],
                                                                                     [
                                                                                         'NADH dehydrogenase subunit 5', 'nad5'],
                                                                                     [
                                                                                         'NADH dehydrogenase subunit 6', 'nad6'],
                                                                                     [
                                                                                         'NADH dehydrogenase subunit5', 'nad5'],
                                                                                     ['ND1',
                                                                                         'nad1'],
                                                                                     ['ND2',
                                                                                         'nad2'],
                                                                                     ['ND3',
                                                                                         'nad3'],
                                                                                     ['ND4',
                                                                                         'nad4'],
                                                                                     ['ND4L',
                                                                                         'nad4L'],
                                                                                     ['nd4l',
                                                                                         'nad4L'],
                                                                                     ['ND5',
                                                                                         'nad5'],
                                                                                     ['ND6', 'nad6'],
                                                                                    ['COX1', 'cox1'],
                                                                                    ['COX2', 'cox2'],
                                                                                    ['COX3', 'cox3'],
                                                                                    ['CYTB', 'cytb'],
                                                                                    ['ATP8', 'atp8'],
                                                                                    ['ATP6', 'atp6'],
                                                                                    ['NADH1', 'nad1'],
                                                                                    ['NADH2', 'nad2'],
                                                                                    ['ATPase 8', 'atp8'],
                                                                                    ['ATPase 6', 'atp6'],
                                                                                    ['NADH3', 'nad3'],
                                                                                    ['NADH4L', 'nad4L'],
                                                                                    ['NADH4', 'nad4'],
                                                                                    ['NADH5', 'nad5'],
                                                                                    ['NADH6', 'nad6'],
                                                                                    ['cytochrome oxidase subunit I', 'cox1'],
                                                                                    ['cytochrome oxidase subunit II', 'cox2'],
                                                                                    ['ATPase subunit 8', 'atp8'],
                                                                                    ['cytochrome oxidase subunit III', 'cox3'],
                                                                                     [
                                                                                         'ribosomal RNA large subunit', 'rrnL'],
                                                                                     [
                                                                                         'ribosomal RNA small subunit', 'rrnS'],
                                                                                     [
                                                                                         'small ribosomal RNA', 'rrnS'],
                                                                                     [
                                                                                         'small ribosomal RNA subunit RNA', 'rrnS'],
                                                                                     [
                                                                                         'small subunit ribosomal RNA', 'rrnS'],
                                                                                     ['s-rRNA',
                                                                                         'rrnS'],
                                                                                     ['trnA',
                                                                                         'A'],
                                                                                     ['tRNA-Ala',
                                                                                         'A'],
                                                                                     ['tRNA-Arg',
                                                                                         'R'],
                                                                                     ['tRNA-Asn',
                                                                                         'N'],
                                                                                     ['tRNA-Asp',
                                                                                         'D'],
                                                                                     ['tRNA-Cys',
                                                                                         'C'],
                                                                                     ['tRNA-Gln',
                                                                                         'Q'],
                                                                                     ['tRNA-Glu',
                                                                                         'E'],
                                                                                     ['tRNA-Gly',
                                                                                         'G'],
                                                                                     ['tRNA-His',
                                                                                         'H'],
                                                                                     ['tRNA-Ile',
                                                                                         'I'],
                                                                                     ['tRNA-Leu',
                                                                                         'L'],
                                                                                     ['tRNA-Lys',
                                                                                         'K'],
                                                                                     ['tRNA-Met',
                                                                                         'M'],
                                                                                     ['tRNA-Phe',
                                                                                         'F'],
                                                                                     ['tRNA-Pro',
                                                                                         'P'],
                                                                                     ['tRNA-Ser',
                                                                                         'S'],
                                                                                     ['tRNA-Thr',
                                                                                         'T'],
                                                                                     ['tRNA-Trp',
                                                                                         'W'],
                                                                                     ['tRNA-Tyr',
                                                                                         'Y'],
                                                                                     ['tRNA-Val',
                                                                                         'V'],
                                                                                     ['trnC',
                                                                                         'C'],
                                                                                     ['trnK',
                                                                                         'K'],
                                                                                     ['trnL',
                                                                                         'L'],
                                                                                     ['trnM',
                                                                                         'M'],
                                                                                     ['trnN',
                                                                                         'N'],
                                                                                     ['trnP',
                                                                                         'P'],
                                                                                     ['trnQ',
                                                                                         'Q'],
                                                                                     ['trnR',
                                                                                         'R'],
                                                                                     ['trnS',
                                                                                         'S'],
                                                                                     ['trnT',
                                                                                         'T'],
                                                                                     ['trnV',
                                                                                         'V'],
                                                                                     ['trnW',
                                                                                         'W'],
                                                                                     ['trnY',
                                                                                         'Y'],
                                                                                     ]),
                                                              ('Qualifiers to be recognized (CDS):', [
                                                               'gene', 'product', 'note']),
                                                              ('Qualifiers to be recognized (tRNA):', ['product', 'gene', 'note'])])),
                            ('18S', OrderedDict([('Features to be extracted', ['rRNA', 'misc_feature']),
                                                       ('Qualifiers to be recognized (rRNA):', [
                                                        'gene', 'product', 'note']),
                                                       ('Qualifiers to be recognized (misc_feature):', [
                                                        'gene', 'product', 'note']),
                                                       ('Names unification', [['Old Name', 'New Name'],
                                                                              ["18S ribosomal RNA", "18s"],
                                                                              ["small subunit ribosomal RNA", "18s"],
                                                                              [
                                                                                  "macronuclear small-subunit ribosomal RNA",
                                                                                  "18s"],
                                                                              ["18S small subunit ribosomal RNA",
                                                                               "18s"],
                                                                              ["18S rRNA", "18s"],
                                                                              ["ribosomal RNA small-subunit", "18s"],
                                                                              ["nuclear small subunit ribosomal RNA",
                                                                               "18s"],
                                                                              ["small subunit RNA", "18s"]])])),
                            ('16S', OrderedDict([('Features to be extracted', ['rRNA', 'misc_feature']),
                                                       ('Qualifiers to be recognized (rRNA):', [
                                                        'gene', 'product', 'note']),
                                                       ('Qualifiers to be recognized (misc_feature):', [
                                                        'gene', 'product', 'note']),
                                                       ('Names unification', [['Old Name', 'New Name'],
                                                                              ["16S ribosomal RNA", "16s"],
                                                                              ["16S rRNA", "16s"],
                                                                              ["16s rRNA", "16s"],
                                                                              ["16S subunit RNA", "16s"]])])),
                            ('cox1', OrderedDict([('Features to be extracted', ['CDS']),
                                                   ('Qualifiers to be recognized (CDS):', [
                                                       'gene', 'product', 'note']),
                                                   ('Names unification', [['Old Name', 'New Name'],
                                                                          ["CO1", "cox1"],
                                                                          ["COI", "cox1"],
                                                                          ["COXI", "cox1"],
                                                                          ["cytochrome c oxidase subunit 1", "cox1"],
                                                                          ["cytochrome c oxidase subunit I", "cox1"],
                                                                          ["cytochrome oxidase subunit 1", "cox1"],
                                                                          ["cox1", "cox1"]])])),
                            ('chloroplast genome', OrderedDict([('Features to be extracted',
                                                                 ['rRNA', 'CDS', 'tRNA', 'misc_feature', 'exon',
                                                                  'intron', 'STS', 'tmRNA']),
                                                   ('Qualifiers to be recognized (rRNA):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (CDS):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (tRNA):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (misc_feature):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (exon):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (intron):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (STS):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (tmRNA):', [
                                                       'gene', 'product', 'note']),
                                                    ('Qualifiers to be recognized (all):', [
                                                       'gene', 'product', 'note']),
                                                   ('Names unification', [['Old Name', 'New Name'],
                                                                          [
                                                                              'acetyl-CoA carboxylase carboxyltransferase beta subunit',
                                                                              'accD'], ['acpP2', 'acpP2'],
                                                                          ['ATP synthase CF1 alpha subunit', 'atpA'],
                                                                          ['AtpA', 'atpA'], ['ATPA', 'atpA'],
                                                                          ['ATP synthase CF1 beta subunit', 'atpB'],
                                                                          ['AtpB', 'atpB'], ['ATPB', 'atpB'],
                                                                          ['ATP synthase CF1 epsilon subunit', 'atpE'],
                                                                          ['AtpE', 'atpE'], ['ATPE', 'atpE'],
                                                                          ['ATP synthase CF0 subunit I', 'atpF'],
                                                                          ['ATP synthase CF0 subunit III', 'atpH'],
                                                                          ['ATP synthase CF0 subunit IV', 'atpI'],
                                                                          ['similar to atpI', 'atpI'],
                                                                          ['chloroplast envelope membrane protein',
                                                                           'cemA'],
                                                                          ['envelope membrane protein', 'cemA'], [
                                                                              'light-independent protochlorophyllide reductase subunit B',
                                                                              'chlB'],
                                                                          ['photochlorophyllide reductase subunit B',
                                                                           'chlB'], [
                                                                              'Light-independent protochlorophyllide reductase iron-sulfur ATP-binding protein',
                                                                              'chlL'],
                                                                          ['photochlorophyllide reductase subunit L',
                                                                           'chlL'], [
                                                                              'Light-independent protochlorophyllide reductase subunit N',
                                                                              'chlN'], [
                                                                              'light-independent protochlorophyllide reductase subunit N',
                                                                              'chlN'],
                                                                          ['Photochlorophyllide reductase subunit N',
                                                                           'chlN'],
                                                                          ['photochlorophyllide reductase subunit N',
                                                                           'chlN'], [
                                                                              'ATP-dependent Clp protease proteolytic subunit',
                                                                              'clpP'],
                                                                          ['clp protease proteolytic subunit', 'clpP'],
                                                                          ['aceohydroxyacid synthase small subunit',
                                                                           'ilvH'], ['maturase K', 'matK'],
                                                                          ['Maturase K', 'matK'],
                                                                          ['NADH dehydrogenase subunit 1', 'nad1'],
                                                                          ['NADH dehydrogenase subunit 2', 'nad2'],
                                                                          ['NADH dehydrogenase subunit 3', 'nad3'],
                                                                          ['NADH dehydrogenase subunit 4', 'nad4'],
                                                                          ['NADH dehydrogenase subunit 4L', 'nad4L'],
                                                                          ['NADH dehydrogenase subunit 5', 'nad5'],
                                                                          ['NADH dehydrogenase subunit 6', 'nad6'],
                                                                          ['NADH dehydrogenase subunit 7', 'nad7'],
                                                                          ['NADH dehydrogenase subunit I', 'nadI'],
                                                                          ['NdhK', 'ndhK'], ['cytochrome f', 'petA'],
                                                                          ['cytochrome b/b6', 'petB'],
                                                                          ['cytochrome b6/f complex subunit IV',
                                                                           'petD'],
                                                                          ['cytochrome b6/f complex subunit V', 'petG'],
                                                                          ['cytochrome b6-f complex subunit V', 'petG'],
                                                                          ['photosystem II protein D1', 'psbA'],
                                                                          ['photosystem II protein D2', 'psbD'], [
                                                                              'photosystem II cytochrome b559 alpha subunit',
                                                                              'psbE'], [
                                                                              'photosystem II cytochrome b559 beta subunit',
                                                                              'psbF'],
                                                                          ['photosystem II protein I', 'psbI'],
                                                                          ['photosystem II protein J', 'psbJ'],
                                                                          ['photosystem II protein K', 'psbK'],
                                                                          ['photosystem II protein L', 'psbL'],
                                                                          ['photosystem II protein M', 'psbM'],
                                                                          ['photosystem II protein N', 'psbN'],
                                                                          ['photosystem II protein T', 'psbT'],
                                                                          ['photosystem II protein Z', 'psbZ'],
                                                                          ['ribosomal protein L14', 'rpl14'],
                                                                          ['ribosomal protein L16', 'rpl16'],
                                                                          ['putative ribosomal protein L2', 'rpl2'],
                                                                          ['ribosomal protein L2', 'rpl2'],
                                                                          ['putative ribosomal protein L20', 'rpl20'],
                                                                          ['ribosomal protein L20', 'rpl20'],
                                                                          ['ribosomal protein L22', 'rpl22'],
                                                                          ['ribosomal protein L23', 'rpl23'],
                                                                          ['ribosomal protein L32', 'rpl32'],
                                                                          ['ribosomal protein L33', 'rpl33'],
                                                                          ['ribosomal protein L36', 'rpl36'],
                                                                          ['RNA polymerase alpha protein', 'rpoA'],
                                                                          ['RNA polymerase alpha subunit', 'rpoA'],
                                                                          ['beta subunit of RNA polymerase', 'rpoB'],
                                                                          ['RNA polymerase beta subunit', 'rpoB'],
                                                                          ["RNA polymerase beta' subunit", 'rpoC1'],
                                                                          ["RNA polymerase beta'' subunit", 'rpoC2'],
                                                                          ['ribosomal protein S11', 'rps11'],
                                                                          ["3'rps12", 'rps12'],
                                                                          ["3'rps12 exon", 'rps12'],
                                                                          ['ribosomal protein S12', 'rps12'],
                                                                          ['ribosomal protein S14', 'rps14'],
                                                                          ['ribosomal protein S15', 'rps15'],
                                                                          ['ribosomal proteins S15', 'rps15'],
                                                                          ['ribosomal protein S16', 'rps16'],
                                                                          ['ribosomal protein S18', 'rps18'],
                                                                          ['ribosomal protein S19', 'rps19'],
                                                                          ['ribosomal protein S9', 'rps19'], [
                                                                              "5' end of rps19 at the IRa/LSC boundary; the intact rps19 spans the IRb/LSC boundary",
                                                                              'rps19'],
                                                                          ['ribosomal protein S2', 'rps2'],
                                                                          ['ribosomal protein S3', 'rps3'],
                                                                          ['ribosomal protein S4', 'rps4'],
                                                                          ['ribosomal protein S7', 'rps7'],
                                                                          ['ribosomal protein S8', 'rps8'],
                                                                          ['16rrn', 'rrn16'], ['16s', 'rrn16'],
                                                                          ['16S', 'rrn16'],
                                                                          ['16S ribosomal RNA', 'rrn16'],
                                                                          ['16S rRNA', 'rrn16'],
                                                                          ['16S small subunit ribosomal RNA', 'rrn16'],
                                                                          ['16SrRNA', 'rrn16'], ['rRNA16', 'rrn16'],
                                                                          ['rrna16', 'rrn16'], ['rrna16S', 'rrn16'],
                                                                          ['23rrn', 'rrn23'], ['23S', 'rrn23'],
                                                                          ['23S large subunit ribosomal RNA', 'rrn23'],
                                                                          ['23S ribosomal RNA', 'rrn23'],
                                                                          ['23S rRNA', 'rrn23'], ['23SrRNA', 'rrn23'],
                                                                          ['rrn23S', 'rrn23'], ['rrn23s', 'rrn23'],
                                                                          ['rrn23S rRNA', 'rrn23'], ['rRNA23', 'rrn23'],
                                                                          ['rrna23S', 'rrn23'],
                                                                          ['4.5 ribosomal RNA', 'rrn4.5'],
                                                                          ['4.5rrn', 'rrn4.5'], ['4.5S', 'rrn4.5'],
                                                                          ['4.5S ribosomal RNA', 'rrn4.5'],
                                                                          ['4.5S rRNA', 'rrn4.5'],
                                                                          ['4.5S small subunit ribosomal RNA',
                                                                           'rrn4.5'], ['4.5Srrn', 'rrn4.5'],
                                                                          ['4.5SrRNA', 'rrn4.5'], ['rrn4.55', 'rrn4.5'],
                                                                          ['rrn4.5S', 'rrn4.5'], ['rrn4.5s', 'rrn4.5'],
                                                                          ['rrn4.5S rRNA', 'rrn4.5'],
                                                                          ['rRNA4.5', 'rrn4.5'], ['rRNA4.5S', 'rrn4.5'],
                                                                          ['5 ribosomal RNA', 'rrn5'], ['5rrn', 'rrn5'],
                                                                          ['5S', 'rrn5'], ['5S ribosomal RNA', 'rrn5'],
                                                                          ['5S rRNA', 'rrn5'],
                                                                          ['5S small subunit ribosomal RNA', 'rrn5'],
                                                                          ['5S subunit ribosomal RNA', 'rrn5'],
                                                                          ['5SrRNA', 'rrn5'], ['rrn5', 'rrn5'],
                                                                          ["rrn5'", 'rrn5'], ['rrn5rRNA', 'rrn5'],
                                                                          ['rrn5S', 'rrn5'], ['rrn5s', 'rrn5'],
                                                                          ['rrn5S rRNA', 'rrn5'], ['rRNA5', 'rrn5'],
                                                                          ['rRNA5S', 'rrn5'],
                                                                          ['anticodon:CAU; trnfM-CAU_2', 'trnfM-CAU'],
                                                                          ['trnfM_CAU', 'trnfM-CAU'],
                                                                          ['trnfM_cau', 'trnfM-CAU'],
                                                                          ["5' fragment hypothetical chloroplast RF1",
                                                                           'ycf1'],
                                                                          ['hypothetical chloroplast RF19-like protein',
                                                                           'ycf1'],
                                                                          ['hypothetical chloroplast ycf1', 'ycf1'],
                                                                          ['putative chloroplast protein RF1', 'ycf1'],
                                                                          ['putative chloroplast RF1', 'ycf1'],
                                                                          ['hypothetical chloroplast RF2', 'ycf2'],
                                                                          ['hypothetical chloroplast RF21', 'ycf2'],
                                                                          ['putative chloroplast RF21', 'ycf2'],
                                                                          ['photosystem I assembly protein Ycf3',
                                                                           'ycf3'],
                                                                          ['photosystem I assembly protein ycf3',
                                                                           'ycf3'],
                                                                          ['photosystem I assembly protein Ycf4',
                                                                           'ycf4'],
                                                                          ['photosystem I assembly protein ycf4',
                                                                           'ycf4']
                                                                          ]),
                                                    ('extract all features', True)]))
                              ])

preset_workflow = {
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/checkBox": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/checkBox_12": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/checkBox_13": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/checkBox_2": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/checkBox_3": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/checkBox_4": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/checkBox_5": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/checkBox_9": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/comboBox": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/groupBox": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/groupBox_3": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/groupBox_4": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/groupBox_5": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/groupBox_top_line": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/lineEdit": "concatenation",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/pos": QtCore.QPoint(875, 254),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/pushButton_color": "#f9c997",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/size": QtCore.QSize(537, 514),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/spinBox_5": "5",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/spinBox_6": "8",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/spinBox_7": "15",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Concatenate Sequence/spinBox_8": "45",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/comboBox_11": ["Don't Save", 'Save'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/comboBox_12": ['Save', 'Save Text', 'Save Short', "Don't Save"],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/comboBox_13": ['Yes', 'No'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/comboBox_5": ['With Half', 'All', 'None'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/comboBox_6": ['Save', "Don't Save"],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/comboBox_7": ["Don't Save", 'Save'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/comboBox_8": ["Don't Save", 'Save'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/comboBox_9": ["Don't Save", 'Save'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/lineEdit_3": "_gb",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/pos": QtCore.QPoint(875, 254),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/radioButton": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/radioButton_2": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/radioButton_3": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/size": QtCore.QSize(658, 665),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/spinBox": "60",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/spinBox_2": "8",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/Gblocks/spinBox_3": "10",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/checkBox": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/checkBox_2": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/checkBox_3": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/checkBox_4": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/checkBox_5": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/checkBox_6": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/checkBox_7": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/checkBox_8": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/comboBox_10": "-1",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/comboBox_11": "-1",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/comboBox_3": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/comboBox_4": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/comboBox_5": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/comboBox_6": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/comboBox_7": "2",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/comboBox_8": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/comboBox_9": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/doubleSpinBox": "0.9",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/pos": QtCore.QPoint(778, 142),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/size": QtCore.QSize(556, 675),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/spinBox": "4",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/spinBox_3": "20000",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/spinBox_4": "1000",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/IQ-TREE/spinBox_5": "1000",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/AA_radioButton_2": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/N2P_radioButton": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/PCG_radioButton_2": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/RNAs_radioButton_2": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/checkBox_2": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/codon_radioButton": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/comboBox_2": "3",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/comboBox_3": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/comboBox_9": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/normal_radioButton": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/pos": QtCore.QPoint(875, 254),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/pushButton_par": [['--adjustdirection', '--adjustdirectionaccurately', '--thread 1', '--op 1.53', '--ep 0.123', '--kappa 2', '--lop -2.00', '--lep 0.1', '--lexp -0.1', '--LOP -6.00', '--LEXP 0.00', '--bl 62', '--jtt 1', '--tm 1', '--fmodel'], [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MAFFT/size": QtCore.QSize(500, 510),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/checkBox": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/checkBox_2": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/comboBox_3": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/comboBox_4": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/comboBox_5": "1",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/comboBox_6": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/comboBox_9": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/pos": QtCore.QPoint(1239, 262),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/radioButton": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/radioButton_2": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/ModelFinder/size": QtCore.QSize(500, 519),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/checkBox": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/checkBox_2": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/checkBox_3": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/comboBox_4": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/comboBox_5": "-1",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/comboBox_6": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/comboBox_7": "-1",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/comboBox_8": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/comboBox_9": "0",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/doubleSpinBox_2": "0.25",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/partition defination": [['Model', 'Subset Name', '', 'Start', '', 'Stop'], [['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', '']]],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/pos": QtCore.QPoint(1064, 204),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/pushButton_partition": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/size": QtCore.QSize(557, 673),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/spinBox": "4",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/spinBox_10": "12500",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/spinBox_2": "5000000",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/spinBox_6": "100",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/spinBox_7": "2",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/MrBayes/spinBox_8": "4",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/aa_list_model": ['LG', 'LG+G', 'LG+G+F', 'WAG', 'WAG+G', 'WAG+G+F'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/comboBox": ['unlinked', 'linked'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/comboBox_2": ['all', 'allx', 'beast', 'mrbayes', 'gamma', 'gammai', '<list>'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/comboBox_3": ['AICc', 'BIC', 'AIC'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/comboBox_4": ['all', 'greedy', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/comboBox_5": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/comboBox_6": ['linked', 'unlinked'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/comboBox_7": ['AICc', 'BIC', 'AIC'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/comboBox_8": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/nuc_list_model": ['JC', 'JC+G', 'HKY', 'HKY+G', 'GTR', 'GTR+G'],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/pos": QtCore.QPoint(1052, 247),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/pushButton_cmd1": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/pushButton_cmd2": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/size": QtCore.QSize(500, 559),
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/tabWidget": "1",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/textEdit": "",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/textEdit_2": "",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/PartitionFinder/user_search": "together = (Gene1_codon1, Gene1_codon2, Gene1_codon3, intron);\
intron_123 = (Gene1_codon1, Gene1_codon2, Gene1_codon3) (intron);\
intron_12_3 = (Gene1_codon1, Gene1_codon2) (Gene1_codon3) (intron);\
separate = (Gene1_codon1) (Gene1_codon2) (Gene1_codon3) (intron);",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/checkBox": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/checkBox_2": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/checkBox_3": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/checkBox_4": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/checkBox_5": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/checkBox_6": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/checkBox_7": "true",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/checkBox_8": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/checkBox_9": "false",
"Align AA, Optimize alignments, Concatenation, Select best-fit partition model, and Build ML and BI trees/checkBox_10": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/checkBox": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/checkBox_12": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/checkBox_13": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/checkBox_2": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/checkBox_3": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/checkBox_4": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/checkBox_5": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/checkBox_9": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/comboBox": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/groupBox": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/groupBox_3": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/groupBox_4": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/groupBox_5": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/groupBox_top_line": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/lineEdit": "concatenation",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/pos": QtCore.QPoint(875, 254),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/pushButton_color": "#f9c997",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/size": QtCore.QSize(537, 514),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/spinBox_5": "5",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/spinBox_6": "8",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/spinBox_7": "15",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Concatenate Sequence/spinBox_8": "45",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/comboBox_11": ["Don't Save", 'Save'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/comboBox_12": ['Save', 'Save Text', 'Save Short', "Don't Save"],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/comboBox_13": ['Yes', 'No'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/comboBox_5": ['With Half', 'All', 'None'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/comboBox_6": ['Save', "Don't Save"],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/comboBox_7": ["Don't Save", 'Save'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/comboBox_8": ["Don't Save", 'Save'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/comboBox_9": ["Don't Save", 'Save'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/lineEdit_3": "_gb",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/pos": QtCore.QPoint(875, 254),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/radioButton": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/radioButton_2": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/radioButton_3": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/size": QtCore.QSize(658, 665),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/spinBox": "60",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/spinBox_2": "8",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/Gblocks/spinBox_3": "10",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/checkBox": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/checkBox_2": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/checkBox_3": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/checkBox_4": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/checkBox_5": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/checkBox_6": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/checkBox_7": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/checkBox_8": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/checkBox_9": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/comboBox_10": "-1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/comboBox_11": "-1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/comboBox_3": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/comboBox_4": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/comboBox_5": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/comboBox_6": "2",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/comboBox_7": "2",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/comboBox_8": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/comboBox_9": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/doubleSpinBox": "0.9",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/pos": QtCore.QPoint(778, 142),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/size": QtCore.QSize(556, 675),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/spinBox": "4",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/spinBox_3": "5000",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/spinBox_4": "1000",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/IQ-TREE/spinBox_5": "1000",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/checkBox": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/checkBox_2": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/comboBox": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/comboBox_2": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/comboBox_3": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/comboBox_4": "-1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/comboBox_5": "-1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/comboBox_6": "1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/comboBox_7": "-1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/comboBox_9": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox": "30",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_10": "6.3",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_11": "0.5",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_12": "0.5",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_2": "10",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_3": "7",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_4": "10",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_5": "50",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_6": "17",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_7": "1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_8": "7",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/doubleSpinBox_9": "0.9",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/lineEdit": "",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/pos": QtCore.QPoint(875, 254),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/size": QtCore.QSize(679, 565),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MACSE/spinBox": "-1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/AA_radioButton_2": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/N2P_radioButton": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/PCG_radioButton_2": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/RNAs_radioButton_2": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/checkBox_2": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/codon_radioButton": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/comboBox_2": "3",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/comboBox_3": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/comboBox_9": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/normal_radioButton": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/pos": QtCore.QPoint(875, 254),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/pushButton_par": [['--adjustdirection', '--adjustdirectionaccurately', '--thread 1', '--op 1.53', '--ep 0.123', '--kappa 2', '--lop -2.00', '--lep 0.1', '--lexp -0.1', '--LOP -6.00', '--LEXP 0.00', '--bl 62', '--jtt 1', '--tm 1', '--fmodel'], [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MAFFT/size": QtCore.QSize(500, 515),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/checkBox": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/checkBox_2": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/comboBox_3": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/comboBox_4": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/comboBox_5": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/comboBox_6": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/comboBox_9": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/pos": QtCore.QPoint(1239, 262),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/radioButton": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/radioButton_2": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/ModelFinder/size": QtCore.QSize(500, 524),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/checkBox": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/checkBox_2": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/checkBox_3": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/checkBox_4": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/comboBox_10": "-1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/comboBox_4": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/comboBox_5": "-1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/comboBox_6": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/comboBox_7": "-1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/comboBox_8": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/comboBox_9": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/doubleSpinBox_2": "0.25",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/partition defination": [['Model', 'Subset Name', '', 'Start', '', 'Stop'], [['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', '']]],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/pos": QtCore.QPoint(1064, 204),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/pushButton_partition": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/size": QtCore.QSize(557, 673),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/spinBox": "4",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/spinBox_10": "25",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/spinBox_2": "10000",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/spinBox_6": "100",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/spinBox_7": "2",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/MrBayes/spinBox_8": "4",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/aa_list_model": ['LG', 'LG+G', 'LG+G+F', 'WAG', 'WAG+G', 'WAG+G+F'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/comboBox": ['unlinked', 'linked'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/comboBox_2": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/comboBox_3": ['AICc', 'BIC', 'AIC'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/comboBox_4": ['all', 'greedy', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/comboBox_5": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/comboBox_6": ['linked', 'unlinked'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/comboBox_7": ['AICc', 'BIC', 'AIC'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/comboBox_8": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/nuc_list_model": ['JC', 'JC+G', 'HKY', 'HKY+G', 'GTR', 'GTR+G'],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/pos": QtCore.QPoint(1052, 247),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/pushButton_cmd1": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/pushButton_cmd2": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/size": QtCore.QSize(500, 564),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/tabWidget": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/textEdit": "",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/textEdit_2": "",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/PartitionFinder/user_search": "together = (Gene1_codon1, Gene1_codon2, Gene1_codon3, intron);intron_123 = (Gene1_codon1, Gene1_codon2, Gene1_codon3) (intron);intron_12_3 = (Gene1_codon1, Gene1_codon2) (Gene1_codon3) (intron);separate = (Gene1_codon1) (Gene1_codon2) (Gene1_codon3) (intron);",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/checkBox": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/checkBox_10": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/checkBox_2": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/checkBox_3": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/checkBox_4": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/checkBox_5": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/checkBox_6": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/checkBox_7": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/checkBox_8": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/checkBox_9": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/checkBox": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/checkBox_2": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/checkBox_3": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/checkBox_4": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/checkBox_5": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/checkBox_6": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/checkBox_7": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/checkBox_8": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/checkBox_9": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/comboBox": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/comboBox_2": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/comboBox_4": "-1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/comboBox_6": "1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/comboBox_9": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/doubleSpinBox": "10",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/doubleSpinBox_2": "0.9",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/doubleSpinBox_3": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/doubleSpinBox_4": "0",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/doubleSpinBox_5": "1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/doubleSpinBox_6": "1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/doubleSpinBox_7": "1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/doubleSpinBox_8": "1",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/groupBox": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/groupBox_2": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/groupBox_3": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/groupBox_4": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/groupBox_5": "true",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/groupBox_6": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/groupBox_7": "false",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/lineEdit_2": "",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/lineEdit_3": "",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/lineEdit_4": "summary.html",
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/pos": QtCore.QPoint(875, 254),
"Align CDS, Refine alignment, Optimize alignment, Concatenation and Select best-fit model/trimAl/size": QtCore.QSize(732, 595),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/checkBox": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/checkBox_12": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/checkBox_13": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/checkBox_2": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/checkBox_3": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/checkBox_4": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/checkBox_5": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/checkBox_9": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/comboBox": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/groupBox": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/groupBox_3": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/groupBox_4": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/groupBox_5": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/groupBox_top_line": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/lineEdit": "concatenation",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/pos": QtCore.QPoint(875, 254),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/pushButton_color": "#f9c997",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/size": QtCore.QSize(537, 514),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/spinBox_5": "5",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/spinBox_6": "8",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/spinBox_7": "15",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Concatenate Sequence/spinBox_8": "45",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/comboBox_11": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/comboBox_12": ['Save', 'Save Text', 'Save Short', "Don't Save"],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/comboBox_13": ['Yes', 'No'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/comboBox_5": ['With Half', 'All', 'None'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/comboBox_6": ['Save', "Don't Save"],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/comboBox_7": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/comboBox_8": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/comboBox_9": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/lineEdit_3": "_gb",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/pos": QtCore.QPoint(875, 254),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/radioButton": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/radioButton_2": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/radioButton_3": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/size": QtCore.QSize(658, 665),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/spinBox": "60",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/spinBox_2": "8",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/Gblocks/spinBox_3": "10",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/checkBox": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/checkBox_2": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/checkBox_3": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/checkBox_4": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/checkBox_5": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/checkBox_6": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/checkBox_7": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/checkBox_8": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/comboBox_10": "-1",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/comboBox_11": "-1",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/comboBox_3": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/comboBox_4": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/comboBox_5": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/comboBox_6": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/comboBox_7": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/comboBox_8": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/comboBox_9": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/doubleSpinBox": "0.9",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/pos": QtCore.QPoint(467, 213),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/size": QtCore.QSize(556, 675),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/spinBox": "4",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/spinBox_3": "20000",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/spinBox_4": "1000",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/IQ-TREE/spinBox_5": "1000",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/AA_radioButton_2": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/N2P_radioButton": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/PCG_radioButton_2": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/RNAs_radioButton_2": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/checkBox_2": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/codon_radioButton": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/comboBox_2": "3",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/comboBox_3": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/comboBox_9": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/normal_radioButton": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/pos": QtCore.QPoint(875, 254),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/pushButton_par": [['--adjustdirection', '--adjustdirectionaccurately', '--thread 1', '--op 1.53', '--ep 0.123', '--kappa 2', '--lop -2.00', '--lep 0.1', '--lexp -0.1', '--LOP -6.00', '--LEXP 0.00', '--bl 62', '--jtt 1', '--tm 1', '--fmodel'], [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MAFFT/size": QtCore.QSize(500, 510),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/checkBox": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/checkBox_2": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/comboBox_3": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/comboBox_4": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/comboBox_5": "1",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/comboBox_6": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/comboBox_9": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/pos": QtCore.QPoint(1239, 262),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/radioButton": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/radioButton_2": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/ModelFinder/size": QtCore.QSize(500, 519),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/checkBox": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/checkBox_2": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/checkBox_3": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/comboBox_4": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/comboBox_5": "-1",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/comboBox_6": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/comboBox_7": "-1",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/comboBox_8": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/comboBox_9": "0",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/doubleSpinBox_2": "0.25",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/partition defination": [['Model', 'Subset Name', '', 'Start', '', 'Stop'], [['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', '']]],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/pos": QtCore.QPoint(1064, 204),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/pushButton_partition": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/size": QtCore.QSize(557, 673),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/spinBox": "4",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/spinBox_10": "12500",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/spinBox_2": "5000000",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/spinBox_6": "100",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/spinBox_7": "2",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/MrBayes/spinBox_8": "4",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/aa_list_model": ['LG', 'LG+G', 'LG+G+F', 'WAG', 'WAG+G', 'WAG+G+F'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/comboBox": ['linked', 'unlinked'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/comboBox_2": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/comboBox_3": ['AICc', 'BIC', 'AIC'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/comboBox_4": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/comboBox_5": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/comboBox_6": ['linked', 'unlinked'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/comboBox_7": ['AICc', 'BIC', 'AIC'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/comboBox_8": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/nuc_list_model": ['JC', 'JC+G', 'HKY', 'HKY+G', 'GTR', 'GTR+G'],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/pos": QtCore.QPoint(1052, 247),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/pushButton_cmd1": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/pushButton_cmd2": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/size": QtCore.QSize(500, 559),
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/tabWidget": "1",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/textEdit": "",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/textEdit_2": "",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/PartitionFinder/user_search": "together = (Gene1_codon1, Gene1_codon2, Gene1_codon3, intron);\
intron_123 = (Gene1_codon1, Gene1_codon2, Gene1_codon3) (intron);\
intron_12_3 = (Gene1_codon1, Gene1_codon2) (Gene1_codon3) (intron);\
separate = (Gene1_codon1) (Gene1_codon2) (Gene1_codon3) (intron);",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/checkBox": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/checkBox_2": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/checkBox_3": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/checkBox_4": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/checkBox_5": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/checkBox_6": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/checkBox_7": "true",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/checkBox_8": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/checkBox_9": "false",
"Concatenation, Select best-fit partition model for AA, and Build BI tree/checkBox_10": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/checkBox": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/checkBox_12": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/checkBox_13": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/checkBox_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/checkBox_3": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/checkBox_4": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/checkBox_5": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/checkBox_9": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/comboBox": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/groupBox": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/groupBox_3": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/groupBox_4": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/groupBox_5": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/groupBox_top_line": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/lineEdit": "concatenation",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/pos": QtCore.QPoint(875, 254),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/pushButton_color": "#f9c997",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/size": QtCore.QSize(537, 514),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/spinBox_5": "5",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/spinBox_6": "8",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/spinBox_7": "15",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Concatenate Sequence/spinBox_8": "45",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/comboBox_11": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/comboBox_12": ['Save', 'Save Text', 'Save Short', "Don't Save"],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/comboBox_13": ['Yes', 'No'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/comboBox_5": ['With Half', 'All', 'None'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/comboBox_6": ['Save', "Don't Save"],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/comboBox_7": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/comboBox_8": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/comboBox_9": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/lineEdit_3": "_gb",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/pos": QtCore.QPoint(875, 254),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/radioButton": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/radioButton_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/radioButton_3": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/size": QtCore.QSize(658, 665),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/spinBox": "60",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/spinBox_2": "8",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/Gblocks/spinBox_3": "10",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/checkBox": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/checkBox_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/checkBox_3": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/checkBox_4": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/checkBox_5": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/checkBox_6": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/checkBox_7": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/checkBox_8": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/comboBox_10": "-1",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/comboBox_11": "-1",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/comboBox_3": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/comboBox_4": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/comboBox_5": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/comboBox_6": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/comboBox_7": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/comboBox_8": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/comboBox_9": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/doubleSpinBox": "0.9",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/pos": QtCore.QPoint(467, 213),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/size": QtCore.QSize(556, 675),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/spinBox": "4",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/spinBox_3": "20000",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/spinBox_4": "1000",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/IQ-TREE/spinBox_5": "1000",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/AA_radioButton_2": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/N2P_radioButton": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/PCG_radioButton_2": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/RNAs_radioButton_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/checkBox_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/codon_radioButton": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/comboBox_2": "3",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/comboBox_3": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/comboBox_9": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/normal_radioButton": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/pos": QtCore.QPoint(875, 254),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/pushButton_par": [['--adjustdirection', '--adjustdirectionaccurately', '--thread 1', '--op 1.53', '--ep 0.123', '--kappa 2', '--lop -2.00', '--lep 0.1', '--lexp -0.1', '--LOP -6.00', '--LEXP 0.00', '--bl 62', '--jtt 1', '--tm 1', '--fmodel'], [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MAFFT/size": QtCore.QSize(500, 510),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/checkBox": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/checkBox_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/comboBox_3": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/comboBox_4": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/comboBox_5": "1",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/comboBox_6": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/comboBox_9": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/pos": QtCore.QPoint(1239, 262),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/radioButton": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/radioButton_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/ModelFinder/size": QtCore.QSize(500, 519),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/checkBox": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/checkBox_2": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/checkBox_3": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/comboBox_4": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/comboBox_5": "-1",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/comboBox_6": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/comboBox_7": "-1",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/comboBox_8": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/comboBox_9": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/doubleSpinBox_2": "0.25",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/partition defination": [['Model', 'Subset Name', '', 'Start', '', 'Stop'], [['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', '']]],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/pos": QtCore.QPoint(1064, 204),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/pushButton_partition": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/size": QtCore.QSize(557, 673),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/spinBox": "4",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/spinBox_10": "12500",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/spinBox_2": "5000000",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/spinBox_6": "100",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/spinBox_7": "2",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/MrBayes/spinBox_8": "4",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/aa_list_model": ['LG', 'LG+G', 'LG+G+F', 'WAG', 'WAG+G', 'WAG+G+F'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/comboBox": ['linked', 'unlinked'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/comboBox_2": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/comboBox_3": ['AICc', 'BIC', 'AIC'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/comboBox_4": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/comboBox_5": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/comboBox_6": ['linked', 'unlinked'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/comboBox_7": ['AICc', 'BIC', 'AIC'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/comboBox_8": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/nuc_list_model": ['JC', 'JC+G', 'HKY', 'HKY+G', 'GTR', 'GTR+G'],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/pos": QtCore.QPoint(1052, 247),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/pushButton_cmd1": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/pushButton_cmd2": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/size": QtCore.QSize(500, 559),
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/tabWidget": "0",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/textEdit": "",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/textEdit_2": "",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/PartitionFinder/user_search": "together = (Gene1_codon1, Gene1_codon2, Gene1_codon3, intron);\
intron_123 = (Gene1_codon1, Gene1_codon2, Gene1_codon3) (intron);\
intron_12_3 = (Gene1_codon1, Gene1_codon2) (Gene1_codon3) (intron);\
separate = (Gene1_codon1) (Gene1_codon2) (Gene1_codon3) (intron);",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/checkBox": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/checkBox_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/checkBox_3": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/checkBox_4": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/checkBox_5": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/checkBox_6": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/checkBox_7": "true",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/checkBox_8": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/checkBox_9": "false",
"Concatenation, Select best-fit partition model for DNA, and Build BI tree/checkBox_10": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/checkBox": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/checkBox_12": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/checkBox_13": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/checkBox_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/checkBox_3": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/checkBox_4": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/checkBox_5": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/checkBox_9": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/comboBox": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/groupBox": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/groupBox_3": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/groupBox_4": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/groupBox_5": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/groupBox_top_line": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/lineEdit": "concatenation",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/pos": QtCore.QPoint(875, 254),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/pushButton_color": "#f9c997",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/size": QtCore.QSize(537, 514),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/spinBox_5": "5",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/spinBox_6": "8",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/spinBox_7": "15",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Concatenate Sequence/spinBox_8": "45",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/comboBox_11": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/comboBox_12": ['Save', 'Save Text', 'Save Short', "Don't Save"],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/comboBox_13": ['Yes', 'No'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/comboBox_5": ['With Half', 'All', 'None'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/comboBox_6": ['Save', "Don't Save"],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/comboBox_7": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/comboBox_8": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/comboBox_9": ["Don't Save", 'Save'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/lineEdit_3": "_gb",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/pos": QtCore.QPoint(875, 254),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/radioButton": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/radioButton_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/radioButton_3": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/size": QtCore.QSize(658, 665),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/spinBox": "60",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/spinBox_2": "8",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/Gblocks/spinBox_3": "10",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/checkBox": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/checkBox_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/checkBox_3": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/checkBox_4": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/checkBox_5": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/checkBox_6": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/checkBox_7": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/checkBox_8": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/comboBox_10": "-1",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/comboBox_11": "-1",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/comboBox_3": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/comboBox_4": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/comboBox_5": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/comboBox_6": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/comboBox_7": "2",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/comboBox_8": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/comboBox_9": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/doubleSpinBox": "0.9",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/pos": QtCore.QPoint(1033, 118),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/size": QtCore.QSize(556, 675),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/spinBox": "4",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/spinBox_3": "20000",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/spinBox_4": "1000",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/IQ-TREE/spinBox_5": "1000",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/AA_radioButton_2": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/N2P_radioButton": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/PCG_radioButton_2": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/RNAs_radioButton_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/checkBox_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/codon_radioButton": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/comboBox_2": "3",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/comboBox_3": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/comboBox_9": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/normal_radioButton": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/pos": QtCore.QPoint(875, 254),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/pushButton_par": [['--adjustdirection', '--adjustdirectionaccurately', '--thread 1', '--op 1.53', '--ep 0.123', '--kappa 2', '--lop -2.00', '--lep 0.1', '--lexp -0.1', '--LOP -6.00', '--LEXP 0.00', '--bl 62', '--jtt 1', '--tm 1', '--fmodel'], [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MAFFT/size": QtCore.QSize(500, 510),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/checkBox": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/checkBox_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/comboBox_3": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/comboBox_4": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/comboBox_5": "1",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/comboBox_6": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/comboBox_9": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/pos": QtCore.QPoint(1239, 262),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/radioButton": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/radioButton_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/ModelFinder/size": QtCore.QSize(500, 519),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/checkBox": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/checkBox_2": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/checkBox_3": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/comboBox_4": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/comboBox_5": "-1",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/comboBox_6": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/comboBox_7": "-1",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/comboBox_8": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/comboBox_9": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/doubleSpinBox_2": "0.25",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/partition defination": [['Model', 'Subset Name', '', 'Start', '', 'Stop'], [['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', '']]],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/pos": QtCore.QPoint(1064, 204),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/pushButton_partition": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/size": QtCore.QSize(557, 673),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/spinBox": "4",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/spinBox_10": "12500",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/spinBox_2": "5000000",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/spinBox_6": "100",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/spinBox_7": "2",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/MrBayes/spinBox_8": "4",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/aa_list_model": ['LG', 'LG+G', 'LG+G+F', 'WAG', 'WAG+G', 'WAG+G+F'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/comboBox": ['linked', 'unlinked'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/comboBox_2": ['all', 'mrbayes', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/comboBox_3": ['AICc', 'BIC', 'AIC'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/comboBox_4": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/comboBox_5": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/comboBox_6": ['linked', 'unlinked'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/comboBox_7": ['AICc', 'BIC', 'AIC'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/comboBox_8": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/nuc_list_model": ['JC', 'JC+G', 'HKY', 'HKY+G', 'GTR', 'GTR+G'],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/pos": QtCore.QPoint(1052, 247),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/pushButton_cmd1": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/pushButton_cmd2": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/size": QtCore.QSize(500, 559),
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/tabWidget": "0",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/textEdit": "",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/textEdit_2": "",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/PartitionFinder/user_search": "together = (Gene1_codon1, Gene1_codon2, Gene1_codon3, intron);\
intron_123 = (Gene1_codon1, Gene1_codon2, Gene1_codon3) (intron);\
intron_12_3 = (Gene1_codon1, Gene1_codon2) (Gene1_codon3) (intron);\
separate = (Gene1_codon1) (Gene1_codon2) (Gene1_codon3) (intron);",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/checkBox": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/checkBox_2": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/checkBox_3": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/checkBox_4": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/checkBox_5": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/checkBox_6": "true",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/checkBox_7": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/checkBox_8": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/checkBox_9": "false",
"Concatenation, Select best-fit partition model for DNA, and Build ML tree/checkBox_10": "false",
"Select best-fit model then build BI tree/Concatenate Sequence/checkBox": "true",
"Select best-fit model then build BI tree/Concatenate Sequence/checkBox_12": "true",
"Select best-fit model then build BI tree/Concatenate Sequence/checkBox_13": "false",
"Select best-fit model then build BI tree/Concatenate Sequence/checkBox_2": "true",
"Select best-fit model then build BI tree/Concatenate Sequence/checkBox_3": "true",
"Select best-fit model then build BI tree/Concatenate Sequence/checkBox_4": "true",
"Select best-fit model then build BI tree/Concatenate Sequence/checkBox_5": "false",
"Select best-fit model then build BI tree/Concatenate Sequence/checkBox_9": "false",
"Select best-fit model then build BI tree/Concatenate Sequence/comboBox": "0",
"Select best-fit model then build BI tree/Concatenate Sequence/groupBox": "false",
"Select best-fit model then build BI tree/Concatenate Sequence/groupBox_3": "false",
"Select best-fit model then build BI tree/Concatenate Sequence/groupBox_4": "false",
"Select best-fit model then build BI tree/Concatenate Sequence/groupBox_5": "false",
"Select best-fit model then build BI tree/Concatenate Sequence/groupBox_top_line": "true",
"Select best-fit model then build BI tree/Concatenate Sequence/lineEdit": "concatenation",
"Select best-fit model then build BI tree/Concatenate Sequence/pos": QtCore.QPoint(875, 254),
"Select best-fit model then build BI tree/Concatenate Sequence/pushButton_color": "#f9c997",
"Select best-fit model then build BI tree/Concatenate Sequence/size": QtCore.QSize(537, 514),
"Select best-fit model then build BI tree/Concatenate Sequence/spinBox_5": "5",
"Select best-fit model then build BI tree/Concatenate Sequence/spinBox_6": "8",
"Select best-fit model then build BI tree/Concatenate Sequence/spinBox_7": "15",
"Select best-fit model then build BI tree/Concatenate Sequence/spinBox_8": "45",
"Select best-fit model then build BI tree/Gblocks/comboBox_11": ["Don't Save", 'Save'],
"Select best-fit model then build BI tree/Gblocks/comboBox_12": ['Save', 'Save Text', 'Save Short', "Don't Save"],
"Select best-fit model then build BI tree/Gblocks/comboBox_13": ['Yes', 'No'],
"Select best-fit model then build BI tree/Gblocks/comboBox_5": ['With Half', 'All', 'None'],
"Select best-fit model then build BI tree/Gblocks/comboBox_6": ['Save', "Don't Save"],
"Select best-fit model then build BI tree/Gblocks/comboBox_7": ["Don't Save", 'Save'],
"Select best-fit model then build BI tree/Gblocks/comboBox_8": ["Don't Save", 'Save'],
"Select best-fit model then build BI tree/Gblocks/comboBox_9": ["Don't Save", 'Save'],
"Select best-fit model then build BI tree/Gblocks/lineEdit_3": "_gb",
"Select best-fit model then build BI tree/Gblocks/pos": QtCore.QPoint(875, 254),
"Select best-fit model then build BI tree/Gblocks/radioButton": "false",
"Select best-fit model then build BI tree/Gblocks/radioButton_2": "true",
"Select best-fit model then build BI tree/Gblocks/radioButton_3": "false",
"Select best-fit model then build BI tree/Gblocks/size": QtCore.QSize(658, 665),
"Select best-fit model then build BI tree/Gblocks/spinBox": "60",
"Select best-fit model then build BI tree/Gblocks/spinBox_2": "8",
"Select best-fit model then build BI tree/Gblocks/spinBox_3": "10",
"Select best-fit model then build BI tree/IQ-TREE/checkBox": "false",
"Select best-fit model then build BI tree/IQ-TREE/checkBox_2": "true",
"Select best-fit model then build BI tree/IQ-TREE/checkBox_3": "false",
"Select best-fit model then build BI tree/IQ-TREE/checkBox_4": "false",
"Select best-fit model then build BI tree/IQ-TREE/checkBox_5": "false",
"Select best-fit model then build BI tree/IQ-TREE/checkBox_6": "true",
"Select best-fit model then build BI tree/IQ-TREE/checkBox_7": "false",
"Select best-fit model then build BI tree/IQ-TREE/checkBox_8": "true",
"Select best-fit model then build BI tree/IQ-TREE/comboBox_10": "-1",
"Select best-fit model then build BI tree/IQ-TREE/comboBox_11": "-1",
"Select best-fit model then build BI tree/IQ-TREE/comboBox_3": "0",
"Select best-fit model then build BI tree/IQ-TREE/comboBox_4": "0",
"Select best-fit model then build BI tree/IQ-TREE/comboBox_5": "0",
"Select best-fit model then build BI tree/IQ-TREE/comboBox_6": "0",
"Select best-fit model then build BI tree/IQ-TREE/comboBox_7": "0",
"Select best-fit model then build BI tree/IQ-TREE/comboBox_8": "0",
"Select best-fit model then build BI tree/IQ-TREE/comboBox_9": "0",
"Select best-fit model then build BI tree/IQ-TREE/doubleSpinBox": "0.9",
"Select best-fit model then build BI tree/IQ-TREE/pos": QtCore.QPoint(467, 213),
"Select best-fit model then build BI tree/IQ-TREE/size": QtCore.QSize(556, 675),
"Select best-fit model then build BI tree/IQ-TREE/spinBox": "4",
"Select best-fit model then build BI tree/IQ-TREE/spinBox_3": "20000",
"Select best-fit model then build BI tree/IQ-TREE/spinBox_4": "1000",
"Select best-fit model then build BI tree/IQ-TREE/spinBox_5": "1000",
"Select best-fit model then build BI tree/MAFFT/AA_radioButton_2": "false",
"Select best-fit model then build BI tree/MAFFT/N2P_radioButton": "false",
"Select best-fit model then build BI tree/MAFFT/PCG_radioButton_2": "false",
"Select best-fit model then build BI tree/MAFFT/RNAs_radioButton_2": "true",
"Select best-fit model then build BI tree/MAFFT/checkBox_2": "true",
"Select best-fit model then build BI tree/MAFFT/codon_radioButton": "false",
"Select best-fit model then build BI tree/MAFFT/comboBox_2": "3",
"Select best-fit model then build BI tree/MAFFT/comboBox_3": "0",
"Select best-fit model then build BI tree/MAFFT/comboBox_9": "0",
"Select best-fit model then build BI tree/MAFFT/normal_radioButton": "true",
"Select best-fit model then build BI tree/MAFFT/pos": QtCore.QPoint(875, 254),
"Select best-fit model then build BI tree/MAFFT/pushButton_par": [['--adjustdirection', '--adjustdirectionaccurately', '--thread 1', '--op 1.53', '--ep 0.123', '--kappa 2', '--lop -2.00', '--lep 0.1', '--lexp -0.1', '--LOP -6.00', '--LEXP 0.00', '--bl 62', '--jtt 1', '--tm 1', '--fmodel'], [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]],
"Select best-fit model then build BI tree/MAFFT/size": QtCore.QSize(500, 510),
"Select best-fit model then build BI tree/ModelFinder/checkBox": "false",
"Select best-fit model then build BI tree/ModelFinder/checkBox_2": "true",
"Select best-fit model then build BI tree/ModelFinder/comboBox_3": "0",
"Select best-fit model then build BI tree/ModelFinder/comboBox_4": "0",
"Select best-fit model then build BI tree/ModelFinder/comboBox_5": "1",
"Select best-fit model then build BI tree/ModelFinder/comboBox_6": "0",
"Select best-fit model then build BI tree/ModelFinder/comboBox_9": "0",
"Select best-fit model then build BI tree/ModelFinder/pos": QtCore.QPoint(1239, 262),
"Select best-fit model then build BI tree/ModelFinder/radioButton": "false",
"Select best-fit model then build BI tree/ModelFinder/radioButton_2": "true",
"Select best-fit model then build BI tree/ModelFinder/size": QtCore.QSize(500, 519),
"Select best-fit model then build BI tree/MrBayes/checkBox": "true",
"Select best-fit model then build BI tree/MrBayes/checkBox_2": "false",
"Select best-fit model then build BI tree/MrBayes/checkBox_3": "true",
"Select best-fit model then build BI tree/MrBayes/comboBox_4": "0",
"Select best-fit model then build BI tree/MrBayes/comboBox_5": "-1",
"Select best-fit model then build BI tree/MrBayes/comboBox_6": "0",
"Select best-fit model then build BI tree/MrBayes/comboBox_7": "-1",
"Select best-fit model then build BI tree/MrBayes/comboBox_8": "0",
"Select best-fit model then build BI tree/MrBayes/comboBox_9": "0",
"Select best-fit model then build BI tree/MrBayes/doubleSpinBox_2": "0.25",
"Select best-fit model then build BI tree/MrBayes/partition defination": [['Model', 'Subset Name', '', 'Start', '', 'Stop'], [['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', '']]],
"Select best-fit model then build BI tree/MrBayes/pos": QtCore.QPoint(1064, 204),
"Select best-fit model then build BI tree/MrBayes/pushButton_partition": "false",
"Select best-fit model then build BI tree/MrBayes/size": QtCore.QSize(557, 673),
"Select best-fit model then build BI tree/MrBayes/spinBox": "4",
"Select best-fit model then build BI tree/MrBayes/spinBox_10": "12500",
"Select best-fit model then build BI tree/MrBayes/spinBox_2": "5000000",
"Select best-fit model then build BI tree/MrBayes/spinBox_6": "100",
"Select best-fit model then build BI tree/MrBayes/spinBox_7": "2",
"Select best-fit model then build BI tree/MrBayes/spinBox_8": "4",
"Select best-fit model then build BI tree/PartitionFinder/aa_list_model": ['LG', 'LG+G', 'LG+G+F', 'WAG', 'WAG+G', 'WAG+G+F'],
"Select best-fit model then build BI tree/PartitionFinder/comboBox": ['unlinked', 'linked'],
"Select best-fit model then build BI tree/PartitionFinder/comboBox_2": ['all', 'allx', 'beast', 'mrbayes', 'gamma', 'gammai', '<list>'],
"Select best-fit model then build BI tree/PartitionFinder/comboBox_3": ['AICc', 'BIC', 'AIC'],
"Select best-fit model then build BI tree/PartitionFinder/comboBox_4": ['all', 'greedy', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Select best-fit model then build BI tree/PartitionFinder/comboBox_5": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Select best-fit model then build BI tree/PartitionFinder/comboBox_6": ['linked', 'unlinked'],
"Select best-fit model then build BI tree/PartitionFinder/comboBox_7": ['AICc', 'BIC', 'AIC'],
"Select best-fit model then build BI tree/PartitionFinder/comboBox_8": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Select best-fit model then build BI tree/PartitionFinder/nuc_list_model": ['JC', 'JC+G', 'HKY', 'HKY+G', 'GTR', 'GTR+G'],
"Select best-fit model then build BI tree/PartitionFinder/pos": QtCore.QPoint(1052, 247),
"Select best-fit model then build BI tree/PartitionFinder/pushButton_cmd1": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Select best-fit model then build BI tree/PartitionFinder/pushButton_cmd2": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Select best-fit model then build BI tree/PartitionFinder/size": QtCore.QSize(500, 559),
"Select best-fit model then build BI tree/PartitionFinder/tabWidget": "1",
"Select best-fit model then build BI tree/PartitionFinder/textEdit": "",
"Select best-fit model then build BI tree/PartitionFinder/textEdit_2": "",
"Select best-fit model then build BI tree/PartitionFinder/user_search": "together = (Gene1_codon1, Gene1_codon2, Gene1_codon3, intron);\
intron_123 = (Gene1_codon1, Gene1_codon2, Gene1_codon3) (intron);\
intron_12_3 = (Gene1_codon1, Gene1_codon2) (Gene1_codon3) (intron);\
separate = (Gene1_codon1) (Gene1_codon2) (Gene1_codon3) (intron);",
"Select best-fit model then build BI tree/checkBox": "false",
"Select best-fit model then build BI tree/checkBox_2": "false",
"Select best-fit model then build BI tree/checkBox_3": "false",
"Select best-fit model then build BI tree/checkBox_4": "false",
"Select best-fit model then build BI tree/checkBox_5": "true",
"Select best-fit model then build BI tree/checkBox_6": "false",
"Select best-fit model then build BI tree/checkBox_7": "true",
"Select best-fit model then build BI tree/checkBox_8": "false",
"Select best-fit model then build BI tree/checkBox_9": "false",
"Select best-fit model then build BI tree/checkBox_10": "false",
"Test run/Concatenate Sequence/checkBox": True,
"Test run/Concatenate Sequence/checkBox_12": True,
"Test run/Concatenate Sequence/checkBox_13": False,
"Test run/Concatenate Sequence/checkBox_2": True,
"Test run/Concatenate Sequence/checkBox_3": True,
"Test run/Concatenate Sequence/checkBox_4": True,
"Test run/Concatenate Sequence/checkBox_5": False,
"Test run/Concatenate Sequence/checkBox_9": False,
"Test run/Concatenate Sequence/comboBox": 0,
"Test run/Concatenate Sequence/groupBox": False,
"Test run/Concatenate Sequence/groupBox_3": False,
"Test run/Concatenate Sequence/groupBox_4": False,
"Test run/Concatenate Sequence/groupBox_5": False,
"Test run/Concatenate Sequence/groupBox_top_line": True,
"Test run/Concatenate Sequence/lineEdit": "concatenation",
"Test run/Concatenate Sequence/pos": QtCore.QPoint(875, 254),
"Test run/Concatenate Sequence/pushButton_color": "#f9c997",
"Test run/Concatenate Sequence/size": QtCore.QSize(537, 514),
"Test run/Concatenate Sequence/spinBox_5": 5,
"Test run/Concatenate Sequence/spinBox_6": 8,
"Test run/Concatenate Sequence/spinBox_7": 15,
"Test run/Concatenate Sequence/spinBox_8": 45,
"Test run/Gblocks/comboBox_11": ["Don't Save", 'Save'],
"Test run/Gblocks/comboBox_12": ['Save', 'Save Text', 'Save Short', "Don't Save"],
"Test run/Gblocks/comboBox_13": ['Yes', 'No'],
"Test run/Gblocks/comboBox_5": ['With Half', 'All', 'None'],
"Test run/Gblocks/comboBox_6": ['Save', "Don't Save"],
"Test run/Gblocks/comboBox_7": ["Don't Save", 'Save'],
"Test run/Gblocks/comboBox_8": ["Don't Save", 'Save'],
"Test run/Gblocks/comboBox_9": ["Don't Save", 'Save'],
"Test run/Gblocks/lineEdit_3": "_gb",
"Test run/Gblocks/pos": QtCore.QPoint(875, 254),
"Test run/Gblocks/radioButton": False,
"Test run/Gblocks/radioButton_2": False,
"Test run/Gblocks/radioButton_3": True,
"Test run/Gblocks/size": QtCore.QSize(658, 665),
"Test run/Gblocks/spinBox": 60,
"Test run/Gblocks/spinBox_2": 8,
"Test run/Gblocks/spinBox_3": 10,
"Test run/IQ-TREE/checkBox": False,
"Test run/IQ-TREE/checkBox_2": True,
"Test run/IQ-TREE/checkBox_3": False,
"Test run/IQ-TREE/checkBox_4": False,
"Test run/IQ-TREE/checkBox_5": False,
"Test run/IQ-TREE/checkBox_6": True,
"Test run/IQ-TREE/checkBox_7": False,
"Test run/IQ-TREE/checkBox_8": True,
"Test run/IQ-TREE/checkBox_9": True,
"Test run/IQ-TREE/comboBox_10": -1,
"Test run/IQ-TREE/comboBox_11": -1,
"Test run/IQ-TREE/comboBox_3": 0,
"Test run/IQ-TREE/comboBox_4": 0,
"Test run/IQ-TREE/comboBox_5": 0,
"Test run/IQ-TREE/comboBox_6": 2,
"Test run/IQ-TREE/comboBox_7": 2,
"Test run/IQ-TREE/comboBox_8": 0,
"Test run/IQ-TREE/comboBox_9": 0,
"Test run/IQ-TREE/doubleSpinBox": 0.9,
"Test run/IQ-TREE/pos": QtCore.QPoint(778, 142),
"Test run/IQ-TREE/size": QtCore.QSize(556, 675),
"Test run/IQ-TREE/spinBox": 4,
"Test run/IQ-TREE/spinBox_3": 5000,
"Test run/IQ-TREE/spinBox_4": 1000,
"Test run/IQ-TREE/spinBox_5": 1000,
"Test run/MAFFT/AA_radioButton_2": False,
"Test run/MAFFT/N2P_radioButton": False,
"Test run/MAFFT/PCG_radioButton_2": True,
"Test run/MAFFT/RNAs_radioButton_2": False,
"Test run/MAFFT/checkBox_2": True,
"Test run/MAFFT/codon_radioButton": True,
"Test run/MAFFT/comboBox_2": 3,
"Test run/MAFFT/comboBox_3": 0,
"Test run/MAFFT/comboBox_9": 1,
"Test run/MAFFT/normal_radioButton": False,
"Test run/MAFFT/pos": QtCore.QPoint(875, 254),
"Test run/MAFFT/pushButton_par": [['--adjustdirection', '--adjustdirectionaccurately', '--thread 1', '--op 1.53', '--ep 0.123', '--kappa 2', '--lop -2.00', '--lep 0.1', '--lexp -0.1', '--LOP -6.00', '--LEXP 0.00', '--bl 62', '--jtt 1', '--tm 1', '--fmodel'], [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]],
"Test run/MAFFT/size": QtCore.QSize(500, 515),
"Test run/ModelFinder/checkBox": "false",
"Test run/ModelFinder/checkBox_2": "true",
"Test run/ModelFinder/comboBox_3": "0",
"Test run/ModelFinder/comboBox_4": "0",
"Test run/ModelFinder/comboBox_5": "1",
"Test run/ModelFinder/comboBox_6": "0",
"Test run/ModelFinder/comboBox_9": "0",
"Test run/ModelFinder/pos": QtCore.QPoint(1239, 262),
"Test run/ModelFinder/radioButton": "false",
"Test run/ModelFinder/radioButton_2": "true",
"Test run/ModelFinder/size": QtCore.QSize(500, 519),
"Test run/MrBayes/checkBox": True,
"Test run/MrBayes/checkBox_2": False,
"Test run/MrBayes/checkBox_3": True,
"Test run/MrBayes/checkBox_4": False,
"Test run/MrBayes/comboBox_10": -1,
"Test run/MrBayes/comboBox_4": 0,
"Test run/MrBayes/comboBox_5": -1,
"Test run/MrBayes/comboBox_6": 0,
"Test run/MrBayes/comboBox_7": -1,
"Test run/MrBayes/comboBox_8": 0,
"Test run/MrBayes/comboBox_9": 0,
"Test run/MrBayes/doubleSpinBox_2": 0.25,
"Test run/MrBayes/partition defination": [['Model', 'Subset Name', '', 'Start', '', 'Stop'], [['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', '']]],
"Test run/MrBayes/pos": QtCore.QPoint(1064, 204),
"Test run/MrBayes/pushButton_partition": True,
"Test run/MrBayes/size": QtCore.QSize(557, 673),
"Test run/MrBayes/spinBox": 4,
"Test run/MrBayes/spinBox_10": 25,
"Test run/MrBayes/spinBox_2": 10000,
"Test run/MrBayes/spinBox_6": 100,
"Test run/MrBayes/spinBox_7": 2,
"Test run/MrBayes/spinBox_8": 4,
"Test run/PartitionFinder/aa_list_model": ['LG', 'LG+G', 'LG+G+F', 'WAG', 'WAG+G', 'WAG+G+F'],
"Test run/PartitionFinder/comboBox": ['unlinked', 'linked'],
"Test run/PartitionFinder/comboBox_2": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Test run/PartitionFinder/comboBox_3": ['AICc', 'BIC', 'AIC'],
"Test run/PartitionFinder/comboBox_4": ['all', 'greedy', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Test run/PartitionFinder/comboBox_5": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"Test run/PartitionFinder/comboBox_6": ['linked', 'unlinked'],
"Test run/PartitionFinder/comboBox_7": ['AICc', 'BIC', 'AIC'],
"Test run/PartitionFinder/comboBox_8": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"Test run/PartitionFinder/nuc_list_model": ['JC', 'JC+G', 'HKY', 'HKY+G', 'GTR', 'GTR+G'],
"Test run/PartitionFinder/pos": QtCore.QPoint(1052, 247),
"Test run/PartitionFinder/pushButton_cmd1": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Test run/PartitionFinder/pushButton_cmd2": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"Test run/PartitionFinder/size": QtCore.QSize(500, 564),
"Test run/PartitionFinder/tabWidget": 0,
"Test run/PartitionFinder/textEdit": "",
"Test run/PartitionFinder/textEdit_2": "",
"Test run/PartitionFinder/user_search": "together = (Gene1_codon1, Gene1_codon2, Gene1_codon3, intron);intron_123 = (Gene1_codon1, Gene1_codon2, Gene1_codon3) (intron);intron_12_3 = (Gene1_codon1, Gene1_codon2) (Gene1_codon3) (intron);separate = (Gene1_codon1) (Gene1_codon2) (Gene1_codon3) (intron);",
"Test run/checkBox": True,
"Test run/checkBox_2": True,
"Test run/checkBox_3": True,
"Test run/checkBox_4": True,
"Test run/checkBox_5": False,
"Test run/checkBox_6": True,
"Test run/checkBox_7": True,
"Test run/checkBox_8": False,
"Test run/checkBox_9": False,
"Test run/checkBox_10": False,
"temporary/Concatenate Sequence/checkBox": "true",
"temporary/Concatenate Sequence/checkBox_12": "true",
"temporary/Concatenate Sequence/checkBox_13": "false",
"temporary/Concatenate Sequence/checkBox_2": "true",
"temporary/Concatenate Sequence/checkBox_3": "true",
"temporary/Concatenate Sequence/checkBox_4": "true",
"temporary/Concatenate Sequence/checkBox_5": "false",
"temporary/Concatenate Sequence/checkBox_9": "false",
"temporary/Concatenate Sequence/comboBox": "0",
"temporary/Concatenate Sequence/groupBox": "false",
"temporary/Concatenate Sequence/groupBox_3": "false",
"temporary/Concatenate Sequence/groupBox_4": "false",
"temporary/Concatenate Sequence/groupBox_5": "false",
"temporary/Concatenate Sequence/groupBox_top_line": "true",
"temporary/Concatenate Sequence/lineEdit": "concatenation",
"temporary/Concatenate Sequence/pos": QtCore.QPoint(875, 254),
"temporary/Concatenate Sequence/pushButton_color": "#f9c997",
"temporary/Concatenate Sequence/size": QtCore.QSize(537, 514),
"temporary/Concatenate Sequence/spinBox_5": "5",
"temporary/Concatenate Sequence/spinBox_6": "8",
"temporary/Concatenate Sequence/spinBox_7": "15",
"temporary/Concatenate Sequence/spinBox_8": "45",
"temporary/Gblocks/comboBox_11": ["Don't Save", 'Save'],
"temporary/Gblocks/comboBox_12": ['Save', 'Save Text', 'Save Short', "Don't Save"],
"temporary/Gblocks/comboBox_13": ['Yes', 'No'],
"temporary/Gblocks/comboBox_5": ['With Half', 'All', 'None'],
"temporary/Gblocks/comboBox_6": ['Save', "Don't Save"],
"temporary/Gblocks/comboBox_7": ["Don't Save", 'Save'],
"temporary/Gblocks/comboBox_8": ["Don't Save", 'Save'],
"temporary/Gblocks/comboBox_9": ["Don't Save", 'Save'],
"temporary/Gblocks/lineEdit_3": "_gb",
"temporary/Gblocks/pos": QtCore.QPoint(875, 254),
"temporary/Gblocks/radioButton": "false",
"temporary/Gblocks/radioButton_2": "true",
"temporary/Gblocks/radioButton_3": "false",
"temporary/Gblocks/size": QtCore.QSize(658, 665),
"temporary/Gblocks/spinBox": "60",
"temporary/Gblocks/spinBox_2": "8",
"temporary/Gblocks/spinBox_3": "10",
"temporary/IQ-TREE/checkBox": "false",
"temporary/IQ-TREE/checkBox_2": "true",
"temporary/IQ-TREE/checkBox_3": "false",
"temporary/IQ-TREE/checkBox_4": "false",
"temporary/IQ-TREE/checkBox_5": "false",
"temporary/IQ-TREE/checkBox_6": "true",
"temporary/IQ-TREE/checkBox_7": "false",
"temporary/IQ-TREE/checkBox_8": "true",
"temporary/IQ-TREE/comboBox_10": "-1",
"temporary/IQ-TREE/comboBox_11": "-1",
"temporary/IQ-TREE/comboBox_3": "0",
"temporary/IQ-TREE/comboBox_4": "0",
"temporary/IQ-TREE/comboBox_5": "0",
"temporary/IQ-TREE/comboBox_6": "0",
"temporary/IQ-TREE/comboBox_7": "0",
"temporary/IQ-TREE/comboBox_8": "0",
"temporary/IQ-TREE/comboBox_9": "0",
"temporary/IQ-TREE/doubleSpinBox": "0.9",
"temporary/IQ-TREE/pos": QtCore.QPoint(778, 142),
"temporary/IQ-TREE/size": QtCore.QSize(556, 675),
"temporary/IQ-TREE/spinBox": "4",
"temporary/IQ-TREE/spinBox_3": "20000",
"temporary/IQ-TREE/spinBox_4": "1000",
"temporary/IQ-TREE/spinBox_5": "1000",
"temporary/MAFFT/AA_radioButton_2": "false",
"temporary/MAFFT/N2P_radioButton": "false",
"temporary/MAFFT/PCG_radioButton_2": "false",
"temporary/MAFFT/RNAs_radioButton_2": "true",
"temporary/MAFFT/checkBox_2": "true",
"temporary/MAFFT/codon_radioButton": "false",
"temporary/MAFFT/comboBox_2": "3",
"temporary/MAFFT/comboBox_3": "0",
"temporary/MAFFT/comboBox_9": "0",
"temporary/MAFFT/normal_radioButton": "true",
"temporary/MAFFT/pos": QtCore.QPoint(875, 254),
"temporary/MAFFT/pushButton_par": [['--adjustdirection', '--adjustdirectionaccurately', '--thread 1', '--op 1.53', '--ep 0.123', '--kappa 2', '--lop -2.00', '--lep 0.1', '--lexp -0.1', '--LOP -6.00', '--LEXP 0.00', '--bl 62', '--jtt 1', '--tm 1', '--fmodel'], [False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]],
"temporary/MAFFT/size": QtCore.QSize(500, 510),
"temporary/ModelFinder/checkBox": "false",
"temporary/ModelFinder/checkBox_2": "true",
"temporary/ModelFinder/comboBox_3": "0",
"temporary/ModelFinder/comboBox_4": "0",
"temporary/ModelFinder/comboBox_5": "1",
"temporary/ModelFinder/comboBox_6": "0",
"temporary/ModelFinder/comboBox_9": "0",
"temporary/ModelFinder/pos": QtCore.QPoint(1239, 262),
"temporary/ModelFinder/radioButton": "false",
"temporary/ModelFinder/radioButton_2": "true",
"temporary/ModelFinder/size": QtCore.QSize(500, 519),
"temporary/MrBayes/checkBox": "true",
"temporary/MrBayes/checkBox_2": "false",
"temporary/MrBayes/checkBox_3": "true",
"temporary/MrBayes/comboBox_4": "0",
"temporary/MrBayes/comboBox_5": "-1",
"temporary/MrBayes/comboBox_6": "0",
"temporary/MrBayes/comboBox_7": "-1",
"temporary/MrBayes/comboBox_8": "0",
"temporary/MrBayes/comboBox_9": "0",
"temporary/MrBayes/doubleSpinBox_2": "0.25",
"temporary/MrBayes/partition defination": [['Model', 'Subset Name', '', 'Start', '', 'Stop'], [['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', ''], ['', '', '=', '', '-', '']]],
"temporary/MrBayes/pos": QtCore.QPoint(1064, 204),
"temporary/MrBayes/pushButton_partition": "true",
"temporary/MrBayes/size": QtCore.QSize(557, 673),
"temporary/MrBayes/spinBox": "4",
"temporary/MrBayes/spinBox_10": "12500",
"temporary/MrBayes/spinBox_2": "5000000",
"temporary/MrBayes/spinBox_6": "100",
"temporary/MrBayes/spinBox_7": "2",
"temporary/MrBayes/spinBox_8": "4",
"temporary/PartitionFinder/aa_list_model": ['LG', 'LG+G', 'LG+G+F', 'WAG', 'WAG+G', 'WAG+G+F'],
"temporary/PartitionFinder/comboBox": ['unlinked', 'linked'],
"temporary/PartitionFinder/comboBox_2": ['all', 'allx', 'beast', 'mrbayes', 'gamma', 'gammai', '<list>'],
"temporary/PartitionFinder/comboBox_3": ['AICc', 'BIC', 'AIC'],
"temporary/PartitionFinder/comboBox_4": ['all', 'greedy', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"temporary/PartitionFinder/comboBox_5": ['greedy', 'all', 'rcluster', 'rclusterf', 'hcluster', 'kmeans', 'user define'],
"temporary/PartitionFinder/comboBox_6": ['linked', 'unlinked'],
"temporary/PartitionFinder/comboBox_7": ['AICc', 'BIC', 'AIC'],
"temporary/PartitionFinder/comboBox_8": ['mrbayes', 'all', 'allx', 'beast', 'gamma', 'gammai', '<list>'],
"temporary/PartitionFinder/nuc_list_model": ['JC', 'JC+G', 'HKY', 'HKY+G', 'GTR', 'GTR+G'],
"temporary/PartitionFinder/pos": QtCore.QPoint(1052, 247),
"temporary/PartitionFinder/pushButton_cmd1": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"temporary/PartitionFinder/pushButton_cmd2": [['--raxml', '--all-states', '--force-restart', '--min-subset-size', '--no-ml-tree', '--processes', '--quick', '--rcluster-max', '--rcluster-percent', '--save-phylofiles', '--weights'], [False, False, False, False, False, False, False, False, False, False, False]],
"temporary/PartitionFinder/size": QtCore.QSize(500, 559),
"temporary/PartitionFinder/tabWidget": "1",
"temporary/PartitionFinder/textEdit": "",
"temporary/PartitionFinder/textEdit_2": "",
"temporary/PartitionFinder/user_search": "together = (Gene1_codon1, Gene1_codon2, Gene1_codon3, intron);\
intron_123 = (Gene1_codon1, Gene1_codon2, Gene1_codon3) (intron);\
intron_12_3 = (Gene1_codon1, Gene1_codon2) (Gene1_codon3) (intron);\
separate = (Gene1_codon1) (Gene1_codon2) (Gene1_codon3) (intron);",
"temporary/checkBox": "true",
"temporary/checkBox_2": "true",
"temporary/checkBox_3": "true",
"temporary/checkBox_4": "true",
"temporary/checkBox_5": "false",
"temporary/checkBox_6": "true",
"temporary/checkBox_7": "true",
"temporary/checkBox_8": "false",
"temporary/checkBox_9": "false",
"temporary/checkBox_10": "false",
}

qss = '''*{font-family: Microsoft YaHei; font-size: 10pt;}

QTableView::item:selected {background: rgb(240, 116, 100); color: white; border: 0px;}

#page_8, #page_5, #page_3, #page_7, #page_display {
	background-color: #A0A0A0;
}

#widget_container, #widget_container2, #widget_container3 {
	background-color: #E8E8EA;
}

QComboBox {
    border: 1px solid gray;
    border-radius: 3px;
    padding: 1px 2px 1px 2px;
    min-width: 7 em;
    background-color: white;
    height: 30px;
    selection-background-color: #BDD7FD;
    selection-color: black;
    /* border-top-color: rgb(218, 216, 216) */
    combobox-popup: 0;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    /* width: 20px; */
    border-left-width: 1px;
    border-left-color: darkgray;
    border-left-style: solid; /* just a single line */
    border-top-right-radius: 3px; /* same radius as the QComboBox */
    border-bottom-right-radius: 3px;
}

QComboBox::down-arrow{
	border-image: url(:/picture/resourses/1485528481_arrow-down-01.png);
}

QComboBox QAbstractItemView::item:selected{background-color: #BDD7FD;}


QPushButton {
border-style:none;
border:1px solid #B2B6B9;
color:#000000;
padding:3px;
min-height:15px;
border-radius:5px;
background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #E1E4E6,stop:1 #CCD3D9);
}
QPushButton:hover {
background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #E5F1FB,stop:1 #E5F1FB);
}
QPushButton:pressed {
background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #CCE4F7,stop:1 #CCE4F7);
}

QPushButton#pushButton_partition {
border-radius: 3px;
padding: 1px 2px 1px 2px;
min-width: 7 em;
border-style:none;
border:1px solid #B2B6B9;
color:#000000;
/* font: 12px;
height: 30px; */
background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #E1E4E6,stop:1 #CCD3D9);
}
QPushButton#pushButton_partition:hover {
background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #E5F1FB,stop:1 #E5F1FB);
}
QPushButton#pushButton_partition:pressed, QPushButton#pushButton_partition:checked  {
background: #A4D6D8;
}


QPushButton#pushButton_3, QPushButton#pushButton_4, QPushButton#pushButton_22{
border-image: url(:/picture/resourses/Open_folder_add_512px_1186192_easyicon.net.png);
padding: 1px;
margin-bottom: 2px;
background: none;
border: 2px solid #B2B6B9;
border-radius: 1px;
min-height: 30px;
min-width: 30px;
}
QPushButton#pushButton_3:hover:!pressed, QPushButton#pushButton_4:hover:!pressed, QPushButton#pushButton_22:hover:!pressed
{
  border: 1px solid red;
}
QPushButton#pushButton_3:disabled, QPushButton#pushButton_4:disabled, QPushButton#pushButton_22:disabled 
{
    border-image: url(:/picture/resourses/disabled_file.png); 
}

QPushButton#pushButton_input1, QPushButton#pushButton_input2{
    border: 1px solid gray;
    border-radius: 3px;
    padding: 1px 2px 1px 2px;
    min-width: 7 em;
    background-color: white;
    /* font: 12px;
    height: 30px; */
    text-align: left;
    }

/* #pushButton_lng {
border-style:none;
border:none;
background:none;
}
#pushButton_lng:hover, #pushButton_lng:pressed {
background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #E1E4E6,stop:1 #CCD3D9);
} */

/* QPushButton::menu-indicator {
subcontrol-position: right center;
right: 5px;
} */

QPushButton::menu-indicator {
    subcontrol-position: right center;
    subcontrol-origin: padding;
    width: 15px;
    /* height: 15px; */
    right: 5px;
    border-left: 1px solid gray;
    border-image: url(:/picture/resourses/1485528481_arrow-down-01.png);
}


QToolButton::menu-indicator{
subcontrol-position: right center;
right: 5px;
}


QPushButton QMenu::separator
{
    height: 1px;
    border-bottom: 1px solid lightGray;
    background: #5A5A5A;
    margin-left: 2px;
    margin-right: 0px;
    margin-top: 2px;
    margin-bottom: 2px;
 }

/*
QToolButton#toolButton_start {
    margin-left:24px;
}
*/

QProgressBar{
min-height:20px;
background:#E1E4E6;
border-radius:5px;
text-align:center;
border:1px solid #E1E4E6;
}

QProgressBar:chunk{
border-radius:5px;
background-color:rgb(76, 169, 106);
}

QGroupBox{
border:1px solid #B2B6B9;
border-radius:5px;
margin-top:3ex;
}

QGroupBox::title{
subcontrol-origin: margin;
subcontrol-position: relative;
left:10px;
}
QGroupBox::indicator,QTreeWidget::indicator,QListWidget::indicator{
padding:0px -3px 0px 3px;
}
QGroupBox::indicator,QTreeWidget::indicator,QListWidget::indicator{
width:13px;
height:13px;
}

/* QGroupBox#groupBox_top_line {
border-top:1px solid #B2B6B9;
}

QGroupBox#groupBox_top_line::title{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    } */

QDialog QDialogButtonBox
{
dialogbuttonbox-buttons-have-icons: 1;
dialog-ok-icon: url(:/picture/resourses/btn_ok.png);
dialog-cancel-icon: url(:/picture/resourses/btn_close.png);
dialog-close-icon: url(:/picture/resourses/btn_close.png);
dialog-discard-icon: url(:/picture/resourses/btn_close.png);
dialog-no-icon: url(:/picture/resourses/btn_close.png);
dialog-yes-icon: url(:/picture/resourses/btn_ok.png);
dialog-apply-icon: url(:/picture/resourses/Adobe Version Cue.png);
dialog-reset-icon: url(:/picture/resourses/label_new green.png);
}
QMessageBox
{
messagebox-information-icon: url(:/picture/resourses/msg_info.png);
messagebox-question-icon: url(:/picture/resourses/msg_question.png);
messagebox-critical-icon: url(:/picture/resourses/msg_error.png);
messagebox-warning-icon: url(:/picture/resourses/480px-Lol_exclam.png);
background-color: white;
border: .5px solid #C1BFBF;
border-radius:3px;
margin: 5px;
padding: 5px;
messagebox-text-interaction-flags: 5;
}

QInputDialog QPushButton, QMessageBox QPushButton{
border-style:none;
border:1px solid #B2B6B9;
color:#000000;
padding:4px;
min-height:10px;
min-width: 65px;
border-radius:5px;
background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #E1E4E6,stop:1 #CCD3D9);
}

QInputDialog QPushButton:hover, QMessageBox QPushButton:hover{
background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #E5F1FB,stop:1 #E5F1FB);
}

QInputDialog QPushButton:pressed, QMessageBox QPushButton:pressed{
background:qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #CCE4F7,stop:1 #CCE4F7);
}

QFileDialog QWidget::item:hover {background-color: #BDD7FD; color: black;}
QFileDialog QWidget::item:selected {background-color: #BDD7FD; color: black} 

QTreeView {
    selection-color: black; 
    selection-background-color: #BDD7FD;
}

QTreeView::branch:has-siblings:!adjoins-item {
    border-image: url(:/picture/resourses/vline.png) 0;
}

QTreeView::branch:has-siblings:adjoins-item {
    border-image: url(:/picture/resourses/branch-more.png) 0;
}

QTreeView::branch:!has-children:!has-siblings:adjoins-item {
    border-image: url(:/picture/resourses/branch-end.png) 0;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    border-image: none;
    image: url(:/picture/resourses/branch-closed.png);
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings  {
    border-image: none;
    image: url(:/picture/resourses/branch-open.png);
}	
QTreeView::node {
border-image: none;
image: url(:/picture/resourses/msg_info.png);
}

QLineEdit {
    border: 1px solid gray;  
    border-radius: 3px; 
    background: white;  
    selection-background-color: green; 
    selection-color:white;
    height: 30px;
}

QLineEdit:hover {
    border: 1px solid blue;  
}

QAbstractSpinBox:focus, QAbstractSpinBox:hover{
border: 1px solid blue;
}
QAbstractSpinBox {  
    border:1px solid #B2B6B9;
	border-radius:3px;
	padding:2px; 
    background:white;
    selection-background-color: green;
    selection-color:white;
    min-width: 60px;
}  
  
QAbstractSpinBox:up-button  
{  
    background-color: transparent;  
    subcontrol-origin: border;  
    subcontrol-position: center right;  
}  
  
QAbstractSpinBox:down-button  
{  
    background-color: transparent;  
    subcontrol-origin: border;  
    subcontrol-position: center left; 
}  
  
QAbstractSpinBox::up-arrow,QAbstractSpinBox::up-arrow:disabled,QAbstractSpinBox::up-arrow:off {  
    image: url(:/picture/resourses/up_arrow_disabled.png);  
    width: 10px;  
    /* height: 10px;   */
}  
QAbstractSpinBox::up-arrow:hover  
{  
    image: url(:/picture/resourses/up_arrow.png);  
}  
  
  
QAbstractSpinBox::down-arrow,QAbstractSpinBox::down-arrow:disabled,QAbstractSpinBox::down-arrow:off  
{  
    image: url(:/picture/resourses/down_arrow_disabled.png);  
    width: 10px;  
    /* height: 10px;   */
}  
QAbstractSpinBox::down-arrow:hover  
{  
    image: url(:/picture/resourses/down_arrow.png);  
}  

QCheckBox  
{  
    spacing: 2px;  
    outline: none;  
    color: black;  
    margin-bottom: 2px; 
}   
 
QCheckBox:disabled  
{  
    color: #76797C;  
}  
 
QCheckBox::indicator,  
QGroupBox::indicator  
{  
    width: 17px;  
    height: 17px;  
} 

QCheckBox::indicator:unchecked  
{  
    image: url(:/checkbox/resourses/Checkbox/checkbox_unchecked_focus.png);
    border: 1px solid transparent;
}  
  
QCheckBox::indicator:unchecked:hover,  
/* QCheckBox::indicator:unchecked:focus,   */
QCheckBox::indicator:unchecked:pressed,  
QGroupBox::indicator:unchecked:hover,  
/* QGroupBox::indicator:unchecked:focus,   */
QGroupBox::indicator:unchecked:pressed  
{  
    border: 2px solid transparent;
    image: url(:/checkbox/resourses/Checkbox/checkbox_unchecked_focus.png);  
}  
  
QCheckBox::indicator:checked  
{  
    image: url(:/checkbox/resourses/Checkbox/checkbox_checked_focus.png);
    border: 1px solid transparent;
}  
  
QCheckBox::indicator:checked:hover,  
/* QCheckBox::indicator:checked:focus,   */
QCheckBox::indicator:checked:pressed,  
QGroupBox::indicator:checked:hover,  
/* QGroupBox::indicator:checked:focus,   */
QGroupBox::indicator:checked:pressed  
{  
  border: 2px solid transparent;
  image: url(:/checkbox/resourses/Checkbox/checkbox_checked_focus.png);  
}  
  
  
QCheckBox::indicator:indeterminate  
{  
    image: url(:/checkbox/resourses/Checkbox/checkbox_indeterminate.png);  
}  
  
QCheckBox::indicator:indeterminate:focus,  
QCheckBox::indicator:indeterminate:hover,  
QCheckBox::indicator:indeterminate:pressed  
{  
    image: url(:/checkbox/resourses/Checkbox/checkbox_indeterminate_focus.png);  
}  
  
QCheckBox::indicator:checked:disabled,  
QGroupBox::indicator:checked:disabled  
{  
    image: url(:/checkbox/resourses/Checkbox/checkbox_checked.png);  
}  
  
QCheckBox::indicator:unchecked:disabled,  
QGroupBox::indicator:unchecked:disabled  
{  
    image: url(:/checkbox/resourses/Checkbox/checkbox_unchecked.png);  
}
  
  
  
QRadioButton  
{  
    spacing: 5px;  
    outline: none;  
    color: black;  
    margin-bottom: 2px;  
}  
  
QRadioButton:disabled  
{  
    color: #76797C;  
}  
/* QRadioButton::indicator  
{  
    width: 26px;  
    height: 26px;  
}   */
  
QRadioButton::indicator:unchecked  
{  
    image: url(:/checkbox/resourses/Checkbox/radio_unchecked.png);  
}  
  
  
QRadioButton::indicator:unchecked:hover,  
QRadioButton::indicator:unchecked:focus,  
QRadioButton::indicator:unchecked:pressed  
{  
    border: none;  
    outline: none;  
    image: url(:/checkbox/resourses/Checkbox/radio_unchecked_focus.png);  
}  
  
QRadioButton::indicator:checked  
{  
    border: none;  
    outline: none;  
    image: url(:/checkbox/resourses/Checkbox/radio_checked_focus.png);  
}  
  
QRadioButton::indicator:checked:hover,  
QRadioButton::indicator:checked:focus,  
QRadioButton::indicator:checked:pressed  
{  
    border: none;  
    outline: none;  
    image: url(:/checkbox/resourses/Checkbox/radio_checked_focus.png);  
}  
  
QRadioButton::indicator:checked:disabled  
{  
    outline: none;  
    image: url(:/checkbox/resourses/Checkbox/radio_checked.png);  
}  
  
QRadioButton::indicator:unchecked:disabled  
{  
    image: url(:/checkbox/resourses/Checkbox/radio_unchecked.png); 
     
}  


Qlabel#label_flow_sum, Qlabel#label_flow_resul 
{
    font: bold 25px;
}

QTextEdit{
    selection-color: white; 
    selection-background-color: rgb(238, 101, 83);
    font-family: "Courier New" 
}

QPlainTextEdit{
    selection-color: white;
    selection-background-color: rgb(238, 101, 83);
    font-family: "Courier New"
}

#topWidget , TestWidget
    {
        color: #eff0f1;
        background-color: #F0F0F0;
        /* selection-background-color:#3daee9; */
        selection-color: #eff0f1;
        background-clip: border;
        border-image: none;
        /* border: 0px transparent black; */
        outline: 0;
        border-bottom: 2px ridge #B9B9B9;
        border-left: 2px dotted #B9B9B9;
        border-right: 2px dotted #B9B9B9;    
    }
TestWidget > QPushButton{
    border-width: 1px;
    
}    
   
    
QWidget #topWidget >QWidget:hover , TestWidget:hover
    {
        background-color: #D8E6F2;
        color: #eff0f1;
    }

/* QWidget #topWidget >QWidget:pressed
    {
        background-color: rgb(6, 64, 114);
        border: 1px solid red;
    } not worked*/

BaseMenuWidget{

        border:1px solid rgb(17, 66, 116);
    }

BaseButton 
{
    background-color: transparent;
    border: none;
}

BaseButton:hover {
    background:transparent;
    }

BaseTable {
    border: 0px none transparent;
    border-radius: 15px;
    background-color: #FFFFFF;
}

BaseTable::item:hover {
    background-color: #D8E6F2;
    border: 1px solid transparent;
}


BaseTable::item:pressed {
    background-color:  rgb(229, 236, 243);
    border: 1px solid transparent;
}

BaseTable::item:selected:active 
{
    background-color: #D8E6F2;
    color: #000000;
    border: 0px none transparent;
}

#settings_widget {
    border-left: 2px dotted #B9B9B9;
}


QToolTip { 
    /* color: #ffffff; 
    background-color: #0078D7; */
    border: 1px solid white;
    min-height: 20px;
    }


QListView{outline: 0; }
QListView::item:selected:active{color: #000000}
/* QListView::item:hover {background: #BDD7FD} */

QDateEdit
{
    border: 1px solid gray;
    border-radius: 3px;
    padding: 1px 2px 1px 2px;
    min-width: 7 em;
    background-color: white;
    /* font: 12px;
	height: 30px; */
}


QDateEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 1px;
    border-left-color: darkgray;
    border-left-style: solid; /* just a single line */
    border-top-right-radius: 3px; /* same radius as the QComboBox */
    border-bottom-right-radius: 3px;
}


QListWidget {
    selection-color: black; 
    selection-background-color: #BDD7FD;
}


/* QDateEdit::down-arrow {
    border-image: url(:/picture/resourses/1485528481_arrow-down-01.png);
    height:15px;
    width:15px;
  } */

/*QTextEdit#textEdit_flowchart {font-family: "Times New Roman";
                              font-size:16 px}*/


/* 
QListWidget
{
    border:1px solid gray; 
    color:black;     
}


QListWidget::item:hover
{
    show-decoration-selected:5;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #FAFBFE, stop: 1 #DCDEF1);
}

QListWidget::item:selected
{
    background:skyblue;
    padding:0px;
    margin:0px;
    color:red;
}

QListWidget::item:selected:!active
{
    border-width:0px;
    background:lightgreen;
}



QListWidget#listWidget_workflow::item:hover
{
    show-decoration-selected:none;
    background: none
}

QListWidget#listWidget_workflow::item:selected
{
    background:none;
    padding:0px;
    margin:0px;
    color:none;
}

QListWidget#listWidget_workflow::item:selected:!active
{
    border-width:0px;
    background:none;
} */

QToolBox  {
    padding: 2px;
    border: 1px transparent black;
    background-color: white;
}

QToolBox QWidget {
    background-color: white;
}

QToolBox::tab {
    color: #000000;
    background-color: qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #E1E4E6,stop:1 #CCD3D9);
    border: 1px solid #76797C;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
}

QToolBox::tab:selected { /* italicize selected tabs */
    font: italic;
    background-color: qlineargradient(spread:pad,x1:0,y1:0,x2:0,y2:1,stop:0 #E1E4E6,stop:1 #CCD3D9);
    border-color: #3daee9;
 }'''
