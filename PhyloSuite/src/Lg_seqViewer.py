#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.CustomWidget import MySeqTable, MyQtableView, MySeqSettingTable
from uifiles.Ui_seqViewSetting import Ui_seqViewSetting
from src.factory import Factory, Parsefmt, Convertfmt
from uifiles.Ui_SeqViewer import Ui_Seq_viewer
import copy
import os
import time
from collections import OrderedDict


class SeqViewSettings(QDialog, Ui_seqViewSetting):
    closeSig = pyqtSignal()

    def __init__(self, parent=None):
        super(SeqViewSettings, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.setupUi(self)
        # 保存设置
        self.Seq_viewer_setting = QSettings(
            self.thisPath +
            '/settings/Seq_viewer_setting.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.Seq_viewer_setting.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.display_font = self.Seq_viewer_setting.value("display font")
        self.refreshFont(self.display_font)
        self.dict_foreColor = self.Seq_viewer_setting.value("foreground colors")
        self.dict_backColor = self.Seq_viewer_setting.value("background colors")
        self.tableView.verticalHeader().setDefaultSectionSize(70)
        self.tableView.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)  # 固定header的大小
        self.tableView.horizontalHeader().setDefaultSectionSize(70)
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.tableView.verticalHeader().hide()
        self.tableView.horizontalHeader().hide()
        self.tableView.doubleClicked.connect(self.popUpColorSel)
        self.table_model = MySeqSettingTable(self.dict_foreColor, self.dict_backColor, self)
        # 信号和槽
        # model.dataChanged.connect(self.datachanged)
        self.tableView.setModel(self.table_model)

    @pyqtSlot()
    def on_toolButton_clicked(self):
        font, ok = QFontDialog.getFont(self.display_font, self)
        if ok:
            self.Seq_viewer_setting.setValue("display font", font)
            self.display_font = font
            self.refreshFont(font)

    def refreshFont(self, font):
        bold = "Bold" if font.bold() else ""
        italic = "Italic" if font.italic() else ""
        display_text = " ".join([font.family(), str(font.pointSize()), bold, italic])
        self.lineEdit_fontSet.setText(display_text)
        self.lineEdit_fontSet.setFont(font)

    def popUpColorSel(self, index):
        dialog = QDialog(self)
        dialog.resize(189, 200)
        dialog.setWindowTitle("")
        verticalLayout = QVBoxLayout(dialog)
        groupBox = QGroupBox(dialog)
        gridLayout = QGridLayout(groupBox)
        gridLayout.setContentsMargins(2, 2, 2, 2)
        toolButton = QToolButton(groupBox)
        toolButton.setText("Foreground color")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(toolButton.sizePolicy().hasHeightForWidth())
        toolButton.setSizePolicy(sizePolicy)
        toolButton.setIcon(QIcon(":/picture/resourses/foreground.png"))
        toolButton.setIconSize(QSize(60, 60))
        toolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolButton.setAutoRaise(True)
        toolButton.clicked.connect(lambda : self.setForeColor(index))
        toolButton.clicked.connect(dialog.close)
        gridLayout.addWidget(toolButton, 0, 0, 1, 1)
        verticalLayout.addWidget(groupBox)
        groupBox_2 = QGroupBox(dialog)
        gridLayout_2 = QGridLayout(groupBox_2)
        gridLayout_2.setContentsMargins(2, 2, 2, 2)
        toolButton_2 = QToolButton(groupBox_2)
        toolButton_2.setText("Background color")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(toolButton_2.sizePolicy().hasHeightForWidth())
        toolButton_2.setSizePolicy(sizePolicy)
        toolButton_2.setIcon(QIcon(":/picture/resourses/background.png"))
        toolButton_2.setIconSize(QSize(60, 60))
        toolButton_2.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolButton_2.setAutoRaise(True)
        toolButton_2.clicked.connect(lambda : self.setBackColor(index))
        toolButton_2.clicked.connect(dialog.close)
        gridLayout_2.addWidget(toolButton_2, 0, 0, 1, 1)
        verticalLayout.addWidget(groupBox_2)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        dialog.exec_()

    def setForeColor(self, index):
        color = QColorDialog.getColor(self.table_model.data(index, Qt.ForegroundRole), self)
        if color.isValid():
            self.table_model.setData(index, color.name(), Qt.ForegroundRole)
            self.dict_foreColor[self.table_model.arraydata[index.row()][index.column()]] = color.name()
            self.Seq_viewer_setting.setValue("foreground colors", self.dict_foreColor)

    def setBackColor(self, index):
        color = QColorDialog.getColor(self.table_model.data(index, Qt.BackgroundRole), self)
        if color.isValid():
            self.table_model.setData(index, color.name(), Qt.BackgroundRole)
            self.dict_backColor[self.table_model.arraydata[index.row()][index.column()]] = color.name()
            self.Seq_viewer_setting.setValue("background colors", self.dict_backColor)

    def closeEvent(self, event):
        self.Seq_viewer_setting.setValue("foreground colors", self.dict_foreColor)
        self.Seq_viewer_setting.setValue("background colors", self.dict_backColor)
        self.Seq_viewer_setting.setValue("display font", self.display_font)
        self.closeSig.emit()

class Seq_viewer(QMainWindow, Ui_Seq_viewer, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    startButtonStatusSig = pyqtSignal(list)

    def __init__(
            self,
            workPath=None,
            alignments=None,   #如果alignments是字典，就是mafft传过来的标记模式:{file: [[taxon1, 22], [taxon2, 31]]}
            processSig=None,
            progressDialog=None,
            parent=None):
        super(Seq_viewer, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.processSig = processSig
        self.progressDialog = progressDialog
        self.parsefmt = Parsefmt("")
        self.alignment_files = alignments
        self.setupUi(self)
        # 保存设置
        self.Seq_viewer_setting = QSettings(
            self.thisPath +
            '/settings/Seq_viewer_setting.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.Seq_viewer_setting.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        # undoView = QUndoView(self.undoStack)
        # self.gridLayout.addWidget(undoView, 1, 0, 1, 1)
        ##tabwidget设置
        self.tabWidget.tabCloseRequested.connect(self.removeTab)
        self.tabWidget.currentChanged.connect(self.currentTable)
        self.tabWidget.installEventFilter(self)
        self.stackedWidget.installEventFilter(self)
        # 恢复用户的设置
        self.guiRestore()
        self.label_5.linkActivated.connect(self.on_actionImport_triggered)
        # ##analyses menu
        # analysis_popMenu = QMenu(self)
        # self.mafft = QAction(QIcon(":/picture/resourses/mafft1.png"), "MAFFT", self,
        #                 statusTip="Align with MAFFT")
        # self.gblocks = QAction(QIcon(":/picture/resourses/if_simpline_22_2305632.png"), "Gblocks", self,
        #                   statusTip="Gblocks")
        # self.catSeq = QAction(QIcon(":/picture/resourses/cat1.png"), "Concatenate Sequence", self,
        #                  statusTip="Concatenate Sequence")
        # self.cvtFMT = QAction(QIcon(":/picture/resourses/transform3.png"), "Convert Sequence Format", self,
        #                  statusTip="Convert Sequence Format")
        # self.modelfinder = QAction(QIcon(":/picture/resourses/if_tinder_334781.png"), "ModelFinder", self,
        #                       statusTip="Select model with ModelFinder")
        # self.iqtree = QAction(QIcon(":/picture/resourses/data-taxonomy-icon.png"), "IQ-TREE", self,
        #                  statusTip="Reconstruct tree with IQ-TREE")
        # self.mrbayes = QAction(QIcon(":/picture/resourses/2000px-Paris_RER_B_icon.svg.png"), "MrBayes", self,
        #                   statusTip="Reconstruct tree with MrBayes")
        # analysis_popMenu.addAction(self.mafft)
        # analysis_popMenu.addAction(self.gblocks)
        # analysis_popMenu.addAction(self.catSeq)
        # analysis_popMenu.addAction(self.cvtFMT)
        # analysis_popMenu.addSeparator()
        # analysis_popMenu.addAction(self.modelfinder)
        # analysis_popMenu.addAction(self.iqtree)
        # analysis_popMenu.addAction(self.mrbayes)
        # # analysis_popMenu.triggered.connect(self.switchWorkPlace)
        # self.actionAnalyses.setMenu(analysis_popMenu)

    @pyqtSlot()
    def on_actionImport_triggered(self):
        """
        open files
        """
        files = QFileDialog.getOpenFileNames(
            self, "Input Files",
            filter="Supported Format(*.fas *.fasta *.phy *.phylip *.nex *.nxs *.nexus);;")
        if files[0]:
            self.input(files[0])

    @pyqtSlot()
    def on_actionExport_triggered(self):
        """
        export files
        """
        file = self.tabWidget.tabToolTip(self.tabWidget.currentIndex())
        if not file:
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Nothing can be exported</p>")
            return
        dict_taxon = self.tableView.model().fetchDictTaxon()
        initial_file = os.path.splitext(file)[0]
        NameAndFilter = QFileDialog.getSaveFileName(self,
                                                             "Choose file and format", initial_file,
                                                             "Fasta Format (*.fas);;Phylip Format (*.phy);;"
                                                             "Nexus Format (*.nex);;")
        if NameAndFilter[0]:
            dict_fmt = {"Fasta Format (*.fas)": "export_fas",
                        "Phylip Format (*.phy)": "export_phylip",
                        "Nexus Format (*.nex)": "export_nex",
                        "": "export_fas"}
            dict_args = {"userSave": NameAndFilter[0], dict_fmt[NameAndFilter[1]]: True}
            convertfmt = Convertfmt(**dict_args)
            convertfmt.generate_each(dict_taxon, file)
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>File saved successfully</p>")

    @pyqtSlot()
    def on_actionCopy_triggered(self):
        """
        Copy
        """
        self.copySeq()

    @pyqtSlot()
    def on_actionCut_triggered(self):
        """
        Cut
        """
        self.cutSeq()

    @pyqtSlot()
    def on_actionPaste_triggered(self):
        """
        Paste
        """
        self.pasteSeq()

    @pyqtSlot()
    def on_actionUndo_triggered(self):
        """
        undo
        """
        self.undoStack.undo()

    @pyqtSlot()
    def on_actionRedo_triggered(self):
        """
        redo
        """
        self.undoStack.redo()

    @pyqtSlot()
    def on_actionRevsComp_triggered(self):
        """
        Reverse Complement
        """
        self.reverseComplete("Reverse Complement")

    @pyqtSlot()
    def on_actionReverse_triggered(self):
        """
        Reverse
        """
        self.reverseComplete("Reverse")

    @pyqtSlot()
    def on_actionComplement_triggered(self):
        """
        Reverse
        """
        self.reverseComplete("Complement")

    @pyqtSlot()
    def on_actionSettings_triggered(self):
        """
        settings
        """
        setting = SeqViewSettings(self)
        setting.closeSig.connect(self.updateTableSettings)
        # 隐藏？按钮
        setting.setWindowFlags(setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        setting.exec_()

    def currentTable(self, index):
        widget = self.tabWidget.widget(index)
        if (not widget) or (not widget.children()):
            return
        flag = False
        for i in widget.children():
            if isinstance(i, QTableView):
                self.tableView = i
                flag = True
                break
        if flag:
            #设置初始的值
            array = self.tableView.model().arraydata
            selectedIndex = self.tableView.selectedIndexes()
            index1 = selectedIndex[0] if selectedIndex else self.tableView.model().index(0, 1)
            self.label.setText("(%d) Taxon Name: %s" %(index1.row()+1, array[index1.row()][0]))
            self.spinBox.setValue(index1.column()) #这个要放在下面信号绑定前执行，否则会有错误
            self.spinBox.valueChanged.connect(self.moveSelcetedSite)
            self.undoStack = self.tableView.undoStack
            ##mark模式
            file = os.path.normpath(self.tabWidget.tabToolTip(index))
            if hasattr(self, "markMode") and self.markMode and (file in self.alignment_files):
                self.dict_mark_area = OrderedDict(("Stop codon %d"%(num+1), coordinate) for num, coordinate in enumerate(self.alignment_files[file]))
                self.MarkCombo.activated[str].connect(self.moveMarkArea)
                model = self.MarkCombo.model()
                self.MarkCombo.clear()
                for num, i in enumerate(self.dict_mark_area):
                    item = QStandardItem(i)
                    # 背景颜色
                    if num % 2 == 0:
                        item.setBackground(QColor(255, 255, 255))
                    else:
                        item.setBackground(QColor(237, 243, 254))
                    model.appendRow(item)

    def deleteSeq(self):
        """
        delete
        """
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if currentModel and indices:
            command = CommandDelete(self.tableView, currentModel,
                                   indices,
                                   description="change model %s" % time.strftime('%Y/%m/%d %H:%M:%S',
                                                                                 time.localtime(time.time())))
            self.undoStack.push(command)
        self.tableView.clearSelection()

    def guiSave(self):
        # Save geometry
        self.Seq_viewer_setting.setValue('size', self.size())
        # self.Seq_viewer_setting.setValue('pos', self.pos())
        # self.Seq_viewer_setting.setValue("foreground colors", self.dict_foreColor)
        # self.Seq_viewer_setting.setValue("background colors", self.dict_backColor)
        # self.display_font = self.Seq_viewer_setting.value("display font", QFont("Courier New", 11))

    def guiRestore(self):

        # Restore geometry
        self.resize(self.Seq_viewer_setting.value('size', QSize(1346, 641)))
        self.factory.centerWindow(self)
        # self.move(self.Seq_viewer_setting.value('pos', QPoint(60, 60)))
        self.font = self.Seq_viewer_setting.value("display font")
        self.dict_foreColor = self.Seq_viewer_setting.value("foreground colors")
        self.dict_backColor = self.Seq_viewer_setting.value("background colors")
        if type(self.alignment_files) == OrderedDict:
            code_table = self.alignment_files.pop("code table")
            self.label_3.setText("<html><head/><body><p><span style='font-weight:600; color:#ff0000;'>Internal stop codons</span> (<a href=\"https://www.ncbi.nlm.nih.gov/Taxonomy/taxonomyhome.html/index.cgi?chapter=tgencodes#SG%s\"><span style=\" text-decoration: underline; color:#0000ff;\">code table %s</span></a>):</p></body></html>"%(code_table, code_table))
            self.markMode = True
            self.label_3.setVisible(True)
            self.MarkCombo.setVisible(True)
            self.input(self.alignment_files, rawSeq=True)
            self.currentTable(self.tabWidget.count()-1) ##初始化一下切换事件
            self.moveMarkArea(list(self.dict_mark_area.keys())[0])
        else:
            self.label_3.setVisible(False)
            self.MarkCombo.setVisible(False)
            self.input(self.alignment_files)

    def popupException(self, exception):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        for index in range(self.tabWidget.count()):
            widget = self.tabWidget.widget(index)
            if widget and widget.children():
                for i in widget.children():
                    if isinstance(i, QTableView):
                        tableView = i
                if self.dataHasChanged(index, tableView):
                    self.handleChangedData(index, tableView)
        self.guiSave()

    def eventFilter(self, obj, event):
        if isinstance(obj, QStackedWidget):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                files = [i for i in files if os.path.splitext(i)[1].upper() in
                         [".FAS", ".FASTA", ".PHY", ".PHYLIP", ".NEX", ".NXS", ".NEXUS"]]
                self.input(files)
        if isinstance(
                obj,
                QTableView) or isinstance(obj, QTabWidget):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                files = [i for i in files if os.path.splitext(i)[1].upper() in
                         [".FAS", ".FASTA", ".PHY", ".PHYLIP", ".NEX", ".NXS", ".NEXUS"]]
                self.input(files)
            if event.type() == QEvent.KeyPress:  # 首先得判断type
                self.list_residue = [Qt.Key_A, Qt.Key_T, Qt.Key_C, Qt.Key_G,  # 绑定20个按键
                                     Qt.Key_P, Qt.Key_S, Qt.Key_D, Qt.Key_V,
                                     Qt.Key_N, Qt.Key_I, Qt.Key_E, Qt.Key_L,
                                     Qt.Key_Q, Qt.Key_H, Qt.Key_M, Qt.Key_F,
                                     Qt.Key_K, Qt.Key_Y, Qt.Key_R, Qt.Key_W,
                                     Qt.Key_U]
                modifiers = QApplication.keyboardModifiers()
                if modifiers == Qt.ControlModifier:
                    if event.key() == Qt.Key_Z:
                        self.undoStack.undo()
                        return True
                    if event.key() == Qt.Key_Y:
                        self.undoStack.redo()
                        return True
                    if event.key() == Qt.Key_C:
                        self.copySeq()
                        return True
                    if event.key() == Qt.Key_X:
                        self.cutSeq()
                        return True
                    if event.key() == Qt.Key_V:
                        self.pasteSeq()
                        return True
                    if event.key() == Qt.Key_S:
                        self.on_actionExport_triggered()
                        return True
                elif event.key() in self.list_residue:
                    self.addResidue(chr(event.key()))
                    return True
                elif event.key() == Qt.Key_Delete:
                    self.deleteSeq()
                    return True
        # # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(Seq_viewer, self).eventFilter(obj, event)  # 0

    def fmtSeq(self, file, noProcess=False, rawSeq=False):
        processSig = self.processSig if not noProcess else None
        dict_taxon = self.parsefmt.readfile(file, 0, 100, processSig)
        array = []
        for i in dict_taxon:
            seq = dict_taxon[i].upper() if not rawSeq else dict_taxon[i].upper().replace("-", "")
            array.append([i] + list(seq))
        if self.progressDialog and (not noProcess):
            self.progressDialog.close()
        return array

    def datachanged(self, index, index1):
        currentModel = self.tableView.model()
        command = CommandEdit(self.tableView, index, currentModel, description="change cell %s"%time.strftime('%Y/%m/%d %H:%M:%S',time.localtime(time.time())))
        self.undoStack.push(command)

    def on_table_clicked(self, index):
        if index.column() == 0:
            self.tableView.selectRow(index.row())
        else:
            self.label.setText("(%d) Taxon Name: %s"%(index.row()+1, self.tableView.model().arraydata[index.row()][0]))
            self.spinBox.setValue(index.column())

    def moveSelcetedSite(self, column):
        row = int(re.search(r"\((\d+)\)", self.label.text()).group(1)) - 1
        self.tableView.setCurrentIndex(self.tableView.model().index(row, column))

    def selectRow(self):
        selectedIndice = self.tableView.selectedIndexes()
        if not selectedIndice:
            return
        self.tableView.selectRow(selectedIndice[0].row())

    def selectCol(self):
        selectedIndice = self.tableView.selectedIndexes()
        if not selectedIndice:
            return
        self.tableView.selectColumn(selectedIndice[0].column())

    def editCell(self):
        selectedIndice = self.tableView.selectedIndexes()
        if not selectedIndice:
            return
        self.tableView.edit(selectedIndice[0])

    def addResidue(self, residue):
        selectedIndice = self.tableView.selectedIndexes()
        if not selectedIndice:
            return
        currentModel = self.tableView.model()
        command = CommandAdd(self.tableView, selectedIndice[0], currentModel, residue,
                              description="add residues %s" % time.strftime('%Y/%m/%d %H:%M:%S',
                                                                           time.localtime(time.time())))
        self.undoStack.push(command)

    def copySeq(self):
        selectedIndice = self.tableView.selectedIndexes()
        if not selectedIndice:
            return
        arraydate = self.tableView.model().arraydata
        selectedText = ""
        sorted_selectedIndice = sorted(selectedIndice, key=lambda x: (x.row(), x.column()))
        lastRow = sorted_selectedIndice[0].row()
        for index in sorted_selectedIndice:
            if arraydate[index.row()][index.column()] == ".":
                continue
            selectedText += arraydate[index.row()][index.column()] if index.row() == lastRow else "\n" + arraydate[index.row()][index.column()]
            lastRow = index.row()
        QApplication.clipboard().setText(selectedText)

    def cutSeq(self):
        selectedIndice = self.tableView.selectedIndexes()
        if not selectedIndice:
            return
        arraydate = self.tableView.model().arraydata
        selectedText = ""
        sorted_selectedIndice = sorted(selectedIndice, key=lambda x: (x.row(), x.column()))
        lastRow = sorted_selectedIndice[0].row()
        for index in sorted_selectedIndice:
            if arraydate[index.row()][index.column()] == ".":
                continue
            selectedText += arraydate[index.row()][index.column()] if index.row() == lastRow else "\n" + arraydate[
                index.row()][index.column()]
            lastRow = index.row()
        QApplication.clipboard().setText(selectedText)
        self.deleteSeq()

    def pasteSeq(self):
        ##暂时未
        indices = self.tableView.selectedIndexes()
        if not indices:
            return
        currentModel = self.tableView.model()
        if currentModel and indices:
            command = CommandPaste(self.tableView, currentModel,
                                   indices,
                                   description="paste contents %s" % time.strftime('%Y/%m/%d %H:%M:%S',
                                                                                 time.localtime(time.time())))
            self.undoStack.push(command)

    def reverseComplete(self, action):
        if type(action) == str:
            text = action
        else:
            text = action.text()
        indices = self.tableView.selectedIndexes()
        if not indices:
            return
        currentModel = self.tableView.model()
        if not currentModel or not indices:
            return
        list_rows = list(set([index.row() for index in indices]))
        if text == "Reverse Complement":
            command = CommandRevCmp(self.tableView, currentModel,
                                    list_rows, "Reverse Complement",
                                    description="Reverse Complement %s" % time.strftime('%Y/%m/%d %H:%M:%S',
                                                                                  time.localtime(time.time())))
            self.undoStack.push(command)
        elif text == "Reverse":
            command = CommandRevCmp(self.tableView, currentModel,
                                    list_rows, "Reverse",
                                    description="Reverse %s" % time.strftime('%Y/%m/%d %H:%M:%S',
                                                                                  time.localtime(time.time())))
            self.undoStack.push(command)
        elif text == "Complement":
            command = CommandRevCmp(self.tableView, currentModel,
                                    list_rows, "Complement",
                                    description="Complement %s" % time.strftime('%Y/%m/%d %H:%M:%S',
                                                                                  time.localtime(time.time())))
            self.undoStack.push(command)
        self.tableView.clearSelection()

    def input(self, list_files, rawSeq=False):
        ##rawSeq用于删除比对序列的-，MAFFT查看终止密码子比较有用
        if not list_files:
            self.stackedWidget.setCurrentIndex(1)
            if self.progressDialog:
                self.progressDialog.close()
        else:
            self.stackedWidget.setCurrentIndex(0)
            currentFiles = [os.path.normpath(self.tabWidget.tabToolTip(index)) for index in range(self.tabWidget.count())]
            for i in list_files:
                if os.path.normpath(i) not in currentFiles:
                    #已经有的文件不导入
                    self.addtab(i, rawSeq=rawSeq)

    def addtab(self, file, rawSeq=False):
        array = self.fmtSeq(file, rawSeq=rawSeq)
        tab = QWidget(self.tabWidget)
        horizontalLayout_2 = QHBoxLayout(tab)
        horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        horizontalLayout_2.setSpacing(0)
        tableView = MyQtableView(self)
        tableView.setStyleSheet(
            "QTableView::item:selected {background: #EDF3FE; color: red; border: 0px outset red;}")
        self.undoStack = tableView.undoStack
        model = MySeqTable(array, self.font, self.dict_foreColor, self.dict_backColor, self)
        # 信号和槽
        model.dataChanged.connect(self.datachanged)
        tableView.setModel(model)
        self.configTableView(tableView)
        horizontalLayout_2.addWidget(tableView)
        self.tabWidget.addTab(tab, QIcon(":/seq_Viewer/resourses/seq_viewer/file_512px_1175580_easyicon.net.png"),
                              os.path.basename(file))
        self.tabWidget.setTabToolTip(self.tabWidget.count()-1, file)
        self.tabWidget.setCurrentIndex(self.tabWidget.count()-1)

    def removeTab(self, index):
        widget = self.tabWidget.widget(index)
        if widget and widget.children():
            for i in widget.children():
                if isinstance(i, QTableView):
                    tableView = i
            if self.dataHasChanged(index, tableView):
                self.handleChangedData(index, tableView)
            widget.deleteLater()
            self.tabWidget.removeTab(index)
        if not self.tabWidget.count():
            self.stackedWidget.setCurrentIndex(1)

    def configTableView(self, tableView):
        # 右键菜单
        tableView_popMenu = QMenu(self)
        selectAll = QAction(QIcon(":/picture/resourses/all icon.png"), "Select All", self,
                            shortcut=QKeySequence("Ctrl+A"),
                            statusTip="Select all sequences",
                            triggered=tableView.selectAll)
        selectRow = QAction(QIcon(":/picture/resourses/if_f-table-row_128_307998.png"), "Select Row", self,
                            statusTip="Select the row",
                            triggered=self.selectRow)
        selectCol = QAction(QIcon(":/picture/resourses/if_f-table-column_128_307997.png"), "Select Column", self,
                            statusTip="Select the column",
                            triggered=self.selectCol)
        save = QAction(QIcon(":/picture/resourses/Save-icon.png"), "Save file", self,
                            shortcut=QKeySequence("Ctrl+S"),
                            statusTip="Save current file",
                            triggered=self.on_actionExport_triggered)
        edit = QAction(QIcon(":/picture/resourses/edit2.png"), "Edit", self,
                       statusTip="Edit select cell",
                       triggered=self.editCell)
        remove = QAction(QIcon(":/picture/resourses/if_Delete_1493279.png"), "Delete", self,
                         shortcut=QKeySequence.Delete,
                         statusTip="Delete selected sequences",
                         triggered=self.deleteSeq)
        copy = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/copy.png"), "Copy", self,
                       shortcut="Ctrl+C",
                       statusTip="Copy selected sequences",
                       triggered=self.copySeq)
        paste = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/paste_512px_1175635_easyicon.net.png"), "Paste", self,
                        shortcut="Ctrl+V",
                        statusTip="Paste sequences",
                        triggered=self.pasteSeq)
        cut = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/cut.png"), "Cut", self,
                      shortcut="Ctrl+X",
                      statusTip="Cut selected sequences",
                      triggered=self.cutSeq)
        undo = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/undo.png"), "Undo", self,
                       statusTip="Undo",
                       shortcut="Ctrl+Z",
                       triggered=self.undoStack.undo)
        redo = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/redo.png"), "Redo", self,
                       statusTip="Redo",
                       shortcut="Ctrl+Y",
                       triggered=self.undoStack.redo)
        revcomp = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/28105126-d6a6ce90-66fb-11e7-8546-72517772000b.png"), "Reverse Complement", self,
                          statusTip="Reverse Complement select sequences")
        reverse = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/transfer-10-67552.png"), "Reverse", self,
                          statusTip="Reverse select sequences")
        complement = QAction(QIcon(":/seq_Viewer/resourses/seq_viewer/if_ic_transform_48px_352180.png"), "Complement", self,
                             statusTip="Complement select sequences")
        # tableView_popMenu.addAction(selectAll)
        # tableView_popMenu.addAction(selectRow)
        # tableView_popMenu.addAction(selectCol)
        # tableView_popMenu.addSeparator()
        tableView_popMenu.addAction(revcomp)
        tableView_popMenu.addAction(reverse)
        tableView_popMenu.addAction(complement)
        tableView_popMenu.addSeparator()
        tableView_popMenu.addAction(save)
        tableView_popMenu.addAction(edit)
        tableView_popMenu.addAction(remove)
        tableView_popMenu.addAction(copy)
        tableView_popMenu.addAction(paste)
        tableView_popMenu.addAction(cut)
        tableView_popMenu.addAction(undo)
        tableView_popMenu.addAction(redo)
        tableView_popMenu.triggered[QAction].connect(self.reverseComplete)
        tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        def popUpMenu(qpoint):
            if not tableView.indexAt(qpoint).isValid():
                return
            indices = tableView.selectedIndexes()
            if len(set([i.column() for i in indices])) < tableView.model().columnCount(self):
                for action in [revcomp, reverse, complement]:
                    action.setDisabled(True)
            else:
                for action in [revcomp, reverse, complement]:
                    action.setDisabled(False)
            tableView_popMenu.exec_(QCursor.pos())
        tableView.customContextMenuRequested.connect(popUpMenu)
        self.setTableCellSize(tableView)
        tableView.clicked.connect(self.on_table_clicked)
        tableView.horizontalHeader().sectionClicked.connect(tableView.selectColumn)
        tableView.setTextElideMode(2)  ##文字省略中间部分
        tableView.setAcceptDrops(True)
        tableView.installEventFilter(self)
        tableView.model().layoutChanged.connect(lambda : [tableView.model().makeColHeader(),
                                                          self.setTableCellSize(tableView)]) #更新头上的星号

    def moveMarkArea(self, text):
        if not text:
            return
        coord = self.dict_mark_area[text]
        model = self.tableView.model()
        array = model.arraydata
        row = [num for num, i in enumerate(array) if i[0] == coord[0]][0]
        self.tableView.clearSelection()
        self.tableView.setCurrentIndex(model.index(row, coord[1]+2))
        self.tableView.scrollTo(model.index(row, coord[1]+2), QAbstractItemView.PositionAtCenter)  #显示在中间
        self.on_table_clicked(model.index(row, coord[1]+1)) ##改变下面文字
        selectionmodel = self.tableView.selectionModel()
        selectionmodel.select(model.index(row, coord[1]+1), QItemSelectionModel.Select)
        selectionmodel.select(model.index(row, coord[1]+2), QItemSelectionModel.Select)
        selectionmodel.select(model.index(row, coord[1]+3), QItemSelectionModel.Select)

    def dataHasChanged(self, index, tableView):
        OriginalArray = self.fmtSeq(self.tabWidget.tabToolTip(index), noProcess=True)
        if OriginalArray != tableView.model().fetchCleanArray():
            return True
        else:
            return False

    def handleChangedData(self, index, tableView):
        filename = self.tabWidget.tabText(index)
        reply = QMessageBox.question(
            self,
            filename,
            "<p style='line-height:25px; height:25px'>Save file <span style='font-weight:600; color:#ff0000;'>%s?</span></p>"%filename,
            QMessageBox.Yes,
            QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            file = self.tabWidget.tabToolTip(index)
            ex_format = os.path.splitext(file)[1]
            dict_fmt = {".FAS": "export_fas",
                        ".FASTA": "export_fas",
                        ".PHY": "export_phylip",
                        ".PHYLIP": "export_phylip",
                        ".NEX": "export_nex",
                        ".NXS": "export_nex",
                        ".NEXUS": "export_nex"}
            dict_taxon = tableView.model().fetchDictTaxon()
            dict_args = {"userSave": file, dict_fmt[ex_format.upper()]: True}
            convertfmt = Convertfmt(**dict_args)
            convertfmt.generate_each(dict_taxon, file)

    def addFiles(self, files):
        if files:
            self.input(files)

    def setTableCellSize(self, tableView):
        width = QFontMetrics(self.font).width("Q")
        height = QFontMetrics(self.font).height()
        tableView.verticalHeader().setDefaultSectionSize(height + height * 4 / 10)
        tableView.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)  # 固定header的大小
        tableView.horizontalHeader().setDefaultSectionSize(width * 2)
        tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        tableView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)  # 只设置第一列
        tableView.horizontalHeader().resizeSection(0, 150)

    def updateTableSettings(self):
        font_changed, foreColChanged, backColChanged = False, False, False
        if self.Seq_viewer_setting.value("display font") != self.font:
            self.font = self.Seq_viewer_setting.value("display font")
            font_changed = True
        if self.Seq_viewer_setting.value("foreground colors") != self.dict_foreColor:
            self.dict_foreColor = self.Seq_viewer_setting.value("foreground colors")
            foreColChanged = True
        if self.Seq_viewer_setting.value("background colors") != self.dict_backColor:
            self.dict_backColor = self.Seq_viewer_setting.value("background colors")
            backColChanged = True
        for index in range(self.tabWidget.count()): #扫描tableview
            widget = self.tabWidget.widget(index)
            if widget and widget.children():
                for i in widget.children():
                    if isinstance(i, QTableView):
                        tableView = i
                        model = tableView.model()
                        if font_changed:
                            model.font = self.font
                            self.setTableCellSize(tableView)
                        if foreColChanged:
                            model.dict_foreColor = self.dict_foreColor
                        if backColChanged:
                            model.dict_backColor = self.dict_backColor
                        model.layoutChanged.emit()


    # def detectChange(self):
    #     OriginalArray = self.fmtSeq(self.tabWidget.tabToolTip(self.tabWidget.currentIndex()), noProcess=True)
    #     if OriginalArray != self.tableView.model().fetchCleanArray():
    #         self.tabWidget.setTabIcon(self.tabWidget.currentIndex(),
    #                                   QIcon(":/seq_Viewer/resourses/seq_viewer/file_512px_1175780_easyicon.net.png"))
    #     else:
    #         self.tabWidget.setTabIcon(self.tabWidget.currentIndex(),
    #                                   QIcon(":/seq_Viewer/resourses/seq_viewer/file_512px_1175580_easyicon.net.png"))


