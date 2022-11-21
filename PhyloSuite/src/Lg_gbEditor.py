#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import inspect
from io import StringIO
from Bio import SeqIO
from src.CustomWidget import ListItemsOption, MyTableModel
from src.Lg_extractSettings import ExtractSettings
from uifiles.Ui_gbEditor import Ui_GBeditor
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import os
import re
import traceback
import sys
from src.handleGB import Normalize_MT, GbManager, ArrayManager
from src.factory import Factory, WorkThread, Find
from uifiles.Ui_tRNA_reANNT import Ui_tRNA_ANNT


class ReANNT(object):

    def __init__(self, arwenResults, gbContent, totaltRNA, progressSig):
        self.arwenResults = arwenResults
        self.gbContent = gbContent
        self.totaltRNA = totaltRNA
        self.progressSig = progressSig
        self.parseArwen()
#         self.saveFile()

    def recogniseLS(self, list_antiCodon):
        dict_SL = {"TAG": "L1",
                   "TAA": "L2",
                   "GCT": "S1",
                   "TCT": "S1",
                   "TGA": "S2",
                   "AAG": "L1",
                   "AGA": "S2",
                   }
        value = False
        for i in list_antiCodon:
            key = i.upper()
            if key in list(dict_SL.keys()):
                value = dict_SL[key]
                break
        return value

    def parseArwen(self):
        rgx_filter = re.compile(
            r"(?is)(\w+?[a-z]{2}_?\d{6}_(complement_)?(\d+)__(\d+)_?).+?Nothing found in \1")
        tail = re.search(
            r"(?is)\w+?[a-z]{2}_?\d{6}_(complement_)?(\d+)__(\d+)_?", self.arwenResults).group()
        # 过滤掉没有预测成功的结果，Nothing found in;并增加一个物种当尾巴，方便识别
        self.arwenResults = rgx_filter.sub(
            "", self.arwenResults) + "\n" + tail + "\n"
        # 先找出每个物种的预测结果
        # group 1，2是起始、终止位置，group 3是反密码子
        rgx_arwen = re.compile(
            r"(?is)([a-z]{2}_?\d{6})_(complement_)?(\d+)__(\d+).+?[a-z]{2}_?\d{6}_(complement_)?\d+__\d+")
        # 然后找到所有预测到的反密码子
        rgx_antiCondon = re.compile(r"mtRNA-.+?\(([a-z]{3})\)\s+?\d+ bases")
        ini_pos = 0
        num = 0
        while rgx_arwen.search(self.arwenResults, ini_pos):
            match = rgx_arwen.search(self.arwenResults, ini_pos)
            gb_num, start, end, group, ini_pos = match.group(1), match.group(3), match.group(
                4), match.group(), match.span()[0] + 80
            list_antiCodon = rgx_antiCondon.findall(group)
#             找出是否能给S和L编号
            numbered = self.recogniseLS(list_antiCodon)
#             登录号也一起放进去用于识别，但是会使速度变慢
            # 这里把\w+换成了[^\n]
            rgx_gb = re.compile(
                r"(?si)(LOCUS {7}%s.+?tRNA {12}(complement\()?%s\.\.%s(\))?.+?/product=\")[^\n]+?\"" % (gb_num, start, end))
#             prefix用于生成replace
            prefix, target = rgx_gb.search(self.gbContent).group(
                1), rgx_gb.search(self.gbContent).group()
            if numbered:  # 如果密码子识别对了，才替换
                replace = prefix + numbered + '"'
                self.gbContent = self.gbContent.replace(target, replace)
            num += 1
            self.progressSig.emit(num * 100 / self.totaltRNA)

    def saveFile(self):
        output_prefix = os.path.splitext(self.gbFile)[0] if os.path.dirname(
            self.gbFile) else "./" + os.path.splitext(self.gbFile)[0]
        with open(output_prefix + "_reAnnote.gb", "w", encoding="utf-8") as f:
            f.write(self.gbContent)


