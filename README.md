# PhyloSuite
PhyloSuite is an integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. It combines the functions of two previous tools: MitoTool (https://github.com/dongzhang0725/MitoTool) and BioSuite (https://github.com/dongzhang0725/BioSuite).

The interface and the main functions of PhyloSuite.  

![main_functions.jpg](https://github.com/dongzhang0725/PhyloSuite_tutorial/blob/master/images/main_functions.jpg?raw=true)

The workflow diagram of PhyloSuite.  

![flowchart.jpg](https://github.com/dongzhang0725/PhyloSuite_tutorial/blob/master/images/flowchart.jpg?raw=true)

The summary of flowchart and references of used programs.  

![flowchart_summary.jpg](https://github.com/dongzhang0725/PhyloSuite_tutorial/blob/master/images/flowchart_summary.jpg?raw=true)

## Homepage

https://dongzhang0725.github.io or http://phylosuite.jushengwu.com/ (China)

## Installation

### 1. Install compiled PhyloSuite 

Installers for all platforms can be downloaded from https://github.com/dongzhang0725/PhyloSuite/releases.

<a id="download" href="https://github.com/dongzhang0725/PhyloSuite/releases"><i class="fa fa-download"></i><span> Download Now</span> </a>

<a id="download" href="http://phylosuite.jushengwu.com/dongzhang0725.github.io/installation/#Chinese_download_link"><i class="fa fa-download"></i><span> Chinese download links</span> </a>

#### 1.1. Windows
Windows 7, 8 and 10 are supported, just double click the `PhyloSuite_xxx_win_setup.exe` to install, and run “PhyloSuite.exe” file after the installation. If the installation fails, download `PhyloSuite_xxx_Win.rar`, unzip it, and run PhyloSuite directly from this folder.

#### 1.2. Mac OSX &&nbsp;Linux
Unzip `PhyloSuite_xxx_Mac.zip/PhyloSuite_xxx_Linux.tar.gz` to anywhere you like, and double click “PhyloSuite” (in PhyloSuite folder) to start, or use the following command: 

```
cd path/to/PhyloSuite
./PhyloSuite
 ```
If you encounter an error of "permission denied", try to use the following command:

```
chmod -R 755 path/to/PhyloSuite(folder)
 ```

<span style="color:red">Note that both 64 bit and 32 bit Windows is supported (Windows 7 and above), whereas only 64 bit has been tested in Linux (Ubuntu 14.04.1 and above) and Mac OSX (macOS Sierra version 10.12.3 and above).</span>

### 2. Install using pip

First, Python (version higher than 3.6) should be installed and added to the environment variable in your computer. Then open the terminal and type:

```
pip install PhyloSuite
```

It will take some time to install. If it installs successfully, PhyloSuite will be automatically added to the environment variables. Then open the terminal again and type:
 ```
 PhyloSuite
 ```

If the above `pip` command failed to install PhyloSuite, you can use compiled PhyloSuite (see `section 1`) or find and download the source codes here (https://pypi.org/project/PhyloSuite/#files or https://github.com/dongzhang0725/PhyloSuite), and install it manually.

### 3. Install manually

Similarly, Python (version higher than 3.6) should be pre-installed and added to the environment variable in your computer. If it is, then download the PhyloSuite from github, either using `git clone https://github.com/dongzhang0725/PhyloSuite.git` or use the `Clone or download`-->`Download ZIP` button in https://github.com/dongzhang0725/PhyloSuite.
After that, change your directory to the `PhyloSuite` folder that contains the `setup.py` file, then type:

```
python setup.py install
```

## Examples

https://raw.githubusercontent.com/dongzhang0725/PhyloSuite/master/example.zip

## Bug report

[Google group](https://groups.google.com/forum/#!forum/phylosuite), [Github issue](https://github.com/dongzhang0725/PhyloSuite/issues) or send email to dongzhang0725@gmail.com.

## Citation
Zhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096. (Download as: <a href="https://raw.githubusercontent.com/dongzhang0725/PhyloSuite/master/PhyloSuite/PhyloSuite_citation.ris">RIS</a>   <a href="https://raw.githubusercontent.com/dongzhang0725/PhyloSuite/master/PhyloSuite/PhyloSuite_citation.xml">XML</a>   <a href="https://raw.githubusercontent.com/dongzhang0725/PhyloSuite/master/PhyloSuite/PhyloSuite_citation.enw">ENW</a>)