class CommandDelete(QUndoCommand):
    #删除的撤销恢复
    def __init__(self, tableView, currentModel, indices, description=None):
        super(CommandDelete, self).__init__(description)
        self.tableView = tableView
        self.indices = indices
        self.currentModel = currentModel

    def redo(self):
        currentData = self.currentModel.arraydata
        # self.dataBeforeEdit = copy.deepcopy(currentData)
        dict_row_cols = OrderedDict()
        for i in self.indices:
            col = i.column()
            row = i.row()
            dict_row_cols.setdefault(row, []).append(col)
        rows = sorted(list(dict_row_cols.keys()), reverse=True)  # 从大到小
        self.dict_coord_value = OrderedDict() #记录被删除的坐标，及其对应的值
        for row in rows:
            # 从每一列的最右边开始删
            cols = sorted(dict_row_cols[row], reverse=True)
            for col in cols:
                self.dict_coord_value[(row, col)] = currentData[row].pop(col)
        self.dict_coord_value["row_removed"] = [] #记录被删除的行
        while [] in currentData:
            self.dict_coord_value["row_removed"].append(currentData.index([]))
            # 循环删除空行
            currentData.remove([])
        self.currentModel.complementArray()
        self.currentModel.layoutChanged.emit()

    def undo(self):
        array = self.currentModel.arraydata
        list_removed_rows = self.dict_coord_value.pop("row_removed")
        if list_removed_rows:
            for i in sorted(list_removed_rows):
                #把行加上去
                array.insert(i, [])
        if self.dict_coord_value:
            for coord in sorted(self.dict_coord_value):
                array[coord[0]].insert(coord[1], self.dict_coord_value[coord])
        # self.currentModel.arraydata = array
        self.currentModel.makeColHeader()
        self.currentModel.complementArray()
        self.currentModel.layoutChanged.emit()