class Lg_ReANNT(QDialog, Ui_tRNA_ANNT, object):
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    close_sig = pyqtSignal()
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号

    def __init__(self, unRecognisetRNA=None, gbContent=None, predict_signal=None, parent=None):
        super(Lg_ReANNT, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.setupUi(self)
        self.textBrowser.setText(unRecognisetRNA)
        self.gbContent = gbContent
        self.predict_signal = predict_signal
        self.totaltRNA = unRecognisetRNA.count(">")
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 信号和槽
        self.progressSig.connect(self.normProgress)
        self.close_sig.connect(self.closeWindow)
        self.exception_signal.connect(self.popupException)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        text = self.textBrowser.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "Predict tRNA", "tRNAs", "fasta Format(*.fas)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(text)
            QMessageBox.information(
                self,
                "Predict tRNA",
                "<p style='line-height:25px; height:25px'>File saved successfully!</p>")

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        self.arwenContents = self.textBrowser_2.toPlainText()
        if self.arwenContents:
            # 进度条
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "replacing...", parent=self)
            self.progressDialog.show()
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
        else:
            QMessageBox.information(
                self,
                "Predict tRNA",
                "<p style='line-height:25px; height:25px'>No ARWEN results found!</p>")

    def run_command(self):
        try:
            # raise BaseException
            self.startButtonStatusSig.emit(
                [
                    self.pushButton_2,
                    None,
                    "start",
                    None,
                    self.qss_file,
                    self])
            self.reANNT = ReANNT(
                self.arwenContents, self.gbContent, self.totaltRNA, self.progressSig)
            self.startButtonStatusSig.emit(
                [self.pushButton_2, None, "simple stop", None, self.qss_file, self])
            self.close_sig.emit()
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "except",
                    self.dict_args["exportPath"],
                    self.qss_file,
                    self])

    def normProgress(self, num):
        oldValue = self.progressDialog.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressDialog.setProperty("value", done_int)
            QCoreApplication.processEvents()
            if done_int == 100:
                self.progressDialog.close()

    def closeWindow(self):
        self.progressDialog.close()
        self.close()
        self.predict_signal.emit(self.reANNT.gbContent)

    def popupException(self, exception):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


