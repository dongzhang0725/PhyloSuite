#!/usr/bin/env python
# -*- coding: utf-8 -*-
import platform

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.CustomWidget import MyColorsetsTableModel
from src.factory import Factory, WorkThread
import inspect
import os
import sys

from uifiles.Ui_color_sets import Ui_color_editor

class Colorset(QDialog, Ui_color_editor, object):

    def __init__(self, parent=None):
        super(Colorset, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.parent = parent
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.setupUi(self)
        # 保存设置
        self.color_settings = QSettings(
                                    self.thisPath +
                                    '/settings/color_sets.ini',
                                    QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.color_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()

    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        """
        add row
        """
        currentModel = self.tableView.model()
        if currentModel:
            currentData = currentModel.arraydata
            currentHeader = currentModel.header
            rowName, ok = QInputDialog.getText(
                self, 'Settings', 'Row Name:')
            if rowName in self.tableView.model().header:
                QMessageBox.information(
                    self,
                    "Color editor",
                    "<p style='line-height:25px; height:25px'>The name exists, please set a new name! </p>")
                return
            if ok and rowName:
                rowName = rowName.strip()
                currentHeader.append(rowName)
                currentModel.layoutAboutToBeChanged.emit()
                length = len(currentData[0])
                currentData.append([""] * length)
                currentModel.layoutChanged.emit()
                self.tableView.scrollToBottom()

    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        """
        add column
        """
        currentModel = self.tableView.model()
        if currentModel:
            currentData = currentModel.arraydata
            currentModel.layoutAboutToBeChanged.emit()
            for i in currentData:
                i.append("")
            currentModel.layoutChanged.emit()
            self.tableView.scrollTo(self.tableView.model().index(0, len(self.tableView.model().header)-1))

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        """
        delete row
        """
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            currentHeader = currentModel.header
            rows = sorted(set(index.row() for index in indices), reverse=True)
            for row in rows:
                currentModel.layoutAboutToBeChanged.emit()
                currentData.pop(row)
                currentHeader.pop(row)
                currentModel.layoutChanged.emit()

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        delete column
        """
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            columns = sorted(set(index.column() for index in indices), reverse=True)
            for column in columns:
                currentModel.layoutAboutToBeChanged.emit()
                for i in currentData:
                    i.pop(column)
                currentModel.layoutChanged.emit()

    def guiSave(self):
        # Save geometry
        self.color_settings.setValue('size', self.size())
        # self.color_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QTableView):
                self.save_colors()

    def guiRestore(self):

        # Restore geometry
        self.resize(self.color_settings.value('size', QSize(900, 500)))
        self.factory.centerWindow(self)

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QTableView):
                PS_color1 = [
                    "#2E91E5",
                    "#E15F99",
                    "#1CA71C",
                    "#FB0D0D",
                    "#DA16FF",
                    "#222A2A",
                    "#B68100",
                    "#750D86",
                    "#EB663B",
                    "#511CFB",
                    "#00A08B",
                    "#FB00D1",
                    "#FC0080",
                    "#B2828D",
                    "#6C7C32",
                    "#778AAE",
                    "#862A16",
                    "#A777F1",
                    "#620042",
                    "#1616A7",
                    "#DA60CA",
                    "#6C4516",
                    "#0D2A63",
                    "#AF0038",
                ]
                PS_color2 = [
                    "#FD3216",
                    "#00FE35",
                    "#6A76FC",
                    "#FED4C4",
                    "#FE00CE",
                    "#0DF9FF",
                    "#F6F926",
                    "#FF9616",
                    "#479B55",
                    "#EEA6FB",
                    "#DC587D",
                    "#D626FF",
                    "#6E899C",
                    "#00B5F7",
                    "#B68E00",
                    "#C9FBE5",
                    "#FF0092",
                    "#22FFA7",
                    "#E3EE9E",
                    "#86CE00",
                    "#BC7196",
                    "#7E7DCD",
                    "#FC6955",
                    "#E48F72",
                ]
                PS_color3 = [
                        "#636EFA",
                        "#EF553B",
                        "#00CC96",
                        "#AB63FA",
                        "#FFA15A",
                        "#19D3F3",
                        "#FF6692",
                        "#B6E880",
                        "#FF97FF",
                        "#FECB52",
                    ]
                PS_color4 = [
                    "#1F77B4",
                    "#FF7F0E",
                    "#2CA02C",
                    "#D62728",
                    "#9467BD",
                    "#8C564B",
                    "#E377C2",
                    "#7F7F7F",
                    "#BCBD22",
                    "#17BECF",
                ]
                PS_color5 = [
                    "#3366CC",
                    "#DC3912",
                    "#FF9900",
                    "#109618",
                    "#990099",
                    "#0099C6",
                    "#DD4477",
                    "#66AA00",
                    "#B82E2E",
                    "#316395",
                ]
                PS_color6 = [
                    "#4C78A8",
                    "#F58518",
                    "#E45756",
                    "#72B7B2",
                    "#54A24B",
                    "#EECA3B",
                    "#B279A2",
                    "#FF9DA6",
                    "#9D755D",
                    "#BAB0AC",
                ]
                default_colors = {
                                  "PhyloSuite color1": PS_color1,
                                  "PhyloSuite color2": PS_color2,
                                  "PhyloSuite color3": PS_color3,
                                  "PhyloSuite color4": PS_color4,
                                  "PhyloSuite color5": PS_color5,
                                  "PhyloSuite color6": PS_color6,
                                  }
                values = self.color_settings.value("PhyloSuite colors", default_colors)
                header = []
                array = []
                for value in values:
                    header.append(value)
                    array.append(values[value])
                array = self.flat_array(array)
                self.colors_model = MyColorsetsTableModel(array, header, parent=self.tableView)
                self.tableView.setModel(self.colors_model)
                self.colors_model.dataChanged.connect(self.save_colors)
                self.colors_model.layoutChanged.connect(self.save_colors)

    def flat_array(self, array):
        max_cols = max([len(row) for row in array])
        new_array = []
        for i in array:
            new_array.append(i + [""]*(max_cols-len(i)))
        return new_array

    def closeEvent(self, event):
        self.guiSave()

    def save_colors(self):
        header = self.tableView.model().header
        array = self.tableView.model().arraydata
        dict_colors = {i:array[num] for num,i in enumerate(header)}
        self.color_settings.setValue("PhyloSuite colors", dict_colors)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = Colorset()
    ui.show()
    sys.exit(app.exec_())