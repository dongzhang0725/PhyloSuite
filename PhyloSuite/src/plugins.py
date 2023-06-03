'''
更新步骤：
1. dict_url里面添加好各自的压缩包，同时把这些压缩包传到各自数据库的位置
2. dict_plugin_settings 里面添加新的plugin的信息，注意link那里，如果是有链接的，需要在LG_settings里面设置

'''


## 新插件的链接加到这里
import platform

dict_url = {
    "windows": {
        "64bit": {
            "Github": {
                "mafft": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/mafft-win64.zip",
                "Rscript": "https://cran.r-project.org/bin/windows/base/old/3.4.4/R-3.4.4-win.exe",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-Windows-x86_64.exe",
                "gblocks": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/Gblocks_win.zip",
                "iq-tree": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/iqtree-win64.zip",
                "MrBayes": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/mrbayes-win.zip",
                "compiled PF2": "https://media.githubusercontent.com/media/dongzhang0725/PhyloSuite_large_plugins/main/PartitionFinder_win64.zip",
                "PF2": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/partitionfinder.zip",
                "macse": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/macse.jar.zip",
                "trimAl": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/trimal.zip",
                "tbl2asn": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/tbl2asn.zip",
                "CodonW": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/Win32CodonW.zip",
                "ASTRAL": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/ASTRAL_win.zip",
                "ASTRAL-PRO": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/ASTRAL_win.zip",
                "FastTree": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/FastTree_win.zip",
                "plot engine": "https://media.githubusercontent.com/media/dongzhang0725/PhyloSuite_large_plugins/main/plot_engine_Win64.zip"
            },
            "Gitlab": {
                "mafft": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/mafft-win64.zip",
                "Rscript": "https://cran.r-project.org/bin/windows/base/old/3.4.4/R-3.4.4-win.exe",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-Windows-x86_64.exe",
                "gblocks": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/Gblocks_win.zip",
                "iq-tree": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/iqtree-win64.zip",
                "MrBayes": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/mrbayes-win.zip",
                "compiled PF2": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/PartitionFinder_win64.zip",
                "PF2": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/partitionfinder.zip",
                "macse": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/macse.jar.zip",
                "trimAl": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/trimal.zip",
                "tbl2asn": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/tbl2asn.zip",
                "CodonW": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/Win32CodonW.zip",
                "ASTRAL": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/ASTRAL_win.zip",
                "ASTRAL-PRO": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/ASTRAL_win.zip",
                "FastTree": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/FastTree_win.zip",
                "plot engine": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/plot_engine_Win64.zip"
            },
            "Coding": {
                "mafft": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/mafft-win64.zip",
                "Rscript": "https://cran.r-project.org/bin/windows/base/old/3.4.4/R-3.4.4-win.exe",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-Windows-x86_64.exe",
                "gblocks": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/Gblocks_win.zip",
                "iq-tree": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/iqtree-win64.zip",
                "MrBayes": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/mrbayes-win.zip",
                "compiled PF2": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/PartitionFinder_win64.zip",
                "PF2": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/partitionfinder.zip",
                "macse": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/macse.jar.zip",
                "trimAl": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/trimal.zip",
                "tbl2asn": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/tbl2asn.zip",
                "CodonW": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/Win32CodonW.zip",
                "ASTRAL": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/ASTRAL_win.zip",
                "ASTRAL-PRO": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/ASTRAL_win.zip",
                "FastTree": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/FastTree_win.zip",
                "plot engine": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/plot_engine_Win64.zip"
            },
            "Chinese resource": {
                "mafft": "http://phylosuite.jushengwu.com/plugins/mafft-win64.zip",
                "Rscript": "https://cran.r-project.org/bin/windows/base/old/3.4.4/R-3.4.4-win.exe",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-Windows-x86_64.exe",
                "gblocks": "http://phylosuite.jushengwu.com/plugins/Gblocks_win.zip",
                "iq-tree": "http://phylosuite.jushengwu.com/plugins/iqtree-win64.zip",
                "MrBayes": "http://phylosuite.jushengwu.com/plugins/mrbayes-win.zip",
                "compiled PF2": "http://phylosuite.jushengwu.com/plugins/PartitionFinder_win64.zip",
                "PF2": "http://phylosuite.jushengwu.com/plugins/partitionfinder.zip",
                "macse": "http://phylosuite.jushengwu.com/plugins/macse.jar.zip",
                "trimAl": "http://phylosuite.jushengwu.com/plugins/trimal.zip",
                "tbl2asn": "http://phylosuite.jushengwu.com/plugins/tbl2asn.zip",
                "CodonW": "http://phylosuite.jushengwu.com/plugins/Win32CodonW.zip",
                "ASTRAL": "http://phylosuite.jushengwu.com/plugins/ASTRAL_win.zip",
                "ASTRAL-PRO": "http://phylosuite.jushengwu.com/plugins/ASTRAL_win.zip",
                "FastTree": "http://phylosuite.jushengwu.com/plugins/FastTree_win.zip",
                "plot engine": "http://phylosuite.jushengwu.com/plugins/plot_engine_Win64.zip"
            }
        },
        "32bit": {
            "Github": {
                "mafft": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/mafft-win32.zip",
                "Rscript": "https://cran.r-project.org/bin/windows/base/old/3.4.4/R-3.4.4-win.exe",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-Windows-x86.exe",
                "gblocks": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/Gblocks_win.zip",
                "iq-tree": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/iqtree-win32.zip",
                "MrBayes": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/mrbayes-win.zip",
                "compiled PF2": "https://media.githubusercontent.com/media/dongzhang0725/PhyloSuite_large_plugins/main/PartitionFinder_win32.zip",
                "PF2": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/partitionfinder.zip",
                "macse": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/macse.jar.zip",
                "trimAl": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/trimal.zip",
                "tbl2asn": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/tbl2asn.zip",
                "CodonW": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/Win32CodonW.zip",
                "ASTRAL": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/ASTRAL_win.zip",
                "ASTRAL-PRO": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/ASTRAL_win.zip",
                "FastTree": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/FastTree_win.zip",
                "plot engine": "https://media.githubusercontent.com/media/dongzhang0725/PhyloSuite_large_plugins/main/plot_engine_Win32.zip"
            },
            "Gitlab": {
                "mafft": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/mafft-win32.zip",
                "Rscript": "https://cran.r-project.org/bin/windows/base/old/3.4.4/R-3.4.4-win.exe",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-Windows-x86.exe",
                "gblocks": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/Gblocks_win.zip",
                "iq-tree": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/iqtree-win32.zip",
                "MrBayes": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/mrbayes-win.zip",
                "compiled PF2": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/PartitionFinder_win32.zip",
                "PF2": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/partitionfinder.zip",
                "macse": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/macse.jar.zip",
                "trimAl": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/trimal.zip",
                "tbl2asn": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/tbl2asn.zip",
                "CodonW": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/Win32CodonW.zip",
                "ASTRAL": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/ASTRAL_win.zip",
                "ASTRAL-PRO": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/ASTRAL_win.zip",
                "FastTree": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/FastTree_win.zip",
                "plot engine": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/plot_engine_Win32.zip"
            },
            "Coding": {
                "mafft": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/mafft-win32.zip",
                "Rscript": "https://cran.r-project.org/bin/windows/base/old/3.4.4/R-3.4.4-win.exe",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-Windows-x86.exe",
                "gblocks": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/Gblocks_win.zip",
                "iq-tree": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/iqtree-win32.zip",
                "MrBayes": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/mrbayes-win.zip",
                "compiled PF2": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/PartitionFinder_win32.zip",
                "PF2": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/partitionfinder.zip",
                "macse": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/macse.jar.zip",
                "trimAl": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/trimal.zip",
                "tbl2asn": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/tbl2asn.zip",
                "CodonW": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/Win32CodonW.zip",
                "ASTRAL": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/ASTRAL_win.zip",
                "ASTRAL-PRO": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/ASTRAL_win.zip",
                "FastTree": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/FastTree_win.zip",
                "plot engine": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/plot_engine_Win32.zip"
            },
            "Chinese resource": {
                "mafft": "http://phylosuite.jushengwu.com/plugins/mafft-win32.zip",
                "Rscript": "https://cran.r-project.org/bin/windows/base/old/3.4.4/R-3.4.4-win.exe",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-Windows-x86.exe",
                "gblocks": "http://phylosuite.jushengwu.com/plugins/Gblocks_win.zip",
                "iq-tree": "http://phylosuite.jushengwu.com/plugins/iqtree-win32.zip",
                "MrBayes": "http://phylosuite.jushengwu.com/plugins/mrbayes-win.zip",
                "compiled PF2": "http://phylosuite.jushengwu.com/plugins/PartitionFinder_win32.zip",
                "PF2": "http://phylosuite.jushengwu.com/plugins/partitionfinder.zip",
                "macse": "http://phylosuite.jushengwu.com/plugins/macse.jar.zip",
                "trimAl": "http://phylosuite.jushengwu.com/plugins/trimal.zip",
                "tbl2asn": "http://phylosuite.jushengwu.com/plugins/tbl2asn.zip",
                "CodonW": "http://phylosuite.jushengwu.com/plugins/Win32CodonW.zip",
                "ASTRAL": "http://phylosuite.jushengwu.com/plugins/ASTRAL_win.zip",
                "ASTRAL-PRO": "http://phylosuite.jushengwu.com/plugins/ASTRAL_win.zip",
                "FastTree": "http://phylosuite.jushengwu.com/plugins/FastTree_win.zip",
                "plot engine": "http://phylosuite.jushengwu.com/plugins/plot_engine_Win32.zip"
            }
        }
    },
    "darwin": {
        "64bit": {
            "Github": {
                "mafft": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/mafft-mac64.zip",
                "Rscript": "https://cran.r-project.org/bin/macosx/R-3.5.1.pkg",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-MacOSX-x86_64.pkg",
                "gblocks": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/Gblocks_OSX_0.91b.zip",
                "iq-tree": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/iqtree-mac64.zip",
                "MrBayes": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/mrbayes-mac64.zip",
                "compiled PF2": "https://media.githubusercontent.com/media/dongzhang0725/PhyloSuite_large_plugins/main/PartitionFinder_mac.zip",
                "PF2": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/partitionfinder.zip",
                "macse": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/macse.jar.zip",
                "CodonW": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/MacOSCodonW.zip",
                "ASTRAL": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/ASTRAL_mac.zip",
                "ASTRAL-PRO": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/ASTRAL_mac.zip",
                "FastTree": "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite_plugins/master/FastTree_mac.zip",
                "plot engine": "https://media.githubusercontent.com/media/dongzhang0725/PhyloSuite_large_plugins/main/plot_engine_Mac.zip"
            },
            "Gitlab": {
                "mafft": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/mafft-mac64.zip",
                "Rscript": "https://cran.r-project.org/bin/macosx/R-3.5.1.pkg",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-MacOSX-x86_64.pkg",
                "gblocks": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/Gblocks_OSX_0.91b.zip",
                "iq-tree": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/iqtree-mac64.zip",
                "MrBayes": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/mrbayes-mac64.zip",
                "compiled PF2": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/PartitionFinder_mac.zip",
                "PF2": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/partitionfinder.zip",
                "macse": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/macse.jar.zip",
                "CodonW": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/MacOSCodonW.zip",
                "ASTRAL": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/ASTRAL_mac.zip",
                "ASTRAL-PRO": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/ASTRAL_mac.zip",
                "FastTree": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/FastTree_mac.zip",
                "plot engine": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/plot_engine_Mac.zip"
            },
            "Coding": {
                "mafft": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/mafft-mac64.zip",
                "Rscript": "https://cran.r-project.org/bin/macosx/R-3.5.1.pkg",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-MacOSX-x86_64.pkg",
                "gblocks": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/Gblocks_OSX_0.91b.zip",
                "iq-tree": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/iqtree-mac64.zip",
                "MrBayes": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/mrbayes-mac64.zip",
                "compiled PF2": "https://gitlab.com/PhyloSuite/PhyloSuite_plugins/raw/master/PartitionFinder_mac.zip",
                "PF2": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/partitionfinder.zip",
                "macse": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/macse.jar.zip",
                "CodonW": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/MacOSCodonW.zip",
                "ASTRAL": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/ASTRAL_mac.zip",
                "ASTRAL-PRO": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/ASTRAL_mac.zip",
                "FastTree": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/FastTree_mac.zip",
                "plot engine": "https://phylosuite.coding.net/p/PhyloSuite_plugins/d/PhyloSuite_plugins/git/raw/master/plot_engine_Mac.zip"
            },
            "Chinese resource": {
                "mafft": "http://phylosuite.jushengwu.com/plugins/mafft-mac64.zip",
                "Rscript": "https://cran.r-project.org/bin/macosx/R-3.5.1.pkg",
                "python27": "https://repo.continuum.io/archive/Anaconda2-5.2.0-MacOSX-x86_64.pkg",
                "gblocks": "http://phylosuite.jushengwu.com/plugins/Gblocks_OSX_0.91b.zip",
                "iq-tree": "http://phylosuite.jushengwu.com/plugins/iqtree-mac64.zip",
                "MrBayes": "http://phylosuite.jushengwu.com/plugins/mrbayes-mac64.zip",
                "compiled PF2": "http://phylosuite.jushengwu.com/plugins/PartitionFinder_mac.zip",
                "PF2": "http://phylosuite.jushengwu.com/plugins/partitionfinder.zip",
                "macse": "http://phylosuite.jushengwu.com/plugins/macse.jar.zip",
                "CodonW": "http://phylosuite.jushengwu.com/plugins/MacOSCodonW.zip",
                "ASTRAL": "http://phylosuite.jushengwu.com/plugins/ASTRAL_mac.zip",
                "ASTRAL-PRO": "http://phylosuite.jushengwu.com/plugins/ASTRAL_mac.zip",
                "FastTree": "http://phylosuite.jushengwu.com/plugins/FastTree_mac.zip",
                "plot engine": "http://phylosuite.jushengwu.com/plugins/plot_engine_Mac.zip"
            }
        }
    }
}