class CommandEdit(QUndoCommand):
    # 双击编辑cell的撤销恢复
    def __init__(self, tableView, index, currentModel, description):
        super(CommandEdit, self).__init__(description)
        self.tableView = tableView
        self.index = index
        self.currentModel = currentModel
        self.textAfterEdit = copy.deepcopy(self.currentModel.textAfterEdit)

    def redo(self):
        currentData = self.currentModel.arraydata
        # self.dataBeforeEdit = copy.deepcopy(currentData)
        self.list_coord_oldValue = [(self.index.row(), self.index.column()), currentData[self.index.row()][self.index.column()]]
        currentData[self.index.row()][self.index.column()] = self.textAfterEdit
        self.currentModel.layoutChanged.emit()

    def undo(self):
        self.textAfterEdit = self.currentModel.arraydata[self.index.row()][self.index.column()] #为redo准备
        self.currentModel.arraydata[self.list_coord_oldValue[0][0]][self.list_coord_oldValue[0][1]] = self.list_coord_oldValue[1]
        self.currentModel.layoutChanged.emit()

class CommandAdd(QUndoCommand):
    # 增加碱基的撤销恢复
    def __init__(self, tableView, index, currentModel, residue, description):
        super(CommandAdd, self).__init__(description)
        self.tableView = tableView
        self.index = index
        self.currentModel = currentModel
        self.residue = residue

    def redo(self):
        currentData = self.currentModel.arraydata
        self.list_addedCol = [(self.index.row(), self.index.column())]
        #先判断一下改行是否有空的，如果有就不用增加一列
        if "." == currentData[self.index.row()][-1]:
            #删除最后的.，等碱基添加
            currentData[self.index.row()].pop(-1)
            self.list_addedCol.append("remove last point")
        else:
            #每行增加一个.
            for row, row_data in enumerate(currentData):
                if row != self.index.row():
                    currentData[row].append(".")
            self.list_addedCol.append("complement last column")
            self.currentModel.makeColHeader() #必须刷新一下header
        currentData[self.index.row()].insert(self.index.column(), self.residue)
        self.currentModel.layoutChanged.emit()

    def undo(self):
        currentData = self.currentModel.arraydata
        if self.list_addedCol[-1] == "complement last column":
            for row, row_data in enumerate(currentData):
                if row != self.list_addedCol[0][0]:
                    currentData[row].pop(-1)
        if self.list_addedCol[-1] == "remove last point":
            currentData[self.list_addedCol[0][0]].append(".")
        currentData[self.list_addedCol[0][0]].pop(self.list_addedCol[0][1])
        self.currentModel.layoutChanged.emit()


