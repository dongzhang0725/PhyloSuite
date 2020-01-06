#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
description goes here
'''
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from src.factory import Factory
import inspect
import os
import platform

from uifiles.Ui_launcher import Ui_launcher


class Launcher(QDialog, Ui_launcher, object):

    def __init__(self, parent=None):
        super(Launcher, self).__init__(parent)
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.launcher_settings = QSettings(
            self.thisPath + '/settings/launcher_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.launcher_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.setupUi(self)
        self.guiRestore()
        if platform.system().lower() == "darwin":
            cursor = self.textEdit.textCursor()
            self.textEdit.selectAll()
            self.textEdit.setFontPointSize(12)
            self.textEdit.setTextCursor(cursor)

    @pyqtSlot()
    def on_pushButton_clicked(self):
        self.guiSave()
        self.accept()

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        self.guiSave()
        self.reject()

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(
            self, "Select workplace", self.thisPath, options)
        if not directory:
            return
        directory = directory.replace(r"\\", "/")
        # if self.factory.checkPath(directory, parent=self):
            # get the corresponding index for specified string in combobox
        index = self.comboBox.findText(directory)
        if index == -1:  # add to list if not found
            self.comboBox.insertItems(0, [directory])
            index = self.comboBox.findText(directory)
            self.comboBox.setCurrentIndex(index)
        else:
            # preselect a combobox value by index
            self.comboBox.setCurrentIndex(index)

    def guiSave(self):
        # Save geometry
        self.launcher_settings.setValue('size', self.size())
        # self.launcher_settings.setValue('pos', self.pos())
        # 存是否打开这个界面
        LauncherState = self.checkBox.isChecked()
        self.launcher_settings.setValue("ifLaunch", LauncherState)

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                text = obj.currentText()
                allItems = [
                    obj.itemText(i) for i in range(obj.count())]
                allItems.remove(text)
                sortItems = [text] + allItems
                if len(sortItems) > 15:
                    sortItems = sortItems[:15] #只保留15个工作区
                self.WorkPlace = sortItems
                self.launcher_settings.setValue("workPlace", sortItems)

#                 text = obj.currentText()
#                 if os.path.isdir(text):
#                     self.WorkPlace = text
#                     self.launcher_settings.setValue("workPlace", text)
#                 else:
#                     self.launcher_settings.setValue(
#                         "workPlace", self.thisPath)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.launcher_settings.value('size', QSize(457, 20)))
        self.factory.centerWindow(self)
        # self.move(self.launcher_settings.value('pos', QPoint(875, 254)))

        # 恢复checkbox
        LauncherState = self.launcher_settings.value("ifLaunch", "false")
        self.checkBox.setChecked(self.factory.str2bool(LauncherState))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                values = self.launcher_settings.value(
                    "workPlace", [self.thisPath + os.sep + "myWorkPlace"])
                model = obj.model()
                obj.clear()
                for num, i in enumerate(values):
                    item = QStandardItem(i)
                    # 背景颜色
                    if num % 2 == 0:
                        item.setBackground(QColor(255, 255, 255))
                    else:
                        item.setBackground(QColor(237, 243, 254))
                    model.appendRow(item)
#                 if value == "":
#                     continue
                # get the corresponding index for specified string in combobox
#                 index = obj.findText(value)
#                 if index == -1:  # add to list if not found
#                     obj.insertItems(0, [value])
#                     index = obj.findText(value)
#                     obj.setCurrentIndex(index)
#                 else:
#                     # preselect a combobox value by index
#                     obj.setCurrentIndex(index)

    def closeEvent(self, event):
        self.guiSave()