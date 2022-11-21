#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

import datetime
import multiprocessing
import random
import time

from src.Lg_extractSettings import ExtractSettings
from src.Lg_settings import Setting
from uifiles.Ui_extracter import Ui_Extractor
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import os
import sys
from src.handleGB import GBextract
import inspect
from src.factory import Factory, WorkThread
import traceback
from collections import OrderedDict
import re
from src.CustomWidget import MyComboBox
import platform


class ExtractGB(QDialog, Ui_Extractor, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条
    progressDialogSig = pyqtSignal(int)  # 控制进度条
    threadFinished = pyqtSignal()
    startButtonStatusSig = pyqtSignal(list)

    def __init__(
            self,
            gb_files=None,
            list_names=None,
            workPath=None,
            totleID=None,
            clearFolderSig=None,
            focusSig=None,
            parent=None):
        super(ExtractGB, self).__init__(parent)
        self.parent = parent
        self.function_name = "Extraction"
        self.setupUi(self)
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.gb_files = gb_files
        self.workPath = workPath
        self.totleID = totleID
        self.clearFolderSig = clearFolderSig
        self.list_names = list_names
        self.focusSig = focusSig
        self.installEventFilter(self)
        self.dict_icon = {
            "rectangle": ":/itol_domain/resourses/itol/re.png",
            "horizontal hexagon": ":/itol_domain/resourses/itol/hh.png",
            "vertical hexagon": ":/itol_domain/resourses/itol/hv.png",
            "ellipse": ":/itol_domain/resourses/itol/el.png",
            "rhombus (diamond)": ":/itol_domain/resourses/itol/di.png",
            "right pointing triangle": ":/itol_domain/resourses/itol/tr.png",
            "left pointing triangle": ":/itol_domain/resourses/itol/tl.png",
            "left pointing pentagram": ":/itol_domain/resourses/itol/pl.png",
            "right pointing pentagram": ":/itol_domain/resourses/itol/pr.png",
            "up pointing pentagram": ":/itol_domain/resourses/itol/pu.png",
            "down pointing pentagram": ":/itol_domain/resourses/itol/pd.png",
            "octagon": ":/itol_domain/resourses/itol/oc.png",
            "rectangle (gap)": ":/itol_domain/resourses/itol/gp.png"}

        self.dict_shape = {
            "rectangle": "RE",
            "horizontal hexagon": "HH",
            "vertical hexagon": "HV",
            "ellipse": "EL",
            "rhombus (diamond)": "DI",
            "right pointing triangle": "TR",
            "left pointing triangle": "TL",
            "left pointing pentagram": "PL",
            "right pointing pentagram": "PR",
            "up pointing pentagram": "PU",
            "down pointing pentagram": "PD",
            "octagon": "OC",
            "rectangle (gap)": "GP"}

        self.extractGB_settings = QSettings(
            self.thisPath + '/settings/extractGB_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.extractGB_settings.setFallbacksEnabled(False)
        self.settings_ini = QSettings(self.thisPath + '/settings/setting_settings.ini', QSettings.IniFormat)
        self.settings_ini.setFallbacksEnabled(False)
        # 保存主界面设置
        self.data_settings = QSettings(
            self.factory.workPlaceSettingPath + os.sep + 'data_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.data_settings.setFallbacksEnabled(False)
        # 恢复用户的设置
        self.displaySettings()
        self.guiRestore()
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)

        self.progressSig.connect(self.runProgress)
        self.exception_signal.connect(self.popupException)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.tableWidget_2.installEventFilter(self)
        self.table_popMenu = QMenu(self)
        self.Copy = QAction("Copy", self,
                              statusTip="Copy color(s)",
                              shortcut="Ctrl+C",
                              triggered=self.copyColor)
        self.Cut = QAction("Cut", self,
                              statusTip="Cut color(s)",
                              shortcut="Ctrl+X",
                              triggered=self.cutColor)
        self.Paste = QAction("Paste", self,
                              statusTip="Paste color(s)",
                              shortcut="Ctrl+V",
                              triggered=self.pasteColor)
        self.remove = QAction("Delete", self,
                                  shortcut=QKeySequence.Delete,
                                  statusTip="Remove color(s)",
                                  triggered=self.on_pushButton_9_clicked)
        self.table_popMenu.addAction(self.Copy)
        self.table_popMenu.addAction(self.Cut)
        self.table_popMenu.addAction(self.Paste)
        self.table_popMenu.addAction(self.remove)
        self.tableWidget_2.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget_2.customContextMenuRequested.connect(lambda x: self.table_popMenu.exec_(QCursor.pos()))
        self.comboBox_6.activated[str].connect(self.switchSeqType)
        self.switchSeqType(self.comboBox_6.currentText())
        # 信号槽
        self.checkBox.toggled.connect(self.judgeCodonWinstallation)
        self.progressDialogSig.connect(self.Progress)
        # 给开始按钮添加菜单
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        self.work_action = QAction(QIcon(":/picture/resourses/work.png"), "", menu)
        self.work_action.triggered.connect(lambda: self.factory.swithWorkPath(self.work_action, parent=self))
        self.dir_action = QAction(QIcon(":/picture/resourses/folder.png"), "Output Dir: ", menu)
        self.dir_action.triggered.connect(lambda: self.factory.set_direct_dir(self.dir_action, self))
        menu.addAction(self.work_action)
        menu.addAction(self.dir_action)
        self.pushButton_2.toolButton.setMenu(menu)
        self.pushButton_2.toolButton.menu().installEventFilter(self)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下
        self.checkBox_2.toggled.connect(self.judgeMAFFT)
        self.qmut_progress = QMutex() # 创建线程锁
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-1-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-1-1-Brief-example"
        self.label_3.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        execute program
        """
        self.dict_args = {}
        self.dict_args["progressSig"] = self.progressSig
        self.dict_args["gb_files"] = self.gb_files
        self.dict_args["workPath"] = self.workPath
        # 创建输出文件夹
        self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
        self.exportPath = self.factory.creat_dirs(self.workPath +
                                                        os.sep + "extract_results" + os.sep + self.output_dir_name)
        self.dict_args["exportPath"] = self.exportPath
        self.dict_args["codon"] = str(
            self.comboBox_9.currentText()).split(" ")[0]
        self.dict_args["Name Type"] = [self.comboBox_4.itemText(i) for i in range(self.comboBox_4.count())
                                               if self.comboBox_4.model().item(i).checkState() == Qt.Checked]
        # self.dict_args["Gene Number"] = str(
        #     self.comboBox_8.currentText())
        # bool
        self.dict_args["if ignore duplicated"] = True #self.checkBox_2.isChecked()
        self.dict_args["if statistics"] = True #self.checkBox_3.isChecked()
        self.dict_args["if itol"] = self.groupBox_4.isChecked()
        self.dict_args["totleID"] = self.totleID
        self.dict_args["seq type"] = str(self.comboBox_6.currentText())
        self.dict_args["checked gene names"] = self.fetch_checked_gene_names()
        self.dict_args["itol gene display"] = OrderedDict()
        for row, gene_name in enumerate(self.dict_args["checked gene names"]):
            color = self.tableWidget.item(row, 1).text()
            size = self.tableWidget.item(row, 2).text()
            shape_combo = self.tableWidget.cellWidget(row, 3)
            shape = self.dict_shape[shape_combo.currentText()] # 转为缩写形式
            self.dict_args["itol gene display"][gene_name] = [color, size, shape]
        self.dict_args["gene interval"] = self.doubleSpinBox.value()
        self.dict_args["included_lineages"] = [self.comboBox_7.itemText(i) for i in range(self.comboBox_7.count())
                                               if self.comboBox_7.model().item(i).checkState() == Qt.Checked]
        # {"Family":["red", "green", ""]}
        dict_color_array = self.getLineageColor()
        for i in dict_color_array:
            while "" in dict_color_array[i]:
                # 删除空行
                dict_color_array[i].remove("")
        self.dict_args["lineage color"] = dict_color_array
        ##提取的设置
        dict_extract_settings = copy.deepcopy(self.dict_gbExtract_set[self.comboBox_6.currentText()])
        #提取所有的话，记得先判断有没有那个键
        extract_all_features = dict_extract_settings.pop("extract all features") if "extract all features" \
                                                                                    in dict_extract_settings else False
        self.dict_args["extract_intergenic_regions"] = dict_extract_settings.pop("extract intergenic regions") if "extract intergenic regions" \
                                                                                    in dict_extract_settings else True
        self.dict_args["extract_overlapping_regions"] = dict_extract_settings.pop("extract overlapping regions") if "extract overlapping regions" \
                                                                             in dict_extract_settings else True
        self.dict_args["intergenic_regions_threshold"] = dict_extract_settings.pop("intergenic regions threshold") if "intergenic regions threshold" \
                                                                             in dict_extract_settings else 200
        self.dict_args["overlapping_regions_threshold"] = dict_extract_settings.pop(
            "overlapping regions threshold") if "overlapping regions threshold" \
                                               in dict_extract_settings else 1
        self.dict_args["features"] = dict_extract_settings.pop("Features to be extracted") if not extract_all_features else "All"
        # self.dict_args["features"] = "All" if self.extract_all_features else self.dict_args["features"]
        name_unify = dict_extract_settings.pop("Names unification")
        self.dict_args["replace"] = {i[0]: i[1] for i in name_unify}
        self.dict_args["extract_list_gene"] = dict_extract_settings.pop("extract listed gene") if "extract listed gene" \
                                                                                    in dict_extract_settings else False
        self.dict_args["qualifiers"] = dict_extract_settings  ###只剩下qualifier的设置
        self.dict_args["extract_entire_seq"] = self.radioButton.isChecked()
        self.dict_args["entire_seq_name"] = self.lineEdit.text() if self.lineEdit.text() else "sequence"
        self.dict_args["cal_codon_bias"] = self.checkBox.isChecked()
        self.dict_args["CodonW_exe"] = self.factory.programIsValid("CodonW", mode="tool") if self.checkBox.isChecked() else None
        self.dict_args["start_gene_with"] = "cox1" if not self.lineEdit_2.text() else self.lineEdit_2.text()
        self.dict_args["analyze all PCGs"] = self.groupBox_3.isChecked()
        self.dict_args["analyze RSCU"] = self.checkBox_8.isChecked()
        self.dict_args["analyze 1st codon"] = self.checkBox_3.isChecked()
        self.dict_args["analyze 2nd codon"] = self.checkBox_4.isChecked()
        self.dict_args["analyze 3rd codon"] = self.checkBox_5.isChecked()
        self.dict_args["analyze all rRNAs"] = self.checkBox_13.isChecked()
        self.dict_args["analyze all tRNAs"] = self.checkBox_14.isChecked()
        self.dict_args["analyze + sequence"] = self.checkBox_6.isChecked()
        self.dict_args["analyze - sequence"] = self.checkBox_7.isChecked()
        self.dict_args["resolve duplicates"] = self.checkBox_2.isChecked()
        self.dict_args["exception_signal"] = self.exception_signal
        ## NCR ratio
        self.dict_args["cal_NCR_ratio"] = self.groupBox_8.isChecked()
        self.dict_args["NCR_features"] = self.textEdit.toPlainText().split("\n")
        # self.progressDialog = self.factory.myProgressDialog(
        #     "Please Wait", "Resolving duplicates...", parent=self, busy=True)
        # self.progressDialog.close()
        # self.dict_args["rsl_dupl progressDialog"] = self.progressDialog
        self.dict_args["rsl_dupl progressSig"] = self.progressDialogSig
        self.dict_args["rsl_dupl threads"] = int(self.comboBox.currentText()) if self.comboBox.currentText() else 1
        MAFFTpath = self.factory.programIsValid("mafft", mode="tool")
        self.dict_args["mafft_exe"] = MAFFTpath
        ok = self.factory.remove_dir(self.dict_args["exportPath"], parent=self)
        if not ok:
            return  # 提醒是否删除旧结果，如果用户取消，就不执行
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateRsdplProcess)
        self.timer.start(1)
        self.worker = WorkThread(self.run_command, parent=self)
        self.worker.start()

    def run_command(self):
        try:
            # 清空文件夹再生成结果,放在这里执行好统一管理报错
            # self.clearFolderSig.emit(self.dict_args["exportPath"])
            time_start = datetime.datetime.now()
            self.progressSig.emit(1)
            ## 比较耗时，放到此处执行
            if self.dict_args["resolve duplicates"]:
                manager = multiprocessing.Manager()
                self.queue = manager.Queue()
                self.dict_args["rsdpl_queue"] = self.queue
                self.resolved_gene_num = 0
            self.startButtonStatusSig.emit(
                [self.pushButton_2, self.progressBar, "start", self.dict_args["exportPath"], self.qss_file, self])
            # if (self.dict_args["seq type"] == "Mitogenome") and (not self.dict_args["extract_entire_seq"]):
            #     # 如果是整个序列提取，也不能用这个
            #     extract = GBextract_MT(**self.dict_args)
            #     extract._exec()
            # else:
            extract = GBextract(**self.dict_args)
            extract._exec()
            if extract.Error_ID:
                stopStatus = "".join(extract.Error_ID)
            elif extract.source_feature_IDs:
                stopStatus = "extract_no_feature%s"%", ".join(extract.source_feature_IDs)
            else:
                stopStatus = "stop"
            # self.progressDialog.close()
            self.startButtonStatusSig.emit(
                [self.pushButton_2, self.progressBar, stopStatus, self.dict_args["exportPath"], self.qss_file, self])
            self.focusSig.emit(self.dict_args["exportPath"])
            time_end = datetime.datetime.now()
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                  str(time_end - time_start))
            with open(self.dict_args["exportPath"] + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write("If you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, "
                        "and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular "
                        "sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, "
                        "2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n\n" + self.time_used_des
                        + "For the summary of this extraction, please see \"overview.csv\"")
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.startButtonStatusSig.emit(
                [self.pushButton_2, self.progressBar, "except", self.dict_args["exportPath"], self.qss_file, self])

    @pyqtSlot()
    def on_pushButton_clicked(self):
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "<p style='line-height:25px; height:25px'>Extracter is still running, terminate it?</p>",
            QMessageBox.Yes,
            QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            if hasattr(self, "worker"):
                try: self.worker.stopWork()
                except: pass
            self.close()

    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        """
        Add row
        """
        currentRows = self.tableWidget_2.rowCount()
        self.tableWidget_2.setRowCount(currentRows + 1)
        for column in range(self.tableWidget_2.columnCount()):
            item = QTableWidgetItem("")
            item.setToolTip("Double click to set colors")
            self.tableWidget_2.setItem(currentRows, column, item)

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        """
        delete row
        """
        selecteditems = self.tableWidget_2.selectedItems()
        rows = sorted(set([i.row() for i in selecteditems]), reverse=True)
        for row in rows:
            self.tableWidget_2.removeRow(row)

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        delete cell
        """
        selecteditems = self.tableWidget_2.selectedItems()
        if selecteditems:
            for i in selecteditems:
                i.setText("")
                i.setBackground(QColor('transparent'))

    @pyqtSlot()
    def on_toolButton_3_clicked(self):
        """
        GenBank file extract settings
        """
        self.extract_setting = ExtractSettings(self)
        self.extract_setting.closeSig.connect(self.displaySettings)
        # 添加最大化按钮
        self.extract_setting.setWindowFlags(self.extract_setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.extract_setting.exec_()

    @pyqtSlot()
    def on_pushButton_10_clicked(self):
        """
        GenBank file lineage recognization settings
        """
        self.setting = Setting(self)
        self.setting.display_table(self.setting.listWidget.item(0))
        self.setting.closeSig.connect(self.updateLineageCombo)
        self.setting.closeSig.connect(self.updateLineageTable)
        self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.setting.exec_()

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
        color = self.colorPicker(self.fetch_used_colors())
        item = QTableWidgetItem(color)
        item.setBackground(QColor(color))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 1, item)
        # col3
        item = QTableWidgetItem("28")
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 2, item)
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
        self.tableWidget.setCellWidget(rowPosition, 3, comb_box)
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

    def handleItemClicked(self, item):
        if item.column() == 1:
            color = QColorDialog.getColor(QColor(item.text()), self)
            if color.isValid():
                item.setText(color.name())
                item.setBackground(color)
            self.tableWidget.clearSelection()

    def handleItemClicked_2(self, item):
        color = QColorDialog.getColor(QColor(item.text()), self)
        if color.isValid():
            item.setText(color.name())
            item.setBackground(color)
        self.tableWidget_2.clearSelection()

    def guiSave(self):
        # Save geometry
        self.extractGB_settings.setValue('size', self.size())
        # self.extractGB_settings.setValue('pos', self.pos())
        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                if name in ["comboBox_7", "comboBox_4"]:
                    dict_state = {}
                    for i in range(obj.count()):
                        text = obj.itemText(i)
                        state = 2 if obj.model().item(i).checkState() == Qt.Checked else 0
                        dict_state[text] = state
                    self.extractGB_settings.setValue(name, dict_state)
                elif name == "comboBox":
                    index = obj.currentIndex()
                    self.extractGB_settings.setValue(name, index)
                elif name != "comboBox_5":
                    text = obj.currentText()
                    if text:
                        allItems = [
                            obj.itemText(i) for i in range(obj.count())]
                        allItems.remove(text)
                        sortItems = [text] + allItems
                        self.extractGB_settings.setValue(name, sortItems)
            if isinstance(obj, QGroupBox):
                state = obj.isChecked()
                self.extractGB_settings.setValue(name, state)
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.extractGB_settings.setValue(name, state)
            if isinstance(obj, QRadioButton):
                state = obj.isChecked()
                self.extractGB_settings.setValue(name, state)
            if isinstance(obj, QTableWidget):
                if name == "tableWidget":
                    array = []  # 每一行存：[gene_name, checked], color, length, index_text
                    for row in range(obj.rowCount()):
                        gene_name = obj.item(row, 0).text()
                        checked = "true" if obj.item(
                            row, 0).checkState() == Qt.Checked else "false"
                        colour = obj.item(row, 1).text()
                        length = obj.item(row, 2).text()
                        shape_combo = obj.cellWidget(row, 3)
                        shape = shape_combo.currentText()
                        array.append([[gene_name, checked], colour, length, shape])
                    self.extractGB_settings.setValue(name, array)
                elif name == "tableWidget_2":
                    dict_color_array = self.getLineageColor()
                    self.extractGB_settings.setValue(name, dict_color_array)
            if isinstance(obj, QTabWidget):
                index = obj.currentIndex()
                self.extractGB_settings.setValue(name, index)
            if isinstance(obj, QDoubleSpinBox):
                value = obj.value()
                self.extractGB_settings.setValue(name, value)
            if isinstance(obj, QLineEdit):
                text = obj.text()
                self.extractGB_settings.setValue(name, text)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.factory.judgeWindowSize(self.extractGB_settings, 756, 661))
        self.factory.centerWindow(self)
        # self.move(self.extractGB_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox_5":
                    # 展示输入
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(self.list_names):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    self.changeLable()
                elif name == "comboBox":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.extractGB_settings.value(name, "0")
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
                # elif name == "comboBox_6":
                #     self.displaySettings()
                elif name == "comboBox_7":
                    self.updateLineageCombo()
                elif name == "comboBox_4":
                    key = re.sub(r"/|\\", "_", self.workPath) + "_availableInfo"
                    value = self.data_settings.value(
                        key, None)
                    if value:
                        source_keys = value[3][1]
                    else:
                        source_keys = None
                    items = ["Organism", "ID", "Name", "Length", "Description", "Date"] + source_keys \
                        if source_keys else ["Organism", "ID", "Name", "Length"]
                    ini_state = {}.fromkeys(items, 0)  # 2代表选中
                    ini_state["Organism"] = 2
                    ini_state["Name"] = 2
                    dict_name_state = self.extractGB_settings.value("comboBox_4", ini_state)
                    if type(dict_name_state) != dict:
                        dict_name_state = ini_state
                    self.comboBox_4.sep = "_"
                    model = self.comboBox_4.model()
                    self.comboBox_4.clear()
                    for num, text in enumerate(items):
                        item = QStandardItem(str(text))
                        state = dict_name_state[text] if text in dict_name_state else ini_state[text]  # 测试一下
                        item.setCheckState(int(state))
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    self.comboBox_4.setTopText()
                    self.comboBox_4.view().pressed.connect(self.judgeName)
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    values = self.extractGB_settings.value(name, allItems)
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
            if isinstance(obj, QGroupBox):
                # 如果没有name，就设置为True
                state = self.extractGB_settings.value(name, "true")
                obj.setChecked(self.factory.str2bool(state))
            if isinstance(obj, QCheckBox):
                if name == "checkBox":
                    CodonWpath = self.factory.programIsValid("CodonW", mode="tool")
                    if not CodonWpath:
                        obj.setChecked(False)
                        continue
                value = self.extractGB_settings.value(
                    name, obj.isChecked())  # get stored value from registry
                # if value != "no setting":
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QRadioButton):
                value = self.extractGB_settings.value(
                    name, "first")  # get stored value from registry
                if value != "first":
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
            if isinstance(obj, QTableWidget):
                if name == "tableWidget":
                    # 每一行存：[gene_name, checked], color, length, index_text
                    ini_array = [
                        [
                            ["ATP6|ATP8", 'true'], '#ffff33', '25', 'rectangle'], [
                            ["NAD1-6|NAD4L", 'true'], '#99ffff', '25', 'rectangle'], [
                            ["CYTB", 'true'], '#ff9999', '30', 'rectangle'], [
                            ["COX1-3", 'true'], '#6699ff', '25', 'rectangle'], [
                            ["rRNAs", 'true'], '#DAA520', '18', 'rectangle'], [
                            ["tRNAs", 'true'], '#ccff00', '15', 'rectangle'], [
                            ["NCR", 'false'], '#bfbfbf', '15', 'ellipse']]
                    array = self.extractGB_settings.value(name, ini_array)
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
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                        obj.setItem(row, 2, item)
                        # col 4
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
                        shape = list_row[3]
                        shape_combo_index = comb_box.findText(shape)
                        if shape_combo_index == -1:  # add to list if not found
                            comb_box.insertItems(0, [value])
                            index = comb_box.findText(value)
                            comb_box.setCurrentIndex(index)
                        else:
                            # preselect a combobox value by index
                            comb_box.setCurrentIndex(shape_combo_index)
                        obj.setCellWidget(row, 3, comb_box)
                    obj.itemClicked.connect(self.handleItemClicked)
                    obj.resizeColumnsToContents()
                    obj.verticalHeader().setVisible(False)
                elif name == "tableWidget_2":
                    self.updateLineageTable()
            if isinstance(obj, QTabWidget):
                index = self.extractGB_settings.value(name, 0)
                obj.setCurrentIndex(int(index))
            if isinstance(obj, QDoubleSpinBox):
                value = self.extractGB_settings.value(name, 1.0)
                obj.setValue(float(value))
            if isinstance(obj, QLineEdit):
                text = self.extractGB_settings.value(name, "first")
                if text != "first":
                    obj.setText(text)

    def popupException(self, exception):
        print(exception)
        rgx = re.compile(r'Permission.+?[\'\"](.+\.csv)[\'\"]')
        if rgx.search(exception):
            csvfile = rgx.search(exception).group(1)
            reply = QMessageBox.critical(
                self,
                "Extract sequence",
                "<p style='line-height:25px; height:25px'>Please close '%s' file first!</p>"%os.path.basename(csvfile),
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes and platform.system().lower() == "windows":
                os.startfile(csvfile)
        elif "Permission" in exception:
            reply = QMessageBox.critical(
                self,
                "Extract sequence",
                "<p style='line-height:25px; height:25px'>Error happened, please close the window and try again!</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.close()
        else:
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

    def runProgress(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def eventFilter(self, obj, event):
        name = obj.objectName()
        if isinstance(obj, QTableWidget):
            if event.type() == QEvent.KeyPress:  # 首先得判断type
                modifiers = QApplication.keyboardModifiers()
                if name == "tableWidget_2":
                    if event.key() == Qt.Key_Delete:
                        self.on_pushButton_9_clicked()
                        return True
                    if (modifiers == Qt.ControlModifier) and (
                                event.key() == Qt.Key_C):
                        self.copyColor()
                        return True
                    if (modifiers == Qt.ControlModifier) and (
                                event.key() == Qt.Key_X):
                        self.cutColor()
                        return True
                    if (modifiers == Qt.ControlModifier) and (
                                event.key() == Qt.Key_V):
                        self.pasteColor()
                        return True
        if (event.type() == QEvent.Show) and (obj == self.pushButton_2.toolButton.menu()):
            if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+",
                         self.dir_action.text()) or self.dir_action.text() == "Output Dir: ":
                self.factory.sync_dir(self.dir_action)  ##同步文件夹名字
            menu_x_pos = self.pushButton_2.toolButton.menu().pos().x()
            menu_width = self.pushButton_2.toolButton.menu().size().width()
            button_width = self.pushButton_2.toolButton.size().width()
            pos = QPoint(menu_x_pos - menu_width + button_width,
                         self.pushButton_2.toolButton.menu().pos().y())
            self.pushButton_2.toolButton.menu().move(pos)
            return True
        return super(ExtractGB, self).eventFilter(obj, event)

    def changeLable(self):
        count = str(self.comboBox_5.count())
        self.label_4.setText("Inputs (" + count + "):")

    def getLineageColor(self):
        dict_color_array = OrderedDict()
        columnNum = self.tableWidget_2.columnCount()
        rowNum = self.tableWidget_2.rowCount()
        for column in range(columnNum):
            headerText = self.tableWidget_2.horizontalHeaderItem(column).text()
            list_columnText = []
            for row in range(rowNum):
                if self.tableWidget_2.item(row, column):
                    list_columnText.append(
                        self.tableWidget_2.item(row, column).text())
            dict_color_array[headerText] = list_columnText
        return dict_color_array

    def copyColor(self):
        selecteditems = self.tableWidget_2.selectedItems()
        if selecteditems:
            list_selItem_text = [i.text() for i in selecteditems]
            QApplication.clipboard().setText("\t".join(list_selItem_text))

    def cutColor(self):
        selecteditems = self.tableWidget_2.selectedItems()
        list_selItem_text = []
        if selecteditems:
            for i in selecteditems:
                list_selItem_text.append(i.text())
                i.setText("")
                i.setBackground(QColor('transparent'))
            QApplication.clipboard().setText("\t".join(list_selItem_text))

    def pasteColor(self):
        colors = QApplication.clipboard().text()
        list_colors = re.split(r"\s+|,", colors)
        while "" in list_colors:
            list_colors.remove("")
        selecteditems = self.tableWidget_2.selectedItems()
        for num, i in enumerate(selecteditems):
            if (num+1) <= len(list_colors):
                color = list_colors[num]
                qcolor = QColor(color)
                if not qcolor.isValid():
                    continue
                i.setText(color)
                i.setBackground(qcolor)

    def displaySettings(self):
        ###提取的设置
        self.GenBankExtract_settings = QSettings(
            self.thisPath + '/settings/GenBankExtract_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.GenBankExtract_settings.setFallbacksEnabled(False)
        self.dict_gbExtract_set = self.GenBankExtract_settings.value("set_version")
        # self.extract_list_gene = self.factory.str2bool(self.GenBankExtract_settings.value("extract listed gene",
        #                                                                                   "false"))
        # self.extract_all_features = self.factory.str2bool(self.GenBankExtract_settings.value("extract all features",
        #
                                                                                     # "false"))
        if self.dict_gbExtract_set:
            self.allVersions = list(self.dict_gbExtract_set.keys())
            model = self.comboBox_6.model()
            self.comboBox_6.clear()
            for num, i in enumerate(self.allVersions + [">>>More<<<"]):
                item = QStandardItem(i)
                # 背景颜色
                if num % 2 == 0:
                    item.setBackground(QColor(255, 255, 255))
                else:
                    item.setBackground(QColor(237, 243, 254))
                model.appendRow(item)
        self.switchSeqType(self.comboBox_6.currentText())

    def switchSeqType(self, text):
        ###保存version顺序
        if text == ">>>More<<<":
            country = self.factory.path_settings.value("country", "UK")
            url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/PhyloSuite-demo/customize_extraction/" if \
                country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/PhyloSuite-demo/customize_extraction/"
            QDesktopServices.openUrl(QUrl(url))
            self.comboBox_6.setCurrentIndex(0)
            return
        if text != self.allVersions[0]:
            if text in self.allVersions:
                list_now_versions = copy.deepcopy(self.allVersions)
                list_now_versions.remove(text)
                reorder_list = [text] + list_now_versions
                self.dict_gbExtract_set = OrderedDict((i, self.dict_gbExtract_set[i]) for i in reorder_list)
                self.GenBankExtract_settings.setValue('set_version', self.dict_gbExtract_set)
        ###控制itol
        # if text != "Mitogenome":
        #     targetIndex = "null"
        #     for index in range(self.tabWidget.count()):
        #         if self.tabWidget.tabText(index) == "Gene order display":
        #             targetIndex = index
        #     if targetIndex != "null":
        #         self.hiddenIndex = targetIndex
        #         self.hiddenWidget = self.tabWidget.widget(self.hiddenIndex)
        #         self.hiddenTabText = self.tabWidget.tabText(self.hiddenIndex)
        #         self.tabWidget.removeTab(self.hiddenIndex)
        #         self.hiddenFlag = True
        # else:
        #     if hasattr(self, "hiddenFlag") and self.hiddenFlag:
        #         self.tabWidget.insertTab(self.hiddenIndex, self.hiddenWidget, self.hiddenTabText)
        #         self.hiddenFlag = False
        self.tabWidget.setCurrentIndex(0)

    def updateLineageTable(self):
        # tableWidget_2
        self.tableWidget_2.itemDoubleClicked.connect(self.handleItemClicked_2)
        header, array = self.factory.getCurrentTaxSetData()
        countColumn = len(header)
        self.tableWidget_2.setColumnCount(countColumn)
        ini_dict_array = OrderedDict()
        for i in header:
            ini_dict_array[i] = [""] * 6
        familyColor = [
            "#81C7D6", "#FF0033", "#6A00D1", "#49BF4E", "#AA538B", "#FF99CC"]
        if "Family" in ini_dict_array: ini_dict_array["Family"] = familyColor
        # ini_dict_array[
        #     "Family"] = familyColor if "Family" in ini_dict_array else ini_dict_array["Family"]
        self.tableWidget_2.setHorizontalHeaderLabels(
            header)
        dict_array = self.extractGB_settings.value(
            "tableWidget_2", ini_dict_array)
        maxRow = len(max(list(dict_array.values()), key=len))
        self.tableWidget_2.setRowCount(maxRow)
        if len(ini_dict_array) > len(dict_array):
            # 如果用户添加了lineage
            list_differ = list(
                set(ini_dict_array.keys()).difference(set(dict_array.keys())))
            for i in list_differ:
                # 加上这个lineage
                dict_array[i] = [""] * maxRow
        for column, columnText in enumerate(header):
            for row, rowText in enumerate(dict_array[columnText]):
                item = QTableWidgetItem(rowText)
                item.setToolTip("Double click to set colors")
                color = QColor(rowText)
                if color.isValid():
                    item.setBackground(color)
                self.tableWidget_2.setItem(row, column, item)

    def updateLineageCombo(self):
        header, array = self.factory.getCurrentTaxSetData()
        ini_state = {}.fromkeys(header, 2)  # 2代表选中
        dict_lng_state = self.extractGB_settings.value("comboBox_7", ini_state)
        model = self.comboBox_7.model()
        self.comboBox_7.clear()
        for num, text in enumerate(header):
            item = QStandardItem(text)
            state = dict_lng_state[text] if text in dict_lng_state else ini_state[text]  # 测试一下
            item.setCheckState(int(state))
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            model.appendRow(item)
        self.comboBox_7.setTopText()

    def judgeName(self):
        if not set(["Organism", "ID", "Name"]).intersection(set(self.comboBox_4.topText.split("_"))):
            QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>At least one of the following should be retained: \"Organism\", \"ID\", \"Name\"</p>")
            self.comboBox_4.item.setCheckState(Qt.Checked)
            self.comboBox_4.setTopText()

    def judgeCodonWinstallation(self, bool_):
        if bool_:
            CodonWpath = self.factory.programIsValid("CodonW", mode="tool")
            if not CodonWpath:
                reply = QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Please install CodonW and reopen the window.</p>",
                    QMessageBox.Ok,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.close()
                    self.setting = Setting(self)
                    self.setting.display_table(self.setting.listWidget.item(1))
                    # 隐藏？按钮
                    self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                    self.setting.exec_()
                else:
                    self.checkBox.setChecked(False)

    def fetch_used_colors(self):
        list_colors = []
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row, 1):
                list_colors.append(self.tableWidget.item(row, 1).text())
        return list_colors

    def colorPicker(self, list_colors):
        # 生成不重复的随机颜色
        colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
        while colour in list_colors:
            # 不让range用自定义的颜色
            colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
        return colour

    def fetch_checked_gene_names(self):
        list_names = []
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row, 0) and \
                    self.tableWidget.item(row, 0).checkState() == Qt.Checked:
                list_names.append(self.tableWidget.item(row, 0).text())
        return list_names

    def Progress(self, num, progressCancel=False):
        # self.blockSignals(True)
        if num <= 5:
            self.progressDialog.show()
        return
        print(num)
        oldValue = self.progressDialog.value()
        done_int = int(num)
        # if not hasattr(self, "last_progress_update_time"):
        #     self.last_progress_update_time = 0
        if (done_int > oldValue): # and ((time.time()-self.last_progress_update_time)>1):
            # print(self.last_progress_update_time, time.time()-self.last_progress_update_time)
            self.progressDialog.setProperty("value", done_int) # 刷新太快会导致程序卡死
            # self.progressDialog.setLabelText(f"finish {done_int}%...")
            # self.last_progress_update_time = time.time()
            if done_int == 100:
                self.progressDialog.close()
        # self.blockSignals(False)
        QCoreApplication.processEvents()

    def judgeMAFFT(self, state):
        MAFFTpath = self.factory.programIsValid("mafft", mode="tool")
        if state and (not MAFFTpath):
            reply = QMessageBox.information(
                self,
                "Information",
                "<p style='line-height:25px; height:25px'>Please install MAFFT first!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            self.checkBox_2.setChecked(False)

    def updateRsdplProcess(self):
        if (not hasattr(self, "queue")) or self.queue.empty():
            return
        total_num = self.queue.get()
        if type(total_num) == tuple:
            total_num = total_num[0]
            self.resolved_gene_num += 1
            # print(self.resolved_gene_num, total_num)
            self.progressSig.emit(70 + self.resolved_gene_num * 25 /total_num)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = ExtractGB()
    ui.show()
    sys.exit(app.exec_())