class CommandRevCmp(QUndoCommand):
    # 反向、互补的撤销恢复
    def __init__(self, tableView, currentModel, list_rows, mode, description):
        super(CommandRevCmp, self).__init__(description)
        self.tableView = tableView
        self.list_rows = list_rows
        self.currentModel = currentModel
        self.mode = mode

    def reverse_Complement(self, list_seq):
        dict1 = {"A": "T", "T": "A", "C": "G", "G": "C"}
        list_comp_seq = []
        for i in list_seq:
            if i.upper() in dict1:
                list_comp_seq.append(dict1[i.upper()])
            else:
                list_comp_seq.append(i.upper())
        return list(reversed(list_comp_seq))

    def reverse(self, list_seq):
        return list(reversed(list_seq))

    def Complement(self, list_seq):
        dict1 = {"A": "T", "T": "A", "C": "G", "G": "C"}
        list_comp_seq = []
        for i in list_seq:
            if i.upper() in dict1:
                list_comp_seq.append(dict1[i.upper()])
            else:
                list_comp_seq.append(i.upper())
        return list_comp_seq

    def redo(self):
        currentData = self.currentModel.arraydata
        self.list_mode_rows = [self.mode, self.list_rows]
        for row in self.list_rows:
            if self.mode == "Reverse Complement":
                currentData[row][1:] = self.reverse_Complement(currentData[row][1:])
            elif self.mode == "Reverse":
                currentData[row][1:] = self.reverse(currentData[row][1:])
            elif self.mode == "Complement":
                currentData[row][1:] = self.Complement(currentData[row][1:])
        self.currentModel.layoutChanged.emit()

    def undo(self):
        currentData = self.currentModel.arraydata
        for row in self.list_mode_rows[1]:
            if self.mode == "Reverse Complement":
                currentData[row][1:] = self.reverse_Complement(currentData[row][1:])
            elif self.mode == "Reverse":
                currentData[row][1:] = self.reverse(currentData[row][1:])
            elif self.mode == "Complement":
                currentData[row][1:] = self.Complement(currentData[row][1:])
        self.currentModel.layoutChanged.emit()

