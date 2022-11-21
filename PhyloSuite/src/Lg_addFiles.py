#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
description goes here
'''
import platform
import re
import sys
import traceback
from Bio import Entrez
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from src.factory import Factory, WorkThread
import inspect
import os
from uifiles.Ui_addFile import Ui_addFile


class Lg_addFiles(QDialog, Ui_addFile, object):
    closeGUI_signal = pyqtSignal()
    inputSig = pyqtSignal(list, list, bool, str)
    inputContentSig = pyqtSignal(str, str)
    exception_signal = pyqtSignal(str)
    progressDiologSig = pyqtSignal(int)
    fastaDownloadFinishedSig = pyqtSignal(str)
    inputFasSig = pyqtSignal(str, str)

    def __init__(self, exportPath=None, parent=None):
        super(Lg_addFiles, self).__init__(parent)
        self.factory = Factory()
        self.parent = parent
        self.thisPath = self.factory.thisPath
        self.exportPath = exportPath
        # 保存设置
        self.addFiles_settings = QSettings(
            self.thisPath +
            '/settings/addFiles_settings.ini',
            QSettings.IniFormat)
        self.closeGUI_signal.connect(self.close)
        self.progressDiologSig.connect(self.runProgressDialog)
        # self.close() 不能在信号槽里面
        self.fastaDownloadFinishedSig.connect(self.parent.setTreeViewFocus)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.setupUi(self)
        self.guiRestore()
        self.exception_signal.connect(self.popupException)
        self.interrupt = False
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#4-3-1-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#4-3-1-1-Brief-example"
        self.label_3.clicked.connect(lambda : QDesktopServices.openUrl(QUrl(url)))

    def fetSeqFromNCBI(self, id_array):
        batch_size = 20
        count = len(id_array)
        download_contents = ""
        for start in range(0, count, batch_size):
            if self.interrupt:
                return
            end = min(count, start + batch_size)
            print("Going to download record %i to %i" % (start + 1, end))
            if (start + batch_size) > count:
                batch_size = count - start
            Entrez.email = self.email if self.email else "A.N.Other@example.com"
            fetch_handle = Entrez.efetch(db=self.db, rettype=self.rettype, retmode="text",
                                         retstart=start, retmax=batch_size, id=id_array)
            download_contents += fetch_handle.read()
            self.progressDiologSig.emit(end * 100 / count)
        if self.rettype == "gb":
            self.inputContentSig.emit(
                download_contents, self.outputPath)
        else:
            with open(self.outputPath + os.sep + self.fasta_file_name, "w", encoding="utf-8") as f:
                f.write(download_contents)
            self.fastaDownloadFinishedSig.emit(self.outputPath)
        # result_handle = Entrez.efetch(
        #     db="nucleotide", rettype="gb",  id=id_array, retmode="text")
        # # with open(self.exportPath + os.sep + "new.gb", "w", encoding="utf-8") as f2:
        # #     f2.write(result_handle.read())
        # self.inputContentSig.emit(
        #     result_handle.read(), [])

    @pyqtSlot()
    def on_pushButton_clicked(self):
        self.outputPath = self.fetchOutputPath()
        if self.parent.isWorkFolder(self.outputPath, mode="gb"):
            files = QFileDialog.getOpenFileNames(
                self, "Input GenBank Files", filter="GenBank and Fasta Format (*.gb *.gbk *.gbf *.gp *.gbff *.fas *.fasta);;")
            if files[0]:
                list_gbs = []
                list_fas = []
                for i in files[0]:
                    if os.path.splitext(i)[1].upper() in [".GB", ".GBK", ".GP", ".GBF", ".GBFF"]:
                        list_gbs.append(i)
                    elif os.path.splitext(i)[1].upper() in [".FAS", ".FASTA"]:
                        list_fas.append(i)
                if list_gbs:
                    self.inputSig.emit(list_gbs, [], False, self.outputPath)
                if list_fas:
                    fasContent = ""
                    for i in list_fas:
                        with open(i, encoding="utf-8", errors='ignore') as f:
                            fasContent += f.read() + "\n"
                    self.inputFasSig.emit(fasContent, self.outputPath)
                self.close()
                self.deleteLater()
                del self
        else:
            files = QFileDialog.getOpenFileNames(
                self, "Input Files",
                filter="Supported Format (*.docx *.doc *.odt *.docm *.dotx *.dotm *.dot "
                       "*.fas *.fasta *.phy *.phylip *.nex *.nxs *.nexus);;")
            if files[0]:
                self.inputSig.emit([], files[0], False, self.outputPath)
                self.close()
                self.deleteLater()
                del self

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        # download
        self.interrupt = False
        text_content = self.plainTextEdit.toPlainText()
        if text_content:
            self.outputPath = self.fetchOutputPath()
            self.db = self.comboBox_2.currentText()
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
            self.downloadState("start")
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "Downloading...", parent=self)
            self.progressDialog.show()
            self.id_array = re.split(r"\s|,", text_content)
            while "" in self.id_array:
                self.id_array.remove("")
            self.email = self.lineEdit.text()
            self.worker_download = WorkThread(self.run_command, parent=self)
            self.progressDialog.canceled.connect(lambda: [setattr(self, "interrupt", True),
                                                          self.worker_download.stopWork(),
                                                          self.progressDialog.close(),
                                                          self.downloadState("stop")])
            self.worker_download.start()
        else:
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please input ID(s) first</p>")

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        #search in NCBI
        self.close()
        self.parent.on_SerhNCBI_triggered()

    @pyqtSlot()
    def on_toolButton_clicked(self):
        info = '''To make use of NCBI's E-utilities, NCBI requires you to specify your email address with each request.<br> 
