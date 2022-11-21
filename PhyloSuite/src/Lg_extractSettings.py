#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import OrderedDict

import shutil
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.CustomWidget import MyExtractSettingModel
from uifiles.Ui_extract_setting import Ui_ExtractSettings
import inspect
import os
import sys

from src.factory import Factory


class ExtractSettings(QDialog, Ui_ExtractSettings, object):
    closeSig = pyqtSignal(OrderedDict)

    def __init__(
            self,
            parent=None):
        super(ExtractSettings, self).__init__(parent)
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.setupUi(self)
        # # 设置比例
        # self.splitter.setStretchFactor(1, 7)
        # 保存主界面设置
        self.GenBankExtract_settings = QSettings(
            self.thisPath + '/settings/GenBankExtract_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.GenBankExtract_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.tableView.installEventFilter(self)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.listWidget.installEventFilter(self)
        self.listWidget_2.installEventFilter(self)
        tableView_popMenu = QMenu(self)
        edit = QAction("Edit", self,
                            statusTip="Edit select item",
                            triggered=lambda: self.tableView.edit(self.tableView.currentIndex()))
        delete = QAction("Delete", self,
                       shortcut=QKeySequence.Delete,
                       statusTip="Remove select rows",
                       triggered=self.on_toolButton_4_clicked)
        add = QAction("Add row", self,
                       statusTip="Add row",
                       triggered=self.on_toolButton_3_clicked)
        export = QAction("Export", self,
                      statusTip="Export table",
                      triggered=self.on_toolButton_5_clicked)
        import_ = QAction("Import", self,
                      statusTip="Import table",
                      triggered=self.on_toolButton_6_clicked)
        tableView_popMenu.addAction(edit)
        tableView_popMenu.addAction(delete)
        tableView_popMenu.addAction(add)
        tableView_popMenu.addAction(export)
        tableView_popMenu.addAction(import_)
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(lambda : tableView_popMenu.exec_(QCursor.pos()))
        self.listWidget.itemRemoveSig.connect(self.depositeData)
        self.listWidget.itemChanged.connect(self.keepMitoFeature)
        self.listWidget.itemSelectionChanged.connect(self.keepMitoFeature)
        self.listWidget_2.itemRemoveSig.connect(self.depositeData)
        self.listWidget_2.model().layoutChanged.connect(self.depositeData)
        self.listWidget_2.model().layoutChanged.connect(self.listWidget_2.refreshBackColors)   ##拖拽以后刷新颜色
        # 恢复用户的设置
        self.checkBox_2.stateChanged.connect(self.change_label3)
        self.checkBox_2.toggled.connect(lambda bool_: self.changeCheckboxSettings("extract all features", bool_))
        self.checkBox.toggled.connect(lambda bool_: self.changeCheckboxSettings("extract listed gene", bool_))
        self.checkBox_3.toggled.connect(lambda bool_: self.changeCheckboxSettings("extract intergenic regions", bool_))
        self.checkBox_4.toggled.connect(lambda bool_: self.changeCheckboxSettings("extract overlapping regions", bool_))
        self.spinBox.valueChanged[int].connect(lambda value: self.changeCheckboxSettings("intergenic regions threshold", value))
        self.spinBox_2.valueChanged[int].connect(
            lambda value: self.changeCheckboxSettings("overlapping regions threshold", value))
        self.guiRestore()
        # 默认显示完整表格
        self.on_toolButton_7_clicked()
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/PhyloSuite-demo/customize_extraction/" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/customize_extraction/"
        self.label_6.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

    @pyqtSlot()
    def on_toolButton_clicked(self):
        """
        add Feature
        """
        feature, ok = QInputDialog.getText(
            self, 'Add Feature', 'New Feature name:')
        if ok:
            self.listWidget.addItemWidget(feature.strip())
            self.listWidget.CurrentItemWidget.itemOpSignal.connect(self.featureRemoved)
            self.listWidget.item(self.listWidget.count() - 1).setSelected(True)
            # self.listWidget.setItemSelected(self.listWidget.item(self.listWidget.count()-1), True)
            self.changeQualifier(self.listWidget.count()-1)
            self.depositeData()

    @pyqtSlot()
    def on_toolButton_2_clicked(self):
        """
        add Qualifier
        """
        Qualifier, ok = QInputDialog.getText(
            self, 'Add Qualifier', 'New Qualifier name:')
        if ok:
            self.listWidget_2.addItemWidget(Qualifier.strip())
            self.depositeData()

    @pyqtSlot()
    def on_toolButton_4_clicked(self):
        """
        delete tableview
        """
        indices = self.tableView.selectedIndexes()
        currentModel = self.tableView.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in indices), reverse=True)
            for row in rows:
                currentModel.layoutAboutToBeChanged.emit()
                currentData.pop(row)
                currentModel.layoutChanged.emit()

    @pyqtSlot()
    def on_toolButton_3_clicked(self):
        """
        add tableview
        """
        currentModel = self.tableView.model()
        if currentModel:
            currentData = currentModel.arraydata
            header = currentModel.headerdata
            currentModel.layoutAboutToBeChanged.emit()
            length = len(header)
            currentData.append([""] * length)
            currentModel.layoutChanged.emit()
            self.tableView.scrollToBottom()

    @pyqtSlot()
    def on_toolButton_6_clicked(self):
        """
        import
        """
        self.importArray()

    @pyqtSlot()
    def on_toolButton_5_clicked(self):
        """
        export
        """
        export_content = self.dict_gbExtract_set[self.currentVersion]["Names unification"]
        content = "\n".join([",".join(i) for i in export_content])
        fileName = QFileDialog.getSaveFileName(
            self, "Export", "replace", "CSV Format(*.csv)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    @pyqtSlot()
    def on_toolButton_7_clicked(self):
        """
        adjust table
        """
        self.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def guiSave(self):
        # Save geometry
        self.GenBankExtract_settings.setValue('size', self.size())
        # self.GenBankExtract_settings.setValue('pos', self.pos())
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QSpinBox):
                ## intergenic regions size
                intergenic_region_size = self.spinBox.value()
                self.dict_gbExtract_set[self.currentVersion][
                    "intergenic regions threshold"] = intergenic_region_size
                ## overlapping regions size
                overlapping_region_size = self.spinBox_2.value()
                self.dict_gbExtract_set[self.currentVersion][
                    "overlapping regions threshold"] = overlapping_region_size
        self.GenBankExtract_settings.setValue('set_version', self.dict_gbExtract_set)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.GenBankExtract_settings.value('size', QSize(685, 511)))
        self.factory.centerWindow(self)
        # self.move(self.GenBankExtract_settings.value('pos', QPoint(875, 254)))
        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QPushButton):
                if name == "pushButton_13":
                    menu = QMenu(self)
                    action_import = QAction(QIcon(":/picture/resourses/Custom-Icon-Design-Flatastic-1-Down.png"),
                                            "Import settings", menu)
                    menu.addAction(action_import)
                    action_export = QAction(QIcon(":/picture/resourses/up.png"),
                                            "Export settings", menu)
                    menu.addAction(action_export)
                    menu.triggered.connect(self.ImportExport)
                    obj.setMenu(menu)

            # if isinstance(obj, QCheckBox):
            #     if name == "checkBox":
            #         value = self.GenBankExtract_settings.value(
            #             "extract listed gene", False)  # get stored value from registry
            #         if value:
            #             obj.setChecked(
            #                 self.factory.str2bool(value))  # restore checkbox
            #     if name == "checkBox_2":
            #         value = self.GenBankExtract_settings.value(
            #             "extract all features", False)  # get stored value from registry
            #         if value:
            #             obj.setChecked(
            #                 self.factory.str2bool(value))  # restore checkbox
        self.refreshVersion()

    def depositeData(self, warning=False):
        if warning == "retain":
            ##最后一项不让删##
            QMessageBox.information(
                self,
                "Settings",
                "<p style='line-height:25px; height:25px'>At least one item should be retained!</p>")
            return
        try:
            self.dict_gbExtract_set[self.currentVersion]["Features to be extracted"] =\
                [self.listWidget.text(i) for i in range(self.listWidget.count())]
            self.dict_gbExtract_set[self.currentVersion][self.current_qualifier_text] = \
                [self.listWidget_2.text(i) for i in range(self.listWidget_2.count())]
            self.dict_gbExtract_set[self.currentVersion]["Names unification"] = \
                [self.tableView.model().headerdata] + self.tableView.model().arraydata
            self.GenBankExtract_settings.setValue('set_version', self.dict_gbExtract_set)
        except: pass

    def closeEvent(self, event):
        self.guiSave()
        self.closeSig.emit(self.dict_gbExtract_set)

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        if isinstance(
                obj,
                QTableView):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                csvs = [j for j in files if os.path.splitext(j)[1].upper() == ".CSV"]
                tsvs = [j for j in files if os.path.splitext(j)[1].upper() == ".TSV"]
                list_csvs = csvs + tsvs
                self.importArray(list_csvs[0])
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Delete:
                    self.on_toolButton_4_clicked()
                    return True
        if isinstance(
                obj,
                QListWidget):
            if event.type() == QEvent.ChildRemoved:
                self.depositeData()
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(ExtractSettings, self).eventFilter(obj, event)  # 0

    def switchVersion(self, action):
        version = action.text()
        list_now_versions = list(self.dict_gbExtract_set.keys())
        if version == "Add new version":
            inputDialog = QInputDialog(self)
            inputDialog.setMinimumWidth(500)
            versionName, ok = inputDialog.getText(
                self, 'Create version', 'New version name:%s'%(" "*26))
            version_num = self.factory.numbered_Name(list_now_versions, versionName, True)[0]
            if ok:
                new_dict_data = OrderedDict([(version_num, self.init_version)])
                new_dict_data.update(self.dict_gbExtract_set) ##为了让新添加的在最前面
                self.dict_gbExtract_set = new_dict_data
        elif version == "Delete current version":
            if list_now_versions[0] == "Mitogenome":
                QMessageBox.information(
                    self,
                    "Settings",
                    "<p style='line-height:25px; height:25px'><span style='font-weight:600; color:#ff0000;'>Mitogenome version</span> should be retained!</p>")
            else:
                self.dict_gbExtract_set.popitem(last=False)
        else:
            if version != list_now_versions[0]:
                list_now_versions.remove(version)
                reorder_list = [version] + list_now_versions
                self.dict_gbExtract_set = OrderedDict((i, self.dict_gbExtract_set[i]) for i in reorder_list)
        self.GenBankExtract_settings.setValue('set_version', self.dict_gbExtract_set)
        self.refreshVersion()

    def refreshVersion(self):
        self.init_version = OrderedDict([("Features to be extracted", ["rRNA"]),
                                         ("Qualifiers to be recognized (rRNA):", ["gene", "product", "note"]),
                                         ("Names unification", [["Old Name", "New Name"], ["18S ribosomal RNA", "18S"]])])
        self.dict_gbExtract_set = self.GenBankExtract_settings.value("set_version",
                                                                     OrderedDict([("18S", self.init_version)]))
        self.allVersions = list(self.dict_gbExtract_set.keys())
        self.currentVersion = self.allVersions[0]
        ###pushbutton
        menu = QMenu(self)
        for num, i in enumerate(self.allVersions):
            if num == 0:
                action_1 = QAction(QIcon(":/picture/resourses/caribbean-blue-clipart-12.png"),
                                   i, menu)
                self.pushButton_14.setText("Current version: %s"%action_1.text())
                menu.addAction(action_1)
                continue
            action = QAction(i, menu)
            menu.addAction(action)
        menu.addAction(QAction(QIcon(":/picture/resourses/add-icon.png"), "Add new version", menu))
        menu.addAction(QAction(QIcon(":/picture/resourses/delete.png"), "Delete current version", menu))
        menu.triggered.connect(self.switchVersion)
        self.pushButton_14.setMenu(menu)
        ###listwidget
        self.listWidget.clear()
        features = self.dict_gbExtract_set[self.currentVersion]["Features to be extracted"]
        for feature in features:
            self.listWidget.addItemWidget(feature)
            self.listWidget.CurrentItemWidget.itemOpSignal.connect(self.featureRemoved)
            self.dict_gbExtract_set[self.currentVersion].setdefault("Qualifiers to be recognized (%s):"%feature,
                                                                    ["gene", "product", "note"])
        self.listWidget.currentRowChanged.connect(self.changeQualifier)
        self.changeQualifier(0)
        self.listWidget.item(0).setSelected(True)
        # self.listWidget.setItemSelected(self.listWidget.item(0), True)
        ###tableview
        unify = self.dict_gbExtract_set[self.currentVersion]["Names unification"]
        header = unify[0]
        array = unify[1:]
        tableModel = MyExtractSettingModel(array, header)
        self.tableView.setModel(tableModel)
        self.tableView.resizeColumnsToContents()
        tableModel.dataChanged.connect(self.depositeData)
        tableModel.layoutChanged.connect(self.depositeData)
        ## extract all features
        ifExtractAll = self.dict_gbExtract_set[self.currentVersion]["extract all features"] if "extract all features" \
                                                            in self.dict_gbExtract_set[self.currentVersion] else False
        self.checkBox_2.setChecked(ifExtractAll)
        ## extract listed genes
        ifExtractlistGene = self.dict_gbExtract_set[self.currentVersion]["extract listed gene"] if "extract listed gene" \
                                                            in self.dict_gbExtract_set[self.currentVersion] else False
        self.checkBox.setChecked(ifExtractlistGene)
        ## extract intergenic regions
        if_extract_inter = self.dict_gbExtract_set[self.currentVersion]["extract intergenic regions"] if "extract intergenic regions" \
                                                            in self.dict_gbExtract_set[self.currentVersion] else True
        self.checkBox_3.setChecked(if_extract_inter)
        ## extract overlapping regions
        if_extract_overl = self.dict_gbExtract_set[self.currentVersion][
            "extract overlapping regions"] if "extract overlapping regions" \
                                             in self.dict_gbExtract_set[self.currentVersion] else True
        self.checkBox_4.setChecked(if_extract_overl)
        ## intergenic regions size
        intergenic_region_size = self.dict_gbExtract_set[self.currentVersion][
            "intergenic regions threshold"] if "intergenic regions threshold" \
                                             in self.dict_gbExtract_set[self.currentVersion] else 200
        self.spinBox.setValue(intergenic_region_size)
        ## overlapping regions size
        overlapping_region_size = self.dict_gbExtract_set[self.currentVersion][
            "overlapping regions threshold"] if "overlapping regions threshold" \
                                               in self.dict_gbExtract_set[self.currentVersion] else 1
        self.spinBox_2.setValue(overlapping_region_size)
        # self.checkBox_3.toggled.connect(lambda bool_: self.changeCheckboxSettings("extract intergenic regions", bool_))
        # self.checkBox_4.toggled.connect(lambda bool_: self.changeCheckboxSettings("extract overlapping regions", bool_))
        # self.spinBox.valueChanged[int].connect(
        #     lambda value: self.changeCheckboxSettings("intergenic regions threshold", value))
        # self.spinBox_2.valueChanged[int].connect(
        #     lambda value: self.changeCheckboxSettings("overlapping regions threshold", value))
        # if self.checkBox_2.isChecked():
        #     self.change_label3(True)

    def input_array(self, byFile=False):
        if not byFile:
            file = QFileDialog.getOpenFileName(
                self, "Input Table", filter="Table format(*.csv *.tsv);;")[0]
        else:
            file=byFile
        if file:
            with open(file, encoding="utf-8", errors='ignore') as f:
                content = f.read().strip()
            if "Old Name,New Name" in content:
                list_ = [i.strip().split(",") for i in [j for j in content.split("\n")] if "Old Name,New Name" not in i]
            else:
                list_ = [i.strip().split("\t") for i in [j for j in content.split("\n")] if "Old Name\tNew Name" not in i]
            return list_
        else:
            return None

    def checkArray(self, array):
        for num, i in enumerate(array):
            while "" in array[num]:
                array[num].remove("")
        # ##去除重复的
        #只要前2个
        return [i[:2] for i in array if len(i) >= 2]

    def importArray(self, byFile=False):
        new_array = self.input_array(byFile)
        if not new_array:
            return
        new_array = self.checkArray(new_array)
        self.dict_gbExtract_set[self.currentVersion]["Names unification"].extend(new_array)
        self.tableView.model().arraydata = self.dict_gbExtract_set[self.currentVersion]["Names unification"][1:]
        self.tableView.model().uniqueArray()
        self.tableView.model().layoutChanged.emit()
        self.tableView.scrollToBottom()

    def ImportExport(self, action):
        text = action.text()
        if text == "Import settings":
            fileName = QFileDialog.getOpenFileName(
                self, "Import settings", filter="Setting Format(*.setting)")[0]
            if fileName:
                shutil.copyfile(fileName, self.thisPath + '/settings/GenBankExtract_settings.ini')
                self.GenBankExtract_settings = QSettings(
                    self.thisPath + '/settings/GenBankExtract_settings.ini', QSettings.IniFormat)
                # File only, no fallback to registry or or.
                self.GenBankExtract_settings.setFallbacksEnabled(False)
                self.refreshVersion()
        elif text == "Export settings":
            fileName = QFileDialog.getSaveFileName(
                self, "Export settings", "GenBank_extract", "Setting Format(*.setting)")
            if fileName[0]:
                shutil.copyfile(self.thisPath + '/settings/GenBankExtract_settings.ini', fileName[0])

    def changeQualifier(self, row):
        itemwidget = self.listWidget.itemWidget(self.listWidget.item(row))
        if not itemwidget:
            return
        text = itemwidget.text
        self.current_qualifier_text = "Qualifiers to be recognized (%s):"%text
        self.label_3.setText(self.current_qualifier_text)
        self.listWidget_2.clear()
        qualifiers = self.dict_gbExtract_set[self.currentVersion].setdefault(self.current_qualifier_text,
                                                                             ["gene", "product", "note"])
        for qualifier in qualifiers:
            self.listWidget_2.addItemWidget(qualifier)

    def featureRemoved(self, listwidgetItem, text):
        if (self.listWidget.count() == 1) and (listwidgetItem == self.listWidget.item(0)):
            return
        removed_qualifier = "Qualifiers to be recognized (%s):" % text
        self.dict_gbExtract_set[self.currentVersion].pop(removed_qualifier)

    def keepMitoFeature(self):
        ##保留线粒体基因组的 CDS，rRNA和tRNA
        if self.currentVersion == "Mitogenome":
            for row in range(self.listWidget.count()):
                itemWidg = self.listWidget.itemWidget(self.listWidget.item(row))
                if itemWidg and (itemWidg.text in ["CDS", "rRNA", "tRNA"]):
                    # if itemWidg.bt_close.isVisible():
                    itemWidg.bt_close.setVisible(False)

    def change_label3(self, bool_):
        # self.GenBankExtract_settings.setValue("extract all features", bool_)
        if bool_:
            self.current_qualifier_text = "Qualifiers to be recognized (all):"
            self.label_3.setText(self.current_qualifier_text)
            self.listWidget_2.clear()
            qualifiers = self.dict_gbExtract_set[self.currentVersion].setdefault(self.current_qualifier_text,
                                                                                 ["gene", "product", "note"])
            for qualifier in qualifiers:
                self.listWidget_2.addItemWidget(qualifier)
        else:
            self.changeQualifier(0)

    def changeCheckboxSettings(self, key, bool_):
        self.dict_gbExtract_set[self.currentVersion][key] = bool_


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = ExtractSettings()
    ui.show()
    sys.exit(app.exec_())