## 添加界面相关的参数,搜索替换，如搜索ASTRAL
## 新添加一个插件往往只需要在这里配置就行了，除了link，如果是要自动识别不同平台的link，就在Lg_settings里面设置即可
## 如果target有多个，就用列表
## 所有插件设计的话，最好都把插件的名字作为顶层文件夹，这样不容易乱，比如所有iqtree都放到名为iqtree的文件夹下面
## zipFileName_win 和 zipFileName_mac 必须保持一致
## link_linux和link_mac里面如果有If download failed, 将会显示下载按钮和下载源的combobox，如果没有，将会隐藏他们
### 或许改成通过label3来判断？根据它是configure还是download
dict_plugin_settings = {
    "ASTRAL": {
        ### macOSx86bin 下的所有文件都可以在mac里面直接用，但是需要是老的x86的mac，新的mac是arm的。
        ### 不管什么版本的mac，都可以cd进去make，这样就有可执行文件在bin文件夹里面生成
        "plugin_name": "ASTRAL", # 必须和键一样
        "version": "1.10.2.1",
        "description": "ASTRAL is a tool for estimating an unrooted species tree given a set of unrooted gene trees",
        "label1":"<html><head/><body><p>If you have <span style=\"color:red\">ASTRAL v1.8.1.0</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>",
        "label2":"ASTRAL:",
        "label3":"<html><head/><body><p>If you don\'t have ASTRAL, please <span style=\" font-weight:600; color:#ff0000;\">configure</span>.</p></body></html>",
        "placeholdertext_win": "C:\\ASTRAL\\exe\\astral.exe",
        "placeholdertext_mac": "../ASTRAL/bin/astral",
        "placeholdertext_linux": "../ASTRAL/bin/astral",
        "target_win": "astral.exe",
        "target_mac": "astral",
        "target_linux": "astral",
        # 如果没有自动下载的链接，就用这个。否则就在Lg_settings里面设置即可
        "link_mac": "<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">" \
                    "If download failed, click " \
                    "<a href=\"https://github.com/chaoszhang/ASTER/blob/master/tutorial/astral.md\">" \
                    "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</span></a>"
                    " to download manually and then specify the path as indicated above. " \
                    "If you are adding ASTRAL to environment variables, when you finish the installation, " \
                    "you need to close and reopen PhyloSuite to see if it installed successfully" \
                    " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the ASTRAL executable" \
                    " file (<span style=\" font-weight:600; color:#ff0000;\">astral</span>) manually (using options above).</p>" \
                    "</body></html>",
        "link_linux": "<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">" \
                    "If you don't have ASTRAL, you need to install it following " \
                    "<a href=\"https://github.com/chaoszhang/ASTER/blob/master/tutorial/astral.md\">" \
                    "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">this tutorial</span></a>. " \
                    "If you are adding ASTRAL to environment variables, when you finish the installation, " \
                    "you need to close and reopen PhyloSuite to see if it installed successfully" \
                    " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the ASTRAL executable" \
                    " file (<span style=\" font-weight:600; color:#ff0000;\">astral</span>) manually (using options above).</p>" \
                    "</body></html>",
        # 卸载相关
        "zipFileName_win": "ASTRAL.zip",
        "zipFileName_mac": "ASTRAL.zip",
        "zipFolder_win": "ASTRAL",
        "zipFolder_mac": "ASTRAL",
        ## 用于给glob匹配软件的名字
        "zipFolderFlag": "ASTRAL",
        # 判断路径相关
        "relative_path_win": "ASTRAL/exe/astral.exe",
        "relative_path_mac": "ASTRAL/bin/astral",
        "relative_path_linux": "ASTRAL/bin/astral",
    },
    "ASTRAL-PRO": {
        ### macOSx86bin 下的所有文件都可以在mac里面直接用，但是需要是老的x86的mac，新的mac是arm的。
        ### 不管什么版本的mac，都可以cd进去make，这样就有可执行文件在bin文件夹里面生成
        "plugin_name": "ASTRAL-PRO", # 必须和键一样
        "version": "1.10.2.1",
        "description": "ASTRAL-Pro stands for ASTRAL for PaRalogs and Orthologs",
        "label1":"<html><head/><body><p>If you have <span style=\"color:red\">ASTRAL-PRO v1.8.1.0</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>",
        "label2":"ASTRAL-PRO:",
        "label3":"<html><head/><body><p>If you don\'t have ASTRAL-PRO, please <span style=\" font-weight:600; color:#ff0000;\">configure</span>.</p></body></html>",
        "placeholdertext_win": "C:\\ASTRAL\\exe\\astral-pro.exe",
        "placeholdertext_mac": "../ASTRAL/bin/astral-pro",
        "placeholdertext_linux": "../ASTRAL/bin/astral-pro",
        "target_win": "astral-pro.exe",
        "target_mac": "astral-pro",
        "target_linux": "astral-pro",
        # 如果没有自动下载的链接，就用这个。否则就在Lg_settings里面设置即可
        "link_mac": "<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">" \
                    "If download failed, click " \
                    "<a href=\"https://github.com/chaoszhang/ASTER/blob/master/tutorial/astral.md\">" \
                    "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</span></a>"
                    " to download manually and then specify the path as indicated above. " \
                    "If you are adding ASTRAL to environment variables, when you finish the installation, " \
                    "you need to close and reopen PhyloSuite to see if it installed successfully" \
                    " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the ASTRAL executable" \
                    " file (<span style=\" font-weight:600; color:#ff0000;\">astral</span>) manually (using options above).</p>" \
                    "</body></html>",
        "link_linux": "<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">" \
                      "If you don't have ASTRAL-PRO, you need to install it following " \
                      "<a href=\"https://github.com/chaoszhang/ASTER/blob/master/tutorial/astral-pro.md\">" \
                      "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">this tutorial</span></a>. " \
                      "If you are adding ASTRAL-PRO to environment variables, when you finish the installation, " \
                      "you need to close and reopen PhyloSuite to see if it installed successfully" \
                      " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the ASTRAL-PRO executable" \
                      " file (<span style=\" font-weight:600; color:#ff0000;\">astral</span>) manually (using options above).</p>" \
                      "</body></html>",
        # 卸载相关
        "zipFileName_win": "ASTRAL.zip",
        "zipFileName_mac": "ASTRAL.zip",
        "zipFolder_win": "ASTRAL",
        "zipFolder_mac": "ASTRAL",
        ## 用于给glob匹配软件的名字
        "zipFolderFlag": "ASTRAL",
        # 判断路径相关
        "relative_path_win": "ASTRAL/exe/astral-pro.exe",
        "relative_path_mac": "ASTRAL/bin/astral-pro",
        "relative_path_linux": "ASTRAL/bin/astral-pro",
    },
    "FastTree": {
        ### macOSx86bin 下的所有文件都可以在mac里面直接用，但是需要是老的x86的mac，新的mac是arm的。
        ### 不管什么版本的mac，都可以cd进去make，这样就有可执行文件在bin文件夹里面生成
        "plugin_name": "FastTree", # 必须和键一样
        "version": "2.1.11",
        "description": "FastTree infers approximately-maximum-likelihood phylogenetic trees from alignments of nucleotide or protein sequences.",
        "label1":"<html><head/><body><p>If you have <span style=\"color:red\">FastTree v2.1.11</span>, please <span style=\" font-weight:600; color:#ff0000;\">specify</span>.</p></body></html>",
        "label2":"FastTree:",
        "label3":"<html><head/><body><p>If you don\'t have FastTree, please <span style=\" font-weight:600; color:#ff0000;\">configure</span>.</p></body></html>",
        "placeholdertext_win": "C:\\FastTree\\FastTree.exe",
        "placeholdertext_mac": "../FastTree/fasttree",
        "placeholdertext_linux": "../FastTree/fasttree",
        "target_win": "FastTree.exe",
        "target_mac": "fasttree",
        "target_linux": "fasttree",
        # 如果没有自动下载的链接，就用这个。否则就在Lg_settings里面设置即可
        "link_mac": "<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">If you already have " \
                    "<a href=\"https://docs.conda.io/en/latest/\">Conda</a> installed, " \
                    "you can install FastTree via the \"conda install -c bioconda fasttree\" or " \
                    "\"conda install -c bioconda/label/cf201901 fasttree\" command. </span><br>" \
                    "If you don't have Conda, you need to download FastTree " \
                    "<a href=\"http://www.microbesonline.org/fasttree/#Install\">" \
                    "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</span></a>. " \
                    "If you are adding FastTree to environment variables, when you finish the installation, " \
                    "you need to close and reopen PhyloSuite to see if it installed successfully" \
                    " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the FastTree executable" \
                    " file (<span style=\" font-weight:600; color:#ff0000;\">CodonW</span>) manually (using options above).</p>" \
                    "</body></html>",
        "link_linux": "<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">If you already have " \
                      "<a href=\"https://docs.conda.io/en/latest/\">Conda</a> installed, " \
                      "you can install FastTree via the \"conda install -c bioconda fasttree\" or " \
                      "\"conda install -c bioconda/label/cf201901 fasttree\" command. </span><br>" \
                      "If you don't have Conda, you need to download FastTree " \
                      "<a href=\"http://www.microbesonline.org/fasttree/#Install\">" \
                      "<span style=\" font-size:12pt; text-decoration: underline; color:#0000ff;\">here</span></a>. " \
                      "If you are adding FastTree to environment variables, when you finish the installation, " \
                      "you need to close and reopen PhyloSuite to see if it installed successfully" \
                      " (if you see \"Uninstall\" button, it means success). Otherwise you need to specify the FastTree executable" \
                      " file (<span style=\" font-weight:600; color:#ff0000;\">CodonW</span>) manually (using options above).</p>" \
                      "</body></html>",
        # 卸载相关
        "zipFileName_win": "FastTree.zip",
        "zipFileName_mac": "FastTree.zip",
        "zipFolder_win": "FastTree",
        "zipFolder_mac": "FastTree",
        ## 用于给glob匹配软件的名字
        "zipFolderFlag": "FastTree",
        # 判断路径相关
        "relative_path_win": "FastTree/FastTree.exe",
        "relative_path_mac": "FastTree/fasttree",
        "relative_path_linux": "FastTree/fasttree",
    },
    "mafft": {
        "target_win": "mafft.bat",
        "target_mac": "mafft.bat",
        "target_linux": "mafft",
    },
    "PF2": {
        "target_win": "partitionfinder-2.1.1",
        "target_mac": "partitionfinder-2.1.1",
        "target_linux": "partitionfinder-2.1.1",
    },
    "gblocks": {
        "target_win": "Gblocks.exe",
        "target_mac": "Gblocks",
        "target_linux": "Gblocks",
    },
    "trimAl": {
        "target_win": "trimal.exe",
        "target_mac": "trimal",
        "target_linux": "trimal",
    },
    "iq-tree": {
        "target_win": ["iqtree.exe", "iqtree2.exe"],
        "target_mac": ["iqtree", "iqtree2"],
        "target_linux": ["iqtree", "iqtree2"],
    },
    "MrBayes": {
        "target_win": ["mrbayes_x64.exe", "mb.3.2.7-win64.exe"] if platform.machine().endswith('64') \
                            else ["mrbayes_x86.exe", "mb.3.2.7-win32.exe"],
        "target_mac": "mb",
        "target_linux": "mb",
    },
    "macse": {
        "target_win": ["macse.jar", "macse_v2.03.jar", "macse_v2.07.jar", "macse_v2.05.jar"],
        "target_mac": ["macse.jar", "macse_v2.03.jar", "macse_v2.07.jar", "macse_v2.05.jar"],
        "target_linux": ["macse.jar", "macse_v2.03.jar", "macse_v2.07.jar", "macse_v2.05.jar"],
    },
    "CodonW": {
        "target_win": ["CodonW.exe"],
        "target_mac": ["codonw"],
        "target_linux": ["codonw"],
    },
}

