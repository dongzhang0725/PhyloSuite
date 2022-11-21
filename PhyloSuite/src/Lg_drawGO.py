#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
import re
import signal
from collections import OrderedDict
from io import StringIO

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtSvg import QSvgGenerator
from PyQt5.QtWidgets import *

from ete3.treeview.CustomWidgets import QGraphicsRoundRectItem, QGraphicsDiamondItem, QGraphicsLeftArrowItem, \
    QGraphicsRightArrowItem, QGraphicsLeftArrowItem2, QGraphicsRightArrowItem2, QGraphicsLeftTriangleItem, \
    QGraphicsRightTriangleItem, QGraphicsTopTriangleItem, QGraphicsBottomTriangleItem
from src.factory import Factory, WorkThread
from src.CustomWidget import MyComboBox
import inspect
import os
import sys
import traceback
import subprocess
import platform

from uifiles.Ui_drawGO import Ui_DrawGO

'''
TODO: 
自动根据文字宽度调整大小
新增编辑group的功能: 
    自动导入提取的结果，会顺便导入生成的PCGs等文件，会把里面的基因自动导入到对应的group.
    运行的时候，处理一下name set和单独的基因
    导入提取的结果时，自动导入PCGs等名字
文件是打开的时候报错？
设置字体，物种名的字体单独设置？
QGraphicsLineItem 设置一个变量，如backbone=True
backbone的颜色要不要支持设置？
删除行以后，settings里面的是不是也对应删除
点击item可以设置颜色
linear order 文件改用制表符来分割
'''

