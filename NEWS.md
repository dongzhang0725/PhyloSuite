# Release Note

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


