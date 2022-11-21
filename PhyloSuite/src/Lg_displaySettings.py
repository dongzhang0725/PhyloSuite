#!/usr/bin/env python
# -*- coding: utf-8 -*-
import platform
import re

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.CustomWidget import TreeModel, CustomTreeIndexWidget
from src.Lg_settings import Setting
from uifiles.Ui_display_setting import Ui_DisplaySettings
import inspect
import os
import sys

from src.factory import Factory
from src.handleGB import ArrayManager


class DisplaySettings(QDialog, Ui_DisplaySettings, object):
    updateSig = pyqtSignal(QModelIndex)

    def __init__(
            self,
            workPath=None,
            parent=None):
        super(DisplaySettings, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.parent = parent
        self.workPath = workPath
        self.setupUi(self)
        # 设置比例
        self.splitter.setStretchFactor(1, 7)
        # 保存主界面设置
        self.data_settings = QSettings(
            self.factory.workPlaceSettingPath + os.sep + 'data_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.data_settings.setFallbacksEnabled(False)
        # 保存设置
        self.display_settings = QSettings(
            self.thisPath + '/settings/display_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.display_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        self.listWidget.installEventFilter(self)
        # 当lineage改变以后，更新树
        self.parent.modify_lineage_finished.connect(self.updateTreee)
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#4-4-2-Information-display-and-modification" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#4-4-2-Information-display-and-modification"
        self.label_6.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        ok
        """
        self.saveNewContents()
        self.updateSig.emit(QFileSystemModel(self).index(self.workPath))
        self.close()

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        Cancel
        """
        self.close()

    @pyqtSlot()
    def on_pushButton_del_clicked(self):
        """
        delete
        """
        listItems = self.listWidget.selectedItems()
        if not listItems:
            return
        for item in listItems:
            if item.text() == "Latest modified":
                QMessageBox.information(
                    self,
                    "PhyloSuite",
                    "<p style='line-height:25px; height:25px'><span style='font-weight:600; color:#ff0000;'>Latest modified</span> must be maintained!!</p>")
                continue
            self.listWidget.takeItem(self.listWidget.row(item))

    def saveNewContents(self):
        key = re.sub(r"/|\\", "_", self.workPath) + "_displayedArray"
        itemsTextList = [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        arrayManager = ArrayManager(self.array)
        new_array = arrayManager.updateArrayByColheader(itemsTextList)
        self.data_settings.setValue(key, new_array)
        ##然后是有新的列就读取对应数据，如果没有新的列就直接展示

    def guiSave(self):
        # Save geometry
        self.display_settings.setValue('size', self.size())
        # self.display_settings.setValue('pos', self.pos())

        # for name, obj in inspect.getmembers(self):
        #     # if type(obj) is QComboBox:  # this works similar to isinstance, but
        #     # missed some field... not sure why?
        #     if isinstance(obj, QlistWidget):
        #         # save combobox selection to registry
        #         text = obj.currentText()
        #         if text:
        #             allItems = [
        #                 obj.itemText(i) for i in range(obj.count())]
        #             allItems.remove(text)
        #             sortItems = [text] + allItems
        #             self.data_settings.setValue(name, sortItems)
        #     if isinstance(obj, QCheckBox):
        #         state = obj.isChecked()
        #         self.data_settings.setValue(name, state)
        #     if isinstance(obj, QRadioButton):
        #         state = obj.isChecked()
        #         self.data_settings.setValue(name, state)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.display_settings.value('size', QSize(685, 511)))
        self.factory.centerWindow(self)
        # self.move(self.display_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QListWidget):
                key = re.sub(r"/|\\", "_", self.workPath) + "_displayedArray"
                self.array = self.data_settings.value(key, None)  #每点一个工作区，就会自动初始化一个，所以一般不会none
                if self.array:
                    displayed_info = self.array[0]
                    self.updatelistWidget(None, displayed_info)
            if isinstance(obj, QTreeView):
                self.updateTreee()
                # key = re.sub(r"/|\\", "_", self.workPath) + "_availableInfo"
                # value = self.data_settings.value(
                #     key, None)  #每点一个工作区，就会自动初始化一个，所以一般不会none
                # treeModel = TreeModel(value)
                # obj.setModel(treeModel)
                # obj.clicked.connect(self.updatelistWidget)
                # obj.expandAll()
                # lineage_set = CustomTreeIndexWidget("Lineages", parent=self.treeView)
                # lineage_set.addBtn("Configure", QIcon(":/picture/resourses/cog.png"))
                # lineage_set.toolBtn.clicked.connect(self.popUpSettings)
                # self.treeView.setIndexWidget(self.treeView.model().index(1, 0, self.treeView.rootIndex()), lineage_set)

    def updateTreee(self):
        key = re.sub(r"/|\\", "_", self.workPath) + "_availableInfo"
        value = self.data_settings.value(
            key, None)  # 每点一个工作区，就会自动初始化一个，所以一般不会none
        # print(value)
        treeModel = TreeModel(value)
        self.treeView.setModel(treeModel)
        self.treeView.clicked.connect(self.updatelistWidget)
        self.treeView.expandAll()
        lineage_set = CustomTreeIndexWidget("Lineages", parent=self.treeView)
        lineage_set.addBtn("Configure", QIcon(":/picture/resourses/cog.png"))
        lineage_set.toolBtn.clicked.connect(self.popUpSettings)
        self.treeView.setIndexWidget(self.treeView.model().index(1, 0, self.treeView.rootIndex()), lineage_set)

    def updatelistWidget(self, treeIndex=None, list_infos=None):
        infos = [treeIndex.internalPointer().itemData] if treeIndex else list_infos
        itemsTextList = [self.listWidget.item(i).text() for i in range(self.listWidget.count())]
        for i in infos:
            if i in itemsTextList + ["Annotations", "Lineages", "Reference", "Sources"]:
                continue
            item = QListWidgetItem(i, parent=self.listWidget)
            if i in ["ID", "Organism"]:
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            # 背景颜色
            if self.listWidget.count() % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            self.listWidget.addItem(item)

    def closeEvent(self, event):
        self.guiSave()

    def popUpSettings(self):
        self.setting = Setting(self)
        # if hasattr(self.parent, "updateTableWorker"):
        self.setting.taxmyChangeSig.connect(lambda x: [self.parent.updateTable(x)])
        self.setting.display_table(self.setting.listWidget.item(0))
        self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.setting.exec_()

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        name = obj.objectName()
        if isinstance(
                obj,
                QListWidget):
            if event.type() == QEvent.ChildRemoved:
                if name == "listWidget":
                    if self.listWidget.item(0).text() != "ID":
                        QMessageBox.critical(
                            self,
                            "Extract sequence",
                            "<p style='line-height:25px; height:25px'>\"ID\" must be the first column!</p>",
                            QMessageBox.Ok)
                        list_infos = [self.listWidget.item(row).text() for row in range(self.listWidget.count())]
                        list_infos.remove("ID")
                        list_infos.insert(0, "ID")
                        self.refreshListWidget(list_infos)
        return super(DisplaySettings, self).eventFilter(obj, event)  # 0

    def refreshListWidget(self, listInfos):
        self.listWidget.clear()
        for i in listInfos:
            if i in ["Annotations", "Lineages", "Reference", "Sources"]:
                continue
            item = QListWidgetItem(i, parent=self.listWidget)
            if i in ["ID", "Organism"]:
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            # 背景颜色
            if self.listWidget.count() % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            self.listWidget.addItem(item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = DisplaySettings()
    ui.show()
    sys.exit(app.exec_())