class GbEditor(QDialog, Ui_GBeditor, object):
    progressSig = pyqtSignal(int)  # 控制进度条
    findSig = pyqtSignal()
    predict_signal = pyqtSignal(str)
    exception_signal = pyqtSignal(str)
    finishValidate = pyqtSignal(list)

    def __init__(self, nmlgb):
        self.dict_args = nmlgb.dict_args
        self.parent = self.dict_args["parent"]
        super(GbEditor, self).__init__(self.parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        # 保存设置
        self.gbEditor_settings = QSettings(
            self.thisPath +
            '/settings/gbEditor_settings.ini',
            QSettings.IniFormat, parent=self)
        # File only, no fallback to registry or or.
        self.gbEditor_settings.setFallbacksEnabled(False)
        self.settings_ini = QSettings(self.thisPath + '/settings/setting_settings.ini', QSettings.IniFormat)
        self.settings_ini.setFallbacksEnabled(False)
        self.setupUi(self)
        # self.splitter.setStretchFactor(1, 7)
        self.allcontent = nmlgb.allContent
        self.errors = nmlgb.errors
        self.warings = nmlgb.warnings
        self.no_annotation_IDs = nmlgb.no_annotation_IDs
        self.no_annotation_GBs = nmlgb.no_annotation_GBs
        self.unRecognisetRNA = nmlgb.unRecognisetRNA
        self.dict_replace = nmlgb.dict_replace
        self.workPath = self.dict_args["outpath"]
        self.plainTextEdit_gb.setStyleSheet("QPlainTextEdit#plainTextEdit_gb "
                                            "{background-color: #f5f5a3; }")
        self.showOn()
        # 信号和槽
        self.progressSig.connect(self.normProgress)
        self.findSig.connect(self.popupFindOver)
        self.predict_signal.connect(self.reANNT_validate)
        self.exception_signal.connect(lambda x: self.factory.popupException(self, x))
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.installEventFilter(self)
        self.guiRestore()
        self.checkBox.toggled.connect(self.askRemoveMisc)
        self.removeMISC = False
        ## 结束validate
        self.finishValidate.connect(self.validateFinishedSlot)

    def showOn(self):
        self.tableWidget.verticalHeader().setVisible(False)
        self.plainTextEdit_gb.setPlainText(self.allcontent) #set(self.allcontent)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(
            ['Type', 'Indices', 'Description'])
        error_list = [str(i + 1) for i in range(len(self.errors))]
        warning_list = [str(i + 1) for i in range(len(self.warings))]
        combo_box_options = [error_list, warning_list]
        data1 = [
            '%d Errors' %
            len(error_list),
            '%d Warnings' %
            len(warning_list)]
        self.combo_errors = QComboBox()
        self.combo_warnings = QComboBox()
        self.combo_errors.activated.connect(self.skip_description)
        self.combo_warnings.activated.connect(self.skip_description)
        self.combo_box_widget = [self.combo_errors, self.combo_warnings]
        self.combo_box_data = [self.errors, self.warings]
        self.tableWidget.setRowCount(2)

        def setColortoRow(table, rowIndex, color):
            # 颜色
            for j in range(table.columnCount()):
                if j != 1:
                    itemWid = table.item(rowIndex, j)
                    if itemWid:
                        itemWid.setBackground(color)
        colors = [QColor("red"), QColor("blue")]
        for row in range(2):
            item1 = QTableWidgetItem(data1[row])
            item1.setForeground(QColor("white"))
            self.tableWidget.setItem(row, 0, item1)
            for t in combo_box_options[row]:
                self.combo_box_widget[row].addItem(t)
            self.tableWidget.setCellWidget(
                row, 1, self.combo_box_widget[row])
            if self.combo_box_data[row] != []:
                # label = QLabel(self.combo_box_data[row][0][1], self)
                # setColortoRow(self.tableWidget, row, colors[row])
                # self.tableWidget.setItem(row, 2, QTableWidgetItem("")) ##必须设置一个空去item，才能设置背景色
                # self.tableWidget.setCellWidget(
                #     row, 2, label)
                widget = QWidget(self)
                hlayout = QHBoxLayout(widget)
                hlayout.setContentsMargins(0, 0, 0, 0)
                spacerItem = QSpacerItem(50, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
                hlayout.addItem(spacerItem)
                toolButton_2 = QToolButton(self)
                self.factory.highlightWidgets(toolButton_2)
                toolButton_2.setToolTip("Configure identifiers")
                # toolButton_2.setAutoRaise(True)
                toolButton_2.clicked.connect(self.openExtractSet)
                toolButton_2.setIcon(QIcon(":/picture/resourses/cog.png"))
                hlayout.addWidget(toolButton_2)
                self.tableWidget.setCellWidget(row, 2, widget)
                # print(self.combo_box_data[row][0][1])
                # if not "identifiers" in self.combo_box_data[row][0][1]:
                #     # print("no identifiers")
                #     self.tableWidget.cellWidget(row, 2).setVisible(False)
                ##设置item
                item2 = QTableWidgetItem(self.combo_box_data[row][0][1])
                item2.setForeground(QColor("white"))
                self.tableWidget.setItem(row, 2, item2)
                setColortoRow(self.tableWidget, row, colors[row])
            else:
                # 当没有错误时
                item2 = QTableWidgetItem(
                    "No %s to display" %
                    data1[row].split(" ")[1])
                item2.setForeground(QColor("white"))
                self.tableWidget.setItem(row, 2, item2)
                setColortoRow(self.tableWidget, row, QColor("green"))
        # self.tableWidget.resizeColumnsToContents()
        ##模拟点击
        # QTimer.singleShot(100, lambda: [self.tableWidget.cellWidget(0, 1).activated.emit(0),
        #                                 self.tableWidget.cellWidget(1, 1).activated.emit(0)])

    def skip_description(self, index):
        current_comb_box = self.sender()
        rowIndex = self.combo_box_widget.index(current_comb_box)
        # 0行是error,1行是waring
        content_data = self.combo_box_data[rowIndex]
        # description
        item = QTableWidgetItem(content_data[index][1])
        item.setForeground(QColor("white"))
        color = QColor("red") if rowIndex == 0 else QColor("blue")
        widget = self.tableWidget.cellWidget(rowIndex, 2)
        if "identifiers" in content_data[index][1]:
            widget.setVisible(True)
        else:
            widget.setVisible(False)
        self.tableWidget.setItem(rowIndex, 2, item)
        # 保持颜色
        self.tableWidget.item(rowIndex, 2).setBackground(color)
        # 跳转到指定位置
        f = Find(
            parent=self.plainTextEdit_gb,
            target=content_data[index][0],
            sig=self.findSig)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        # text = self.plainTextEdit_gb.toPlainText()
        f = Find(parent=self.plainTextEdit_gb)
        f.show()

    @pyqtSlot()
    def on_pushButton_2_clicked(self, predict=False):
        '''
        validate, predict即预测过后执行这个
        '''
        currentContent = self.plainTextEdit_gb.toPlainText()
        totalID = currentContent.count("//")
        # 进度条
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "validating...", parent=self)
        self.progressDialog.show()
        self.dict_args["MarkNCR"] = self.checkBox.isChecked()
        self.dict_args["ncrLenth"] = self.spinBox.value()
        self.dict_args["progressSig"] = self.progressSig
        self.dict_args["gbContents"] = currentContent
        self.dict_args["outpath"] = self.workPath
        self.dict_args["totalID"] = totalID
        self.normWorker = WorkThread(lambda: self.validateSlot(currentContent, self.dict_args), parent=self)
        self.normWorker.start()
        self.normWorker.finished.connect(self.progressDialog.close)

    # @pyqtSlot()
    # def on_pushButton_6_clicked(self):
    #     '''
    #     save
    #     '''
    #     currentContent = self.plainTextEdit_gb.toPlainText()
    #     gbManager = GbManager(self.workPath, parent=self)
    #     gbManager.addRefinedContent(currentContent)
    #     gbManager.close()
    #     QMessageBox.information(self,
    #                             "GenBank file editor", "<p style='line-height:25px; height:25px'>File saved succesfully!</p>")

    @pyqtSlot()
    def on_pushButton_rmv_clicked(self):
        '''
        remove IDs with no annotation
        '''
        if self.no_annotation_IDs:
            no_annotation_IDs = copy.deepcopy(self.no_annotation_IDs) # 如果不
            currentContent = self.plainTextEdit_gb.toPlainText()
            for content in self.no_annotation_GBs:
                currentContent = currentContent.replace(content, "")
            totalID = currentContent.count("//")
            # 进度条
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "validating...", parent=self)
            self.progressDialog.show()
            self.dict_args["MarkNCR"] = self.checkBox.isChecked()
            self.dict_args["ncrLenth"] = self.spinBox.value()
            self.dict_args["progressSig"] = self.progressSig
            self.dict_args["gbContents"] = currentContent
            self.dict_args["outpath"] = self.workPath
            self.dict_args["totalID"] = totalID
            self.normWorker = WorkThread(lambda: self.validateSlot(currentContent, self.dict_args, quiet=True), parent=self)
            self.normWorker.start()
            self.normWorker.finished.connect(lambda : [self.progressDialog.close(),
                                                       self.removeIDs(no_annotation_IDs)])
        else:
            QMessageBox.information(self,
                                    "GenBank file editor",
                                    "<p style='line-height:25px; height:25px'>All IDs have annotations</p>")
            # self.no_annotation_IDs = []
            # self.no_annotation_GBs = []

    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        '''
        PREDICT TRNA
        '''
        if self.unRecognisetRNA:
            currentContent = self.plainTextEdit_gb.toPlainText()
            self.Lg_ReANNT = Lg_ReANNT(
                self.unRecognisetRNA, currentContent, self.predict_signal, parent=self)
            # 添加最大化按钮
            self.Lg_ReANNT.setWindowFlags(self.Lg_ReANNT.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.Lg_ReANNT.show()
#             self.plainTextEdit_gb.setText(self.unRecognisetRNA)
        else:
            QMessageBox.information(self,
                                    "GenBank file editor", "<p style='line-height:25px; height:25px'>No tRNA(s) needing predict</p>")

    def normProgress(self, num):
        oldValue = self.progressDialog.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressDialog.setProperty("value", done_int)
            QCoreApplication.processEvents()
            if done_int == 100:
                self.progressDialog.close()

    def popupFindOver(self):
        reply = QMessageBox.information(
            self,
            "GenBank file editor",
            'This item has changed, please click "validate" button to validate changes', QMessageBox.Yes,
                QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            self.on_pushButton_2_clicked()

    def eventFilter(self, obj, event):
        modifiers = QApplication.keyboardModifiers()
        if event.type() == QEvent.KeyPress:  # 首先得判断type
            if (modifiers == Qt.ControlModifier) and (event.key() == Qt.Key_S):
                self.on_pushButton_6_clicked()
                return True
            if (modifiers == Qt.ControlModifier) and (event.key() == Qt.Key_F):
                self.on_pushButton_clicked()
                return True
        return super(GbEditor, self).eventFilter(obj, event)

    def guiSave(self):
        # Save geometry
        self.gbEditor_settings.setValue('size', self.size())
        # self.gbEditor_settings.setValue('pos', self.pos())
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.gbEditor_settings.setValue(name, state)
            if isinstance(obj, QSpinBox):
                value = obj.value()
                self.gbEditor_settings.setValue(name, value)

    def guiRestore(self):
        # Restore geometry
        self.resize(self.factory.judgeWindowSize(self.gbEditor_settings, 807, 612))
        self.factory.centerWindow(self)
        # self.move(self.gbEditor_settings.value('pos', QPoint(875, 254)))
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QCheckBox):
                value = self.gbEditor_settings.value(
                    name, "false")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QSpinBox):
                value = self.gbEditor_settings.value(
                    name)  # get stored value from registry
                if value:
                    obj.setValue(int(value))

    def closeEvent(self, event):
        self.guiSave()

    def reANNT_validate(self, gbContent):
        totalID = gbContent.count("//")
        # 进度条
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "validating...", parent=self)
        self.progressDialog.show()
        self.dict_args["progressSig"] = self.progressSig
        self.dict_args["gbContents"] = gbContent
        self.dict_args["outpath"] = self.workPath
        self.dict_args["totalID"] = totalID
        self.normWorker = WorkThread(lambda: self.validateSlot(gbContent, self.dict_args), parent=self)
        self.normWorker.start()
        self.normWorker.finished.connect(self.progressDialog.close)

    def openExtractSet(self):
        """
        GenBank file extract settings
        """
        self.extract_setting = ExtractSettings(self)
        self.extract_setting.closeSig.connect(self.saveExtractSet)
        # 添加最大化按钮
        self.extract_setting.setWindowFlags(self.extract_setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.extract_setting.exec_()

    def saveExtractSet(self, dict_gbExtract_set):
        dict_settings = dict_gbExtract_set[list(dict_gbExtract_set.keys())[0]]
        changed = False
        for i in self.dict_args:
            if i in dict_settings and (self.dict_args[i] != dict_settings[i]):
                changed = True
                self.dict_args[i] = dict_settings[i]
        if changed:
            self.on_pushButton_2_clicked()

    def askRemoveMisc(self, bool_):
        if bool_:
            icon = ":/picture/resourses/msg_info.png"
            message1 = "Would you like to remove the following annotation features before using \"Validate\" button? " \
                       "these features will all be reannotated as \"misc_feature\" and named \"NCR\""
            message2 = "Type in other features you wish to remove (one line per feature)"
            text = "misc_feature\nD-loop\nintergenic_regions\nrep_origin\nrepeat_region\nstem_loop"
            itemAsk = ListItemsOption(
                message1, message2, text, icon, parent=self)
            itemAsk.resize(550, 282)
            if itemAsk.exec_() == QDialog.Accepted:
                self.removeMISC = itemAsk.textEdit.toPlainText()

    def validateSlot(self, gbContent, dict_args, quiet=False):
        ##替换掉 misc_feature 等的内容
        progressSig = dict_args["progressSig"]
        progressSig.emit(5)
        if self.removeMISC:
            gb = SeqIO.parse(StringIO(gbContent), "genbank")
            list_features = self.removeMISC.split("\n")
            while "" in list_features:
                list_features.remove("")
            new_gb = ""
            for gb_record in gb:
                screened_features = [feature for feature in gb_record.features if feature.type not in list_features]
                gb_record.features = screened_features
                new_gb += gb_record.format("genbank")
            dict_args["gbContents"] = new_gb
        progressSig.emit(10)
        nmlgb = Normalize_MT(**dict_args)
        self.finishValidate.emit([nmlgb.allContent,
                                  nmlgb.errors,
                                  nmlgb.warnings,
                                  nmlgb.no_annotation_IDs,
                                  nmlgb.no_annotation_GBs,
                                  quiet])

    def validateFinishedSlot(self, list_):
        self.allcontent = list_[0]
        self.errors = list_[1]
        self.warings = list_[2]
        self.no_annotation_IDs = list_[3]
        self.no_annotation_GBs = list_[4]
        quiet = list_[5]
        self.showOn()
        if not quiet:
            QMessageBox.information(
                self, "GenBank file editor", "<p style='line-height:25px; height:25px'>Validation complete!!</p>")

    def removeIDs(self, IDs):
        treeIndex = self.parent.treeView.currentIndex()
        filePath = self.parent.tree_model.filePath(treeIndex)
        gbManager = GbManager(filePath, parent=self.parent)
        array = gbManager.fetch_array()
        reverse_array = [array[0]] + sorted(array[1:], reverse=True)  # 反转一下
        self.parent.displayTableModel = MyTableModel(
            reverse_array, parent=self.parent)
        self.parent.tableView.setModel(self.parent.displayTableModel)
        arrayMAN = ArrayManager(reverse_array)
        found_rows = arrayMAN.get_index_by_IDs(IDs)
        # # 选中全部行
        # 先清除已有选中的行
        self.parent.tableView.clearSelection()
        indexes = [self.parent.displayTableModel.index(row, 0) for row in found_rows]
        mode = QItemSelectionModel.Select | QItemSelectionModel.Rows
        selectModel = self.parent.tableView.selectionModel()
        selectModel.selectionChanged.connect(lambda:
                                             self.parent.statusBar().showMessage(str(len(set([i.row() for i in
                                                                                self.parent.tableView.selectedIndexes()]))) + " sequence(s) selected"))
        [selectModel.select(index, mode) for index in indexes]
        self.parent.displayTableModel.modifiedSig.connect(
            self.parent.depositeData)
        ## 开始删除
        self.parent.rmTableRow(parent=self)

