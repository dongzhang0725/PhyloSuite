#!/usr/bin/env python
# -*- coding: utf-8 -*-

import traceback

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.CustomWidget import MyNCBITableModel, CheckBoxHeader
from src.factory import Factory, WorkThread
from uifiles.Ui_NCBI import Ui_SerhNCBI
import inspect
import os
import sys
from Bio import Entrez


class SerhNCBI(QMainWindow, Ui_SerhNCBI, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    updateSig = pyqtSignal(list)
    searchSig = pyqtSignal(str)
    progressBarSig = pyqtSignal(int)  # 控制进度条
    progressDiologSig = pyqtSignal(int)
    ctrlItemsSig = pyqtSignal(int)
    inputContentSig = pyqtSignal(str, str)
    downloadFinished = pyqtSignal()
    fastaDownloadFinishedSig = pyqtSignal(str)

    def __init__(
            self,
            workPath=None,
            parent=None):
        super(SerhNCBI, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.parent = parent
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.setupUi(self)
        # 保存设置
        self.serhNCBI_settings = QSettings(
            self.thisPath +
            '/settings/serhNCBI_settings.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.serhNCBI_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        self.exception_signal.connect(self.popupException)
        # self.progressSig.connect(self.runProgress)
        # self.logGuiSig.connect(self.addText2Log)
        self.lineEdit.buttonSearch.clicked.connect(lambda : [self.startSearch(), self.sync_completer_texts(self.lineEdit.text())])
        self.lineEdit.buttonStop.clicked.connect(self.stopSearch)
        # self.lineEdit.completer().popup().show()
        # self.lineEdit.clicked.connect(lambda : self.lineEdit.completer().popup())
        self.dict_ncbi_headers = {
            "GBSeq_accession-version": "ID",
            "GBSeq_definition": "Description",
            "GBSeq_organism": "Organism",
            "GBSeq_length": "Length",
            "GBSeq_update-date": "Update date",
            "GBSeq_taxonomy": "Taxonomy",
            "GBSeq_create-date": "Create date",
            "GBSeq_moltype": "Molecular type",
            "GBSeq_topology": "Topology",
            "GBSeq_references": "References",
            "GBSeq_source": "Source",
            "GBSeq_keywords": "Keywords",
            "GBSeq_project": "Project",
            "GBSeq_other-seqids": "Other IDs",
            "GBSeq_strandedness": "Strandedness",
            "GBSeq_comment": "Comments"
        }
        self.init_list()
        self.updateSig.connect(self.updateTable)
        self.searchSig.connect(self.ctrlSearchState)
        self.progressBarSig.connect(self.searchProgress)
        self.progressDiologSig.connect(self.runProgressDialog)
        self.spinBox.valueChanged.connect(self.sync_display_items)
        self.ctrlItemsSig.connect(self.ctrlItems)
        # self.downloadFinished.connect(self.downloadDone)
        self.fastaDownloadFinishedSig.connect(self.parent.setTreeViewFocus)
        self.NCBI_model = MyNCBITableModel([self.list_table_header], parent=self)
        self.tableView.setModel(self.NCBI_model)
        header = CheckBoxHeader(parent=self.tableView)
        header.clicked.connect(self.check_displayed)
        self.tableView.setHorizontalHeader(header)
        self.NCBI_model.checkedChanged.connect(self.ctrl_text)
        self.interrupt = False
        ##下载的状态
        widget = QWidget(self)
        horizBox = QHBoxLayout(widget)
        horizBox.setContentsMargins(0, 0, 0, 0)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.disp_check_label = QLabel("<span style='font-weight:600; color:red;'>Searching...</span>",
                                       self)
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
        self.lineEdit.installEventFilter(self)
        self.spinBox.installEventFilter(self)
        table_popMenu = QMenu(self)
        table_popMenu.setToolTipsVisible(True)
        OpenID = QAction(QIcon(":/seq_Viewer/resourses/field-Display.png"), "Open in NCBI webpage", self,
                         triggered=self.openID)
        OpenID.setToolTip("Open sequence in NCBI webpage")
        table_popMenu.addAction(OpenID)
        def table_popmenu(qpoint):
            if self.tableView.indexAt(qpoint).isValid():
                table_popMenu.exec_(QCursor.pos())
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(table_popmenu)
        # self.tableView.horizontalHeader().resizeSection(1, 300)
        # self.tableView.horizontalHeader().resizeSection(2, 80)
        # ##增加check按钮
        # self.check_all = QCheckBox("Check/Uncheck", self)
        # self.check_all.toggled.connect(self.check_displayed)
        # self.statusbar.addWidget(self.check_all)
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#4-3-3-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#4-3-3-1-Brief-example"
        self.label_6.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

    @pyqtSlot()
    def on_toolButton_clicked(self):
        info = '''To make use of NCBI's E-utilities, NCBI requires you to specify your email address with each request.<br> 
In case of excessive usage of the E-utilities, NCBI will attempt to contact a user at the email address provided before blocking access to the E-utilities.'''
        QMessageBox.information(
            self,
            "Information",
            "<p style='line-height:25px; height:25px'>%s</p>" % info)

    @pyqtSlot()
    def on_toolButton_2_clicked(self):
        #refresh
        self.interrupt = False
        self.exist_base = self.NCBI_model.rowCount(self.tableView)
        if not self.exist_base:
            return
        if hasattr(self, "worker_addition") and self.worker_addition.isRunning():
            return
        if self.display_items > self.exist_base:
            self.worker_addition = WorkThread(self.addition_search, parent=self)
            self.worker_addition.start()
        # elif self.display_items < self.exist_base:
        #     list_checked = self.NCBI_model.list_checked
        #     array = self.NCBI_model.array[:self.display_items+1]
        #     self.NCBI_model = MyNCBITableModel(array, list_checked, self.tableView)
        #     self.tableView.setModel(self.NCBI_model)
        #     self.tableView.update()

    @pyqtSlot()
    def on_toolButton_3_clicked(self):
        # download
        index = self.comboBox.currentIndex()
        self.outputPath = self.comboBox.itemData(index, role=Qt.ToolTipRole)
        self.rettype = "gb" if self.parent.isWorkFolder(self.outputPath, mode="gb") else "fasta"
        if self.rettype == "fasta":
            name, ok = QInputDialog.getText(
                self, 'Set output file name', 'Output file name:', text="sequence.fas")
            if ok:
                self.fasta_file_name = name + ".fas" if "." not in name else name
                if os.path.exists(self.outputPath + os.sep + self.fasta_file_name):
                    reply = QMessageBox.question(
                        self,
                        "Concatenate sequence",
                        "<p style='line-height:25px; height:25px'>The file exists, replace it?</p>",
                        QMessageBox.Yes,
                        QMessageBox.Cancel)
                    if reply == QMessageBox.Cancel:
                        return
            else:
                QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Download canceled!</p>")
                return
        if self.NCBI_model.arraydata:
            self.interrupt = False
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "Downloading...", parent=self)
            self.progressDialog.show()
            self.worker_download = WorkThread(self.downloadSeq, parent=self)
            self.progressDialog.canceled.connect(lambda : [setattr(self, "interrupt", True),
                                                 self.worker_download.stopWork(), self.progressDialog.close()])
            self.worker_download.finished.connect(self.downloadDone)
            self.worker_download.start()
        else:
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please search first!</p>")

    def downloadSeq(self):
        try:
            checked_ids = self.NCBI_model.list_checked
            # if not checked_ids:
            #     checked_ids = self.NCBI_model.fetchAllIDs()
            batch_size = 20
            count = len(checked_ids) if checked_ids else self.count
            self.download_contents = ""
            for start in range(0, count, batch_size):
                if self.interrupt:
                    return
                end = min(count, start + batch_size)
                print("Going to download record %i to %i" % (start + 1, end))
                if (start + batch_size) > count:
                    batch_size = count - start
                if not checked_ids:
                    #下载所有序列的模式
                    fetch_handle = Entrez.efetch(db=self.database, rettype=self.rettype, retmode="text",
                                                 retstart=start, retmax=batch_size,
                                                 webenv=self.webenv, query_key=self.query_key)
                else:
                    fetch_handle = Entrez.efetch(db=self.database, rettype=self.rettype, retmode="text",
                                             retstart=start, retmax=batch_size, id=checked_ids)
                self.download_contents += fetch_handle.read()
                self.progressDiologSig.emit(end * 100 / count)
            # index = self.comboBox.currentIndex()
            # filepath = self.comboBox.itemData(index, role=Qt.ToolTipRole)
            # self.downloadFinished.emit()
        except:
            self.exception_signal.emit(''.join(
                traceback.format_exception(
                    *sys.exc_info())))

    def downloadDone(self):
        self.progressDialog.close()
        QMessageBox.information(
            self,
            "Download finished",
            "<p style='line-height:25px; height:25px'>Done! Back to home page to view them.</p>")
        if self.rettype == "gb":
            self.inputContentSig.emit(
                self.download_contents, self.outputPath)
        else:
            with open(self.outputPath + os.sep + self.fasta_file_name, "w", encoding="utf-8") as f:
                f.write(self.download_contents)
            self.fastaDownloadFinishedSig.emit(self.outputPath)

    def startSearch(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            return
        if self.spinBox.value() == 0:
            self.spinBox.setValue(20)
        if self.lineEdit.text():
            self.interrupt = False
            self.NCBI_model.init_table() #刷新一下table（归零）
            self.worker = WorkThread(self.search, parent=self)
            self.worker.start()
        else:
            QMessageBox.information(
                self,
                "Search in NCBI",
                "<p style='line-height:25px; height:25px'>Please input keywords first!</p>")

    def guiSave(self):
        # Save geometry
        self.serhNCBI_settings.setValue('size', self.size())
        # self.serhNCBI_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            # if isinstance(obj, QComboBox):
            #     # save combobox selection to registry
            #     text = obj.currentText()
            #     if text:
            #         allItems = [
            #             obj.itemText(i) for i in range(obj.count())]
            #         allItems.remove(text)
            #         sortItems = [text] + allItems
            #         self.serhNCBI_settings.setValue(name, sortItems)
            if isinstance(obj, QLineEdit):
                if name == "lineEdit":
                    self.serhNCBI_settings.setValue(name, self.completer_texts)
            if isinstance(obj, QSpinBox):
                if name == "spinBox":
                    self.serhNCBI_settings.setValue(name, self.display_items)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.serhNCBI_settings.value('size', QSize(1000, 600)))
        self.factory.centerWindow(self)
        # self.move(self.serhNCBI_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox":
                    allItems = self.factory.fetchAllWorkFolders(self.workPath)
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(allItems):
                        if self.parent.isWorkFolder(i, mode="gb"):
                            text = "\"%s\" in GenBank_File (GenBank format)"%os.path.basename(i)
                        else:
                            text = "\"%s\" in Other_File (Fasta format)" % os.path.basename(i)
                        item = QStandardItem(text)
                        item.setToolTip(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    # obj.setCurrentText(os.path.basename(self.workPath))
                    if self.parent.isWorkFolder(self.workPath, mode="gb"):
                        obj.setCurrentText("\"%s\" in GenBank_File (GenBank format)"%os.path.basename(self.workPath))
                    else:
                        obj.setCurrentText("\"%s\" in Other_File (Fasta format)" % os.path.basename(self.workPath))
            if isinstance(obj, QLineEdit):
                if name == "lineEdit":
                    self.completer_texts = self.serhNCBI_settings.value(
                        name, ["Monogenea[ORGN] AND (mitochondrion[TITL] OR mitochondrial[TITL]) AND 10000:50000[SLEN]"])  # get stored value from registry
                    if not self.completer_texts: # avoid trouble
                        self.completer_texts = ["Monogenea[ORGN] AND (mitochondrion[TITL] OR mitochondrial[TITL]) AND 10000:50000[SLEN]"]
                    self.setLCompleter()
            if isinstance(obj, QSpinBox):
                if name == "spinBox":
                    self.display_items = int(self.serhNCBI_settings.value(
                        name, 100))  # get stored value from registry
                    obj.setValue(self.display_items)

    def runProgressDialog(self, num):
        oldValue = self.progressDialog.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressDialog.setProperty("value", done_int)
            QCoreApplication.processEvents()
            if done_int == 100:
                self.progressDialog.close()

    def popupException(self, exception):
        if ("getaddrinfo failed" in exception) or ("RuntimeError" in exception):
            text = "<p style='line-height:25px; height:25px'>Search failed, try to check your network connection!</p>"
        else:
            text = "<p style='line-height:25px; height:25px'>The search failed for some of the sequences. As this may have been  caused by a network problem, you can wait for a while and try again.<br> If the problem persists you may report it at " \
                   "<a href=\"https://github.com/dongzhang0725/PhyloSuite/issues\">https://github.com/dongzhang0725/PhyloSuite/issues</a> " \
                   "or send an email with the detailed traceback to dongzhang0725@gmail.com</p>"
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(text)
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def closeEvent(self, event):
        self.interrupt = True
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stopWork()
        if hasattr(self, "worker_addition") and self.worker_addition.isRunning():
            self.worker_addition.stopWork()
        if hasattr(self, "worker_download") and self.worker_download.isRunning():
            self.worker_download.stopWork()
        if hasattr(self, "progressDialog"):
            self.progressDialog.close()
        self.guiSave()
        # self.log_gui.close()  # 关闭子窗口

    def eventFilter(self, obj, event):
        name = obj.objectName()
        if event.type() == QEvent.KeyPress:  # 首先得判断type
            if event.key() == Qt.Key_Return:
                if name == "lineEdit":
                    self.sync_completer_texts(self.lineEdit.text())
                    self.startSearch()
                    return True
                if name == "spinBox":
                    self.on_toolButton_2_clicked()
                    return True
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(SerhNCBI, self).eventFilter(obj, event)  # 0

    def sync_completer_texts(self, text):
        if text and (text not in self.completer_texts):
            self.completer_texts.insert(0, text)
        if len(self.completer_texts) > 15:
            self.completer_texts = self.completer_texts[:15]
        self.guiSave()
        self.setLCompleter()

    def setLCompleter(self):
        comp = QCompleter(self.completer_texts)
        comp.setFilterMode(Qt.MatchContains)
        comp.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        # comp.popup().setStyleSheet("background-color: yellow")
        self.lineEdit.setCompleter(comp)

    def init_list(self):
        self.list_table_header = ["ID", "Description", "Organism", "Length", "Update date", "Taxonomy", "Create date",
                            "Molecular type", "Topology", "References", "Source", "Keywords", "Project", "Other IDs",
                            "Strandedness", "Comments"]

    def updateTable(self, list_):
        # print(array)
        # 测试array是新添加的list
        self.NCBI_model.appendTable(list_)

    def ctrlSearchState(self, state):
        if state == "searching":
            self.disp_check_label.setText("Searching...")
            self.disp_check_label.setVisible(True)
            self.disp_check_gifLabel.setVisible(True)
            self.lineEdit.buttonSearch.setDisabled(True)
            self.lineEdit.buttonStop.setDisabled(False)
            self.toolButton_2.setDisabled(True)
            self.toolButton_3.setDisabled(True)
        elif state == "fetching":
            self.disp_check_label.setText("Fetching...")
            self.disp_check_label.setVisible(True)
            self.disp_check_gifLabel.setVisible(True)
            self.disp_check_progress.setValue(0)
            self.disp_check_progress.setVisible(True)
            self.lineEdit.buttonStop.setDisabled(False)
        elif state == "except":
            self.disp_check_label.setVisible(False)
            self.disp_check_gifLabel.setVisible(False)
            self.disp_check_progress.setVisible(False)
            self.lineEdit.buttonSearch.setDisabled(False)
            self.lineEdit.buttonStop.setDisabled(True)
            self.toolButton_2.setDisabled(False)
            self.toolButton_3.setDisabled(False)
        elif state == "finished":
            self.disp_check_label.setVisible(False)
            self.disp_check_gifLabel.setVisible(False)
            self.disp_check_progress.setVisible(False)
            self.lineEdit.buttonSearch.setDisabled(False)
            self.lineEdit.buttonStop.setDisabled(True)
            self.toolButton_2.setDisabled(False)
            self.toolButton_3.setDisabled(False)
            ##如果啥也没搜到
            self.exist_base = self.NCBI_model.rowCount(self.tableView)
            if not self.exist_base:
                QMessageBox.information(
                    self,
                    "Download finished",
                    "<p style='line-height:25px; height:25px'>No items found!</p>")

    def ctrlItems(self, count):
        count = count if count != 0 else 20
        self.spinBox.setMaximum(count)
        if count == 0:
            self.spinBox.setValue(20)
        self.label_4.setText("items of %s (total)" % count)
        self.label_2.setText("Download all (%s) sequences to:"%count)
        # if count < self.display_items:
        #     self.display_items = count
        #     self.spinBox.setValue(count)

    def searchProgress(self, value):
        oldValue = self.disp_check_progress.value()
        done_int = int(value)
        if done_int > oldValue:
            self.disp_check_progress.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def sync_display_items(self, value):
        self.display_items = value

    def search(self):
        try:
            self.searchSig.emit("searching")
            self.init_list()
            self.ctrl_text() #文本还原
            self.NCBI_model.list_checked = []
            self.database = self.comboBox_2.currentText()
            keywords = self.lineEdit.text()
            email = self.lineEdit_2.text()
            email = email if email else "A.N.Other@example.com"
            Entrez.email = email
            search_handle = Entrez.esearch(db=self.database,term=keywords,
                                       usehistory="y")
            search_results = Entrez.read(search_handle)
            self.webenv = search_results["WebEnv"]
            self.query_key = search_results["QueryKey"]
            self.count = int(search_results["Count"])
            self.ctrlItemsSig.emit(self.count) #如果只有2个序列，self.display_items也会变成2
            search_handle.close()
            batch_size = 20
            self.searchSig.emit("fetching")
            # time_start = time.time()
            total_displayed = self.display_items
            if self.count < total_displayed:
                total_displayed = self.count
            for start in range(0, total_displayed, batch_size):
                # try:
                if self.interrupt:
                    return
                end = min(total_displayed, start + batch_size)
                print("Going to download record %i to %i" % (start + 1, end))
                if (start + batch_size) > total_displayed:
                    batch_size = total_displayed - start
                fetch_handle = Entrez.efetch(db=self.database, retmode="xml",
                                             retstart=start, retmax=batch_size,
                                             webenv=self.webenv, query_key=self.query_key)
                fetch_records = Entrez.read(fetch_handle)
                for num, record in enumerate(fetch_records):
                    list_ = []
                    for i in ["GBSeq_accession-version", "GBSeq_definition", "GBSeq_organism", "GBSeq_length",
                              "GBSeq_update-date",
                              "GBSeq_taxonomy", "GBSeq_create-date", "GBSeq_moltype", "GBSeq_topology", "GBSeq_references",
                              "GBSeq_source", "GBSeq_keywords", "GBSeq_project", "GBSeq_other-seqids", "GBSeq_strandedness",
                              "GBSeq_comment"]:
                        if i in record:
                            list_.append(str(record[i]))
                        else:
                            list_.append("N/A")
                    self.updateSig.emit(list_)
                    self.progressBarSig.emit((start + num + 1) * 100 / total_displayed)
                fetch_handle.close()
                # except:
                #     pass
            self.searchSig.emit("finished")
        except:
            self.searchSig.emit("except")
            self.exception_signal.emit(''.join(
                traceback.format_exception(
                    *sys.exc_info())))
        # time_end = time.time()
        # print("time:", time_end - time_start)

    def addition_search(self):
        try:
            total_displayed = self.display_items
            if self.count < total_displayed:
                total_displayed = self.count
            batch_size = 20
            self.searchSig.emit("fetching")
            for start in range(self.exist_base, total_displayed, batch_size):
                if self.interrupt:
                    break
                end = min(total_displayed, start + batch_size)
                print("Going to download record %i to %i" % (start + 1, end))
                if (start + batch_size) > total_displayed:
                    batch_size = total_displayed - start
                fetch_handle = Entrez.efetch(db=self.database, retmode="xml",
                                             retstart=start, retmax=batch_size,
                                             webenv=self.webenv, query_key=self.query_key)
                fetch_records = Entrez.read(fetch_handle)
                for num, record in enumerate(fetch_records):
                    list_ = []
                    for i in ["GBSeq_accession-version", "GBSeq_definition", "GBSeq_organism", "GBSeq_length",
                              "GBSeq_update-date",
                              "GBSeq_taxonomy", "GBSeq_create-date", "GBSeq_moltype", "GBSeq_topology", "GBSeq_references",
                              "GBSeq_source", "GBSeq_keywords", "GBSeq_project", "GBSeq_other-seqids", "GBSeq_strandedness",
                              "GBSeq_comment"]:
                        if i in record:
                            list_.append(str(record[i]))
                        else:
                            list_.append("N/A")
                    self.updateSig.emit(list_)
                    self.progressBarSig.emit((start - self.exist_base + num + 1) * 100 / (total_displayed - self.exist_base))
                # self.progressBarSig.emit((start - self.exist_base)*100/(total_displayed - self.exist_base))
                fetch_handle.close()
            self.searchSig.emit("finished")
        except:
            self.searchSig.emit("except")
            self.exception_signal.emit(''.join(
                traceback.format_exception(
                    *sys.exc_info())))

    def ctrl_text(self):
        selected_num = len(self.NCBI_model.list_checked)
        if selected_num:
            self.label_2.setText("Download selected (%d) sequences to:"%(selected_num))
        else:
            text = "Download all (%d) sequences to:"%self.count if hasattr(self, "count") else "Download all sequences to:"
            self.label_2.setText(text)

    def openID(self):
        indices = self.tableView.selectedIndexes()
        arraydata = self.NCBI_model.arraydata
        ID = arraydata[indices[0].row()][0].text()
        url = "https://www.ncbi.nlm.nih.gov/nuccore/%s"%ID if self.comboBox_2.currentText() == "nucleotide" \
            else "https://www.ncbi.nlm.nih.gov/protein/%s"%ID
        QDesktopServices.openUrl(QUrl(url))

    def stopSearch(self):
        self.interrupt = True
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stopWork()
        if hasattr(self, "worker_addition") and self.worker_addition.isRunning():
            self.worker_addition.stopWork()
        self.searchSig.emit("except")


    def check_displayed(self, isCheck):
        if hasattr(self, "NCBI_model") and self.NCBI_model.rowCount(self.tableView):
            # self.NCBI_model.beginResetModel()
            self.NCBI_model.layoutAboutToBeChanged.emit()
            if isCheck:
                self.NCBI_model.list_checked = [i[0].text() for i in self.NCBI_model.arraydata]
            else:
                self.NCBI_model.list_checked = []
            self.NCBI_model.layoutChanged.emit()
            self.ctrl_text()
            # self.NCBI_model.endResetModel()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = SerhNCBI()
    ui.show()
    sys.exit(app.exec_())