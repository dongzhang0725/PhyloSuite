#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 自己调整好一个size，然后再guirestore恢复一下
import datetime
import glob
import operator
import random
import re

import multiprocessing
import shutil
import signal

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ete3 import NCBITaxa

from ete3.treeview.CustomWidgets import MyTaxTableModel
from uifiles.Ui_ASTRAL import Ui_ASTRAL
from uifiles.Ui_HmmCleaner import Ui_HmmCleaner
from src.factory import Factory, WorkThread
import inspect
import os
import sys
import traceback
import subprocess
import platform
from multiprocessing.pool import ApplyResult

from uifiles.Ui_iTOLAnnotation import Ui_annotation_editor

class Itol_editor(QDialog, Ui_annotation_editor, object):

    def __init__(
            self,
            # autoInputs=None,
            workPath=None,
            focusSig=None,
            parent=None):
        super(Itol_editor, self).__init__(parent)
        self.parent = parent
        self.function_name = "Itol_editor"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        # self.autoInputs = autoInputs
        self.setupUi(self)
        # 保存设置
        self.Itol_editor_settings = QSettings(
            self.thisPath + '/settings/Itol_editor_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.Itol_editor_settings.setFallbacksEnabled(False)
        self.dict_tax_color = {}
        # 开始装载样式表
        # with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
        #     self.qss_file = f.read()
        # self.setStyleSheet(self.qss_file)
        self.qss_file = self.factory.set_qss(self)
        # 恢复用户的设置
        self.guiRestore()
        # self.tax_model = MyTaxTableModel2(array, header, parent=self.tableView, dialog=self)
        #


    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        add column
        """
        self.tax_model.header.append(f"Taxonomy{len(self.tax_model.header)}")
        self.tax_model.headerDataChanged.emit(Qt.Horizontal, len(self.tax_model.header)-1, len(self.tax_model.header)-1)
        setattr(self.tax_model, "arraydata", [row + [""] for row in self.tax_model.arraydata])
        self.tax_model.dataChanged.emit(self.tax_model.index(0, 0), self.tax_model.index(0, 0))
        self.tableView.scrollTo(self.tax_model.index(0, len(self.tax_model.header)-1))

    def guiSave(self):
        # Save geometry
        self.Itol_editor_settings.setValue('size', self.size())
        # self.Itol_editor_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.Itol_editor_settings.setValue(name, index)
            # if isinstance(obj, QCheckBox):
            #     state = obj.isChecked()
            #     self.Itol_editor_settings.setValue(name, state)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.Itol_editor_settings.setValue(name, float_)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.Itol_editor_settings.value('size', QSize(1000, 750)))
        self.factory.centerWindow(self)
        # self.move(self.Itol_editor_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox_6":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.Itol_editor_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(list_cpu):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.Itol_editor_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(allItems):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
            # elif isinstance(obj, QCheckBox):
            #     value = self.Itol_editor_settings.value(
            #         name, "no setting")  # get stored value from registry
            #     if value != "no setting":
            #         obj.setChecked(
            #             self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QLineEdit):
                if name == "lineEdit_5" and self.autoInputs:
                    self.input(self.autoInputs, obj)
            elif isinstance(obj, QDoubleSpinBox):
                ini_float_ = obj.value()
                float_ = self.Itol_editor_settings.value(name, ini_float_)
                obj.setValue(float(float_))

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
        self.log_gui.close()  # 关闭子窗口
        # 断开showSig和closeSig的槽函数连接
        try:
            self.showSig.disconnect()
        except:
            pass
        try:
            self.closeSig.disconnect()
        except:
            pass

    def showEvent(self, event):
        QTimer.singleShot(100, lambda: self.showSig.emit(self))

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        if isinstance(
                obj,
                QLineEdit):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                self.input(file=files, lineedit=obj)
        if (event.type() == QEvent.Show) and (obj == self.pushButton.toolButton.menu()):
            if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+",
                         self.dir_action.text()) or self.dir_action.text() == "Output Dir: ":
                self.factory.sync_dir(self.dir_action)  ##同步文件夹名字
            menu_x_pos = self.pushButton.toolButton.menu().pos().x()
            menu_width = self.pushButton.toolButton.menu().size().width()
            button_width = self.pushButton.toolButton.size().width()
            pos = QPoint(menu_x_pos - menu_width + button_width,
                         self.pushButton.toolButton.menu().pos().y())
            self.pushButton.toolButton.menu().move(pos)
            return True
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(Itol_editor, self).eventFilter(obj, event)  # 0

    def popup_iTOL_editor_exception(self, text):
        if not self.error_has_shown:
            QMessageBox.critical(
                self,
                "iTOL_editor",
                "<p style='line-height:25px; height:25px'>%s</p>" % text)
            if "Show log" in text:
                self.on_pushButton_9_clicked()

    def popup(self, qpoint):
        popMenu = QMenu(self.parent)
        bgcolor = QAction("Set background color", self,
                          statusTip="Set background color",
                          triggered=self.set_bgcolor)
        fetch_tax = QAction("Fetch taxonomy using information of this column", self,
                            statusTip="Fetch taxonomy using information of this column",
                            triggered=lambda : self.get_taxonomy(by="col"))
        popMenu.addAction(bgcolor)
        popMenu.addAction(fetch_tax)
        if self.parent.indexAt(qpoint).isValid():
            popMenu.exec_(QCursor.pos())

    def set_bgcolor(self):
        indices = self.parent.selectedIndexes()
        index = indices[0]
        if index.column() != 0:
            tax = index.data(Qt.DisplayRole)
            color_ = self.dict_tax_color[tax] if tax in self.dict_tax_color else None
            color = QColorDialog.getColor(QColor(color_))
            if color.isValid():
                if color in list(self.dict_tax_color.values()):
                    reply = QMessageBox.question(
                        self,
                        "Confirmation",
                        "<p style='line-height:25px; height:25px'>This colour has already been used for another "
                        "taxonomic category, \n"
                        "are you sure you still want to use it?</p>",
                        QMessageBox.Yes,
                        QMessageBox.Cancel)
                    if reply == QMessageBox.Cancel:
                        return
                self.dict_tax_color[tax] = color
                self.dataChanged.emit(index, index)

    def set_example_text(self):
        current_text = self.parent.lineEdit.text()
        data_text = self.arraydata[0][0]
        if data_text != current_text:
            self.parent.lineEdit.setText(" ".join(re.split(r"[\W|_]", data_text)))

    def changeGenusName(self, value):
        list_names = re.split(r"[\W|_]", self.parent.lineEdit.text())
        index = len(list_names)-1 if value > len(list_names) else value-1
        genusName = list_names[index]
        self.parent.lineEdit_2.setText(genusName)

    def showGenusName(self, text):
        index = self.parent.spinBox.value()
        genusName = re.split(r"[\W|_]", text)[index-1]
        self.parent.lineEdit_2.setText(genusName)

    def fetch_tax_by_col(self):
        indices = self.parent.selectedIndexes()
        index = indices[0]
        if index.column() == 0:
            return
        LineageNames = [i.upper() for i in self.header[1:]]
        ncbi = NCBITaxa()
        for row in range(len(self.arraydata)):
            tax = self.index(row, index.column()).data(Qt.DisplayRole)
            if not tax:
                continue
            dict_name_id = ncbi.get_name_translator([tax])
            if dict_name_id:
                query_id = dict_name_id[tax][0]
                lineage_ids = ncbi.get_lineage(query_id)
                dict_id_rank = ncbi.get_rank(lineage_ids)
                for id in dict_id_rank:
                    if dict_id_rank[id].upper() in LineageNames:
                        col = LineageNames.index(dict_id_rank[id].upper())
                        self.arraydata[row][col+1] = ncbi.get_taxid_translator([id])[id]
        self.layoutChanged.emit()

    def colourPicker(self, tax):

        colours = list(self.dict_tax_color.values())
        # 生成不重复的随机颜色
        if tax in self.dict_tax_color:
            colour = self.dict_tax_color[tax]
        else:
            colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
            while colour in colours:
                colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
            self.dict_tax_color[tax] = colour
        return colour

    def get_colors(self):
        dict_ = {}
        for row, list_row in enumerate(self.arraydata):
            for col, i in enumerate(list_row):
                if col != 0:
                    if self.hheader.isOn[col]:
                        if i:
                            dict_[i] = self.index(row, col).data(Qt.BackgroundRole).name()
        return dict_

    def get_taxonomy_slot(self):
        LineageNames = [i.upper() for i in self.header[1:]]
        ncbi = NCBITaxa()
        for row in range(len(self.arraydata)):
            index = self.parent.spinBox.value()
            genusName = re.split(r"[\W|_]", self.arraydata[row][0])[index-1]
            dict_name_id = ncbi.get_name_translator([genusName])
            if dict_name_id:
                query_id = dict_name_id[genusName][0]
                lineage_ids = ncbi.get_lineage(query_id)
                dict_id_rank = ncbi.get_rank(lineage_ids)
                for id in dict_id_rank:
                    if dict_id_rank[id].upper() in LineageNames:
                        col = LineageNames.index(dict_id_rank[id].upper())
                        self.arraydata[row][col+1] = ncbi.get_taxid_translator([id])[id]
        self.layoutChanged.emit()

    def get_taxonomy(self, by=None):
        # 进度条
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "Finding... \n(note that if you use this function for the first time, \n"
                           "it will take some time to configure NCBI database)",
            busy=True, parent=self.dialog)
        self.progressDialog.show()
        slot_fun = self.get_taxonomy_slot if by != "col" else self.fetch_tax_by_col
        taxWorker = WorkThread(slot_fun, parent=self)
        taxWorker.finished.connect(self.progressDialog.close)
        taxWorker.start()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = ASTRAL()
    ui.show()
    sys.exit(app.exec_())