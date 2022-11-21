#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
description goes here
'''
import calendar
import csv
import datetime
import multiprocessing
import os
import signal

import Bio
from Bio.SeqFeature import FeatureLocation
from ete3.treeview.drawer import exit_gui

from ete3.treeview.qt4_gui import _GUI

from ete3.treeview.qt4_render import _TreeScene
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys

from ete3 import NCBITaxa, PhyloTree, Tree, TreeStyle
from src.LG_TreeSuite import TreeSuite

from src.Launcher import Launcher
from src.Lg_ASTRAL import ASTRAL
from src.Lg_ClipQuery import Lg_ClipQuery
from src.LG_colorsets import Colorset
from src.Lg_ConvertFmt import ConvertFMT
from src.Lg_FastTree import FastTree
from src.Lg_HmmCleaner import HmmCleaner
from src.Lg_IQTREE import IQTREE
from src.Lg_Manual_update import LG_Manual_update
from src.Lg_Mrbayes import MrBayes
from src.Lg_SerhNCBI import SerhNCBI
from src.Lg_addFiles import Lg_addFiles
from src.Lg_displaySettings import DisplaySettings
from src.Lg_drawGO import DrawGO
from src.Lg_extractSettings import ExtractSettings
from src.Lg_macse import MACSE
from src.Lg_seqViewer import Seq_viewer
from src.Lg_tiger import Tiger
from src.Lg_trimAl import TrimAl
from src.Lg_workflow import WorkFlow
# from todo.test_plot import Plot
from uifiles.Ui_MainWindow import Ui_MainWindow
from uifiles.Ui_about import Ui_about
from src.Lg_settings import Setting
from src.CustomWidget import MyTableModel, MyOtherFileTableModel, NMLPopupGui, CustomTreeIndexWidget, UpdatePopupGui, \
    ProgressDialog, FileIconProvider
from src.handleGB import DetermineCopyGene, DetermineCopyGeneParallel, GbManager, GBnormalize, ArrayManager
from src.Lg_extracter import ExtractGB
from src.Lg_mafft import Mafft
from src.Lg_Concatenate import Matrix
import platform
if platform.system().lower() == "windows":
    ##windows下才导入这个
    from src.Lg_parseANNT import ParseANNT
from src.Lg_compareTable import CompareTable
from src.Lg_PartitionFinder import PartitionFinder
from src.Lg_Gblocks import Gblocks
from src.Lg_ModelFinder import ModelFinder
import shutil
import glob
from copy import deepcopy
from Bio import Entrez, SeqIO, SeqFeature
import traceback
from src.factory import Factory, WorkThread, Convertfmt, Parsefmt, WorkRunThread
import re
from src.update import UpdateAPP
import subprocess
from io import StringIO
from Bio.Alphabet import generic_dna, generic_protein, generic_rna
import time
from src.Lg_RSCUfig import DrawRSCUfig

class MyMainWindow(QMainWindow, Ui_MainWindow, object):
    progressSig = pyqtSignal(int)  # 控制进度条
    progressBarSig = pyqtSignal(int)  # 控制进度条
    clearFolderSig = pyqtSignal(str)
    restarted = pyqtSignal(QWidget, list)
    focusSig = pyqtSignal(str)
    _Self = None  # 很重要,保留窗口引用
    ###tree button的信号
    folderDeleteSig = pyqtSignal(QModelIndex)
    folderOpenSig = pyqtSignal(QModelIndex)
    creatFolderSig = pyqtSignal(QModelIndex)
    restoreFolderSig = pyqtSignal(QModelIndex)
    openDisplaySetSig = pyqtSignal(QModelIndex)
    ###更新
    updateSig = pyqtSignal(str, str, str)
    exception_signal = pyqtSignal(str)
    ###gb文件检查
    display_checkSig = pyqtSignal(list)
    # modify_tableSig = pyqtSignal(QModelIndex, str)
    ##修改表格完成的信号
    modify_table_finished = pyqtSignal()
    ## 修改分类表完成的信号
    modify_lineage_finished = pyqtSignal()
    warning_signal = pyqtSignal(str)

    def __init__(self, workplace=None, parent=None):
        super(MyMainWindow, self).__init__(parent)
        MyMainWindow._Self = self
        self.treeRootPath = workplace[0]
        ##工作区的路径存到系统里面
        workPlaceSettings = self.treeRootPath + os.sep + ".settings"
        QApplication.setApplicationName("PhyloSuite_settings")
        QApplication.setOrganizationName("PhyloSuite")
        QSettings.setDefaultFormat(QSettings.IniFormat)
        path_settings = QSettings()
        path_settings.setValue("current workplace setting path", workPlaceSettings)
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        # 保存设置
        self.mainwindow_settings = QSettings(
            self.thisPath +
            '/settings/mainwindow_settings.ini',
            QSettings.IniFormat, parent=self)
        # File only, no fallback to registry or or.
        self.mainwindow_settings.setFallbacksEnabled(False)
        self.setupUi(self)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            qss_file = f.read()
        # 统一界面字体
        QSettings.setDefaultFormat(QSettings.IniFormat)
        font_settings = QSettings()
        font_changed = font_settings.value("font changed", False)
        if platform.system().lower() == "darwin":
            self.label_6.setText(
                self.label_6.text().replace("font-size:14pt;", "font-size:15pt;").replace("font-size:20pt;",
                                                                                          "font-size:25pt;"))
            if not font_changed:
                # 如果用户没有改过字体
                qss_file = re.sub(r"^\*{font-family: (.+?); font-size: (\d+)pt;}",
                                  "*{font-family: Arial; font-size: 12pt;}", qss_file)
                with open(self.thisPath + os.sep + 'style.qss', "w", encoding="utf-8", errors='ignore') as f:
                    f.write(qss_file)
        elif platform.system().lower() == "windows":
            self.label_6.setText(
                self.label_6.text().replace("font-size:14pt;", "font-size:13pt;"))
        elif platform.system().lower() == "linux":
            self.label_6.setText(
                self.label_6.text().replace("font-size:14pt;", "font-size:12pt;").replace("font-size:20pt;",
                                                                                          "font-size:18pt;"))
            if not font_changed:
                # 如果用户没有改过字体
                qss_file = re.sub(r"^\*{font-family: (.+?); font-size: (\d+)pt;}",
                                  "*{font-family: Arial; font-size: 10pt;}", qss_file)
                with open(self.thisPath + os.sep + 'style.qss', "w", encoding="utf-8", errors='ignore') as f:
                    f.write(qss_file)
        self.setStyleSheet(qss_file)
        # 信号和槽
        self.progressSig.connect(self.Progress)
        self.progressBarSig.connect(lambda value: self.disp_check_progress.setValue(value))
        self.clearFolderSig.connect(self.clearFolder)
        self.restarted.connect(MyMainWindow.onRestart)
        self.focusSig.connect(self.setTreeViewFocus)
        self.folderDeleteSig.connect(self.rmdir)
        self.folderOpenSig.connect(self.openinwindow)
        self.creatFolderSig.connect(self.mkdir)
        self.restoreFolderSig.connect(self.recycled_restore)
        self.exception_signal.connect(lambda x: self.factory.popupException(self, x))
        self.warning_signal.connect(self.popupWarning)
        self.updateSig.connect(self.UpdatesSlot)
        self.openDisplaySetSig.connect(self.on_actionDisplay_triggered)
        self.display_checkSig.connect(lambda array: self.displayTableModel.updateModel(array))
        # 修改主界面version展示
        current_version = self.factory.get_PS_version()
        if current_version:
            self.label_6.setText(re.sub(r"PhyloSuite v[^<]+",
                                       f"PhyloSuite v{current_version}",
                                       self.label_6.text()))
        self.label_6.linkActivated.connect(self.saveCitation)
        # self.modify_tableSig.connect(self.modifyTable)
        # 删除更新留下的旧文件，延迟2秒执行
        QTimer.singleShot(2000, lambda : WorkThread(self.removeOldApp, parent=self).start())
        ##检查版本
        not_check_update = self.mainwindow_settings.value("not auto check update", "0")
        if not self.factory.str2bool(not_check_update):
            ##允许检查才检查
            self.factory.checkUpdates(self.updateSig, self.exception_signal, mode="auto check", parent=self)
            # httpread = HttpRead(parent=self)
            # WorkThread(lambda: self.factory.checkUpdates(self.updateSig, self.exception_signal,
            #                                              mode="auto check", httpread=httpread), parent=self).start()
        # workplace
        self.workplace_widget._creatMenu(self)
        # 改变工作路径,工作路径的列表
        for num, i in enumerate(workplace):
            if num == 0:
                self.workplace_widget.DropDownMenu.addMenuItem(":/picture/resourses/caribbean-blue-clipart-12.png",
                                                               i)
                continue
            self.workplace_widget.DropDownMenu.addMenuItem(":/picture/resourses/folder-icon.png", i)
        #计算最长工作路径的有多长
        font_ = self.font()
        length = QFontMetrics(QFont(font_.family(), font_.pointSize())).width(max(workplace, key=len))
        self.workplace_widget.DropDownMenu.setMinimumWidth(length+40) #让下拉菜单显示完全
        self.workplace_widget.DropDownMenu.addMenuItem(":/picture/resourses/other.png", "Others...")
        self.workplace_widget.DropDownMenu.tableWidget.itemClicked.connect(self.switchWorkPlace)
        self.workplace_widget.DropDownMenu.tableWidget.setWordWrap(True)
        # self.workplace_widget.DropDownMenu.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        # 设置比例
        self.splitter.setStretchFactor(1, 9)
        # 拷贝
        self.clip = QApplication.clipboard()
        # treeView
        self.treeRootPath = workplace[0]
        self.tree_model = QFileSystemModel(self)
        fileIconProvider = FileIconProvider()
        self.tree_model.setIconProvider(fileIconProvider)
        self.gb_files_path = self.treeRootPath + os.sep + "GenBank_File/files"
        self.factory.creat_dirs(self.gb_files_path)
        self.factory.creat_dirs(self.gb_files_path + os.sep + ".data")
        self.factory.creat_dirs(
            self.treeRootPath +
            os.sep +
            "GenBank_File/flowchart/.data")
        self.GenBank_File_recycle = self.treeRootPath + \
            os.sep + "GenBank_File/recycled"
        self.factory.creat_dirs(self.GenBank_File_recycle)
        self.other_files_path = self.treeRootPath + os.sep + "Other_File/files"
        self.factory.creat_dirs(self.other_files_path)
        self.factory.creat_dirs(
            self.treeRootPath +
            os.sep +
            "Other_File/flowchart")
        self.Other_File_recycle = self.treeRootPath + \
            os.sep + "Other_File/recycled"
        self.factory.creat_dirs(self.Other_File_recycle)
        self.tree_model.setRootPath(self.treeRootPath)
        # 只显示文件夹
        self.tree_model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs)
        # filter = [".data"]
        # self.tree_model.setNameFilters(filter)
        # self.tree_model.setNameFilterDisables(True)
        # 有这个命令，双击可以改文件名
        self.treeView.setModel(self.tree_model)
        self.treeView.setRootIndex(
            self.tree_model.index(self.treeRootPath))
        self.tree_model.directoryLoaded.connect(self.expand)
        ## init check
        iniCheckWorker = WorkThread(lambda: self.factory.init_check(self),
                                    parent=self)
        iniCheckWorker.start()
        # 展开所有文件
        # self.treeView.expandAll()
        # 隐藏type，size等信息
        self.treeView.hideColumn(1)
        self.treeView.hideColumn(2)
        self.treeView.hideColumn(3)
        # 右键菜单
        self.tree_popMenu = QMenu(self)
        self.newFolder = QAction(QIcon(":/picture/resourses/add-icon.png"), 'New Work Folder', self,
                                 statusTip="create new folder",
                                 triggered=self.mkdir)
        self.rmvFolder = QAction(QIcon(":/picture/resourses/if_Delete_1493279.png"), "Remove Folder", self,
                                 shortcut=QKeySequence.Delete,
                                 statusTip="remove folder",
                                 triggered=self.rmdir)
        self.rmvCFolder = QAction(QIcon(":/picture/resourses/if_Delete_1493279.png"), "Remove Folder", self,
                                 shortcut=QKeySequence.Delete,
                                 statusTip="remove folder",
                                 triggered=self.recycled_remove)
        self.restore = QAction(QIcon(":/picture/resourses/Custom-Icon-Design-Flatastic-9-Undo.ico"), "Restore Folder", self,
                                  shortcut=QKeySequence.Delete,
                                  statusTip="restore folder",
                                  triggered=lambda : self.recycled_restore(self.treeView.currentIndex()))
        self.displaySet = QAction(QIcon(":/picture/resourses/cog.png"), "Information Display Setting",
                               self,
                               statusTip="GenBank File Information Display Setting",
                               triggered=self.on_actionDisplay_triggered)
        self.rnmFolder = QAction("Rename Work Folder", self,
                                 statusTip="rename folder",
                                 triggered=self.rnmdir)
        self.openInWindow = QAction(QIcon(":/picture/resourses/if_file-explorer_60174.png"),
            "Open In Windows Explorer",
            self,
            statusTip="open folder in windows explorer",
            triggered=self.openinwindow)
        self.tree_popMenu.addAction(self.newFolder)
        self.tree_popMenu.addAction(self.rmvFolder)
        self.tree_popMenu.addAction(self.rmvCFolder)
        self.tree_popMenu.addAction(self.restore)
        # self.tree_popMenu.addAction(self.rnmFolder)
        self.tree_popMenu.addSeparator()
        self.tree_popMenu.addAction(self.openInWindow)
        self.tree_popMenu.addAction(self.displaySet)

        def tree_popmenu(qpoint):
            index = self.treeView.indexAt(qpoint)
            if not index.isValid():
                return
            filePath = self.tree_model.filePath(index)
            fileName = self.tree_model.fileName(index)
            if self.isRootFolder(filePath):
                self.rmvFolder.setVisible(False)
                self.rmvCFolder.setVisible(False)
                self.restore.setVisible(False)
                # self.rnmFolder.setVisible(False)
                self.newFolder.setVisible(True)
            elif self.isRecycledFolder(filePath):
                self.rmvCFolder.setVisible(True)
                self.restore.setVisible(True)
                self.rmvFolder.setVisible(False)
                self.newFolder.setVisible(False)
            elif self.isWorkFolder(filePath) or self.isResultsFolder(filePath):
                #GB display的设置
                if os.path.basename(filePath) != "recycled" and self.isWorkFolder(filePath, mode="gb"):
                    self.displaySet.setVisible(True)
                else:
                    self.displaySet.setVisible(False)
                if fileName not in ["files", "flowchart", "recycled", ".data"]:
                    self.rmvFolder.setVisible(True)
                else:
                    self.rmvFolder.setVisible(False)
                # self.rnmFolder.setVisible(True)
                self.newFolder.setVisible(False)
                self.rmvCFolder.setVisible(False)
                self.restore.setVisible(False)
            self.tree_popMenu.exec_(QCursor.pos())
            # index = self.treeView.currentIndex()
            # if index.isValid() and self.tree_model.fileInfo(index).isDir():
            #     self.tree_popMenu.exec_(QCursor.pos())

        self.treeView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(tree_popmenu)
        self.treeView.installEventFilter(self)
        self.treeView.selectionModel().selectionChanged.connect(self.display)
        self.treeView.doubleClicked.connect(self.openinwindow)
        self.stackedWidget.installEventFilter(self)
        # tableview
        self.tableView.installEventFilter(self)
        table_popMenu = QMenu(self)
        OpenID = QAction(QIcon(":/seq_Viewer/resourses/field-Display.png"), "Open", self,
                            statusTip="Open sequences",
                            triggered=self.openID)
        addFile = QAction(QIcon(":/picture/resourses/iconfinder_file_add_48761.png"), "Add file", self,
                          statusTip="Add file",
                          triggered=self.on_Add_Files_triggered)
        mergeFile = QAction(QIcon(":/picture/resourses/round arrangement-fill.svg"), "Merge GB files", self,
                          statusTip="Merge genbank files",
                          triggered=self.mergeID)
        SelectAll = QAction(QIcon(":/picture/resourses/all icon.png"), "Select All", self,
                              statusTip="Select All",
                              shortcut=QKeySequence("Ctrl+A"),
                              triggered=self.tableView.selectAll)
        # EditCell = QAction(QIcon(":/picture/resourses/edit2.png"), "Edit cell", self,
        #                  statusTip="Edit selected table cell",
        #                  triggered= self.editCell) #lambda : self.tableView.edit(self.tableView.selectedIndexes()[0]))
        CopyID = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/copy.png"), "Copy", self,
                              statusTip="Copy IDs",
                              shortcut="Ctrl+C",
                              triggered=self.copyID)
        CutID = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/cut.png"), "Cut", self,
                              statusTip="Cut IDs",
                              shortcut="Ctrl+X",
                              triggered=self.cutID)
        PasteID = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/paste_512px_1175635_easyicon.net.png"), "Paste", self,
                              statusTip="Paste IDs",
                              shortcut="Ctrl+V",
                              triggered=self.pasteID)
        rmtablerow = QAction(QIcon(":/picture/resourses/if_Delete_1493279.png"), "Delete", self,
                                  shortcut=QKeySequence.Delete,
                                  statusTip="Remove Rows",
                                  triggered=self.rmTableRow)
        refresh = QAction(QIcon(":/picture/resourses/refresh-icon.png"), "Refresh table", self,
                             statusTip="Refresh table",
                             triggered=self.refreshTable)
        find_tax_ncbi = QAction(QIcon(":/picture/resourses/Spotlight_OS_X.svg.png"), "Get taxonomy (NCBI, fast)", self,
                           statusTip="Get taxonomy from NCBI 'taxonomy' database",
                           triggered=lambda : self.updateTaxonomy(database="NCBI"))
        update_tax_ncbi = QAction(QIcon(":/picture/resourses/refresh-icon.png"), "Update NCBI taxonomy database", self,
                            statusTip="Update NCBI 'taxonomy' database",
                            triggered=lambda : self.updateTaxonomyDB())
        extract_tax_ncbi = QAction(QIcon(":/picture/resourses/Spotlight_OS_X.svg.png"), "Select IDs by taxonomy (NCBI)", self,
                                statusTip="Fetch sequence in current work dir by taxonomy name",
                                triggered=self.fetchByTaxonomy)
        find_tax_worms = QAction(QIcon(":/picture/resourses/Spotlight_OS_X.svg.png"), "Get taxonomy (WoRMS, slow)", self,
                           statusTip="Get taxonomy from 'WoRMS' database",
                           triggered=lambda : self.updateTaxonomy(database="WoRMS"))
        reorderGBbyName = QAction(QIcon(":/picture/resourses/sequence.png"), "Reorder gb file(s) by gene", self,
                                 statusTip="Reorder GenBank file according to the specifed annotation feature (gene name) or position",
                                 triggered=lambda : self.reorderGB(byName=True))
        reorderGBbyPos = QAction(QIcon(":/picture/resourses/sequence.png"), "Reorder gb file(s) by position",
                                  self,
                                  statusTip="Reorder GenBank file according to the specifed annotation feature (gene name) or position",
                                  triggered=lambda : self.reorderGB(byName=False))
        standard = QAction(QIcon(":/picture/resourses/normalization.png"), "Standardization", self,
                            statusTip="Standardize GenBank file",
                            triggered=self.on_Normalization_triggered)
        extractGB = QAction(QIcon(":/picture/resourses/extract1.png"), "Extract", self,
                           statusTip="Extract GenBank file",
                           triggered=self.on_Extract_triggered)
        exportSelectID = QAction(QIcon(":/picture/resourses/if_10_Menu_List_Text_Line_Item_Bullet_Paragraph_2142684.png"), "Export GenBank", self,
                                      statusTip="Export select IDs as GenBank file",
                                      triggered=self.exportID)
        exportID2fas = QAction(QIcon(":/picture/resourses/if_10_Menu_List_Text_Line_Item_Bullet_Paragraph_2142684.png"), "Export Fasta", self,
                                 statusTip="Export select IDs as Fasta file",
                                 triggered=self.exportFASTA)
        exportTable = QAction(QIcon(":/picture/resourses/table.png"), "Export table", self,
                                   statusTip="Export select IDs as table",
                                   triggered=self.saveTable)
        importTable = QAction(QIcon(":/picture/resourses/table.png"), "Import corrected table", self,
                              statusTip="Import table for modification",
                              triggered=self.table4Modification)
        table_popMenu.addAction(OpenID)
        table_popMenu.addAction(refresh)
        table_popMenu.addAction(addFile)
        table_popMenu.addAction(mergeFile)
        table_popMenu.addAction(SelectAll)
        table_popMenu.addAction(CopyID)
        table_popMenu.addAction(CutID)
        table_popMenu.addAction(PasteID)
        table_popMenu.addAction(rmtablerow)
        table_popMenu.addSeparator()
        table_popMenu.addAction(find_tax_ncbi)
        table_popMenu.addAction(update_tax_ncbi)
        table_popMenu.addAction(extract_tax_ncbi)
        table_popMenu.addAction(find_tax_worms)
        table_popMenu.addAction(reorderGBbyName)
        table_popMenu.addAction(reorderGBbyPos)
        table_popMenu.addAction(standard)
        table_popMenu.addAction(extractGB)
        table_popMenu.addSeparator()
        table_popMenu.addAction(exportSelectID)
        table_popMenu.addAction(exportID2fas)
        table_popMenu.addAction(exportTable)
        table_popMenu.addSeparator()
        table_popMenu.addAction(importTable)
        # tree_popMenu.addAction(rnmFolder)
        # tree_popMenu.addAction(cutcell)

        def table_popmenu(qpoint):
            if self.tableView.indexAt(qpoint).isValid():
                table_popMenu.exec_(QCursor.pos())
            # index = self.treeView.currentIndex()
            # if index.isValid() and self.tree_model.fileInfo(index).isDir():
            #     table_popMenu.exec_(QCursor.pos())
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(table_popmenu)

        # treeView_3右键菜单
        tree3_popMenu = QMenu(self)
        restoreFile = QAction("Restore", self,
                              statusTip="restore",
                              triggered=self.recycled_restore)
        removeFile = QAction("Remove", self,
                             shortcut=QKeySequence.Delete,
                             statusTip="remove file",
                             triggered=self.recycled_remove)

        def popup(qpoint):
            if self.treeView_3.indexAt(qpoint).isValid():
                tree3_popMenu.exec_(QCursor.pos())
        tree3_popMenu.addAction(restoreFile)
        tree3_popMenu.addAction(removeFile)
        self.treeView_3.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView_3.customContextMenuRequested.connect(popup)
        # treeView_4右键菜单
        tree4_popMenu = QMenu(self)
        openFile = QAction(QIcon(":/seq_Viewer/resourses/field-Display.png"), "Open", self,
                           statusTip="open file",
                           triggered=lambda : self.openResultsInWindow(self.treeView_4.model().filePath(self.treeView_4.currentIndex())))
        openInExplore = QAction(QIcon(":/picture/resourses/folder.png"), "Open in file explorer", self,
                           statusTip="open in file explorer",
                           triggered=lambda : self.factory.openPath(os.path.dirname(self.treeView_4.model().filePath(self.treeView_4.currentIndex())), self))
        remove = QAction(QIcon(":/picture/resourses/if_Delete_1493279.png"), "Remove", self,
                           statusTip="Remove",
                           triggered=self.remove_treeview4)
        mafft = QAction(QIcon(":/picture/resourses/mafft1.png"), "Import to MAFFT", self,
                        statusTip="Align with MAFFT",
                        triggered=self.on_Mafft_triggered)
        MACSE = QAction(QIcon(":/picture/resourses/M.png"), "Import to MACSE (for CDS)", self,
                        statusTip="Align with MACSE",
                        triggered=self.on_MACSE_triggered)
        trimAl = QAction(QIcon(":/picture/resourses/icon--trim-confirm-0.png"), "Import to trimAl", self,
                         statusTip="trimAl",
                         triggered=self.on_actiontrimAl_triggered)
        HmmCleaner = QAction(QIcon(":/picture/resourses/clean.png"), "Import to HmmCleaner", self,
                             statusTip="HmmCleaner",
                             triggered=self.on_actionHmmCleaner_triggered)
        gblocks = QAction(QIcon(":/picture/resourses/if_simpline_22_2305632.png"), "Import to Gblocks", self,
                          statusTip="Gblocks",
                          triggered=self.on_actionGblocks_triggered)
        catSeq = QAction(QIcon(":/picture/resourses/cat1.png"), "Import to Concatenate Sequence", self,
                         statusTip="Concatenate Sequence",
                         triggered=self.on_Concatenate_triggered)
        cvtFMT = QAction(QIcon(":/picture/resourses/transform3.png"), "Import to Convert Sequence Format", self,
                         statusTip="Convert Sequence Format",
                         triggered=self.on_ConvertFMT_triggered)
        modelfinder = QAction(QIcon(":/picture/resourses/if_tinder_334781.png"), "Import to ModelFinder", self,
                              statusTip="Select model with ModelFinder",
                              triggered=self.on_actionModelFinder_triggered)
        iqtree = QAction(QIcon(":/picture/resourses/data-taxonomy-icon.png"), "Import to IQ-TREE", self,
                         statusTip="Reconstruct tree with IQ-TREE",
                         triggered=self.on_actionIQTREE_triggered)
        mrbayes = QAction(QIcon(":/picture/resourses/2000px-Paris_RER_B_icon.svg.png"), "Import to MrBayes", self,
                          statusTip="Reconstruct tree with MrBayes",
                          triggered=self.on_actionMrBayes_triggered)
        partfind = QAction(QIcon(":/picture/resourses/pie-chart.png"), "Import to PartitionFinder2", self,
                          statusTip="Select partition model with PartitionFinder2",
                          triggered=self.on_actionPartitionFinder_triggered)
        rscu = QAction(QIcon(":/picture/resourses/if_7_2172765.png"), "Import to Draw RSCU figure", self,
                           statusTip="Draw RSCU figure",
                           triggered=self.on_actionRSCUfig_triggered)
        compareTable = QAction(QIcon(":/picture/resourses/ezsrokaxkrotbkoewfgb.png"), "Import to Compare Table", self,
                       statusTip="Compare table",
                       triggered=self.on_Compare_table_triggered)
        drawGO = QAction(QIcon(":/picture/resourses/round arrangement-fill.svg"), "Import to Draw gene order", self,
                               statusTip="Draw gene order",
                               triggered=self.on_actionDrawGO_triggered)
        rsl_dups = QAction(QIcon(":/picture/resourses/drag.png"), "Resolve gene duplicates", self,
            statusTip="Resolve gene duplicates",
            triggered=self.on_rsl_duplicates_triggered)
        tree_suite = QAction(QIcon(":/Menu/resourses/Menu/echarts-tree.png"), "Import to Treesuite", self,
                           statusTip="TreeSuite",
                           triggered=self.on_TreeSuite_triggered)
        ASTRAL = QAction(QIcon(":/picture/resourses/menu_icons/A2.png"), "Import to ASTRAL", self,
                         statusTip="Reconstruct species tree with ASTRAL",
                         triggered=self.on_actionASTRAL_triggered)
        FastTree = QAction(QIcon(":/picture/resourses/menu_icons/fast.svg"), "Import to FastTree", self,
                         statusTip="Reconstruct tree with FastTree",
                         triggered=self.on_actionFastTree_triggered)
        def popup(qpoint):
            index = self.treeView_4.indexAt(qpoint)
            if not index.isValid():
                return
            dict_ = {"extract_results": [mafft, MACSE, rscu, compareTable, drawGO, rsl_dups],
                     "mafft_results": [MACSE, gblocks, trimAl, HmmCleaner, cvtFMT, catSeq, FastTree],
                     "MACSE_results": [gblocks, trimAl, HmmCleaner, cvtFMT, catSeq, FastTree],
                     "concatenate_results": [gblocks, trimAl, HmmCleaner, iqtree, modelfinder, partfind, FastTree],
                     "PartFind_results": [iqtree, mrbayes],
                     "ModelFinder_results": [iqtree, mrbayes, FastTree],
                     "Gblocks_results": [cvtFMT, catSeq, FastTree],
                     "trimAl_results": [cvtFMT, catSeq, FastTree],
                     "HmmCleaner_results": [cvtFMT, catSeq, FastTree],
                     "IQtree_results": [tree_suite, ASTRAL],
                     "MrBayes_results": [tree_suite],
                     "FastTree_results": [ASTRAL]
                     }
            list_actions = [mafft, gblocks, trimAl, HmmCleaner, cvtFMT, catSeq, iqtree, FastTree,
                            modelfinder, partfind, MACSE, mrbayes, rscu, compareTable, drawGO,
                            rsl_dups, tree_suite, ASTRAL]
            filePath = self.treeView_4.model().filePath(index)
            topResultsName = os.path.basename(os.path.dirname(filePath))
            for action in list_actions:
                if (topResultsName in dict_) and (action in dict_[topResultsName]):
                    action.setVisible(True)
                else:
                    action.setVisible(False)
            tree4_popMenu.exec_(QCursor.pos())
        tree4_popMenu.addAction(openFile)
        tree4_popMenu.addAction(openInExplore)
        tree4_popMenu.addAction(remove)
        tree4_popMenu.addSeparator()
        tree4_popMenu.addAction(mafft)
        tree4_popMenu.addAction(MACSE)
        tree4_popMenu.addAction(trimAl)
        if platform.system().lower() in ["darwin", "linux"]:
            tree4_popMenu.addAction(HmmCleaner)
        tree4_popMenu.addAction(gblocks)
        tree4_popMenu.addAction(catSeq)
        tree4_popMenu.addAction(cvtFMT)
        tree4_popMenu.addSeparator()
        tree4_popMenu.addAction(modelfinder)
        tree4_popMenu.addAction(partfind)
        tree4_popMenu.addAction(iqtree)
        tree4_popMenu.addAction(FastTree)
        tree4_popMenu.addAction(mrbayes)
        tree4_popMenu.addSeparator()
        tree4_popMenu.addAction(rscu)
        tree4_popMenu.addAction(compareTable)
        tree4_popMenu.addAction(drawGO)
        tree4_popMenu.addAction(rsl_dups)
        tree4_popMenu.addAction(tree_suite)
        tree4_popMenu.addAction(ASTRAL)
        self.treeView_4.setContextMenuPolicy(Qt.CustomContextMenu)
        self.treeView_4.customContextMenuRequested.connect(popup)
        self.treeView_4.doubleClicked.connect(lambda index: self.openResultsInWindow(self.treeView_4.model().filePath(index)))
        # 恢复用户的设置
        self.guiRestore()
        # ini_index = self.tree_model.index(self.treeRootPath +
        #                                   os.sep +
        #                                   "GenBank_File")
        # self.treeView.setCurrentIndex(ini_index)
        # self.display(ini_index)
        self.parsefmt = Parsefmt("")
        self.tableView_2.installEventFilter(self)
        self.tableView_2.doubleClicked.connect(self.open_tableItem)
        ###menu###
        self.verticalLayout_2.setAlignment(self.flowchart, Qt.AlignCenter)
        self.verticalLayout_3.setAlignment(self.file, Qt.AlignCenter)
        self.verticalLayout_4.setAlignment(self.alignment, Qt.AlignCenter)
        self.verticalLayout_5.setAlignment(self.phylogeny, Qt.AlignCenter)
        self.verticalLayout_6.setAlignment(self.mitogenome, Qt.AlignCenter)
        self.verticalLayout_7.setAlignment(self.Settings, Qt.AlignCenter)
        self.verticalLayout_8.setAlignment(self.workplace, Qt.AlignCenter)
        #给按钮加图片
        #创建菜单
        self.flowchart_widget.clicked.connect(self.on_actionWorkflow_triggered)
        self.flowchart.clicked.connect(self.on_actionWorkflow_triggered)
        self.file_widget._creatMenu(self)
        self.file_widget.DropDownMenu.addMenuItem(":/picture/resourses/Open_folder_add_512px_1186192_easyicon.net.png",
                                                  "Import file(s) or ID(s)")
        self.file_widget.DropDownMenu.addMenuItem(":/picture/resourses/normalization.png",
                                                  "Standardize GenBank file")
        self.file_widget.DropDownMenu.addMenuItem(":/picture/resourses/extract1.png",
                                                  "Extract GenBank file")
        self.file_widget.DropDownMenu.addMenuItem(":/picture/resourses/NCBI-logo-2.png",
                                                  "Search in NCBI")
        # self.file_widget.DropDownMenu.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.file_widget.DropDownMenu.tableWidget.itemClicked.connect(self.popFunction)
        self.alignment_widget._creatMenu(self)
        self.alignment_widget.DropDownMenu.addMenuItem(":/picture/resourses/mafft1.png",
                                                  "MAFFT")
        self.alignment_widget.DropDownMenu.addMenuItem(":/picture/resourses/M.png",
                                                       "MACSE (for CDS)")
        self.alignment_widget.DropDownMenu.addMenuItem(":/picture/resourses/icon--trim-confirm-0.png",
                                                       "trimAl")
        if platform.system().lower() != "windows":
            self.alignment_widget.DropDownMenu.addMenuItem(":/picture/resourses/clean.png",
                                                           "HmmCleaner")
        self.alignment_widget.DropDownMenu.addMenuItem(":/picture/resourses/if_simpline_22_2305632.png",
                                                       "Gblocks")
        self.alignment_widget.DropDownMenu.addMenuItem(":/picture/resourses/cat1.png",
                                                       "Concatenate Sequence")
        self.alignment_widget.DropDownMenu.addMenuItem(":/picture/resourses/transform3.png",
                                                       "Convert Sequence Format")
        self.alignment_widget.DropDownMenu.addMenuItem(":/seq_Viewer/resourses/field-Display.png",
                                                       "Sequence Viewer")
        self.alignment_widget.DropDownMenu.tableWidget.itemClicked.connect(self.popFunction)
        self.phylogeny_widget._creatMenu(self)
        self.phylogeny_widget.DropDownMenu.addMenuItem(":/picture/resourses/pie-chart.png",
                                                       "PartitionFinder2")
        self.phylogeny_widget.DropDownMenu.addMenuItem(":/picture/resourses/if_tinder_334781.png",
                                                       "ModelFinder")
        self.phylogeny_widget.DropDownMenu.addMenuItem(":/picture/resourses/data-taxonomy-icon.png",
                                                       "IQ-TREE")
        self.phylogeny_widget.DropDownMenu.addMenuItem(":/picture/resourses/menu_icons/fast.svg",
                                                       "FastTree")
        self.phylogeny_widget.DropDownMenu.addMenuItem(":/picture/resourses/2000px-Paris_RER_B_icon.svg.png",
                                                       "MrBayes")
        self.phylogeny_widget.DropDownMenu.addMenuItem(":/picture/resourses/menu_icons/A2.png",
                                                       "ASTRAL")
        self.phylogeny_widget.DropDownMenu.addMenuItem(":/picture/resourses/sharpicons_Tiger.svg",
                                                       "Tiger")
        self.phylogeny_widget.DropDownMenu.addMenuItem(":/Menu/resourses/Menu/tree_structure.png",
                                                       "Tree annotation")
        self.phylogeny_widget.DropDownMenu.addMenuItem(":/Menu/resourses/Menu/echarts-tree.png",
                                                       "TreeSuite")
        self.phylogeny_widget.DropDownMenu.tableWidget.itemClicked.connect(self.popFunction)
        self.mitogenome_widget._creatMenu(self)
        if platform.system().lower() == "windows":
            ##windows下才加上这个
            self.mitogenome_widget.DropDownMenu.addMenuItem(":/picture/resourses/WORD.png",
                                                           "Parse Annotation")
        self.mitogenome_widget.DropDownMenu.addMenuItem(":/picture/resourses/ezsrokaxkrotbkoewfgb.png",
                                                        "Compare Table")
        self.mitogenome_widget.DropDownMenu.addMenuItem(":/picture/resourses/if_7_2172765.png",
                                                        "Draw RSCU figure")
        # self.mitogenome_widget.DropDownMenu.addMenuItem(":/picture/resourses/ic-scatter-plot.svg",
        #                                                 "Plot")
        self.mitogenome_widget.DropDownMenu.addMenuItem(":/picture/resourses/round arrangement-fill.svg",
                                                        "Draw gene order")
        self.mitogenome_widget.DropDownMenu.tableWidget.itemClicked.connect(self.popFunction)
        self.settings_widget._creatMenu(self)
        self.settings_widget.DropDownMenu.addMenuItem(":/picture/resourses/Eye_Care_Services-512.png",
                                                       "GenBank File Information Display")
        self.settings_widget.DropDownMenu.addMenuItem(":/picture/resourses/outflow.png",
                                                      "GenBank File Extracting")
        self.settings_widget.DropDownMenu.addMenuItem(":/picture/resourses/colors.svg",
                                                      "Color sets")
        self.settings_widget.DropDownMenu.addMenuItem(":/picture/resourses/settings.png",
                                                      "Settings")
        self.settings_widget.DropDownMenu.addMenuItem(":/picture/resourses/update.png",
                                                      "Check for Updates")
        self.settings_widget.DropDownMenu.addMenuItem(":/picture/resourses/update.png",
                                                      "Update manually")
        self.settings_widget.DropDownMenu.tableWidget.itemClicked.connect(self.popFunction)
        self.about_widget._creatMenu(self)
        self.about_widget.DropDownMenu.addMenuItem(":/picture/resourses/about-us.png",
                                                      "About")
        self.about_widget.DropDownMenu.addMenuItem(":/picture/resourses/file.png",
                                                   "Documentation")
        self.about_widget.DropDownMenu.addMenuItem(":/picture/resourses/help.gif",
                                                   "Operation")
        self.about_widget.DropDownMenu.addMenuItem(":/picture/resourses/example.png",
                                                   "Examples")
        self.about_widget.DropDownMenu.tableWidget.itemClicked.connect(self.popFunction)
        ##检查序列的状态
        widget = QWidget(self)
        horizBox = QHBoxLayout(widget)
        horizBox.setContentsMargins(0, 0, 0, 0)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.disp_check_label = QLabel("<span style='font-weight:600; color:red;'>Checking informations...</span>", self)
        self.disp_check_gifLabel = QLabel(self)
        movie = QMovie(":/picture/resourses/Spinner-1s-34px.gif")
        self.disp_check_gifLabel.setMovie(movie)
        self.disp_check_progress = QProgressBar(self)
        self.disp_check_progress.setFixedWidth(100)
        movie.start()
        horizBox.addItem(spacerItem)
        horizBox.addWidget(self.disp_check_gifLabel)
        horizBox.addWidget(self.disp_check_label)
        horizBox.addWidget(self.disp_check_progress)
        self.statusbar.addPermanentWidget(widget)
        self.disp_check_label.setVisible(False)
        self.disp_check_gifLabel.setVisible(False)
        self.disp_check_progress.setVisible(False)
        ###status bar上面加按钮
        self.highlight_identical_btn = QToolButton(self)
        self.highlight_identical_btn.setToolTip("Highlight Identical Sequences")
        icon1 = QIcon(QPixmap(":/picture/resourses/if_Vector-icons_44_1041648.png"))
        self.highlight_identical_btn.setIcon(icon1)
        self.highlight_identical_btn.clicked.connect(self.highlight_identical_sequences)
        self.find_IDs_btn = QToolButton(self)
        self.find_IDs_btn.setToolTip("Find Records by IDs")
        icon2 = QIcon(QPixmap(":/picture/resourses/if_search_126577.png"))
        self.find_IDs_btn.setIcon(icon2)
        self.find_IDs_btn.clicked.connect(self.inputIDS_UI)
        self.statusbar.addPermanentWidget(self.highlight_identical_btn)
        self.statusbar.addPermanentWidget(self.find_IDs_btn)
        # 让这2个button不能被点击
        self.highlight_identical_btn.setDisabled(True)
        self.find_IDs_btn.setDisabled(True)
        self.label_17.linkActivated.connect(self.on_Add_Files_triggered)
        self.label_24.linkActivated.connect(self.on_Add_Files_triggered)
        self.addToolBtn2Tree()
        ##workflow的东西
        self.comboBox.activated[str].connect(self.switchWorkflowResults)
        # 这个放在最后面执行
        ini_index = self.tree_model.index(self.treeRootPath +
                                          os.sep +
                                          "GenBank_File")
        self.treeView.setCurrentIndex(ini_index)
        ## 线程池
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(1)
        self.display(ini_index)

    def switchWorkPlace(self, item):
        currentPlace = item.text()
        if currentPlace != "Others...":
            launcher_settings = QSettings(
                self.thisPath +
                '/settings/launcher_settings.ini',
                QSettings.IniFormat, parent=self)
            launcher_settings.setFallbacksEnabled(False)
            workPlace = launcher_settings.value("workPlace", [self.thisPath])
            workPlace.remove(currentPlace)
            if not os.path.isdir(currentPlace):
                # 没有就创建这个文件夹
                self.factory.creat_dirs(currentPlace)
            sortItems = [currentPlace] + workPlace
            if len(sortItems) > 15:
                sortItems = sortItems[:15]  # 只保留15个工作区
            launcher_settings.setValue("workPlace", sortItems)
            self.hide()
            self.restarted.emit(self, sortItems)
        else:
            # 打开新的选工作路径的
            launcher = Launcher(self)
            launcher.checkBox.hide()
            if launcher.exec_() == QDialog.Accepted:
                sortItems = launcher.WorkPlace
                self.hide()
                self.restarted.emit(self, sortItems)

    def expand(self, path):
        if not os.path.exists(path):
            return
        if os.path.samefile(path, self.treeRootPath):
            ##隐藏非工作区文件和文件夹
            index = self.tree_model.index(path)
            for row in range(self.tree_model.rowCount(index)):
                #找到该路径所在行
                if not self.isWorkPlaceFolder(self.tree_model.filePath(self.tree_model.index(row, 0, index))):
                    self.treeView.setRowHidden(row, index, True)
        if self.isValideName(path, mode="expand"):
            gb_index = self.tree_model.index(self.treeRootPath + os.sep + "GenBank_File")
            other_index = self.tree_model.index(self.treeRootPath + os.sep + "Other_File")
            if not self.treeView.isExpanded(gb_index):
                self.treeView.expand(gb_index)
            if not self.treeView.isExpanded(other_index):
                self.treeView.expand(other_index)
            # print(path)
            # self.treeView.expandAll()
        # elif self.isValideName(path, mode="hide"):
        #     index = self.tree_model.index(path)
        #     self.treeView.setRowHidden(index.row(), index.parent(), True)
        else:
            # 隐藏了output文件夹
            index = self.tree_model.index(path)
            for row in range(self.tree_model.rowCount(index)):
                # child = index.child(row, 0)
                self.treeView.setRowHidden(row, index, True)
        self.addToolBtn2Tree(byFolder=path)  #可能比较耗时
        # self.addToolBtn2Tree(path)
        # 设置按时间先后顺序排序
        # self.tree_model.sort(3)

    def mkdir(self, index=None):
        if not index:
            index = self.treeView.currentIndex()
        if self.tree_model.fileName(index) in ["Other_File", "GenBank_File"]:
            dirname, ok = QInputDialog.getText(
                self, 'Create New Folder', 'Folder Name:%s'%(" "*33))
            if ok and dirname:
                dirname = dirname.strip()
                self.tree_model.mkdir(index, dirname)
                new_index = self.tree_model.index(self.tree_model.filePath(index) + os.sep + dirname)
                self.treeView.setCurrentIndex(new_index)
                # self.display(new_index)
        else:
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>Only root folder can make folder</p>")

    def rmdir(self, index=None):
        if not index:
            index = self.treeView.currentIndex()
        filepath = os.path.normpath(self.tree_model.filePath(
            index))
        # reply = QMessageBox.question(
        #     self,
        #     "Delete folder",
        #     "<p style='line-height:25px; height:25px'>It is safer to delete it in the local file system. "
        #     "Select 'Ok' to open it in local file system.</p>",
        #     QMessageBox.Ok,
        #     QMessageBox.Cancel)
        # if reply == QMessageBox.Ok:
        #     self.factory.openPath(filepath, self)
        if self.isValideName(filepath, mode="recycled"):
            if "recycled" not in filepath:
                recycle_name = self.tree_model.fileName(
                    index.parent()) + "_" + self.tree_model.fileName(index)
                recycle = self.GenBank_File_recycle if "GenBank_File" in filepath else self.Other_File_recycle
                # 先标准化
                recyclePath = os.path.normpath(recycle + os.sep + recycle_name)
                # 打标签
                recyclePath, self.list_repeat_name_num = self.factory.numbered_Name(
                    self.list_repeat_name_num, recyclePath, omit=True)
                # 记录路径，以便恢复
                self.dict_recycled_name[recyclePath] = filepath
                shutil.copytree(filepath, recyclePath)
#                 watcher = QFileSystemWatcher(self)
#                 print(watcher.directories())
#                 watcher.removePath(filepath)
                self.clearFolder(filepath)
                if filepath in self.list_repeat_name_num:
                    self.list_repeat_name_num.remove(filepath)
                recycle_index = self.tree_model.index(recycle)
                # 删除以后，要展示当前的目录
                self.treeView.setCurrentIndex(recycle_index)
                # self.display(self.treeView.currentIndex())
        else:
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>The selected folder can not be removed</p>")

    def rnmdir(self):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        if (
            not os.path.samefile(
                filePath,
                self.treeRootPath +
                os.sep +
                "GenBank_File")) and (
            not os.path.samefile(
                filePath,
                self.treeRootPath +
                os.sep +
                "Other_File")):
            dirname, ok = QInputDialog.getText(
                self, 'Rename Folder', 'New Folder Name:')
            fullpath = os.path.dirname(filePath) + os.sep + dirname
            if ok:
                dir = QDir()
                dir.rename(filePath, fullpath)

    def openID(self):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in
                              indices), reverse=True)
            list_IDs = [currentData[row][0] for row in rows]
            gbManager = GbManager(filePath, parent=self)
            path = gbManager.fetchRecordPath(list_IDs[0])
            self.factory.openPath(path, self)

    def mergeID_slot(self, filePath, list_IDs, for_):
        gbManager = GbManager(filePath, parent=self)
        if for_ == "species":
            dict_spe_gb = {}
            dict_spe_1st_gb = {}
            if len(list_IDs) > 1:
                # mergedGB = Bio.SeqRecord.SeqRecord("")
                for num, ID in enumerate(list_IDs):
                    gbRecord = gbManager.fetchRecordByID(ID)
                    organism = gbRecord.annotations["organism"]
                    if organism not in dict_spe_gb:
                        dict_spe_gb[organism] = gbRecord
                        dict_spe_1st_gb[organism] = gbRecord
                    else:
                        gbRecord.features = [feature for feature in gbRecord.features
                                             if feature.type != "source"]
                        dict_spe_gb[organism] += gbRecord
                for spe in dict_spe_gb:
                    # 创造唯一的id
                    dict_spe_gb[spe].dbxrefs = dict_spe_1st_gb[spe].dbxrefs[:]
                    dict_spe_gb[spe].annotations = dict_spe_1st_gb[spe].annotations.copy()
                    gmt = time.gmtime()
                    ts = calendar.timegm(gmt)
                    dict_spe_gb[spe].id = str(ts)
                    dict_spe_gb[spe].annotations["organism"] = dict_spe_1st_gb[spe].annotations["organism"] + " [merged]"
            else:
                dict_spe_gb["all"] = gbManager.fetchRecordByID(list_IDs[0])
            all_gb_text = "\n".join([mergedGB.format("genbank") for spe, mergedGB in dict_spe_gb.items()])
            gbManager.addRecords(all_gb_text, 0, 100,
                         self.progressSig, self, byContent=True)
        else:
            if len(list_IDs) > 1:
                mergedGB = Bio.SeqRecord.SeqRecord("")
                for num, ID in enumerate(list_IDs):
                    gbRecord = gbManager.fetchRecordByID(ID)
                    if num != 0:
                        gbRecord.features = [feature for feature in gbRecord.features
                                             if feature.type != "source"]
                    else:
                        first_rcd = gbRecord
                    mergedGB += gbRecord
                mergedGB.dbxrefs = first_rcd.dbxrefs[:]
                mergedGB.annotations = first_rcd.annotations.copy()
            else:
                mergedGB = gbManager.fetchRecordByID(list_IDs[0])
                first_rcd = mergedGB
            # 创造唯一的id
            gmt = time.gmtime()
            ts = calendar.timegm(gmt)
            mergedGB.id = str(ts)
            mergedGB.annotations["organism"] = first_rcd.annotations["organism"] + " [merged]"
            gb_text = mergedGB.format("genbank")
            if gbManager.isValidGB(gb_text):
                gbManager.addRecords(gb_text, 0, 100,
                                     self.progressSig, self, byContent=True)

    def mergeID(self):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in
                              indices), reverse=True)
            list_IDs = [currentData[row][0] for row in rows]
            if len(list_IDs) == 1:
                QMessageBox.warning(
                    self,
                    "Warning",
                    "<p style='line-height:25px; height:25px'>Please select at least two sequences!</p>")
                return
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "<p style='line-height:25px; height:25px'>Do you want to merge by species? "
                "If not, PhyloSuite will merge all these sequences into one sequence.</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            for_ = "species" if reply == QMessageBox.Yes else "all"
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "Importing...", parent=self)
            self.progressDialog.show()
            gbWorker = WorkThread(lambda: self.mergeID_slot(filePath, list_IDs, for_),
                                  parent=self)
            gbWorker.finished.connect(lambda: [self.progressDialog.close(), self.display(index)])
            gbWorker.start()
        else:
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>Please select IDs!</p>")
            if hasattr(self, "tableView") and self.tableView.model() and self.tableView.model().arraydata:
                self.tableView.selectAll()

    def copyID(self):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in
                              indices), reverse=True)
            list_IDs = [currentData[row][0] for row in rows]
            gbManager = GbManager(filePath, parent=self)
            contents = gbManager.fetchContentsByIDs(list_IDs)
            QApplication.clipboard().setText(contents)
        else:
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>Please select IDs!</p>")
            if hasattr(self, "tableView") and self.tableView.model() and self.tableView.model().arraydata:
                self.tableView.selectAll()

    def cutID(self):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in
                              indices), reverse=True)
            list_IDs = [currentData[row][0] for row in rows]
            gbManager = GbManager(filePath, parent=self)
            contents = gbManager.fetchContentsByIDs(list_IDs)
            self.rmTableRow()
            QApplication.clipboard().setText(contents)
        else:
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>Please select IDs!</p>")
            if hasattr(self, "tableView") and self.tableView.model() and self.tableView.model().arraydata:
                self.tableView.selectAll()

    def pasteID(self):
        treeIndex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(treeIndex)
        if not self.isWorkFolder(filePath, mode="gb"):
            # QMessageBox.warning(
            #     self,
            #     "Warning",
            #     "<p style='line-height:25px; height:25px'>Please select a work folder!</p>")
            return
        text = QApplication.clipboard().text()
        gbManager = GbManager(filePath, parent=self)
        if gbManager.isValidGB(text):
            # self.tableView.model().layoutAboutToBeChanged.emit()
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "Importing...", parent=self)
            self.progressDialog.show()
            gbWorker = WorkThread(lambda: gbManager.addRecords(text, 0, 100, self.progressSig, self, byContent=True),
                                  parent=self)
            # self.progressDialog.canceled.connect(lambda: [gbWorker.wait(), gbWorker.terminate(),
            #                                               QTimer.singleShot(20, lambda : self.progressDialog.close())]) #这个代码好像会造成RuntimeError: wrapped C/C++ object of type QProgressDialog has been deleted
            gbWorker.finished.connect(lambda: [self.progressDialog.close(), self.display(treeIndex)])
            gbWorker.start()
        elif "\t" in text:
            self.table4Modification(byContent=text)
        else:
            self.clip_query = Lg_ClipQuery(self)
            self.clip_query.setWindowFlags(self.clip_query.windowFlags() | Qt.WindowMinMaxButtonsHint)
            if re.search(r"^>\w+", text):
                is_fas = True
                fas_seq = re.sub(r"(?ms)^>.+?\n", "", text) #re.search(r"(?ms)^>\S+\n([^>]+)(^>|$)", text).group(1)
                fas_seq = re.sub(r"\s", "", fas_seq)
                type = Parsefmt().judge(fas_seq)
                self.clip_query.is_fas = True
                self.clip_query.label_2.setDisabled(True)
                self.clip_query.lineEdit.setDisabled(True)
                self.clip_query.lineEdit.setText("ID(s) already recognized")
            else:
                is_fas = False
                type = Parsefmt().judge(text)
            if type == "DNA":
                seq_type = "nucleotide sequences"
                self.clip_query.radioButton.setChecked(True)
            elif type == "RNA":
                seq_type = "RNA sequences"
                self.clip_query.radioButton_4.setChecked(True)
            elif type == "PROTEIN":
                seq_type = "protein sequences"
                self.clip_query.radioButton_2.setChecked(True)
            else:
                seq_type = "not sequences"
                self.clip_query.radioButton_3.setChecked(True)
            self.clip_query.label.setText("Which type of sequences are in the clipboard content? "
                                          "PhyloSuite guesses these are probably %s."%seq_type)
            reply = self.clip_query.exec_()
            if reply == QDialog.Accepted and (not self.clip_query.radioButton_3.isChecked()):
                ID = self.factory.refineName(self.clip_query.ID)
                organism = self.clip_query.organism
                self.progressDialog = self.factory.myProgressDialog(
                    "Please Wait", "reading sequence...", parent=self)
                self.progressDialog.show()
                gbIO = GbManager(filePath, parent=self)
                fas_content = text if is_fas else ">%s\n%s\n"%(ID, text)
                if is_fas:
                    ID = None
                    fas_content = text
                else:
                    fas_content = ">%s\n%s\n"%(ID, text)
                ##有时候用户选择了其他序列类型
                if self.clip_query.radioButton.isChecked():
                    type = "DNA"
                elif self.clip_query.radioButton_4.isChecked():
                    type = "RNA"
                else:
                    type = "PROTEIN"
                gbWorker = WorkThread(lambda: self.fas2gb(fas_content, gbIO, seq_type=type,
                                                          id=ID, organism=organism), parent=self)
                gbWorker.start()
                gbWorker.finished.connect(lambda: [self.progressDialog.close(), self.setTreeViewFocus(filePath)])
            return
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>The text may not be a accessible GenBank content!</p>")

    def openinwindow(self, index=None):
        if not index:
            index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        self.factory.openPath(filePath, self)

    def openResultsInWindow(self, filePath=None):
        if not filePath:
            return
        if os.path.splitext(filePath)[1].upper() in [".FAS", ".FASTA", ".PHY", ".PHYLIP", ".NEX", ".NXS", ".NEXUS"] and \
                not filePath.endswith(".best_scheme.nex"):
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "loading...", parent=self)
            self.seqViewer = Seq_viewer(filePath, [filePath], self.progressSig, self.progressDialog, self)
            # 添加最大化按钮
            self.seqViewer.setWindowFlags(self.seqViewer.windowFlags() | Qt.WindowMinMaxButtonsHint)
            # self.seqViewer.setWindowModality(Qt.ApplicationModal)
            self.seqViewer.show()
        elif os.path.splitext(filePath)[1].upper() in [".TREEFILE", ".NWK", ".TRE"]:
            tre = self.factory.read_tree(filePath, parent=self)
            if tre:
                tre.show(name="PhyloSuite-ETE", parent=self)
        elif not os.path.isdir(filePath):
            self.factory.openPath(filePath, self)

    def rmTableRow(self, parent=None):
        parent = parent if parent else self
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if indices:
            # 进度条
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "removing...", parent=parent)
            self.progressDialog.show()
            self.tableView.model().layoutAboutToBeChanged.emit()
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in
                              indices), reverse=True)
            list_IDs = []
            for row in rows:
                list_IDs.append(currentData[row][0])
                currentData.pop(row) #必须在这里删currentData，这样tableview才能实时更新
            # list_IDs = [currentData[row][0] for row in rows]
            def judgeData(currentData, index):
                if not currentData: self.display(index)
            gbManager = GbManager(filePath, parent=self)
            deleteWorker = WorkThread(lambda: gbManager.deleteRecords(list_IDs, 0, 100, self.progressSig), parent=self)
            deleteWorker.finished.connect(lambda : [self.progressDialog.close(),
                                                    self.tableView.model().layoutChanged.emit(),
                                                    self.tableView.clearSelection(),
                                                    judgeData(currentData, index)]) #, self.display(index)
            deleteWorker.start()
            # 如果删干净了, 就展示label
            # if not array:
            #     self.stackedWidget.setCurrentIndex(1)
            #     self.stackedWidget.setFocus()

    @pyqtSlot()
    def on_pushButton_clicked(self):
        self.openinwindow()

    @pyqtSlot()
    def on_settings_triggered(self):
        self.setting = Setting(self)
        self.setting.taxmyChangeSig.connect(self.updateTable)
        # 隐藏？按钮
        self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.setting.exec_()
        # self.setting.show()

    @pyqtSlot()
    def on_Add_Files_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        self.addFiles = Lg_addFiles(exportPath=workPath, parent=self)
        self.addFiles.inputSig.connect(self.input)
        self.addFiles.inputContentSig.connect(self.inputGb_content)
        self.addFiles.inputFasSig.connect(self.inputFastaContent)
        # 隐藏？按钮
        self.addFiles.setWindowFlags(self.addFiles.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.addFiles.show()

    @pyqtSlot()
    def on_Normalization_triggered(self):
        indices = self.tableView.selectedIndexes()
        if indices:
            ###提取的设置
            self.GenBankExtract_settings = QSettings(
                self.thisPath + '/settings/GenBankExtract_settings.ini', QSettings.IniFormat)
            self.GenBankExtract_settings.setFallbacksEnabled(False)
            # 字典GenBankExtract_settings里面的set_version存的是版本设置：里面有Features to be extracted， Names unification和
            # Qualifiers to be recognized (rRNA)：；键extract listed gene存的是是否只提取列出来的基因
            self.dict_gbExtract_set = self.GenBankExtract_settings.value("set_version")
            popupGui = NMLPopupGui(self)
            popupGui.addItemWidgets(self.dict_gbExtract_set)
            popupGui.setWindowFlags(popupGui.windowFlags() | Qt.WindowMinMaxButtonsHint)
            popupGui.show()
            if popupGui.exec_() == QDialog.Accepted:
                widget = popupGui.listWidget_framless.itemWidget(popupGui.listWidget_framless.selectedItems()[0])
                dict_NML_settings = deepcopy(widget.dict_extract_settings)
                dict_NML_settings["extract_all_features"] = self.factory.str2bool(self.GenBankExtract_settings.value("extract all features",
                                                                                          "false"))
                self.normalization(widget.version, dict_NML_settings)
        else:
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please select ID(s) first</p>")
            if hasattr(self, "tableView") and self.tableView.model() and self.tableView.model().arraydata:
                self.tableView.selectAll()

    @pyqtSlot()
    def on_Extract_triggered(self):
        treeIndex = self.treeView.currentIndex()
        if treeIndex.isValid():
            indices = self.tableView.selectedIndexes()
            currentModel = self.tableView.model()
            if indices:
                self.progressDialog = self.factory.myProgressDialog(
                    "Please Wait", "preparing...", parent=self)
                self.progressDialog.show()
                currentData = currentModel.arraydata
                rows = sorted(set(index.row() for index in indices))
                self.progressSig.emit(5)
                list_names = []
                list_IDs = []
                for num, row in enumerate(rows):
                    list_IDs.append(currentData[row][0])
                    list_names.append(currentData[row][1] + " " + currentData[row][0])
                    self.progressSig.emit(5 + (num+1)*95/len(rows))
                filePath = self.tree_model.filePath(treeIndex)
                gbManager = GbManager(filePath, parent=self)
                listGB_paths = [gbManager.fetchRecordPath(ID) for ID in list_IDs]
                totalID = len(list_IDs)
                self.progressDialog.close()
                self.extractGB = ExtractGB(
                    gb_files=listGB_paths,
                    list_names=list_names,
                    workPath=filePath,
                    totleID=totalID,
                    clearFolderSig=self.clearFolderSig,
                    focusSig=self.focusSig,
                    parent=self)
                # 添加最大化按钮
                self.extractGB.setWindowFlags(self.extractGB.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.extractGB.show()
                # else:
                #     # 有序列未验证
                #     reply = QMessageBox.information(
                #             self,
                #             "Information",
                #             "<p style='line-height:25px; height:25px'>Please normalize %s first!</p>"%", ".join(list_unverifiedIDs),
                #             QMessageBox.Ok,
                #             QMessageBox.Cancel
                #         )
                #     if reply == QMessageBox.Ok:
                #         self.on_Normalization_triggered()
            else:
                QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Please select ID(s) first</p>")
                if hasattr(self, "tableView") and self.tableView.model() and self.tableView.model().arraydata:
                    self.tableView.selectAll()

    @pyqtSlot()
    def on_Mafft_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        MAFFTpath = self.factory.programIsValid("mafft", mode="tool")
        if MAFFTpath:
            autoInputs = self.factory.init_judge(mode="MAFFT", filePath=filePath, parent=self)
            self.mafft = Mafft(
                autoInputs=autoInputs,
                workPath=workPath,
                mafft_exe=MAFFTpath,
                clearFolderSig=self.clearFolderSig,
                focusSig=self.focusSig,
                parent=self)
            # 添加最大化按钮
            self.mafft.setWindowFlags(self.mafft.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.mafft.show()
            if (not autoInputs) and (not self.factory.autoInputDisbled()):
                self.mafft.popupAutoDec(init=True)
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install MAFFT first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()

    @pyqtSlot()
    def on_Concatenate_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        autoInputs = self.factory.init_judge(mode="Concatenation", filePath=filePath, parent=self)
        self.concatenate = Matrix(
            files=autoInputs,
            workPath=workPath,
            focusSig=self.focusSig,
            parent=self)
        # 添加最大化按钮
        self.concatenate.setWindowFlags(self.concatenate.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.concatenate.show()
        if (not autoInputs) and (not self.factory.autoInputDisbled()):
            self.concatenate.popupAutoDec(init=True)

    @pyqtSlot()
    def on_ParseANNT_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="other")
        indices = self.tableView_2.selectedIndexes()
        files = []
        if self.stackedWidget.currentIndex() == 2 and indices:
            currentModel = self.tableView_2.model()
            rows = sorted(set(index.row() for index in indices), reverse=True)
            currentData = currentModel.arraydata
            files = [filePath + os.sep + currentData[row][0] for row in rows if "Word annotation file" in currentData[row]]
        TSpath = self.factory.programIsValid("tbl2asn", mode="tool")
        if TSpath:
            self.parseANNT = ParseANNT(
                workPath=workPath,
                t2n_exe=TSpath,
                inputDocxs=files,
                focusSig=self.focusSig,
                parent=self)
            # 添加最大化按钮
            self.parseANNT.setWindowFlags(self.parseANNT.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.parseANNT.show()
            # else:
            #     QMessageBox.information(
            #         self,
            #         "Information",
            #         "<p style='line-height:25px; height:25px'>Please select Word file(s) first</p>")
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install tbl2asn first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() & ~Qt.WindowContextHelpButtonHint)
                self.setting.exec_()

    @pyqtSlot()
    def on_Compare_table_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        autoInputs = self.factory.init_judge(mode="compare_table", filePath=filePath, parent=self)
        MAFFTpath = self.factory.programIsValid("mafft", mode="tool")
        if MAFFTpath:
            # if fileName == "extract_results":
            #     files = glob.glob(
            #         filePath + os.sep + "StatFiles\\speciesSTAT\\*.csv")
            #     orgFiles = [i for i in files if "_org" in i]
            #     workPath = self.tree_model.filePath(treeIndex.parent())
            # else:
            #     orgFiles = None
            #     if self.isWorkFolder(filePath):
            #         workPath = filePath
            #     elif self.isResultsFolder(filePath):
            #         workPath = self.tree_model.filePath(treeIndex.parent())
            #     else:
            #         workPath = self.treeRootPath + os.sep + "GenBank_File/files"
            self.compareTable = CompareTable(
                autoInputs, workPath, self.focusSig, MAFFTpath, self)
            # 添加最大化按钮
            self.compareTable.setWindowFlags(self.compareTable.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.compareTable.show()
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install MAFFT first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()

    @pyqtSlot()
    def on_actionRSCUfig_triggered(self):
        try:
            import plotly
            import pandas as pd
            from src.Lg_RSCUfig import DrawRSCUfig
            flag = True
        except:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install plot engine of PhyloSuite first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()
            flag = False
        if flag:
            filePath, workPath = self.fetchWorkPath(mode="all")
            autoInputs = self.factory.init_judge(mode="RSCU", filePath=filePath, parent=self)
            self.RSCUfig = DrawRSCUfig(
                autoInputs, workPath, self.focusSig, self)
            # 添加最大化按钮
            self.RSCUfig.setWindowFlags(self.RSCUfig.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.RSCUfig.show()
        # else:
        #     reply = QMessageBox.information(
        #         self,
        #         "Information",
        #         "<p style='line-height:25px; height:25px'>Please install Rscript first!</p>",
        #         QMessageBox.Ok,
        #         QMessageBox.Cancel)
        #     if reply == QMessageBox.Ok:
        #         self.setting = Setting(self)
        #         self.setting.display_table(self.setting.listWidget.item(1))
        #         # 隐藏？按钮
        #         self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        #         self.setting.exec_()

    # @pyqtSlot()
    # def on_actionPlot_triggered(self):
    #     treeIndex = self.treeView.currentIndex()
    #     filePath = self.tree_model.filePath(treeIndex)
    #     fileName = self.tree_model.fileName(treeIndex)
    #     if fileName == "extract_results":
    #         stack_files = glob.glob(
    #             filePath + os.sep + "StatFiles\\RSCU\\*_stack.csv")
    #         allStack = filePath + os.sep + "StatFiles\\RSCU\\all_AA_stack.csv"
    #         if os.path.exists(allStack):
    #             stack_files.remove(allStack)
    #         workPath = self.tree_model.filePath(treeIndex.parent())
    #     else:
    #         stack_files = None
    #         if self.isWorkFolder(filePath):
    #             workPath = filePath
    #         elif self.isResultsFolder(filePath):
    #             workPath = self.tree_model.filePath(treeIndex.parent())
    #         else:
    #             workPath = self.treeRootPath + os.sep + "GenBank_File/files"
    #     self.plot = Plot(workPath, self.focusSig, self)
    #     # 添加最大化按钮
    #     self.plot.setWindowFlags(self.plot.windowFlags() | Qt.WindowMinMaxButtonsHint)
    #     self.plot.show()

    @pyqtSlot()
    def on_actionDrawGO_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        autoInputs = self.factory.init_judge(mode="drawGO", filePath=filePath, parent=self)
        self.drawGO = DrawGO(
            autoInputs, workPath, self.focusSig, self)
        # 添加最大化按钮
        self.drawGO.setWindowFlags(self.drawGO.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.drawGO.show()

    @pyqtSlot()
    def on_actionWorkplace_triggered(self):
        self.actionWorkplace.menu().popup(QCursor.pos())

    @pyqtSlot()
    def on_actionPartitionFinder_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        Py27Path = self.factory.programIsValid("python27", mode="tool")
        PFpath = self.factory.programIsValid("PF2", mode="tool")
        need_configure = False
        if PFpath:
            if os.path.exists(PFpath + os.sep + "PartitionFinder.py") and (not Py27Path):
                ##脚本形式的
                message = "Please install Python 2.7 first, as PartitionFinder2 python scripts relies on it!"
                need_configure = True
        else:
            message = "Please install PartitionFinder2 first!"
            need_configure = True
        if need_configure:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>%s!</p>"%message,
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()
            return
        ##先找到可以用于自动导入的路径
        autoPartFindPath = self.factory.init_judge(mode="PartitionFinder2", filePath=filePath, parent=self)
        self.partfind = PartitionFinder(
            autoPartFindPath, workPath, self.focusSig, PFpath, Py27Path, False, self)
        # 添加最大化按钮
        self.partfind.setWindowFlags(self.partfind.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.partfind.show()
        if (not autoPartFindPath) and (not self.factory.autoInputDisbled()):
            self.partfind.popupAutoDec(init=True)

    @pyqtSlot()
    def on_actiontrimAl_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        TApath = self.factory.programIsValid("trimAl", mode="tool")
        if TApath:
            autoInputs = self.factory.init_judge(mode="trimAl", filePath=filePath, parent=self)
            self.trimAl = TrimAl(workPath, TApath, autoInputs, self.focusSig, False, self)
            # 添加最大化按钮
            self.trimAl.setWindowFlags(self.trimAl.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.trimAl.show()
            if (not autoInputs) and (not self.factory.autoInputDisbled()):
                self.trimAl.popupAutoDec(init=True)
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install trimAl first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()

    @pyqtSlot()
    def on_actionHmmCleaner_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        HmmCleanerpath = self.factory.programIsValid("HmmCleaner", mode="tool")
        perl = self.factory.programIsValid("perl", mode="tool")
        need_configure = False
        #hmmbuild
        if HmmCleanerpath:
            if HmmCleanerpath != "HmmCleaner.pl":
                ## 证明HmmCleaner没有在环境变量
                if not perl:
                    ##脚本形式的
                    message = "Please install Perl 5 first, as HmmCleaner.pl relies on it!"
                    need_configure = True
        else:
            message = "Please install HmmCleaner first!"
            need_configure = True
        # hmmbuild
        popen = subprocess.Popen(
            "hmmbuild -h", stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        stdout = self.factory.getSTDOUT(popen)
        if not re.search(r"hmmbuild \[-options\]", stdout, re.I):
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>HmmCleaner relies on HMMER version 3.1b2 (http://hmmer.org)!"
                " Please install it and add its subprograms (e.g. hmmbuild) to the environment variable ($PATH, mandatory).</p>")
        if need_configure:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>%s!</p>"%message,
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()
            return
        autoInputs = self.factory.init_judge(mode="HmmCleaner", filePath=filePath, parent=self)
        self.HmmCleaner = HmmCleaner(workPath, HmmCleanerpath, autoInputs, perl, self.focusSig, False, self)
        # 添加最大化按钮
        self.HmmCleaner.setWindowFlags(self.HmmCleaner.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.HmmCleaner.show()
        if (not autoInputs) and (not self.factory.autoInputDisbled()):
            self.HmmCleaner.popupAutoDec(init=True)

    @pyqtSlot()
    def on_actionGblocks_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        GBpath = self.factory.programIsValid("gblocks", mode="tool")
        if GBpath:
            autoInputs = self.factory.init_judge(mode="Gblocks", filePath=filePath, parent=self)
            self.gblocks = Gblocks(autoInputs,
                workPath, self.focusSig, GBpath, False, self)
            # 添加最大化按钮
            self.gblocks.setWindowFlags(self.gblocks.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.gblocks.show()
            if (not autoInputs) and (not self.factory.autoInputDisbled()):
                self.gblocks.popupAutoDec(init=True)
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install Gblocks first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()

    @pyqtSlot()
    def on_actionModelFinder_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        IQpath = self.factory.programIsValid("iq-tree", mode="tool")
        if IQpath:
            input_file, partition_file = self.factory.init_judge(mode="ModelFinder", filePath=filePath, parent=self)
            self.IQtree = ModelFinder(input_file, partition_file,
                                   workPath, self.focusSig, IQpath, False, self)
            # 添加最大化按钮
            self.IQtree.setWindowFlags(self.IQtree.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.IQtree.show()
            if (not input_file) and (not self.factory.autoInputDisbled()):
                self.IQtree.popupAutoDec(init=True)
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install IQ-TREE first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()

    @pyqtSlot()
    def on_actionIQTREE_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        IQpath = self.factory.programIsValid("iq-tree", mode="tool")
        if IQpath:
            input_MSA, model = self.factory.init_judge(mode="IQ-TREE", filePath=filePath, parent=self)
            self.IQtree_infer = IQTREE(input_MSA, model,
                                      workPath, self.focusSig, IQpath, False, self)
            # 添加最大化按钮
            self.IQtree_infer.setWindowFlags(self.IQtree_infer.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.IQtree_infer.show()
            if (not input_MSA) and (not self.factory.autoInputDisbled()):
                self.IQtree_infer.popupAutoDec(init=True)
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install IQ-TREE first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()

    @pyqtSlot()
    def on_actionFastTree_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        FastTreePath = self.factory.programIsValid("FastTree", mode="tool")
        if FastTreePath:
            input_MSA, model = self.factory.init_judge(mode="FastTree", filePath=filePath, parent=self)
            self.FastTree = FastTree(input_MSA, model,
                                       workPath, self.focusSig, FastTreePath, False, self)
            # 添加最大化按钮
            self.FastTree.setWindowFlags(self.FastTree.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.FastTree.show()
            if (not input_MSA) and (not self.factory.autoInputDisbled()):
                self.FastTree.popupAutoDec(init=True)
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install FastTree first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()

    @pyqtSlot()
    def on_actionMrBayes_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        MBpath = self.factory.programIsValid("MrBayes", mode="tool")
        if MBpath:
            input_MSA, input_model = self.factory.init_judge(mode="MrBayes", filePath=filePath, parent=self)
            if type(input_MSA) == list:
                #otherfile的自动导入会传过来列表
                input_MSA = input_MSA[0] if input_MSA else None
            if input_MSA:   # and (os.path.splitext(input_MSA)[1].upper() not in [".NEX", ".NXS", ".NEXUS"]):
                def startMB(input_MSA, input_model, workPath, focusSig, MBpath, workflow, parent):
                    MrBayes_infer = MrBayes(input_MSA, input_model,
                                            workPath, focusSig, MBpath, workflow, parent)
                    # 添加最大化按钮
                    MrBayes_infer.setWindowFlags(MrBayes_infer.windowFlags() | Qt.WindowMinMaxButtonsHint)
                    MrBayes_infer.show()
                if os.path.splitext(input_MSA)[1].upper() not in [".NEX", ".NXS", ".NEXUS"]:
                    #转格式
                    self.progressDialog = self.factory.myProgressDialog(
                        "Please Wait", "Converting format...", busy=True, parent=self)
                    # self.progressDialog.setMaximum(0)
                    # self.progressDialog.setMinimum(0)
                    self.progressDialog.show()
                    # convertfmt = Convertfmt(**{"export_path": os.path.dirname(input_MSA), "files": [input_MSA],
                    #                            "export_nexi": True, #"progressSig": self.progressSig,
                    #                            "exception_signal": self.exception_signal})
                    # convertfmt.exec_()
                    # input_MSA = convertfmt.f3
                    self.convertfmt = Convertfmt(**{"export_path": os.path.dirname(input_MSA), "files": [input_MSA],
                                  "export_nexi": True,  "remove B": True,
                                  "exception_signal": self.exception_signal})
                    gbWorker = WorkThread(
                        lambda: self.convertfmt.exec_(),
                        parent=self)
                    gbWorker.finished.connect(lambda: [self.progressDialog.close(), startMB(self.convertfmt.f3, input_model,
                                                 workPath, self.focusSig, MBpath, False, self)])
                    gbWorker.start()
                else:
                    startMB(input_MSA, input_model,
                            workPath, self.focusSig, MBpath, False, self)
            else:
                self.MrBayes_infer = MrBayes(input_MSA, input_model,
                                             workPath, self.focusSig, MBpath, False, self)
                # 添加最大化按钮
                self.MrBayes_infer.setWindowFlags(self.MrBayes_infer.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.MrBayes_infer.show()
                if not self.factory.autoInputDisbled():
                    self.MrBayes_infer.popupAutoDec(init=True)
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install MrBayes first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()

    @pyqtSlot()
    def on_actionWorkflow_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        self.work_flow = WorkFlow(workPath=workPath,
                                  clearFolderSig=self.clearFolderSig,
                                  focusSig=self.focusSig,
                                  parent=self)
        # 添加最大化按钮
        self.work_flow.setWindowFlags(self.work_flow.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.work_flow.show()

    # @pyqtSlot()
    def on_actionDisplay_triggered(self, index=None):
        treeIndex = self.treeView.currentIndex() if not index else index
        filePath = self.tree_model.filePath(treeIndex)
        if not self.isWorkFolder(filePath, mode="gb"):
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>A GenBank_File work folder needs to be selected "
                "(<strong>GenBank_File/files</strong> path is selected automatically).</p>")
            self.setTreeViewFocus(self.treeRootPath + os.sep + "GenBank_File/files")
            filePath = (self.treeRootPath + os.sep + "GenBank_File" + os.sep + "files").replace("\\", "/")
        # print(filePath)
        self.display_settings = DisplaySettings(workPath=filePath, parent=self)
        self.display_settings.updateSig.connect(self.display)
        # 添加最大化按钮
        self.display_settings.setWindowFlags(self.display_settings.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.display_settings.exec_()

    @pyqtSlot()
    def on_ConvertFMT_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        autoInputs = self.factory.init_judge(mode="format conversion", filePath=filePath, parent=self)
        self.convertFMT = ConvertFMT(workPath=workPath,
            focusSig=self.focusSig,
            autoFiles=autoInputs,
            parent=self)
        if (not autoInputs) and (not self.factory.autoInputDisbled()):
            self.convertFMT.popupAutoDec(init=True)
        # 添加最大化按钮
        self.convertFMT.setWindowFlags(self.convertFMT.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.convertFMT.show()

    @pyqtSlot()
    def on_seqViewer_triggered(self):
        tindex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(tindex)
        files = []
        if self.isWorkFolder(filePath, mode="other"):
            indices = self.tableView_2.selectedIndexes()
            model = self.tableView_2.model()
            rows = list(set([index.row() for index in indices]))
            files = [filePath + os.sep + model.arraydata[row][0] for row in rows if model.arraydata[row][1] == "Alignment file"]
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "loading...", parent=self)
        self.seqViewer = Seq_viewer(filePath, files, self.progressSig, self.progressDialog, self)
        # 添加最大化按钮
        self.seqViewer.setWindowFlags(self.seqViewer.windowFlags() | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.seqViewer.setWindowModality(Qt.ApplicationModal)
        self.seqViewer.show()

    @pyqtSlot()
    def on_MACSE_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        JAVApath = self.factory.programIsValid("java", mode="tool")
        macseEXE = self.factory.programIsValid("macse", mode="tool")
        need_configure = False
        if macseEXE:
            if os.path.exists(macseEXE) and (not JAVApath):
                ##脚本形式的
                message = "Please install JAVA (JRE > 1.5) first, as MACSE relies on it!"
                need_configure = True
        else:
            message = "Please install MACSE first!"
            need_configure = True
        if need_configure:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>%s!</p>" % message,
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()
            return
        autoInputs = self.factory.init_judge(mode="MACSE", filePath=filePath, parent=self)
        self.MACSE = MACSE(workPath, self.focusSig, False, JAVApath, macseEXE, autoInputs, self)
        # 添加最大化按钮
        self.MACSE.setWindowFlags(self.MACSE.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.MACSE.show()
        if (not autoInputs) and (not self.factory.autoInputDisbled()):
            self.MACSE.popupAutoDec(init=True)
    @pyqtSlot()
    def on_GBextSetting_triggered(self):
        self.extract_setting = ExtractSettings(self)
        # self.extract_setting.closeSig.connect(self.displaySettings)
        # 添加最大化按钮
        self.extract_setting.setWindowFlags(self.extract_setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.extract_setting.exec_()

    @pyqtSlot()
    def on_UpdateApp_triggered(self):
        self.wait_state = ProgressDialog(window_title="Please wait", label_text="Checking updates...",
                                              mode="waiting", parent=self)
        self.wait_state.show()
        QCoreApplication.processEvents()
        ###必须先断开信号的连接
        self.factory.checkUpdates(self.updateSig, self.exception_signal, parent=self)

    @pyqtSlot()
    def on_manualUpdate_triggered(self):
        update_path = self.factory.get_update_path()
        self.Manual_update = LG_Manual_update(
                                       update_path=update_path,
                                       parent=self,
                                       thisPath=self.thisPath)
        self.Manual_update.setWindowFlags(self.Manual_update.windowFlags() |
                                          Qt.WindowMinMaxButtonsHint)
        self.Manual_update.show()

    @pyqtSlot()
    def on_About_triggered(self):
        self.about_window = Ui_about()
        dialog = QDialog(self)
        self.about_window.setupUi(dialog)
        # 更新版本
        current_version = self.factory.get_PS_version()
        if current_version:
            self.about_window.label_2.setText(re.sub(r" v[^<]+",
                                        f" v{current_version}",
                                                     self.about_window.label_2.text()))
        self.about_window.label_2.setText(
            self.about_window.label_2.text().replace("font-size:14pt;", "font-size:13pt;"))
        # 添加最大化按钮
        # self.extract_setting.setWindowFlags(
        #     self.extract_setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        dialog.show()

    @pyqtSlot()
    def on_SerhNCBI_triggered(self):
        currentPath, gworkPath = self.fetchWorkPath(mode="all")
        self.search_NCBI = SerhNCBI(workPath=gworkPath, parent=self)
        self.search_NCBI.inputContentSig.connect(self.inputGb_content)
        # 添加最大化按钮
        self.search_NCBI.setWindowFlags(self.search_NCBI.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.search_NCBI.show()

    @pyqtSlot()
    def on_Tiger_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        # autoInputs = self.factory.init_judge(mode="format conversion", filePath=filePath, parent=self)
        self.tiger = Tiger(workPath=workPath,
                         focusSig=self.focusSig,
                         # autoFiles=autoInputs,
                         parent=self)
        # if (not autoInputs) and (not self.factory.autoInputDisbled()):
        #     self.tiger.popupAutoDec(init=True)
        # 添加最大化按钮
        self.tiger.setWindowFlags(self.tiger.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.tiger.show()

    @pyqtSlot()
    def on_TreeAnnotation_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        GUI_TIMEOUT = None
        # autoInputs = self.factory.init_judge(mode="format conversion", filePath=filePath, parent=self)
        scene = _TreeScene()
        scene.init_values(None, TreeStyle(), None, None)
        self.PhyloSuite_ETE = _GUI(scene)
        self.PhyloSuite_ETE.setObjectName("PhyloSuite_ETE")
        self.PhyloSuite_ETE.setParent(self)
        self.PhyloSuite_ETE.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | self.PhyloSuite_ETE.windowFlags())
        self.PhyloSuite_ETE.show()
        # Restore Ctrl-C behavior
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        if GUI_TIMEOUT is not None:
            signal.signal(signal.SIGALRM, exit_gui)
            signal.alarm(GUI_TIMEOUT)

    @pyqtSlot()
    def on_TreeSuite_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        # GUI_TIMEOUT = None
        autoInputs = self.factory.init_judge(mode="tree suite", filePath=filePath, parent=self)
        self.TreeSuite = TreeSuite(workPath=workPath,
                                   focusSig=self.focusSig,
                                   autoInputs=autoInputs,
                                   parent=self)
        self.TreeSuite.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | self.TreeSuite.windowFlags())
        self.TreeSuite.show()
        if (not autoInputs) and (not self.factory.autoInputDisbled()):
            self.TreeSuite.popupAutoDec(init=True)

    @pyqtSlot()
    def on_actionASTRAL_triggered(self):
        filePath, workPath = self.fetchWorkPath(mode="all")
        ASTRALPATH = self.factory.programIsValid("ASTRAL", mode="tool")
        if ASTRALPATH:
            autoInputs = self.factory.init_judge(mode="ASTRAL", filePath=filePath, parent=self)
            self.ASTRAL = ASTRAL(autoInputs, workPath, ASTRALPATH,
                                 self.focusSig, False, self)
            # 添加最大化按钮
            self.ASTRAL.setWindowFlags(self.ASTRAL.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.ASTRAL.show()
            if (not autoInputs) and (not self.factory.autoInputDisbled()):
                self.ASTRAL.popupAutoDec(init=True)
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install ASTRAL first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()

    @pyqtSlot()
    def on_colorsets_triggered(self):
        self.colorset = Colorset(parent=self)
        # 添加最大化按钮
        self.colorset.setWindowFlags(self.colorset.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.colorset.show()

    @pyqtSlot()
    def on_rsl_duplicates_triggered(self):
        MAFFTpath = self.factory.programIsValid("mafft", mode="tool")
        if MAFFTpath:
            cpu_num = multiprocessing.cpu_count()
            list_cpu = [str(i + 1) for i in range(cpu_num)]
            current = cpu_num // 2
            item, ok = QInputDialog.getItem(
                self, "Specify thread number", "Thread:", list_cpu, current, False)
            if ok and item:
                self.progressDialog = self.factory.myProgressDialog(
                    "Please Wait", "Resolving duplicates...", parent=self, busy=True)
                self.progressDialog.show()
                treeIndex = self.treeView_4.currentIndex()
                filePath = self.tree_model4.filePath(treeIndex)
                try:
                    rsl_dupl_worker = DetermineCopyGeneParallel()
                    worker = WorkThread(lambda: rsl_dupl_worker.exec2_(filePath,
                                                                        f"{filePath}/resolve_duplicates",
                                                                        None,
                                                                        mafft_exe=MAFFTpath,
                                                                        threads=int(item),
                                                                        exception_signal=self.exception_signal),
                                                                        parent=self)
                    worker.finished.connect(lambda: [self.progressDialog.close()])
                    worker.start()
                except:
                    exceptionInfo = ''.join(
                        traceback.format_exception(
                            *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
                    self.exception_signal.emit(exceptionInfo)  # 激发这个信号
        else:
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install MAFFT first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                self.setting = Setting(self)
                self.setting.display_table(self.setting.listWidget.item(1))
                # 隐藏？按钮
                self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.setting.exec_()


    def fas2gb(self, fasContent, gbIO, seq_type=None, id=None, organism=None):
        fas_gb_contents = ""
        if ">" not in fasContent:
            self.exception_signal.emit("The input file is not in "
                "'<span style=\"color:red\">FASTA</span>' format!<normal exception>")
            return
        try:
            count = fasContent.count(">")
            parseFMT = Parsefmt()
            new_fas_contents = parseFMT.standardizeFas(StringIO(fasContent), removeAlign=True)
            list_names = []
            for num, record in enumerate(SeqIO.parse(StringIO(new_fas_contents), "fasta")):
                if len(record.name) > 15:
                    name = record.id[:15]
                    if name in list_names:
                        num = 2
                        while (name[:14] + str(num)) in list_names:
                            num += 1
                        name = name[:14] + str(num)
                    record.name = name
                list_names.append(record.name)
                seq_type = parseFMT.judge(str(record.seq)) if not seq_type else seq_type
                if seq_type == "DNA":
                    alphabet = generic_dna
                elif seq_type == "RNA":
                    alphabet = generic_rna
                else:
                    alphabet = generic_protein
                record.seq.alphabet = alphabet
                if id:
                    record.id = id
                record.annotations["organism"] = record.id if not organism else organism
                ##加一个source feature
                my_start_pos = SeqFeature.ExactPosition(0)
                my_end_pos = SeqFeature.ExactPosition(len(record.seq))
                my_feature_location = FeatureLocation(my_start_pos, my_end_pos)
                my_feature_type = "source"
                my_feature = SeqFeature.SeqFeature(my_feature_location, type=my_feature_type)
                record.features.append(my_feature)
                fas_gb_contents += record.format("genbank")
                self.progressSig.emit((num+1) * 80/count)
            gbIO.addRecords(fas_gb_contents, 0, 20, self.progressSig, self, byContent=True)
        except:
            self.exception_signal.emit(''.join(
                traceback.format_exception(*sys.exc_info())) + "\n")

    def inputFastaContent(self, fasContent, filePath=None):
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "reading file...", parent=self)
        self.progressDialog.show()
        treeIndex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(treeIndex) if not filePath else filePath
        gbIO = GbManager(filePath, parent=self)
        gbWorker = WorkThread(lambda : self.fas2gb(fasContent, gbIO),
                              parent=self)
        gbWorker.start()
        gbWorker.finished.connect(lambda: [self.progressDialog.close(), self.setTreeViewFocus(filePath)])

    def inputGb_content(self, content, filePath=None):
        if content:
            treeIndex = self.treeView.currentIndex()
            filePath = self.tree_model.filePath(treeIndex) if not filePath else filePath
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "importing...", parent=self)
            self.progressDialog.show()
            gbIO = GbManager(filePath, parent=self)
            gbWorker = WorkThread(lambda: gbIO.addRecords(content, 0, 100, self.progressSig, self, byContent=True),
                                  parent=self)
            gbWorker.start()
            self.progressDialog.canceled.connect(lambda: [gbWorker.stopWork(),
                                                          self.setTreeViewFocus(filePath)])
            gbWorker.finished.connect(lambda: [self.progressDialog.close(), self.setTreeViewFocus(filePath)])

    def input(self, gb_files, other_files, invalid=None, expFilePath=None):
        # 添加GB文件的系统操作
        treeIndex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(treeIndex) if not expFilePath else expFilePath
        if gb_files:
            # 进度条
            ok = False
            if self.isWorkFolder(filePath, mode="gb"):
                ok = True
            else:
                selected_folder = "GenBank_File/files" if "GenBank_File" in filePath else "Other_File/files"
                reply = QMessageBox.information(
                        self,
                        "PhyloSuite",
                        "<p style='line-height:25px; height:25px'>The selected folder can not display GenBank file(s), "
                        "transfer the files to <strong>%s</strong>?</p>" % selected_folder,
                        QMessageBox.Ok,
                        QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    filePath = self.gb_files_path if "GenBank_File" in filePath else self.other_files_path
                    treeIndex = self.tree_model.index(filePath)
                    self.setTreeViewFocus(filePath)
                    ok = True
            if ok:
                self.progressDialog = self.factory.myProgressDialog(
                    "Please Wait", "importing...", parent=self)
                self.progressDialog.show()
                gbIO = GbManager(filePath, parent=self)
                gbWorker = WorkThread(lambda: gbIO.addRecords(gb_files, 0, 100, self.progressSig, self),
                                      parent=self)
                gbWorker.start()
                gbWorker.finished.connect(lambda: [self.progressDialog.close(), self.setTreeViewFocus(filePath)])
        elif other_files:
            ok = False
            if self.isWorkFolder(filePath, mode="other"):
                ok = True
            else:
                selected_folder = "GenBank_File/files" if "GenBank_File" in filePath else "Other_File/files"
                reply = QMessageBox.information(
                    self,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>The selected folder can not display GenBank file(s), "
                    "transfer the files to <strong>%s</strong>?</p>" % selected_folder,
                    QMessageBox.Ok,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    filePath = self.gb_files_path if "GenBank_File" in filePath else self.other_files_path
                    # treeIndex = self.tree_model.index(filePath)
                    self.setTreeViewFocus(filePath)
                    ok = True
            if ok:
                flag = False
                rgx_path = re.compile(r'[^\w_.)(-:\\]')
                rgx_name = re.compile(r'[^\w_.)(-]')
                for i in other_files:
                    dir = os.path.dirname(i)
                    if rgx_path.search(dir):
                        QMessageBox.warning(
                            self,
                            "Warning",
                            "<p style='line-height:25px; height:25px'>Invalid symbol found in file path, please copy the file to desktop and try again!</p>")
                        continue
                    base = os.path.basename(i)
                    if rgx_name.search(base):
                        base = rgx_name.sub("_", base)
                        flag = True
                    shutil.copyfile(i, filePath + os.sep + base)
                self.setTreeViewFocus(filePath)
                if flag:
                    QMessageBox.information(
                        self,
                        "PhyloSuite",
                        "<p style='line-height:25px; height:25px'>Invalid symbol found in file name, replacing it with '_'!</p>")
        if invalid:
            invalid_files = ", ".join(invalid)
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>Files not accessed: %s</p>"%invalid_files)

    def isValideName(self, filepath, mode=None):  # displayID=False):
        # 控制展示ID， 以及expand tree
        valid = True
        if mode == "gb":
            # 设置只有genBank下面一层文件夹的才可以拖数据
            if not os.path.basename(os.path.dirname(filepath)) == "GenBank_File":
                valid = False
        elif mode == "other":
            # 设置只有Other_File下面一层文件夹的才可以拖数据
            if not os.path.basename(os.path.dirname(filepath)) == "Other_File":
                valid = False
        elif mode == "expand":
            if self.isResultsFolder(filepath):
                valid = False
        elif mode == "recycled":
            base = os.path.basename(filepath)
            for i in ["Other_File", "GenBank_File", "recycled", "files", "flowchart", ".data"]:
                if base == i:
                    valid = False
        elif mode == "dnd":
            # 设置只有genBank下面一层文件夹的才可以拖数据
            if (not os.path.basename(os.path.dirname(filepath)) == "GenBank_File") or (os.path.basename(filepath) == "recycled"):
                valid = False
        return valid

    def display(self, index):
        if type(index) == QItemSelection:
            list_index = index.indexes()
            if list_index:
                index = index.indexes()[0]
            else:
                index = self.treeView.currentIndex()
        self.expandCurrent(index)
        # displayed_IDs用于展示界面，IDs用于提取序列，gb文件用于操作
        filePath = self.tree_model.filePath(index)
        fileName = self.tree_model.fileName(index)
        parentName = self.tree_model.fileName(index.parent())
        self.statusBar().showMessage('')
        #让这2个button不能被点击
        self.highlight_identical_btn.setDisabled(True)
        self.find_IDs_btn.setDisabled(True)
        if fileName == "recycled":
            # 设置一下model为空才执行这个
            tree_model3 = QFileSystemModel(self)
            tree_model3.setRootPath(filePath)
            fileIconProvider = FileIconProvider(trashMode=True)
            tree_model3.setIconProvider(fileIconProvider)
            self.treeView_3.setModel(tree_model3)
            self.treeView_3.setRootIndex(tree_model3.index(filePath))
            self.treeView_3.header().setSectionResizeMode(
                0, QHeaderView.ResizeToContents)
            self.treeView_3.installEventFilter(self)
            self.stackedWidget.setCurrentIndex(5)
        elif fileName == "Flowchart_reports":
            self.refresh_workflow_results(filePath)
        elif self.isResultsFolder(filePath):
            # 设置一下model为空才执行这个
            self.tree_model4 = QFileSystemModel(self)
            self.tree_model4.setReadOnly(False)
            self.tree_model4.setRootPath(filePath)
            self.treeView_4.setModel(self.tree_model4)
            self.treeView_4.setRootIndex(self.tree_model4.index(filePath))
            self.treeView_4.header().setSectionResizeMode(
                0, QHeaderView.ResizeToContents)
            # self.treeView_4.installEventFilter(self)
            self.stackedWidget.setCurrentIndex(8)
            ##选中最新的那个结果
            list_results = [filePath + os.sep + i for i in os.listdir(filePath) if os.path.isdir(filePath + os.sep + i)]
            if list_results:
                newest_results = sorted(list_results,
                       key=os.path.getmtime, reverse=True)[0]
                newest_index = self.tree_model4.index(newest_results)
                self.treeView_4.setCurrentIndex(newest_index)
        elif "GenBank_File" in filePath:
            # 在输出文件夹的时候不执行这个
            if fileName == "GenBank_File":
                self.stackedWidget.setCurrentIndex(6)
            elif self.isValideName(filePath, mode="gb"):
                self.highlight_identical_btn.setDisabled(False)
                self.find_IDs_btn.setDisabled(False)
                self.factory.creat_dirs(filePath + os.sep + ".data")
                gbManager = GbManager(filePath, parent=self)
                array = gbManager.fetch_array()
                gbIndata = gbManager.fetchAllGBpath()
                if (len(array) < 2) and (not gbIndata):
                    ##第一次进入这个工作区，需要初始化一下 info和矩阵
                    gbManager.saveArray(array)
                    gbManager.fetchAvailableInfo()
                    # 如果没数据，就展示文字页
                    self.stackedWidget.setFocus()
                    self.stackedWidget.setCurrentIndex(1)
                else:
                    # 进度条
                    # self.progressDialog = self.factory.myProgressDialog(
                    #     "Please Wait", "updating...", parent=self)
                    # self.progressDialog.show()
                    # #如果有更新，就要重新获得array
                    # haveUpdate = gbManager.updateModifiedRecord(self.progressSig)
                    # if haveUpdate:
                    #     array = gbManager.fetch_array()
                    # haveNewArray = gbManager.updateArrayByInfo(0, 100, self.progressSig)  # 检查是否有需要补充的信息
                    # if haveNewArray:
                    #     array = gbManager.fetch_array()
                    # validatedIDs = gbManager.fetchVerifiedIDs()
                    # reverse_array = [array[0]] + sorted(array[1:], reverse=True) #反转一下
                    # self.progressDialog.close()
                    self.displayTableModel = MyTableModel(
                        array, parent=self)
                    self.tableView.setModel(self.displayTableModel)
                    self.displayTableModel.modifiedSig.connect(
                        self.depositeData)
                    # self.displayTableModel.layoutChanged.connect(
                    #     self.depositeData)
                    self.stackedWidget.setCurrentIndex(0)
                    self.disp_check_label.setVisible(True)
                    self.disp_check_gifLabel.setVisible(True)
                    self.disp_check_progress.setValue(0)
                    self.disp_check_progress.setVisible(True)
                    selectModel = self.tableView.selectionModel()
                    selectModel.selectionChanged.connect(lambda :
                                                         self.statusBar().showMessage(str(len(set([i.row() for i in
                                                        self.tableView.selectedIndexes()]))) + " sequence(s) selected"))
                    # print(int(QThread.currentThreadId()))
                    if not (hasattr(self, "displayWorker") and self.displayWorker.isRunning()):
                        # 如果没有线程在运行
                        self.displayWorker = WorkThread(lambda: self.factory.display_check(array, gbManager, self.exception_signal,
                                                                      self.display_checkSig, self.progressBarSig), parent=self)
                        self.displayWorker.start()
                        self.displayWorker.finished.connect(lambda : [self.disp_check_label.setVisible(False),
                                                                 self.disp_check_gifLabel.setVisible(False),
                                                                 self.disp_check_progress.setVisible(False)])
                    # print(self.displayTableModel.array)
            else:
                self.stackedWidget.setCurrentIndex(3)
        elif "Other_File" in filePath:
            if fileName == "Other_File":
                self.stackedWidget.setCurrentIndex(6)
            elif self.isValideName(filePath, mode="other"):
                list_alignments = self.factory.fetchAlignmentFile(filePath)
                list_docx_files = [filePath + os.sep + i for i in os.listdir(filePath)
                                   if os.path.splitext(i)[1].upper() in [".DOCX", ".DOC", ".ODT", ".DOCM", ".DOTX", ".DOTM", ".DOT"]]
                if (not list_alignments) and (not list_docx_files):
                    # 文件夹没东西就展示这个
                    self.stackedWidget.setCurrentIndex(4)
                    return
                else:
                    # list_docx_files = [filePath + os.sep + i for i in os.listdir(filePath)
                    #                    if os.path.splitext(i)[1].upper() == ".DOCX"]
                    header = ["Name", "Descriptions", "Num. of seq.", "Remarks", "Latest modified", "Date created"]
                    array = []
                    if list_alignments:
                        for alignment in list_alignments:
                            name = os.path.basename(alignment)
                            Description = "Alignment file"
                            ModifiedDate = datetime.datetime.fromtimestamp(os.path.getmtime(alignment)).strftime('%Y-%m-%d %H:%M:%S')
                            CreateDate = datetime.datetime.fromtimestamp(os.path.getctime(alignment)).strftime('%Y-%m-%d %H:%M:%S')
                            dict_taxon = self.parsefmt.readfile(alignment)
                            remarks = "aligned" if self.factory.is_aligned(dict_taxon) else "unaligned"
                            seq_num = str(len(dict_taxon))
                            array.append([name, Description, seq_num, remarks, ModifiedDate, CreateDate])
                    if list_docx_files:
                        for docx in list_docx_files:
                            name = os.path.basename(docx)
                            Description = "Word annotation file"
                            ModifiedDate = datetime.datetime.fromtimestamp(os.path.getmtime(docx)).strftime('%Y-%m-%d %H:%M:%S')
                            CreateDate = datetime.datetime.fromtimestamp(os.path.getctime(docx)).strftime('%Y-%m-%d %H:%M:%S')
                            remarks = "N/A"
                            seq_num = "N/A"
                            array.append([name, Description, seq_num, remarks, ModifiedDate, CreateDate])
                    model = MyOtherFileTableModel(array, header, parent=self)
                    self.tableView_2.setModel(model)
                    self.tableView_2.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
                self.stackedWidget.setCurrentIndex(2)
            else:
                self.stackedWidget.setCurrentIndex(3)

    def modify_table(self, gbManager, array, row, column):
        try:
            gbManager.modifyRecords(array, row, column)  # 传入新的矩阵，以及行和列
        except:
            self.exception_signal.emit(''.join(
                traceback.format_exception(*sys.exc_info())) + "\n")

    def depositeData(self, array, row, column):
        if not array:
            return
        treeIndex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(treeIndex)
        # currentModel = self.tableView.model()
        # array = currentModel.array
        # row, column = index.row(), index.column()
        gbManager = GbManager(filePath, parent=self)
        # gbManager.modifyRecords(array, row, column)
        gbWorker = WorkRunThread(lambda: self.modify_table(gbManager, array, row, column))
        self.pool.start(gbWorker)
        # print(self.pool.activeThreadCount())

    def Progress(self, num, progressCancel=False):
        # self.progressCancel = progressCancel
        # if self.progressCancel:
        #     self.progressDialog.close()
        #     return
        oldValue = self.progressDialog.value()
        done_int = int(num)
        # if done_int == 0:
        #     self.progressDialog.close()
        if done_int > oldValue:
            # print(done_int)
            self.progressDialog.setProperty("value", done_int)
            QCoreApplication.processEvents()
            if done_int == 100:
                self.progressDialog.close()

    def clearFolder(self, filepath):
        list_folder = self.factory.delete_all_files(filepath)
        # 从子文件夹到父文件夹排列
        list_folder_sorted = [k[1] for k in sorted(list(map(lambda x, y: (
            x, y), [j.count("\\") for j in list_folder], list_folder)), reverse=True)]
        for path in list_folder_sorted:
            self.tree_model.rmdir(self.tree_model.index(path))
        # print("remain dir: ", os.listdir(filepath))
        self.treeView.update(self.tree_model.index(filepath))

    def saveTable(self):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        indices = self.tableView.selectedIndexes()
        # 在输出文件夹的时候不执行这个
        if self.isValideName(filePath, mode="gb"):
            rows = sorted(set(index.row() for index in
                              indices))
            array = self.tableView.model().arraydata[:]
            header = self.tableView.model().headerdata[:]
            # print(rows)
            save_array = [header] + [array[row] for row in rows]
            save_array[0][0] = '="ID"' #这样才不会报Excel CSV import returns an SYLK file format error错误
            fileName = QFileDialog.getSaveFileName(
                self, "PhyloSuite", "table", "CSV Format(*.csv)")
            if fileName[0]:
                self.factory.write_csv_file(fileName[0], save_array, self)
        else:
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>No table available</p>")

    def recursePath(self, model, rootIndex):
        '''得到目标index下面的所有子文件和文件夹的modelIndex（前提是得要展开expand）'''
        def recurse(model, rootIndex):
            for row in range(model.rowCount(rootIndex)):
                child = rootIndex.child(row, 0)
                yield child
                if model.hasChildren(child):
                    yield from recurse(model, child)
        sys.setrecursionlimit(10000)
        if rootIndex is not None:
            yield from recurse(model, rootIndex)

    def guiSave(self):
        # Save geometry
        self.mainwindow_settings.setValue('size', self.size())
        # self.mainwindow_settings.setValue('pos', self.pos())
        self.mainwindow_settings.setValue(
            'numbered recycled name', self.list_repeat_name_num)
        self.mainwindow_settings.setValue(
            'recycled name', self.dict_recycled_name)
        # if hasattr(self, "dict_workflow_reports"):
        #     self.mainwindow_settings.setValue(
        #         'workflow_reports', self.dict_workflow_reports)

    def guiRestore(self):
        # Restore geometry
        self.resize(self.mainwindow_settings.value('size', QSize(1195, 650)))
        self.factory.centerWindow(self)
        if self.width() < 1120:
            self.resize(QSize(1195, 650))
        # self.move(self.mainwindow_settings.value('pos', QPoint(471, 207)))
        self.list_repeat_name_num = self.mainwindow_settings.value(
            'numbered recycled name', [])
        # 清零无效的路径
        if self.list_repeat_name_num:
            # 必须深拷贝，才能删除
            list_repeat_name_num = deepcopy(self.list_repeat_name_num)
            for i in list_repeat_name_num:
                if not os.path.exists(i):
                    self.list_repeat_name_num.remove(i)
        else:
            # 有时候空的列表没法存
            self.list_repeat_name_num = []
        self.dict_recycled_name = self.mainwindow_settings.value(
            'recycled name', {})
        # self.dict_workflow_reports = self.mainwindow_settings.value(
        #     'workflow_reports', {})
        # if self.dict_workflow_reports:
        #     self.display_workflow_report(self.dict_workflow_reports)
#         if(self.mainwindow_settings.contains("Model/model")):  # 此节点是否存在该数据
#             model = self.mainwindow_settings.value("Model/model")
#             exec('''self.qmodel=%s''' % (model))
#             print('2:', self.qmodel)
#         model = self.factory.readArgs(".", "model.pkl").__init__()
#         print(model)
        # tableView_2右键菜单
        tableView_2_popMenu = QMenu(self)
        openFile = QAction(QIcon(":/seq_Viewer/resourses/field-Display.png"), "Open", self,
                       statusTip="open file",
                       triggered=self.open_tableItemByMenu)
        addFile = QAction(QIcon(":/picture/resourses/iconfinder_file_add_48761.png"), "Add file", self,
                           statusTip="Add file",
                           triggered=self.on_Add_Files_triggered)
        saveAs = QAction(QIcon(":/picture/resourses/Save-icon.png"), "Save as", self,
                       shortcut=QKeySequence("Ctrl+S"),
                       statusTip="save file",
                       triggered=self.save_other_file)
        removeFile = QAction(QIcon(":/picture/resourses/if_Delete_1493279.png"), "Remove", self,
                             shortcut=QKeySequence.Delete,
                             statusTip="remove file",
                             triggered=self.removeFiles)
        mafft = QAction(QIcon(":/picture/resourses/mafft1.png"), "Import to MAFFT", self,
                        statusTip="Align with MAFFT",
                        triggered=self.on_Mafft_triggered)
        MACSE = QAction(QIcon(":/picture/resourses/M.png"), "Import to MACSE (for CDS)", self,
                        statusTip="Align with MACSE",
                        triggered=self.on_MACSE_triggered)
        trimAl = QAction(QIcon(":/picture/resourses/icon--trim-confirm-0.png"), "Import to trimAl", self,
                        statusTip="trimAl",
                        triggered=self.on_actiontrimAl_triggered)
        HmmCleaner = QAction(QIcon(":/picture/resourses/clean.png"), "Import to HmmCleaner", self,
                        statusTip="HmmCleaner",
                        triggered=self.on_actionHmmCleaner_triggered)
        gblocks = QAction(QIcon(":/picture/resourses/if_simpline_22_2305632.png"), "Import to Gblocks", self,
                          statusTip="Gblocks",
                          triggered=self.on_actionGblocks_triggered)
        catSeq = QAction(QIcon(":/picture/resourses/cat1.png"), "Import to Concatenate Sequence", self,
                         statusTip="Concatenate Sequence",
                         triggered=self.on_Concatenate_triggered)
        cvtFMT = QAction(QIcon(":/picture/resourses/transform3.png"), "Import to Convert Sequence Format", self,
                         statusTip="Convert Sequence Format",
                         triggered=self.on_ConvertFMT_triggered)
        modelfinder = QAction(QIcon(":/picture/resourses/if_tinder_334781.png"), "Import to ModelFinder", self,
                              statusTip="Select model with ModelFinder",
                              triggered=self.on_actionModelFinder_triggered)
        iqtree = QAction(QIcon(":/picture/resourses/data-taxonomy-icon.png"), "Import to IQ-TREE", self,
                         statusTip="Reconstruct tree with IQ-TREE",
                         triggered=self.on_actionIQTREE_triggered)
        mrbayes = QAction(QIcon(":/picture/resourses/2000px-Paris_RER_B_icon.svg.png"), "Import to MrBayes", self,
                          statusTip="Reconstruct tree with MrBayes",
                          triggered=self.on_actionMrBayes_triggered)
        parseANNT = QAction(QIcon(":/picture/resourses/WORD.png"), "Import to Parse Annotation", self,
                            statusTip="Parse Annotation",
                            triggered=self.on_ParseANNT_triggered)
        ASTRAL = QAction(QIcon(":/picture/resourses/menu_icons/A2.png"), "Import to ASTRAL", self,
                            statusTip="Reconstruct species tree with ASTRAL",
                            triggered=self.on_actionASTRAL_triggered)
        if platform.system().lower() in ["darwin", "linux"]:
            HmmCleaner.setVisible(True)
        else:
            HmmCleaner.setVisible(False)
        tableView_2_popMenu.addAction(openFile)
        tableView_2_popMenu.addAction(addFile)
        tableView_2_popMenu.addAction(saveAs)
        tableView_2_popMenu.addAction(removeFile)
        tableView_2_popMenu.addSeparator()
        tableView_2_popMenu.addAction(mafft)
        tableView_2_popMenu.addAction(MACSE)
        tableView_2_popMenu.addAction(trimAl)
        tableView_2_popMenu.addAction(HmmCleaner)
        tableView_2_popMenu.addAction(gblocks)
        tableView_2_popMenu.addAction(catSeq)
        tableView_2_popMenu.addAction(cvtFMT)
        tableView_2_popMenu.addSeparator()
        tableView_2_popMenu.addAction(modelfinder)
        tableView_2_popMenu.addAction(iqtree)
        tableView_2_popMenu.addAction(mrbayes)
        tableView_2_popMenu.addAction(parseANNT)
        tableView_2_popMenu.addAction(ASTRAL)
        if os.name != "nt":
            parseANNT.setVisible(False)

        def popup(qpoint):
            if self.tableView_2.indexAt(qpoint).isValid():
                tableView_2_popMenu.exec_(QCursor.pos())

        self.tableView_2.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView_2.customContextMenuRequested.connect(popup)
        if platform.system().lower() == "linux":
            self.pushButton.setText("Click here to show path")

    def closeEvent(self, event):
        self.guiSave()

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        name = obj.objectName()
        if isinstance(obj, QTreeView):
            if event.type() == QEvent.KeyPress:  # 首先得判断type
                if event.key() == Qt.Key_Delete:
                    if name == "treeView":
                        self.rmdir()
                        return True
                    elif name == "treeView_3":
                        self.recycled_remove()
                        return True
                if event.key() == Qt.Key_F2:
                    if name == "treeView":
                        self.rnmdir()
                        return True
            if name == "treeView":
                if event.type() == QEvent.DragEnter:
                    if "application/x-qabstractitemmodeldatalist" in event.mimeData().formats():
                        event.accept()
                        return True
                if event.type() == QEvent.Drop:
                    currentIndex = obj.currentIndex()
                    pos = event.pos()
                    index = obj.indexAt(pos)
                    if currentIndex == index:
                        return True
                    filePath = obj.model().filePath(index)
                    if self.isValideName(filePath, mode="dnd"):
                        self.drop2treeView(filePath)
        if isinstance(
                obj,
                QTableView) or isinstance(
                obj,
                QLabel) or isinstance(
                obj,
                QStackedWidget):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                if name in ["label", "label_2", "label_3", "stackedWidget", "tableView", "label_4"]:
                    files = [u.toLocalFile() for u in event.mimeData().urls()]
                    gb_files = []
                    other_files = []
                    csv_files = []
                    invalid_files = []
                    list_fas = []
                    for i in files:
                        if os.path.splitext(i)[1].upper() in [".GB", ".GBK", ".GP", ".GBF", ".GBFF"]:
                            gb_files.append(i)
                        elif os.path.splitext(i)[1].upper() in [".DOCX", ".DOC", ".ODT", ".DOCM", ".DOTX", ".DOTM", ".DOT",
                                                                ".FAS", ".FASTA", ".PHY",
                                                                ".PHYLIP", ".NEX", ".NXS", ".NEXUS"]:
                            if os.path.splitext(i)[1].upper() in [".FAS", ".FASTA"]:
                                list_fas.append(i)
                            other_files.append(i)
                        elif os.path.splitext(i)[1].upper() == ".CSV":
                            csv_files.append(i)
                        else:
                            invalid_files.append(os.path.basename(i))
                    treeIndex = self.treeView.currentIndex()
                    filePath = self.tree_model.filePath(treeIndex)
                    root_name = self.isWorkFolder(filePath)
                    if root_name == "Other_File":
                        invalid_files = invalid_files + [os.path.basename(k) for k in gb_files]
                        gb_files = []
                    else:
                        invalid_files = invalid_files + [os.path.basename(l) for l in other_files]
                        other_files = []
                        if list_fas:
                            fasContent = ""
                            for i in list_fas:
                                invalid_files.remove(os.path.basename(i))
                                with open(i, encoding="utf-8", errors='ignore') as f:
                                    fasContent += f.read() + "\n"
                            self.inputFastaContent(fasContent, filePath)
                    self.input(gb_files, other_files, invalid=invalid_files)
                    if csv_files:
                        self.table4Modification(csv_files[0])
            if event.type() == QEvent.KeyPress:  # 首先得判断type
                modifiers = QApplication.keyboardModifiers()
                if name in ["stackedWidget", "tableView"]:
                    if (modifiers == Qt.ControlModifier) and (
                            event.key() == Qt.Key_V):
                        self.pasteID()
                        return True
                    if name == "tableView":
                        if event.key() == Qt.Key_Delete:
                            self.rmTableRow()
                            return True
                        if (modifiers == Qt.ControlModifier) and (
                                event.key() == Qt.Key_S):
                            self.saveTable()
                            return True
                        if (modifiers == Qt.ControlModifier) and (
                                event.key() == Qt.Key_C):
                            self.copyID()
                            return True
                        if (modifiers == Qt.ControlModifier) and (
                                event.key() == Qt.Key_X):
                            self.cutID()
                            return True
                elif name == "tableView_2":
                    if event.key() == Qt.Key_Delete:
                        self.removeFiles()
                        return True
                    if (modifiers == Qt.ControlModifier) and (
                                event.key() == Qt.Key_S):
                        self.save_other_file()
                        return True
        # 其他情况会返回系统默认的事件处理方法。
        return super(MyMainWindow, self).eventFilter(obj, event)  # 0

    @classmethod
    def onRestart(cls, widget, list_path):
        # 用于重启界面
        widget.close()
        widget.deleteLater()
        del widget
        w = MyMainWindow(list_path)
        w.show()

    def open_tableItemByMenu(self):
        tindex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(tindex)
        list_align, list_docx = self.fetchSelectFile(filePath)
        if list_docx:
            if platform.system().lower() == "windows":
                for file in list_docx:
                    os.startfile(file.replace("/", "\\"))
            elif platform.system().lower() == "darwin":
                for file in list_docx:
                    os.system('open %s'%file)
            elif platform.system().lower() == "linux":
                for file in list_docx:
                    os.system('open %s'%file)
        if list_align:
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "loading...", parent=self)
            self.seqViewer = Seq_viewer(filePath, list_align, self.progressSig, self.progressDialog, self)
            # 添加最大化按钮
            self.seqViewer.setWindowFlags(self.seqViewer.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.seqViewer.setWindowModality(Qt.ApplicationModal)
            self.seqViewer.show()

    def open_tableItem(self, index):
        tindex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(tindex)
        model = self.tableView_2.model()
        list_row = model.arraydata[index.row()]
        file = filePath + os.sep + list_row[0]
        descript = list_row[1]
        if descript == "Word annotation file":
            self.factory.openPath(file, self)
        else:
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "loading...", parent=self)
            self.seqViewer = Seq_viewer(filePath, [file], self.progressSig, self.progressDialog, self)
            # 添加最大化按钮
            self.seqViewer.setWindowFlags(self.seqViewer.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.seqViewer.setWindowModality(Qt.ApplicationModal)
            self.seqViewer.show()

    def exportID(self):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if currentModel and indices:
            rows = list(set([index.row() for index in indices]))
            currentData = currentModel.arraydata
            list_IDs = [currentData[row][0] for row in rows]
            fileName = QFileDialog.getSaveFileName(
                self, "PhyloSuite", "sequences", "GenBank Format(*.gb)")
            gbManager = GbManager(filePath, parent=self)
            def save2gb(gbManager, fileName):
                export_content = gbManager.fetchContentsByIDs(
                    list_IDs)
                with open(fileName[0], "w", encoding="utf-8") as f:
                    f.write(export_content)
            if fileName[0]:
                convertWorker = WorkThread(
                    lambda: save2gb(gbManager, fileName),
                    parent=self)
                convertWorker.start()
                convertWorker.finished.connect(lambda: QMessageBox.information(
                    self,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>File saved successfully!</p>"))

    def exportFASTA(self):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if currentModel and indices:
            rows = list(set([index.row() for index in indices]))
            currentData = currentModel.arraydata
            list_IDs = [currentData[row][0] for row in rows]
            fileName = QFileDialog.getSaveFileName(
                self, "PhyloSuite", "sequences", "Fasta Format(*.fas)")
            gbManager = GbManager(filePath, parent=self)
            def save2fas(gbManager, fileName):
                export_content = gbManager.fetchContentsByIDs(
                    list_IDs)
                SeqIO.convert(StringIO(export_content), "genbank", fileName[0], "fasta")
            if fileName[0]:
                convertWorker = WorkThread(
                    lambda: save2fas(gbManager, fileName),
                    parent=self)
                convertWorker.start()
                convertWorker.finished.connect(lambda: QMessageBox.information(
                    self,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>File saved successfully!</p>"))

    def removeFiles(self):
        tree_index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(tree_index)
        indices = self.tableView_2.selectedIndexes()
        currentModel = self.tableView_2.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in indices), reverse=True)
            for row in rows:
                currentModel.layoutAboutToBeChanged.emit()
                os.remove(filePath + os.sep + currentData.pop(row)[0])
                currentModel.layoutChanged.emit()
        self.display(tree_index)

    def recycled_restore(self, tree_index=None):
        if not tree_index:
            model = self.treeView_3.model()
            recycledPath = os.path.normpath(model.filePath(
                self.treeView_3.currentIndex()))
        else:
            recycledPath = os.path.normpath(self.tree_model.filePath(tree_index))
        # filePath在存的时候已经标准化了
        if recycledPath in self.dict_recycled_name:
            filePath = self.dict_recycled_name.pop(recycledPath)
            if os.path.exists(filePath):
                filePath, self.list_repeat_name_num = self.factory.numbered_Name(
                    self.list_repeat_name_num, filePath)
            shutil.copytree(recycledPath, filePath)
            self.clearFolder(recycledPath)
        else:
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Can't restore this folder</p>")

    def recycled_remove(self):
        model = self.treeView_3.model()
        indices = self.treeView_3.selectedIndexes()
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "<p style='line-height:25px; height:25px'>Once deleted, these data will not be recoverable. Continue?</p>",
            QMessageBox.Yes,
            QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            for j in indices:
                recycledPath = os.path.normpath(model.filePath(j))
                self.clearFolder(recycledPath)
                if recycledPath in self.dict_recycled_name:
                    self.dict_recycled_name.pop(recycledPath)
                if recycledPath in self.list_repeat_name_num:
                    self.list_repeat_name_num.remove(recycledPath)

    def drop2treeView(self, dropPath):
        treeIndex = self.treeView.currentIndex()
        if treeIndex.isValid():
            indices = self.tableView.selectedIndexes()
            currentModel = self.tableView.model()
            if indices:
                currentData = currentModel.arraydata
                rows = sorted(set(index.row() for index in indices))
                list_IDs = [currentData[row][0] for row in rows]
                filePath = self.tree_model.filePath(treeIndex)
                gbManager = GbManager(filePath, parent=self)
                rawContent = gbManager.fetchContentsByIDs(
                    list_IDs)
                self.dropInput(dropPath, rawContent)

    def dropInput(self, filePath, newContent):
        # 新拖进来的内存存在了new文件里面
        # 进度条
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "importing...", parent=self)
        if self.isValideName(filePath, mode="gb"):
            treeIndex = self.treeView.model().index(filePath)
            self.progressDialog.show()
            gbManager = GbManager(filePath, parent=self)
            gbWorker = WorkThread(lambda: gbManager.addRecords(newContent, 0, 100, self.progressSig, self, byContent=True),
                                  parent=self)
            gbWorker.start()
            gbWorker.finished.connect(lambda: [self.progressDialog.close(), self.display(treeIndex)])
        else:
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>The selected folder can not display GenBank file!</p>")

    def setTreeViewFocus(self, path):
        if self.isResultsSubFolder(path):
            index = self.tree_model.index(os.path.dirname(path))
            if index == self.treeView.currentIndex():
                self.display(index)
            self.treeView.setCurrentIndex(index)
            index_sub = self.tree_model4.index(path)
            self.treeView_4.setCurrentIndex(index_sub)
            self.expandTreeView4(index_sub)
        else:
            index = self.tree_model.index(path)
            if index == self.treeView.currentIndex():
                self.display(index)
            self.treeView.setCurrentIndex(index)

    def normalization(self, version, dict_NML_settings):
        treeIndex = self.treeView.currentIndex()
        if not treeIndex.isValid():
            return
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        currentData = currentModel.arraydata
        rows = sorted(set(index.row() for index in indices))
        list_IDs = [currentData[row][0] for row in rows]
        filePath = self.tree_model.filePath(treeIndex)
        # 进度条
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "validating...", parent=self)
        # 其他序列标准化，只需要替换名字
        dict_NML_settings["outpath"] = filePath
        dict_NML_settings["totalID"] = len(list_IDs)
        dict_NML_settings["list_IDs"] = list_IDs
        dict_NML_settings["progressSig"] = self.progressSig
        dict_NML_settings["parent"] = self
        dict_NML_settings["exception_signal"] = self.exception_signal
        if version == "Mitogenome":
            gbManager = GbManager(filePath, parent=self)
            self.progressDialog.show()
            gbWorker = WorkThread(lambda: self.factory.normalizeMT_child(gbManager, dict_NML_settings),
                                  parent=self)
            gbWorker.start()
            gbWorker.finished.connect(lambda : [self.progressDialog.close(),
                                               self.display(treeIndex), self.factory.normalizeMT_main(self.nmlgb)])
        else:
            self.progressDialog.show()
            gbManager = GbManager(filePath, parent=self)
            dict_NML_settings["gbManager"] = gbManager
            gbWorker = WorkThread(lambda: GBnormalize(**dict_NML_settings),
                                  parent=self)
            gbWorker.start()
            gbWorker.finished.connect(lambda: [self.progressDialog.close(), self.display(treeIndex)])
            # num = 0
            # total = len(dict_replace)
            # for i in dict_replace:
            #     validate_content = validate_content.replace(
            #         '/product="%s"' % i, '/product="%s"' % dict_replace[i])
            #     validate_content = validate_content.replace(
            #         '/gene="%s"' % i, '/gene="%s"' % dict_replace[i])
            #     validate_content = re.sub(r"(/State=\".+)unverified", r'\1verified', validate_content)
            #     num += 1
            #     self.progressSig.emit(num * 50 / total)
            # gbManager.updateNewRecords(50, 50, self.progressSig, byContent=validate_content)
            # self.progressDialog.close()
            # self.display(treeIndex)

    def refresh_workflow_results(self, path):
        self.stackedWidget.setCurrentIndex(7)
        self.workflow_results_settings = QSettings(self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
        self.workflow_results_settings.setFallbacksEnabled(False)
        self.workflow_results_settings.beginGroup("Flowchart results")
        self.workflow_results_settings.beginGroup(os.path.normpath(path))
        flowchart_names = self.workflow_results_settings.allKeys()
        if not flowchart_names:
            self.textEdit_flowchart.clear()

            self.listWidget.clear()
            return
        list_name_time = [[name, self.workflow_results_settings.value(name)["time"]] for name in flowchart_names
                          if "time" in self.workflow_results_settings.value(name)]
        # print(sorted(list_name_time, key=lambda x: x[1]))
        recentReportName = sorted(list_name_time, key=lambda x: x[1], reverse=True)[0][0]
        # 给combobox添加
        model = self.comboBox.model()
        self.comboBox.clear()
        for num, i in enumerate(flowchart_names):
            item = QStandardItem(i)
            item.setToolTip(i)
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            model.appendRow(item)
        self.display_workflow_report(self.workflow_results_settings.value(recentReportName), name=recentReportName)

    def display_workflow_report(self, dict_reports, name=None):
        if name:
            self.comboBox.setCurrentText(name)
        if dict_reports:
            self.listWidget.clear()
            ###设置textedit
            if "reports" in dict_reports:
                reports = dict_reports["reports"]
                self.textEdit_flowchart.clear()
                self.textEdit_flowchart.setHtml(reports)
            ###设置listwidget
            for i in dict_reports:
                if i in ["reports", "time"]:
                    continue
                analysisButton = QListWidgetItem(self.listWidget)
                analysisButton.setIcon(QIcon(':/picture/resourses/folder.png'))
                analysisButton.setText(i)
                analysisButton.setTextAlignment(Qt.AlignHCenter)
                analysisButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                if not os.path.exists(dict_reports[i]):
                    analysisButton.setFlags(Qt.NoItemFlags)
                    # analysisButton.
            try:
                self.listWidget.itemDoubleClicked.disconnect() #先清空连接
            except:
                pass
            self.listWidget.itemDoubleClicked.connect(lambda item_widget:
                                                      self.factory.openPath(dict_reports[item_widget.text()], self))

    def switchWorkflowResults(self, name):
        # treeIndex = self.treeView.currentIndex()
        # filePath = self.tree_model.filePath(treeIndex)
        # qsettings = QSettings(self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
        # qsettings.setFallbacksEnabled(False)
        # qsettings.beginGroup("Flowchart results")
        # qsettings.beginGroup(os.path.normpath(filePath))
        dict_reports = self.workflow_results_settings.value(name)
        self.display_workflow_report(dict_reports)

    @pyqtSlot()
    def on_toolButton_wrap_clicked(self):
        button = self.sender()
        if button.isChecked():
            button.setChecked(True)
            self.textEdit_flowchart.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            button.setChecked(False)
            self.textEdit_flowchart.setLineWrapMode(QTextEdit.NoWrap)

    @pyqtSlot()
    def on_toolButton_save_clicked(self):
        content = self.textEdit_flowchart.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "PhyloSuite", "flowchart_summary", "text Format(*.txt)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    @pyqtSlot()
    def on_toolButton_del_clicked(self):
        currentResults = self.comboBox.currentText()
        reply = QMessageBox.question(
            self,
            "Flowchart",
            "<p style='line-height:25px; height:25px'>You decided to remove the workflow results of \"%s\"?</p>" % currentResults,
            QMessageBox.Yes,
            QMessageBox.No)
        if reply == QMessageBox.No:
            return
        treeIndex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(treeIndex)
        # qsettings = QSettings(self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
        # qsettings.setFallbacksEnabled(False)
        # qsettings.beginGroup("Flowchart results")
        # qsettings.beginGroup(os.path.normpath(filePath))
        # qsettings.endGroup()
        # qsettings.endGroup()
        self.deleteFlowchartResults(filePath, currentResults)
        # self.workflow_results_settings.remove(currentResults)
        self.comboBox.removeItem(self.comboBox.currentIndex())
        self.display(treeIndex)

    def isRootFolder(self, path, mode=None):
        path = path.rstrip(os.sep) ##可能会出错
        if mode == "gb":
            if os.path.basename(path) == "GenBank_File":
                return os.path.basename(path)
        elif mode == "other":
            if os.path.basename(path) == "Other_File":
                return os.path.basename(path)
        else:
            if os.path.basename(path) in ["Other_File", "GenBank_File"]:
                return os.path.basename(path)  #返回具体名字
        return False

    def isWorkFolder(self, path, mode=None):
        path = path.rstrip(os.sep)
        if os.path.basename(path) == "recycled":
            return False
        if mode == "gb":
            if os.path.basename(os.path.dirname(path)) == "GenBank_File":
                return os.path.basename(os.path.dirname(path))
        elif mode == "other":
            if os.path.basename(os.path.dirname(path)) == "Other_File":
                return os.path.basename(os.path.dirname(path))
        else:
            if os.path.basename(os.path.dirname(path)) in ["Other_File", "GenBank_File"]:
                return os.path.basename(os.path.dirname(path))  #返回具体名字
        return False

    def isResultsFolder(self, path, mode=None):
        path = path.rstrip(os.sep)
        if mode == "gb":
            if os.path.basename(os.path.dirname(os.path.dirname(path))) == "GenBank_File":
                return os.path.basename(os.path.dirname(os.path.dirname(path)))
        elif mode == "other":
            if os.path.basename(os.path.dirname(os.path.dirname(path))) == "Other_File":
                return os.path.basename(os.path.dirname(os.path.dirname(path)))
        else:
            if os.path.basename(os.path.dirname(os.path.dirname(path))) in ["Other_File", "GenBank_File"]:
                return os.path.basename(os.path.dirname(os.path.dirname(path)))
        return False

    def isResultsSubFolder(self, path, mode=None):
        path = path.rstrip(os.sep)
        if mode == "gb":
            if os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path)))) == "GenBank_File":
                return os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))
        elif mode == "other":
            if os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path)))) == "Other_File":
                return os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))
        else:
            if os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path)))) in ["Other_File", "GenBank_File"]:
                return os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(path))))
        return False

    def isRecycledFolder(self, path):
        if os.path.basename(os.path.dirname(path)) == "recycled":
            return True
        return False

    def isWorkPlaceFolder(self, path):
        if ("GenBank_File" in path) or ("Other_File" in path):
            return True
        return False

    def expandCurrent(self, index):
        if not self.isWorkFolder(self.tree_model.filePath(index)):
            return
        self.treeView.expand(index)
        rowCount = self.tree_model.rowCount(index.parent())
        list_index = [self.tree_model.index(row, 0, index.parent()) for row in range(rowCount)]
        for index1 in list_index:
            if index1 == index:
                continue
            if self.treeView.isExpanded(index1):
                self.treeView.setExpanded(index1, False)

    def expandTreeView4(self, index):
        if not self.isResultsSubFolder(self.tree_model.filePath(index)):
            return
        self.treeView_4.expand(index)
        rowCount = self.tree_model4.rowCount(index.parent())
        list_index = [self.tree_model4.index(row, 0, index.parent()) for row in range(rowCount)]
        for index1 in list_index:
            if index1 == index:
                continue
            if self.treeView_4.isExpanded(index1):
                self.treeView_4.setExpanded(index1, False)

    def popFunction(self, item):
        if item.text() == "Import file(s) or ID(s)":
            self.on_Add_Files_triggered()
        elif item.text() == "Standardize GenBank file":
            self.on_Normalization_triggered()
        elif item.text() == "Extract GenBank file":
            self.on_Extract_triggered()
        elif item.text() == "Search in NCBI":
            self.on_SerhNCBI_triggered()
        elif item.text() == "MAFFT":
            self.on_Mafft_triggered()
        elif item.text() == "MACSE (for CDS)":
            self.on_MACSE_triggered()
        elif item.text() == "trimAl":
            self.on_actiontrimAl_triggered()
        elif item.text() == "HmmCleaner":
            self.on_actionHmmCleaner_triggered()
        elif item.text() == "Gblocks":
            self.on_actionGblocks_triggered()
        elif item.text() == "Concatenate Sequence":
            self.on_Concatenate_triggered()
        elif item.text() == "Convert Sequence Format":
            self.on_ConvertFMT_triggered()
        elif item.text() == "PartitionFinder2":
            self.on_actionPartitionFinder_triggered()
        elif item.text() == "ModelFinder":
            self.on_actionModelFinder_triggered()
        elif item.text() == "IQ-TREE":
            self.on_actionIQTREE_triggered()
        elif item.text() == "FastTree":
            self.on_actionFastTree_triggered()
        elif item.text() == "MrBayes":
            self.on_actionMrBayes_triggered()
        elif item.text() == "ASTRAL":
            self.on_actionASTRAL_triggered()
        elif item.text() == "Tiger":
            self.on_Tiger_triggered()
        elif item.text() == "Tree annotation":
            self.on_TreeAnnotation_triggered()
        elif item.text() == "TreeSuite":
            self.on_TreeSuite_triggered()
        elif item.text() == "Parse Annotation":
            self.on_ParseANNT_triggered()
        elif item.text() == "Compare Table":
            self.on_Compare_table_triggered()
        elif item.text() == "Draw RSCU figure":
            self.on_actionRSCUfig_triggered()
        # elif item.text() == "Plot":
        #     self.on_actionPlot_triggered()
        elif item.text() == "Draw gene order":
            self.on_actionDrawGO_triggered()
        elif item.text() == "GenBank File Information Display":
            self.on_actionDisplay_triggered()
        elif item.text() == "Settings":
            self.on_settings_triggered()
        elif item.text() == "Sequence Viewer":
            self.on_seqViewer_triggered()
        elif item.text() == "GenBank File Extracting":
            self.on_GBextSetting_triggered()
        elif item.text() == "Color sets":
            self.on_colorsets_triggered()
        elif item.text() == "Check for Updates":
            self.on_UpdateApp_triggered()
        elif item.text() == "Update manually":
            self.on_manualUpdate_triggered()
        elif item.text() == "About":
            self.on_About_triggered()
        elif item.text() == "Documentation":
            country = self.factory.path_settings.value("country", "UK")
            url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/" if \
                country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/"
            QDesktopServices.openUrl(QUrl(url))
        elif item.text() == "Operation":
            country = self.factory.path_settings.value("country", "UK")
            url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#4-1-1-Brief-example" if \
                country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#4-1-1-Brief-example"
            QDesktopServices.openUrl(QUrl(url))
        elif item.text() == "Examples":
            country = self.factory.path_settings.value("country", "UK")
            url = "http://phylosuite.jushengwu.com/example.zip" if \
                country == "China" else "https://raw.githubusercontent.com/dongzhang0725/PhyloSuite/master/example.zip"
            QDesktopServices.openUrl(QUrl(url))

    def highlight_identical_sequences(self):
        if self.highlight_identical_btn.toolTip() == "Clean Identical Sequences":
            self.clearSeq()
            self.highlight_identical_btn.setToolTip("Highlight Identical Sequences")
            icon1 = QIcon(QPixmap(":/picture/resourses/if_Vector-icons_44_1041648.png"))
            self.highlight_identical_btn.setIcon(icon1)
        else:
            treeIndex = self.treeView.currentIndex()
            filePath = self.tree_model.filePath(treeIndex)
            gbManager = GbManager(filePath, parent=self)
            highlightRepeat, self.list_repeat_index = gbManager.highlightRepeatIDs()
            if highlightRepeat:
                array = gbManager.fetch_array()
                # validatedIDs = gbManager.fetchVerifiedIDs()
                reverse_array = [array[0]] + sorted(array[1:], reverse=True)  # 反转一下
                self.displayTableModel = MyTableModel(
                    reverse_array, highlightRepeat=highlightRepeat, parent=self)
                self.tableView.setModel(self.displayTableModel)
                self.displayTableModel.modifiedSig.connect(
                    self.depositeData)
                # self.displayTableModel.layoutChanged.connect(
                #     self.depositeData)
                self.highlight_identical_btn.setToolTip("Clean Identical Sequences")
                icon1 = QIcon(QPixmap(":/picture/resourses/ic_cleaning_clean.png"))
                self.highlight_identical_btn.setIcon(icon1)
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setText("<p style='line-height:25px; height:25px'>Identical sequences are marked with identical color!"
                            " Click <span style='font-weight:600; color:purple;'>clean button</span> to delete identical sequences</p>")
                msg.setWindowTitle("PhyloSuite")
                msg.setDetailedText("\n".join([", ".join(i) for i in self.list_repeat_index]))
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
                # QMessageBox.information(
                #     self,
                #     "PhyloSuite",
                #     "<p style='line-height:25px; height:25px'>Identical sequences are marked with identical color!"
                #     " Click <span style='font-weight:600; color:purple;'>clean button</span> to delete identical sequences</p>")
            else:
                QMessageBox.information(
                    self,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>No identical sequences Found!</p>")

    def clearSeq(self):
        removeIDs = []
        for i in self.list_repeat_index:
            # [[MF187612, KR013001], [GU130256, KX289584]]
            NC_IDs = []
            restIDs = []
            for j in i:
                if "NC_" in j:
                    NC_IDs.append(j)
                else:
                    restIDs.append(j)
            if NC_IDs:
                NC_IDs.pop(0) #保留一个ID
                removeIDs.extend(NC_IDs)
                removeIDs.extend(restIDs)
            else:
                restIDs.pop(0)
                removeIDs.extend(restIDs)
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        # 进度条
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "removing...", parent=self)
        self.progressDialog.show()
        gbManager = GbManager(filePath, parent=self)
        gbManager.deleteRecords(removeIDs, 0, 100, self.progressSig)
        self.tableView.clearSelection()
        self.progressDialog.close()
        self.display(index)

    def inputIDS_UI(self):
        dialog = QDialog(self)
        dialog.resize(400, 300)
        dialog.setWindowTitle("Find IDs")
        gridLayout = QGridLayout(dialog)
        dialog.label = QLabel(dialog)
        dialog.label.setText("IDs:")
        pushButton = QPushButton("Ok", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_ok.png"))
        pushButton.setIcon(icon)
        pushButton_2 = QPushButton("Close", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/if_Delete_1493279.png"))
        pushButton_2.setIcon(icon)
        dialog.pushButton_3 = QPushButton("Previous", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/previous.png"))
        dialog.pushButton_3.setIcon(icon)
        dialog.pushButton_3.setEnabled(False)
        dialog.pushButton_4 = QPushButton("Next", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/next.png"))
        dialog.pushButton_4.setIcon(icon)
        dialog.pushButton_4.setEnabled(False)
        self.textEdit_IDs = QTextEdit(dialog)
        self.textEdit_IDs.setToolTip("""For example: 
NC_026309.1
NC_033360.1
NC_023104.1
NC_025564.1
NC_017760.1
NC_034937.1
""")
        gridLayout.addWidget(dialog.label, 0, 0, 1, 2)
        gridLayout.addWidget(self.textEdit_IDs, 1, 0, 1, 2)
        gridLayout.addWidget(pushButton, 2, 0, 1, 1)
        gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
        gridLayout.addWidget(dialog.pushButton_3, 3, 0, 1, 1)
        gridLayout.addWidget(dialog.pushButton_4, 3, 1, 1, 1)
        pushButton.clicked.connect(lambda : self.highlight_ids(dialog))
        pushButton_2.clicked.connect(dialog.close)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        dialog.show()

    def highlight_ids(self, dialog):
        list_IDs = re.split(r"\s|,", self.textEdit_IDs.toPlainText())
        while "" in list_IDs:
            list_IDs.remove("")
        if not list_IDs:
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>No IDs detected!</p>")
            return
        treeIndex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(treeIndex)
        gbManager = GbManager(filePath, parent=self)
        array = gbManager.fetch_array()
        # validatedIDs = gbManager.fetchVerifiedIDs()
        reverse_array = [array[0]] + sorted(array[1:], reverse=True)  # 反转一下
        self.displayTableModel = MyTableModel(
            reverse_array, parent=self, highlightIDs=list_IDs)
        self.tableView.setModel(self.displayTableModel)
        ##滚动条
        arrayMAN = ArrayManager(reverse_array)
        self.found_rows = arrayMAN.get_index_by_IDs(list_IDs)
        self.current_find_IDs = 0
        # # 选中全部行
        indexes = [self.displayTableModel.index(row, 0) for row in self.found_rows]
        selectModel = self.tableView.selectionModel()
        selectModel.selectionChanged.connect(lambda:
                                             self.statusBar().showMessage(str(len(set([i.row() for i in
                                                                                       self.tableView.selectedIndexes()]))) + " sequence(s) selected"))
        self.switchFindIDs()
        selection = QItemSelection()
        for model_index in indexes:
            # Select single row.
            selection.select(model_index, model_index)  # top left, bottom right identical
        mode = QItemSelectionModel.Select | QItemSelectionModel.Rows
        # Apply the selection, using the row-wise mode.
        selectModel.select(selection, mode)
        if len(self.found_rows) > 1:
            dialog.label.setVisible(False)
            self.textEdit_IDs.setVisible(False)
            dialog.resize(300, 100)
            dialog.setMaximumHeight(100)
            dialog.setMinimumHeight(100)
            dialog.pushButton_3.setEnabled(True)
            dialog.pushButton_4.setEnabled(True)
            dialog.pushButton_3.clicked.connect(lambda : self.switchFindIDs(mode="-1"))
            dialog.pushButton_4.clicked.connect(lambda: self.switchFindIDs(mode="+1"))
        self.displayTableModel.modifiedSig.connect(
            self.depositeData)
        # self.displayTableModel.layoutChanged.connect(
        #     self.depositeData)

    def switchFindIDs(self, mode="0"):
        if mode == "+1":
            self.current_find_IDs += 1
        elif mode == "-1":
            self.current_find_IDs -= 1
        if abs(self.current_find_IDs) >= len(self.found_rows):
            self.current_find_IDs = 0
        if self.found_rows:
            self.tableView.clearSelection()
            self.tableView.setCurrentIndex(self.displayTableModel.index(self.found_rows[self.current_find_IDs], 0))
            self.tableView.scrollTo(self.displayTableModel.index(self.found_rows[self.current_find_IDs], 0),
                                    QAbstractItemView.PositionAtCenter)  # 显示在中间
        else:
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>Can't find the queried ID!</p>")

    def select_ids(self, list_IDs):
        if not list_IDs:
            return
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "Selecting sequences...", parent=self, busy=True)
        self.progressDialog.show()
        treeIndex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(treeIndex)
        gbManager = GbManager(filePath, parent=self)
        array = gbManager.fetch_array()
        # validatedIDs = gbManager.fetchVerifiedIDs()
        reverse_array = [array[0]] + sorted(array[1:], reverse=True)  # 反转一下
        self.displayTableModel = MyTableModel(
            reverse_array, parent=self, highlightIDs=list_IDs)
        self.tableView.setModel(self.displayTableModel)
        # ##滚动条
        arrayMAN = ArrayManager(reverse_array)
        self.found_rows = arrayMAN.get_index_by_IDs(list_IDs)
        # self.current_find_IDs = 0
        # # 选中全部行
        indexes = [self.displayTableModel.index(row, 0) for row in self.found_rows]
        selectModel = self.tableView.selectionModel()
        selectModel.selectionChanged.connect(lambda:
                                             self.statusBar().showMessage(str(len(set([i.row() for i in
                                                                                       self.tableView.selectedIndexes()]))) + " sequence(s) selected"))
        selection = QItemSelection()
        for model_index in indexes:
            # Select single row.
            selection.select(model_index, model_index)  # top left, bottom right identical
        mode = QItemSelectionModel.Select | QItemSelectionModel.Rows
        # Apply the selection, using the row-wise mode.
        selectModel.select(selection, mode)
        self.displayTableModel.modifiedSig.connect(
            self.depositeData)
        self.progressDialog.close()

    def fetchWorkPath(self, mode="gb"):
        treeIndex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(treeIndex)
        if self.isWorkFolder(filePath, mode):
            workPath = filePath
        elif self.isResultsFolder(filePath, mode):
            workPath = self.tree_model.filePath(treeIndex.parent())
        else:
            workPath = self.treeRootPath + os.sep + "GenBank_File/files" \
                if (mode=="gb" or mode=="all") else self.treeRootPath + os.sep + "Other_File/files"
        return filePath, workPath

    def fetchResultsPath(self):
        if hasattr(self, "treeView_4") and hasattr(self, "tree_model4"):
            treeIndex = self.treeView_4.currentIndex()
            if treeIndex:
                resultsPath = os.path.normpath(self.tree_model4.filePath(treeIndex))
                rootpath = os.path.normpath(self.tree_model4.rootPath())
                if resultsPath.startswith(rootpath):
                    while os.path.dirname(resultsPath) != rootpath:
                        # 得到最接近根的那个结果路径
                        resultsPath = os.path.dirname(resultsPath)
                return resultsPath
        return

    def fetchSelectFile(self, filePath):
        model = self.tableView_2.model()
        indices = self.tableView_2.selectedIndexes()
        list_docx = []
        list_align = []
        rows = list(set([index.row() for index in indices]))
        for row in rows:
            list_row = model.arraydata[row]
            file = os.path.normpath(filePath + os.sep + list_row[0])
            descript = list_row[1]
            if descript == "Word annotation file":
                list_docx.append(file)
            else:
                list_align.append(file)
        return list_align, list_docx

    def list_all_folders(self, path):
        fs = os.listdir(path)
        for f1 in fs:
            tmp_path = os.path.join(path, f1)
            if os.path.isdir(tmp_path):
                if self.isRootFolder(tmp_path):
                    self.list_rootFolders.append(tmp_path)
                elif self.isWorkFolder(tmp_path):
                    self.list_workFolers.append(tmp_path)
                elif self.isResultsFolder(tmp_path):
                    self.list_resultFolders.append(tmp_path)
                self.list_all_folders(tmp_path)

    def addToolBtn2Tree(self, byFolder=False):
        if not os.path.exists(byFolder):
            #删除文件夹的时候避免报错
            return
        if byFolder:
            ##比如增加了一个文件夹
            # newestFolder = max([os.path.join(byFolder, i) for i in os.listdir(byFolder)], key=os.path.getmtime) #只改最新的文件夹
            list_folder = [os.path.join(byFolder, i) for i in os.listdir(byFolder)]
            for each_folder in list_folder:
                index = self.tree_model.index(each_folder)
                indexWDG = self.treeView.indexWidget(index)
                if indexWDG:
                    continue  #只添加没有按钮的
                # print("newFolder: %s"%each_folder)
                index_widget = CustomTreeIndexWidget(os.path.basename(each_folder), index=index,
                                                     hoverMode=True, parent=self.treeView)
                if self.isRootFolder(each_folder):
                    index_widget.addBtn("Add Work Folder", QIcon(":/picture/resourses/add-icon.png"),
                                        triggerSig=self.creatFolderSig)
                elif self.isRecycledFolder(each_folder):
                    index_widget.addBtn("Restore", QIcon(":/picture/resourses/Custom-Icon-Design-Flatastic-9-Undo.ico"),
                                        triggerSig=self.restoreFolderSig)
                # elif os.path.basename(each_folder) not in ["files", "flowchart", "recycled", ".data"]:
                #     index_widget.addBtn("Delete", QIcon(":/picture/resourses/if_Delete_1493279.png"),
                #                         triggerSig=self.folderDeleteSig)
                index_widget.addBtn("Open In Windows Explorer", QIcon(":/picture/resourses/if_file-explorer_60174.png"),
                                    triggerSig=self.folderOpenSig)
                # GenBank的增加一个设置gb display的功能
                if os.path.basename(each_folder) != "recycled" and self.isWorkFolder(each_folder, mode="gb"):
                    index_widget.addBtn("GenBank File Information Display Setting",
                                        QIcon(":/picture/resourses/cog.png"),
                                        triggerSig=self.openDisplaySetSig)
                self.treeView.setIndexWidget(index, index_widget)
            return
        ###给tree加按钮
        self.list_rootFolders = []
        self.list_workFolers = []
        self.list_resultFolders = []
        try:
            #有时候怕报不存在路径的错误
            self.list_all_folders(self.treeRootPath)
        except:
            pass
        for rootFolder in self.list_rootFolders:
            index = self.tree_model.index(rootFolder)
            index_widget = CustomTreeIndexWidget(os.path.basename(rootFolder), index=index,
                                                 hoverMode=True, parent=self.treeView)
            index_widget.addBtn("Add Work Folder", QIcon(":/picture/resourses/add-icon.png"),
                                 triggerSig=self.creatFolderSig)
            index_widget.addBtn("Open In Windows Explorer", QIcon(":/picture/resourses/if_file-explorer_60174.png"),
                                triggerSig=self.folderOpenSig)
            self.treeView.setIndexWidget(index, index_widget)
        for folder in self.list_workFolers:
            index = self.tree_model.index(folder)
            index_widget = CustomTreeIndexWidget(os.path.basename(folder), index=index,
                                                 hoverMode=True, parent=self.treeView)
            # if os.path.basename(folder) not in ["files", "flowchart", "recycled"]:
            #     index_widget.addBtn("Delete", QIcon(":/picture/resourses/if_Delete_1493279.png"),
            #                         triggerSig=self.folderDeleteSig)
            index_widget.addBtn("Open In Windows Explorer", QIcon(":/picture/resourses/if_file-explorer_60174.png"),
                                triggerSig=self.folderOpenSig)
            # GenBank的增加一个设置gb display的功能
            if os.path.basename(folder) != "recycled" and self.isWorkFolder(folder, mode="gb"):
                index_widget.addBtn("GenBank File Information Display Setting", QIcon(":/picture/resourses/cog.png"),
                                    triggerSig=self.openDisplaySetSig)
            self.treeView.setIndexWidget(index, index_widget)
        for folder in self.list_resultFolders:
            index = self.tree_model.index(folder)
            index_widget = CustomTreeIndexWidget(os.path.basename(folder), index=index,
                                                 hoverMode=True, parent=self.treeView)
            if self.isRecycledFolder(folder):
                index_widget.addBtn("Restore", QIcon(":/picture/resourses/Custom-Icon-Design-Flatastic-9-Undo.ico"),
                                    triggerSig=self.restoreFolderSig)
            # else:
            #     if os.path.basename(folder) != ".data":
            #         index_widget.addBtn("Delete", QIcon(":/picture/resourses/if_Delete_1493279.png"),
            #                             triggerSig=self.folderDeleteSig)
            index_widget.addBtn("Open In Windows Explorer", QIcon(":/picture/resourses/if_file-explorer_60174.png"),
                                triggerSig=self.folderOpenSig)
            self.treeView.setIndexWidget(index, index_widget)

    def save_other_file(self):
        tindex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(tindex)
        model = self.tableView_2.model()
        indices = self.tableView_2.selectedIndexes()
        rows = list(set([index.row() for index in indices]))
        first_row = model.arraydata[rows[0]]
        file = os.path.normpath(filePath + os.sep + first_row[0])
        saveFileName = QFileDialog.getSaveFileName(
            self, "Save File", first_row[0])
        if saveFileName[0]:
            shutil.copy(file, saveFileName[0])
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>File saved successfully!</p>")

    def removeOldApp(self):
        ##删除更新留下的旧文件
        self.factory.remove_old_files(self.thisPath)
        ##导入新的设置的旧文件
        self.factory.remove_old_files(self.thisPath + os.sep + "settings")
        self.factory.remove_old_files(self.thisPath + os.sep + "plugins")
        # for path in glob.glob(self.thisPath + os.sep + "*.old"):
        #     try:
        #         if os.path.isfile(path):
        #             os.remove(path)
        #         elif os.path.isdir(path):
        #             shutil.rmtree(path, True)
        #     except:
        #         pass

    def UpdatesSlot(self, current_version, new_version, description):
        if hasattr(self, "wait_state"):
            self.wait_state.close()
            self.wait_state.deleteLater()
            del self.wait_state
            mode = "check"
        else:
            mode = "remind"
        if not current_version:
            ##网络有问题的时候，就不执行
            return
        if new_version != current_version: #(glob.glob(self.thisPath + os.sep + "*.exe")) and (
            description = description + '<span style="font-size: 13px; font-weight:bold; font-style: italic; color:red;">' \
                                        'Please close your antivirus software before updating!!!</span><br>'
            popupUI = UpdatePopupGui(new_version, description, self)
            if os.path.exists(self.thisPath + os.sep + "base_library.zip"):
                # 证明是打包好的
                if mode == "check":
                    popupUI.checkBox.setVisible(False)
                if popupUI and popupUI.exec_() == QDialog.Accepted:
                    self.updateAPP()
            else:
                popupUI.label.setText("New version <span style='font-weight:600; color:#ff0000;'>%s</span> found. "
                                      "<br>To update, please click the '<span style='font-weight:600; color:#ff0000;'>Update now</span>' "
                                      "button below<br> or use '<span style='font-weight:600; color:#ff0000;'>"
                                      "pip install --upgrade PhyloSuite</span>' if you use the Python version"
                                      "."%new_version)
                popupUI.exec_()
        else:
            if mode == "check":
                QMessageBox.information(
                    self,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>No updates found!</p>")

    def updateAPP(self):
        percentProgress = ProgressDialog("Update", "Downloading...", parent=self)
        percentProgress.show()
        updateApp = UpdateAPP(self)
        def setProgress(value):
            oldValue = percentProgress.value()
            done_int = int(value)
            # if done_int == 0:
            #     self.progressDialog.close()
            if done_int > oldValue:
                percentProgress.setValue(done_int)
                QCoreApplication.processEvents()
                if done_int == 100:
                    percentProgress.close()
        updateApp.progressSig.connect(setProgress)
        updateApp.downloadNewAPP()

    def updateTable(self, removedTaxmy):
        # if hasattr(self.setting, "haveNewTaxmy") and self.setting.haveNewTaxmy:
        reply = QMessageBox.question(
            self,
            "Confirmation!",
            "<p style='line-height:25px; height:25px'>Do you wish to update the taxonomic nomenclature? "
            "If you choose \"Yes\", the exsisting taxonomic nomenclature will be replaced</p>",
            QMessageBox.Yes,
            QMessageBox.No)
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "refreshing...", parent=self)
        self.progressDialog.show()
        if reply == QMessageBox.No:
            self.updateLineageWorker = WorkThread(lambda : self.updateLineageSlot(), parent=self)
            self.updateLineageWorker.start()
            self.updateLineageWorker.finished.connect(lambda : [self.progressDialog.close(),
                                                              self.modify_lineage_finished.emit()])
            return
        self.updateTableWorker = WorkThread(lambda : self.updateTableSlot(removedTaxmy), parent=self)
        self.updateTableWorker.start()
        self.updateTableWorker.finished.connect(lambda : [self.progressDialog.close(),
                                                          self.display(self.treeView.currentIndex()),
                                                          self.modify_lineage_finished.emit()])

    def updateTableSlot(self, removedTaxmy):
        gbPath = self.treeRootPath + os.sep + "GenBank_File"
        gbWorkPaths = [gbPath + os.sep + i for i in os.listdir(gbPath) if self.isWorkFolder(gbPath + os.sep + i, mode="gb")]
        each_proportion = 100 / len(gbWorkPaths)
        for num, path in enumerate(gbWorkPaths):
            gbIO = GbManager(path, exceptSig=self.exception_signal)
            gbIO.updateRecords(num * each_proportion, each_proportion, self.progressSig,
                               removedTaxmy=removedTaxmy, reidentLineage=True)

    def updateLineageSlot(self):
        # 更新lineage
        gbPath = self.treeRootPath + os.sep + "GenBank_File"
        gbWorkPaths = [gbPath + os.sep + i for i in os.listdir(gbPath) if self.isWorkFolder(gbPath + os.sep + i, mode="gb")]
        each_proportion = 100 / len(gbWorkPaths)
        for num, path in enumerate(gbWorkPaths):
            gbIO = GbManager(path, exceptSig=self.exception_signal)
            gbIO.updateLineageOfAllWorDir()
            self.progressSig.emit(num*each_proportion)

    def refreshTable(self):
        # 只刷新单个
        reply = QMessageBox.question(
            self,
            "Confirmation!",
            "<p style='line-height:25px; height:25px'>Do you wish to update the taxonomic nomenclature? "
            "If you choose \"Yes\", the exsisting taxonomic nomenclature will be replaced</p>",
            QMessageBox.Yes,
            QMessageBox.No)
        reidentLineage = True if reply == QMessageBox.Yes else False
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "refreshing...", parent=self)
        self.progressDialog.show()
        self.refreshTableWorker = WorkThread(lambda : self.refreshTableSlot(reidentLineage), parent=self)
        self.refreshTableWorker.start()
        self.refreshTableWorker.finished.connect(lambda : [self.progressDialog.close(), self.display(self.treeView.currentIndex())])

    def refreshTableSlot(self, reidentLineage):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        gbIO = GbManager(filePath, exceptSig=self.exception_signal)
        gbIO.updateRecords(0, 100, self.progressSig, reidentLineage=reidentLineage)

    def updateTaxonomyDB(self):
        # self.progressDialog = self.factory.myProgressDialog(
        #     "Please Wait", "Updating...", parent=self, busy=True)
        # self.progressDialog.show()
        # self.updateTaxWorker = WorkThread(lambda : NCBITaxa().update_taxonomy_database(), parent=self)
        # self.updateTaxWorker.start()
        # self.updateTaxWorker.finished.connect(
        #     lambda : [self.progressDialog.close()])
        self.factory.update_NCBI_tax_database(self)

    def updateTaxonomy(self, database="NCBI"):
        database_name = "NCBI's 'Taxonomy' database" if database=="NCBI" else "WoRMS website"
        reply = QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>This will replace the existing taxonomic nomenclature"
                    " with the one from the %s. Continue?</p>"%database_name,
                    QMessageBox.Ok,
                    QMessageBox.Cancel
                )
        if reply == QMessageBox.Ok:
            if database == "NCBI":
                state = self.factory.judge_NCBI_tax_database(parent=self)
                if not state:
                    return
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "Retrieving...", parent=self)
            self.progressDialog.show()
            self.updateTaxWorker = WorkThread(lambda : self.updateTaxonomy_slot(database), parent=self)
            self.updateTaxWorker.start()
            self.updateTaxWorker.finished.connect(
                lambda : [self.progressDialog.close(), self.display(self.treeView.currentIndex()), self.tableView.update()])

    def updateTaxonomy_slot(self, database="NCBI"):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        currentData = currentModel.arraydata
        rows = sorted(set(index.row() for index in
                          indices), reverse=True)
        list_IDs = [currentData[row][0] for row in rows]
        # header = currentModel.headerdata
        # organism_index = header.index("Organism")
        # list_organisms = [currentData[row][organism_index] for row in rows]
        gbIO = GbManager(filePath, exceptSig=self.exception_signal)
        gbIO.updateRecords_tax(0, 100, self.progressSig, findLineage=True, IDs=list_IDs,
                               database=database)

    def fetchByTaxonomy(self):
        tax_, ok = QInputDialog.getText(
            self, 'Enter the taxonomic term', ' Taxonomic name:')
        if not ok:
            return
        else:
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "Working...", parent=self)
            self.progressDialog.show()
            self.fetchTaxWorker = WorkThread(lambda : self.fetchByTaxonomy_slot(tax_), parent=self)
            self.fetchTaxWorker.start()
            self.fetchTaxWorker.finished.connect(
                lambda : [self.progressDialog.close(),
                          self.tableView.clearSelection(),
                          self.select_ids(self.feched_ids)])

    def fetchByTaxonomy_slot(self, tax_):
        index = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(index)
        # indices = self.tableView.selectedIndexes()
        # currentModel = self.tableView.model()
        # currentData = currentModel.arraydata
        # rows = sorted(set(index.row() for index in
        #                   indices), reverse=True)
        # list_IDs = [currentData[row][0] for row in rows]
        gbIO = GbManager(filePath, exceptSig=self.exception_signal)
        self.feched_ids = gbIO.fetch_records_by_tax(0, 100, self.progressSig, taxonomy=tax_)
        # print(ids)

    def saveCitation(self, qtext):
        if qtext.strip() == "XML":
            fileName = QFileDialog.getSaveFileName(
                self, "PhyloSuite", "PhyloSuite_citation", "XML Format(*.xml)")
            xml_path = self.thisPath + os.sep + "PhyloSuite_citation.xml"
            if fileName[0] and (os.path.normpath(fileName[0]) != os.path.normpath(xml_path)):
                shutil.copy(xml_path, fileName[0])
                QMessageBox.information(
                    self,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>File saved successfully!</p>")
        elif qtext.strip() == "RIS":
            fileName = QFileDialog.getSaveFileName(
                self, "PhyloSuite", "PhyloSuite_citation", "RIS Format(*.ris)")
            ris_path = self.thisPath + os.sep + "PhyloSuite_citation.ris"
            if fileName[0] and (os.path.normpath(fileName[0]) != os.path.normpath(ris_path)):
                shutil.copy(ris_path, fileName[0])
                QMessageBox.information(
                    self,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>File saved successfully!</p>")
        elif qtext.strip() == "ENW":
            fileName = QFileDialog.getSaveFileName(
                self, "PhyloSuite", "PhyloSuite_citation", "ENW Format(*.enw)")
            ris_path = self.thisPath + os.sep + "PhyloSuite_citation.enw"
            if fileName[0] and (os.path.normpath(fileName[0]) != os.path.normpath(ris_path)):
                shutil.copy(ris_path, fileName[0])
                QMessageBox.information(
                    self,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'>File saved successfully!</p>")
        elif qtext.strip() == "here":
            country = self.factory.path_settings.value("country", "UK")
            url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/example/" if \
                country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/example/"
            QDesktopServices.openUrl(QUrl(url))
        elif qtext.strip() == "Quick Start":
            country = self.factory.path_settings.value("country", "UK")
            url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/PhyloSuite-demo/quick_start/" if \
                country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/quick_start/"
            QDesktopServices.openUrl(QUrl(url))
        else:
            QDesktopServices.openUrl(QUrl(qtext))

    def deleteFlowchartResults(self, path, name):
        qsettings = QSettings(self.thisPath + '/settings/workflow_settings.ini', QSettings.IniFormat)
        qsettings.setFallbacksEnabled(False)
        qsettings.beginGroup("Flowchart results")
        qsettings.beginGroup(os.path.normpath(path))
        dict_reports = qsettings.value(name, None)
        if not dict_reports:
            return
        ###设置listwidget
        for i in dict_reports:
            if i in ["reports", "time"]:
                continue
            if os.path.exists(dict_reports[i]):
                self.factory.remove_dir_directly(dict_reports[i], removeRoot=True)
        qsettings.remove(name)

    def table4Modification(self, file=None, byContent=False):
        inTable = []
        if byContent:
            inTable = [i.split("\t") for i in byContent.split("\n")]
        else:
            if not file:
                fileName = QFileDialog.getOpenFileName(
                    self, "Input corrected table",
                    filter="CSV Format(*.csv);;")
                if fileName[0]:
                    file = fileName[0]
            inTable = []
            with open(file, encoding="utf-8", errors='ignore') as f:
                reader = csv.reader(f)  # change contents to floats
                for row in reader:  # each row is a list
                    inTable.append(row)
        if inTable:
            while [""] in inTable:
                inTable.remove([""])
            table = self.displayTableModel.array
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "Correcting...", parent=self)
            self.progressDialog.show()
            self.modify_break = False
            self.progressDialog.canceled.connect(lambda: [setattr(self, "modify_break", True),
                                                          self.progressDialog.close()])
            self.readTable2PS(inTable, table)
            # self.worker_modify = WorkThread(lambda : self.readTable2PS(file, table), parent=self)
            # self.modify_break = False

    def readTable2PS(self, inTable, table):
        try:
            ##read inTablePath
            un_editable_col = ["ID", "Length", "AT%", "Date",
                               "Latest modified", "author(s)", "title(s)",
                               "journal(s)", "pubmed ID(s)", "comment(s)",
                               "Keywords", "Molecule type", "Topology",
                               "Accessions", "Sequence version", "Source"]
            inTableHeader = inTable.pop(0)
            total = len(inTable) * len(inTableHeader)
            ##parse table
            # table_1 = deepcopy(table)
            tableHeader = table[0]
            tableRowTexts = [i.split(".")[0] for i in list(map(list, zip(*table)))[0]] #ID把.后面的去掉
            ##开始迭代
            if "=\"ID\"" in inTableHeader:
                inTableHeader[inTableHeader.index("=\"ID\"")] = "ID"
            ID_index = inTableHeader.index("ID") if "ID" in inTableHeader else 0
            # self.modifygen = threadsafe_generator(self.modifyGen(inTable, inTableHeader, un_editable_col,
            #                                                      ID_index, tableRowTexts, tableHeader, table, total))
            # self.modify_table_finished.connect(lambda : next(self.modifygen))
            # next(self.modifygen)
            for num, in_table_row in enumerate(inTable):
                for inTable_col_index, in_value in enumerate(in_table_row):
                    # print(self.modify_break)
                    p_value = (num * len(inTableHeader) + inTable_col_index + 1) * 100 / total
                    self.progressSig.emit(p_value)
                    if self.modify_break:
                        return
                    if not in_value: #有时候有空值
                        continue
                    if inTableHeader[inTable_col_index] not in un_editable_col:
                        ID = in_table_row[ID_index].split(".")[0]
                        if ID in tableRowTexts:
                            if not inTableHeader[inTable_col_index] in tableHeader:
                                continue
                            table_col_index = tableHeader.index(inTableHeader[inTable_col_index])
                            table_row_index = tableRowTexts.index(ID)
                            table_value = table[table_row_index][table_col_index]
                            if in_value != table_value:
                                # print(ID, table_value, in_value, table_row_index, table_col_index)
                                # print(ID, inTableHeader[inTable_col_index], "new value %s"%in_value, "old value %s"%table_value)
                                index = self.displayTableModel.index(table_row_index - 1, table_col_index) #修改的时候行号需要减1，因为加了header
                                # QMetaObject.invokeMethod(self, "modifyTable",
                                #                          Qt.BlockingQueuedConnection,
                                #                          Q_ARG(QModelIndex, str))
                                self.displayTableModel.setData(index, in_value, role=Qt.EditRole)
                                time.sleep(0.03)
                                # self.modify_tableSig.emit(index, in_value)  #是不是要等上个修改完成,再开始下一个比较好
        except:
            self.exception_signal.emit(''.join(
                traceback.format_exception(*sys.exc_info())) + "\n")

    # def modifyGen(self, inTable, inTableHeader, un_editable_col, ID_index, tableRowTexts, tableHeader, table, total):
    #     for num, in_table_row in enumerate(inTable):
    #         for inTable_col_index, in_value in enumerate(in_table_row):
    #             if self.modify_break:
    #                 return
    #             if not in_value:  # 有时候有空值
    #                 self.modify_table_finished.emit()
    #             if inTableHeader[inTable_col_index] not in un_editable_col:
    #                 ID = in_table_row[ID_index]
    #                 if ID in tableRowTexts:
    #                     table_col_index = tableHeader.index(inTableHeader[inTable_col_index])
    #                     table_row_index = tableRowTexts.index(ID)
    #                     table_value = table[table_row_index][table_col_index]
    #                     if in_value != table_value:
    #                         # print(ID, inTableHeader[inTable_col_index], "new value %s"%in_value, "old value %s"%table_value)
    #                         index = self.displayTableModel.index(table_row_index, table_col_index)
    #                         # QMetaObject.invokeMethod(self, "modifyTable",
    #                         #                          Qt.BlockingQueuedConnection,
    #                         #                          Q_ARG(QModelIndex, str))
    #                         self.displayTableModel.setData(index, in_value, role=Qt.EditRole)
    #                         # self.modify_tableSig.emit(index, in_value)  #是不是要等上个修改完成,再开始下一个比较好
    #                     else:
    #                         self.modify_table_finished.emit()
    #                 else:
    #                     self.modify_table_finished.emit()
    #             else:
    #                 self.modify_table_finished.emit()
    #             p_value = (num * len(inTableHeader) + inTable_col_index + 1) * 100 / total
    #             self.progressSig.emit(p_value)
    #             yield

    def remove_treeview4(self):
        indices = self.treeView_4.selectedIndexes()
        currentModel = self.treeView_4.model()
        list_rows = []
        if not indices:
            return
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle('Confirmation!')
        box.setText("<p style='line-height:25px; height:25px'>Once deleted, these data will not be recoverable. Continue? "
                    "<br>Tip: It is safer to delete them in the local file system (that way the data are recoverable). "
                    "Select 'Open' to open it in local file system.</p>")
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        box.addButton(QMessageBox.Open)
        # reply = box.exec_()
        # tree_index = self.treeView.currentIndex()
        # filePath = self.tree_model.filePath(tree_index)
        reply = box.exec_()
        if reply == QMessageBox.Yes:
            for index in indices:
                if index.row() not in list_rows:
                    list_rows.append(index.row())
                    filePath = currentModel.filePath(index)
                    if os.path.isfile(filePath):
                        os.remove(filePath)
                    elif os.path.isdir(filePath):
                        self.factory.remove_dir_directly(filePath, removeRoot=True)
        elif reply == QMessageBox.Open:
            filePath = currentModel.filePath(indices[0])
            self.factory.openPath(filePath, parent=self)

    # @pyqtSlot(dict, result=str)
    # def convertFMT4MrBayes(self, dict_args):
    #     convertfmt = Convertfmt(**dict_args)
    #     return convertfmt.f3

    def isOtherFileSelected(self):
        return self.stackedWidget.currentIndex() == 2 and self.tableView_2.selectedIndexes()

    def reorderGB(self, byName=True):
        treeIndex = self.treeView.currentIndex()
        filePath = self.tree_model.filePath(treeIndex)
        indices = self.tableView.selectedIndexes()
        if indices:
            target = None
            start = None
            if byName:
                name, ok = QInputDialog.getText(
                    self, 'Set gene name', 'Gene name:')
                if ok: target = name
            else:
                pos, ok = QInputDialog.getInt(self, "Set start position", "Position:", 0, 0, 9999999999999999, 1)
                if ok: start = pos
            gbManager = GbManager(filePath, parent=self)
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "reordering...", parent=self)
            self.progressDialog.show()
            currentModel = self.tableView.model()
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in
                              indices), reverse=True)
            list_IDs = [currentData[row][0] for row in rows]
            self.progressSig.emit(5)
            gbWorker = WorkThread(lambda: gbManager.reorder(list_IDs, 5, 95, self.progressSig, target, start, self.warning_signal),
                                  parent=self)
            gbWorker.start()
            gbWorker.finished.connect(self.progressDialog.close)

    def popupWarning(self, text):
        QMessageBox.warning(
            self,
            "Warning",
            "<p style='line-height:25px; height:25px'>%s</p>"%text)