class DrawGO(QDialog, Ui_DrawGO, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)
    logGuiSig = pyqtSignal(str)

    def __init__(
            self,
            autoInputs=None,
            workPath=None,
            focusSig=None,
            parent=None):
        super(DrawGO, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.parent = parent
        self.autoInputs = autoInputs
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.setupUi(self)
        self.drawGO_settings = QSettings(
            self.thisPath + '/settings/drawGO_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.drawGO_settings.setFallbacksEnabled(False)
        self.interrupt = False
        self.dict_icon = {
            "right arrow2": ":/shape/resourses/shape/right_arrow2.svg",
            "left arrow2": ":/shape/resourses/shape/left_arrow2.svg",
            "left arrow": ":/shape/resourses/shape/left_arrow.svg",
            "right arrow": ":/shape/resourses/shape/right_arrow.svg",
            "rectangle": ":/shape/resourses/shape/rectangle.svg",
            "ellipse": ":/shape/resourses/shape/circle.svg",
            "round corner rectangle": ":/shape/resourses/shape/round_rect.svg",
            "diamond": ":/shape/resourses/shape/diamond.svg",
            "left triangle": ":/shape/resourses/shape/left_tri.svg",
            "right triangle": ":/shape/resourses/shape/right_tri.svg",
            "top trangle": ":/shape/resourses/shape/top_tri.svg",
            "bottom triangle": ":/shape/resourses/shape/bottom_tri.svg"
        }
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        self.exception_signal.connect(self.popupException)
        self.comboBox_4.installEventFilter(self)
        self.splitter.setStretchFactor(5, 30)
        # self.splitter.setStretchFactor(1, 30)
        # 信号和曹
        self.lineEdit.clicked.connect(self.setFont)
        self.toolButton.clicked.connect(self.setWordWrap)
        # self.plainTextEdit.textChanged.connect(self.on_pushButton_save_ns_clicked)

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        open files
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input gene order Files")
        if fileNames[0]:
            self.comboBox_4.refreshInputs(fileNames[0])

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        TODO： 自定义名字集；自定义border size
        """
        if self.comboBox_4.count():
            # 有数据才执行
            self.interrupt = False
            self.dict_args = {}
            self.dict_args["exception_signal"] = self.exception_signal
            # self.dict_args["workPath"] = self.workPath
            # self.exportPath = self.factory.creat_dirs(self.workPath + \
            #                                           os.sep + "DrawGO_results" + os.sep + self.output_dir_name)
            # self.dict_args["exportPath"] = self.exportPath
            # ok = self.factory.remove_dir(self.exportPath, parent=self)
            # if not ok:
            #     #提醒是否删除旧结果，如果用户取消，就不执行
            #     return
            self.dict_args["start_gene_with"] = self.lineEdit_2.text() if self.lineEdit_2.text() else "cox1"
            self.dict_args["hspace"] = self.doubleSpinBox.value()
            self.dict_args["vspace"] = self.doubleSpinBox_2.value()
            self.dict_args["title_vspace"] = self.doubleSpinBox_3.value()
            self.dict_args["title_height"] = self.doubleSpinBox_4.value()
            self.dict_args["border"] = self.doubleSpinBox_5.value()
            self.dict_args["show strands"] = self.checkBox.isChecked()
            self.dict_args["show backbone line"] = self.checkBox_2.isChecked()
            self.dict_args["draw all genes"] = self.checkBox_3.isChecked()
            self.dict_args["use fill color"] = self.checkBox_4.isChecked()
            self.dict_args["use border color"] = self.checkBox_5.isChecked()
            self.dict_args["top margin"] = self.doubleSpinBox_6.value()
            self.dict_args["bottom margin"] = self.doubleSpinBox_7.value()
            self.dict_args["left margin"] = self.doubleSpinBox_8.value()
            self.dict_args["right margin"] = self.doubleSpinBox_9.value()
            self.dict_args["font"] = self.lineEdit.font_
            self.dict_args["width factor"] = self.doubleSpinBox_10.value()/100
            self.dict_args["height factor"] = self.doubleSpinBox_11.value()/100
            self.dict_args["GO text xshift"] = self.doubleSpinBox_12.value()
            self.dict_args["GO text yshift"] = self.doubleSpinBox_13.value()
            # 名字集
            self.dict_args["name sets"] = self.plainTextEdit.dict_groups
            self.dict_args["checked gene names"] = self.fetch_checked_gene_names()
            self.dict_args["go_parms"] = OrderedDict()
            for row, gene_name in enumerate(self.dict_args["checked gene names"]):
                Fcolor = self.tableWidget.item(row, 1).text()
                Bcolor = self.tableWidget.item(row, 2).text()
                Tcolor = self.tableWidget.item(row, 3).text()
                length = self.tableWidget.item(row, 4).text()
                height = self.tableWidget.item(row, 5).text()
                shape_combo = self.tableWidget.cellWidget(row, 6)
                shape = shape_combo.currentText() # 转为缩写形式
                self.dict_args["go_parms"][gene_name] = [Fcolor, Bcolor, Tcolor, length, height, shape]
            self.parseGO()
            self.align_order()
            self.draw_()
        else:
            QMessageBox.critical(
                self,
                "Draw GO",
                "<p style='line-height:25px; height:25px'>Please input files first!</p>")

    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        """
        add row for gene order table
        """
        rowPosition = self.tableWidget.rowCount()
        self.tableWidget.insertRow(rowPosition)
        # 初始化必要的item
        # col1
        item = QTableWidgetItem("Dblclick to input name")
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
        item.setCheckState(Qt.Checked)
        self.tableWidget.setItem(rowPosition, 0, item)
        # col2
        color = self.colorPicker(self.fetch_used_colors(1))
        item = QTableWidgetItem(color)
        item.setBackground(QColor(color))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 1, item)
        # col3
        color = self.fetch_used_colors(2)[-1]
        item = QTableWidgetItem(color)
        item.setBackground(QColor(color))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 2, item)
        # col4
        color = self.fetch_used_colors(3)[-1]
        item = QTableWidgetItem(color)
        item.setBackground(QColor(color))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 3, item)
        # col5
        item = QTableWidgetItem("50")
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 4, item)
        # col6
        item = QTableWidgetItem("20")
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 5, item)
        # col7
        model = QStandardItemModel()
        for i in self.dict_icon:
            item = QStandardItem(i)
            item.setIcon(QIcon(self.dict_icon[i]))
            font = item.font()
            font.setPointSize(13)
            item.setFont(font)
            model.appendRow(item)
        comb_box = MyComboBox(self)
        comb_box.setModel(model)
        # 改变icon大小
        view = comb_box.view()
        view.setIconSize(QSize(38, 38))
        self.tableWidget.setCellWidget(rowPosition, 6, comb_box)
        self.tableWidget.scrollToBottom()

    @pyqtSlot()
    def on_pushButton_11_clicked(self):
        """
        delete selected row of gene order table
        """
        rows = []
        for idx in self.tableWidget.selectedIndexes():
            rows.append(idx.row())
        rows = sorted(rows, reverse=True)
        for row in rows:
            self.tableWidget.removeRow(row)

    @pyqtSlot()
    def on_pushButton_export_clicked(self):
        ## 图片格式
        fileName = QFileDialog.getSaveFileName(
            self, "Draw gene order", "gene order",
                                    "PDF Format (*.pdf);;"
                                    "PNG format (*.png);;"
                                    "SVG format (*.svg);;")
                                    # "PS format (*.ps)")
        if fileName[0]:
            self.save(self.scene, fileName[0])
            QMessageBox.information(
                self,
                "Draw gene order",
                "<p style='line-height:25px; height:25px'>Figure saved successfully!</p>")
    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        '''
        Convert current name as name set
        :return:
        '''
        go_name = self.tabWidget.tabText(1)
        if (go_name != "Name set") and (go_name not in self.plainTextEdit.dict_groups):
            self.plainTextEdit.dict_groups[go_name] = [go_name]
            self.plainTextEdit.setPlainText(f"##{go_name}##\n" + ", ".join([go_name]))
            QMessageBox.information(
                self,
                "Draw gene order",
                f"<p style='line-height:25px; height:25px'>\"{go_name}\" is a name set now!</p>")

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        '''
        Remove current name set
        :return:
        '''
        go_name = self.tabWidget.tabText(1)
        if (go_name != "Name set") and (go_name in self.plainTextEdit.dict_groups):
            self.plainTextEdit.dict_groups.pop(go_name)
            self.plainTextEdit.setPlainText(f"##{go_name}## is not a name set!\n")
            QMessageBox.information(
                self,
                "Draw gene order",
                f"<p style='line-height:25px; height:25px'>Name set \"{go_name}\" has been removed!</p>")

    @pyqtSlot()
    def on_pushButton_save_ns_clicked(self):
        '''
        Save current name set
        :return:
        '''
        text = self.plainTextEdit.toPlainText()
        text.replace("，", ",") # 替换中文的逗号
        f2 = StringIO(text)
        line = f2.readline()
        while line:
            while not re.search(r"##(.+)##", line) and line:
                line = f2.readline()
            key = re.search(r"##(.+)##", line).group(1)
            content = ""
            line = f2.readline()
            while not re.search(r"##(.+)##", line) and line:
                content += re.sub(r"\s", "", line)
                line = f2.readline()
            list_ = []
            for i in content.split(","):
                if i not in list_:
                    list_.append(i)
            self.plainTextEdit.dict_groups[key] = list_
        QMessageBox.information(
            self,
            "Draw gene order",
            f"<p style='line-height:25px; height:25px'>Current name set has been saved!</p>")

    def guiSave(self):
        # Save geometry
        self.drawGO_settings.setValue('size', self.size())
        # self.drawGO_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.drawGO_settings.setValue(name, state)
            if isinstance(obj, QLineEdit):
                if name == "lineEdit":
                    font = obj.font_
                    self.drawGO_settings.setValue(name, font)
                else:
                    text = obj.text()
                    self.drawGO_settings.setValue(name, text)
            if isinstance(obj, QPlainTextEdit):
                if name == "plainTextEdit":
                    dict_groups = obj.dict_groups
                    self.drawGO_settings.setValue(name, dict_groups)
            if isinstance(obj, QTableWidget):
                if name == "tableWidget":
                    array = []  # 每一行存：[gene_name, checked], Fcolor, Bcolor, Tcolor, width, height, shape
                    for row in range(obj.rowCount()):
                        gene_name = obj.item(row, 0).text()
                        checked = "true" if obj.item(
                            row, 0).checkState() == Qt.Checked else "false"
                        Fcolor = obj.item(row, 1).text()
                        Bcolor = obj.item(row, 2).text()
                        Tcolor = obj.item(row, 3).text()
                        width = obj.item(row, 4).text()
                        height = obj.item(row, 5).text()
                        shape_combo = obj.cellWidget(row, 6)
                        shape = shape_combo.currentText()
                        array.append([[gene_name, checked], Fcolor, Bcolor, Tcolor, width, height, shape])
                    self.drawGO_settings.setValue(name, array)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.drawGO_settings.value('size', QSize(1000, 700)))
        self.factory.centerWindow(self)
        # self.move(self.drawGO_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if (name == "comboBox_4") and self.autoInputs:
                    self.comboBox_4.refreshInputs(self.autoInputs)
            if isinstance(obj, QCheckBox):
                value = self.drawGO_settings.value(
                    name, "true")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QLineEdit):
                if name == "lineEdit":
                    font = self.drawGO_settings.value(name, QFont("Arial", 8, QFont.Normal))
                    obj.font_ = font
                    italic = "italic, " if font.italic() else ""
                    bold = "bold, " if font.bold() else ""
                    obj.setText(f"{font.family()}, {italic}{bold}{font.pointSize()}")
                else:
                    text = self.drawGO_settings.value(name, "cox1")
                    if text:
                        obj.setText(text)
            if isinstance(obj, QPlainTextEdit):
                if name == "plainTextEdit":
                    dict_ = {"tRNAs": ["T", "C", "E", "Y", "R", "G", "H", "L1", "L2", "S1", "S2", "Q", "F", "M", "V", "A", "D", "N", "P", "I", "K", "W", "S", "L"],
                             "rRNAs": ["rrnS", "rrnL"],
                             "PCGs": ["atp6", "atp8", "cox1", "cox2", "cox3", "cytb", "nad1", "nad2", "nad3", "nad4", "nad4L", "nad5", "nad6"]}
                    dict_groups = self.drawGO_settings.value(name, dict_)
                    obj.dict_groups = dict_groups
                    obj.setPlainText("\n\n".join([f"##{key}##\n" + ", ".join(dict_groups[key]) for key in dict_groups]))
            if isinstance(obj, QTableWidget):
                if name == "tableWidget":
                    ini_array = [
                        [
                            ["ATP6|ATP8", 'true'], '#ffff33', '#bfbfbf', "black", '50', '20', 'right arrow2'], [
                            ["NAD1-6|NAD4L", 'true'], '#99ffff', '#bfbfbf', "black", '50', '20', 'right arrow2'], [
                            ["CYTB", 'true'], '#ff9999', '#bfbfbf', "black", '50', '20', 'right arrow2'], [
                            ["COX1-3", 'true'], '#6699ff', '#bfbfbf', "black", '50', '20', 'right arrow2'], [
                            ["PCGs", 'true'], '#aa55ff', '#bfbfbf', "black", '50', '20', 'right arrow2'], [
                            ["rRNAs", 'true'], '#DAA520', '#bfbfbf', "black", '50', '20', 'right arrow2'], [
                            ["tRNAs", 'true'], '#ccff00', '#bfbfbf', "black", '22', '20', 'ellipse'], [
                            ["NCR", 'false'], '#bfbfbf', '#bfbfbf', "black", '50', '20', 'right arrow2']]
                    array = self.drawGO_settings.value(name, ini_array)
                    obj.setRowCount(len(array))
                    for row, list_row in enumerate(array):
                        # col 1
                        if type(list_row[0]) == list:
                            ifChecked = Qt.Checked if list_row[
                                                          0][1] == "true" else Qt.Unchecked
                            gene_name = list_row[0][0]
                            item = QTableWidgetItem(gene_name)
                            item.setFlags(
                                Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
                            item.setCheckState(ifChecked)
                            obj.setItem(row, 0, item)
                        else:
                            # 旧版本保存的字符串（true或false）
                            ifChecked = Qt.Checked if list_row[0] == "true" else Qt.Unchecked
                            obj.item(row, 0).setCheckState(ifChecked)
                        # col 2
                        item = QTableWidgetItem(list_row[1])
                        item.setBackground(QColor(list_row[1]))
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                        obj.setItem(row, 1, item)
                        # col 3
                        item = QTableWidgetItem(list_row[2])
                        item.setBackground(QColor(list_row[2]))
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                        obj.setItem(row, 2, item)
                        # col 4
                        item = QTableWidgetItem(list_row[3])
                        item.setBackground(QColor(list_row[3]))
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                        obj.setItem(row, 3, item)
                        # col 5
                        item = QTableWidgetItem(list_row[4])
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                        obj.setItem(row, 4, item)
                        # col 6
                        item = QTableWidgetItem(list_row[5])
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                        obj.setItem(row, 5, item)
                        # col 7
                        model = QStandardItemModel()
                        for i in self.dict_icon:
                            item = QStandardItem(i)
                            item.setIcon(QIcon(self.dict_icon[i]))
                            font = item.font()
                            font.setPointSize(13)
                            item.setFont(font)
                            model.appendRow(item)
                        comb_box = MyComboBox(self)
                        comb_box.setModel(model)
                        # 改变icon大小
                        view = comb_box.view()
                        view.setIconSize(QSize(38, 38))
                        shape = list_row[6]
                        shape_combo_index = comb_box.findText(shape)
                        if shape_combo_index == -1:  # add to list if not found
                            comb_box.insertItems(0, ["right arrow2"])
                            index = comb_box.findText("right arrow2")
                            comb_box.setCurrentIndex(index)
                        else:
                            # preselect a combobox value by index
                            comb_box.setCurrentIndex(shape_combo_index)
                        obj.setCellWidget(row, 6, comb_box)
                    obj.itemClicked.connect(self.handleItemClicked)
                    obj.resizeColumnsToContents()
                    obj.verticalHeader().setVisible(False)

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
        self.guiSave()

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        if isinstance(
                obj,
                QComboBox):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                self.comboBox_4.refreshInputs(files)
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(DrawGO, self).eventFilter(obj, event)  # 0

    def handleItemClicked(self, item):
        if item.column() == 0:
            text = item.text()
            dict_groups = self.plainTextEdit.dict_groups
            self.tabWidget.setTabText(1, text)
            if text in dict_groups:
                self.plainTextEdit.setPlainText(f"##{text}##\n" + ", ".join(dict_groups[text]))
            else:
                self.plainTextEdit.setPlainText(f"##{text}## is not a name set!\n")
        if item.column() in [1, 2, 3]:
            color = QColorDialog.getColor(QColor(item.text()), self)
            if color.isValid():
                item.setText(color.name())
                item.setBackground(color)
            self.tableWidget.clearSelection()

    def parseGO(self):
        go_file = self.comboBox_4.fetchListsText()[0]
        with open(go_file) as f:
            lines = f.readlines()
        self.dict_go = OrderedDict()
        for line in lines:
            if line.startswith(">"):
                name = line.strip().replace(">", "")
            else:
                list_go = line.rstrip("\n").split("\t")
                self.dict_go[name] = list_go

    def align_order(self):
        for i in self.dict_go:
            list_order = self.dict_go[i]
            for num, j in enumerate(list_order):
                if self.dict_args["start_gene_with"] in j:
                    self.dict_go[i] = list_order[num:] + list_order[:num]

    def draw_(self):
        self.list_shapes = []
        list_hbase = []
        hspace = self.dict_args["hspace"]
        vspace = self.dict_args["vspace"]
        title_vspace = self.dict_args["title_vspace"]
        title_height = self.dict_args["title_height"]
        border = self.dict_args["border"]
        vbase = self.dict_args["top margin"]
        width_factor = self.dict_args["width factor"]
        height_factor = self.dict_args["height factor"]
        text_xshift = self.dict_args["GO text xshift"]
        text_yshift = self.dict_args["GO text yshift"]
        for num, name in enumerate(self.dict_go):
            # title text row
            name_ = QGraphicsTextItem(name)
            name_.setTextInteractionFlags(Qt.TextEditorInteraction)
            name_.setPos(self.dict_args["left margin"], vbase)
            # format = QTextBlockFormat()
            # format.setAlignment(Qt.AlignLeft)
            # cursor = name_.textCursor()
            # cursor.select(QTextCursor.Document)
            # cursor.mergeBlockFormat(format)
            # cursor.clearSelection()
            # name_.setTextCursor(cursor)
            self.list_shapes.append(name_)
            vbase += title_height + title_vspace
            # go row
            hbase = self.dict_args["left margin"]
            list_height = []
            has_plus = False
            has_minus = False
            for go in self.dict_go[name]:
                go = go.split("_copy")[0]  # 预防有copy的基因
                # 是否有该基因对应的设置（单基因模式）
                match = False
                for gene_name in self.dict_args["checked gene names"]:
                    if gene_name not in self.dict_args["name sets"]:
                        rgx_gene_name = "-?" + "$|-?".join(gene_name.split("|")) + "$"
                        num_range = re.findall(r"(\d+)\-(\d+)", gene_name)
                        if num_range:
                            nums = f'({"|".join([str(num) for num in range(int(num_range[0][0]), int(num_range[0][1])+1)])})'
                            rgx_gene_name = re.sub(r"\d+\-\d+", nums, rgx_gene_name) # COX1-3 --> COX(1|2|3)
                        rgx = re.compile(rgx_gene_name, re.I)
                        # print(rgx)
                        if rgx.match(go):
                            Fcolor, Bcolor, Tcolor, width, height, shape = self.dict_args["go_parms"][gene_name]
                            match = True
                            break
                if not match:
                    # 如果单个基因没有设置，就看PCGs、tRNA等name set是否匹配
                    flag = False
                    judge_name = re.sub("^NCR\d+$", "NCR", go.lstrip("-"), re.I) # 用于判断用的名字
                    for neme_set in self.dict_args["name sets"]:
                        if (neme_set in self.dict_args["checked gene names"]) and \
                                (judge_name in self.dict_args["name sets"][neme_set]):
                            Fcolor, Bcolor, Tcolor, width, height, shape = self.dict_args["go_parms"][neme_set]
                            flag = True
                    if not flag:
                        if self.dict_args["draw all genes"]:
                            Fcolor, Bcolor, Tcolor, width, height, shape = "#bfbfbf", "#ff9999", "black", '25', '21', "right arrow2"
                        else:
                            continue
                ## draw GO shape
                width = int(width)
                height = int(height)
                list_height.append(height)
                # shape
                dict_shape = {"ellipse": QGraphicsEllipseItem,
                              "rectangle": QGraphicsRectItem,
                              "round corner rectangle": QGraphicsRoundRectItem,
                              "diamond": QGraphicsDiamondItem,
                              "left arrow": QGraphicsLeftArrowItem,
                              "right arrow": QGraphicsRightArrowItem,
                              "left arrow2": QGraphicsLeftArrowItem2,
                              "right arrow2": QGraphicsRightArrowItem2,
                              "left triangle": QGraphicsLeftTriangleItem,
                              "right triangle": QGraphicsRightTriangleItem,
                              "top trangle": QGraphicsTopTriangleItem,
                              "bottom triangle": QGraphicsBottomTriangleItem}
                shape_graph = dict_shape[shape]
                if shape in ["ellipse", "rectangle", "round corner rectangle"]:
                    go_shape = shape_graph(0, 0, width, height)
                else:
                    if (shape in ["left arrow", "right arrow"]):
                        if go.startswith("-"):
                            go_shape = QGraphicsLeftArrowItem(width, height,
                                                              height_factor=height_factor,
                                                              width_factor=width_factor)
                        else:
                            go_shape = QGraphicsRightArrowItem(width, height,
                                                               height_factor=height_factor,
                                                               width_factor=width_factor)
                    elif (shape in ["left arrow2", "right arrow2"]):
                        if go.startswith("-"):
                            go_shape = QGraphicsLeftArrowItem2(width, height, width_factor=width_factor)
                        else:
                            go_shape = QGraphicsRightArrowItem2(width, height, width_factor=width_factor)
                    else:
                        go_shape = shape_graph(width, height)
                if go.startswith("-"):
                    has_minus = True
                    go_shape.setPos(hbase, vbase + height)
                else:
                    has_plus = True
                    go_shape.setPos(hbase, vbase)
                # Define the brush (fill).
                if self.dict_args["use fill color"]:
                    brush = QBrush(QColor(Fcolor))
                    go_shape.setBrush(brush)
                # Define the pen (line)
                if self.dict_args["use border color"]:
                    pen = QPen(QColor(Bcolor))
                    pen.setWidth(border)
                    go_shape.setPen(pen)
                else:
                    go_shape.setPen(QPen(Qt.NoPen))
                    # pen = QPen(QColor("white"))
                    # pen.setWidth(0)
                    # go_shape.setPen(pen)
                self.list_shapes.append(go_shape)
                hbase += width + hspace
                ## draw go name
                go_name = QGraphicsTextItem(go.lstrip("-"))
                go_name.setTextInteractionFlags(Qt.TextEditorInteraction)
                go_name.setParentItem(go_shape)
                tw = go_name.boundingRect().width()
                th = go_name.boundingRect().height()
                center = go_shape.boundingRect().center()
                width = go_shape.boundingRect().width()
                if "arrow" in shape:
                    if go.startswith("-"):
                        center_x = center.x() + (width*go_shape.width_factor)/2
                    else:
                        center_x = center.x() - (width*go_shape.width_factor)/2
                else:
                    center_x = center.x()
                go_name.setPos(center_x - tw / 2 + text_xshift, center.y() - th / 2 + text_yshift)
                # set text color
                go_name.setDefaultTextColor(QColor(Tcolor))
                self.list_shapes.append(go_name)
            # hbase += width + hspace
            # backbone line
            if self.dict_args["show backbone line"]:
                if has_plus:
                    backbone_plus = QGraphicsLineItem(self.dict_args["left margin"],vbase+(height/2),
                                                  hbase,vbase+(height/2))
                    pen = QPen(QColor("grey"))
                    pen.setWidth(0.5)
                    backbone_plus.setPen(pen)
                    self.list_shapes.append(backbone_plus)
                if has_minus:
                    backbone_minus = QGraphicsLineItem(self.dict_args["left margin"],vbase+height+(height/2),
                                                   hbase,vbase+height+(height/2))
                    pen = QPen(QColor("grey"))
                    pen.setWidth(0.1)
                    backbone_minus.setPen(pen)
                    self.list_shapes.append(backbone_minus)
            # strand name
            if self.dict_args["show strands"]:
                strand_plus = QGraphicsTextItem("(+)")
                tw_plus = strand_plus.boundingRect().width()
                strand_plus.setPos(hbase, vbase)
                if has_plus:
                    self.list_shapes.append(strand_plus)
                strand_minus = QGraphicsTextItem("(-)")
                tw_minus = strand_minus.boundingRect().width()
                strand_minus.setPos(hbase, vbase + height)
                if has_minus:
                    self.list_shapes.append(strand_minus)
                list_hbase.append(hbase + max([tw_plus, tw_minus]))
            else:
                list_hbase.append(hbase)
            # 把GO行的高度加上
            this_row_height = 2*max(list_height) if (has_plus and has_minus) else max(list_height)
            vbase += this_row_height + vspace
        self.scene = QGraphicsScene(0, 0, max(list_hbase) + self.dict_args["right margin"],
                                    vbase + self.dict_args["bottom margin"])
        for shape in self.list_shapes:
            if type(shape) == QGraphicsLineItem:
                shape.setZValue(0)
            else:
                shape.setZValue(1)
            if type(shape) == QGraphicsTextItem:
                shape.setFont(self.dict_args["font"])
            self.scene.addItem(shape)
        self.graphicsView.setScene(self.scene)

    def fetch_checked_gene_names(self):
        list_names = []
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row, 0) and \
                    self.tableWidget.item(row, 0).checkState() == Qt.Checked:
                list_names.append(self.tableWidget.item(row, 0).text())
        return list_names

    def setFont(self):
        # family = self.lineEdit.text()
        # size = int(self.lineEdit_2.text())
        font, ok = QFontDialog.getFont(QFont("Arial", 8, QFont.Normal), self)
        # print(font.family(), font.style(), font.weight(), font.pointSize(), font.key(), font.toString())
        if ok:
            family_ = font.family()
            size_ = str(font.pointSize())
            italic = "italic, " if font.italic() else ""
            bold = "bold, " if font.bold() else ""
            self.lineEdit.setText(f"{family_}, {italic}{bold}{size_}")
            self.lineEdit.font_ = font

    def colorPicker(self, list_colors):
        # 生成不重复的随机颜色
        colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
        while colour in list_colors:
            # 不让range用自定义的颜色
            colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
        return colour

    def fetch_used_colors(self, col):
        list_colors = []
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row, col):
                list_colors.append(self.tableWidget.item(row, col).text())
        return list_colors

    def setWordWrap(self):
        button = self.sender()
        if button.isChecked():
            button.setChecked(True)
            self.plainTextEdit.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        else:
            button.setChecked(False)
            self.plainTextEdit.setLineWrapMode(QPlainTextEdit.NoWrap)

    def save(self, scene, imgName, w=None, h=None, dpi=300, \
             take_region=False, units="px"):
        ipython_inline = False
        if imgName == "%%inline":
            ipython_inline = True
            ext = "PNG"
        elif imgName == "%%inlineSVG":
            ipython_inline = True
            ext = "SVG"
        elif imgName.startswith("%%return"):
            try:
                ext = imgName.split(".")[1].upper()
            except IndexError:
                ext = 'SVG'
            imgName = '%%return'
        else:
            ext = imgName.split(".")[-1].upper()

        main_rect = scene.sceneRect()
        aspect_ratio = main_rect.height() / main_rect.width()

        # auto adjust size
        if not w and not h:
            units = "px"
            w = main_rect.width()
            h = main_rect.height()
            ratio_mode = Qt.KeepAspectRatio
        elif w and h:
            ratio_mode = Qt.IgnoreAspectRatio
        elif h is None :
            h = w * aspect_ratio
            ratio_mode = Qt.KeepAspectRatio
        elif w is None:
            w = h / aspect_ratio
            ratio_mode = Qt.KeepAspectRatio

        # Adjust to resolution
        if units == "mm":
            if w:
                w = w * 0.0393700787 * dpi
            if h:
                h = h * 0.0393700787 * dpi
        elif units == "in":
            if w:
                w = w * dpi
            if h:
                h = h * dpi
        elif units == "px":
            pass
        else:
            raise Exception("wrong unit format")

        x_scale, y_scale = w/main_rect.width(), h/main_rect.height()

        if ext == "SVG":
            svg = QSvgGenerator()
            targetRect = QRectF(0, 0, w, h)
            svg.setSize(QSize(w, h))
            svg.setViewBox(targetRect)
            svg.setTitle("Generated with PhyloSuite http://phylosuite.jushengwu.com/")
            svg.setDescription("Generated with PhyloSuite http://phylosuite.jushengwu.com/")

            if imgName == '%%return':
                ba = QByteArray()
                buf = QBuffer(ba)
                buf.open(QIODevice.WriteOnly)
                svg.setOutputDevice(buf)
            else:
                svg.setFileName(imgName)

            pp = QPainter()
            pp.begin(svg)
            scene.render(pp, targetRect, scene.sceneRect(), ratio_mode)
            pp.end()
            if imgName == '%%return':
                compatible_code = str(ba)
                print('from memory')
            else:
                compatible_code = open(imgName).read()
            # Fix a very annoying problem with Radial gradients in
            # inkscape and browsers...
            compatible_code = compatible_code.replace("xml:id=", "id=")
            compatible_code = re.sub('font-size="(\d+)"', 'font-size="\\1pt"', compatible_code)
            compatible_code = compatible_code.replace('\n', ' ')
            compatible_code = re.sub('<g [^>]+>\s*</g>', '', compatible_code)
            # End of fix
            if ipython_inline:
                from IPython.core.display import SVG
                return SVG(compatible_code)

            elif imgName == '%%return':
                return x_scale, y_scale, compatible_code
            else:
                open(imgName, "w").write(compatible_code)


        elif ext == "PDF" or ext == "PS":
            if ext == "PS":
                format = QPrinter.PostScriptFormat
            else:
                format = QPrinter.PdfFormat

            printer = QPrinter(QPrinter.HighResolution)
            printer.setResolution(dpi)
            printer.setOutputFormat(format)
            printer.setPageSize(QPrinter.A4)
            printer.setPaperSize(QSizeF(w, h), QPrinter.DevicePixel)
            printer.setPageMargins(0, 0, 0, 0, QPrinter.DevicePixel)

            #pageTopLeft = printer.pageRect().topLeft()
            #paperTopLeft = printer.paperRect().topLeft()
            # For PS -> problems with margins
            #print paperTopLeft.x(), paperTopLeft.y()
            #print pageTopLeft.x(), pageTopLeft.y()
            # print  printer.paperRect().height(),  printer.pageRect().height()
            #topleft =  pageTopLeft - paperTopLeft

            printer.setFullPage(True);
            printer.setOutputFileName(imgName);
            pp = QPainter(printer)
            targetRect =  QRectF(0, 0 , w, h)
            scene.render(pp, targetRect, scene.sceneRect(), ratio_mode)
        else:
            targetRect = QRectF(0, 0, w, h)
            ii= QImage(w, h, QImage.Format_ARGB32)
            ii.fill(QColor(Qt.white).rgb())
            ii.setDotsPerMeterX(dpi / 0.0254) # Convert inches to meters
            ii.setDotsPerMeterY(dpi / 0.0254)
            pp = QPainter(ii)
            pp.setRenderHint(QPainter.Antialiasing)
            pp.setRenderHint(QPainter.TextAntialiasing)
            pp.setRenderHint(QPainter.SmoothPixmapTransform)

            scene.render(pp, targetRect, scene.sceneRect(), ratio_mode)
            pp.end()
            if ipython_inline:
                ba = QByteArray()
                buf = QBuffer(ba)
                buf.open(QIODevice.WriteOnly)
                ii.save(buf, "PNG")
                from IPython.core.display import Image
                return Image(ba.data())
            elif imgName == '%%return':
                ba = QByteArray()
                buf = QBuffer(ba)
                buf.open(QIODevice.WriteOnly)
                ii.save(buf, "PNG")
                return x_scale, y_scale, ba.toBase64()
            else:
                ii.save(imgName)

        return w/main_rect.width(), h/main_rect.height()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = DrawGO()
    ui.show()
    sys.exit(app.exec_())