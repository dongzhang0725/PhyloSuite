# Release Note

## PhyloSuite v1.2.2 (2020-08-06, Thursday)
+ Fixed some bugs in MACSE, PartitionFinder, MrBayes and IQ-TREE plugins
+ Added a function to continue previous analyses for IQ-TREE and ModelFinder
+ Added a new homepage for Chinese users (http://phylosuite.jushengwu.com/)
+ Added a user-friendly partition editor for PartitionFinder and ModelFinder
+ Added an option to specify start gene for gene order figure in “Extract” function
+ Added an option to restore the settings to default
+ Updated MAFFT and IQ-TREE to newest versions

## PhyloSuite v1.2.1 (2020-01-06, Mon)
+ Updated citation for PhyloSuite
+ Added launch image
+ Changed the icon
+ Added a google group for PhyloSuite
+ Fixed a bug that caused PhyloSuite to crash when there are too large data in one workplace 
+ Added shortcuts for available downstream analyses for each function (after it is finished)
+ Added context menu for each results folder to import the results into downstream functions 
+ Added the option of different settings for each project
+ Added AA model for Beast to the Modelfinder analysis
+ Added an option that allows users to export/import taxonomy settings
+ Added a sorting function to Concatenation
+ Added several resources for plugins installation
+ Added a function to reorder the GenBank file
+ Added a function to change the font in PhyloSuite
+ Optimized some functions

## PhyloSuite v1.1.16 (2019-08-12, Mon)
+ Enabled IQ-TREE to select multiple outgroups
+ Added overlapping and intergenic regions to extraction function
+ Added MACSE, an alignment software which preserves reading frame and allows incorporation of sequencing errors or sequences with frameshifts (Ranwez V, Douzery EJP, Cambon C, Chantret N, Delsuc F. 2018. MACSE v2: Toolkit for the alignment of coding sequences accounting for frameshifts and stop codons. Mol Biol Evol. 35: 2582-2584. doi: 10.1093/molbev/msy159.)
+ Added trimAl, a tool for the automated removal of spurious sequences or poorly aligned regions from a multiple sequence alignment (Capella-Gutierrez S, Silla-Martinez JM, Gabaldon T. 2009. trimAl: a tool for automated alignment trimming in large-scale phylogenetic analyses. Bioinformatics. 25: 1972-1973. doi: 10.1093/bioinformatics/btp348.)
+ Added HmmCleaner, a tool for removing low similarity segments from the MSA (Di Franco A, Poujol R, Baurain D, Philippe H. 2019. Evaluating the usefulness of alignment filtering methods to reduce the impact of errors on evolutionary inferences. BMC Evol Biol. 19: 21. doi: 10.1186/s12862-019-1350-2.)
+ Added above three softwars to flowchart function
+ Added a function to incrementally input files
+ Fixed coding problem
+ Fixed some bugs

## PhyloSuite v1.1.153 (2019-05-17, Sun, <font color="red">BUG fix for v1.1.15</font>)
+ Fixed a bug that caused PhyloSuite to crash on MAC and Linux
    + Added test run
    + Added strand-specific statistics to mitogenome extraction function 
    + Fixed bugs in the 'Extract' function
    + Fixed a bug that caused Gblocks to crash
    + Canceled "+R" when calculating the best-fit model for BEAST
    + Added an exclusion function when customizing taxonomy recognition
    + Fixed a bug that caused incompatibility issues with MrBayes 3.2.7
    + Added rename, drag and drop functions for the file explorer in the main page of PhyloSuite
    + Added a function to extract chloroplast genome (thanks to Dr. Kai-Kai Meng)
    + Made a homepage for PhyloSuite (https://dongzhang0725.github.io)
    + Added a funtion to clear "misc_feature" in "Standardization" function
    + Fixed a bug that caused IQ-TREE and MrBayes to fail recognizing the outgroup
    + Added a function to draw a linear figure in "Concatenation"
    + Added the ability to allow mutiple results of each function, instead of overwriting them 
    + Added a function to reconstruct phylogenetic trees in batches using IQ-TREE 
    + Added a function to search sequences in the nucleotide and protein databases of NCBI
    + Optimized and upgraded the function of input files into PhyloSuite, see https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/five_ways_to_import/
    + Added a multi-thread MrBayes run option to the Linux version
    + Enabled the Flowchart function to save different settings as workflow
    + Allowed spaces in the software and workplace paths
    + Changed the interfaces of some functions
    + Enabled MrBayes to infer the tree at any generation
    + Enabled user to customize the sequence name when extracting sequence

## PhyloSuite v1.1.152 (2019-05-12, Sun, <font color="red">BUG fix</font>)
+ Added test run
+ Added strand-specific statistics to mitogenome extraction function 
+ Fixed bugs in the 'Extract' function
+ Fixed a bug that caused Gblocks to crash
+ Canceled "+R" when calculating the best-fit model for BEAST
+ Added an exclusion function when customizing taxonomy recognition
+ Fixed a bug that caused incompatibility issues with MrBayes 3.2.7
+ Added rename, drag and drop functions for the file explorer in the main page of PhyloSuite
+ Added a function to extract chloroplast genome (thanks to Dr. Kai-Kai Meng)
    + Made a homepage for PhyloSuite (https://dongzhang0725.github.io)
    + Added a funtion to clear "misc_feature" in "Standardization" function
    + Fixed a bug that caused IQ-TREE and MrBayes to fail recognizing the outgroup
    + Added a function to draw a linear figure in "Concatenation"
    + Added the ability to allow mutiple results of each function, instead of overwriting them 
    + Added a function to reconstruct phylogenetic trees in batches using IQ-TREE 
    + Added a function to search sequences in the nucleotide and protein databases of NCBI
    + Optimized and upgraded the function of input files into PhyloSuite, see https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/five_ways_to_import/
    + Added a multi-thread MrBayes run option to the Linux version
    + Enabled the Flowchart function to save different settings as workflow
    + Allowed spaces in the software and workplace paths
    + Changed the interfaces of some functions
    + Enabled MrBayes to infer the tree at any generation
    + Enabled user to customize the sequence name when extracting sequence


## PhyloSuite v1.1.151 (2019-03-28, Thu, <font color="red">BUG fix</font>)
+ Added compiled PartitionFinder2 (MAC and Window only), which doesn't rely on Python 2.7 any more
+ Optimized plugins download and configuration, and added a demo tutorial for this (https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/how-to-configure-plugins/)
+ Fixed a bug that caused MAFFT to crash
+ Fixed bugs in "Concatenation", "Search in NCBI", and "Fasta file import" functions
    + Made a homepage for PhyloSuite (https://dongzhang0725.github.io)
    + Added a funtion to clear "misc_feature" in "Standardization" function
    + Fixed a bug that caused IQ-TREE and MrBayes to fail recognizing the outgroup
    + Added a function to draw a linear figure in "Concatenation"
    + Added the ability to allow mutiple results of each function, instead of overwriting them 
    + Added a function to reconstruct phylogenetic trees in batches using IQ-TREE 
    + Added a function to search sequences in the nucleotide and protein databases of NCBI
    + Optimized and upgraded the function of input files into PhyloSuite, see https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/five_ways_to_import/
    + Added a multi-thread MrBayes run option to the Linux version
    + Enabled the Flowchart function to save different settings as workflow
    + Allowed spaces in the software and workplace paths
    + Changed the interfaces of some functions
    + Enabled MrBayes to infer the tree at any generation
    + Enabled user to customize the sequence name when extracting sequence


## PhyloSuite v1.1.15 (2019-03-08, Fri)
+ Made a homepage for PhyloSuite (https://dongzhang0725.github.io)
+ Added a funtion to clear "misc_feature" in "Standardization" function
+ Fixed a bug that caused IQ-TREE and MrBayes to fail recognizing the outgroup
+ Added a function to draw a linear figure in "Concatenation"
+ Added the ability to allow mutiple results of each function, instead of overwriting them 
+ Added a function to reconstruct phylogenetic trees in batches using IQ-TREE 
+ Added a function to search sequences in the nucleotide and protein databases of NCBI
+ Optimized and upgraded the function of input files into PhyloSuite, see https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/five_ways_to_import/
+ Added a multi-thread MrBayes run option to the Linux version
+ Enabled the Flowchart function to save different settings as workflow
+ Allowed spaces in the software and workplace paths
+ Changed the interfaces of some functions
+ Enabled MrBayes to infer the tree at any generation
+ Enabled user to customize the sequence name when extracting sequence

## PhyloSuite v1.1.141 (2019-01-09, Wed, <font color="red">BUG fix</font>)
+ Fixed the bug that caused "Flowchart" function to crash
    + Shielded the folder/files which are irrelevant to the workplace
    + Fixed the bug that caused the results of PartitionFinder to be unrecognized by MrBayes and IQ-TREE on MAC and Linux
    + Added outgroup parameters to IQ-TREE
    + Added a function to view and/or edit the command of IQ-TREE and ModelFinder before starting
    + Added a parameter to "Draw RSCU Figure" function, which can define the maximum value of y-axis
    + Fixed the bug that the child-window of PhyloSuite cannot be resized by mouse on MAC
    + Added a function to check the validity of the path of plugins, workplace and input file for each functions, and made the warning clearer
    + Added "–adjustdirectionaccurately" and "–adjustdirection" parameters to MAFFT
    + Fixed the bug that prevented the sequences to be reordered more than once in the "Concatenation" function on MAC
    + Added "Reminder settings" to "Settings-->Settings" function
    + Fixed the bug that disabled the "Continue Previous Analysis" function of MrBayes
    + Added "Default" and "Custom" options to "Extracter" function, which can extract the entire sequence and specific features, respectively

## PhyloSuite v1.1.14 (2019-01-06, Sun)
+ Shielded the folder/files which are irrelevant to the workplace
+ Fixed the bug that caused the results of PartitionFinder to be unrecognized by MrBayes and IQ-TREE on MAC and Linux
+ Added outgroup parameters to IQ-TREE
+ Added a function to view and/or edit the command of IQ-TREE and ModelFinder before starting
+ Added a parameter to "Draw RSCU Figure" function, which can define the maximum value of y-axis
+ Fixed the bug that the child-window of PhyloSuite cannot be resized by mouse on MAC
+ Added a function to check the validity of the path of plugins, workplace and input file for each functions, and made the warning clearer
+ Added "–adjustdirectionaccurately" and "–adjustdirection" parameters to MAFFT
+ Fixed the bug that prevented the sequences to be reordered more than once in the "Concatenation" function on MAC
+ Added "Reminder settings" to "Settings-->Settings" function
+ Fixed the bug that disabled the "Continue Previous Analysis" function of MrBayes
+ Added "Default" and "Custom" options to "Extracter" function, which can extract the entire sequence and specific features, respectively

## PhyloSuite v1.1.132 (2018-12-09, Sun, <font color="red">BUG fix</font>)
+ Fixed an error when using "Draw RSCU figure" function in MAC (for v1.1.13)
+ Fixed an error when using "Compare Table" function in MAC and Linux (for v1.1.13)
+ Optimized some functions
    - Added warning when deleting old results 
    - Added a function to shorten the partition name in the results of ModelFinder automatically when using it for MrBayes
    - Enabled viewing the contents of results folder in the display area
    - Added a function to check the validity of the path of PhyloSuite as well as plugins
    - Added a user manual to the PhyloSuite/manual folder
    - Added example link to the PhyloSuite main window
    - Fixed the bug of 'UnicodeEncodeError' when opening files
    - Fixed some other small bugs
    - Added LICENSE file

## PhyloSuite v1.1.131 (2018-12-09, Sun, <font color="red">BUG fix</font>)
+ Fixed the error when using "AUTO" model in IQ-TREE (for v1.1.13)
    - Added warning when deleting old results 
    - Added a function to shorten the partition name in the results of ModelFinder automatically when using it for MrBayes
    - Enabled viewing the contents of results folder in the display area
    - Added a function to check the validity of the path of PhyloSuite as well as plugins
    - Added a user manual to the PhyloSuite/manual folder
    - Added example link to the PhyloSuite main window
    - Fixed the bug of 'UnicodeEncodeError' when opening files
    - Fixed some other small bugs
    - Added LICENSE file

## PhyloSuite v1.1.13 (2018-12-09, Sun)
+ Added warning when deleting old results 
+ Added a function to shorten the partition name in the results of ModelFinder automatically when using it for MrBayes
+ Enabled viewing the contents of results folder in the display area
+ Added a function to check the validity of the path of PhyloSuite as well as plugins
+ Added a user manual to the PhyloSuite/manual folder
+ Added example link to the PhyloSuite main window
+ Fixed the bug of 'UnicodeEncodeError' when opening files
+ Fixed some other small bugs
+ Added LICENSE file

## PhyloSuite v1.1.12 (2018-12-04, Tue)
+ Enabled MAFFT to align protein-coding genes with internal stop codons
+ Uniformized/replaced model names in ModelFinder, IQ-TREE and MrBayes
+ Added parameters check and autocorrection functions to Flowchart
+ Enabled PhyloSuite to run on MAC and Linux systems