In case of excessive usage of the E-utilities, NCBI will attempt to contact a user at the email address provided before blocking access to the E-utilities.'''
        QMessageBox.information(
            self,
            "Information",
            "<p style='line-height:25px; height:25px'>%s</p>"%info)

    def run_command(self):
        try:
            self.fetSeqFromNCBI(self.id_array)
            self.closeGUI_signal.emit()
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)
            # self.popupException(self.exceptionInfo)  # 激发这个信号

    def popupException(self, exception):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        self.pushButton_2.setEnabled(True)
        self.pushButton_2.setStyleSheet(self.qss_file)
        self.pushButton_2.setText("Start")

    def guiSave(self):
        # Save geometry
        self.addFiles_settings.setValue('size', self.size())
        # self.addFiles_settings.setValue('pos', self.pos())

        # for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            # if isinstance(obj, QTextBrowser):
            #     # save combobox selection to registry
            #     htmlText = obj.toHtml()
            #     self.addFiles_settings.setValue(name, htmlText)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.factory.judgeWindowSize(self.addFiles_settings, 620, 500))
        self.factory.centerWindow(self)
        # self.move(self.addFiles_settings.value('pos', QPoint(875, 254)))
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox":
                    allItems = self.factory.fetchAllWorkFolders(self.exportPath)
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(allItems):
                        if self.parent.isWorkFolder(i, mode="gb"):
                            text = "\"%s\" in GenBank_File (GenBank format)"%os.path.basename(i)
                        else:
                            text = "\"%s\" in Other_File" % os.path.basename(i)
                        item = QStandardItem(text)
                        item.setToolTip(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    if self.parent.isWorkFolder(self.exportPath, mode="gb"):
                        obj.setCurrentText("\"%s\" in GenBank_File (GenBank format)"%os.path.basename(self.exportPath))
                    else:
                        obj.setCurrentText("\"%s\" in Other_File" % os.path.basename(self.exportPath))

    def closeEvent(self, event):
        self.interrupt = True
        if hasattr(self, "worker_download"):
            self.worker_download.stopWork()
        if hasattr(self, "progressDialog"):
            self.progressDialog.close()
        self.guiSave()

    def runProgressDialog(self, num):
        oldValue = self.progressDialog.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressDialog.setProperty("value", done_int)
            QCoreApplication.processEvents()
            if done_int == 100:
                self.progressDialog.close()

    def fetchOutputPath(self):
        index = self.comboBox.currentIndex()
        return self.comboBox.itemData(index, role=Qt.ToolTipRole)

    def downloadState(self, state):
        if state == "start":
            self.pushButton_2.setEnabled(False)  # 使之失效
            self.pushButton_2.setStyleSheet(
                'QPushButton {color: red; background-color: rgb(219, 217, 217)}')
            self.pushButton_2.setText("Downloading...")
        elif state == "stop":
            self.pushButton_2.setText("Download")
            self.pushButton_2.setStyleSheet(self.qss_file)
            self.pushButton_2.setEnabled(True)