class CommandPaste(QUndoCommand):
    '''#粘贴序列的撤销恢复
    1）如果用户只选了1个碱基，那么在这个碱基的位置插入
    2）如果用户选择了多个碱基，那么删掉这个碱基，然后在该位置插入序列
    3）如果粘贴的内容有多行，超出的行就不粘贴'''
    def __init__(self, tableView, currentModel, indices, description=None):
        super(CommandPaste, self).__init__(description)
        self.tableView = tableView
        self.indices = indices
        self.currentModel = currentModel
        self.dict_coord_value = OrderedDict()  # 记录被删除的坐标，及其对应的值,delete函数的

    def delete(self):
        currentData = self.currentModel.arraydata
        dict_row_cols = OrderedDict()
        for i in self.indices:
            col = i.column()
            row = i.row()
            dict_row_cols.setdefault(row, []).append(col)
        rows = sorted(list(dict_row_cols.keys()), reverse=True)  # 从大到小
        for row in rows:
            # 从每一列的最右边开始删
            cols = sorted(dict_row_cols[row], reverse=True)
            for col in cols:
                self.dict_coord_value[(row, col)] = currentData[row].pop(col)
        self.currentModel.complementArray()
        self.currentModel.layoutChanged.emit()

    def redo(self):
        self.list_row_col_len = []  #记录哪一行，第几列开始新加了多少列的东西
        text = QApplication.clipboard().text()
        text_array = [list(i) for i in text.split("\n")]
        max_len = len(max(text_array, key=len))
        text_array = [j + ["-"] * (max_len - len(j)) for j in text_array]  #[['C', 'T', 'C', 'T', 'C'], ['A', 'A', 'T', 'G', 'A'], ['C', 'C', 'T', 'T', '-']]
        currentData = self.currentModel.arraydata
        if len(self.indices) == 1:  #只选择了1个点
            row = self.indices[0].row()
            column = self.indices[0].column()
            for num, list_text in enumerate(text_array):
                if (row + num + 1) <= len(currentData):
                    #大于了的不添加
                    currentData[row + num][column:column] = list_text
                    self.list_row_col_len.append([row+num, column, len(list_text)])
            self.currentModel.complementArray()
        else:
            #先删除，再添加
            self.delete()  # self.dict_coord_value记录了删除过程
            ##选中的比添加的少，下面的右移；如果选中的比添加的多，删除所有选中的，然后添加
            sorted_selectedIndice = sorted(self.indices, key=lambda x: (x.row(), x.column())) #按行与列从小到大排列
            initial_row = sorted_selectedIndice[0].row()
            initial_column = sorted_selectedIndice[0].column()
            for num, list_text in enumerate(text_array):
                if (initial_row + num + 1) <= len(currentData):
                    currentData[initial_row + num][initial_column:initial_column] = list_text
                    self.list_row_col_len.append([initial_row + num, initial_column, len(list_text)])
            self.currentModel.complementArray()
        self.currentModel.layoutChanged.emit()

    def undo(self):
        array = self.currentModel.arraydata
        if self.dict_coord_value:
            #先删除，再添加的模式
            for i in self.list_row_col_len:
                array[i[0]][i[1]:i[1]+i[2]] = []
            if self.dict_coord_value:
                for coord in sorted(self.dict_coord_value):
                    array[coord[0]].insert(coord[1], self.dict_coord_value[coord])
            self.currentModel.complementArray()
            self.currentModel.makeColHeader()
        else:
            #直接添加模式
            for i in self.list_row_col_len:
                array[i[0]][i[1]:i[1] + i[2]] = []
            self.currentModel.complementArray()
            self.currentModel.makeColHeader()
        self.currentModel.layoutChanged.emit()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    ui = Seq_viewer()
    ui.show()
    sys.exit(app.exec_())