#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from src.CustomWidget import MyPartEditorTableModel
from src.factory import Factory, WorkThread
import os
import sys
from uifiles.Ui_partition_editor import Ui_Partition_editor


class PartitionEditor(QDialog, Ui_Partition_editor, object):
    '''
    局限性：三联密码子位置必须紧挨着，不能散布
    '''
    guiCloseSig = pyqtSignal(str)

    def __init__(self, mode="PF2", parent=None):
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        super(PartitionEditor, self).__init__(parent)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        self.resize(400, 600)
        self.setWindowFlags(
                    self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.setupUi(self)
        self.header = ["Name", "", "Start", "", "Stop"]
        self.pushButton_2.clicked.connect(self.addRow)
        self.pushButton.clicked.connect(self.deleteRow)
        self.pushButton_recog.clicked.connect(self.recogFromText)
        self.pushButton_codon.clicked.connect(self.ToCodonMode3)
        self.pushButton_codon_2.clicked.connect(self.ToCodonMode2)
        self.pushButton_nocodon.clicked.connect(self.CancelCodonMode)
        self.data_type = "NUC"
        self.mode = mode
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-10-2-Brief-tutorial-for-partition-editor" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-10-2-Brief-tutorial-for-partition-editor"
        self.label_4.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

    def readPartition(self, partition_content, mode="PF2"):
        '''

        :param partition_content: 串联生成的分区文件
        :return: tableview的矩阵
        '''
        rgx = re.compile(r"(.+) *= *(\d+) *\- *(\d+)(\\3)?;") if mode == "PF2" \
            else re.compile(r"charset (.+) *= *(\d+) *\- *(\d+)(\\3)?;")
        list_contents = partition_content.split("\n")
        arraydata = []
        for line in list_contents:
            if rgx.search(line):
                geneName, start, stop, codonSite = rgx.findall(line)[0]
                geneName_new = self.factory.refineName(geneName.strip(), remain_words="-")
                arraydata.append([geneName_new, "=", start, "-", stop + codonSite])
        return arraydata

    def readPartitionFromText(self, partition_content):
        '''
        从文本识别分区，先识别PF2格式的，如果没有再识别nex格式的
        :param partition_content: 分区文本
        :return: tableview的矩阵
        '''
        rgx1 = re.compile(r"(.+) *= *(\d+) *\- *(\d+)(\\3)?;")
        rgx2 = re.compile(r"charset (.+) *= *(\d+) *\- *(\d+)(\\3)?;")
        list_contents = partition_content.split("\n")
        arraydata = []
        for line in list_contents:
            if rgx1.search(line):
                geneName, start, stop, codonSite = rgx1.findall(line)[0]
                geneName_new = self.factory.refineName(geneName.strip(), remain_words="-")
                arraydata.append([geneName_new, "=", start, "-", stop + codonSite])
            elif rgx2.search(line):
                geneName, start, stop, codonSite = rgx2.findall(line)[0]
                geneName_new = self.factory.refineName(geneName.strip(), remain_words="-")
                arraydata.append([geneName_new, "=", start, "-", stop + codonSite])
        return arraydata

    def partition2text(self, arraydata, mode="PF2"):
        '''

        :param arraydata:
        :return: partition文本，用于界面展示
        '''
        array = self.trimArray(arraydata)
        if array:
            self.GeneIndexIsOK(array)
            if mode == "PF2": return ";\n".join(["".join(i) for i in array]) + ";"
            else: return "#nexus\nbegin sets;\n%send;\n"%(";\n".join(["charset " + "".join(i) for i in array]) + ";\n")
        else: return ""

    def addRow(self):
        """
        add row
        """
        currentModel = self.tableView_partition.model()
        # print(currentModel.CDS_rows)
        if currentModel:
            currentData = currentModel.arraydata
            currentModel.layoutAboutToBeChanged.emit()
            list_data = []
            if currentData:
                for i in currentData[-1]:
                    if i in ["=", "-", " "]:
                        list_data.append(i)
                    else:
                        list_data.append("")
            else:
                list_data = ["","=", "", "-", ""]
            currentData.append(list_data)
            currentModel.layoutChanged.emit()
            # self.partitionDataSig.emit(currentData)
            self.tableView_partition.scrollToBottom()

    def deleteRow(self):
        """
        delete row
        """
        indices = self.tableView_partition.selectedIndexes()
        if indices:
            rows = sorted(set(index.row() for index in indices), reverse=True)
            self.deleteFromRows(rows)

    def deleteFromRows(self, rows):
        currentModel = self.tableView_partition.model()
        if currentModel:
            currentData = currentModel.arraydata
            for row in rows:
                currentModel.layoutAboutToBeChanged.emit()
                currentData.pop(row)
                currentModel.layoutChanged.emit()
        self.tableView_partition.clearSelection()

    def refreshTableView(self, array, header):
        model = MyPartEditorTableModel(array, header, parent=self)
        model.dataChanged.connect(self.sortGenes)
        self.tableView_partition.setModel(model)

    def ctrlResizedColumn(self):
        for j in range(0,5):
            self.tableView_partition.horizontalHeader().setSectionResizeMode(
                j, QHeaderView.ResizeToContents)

    def recogFromText(self):
        text = self.textEdit.toPlainText()
        array = self.readPartitionFromText(text)
        if array:
            reply = QMessageBox.question(
                self,
                "Partition editor",
                "This will overwrite the partitions in the above table and cannot be undone, continue?",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                model = MyPartEditorTableModel(array, self.header, parent=self)
                model.dataChanged.connect(self.sortGenes)
                self.tableView_partition.setModel(model)
                self.ctrlResizedColumn()  # 先执行一次改变列的宽度
        else:
            QMessageBox.information(
                self,
                "Partition editor",
                "<p style='line-height:25px; height:25px'>The format of the partition text cannot be recognized! "
                "Hover mouse over the text box to see example.</p>")

    def closeEvent(self, e):
        currentModel = self.tableView_partition.model()
        text = self.partition2text(currentModel.arraydata, mode=self.mode)
        self.guiCloseSig.emit(text)

    def trimArray(self, arraydata):
        '''
        只保留有值的array
        :param arraydata:
        :return:
        '''
        array = []
        for i in arraydata:
            if i[0] and i[2] and i[4]:
                array.append(i)
        return array

    def ToCodonMode3(self):
        indices = self.tableView_partition.selectedIndexes()
        currentModel = self.tableView_partition.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in indices), reverse=True)
            # 排除/3的行
            CDS_rows = self.fetchCDSrow(currentData)
            intersect_rows = list(set(rows).intersection(set(CDS_rows)))
            if intersect_rows:
                new_array = []
                for row, line in enumerate(currentData):
                    if row in intersect_rows:
                        name, x1, start, x2, stop = line
                        new_array.append([name + "_codon1", "=", start, "-", stop + "\\3"])
                        new_array.append([name + "_codon2", "=", str(int(start)+1), "-", stop + "\\3"])
                        new_array.append([name + "_codon3", "=", str(int(start)+2), "-", stop + "\\3"])
                    else:
                        new_array.append(line)
                model = MyPartEditorTableModel(new_array, self.header, parent=self)
                model.dataChanged.connect(self.sortGenes)
                self.tableView_partition.setModel(model)
                self.ctrlResizedColumn()
            else:
                QMessageBox.information(
                    self,
                    "Partition editor",
                    "<p style='line-height:25px; height:25px'>The length of the selected genes is not a multiple of 3 or "
                    "the data are already in the codon mode (3)!</p>")

    def ToCodonMode2(self):
        indices = self.tableView_partition.selectedIndexes()
        currentModel = self.tableView_partition.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in indices), reverse=True)
            # 排除/2的行
            CDS_rows = self.fetchCDSrow(currentData, mode="2")
            intersect_rows = list(set(rows).intersection(set(CDS_rows)))
            if intersect_rows:
                new_array = []
                for row, line in enumerate(currentData):
                    if row in intersect_rows:
                        name, x1, start, x2, stop = line
                        new_array.append([name + "_codonA", "=", start, "-", stop + "\\2"])
                        new_array.append([name + "_codonB", "=", str(int(start)+1), "-", stop + "\\2"])
                    else:
                        new_array.append(line)
                model = MyPartEditorTableModel(new_array, self.header, parent=self)
                model.dataChanged.connect(self.sortGenes)
                self.tableView_partition.setModel(model)
                self.ctrlResizedColumn()
            else:
                QMessageBox.information(
                    self,
                    "Partition editor",
                    "<p style='line-height:25px; height:25px'>The length of the selected genes is not a multiple of 2 or "
                    "the data are already in the codon mode (2)!</p>")

    def CancelCodonMode(self):
        '''
        3个位点都选中的时候，才能取消，如果没有选中要说明一下
        :return:
        '''
        indices = self.tableView_partition.selectedIndexes()
        currentModel = self.tableView_partition.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in indices), reverse=True)
            dict_ = {} # {789: [1, 2, 3]} #stop位置及其所有起始位置
            for row in rows:
                if "\\3" in currentData[row][4]:
                    start = int(currentData[row][2])
                    stop = int(currentData[row][4].replace("\\3", ""))
                    dict_.setdefault(stop, ["NA", "NA", "NA"])
                    # 不管是哪一位，先把三联的起始位置找到
                    if (stop - start + 1)%3 == 0: dict_[stop][0] = row #第一位
                    elif (stop - start + 1)%3 == 2:  dict_[stop][1] = row #第二位
                    elif (stop - start + 1) % 3 == 1:  dict_[stop][2] = row  # 第三位
                elif "\\2" in currentData[row][4]:
                    start = int(currentData[row][2])
                    stop = int(currentData[row][4].replace("\\2", ""))
                    dict_.setdefault(stop, ["NA", "NA"])
                    # 不管是哪一位，先把三联的起始位置找到
                    if (stop - start + 1) % 2 == 0:
                        dict_[stop][0] = row  # 第一位
                    elif (stop - start + 1) % 2 == 1:
                        dict_[stop][1] = row  # 第二位
            #先按三联行的位置排序，然后从大开始删和修改
            list_values = sorted([i for i in dict_.values() if "NA" not in i], key=lambda x: max(x), reverse=True)
            for i in list_values:
                delete_rows = sorted(i, reverse=True)
                if delete_rows:
                    # 先修改第一个
                    currentModel.layoutAboutToBeChanged.emit()
                    currentData[delete_rows[-1]][0] = re.sub(r"_codon[\dAB]", "", currentData[delete_rows[0]][0]) # 将基因名字替换为正常的
                    currentData[delete_rows[-1]][4] = currentData[delete_rows[0]][4].replace("\\3", "").replace("\\2", "") # 将最后的索引替换为正常的
                    currentModel.layoutChanged.emit()
                    self.deleteFromRows(delete_rows[:-1]) #只删除2、3行或2行
            self.ctrlResizedColumn()

    def fetchCDSrow(self, array, mode="3"):
        CDS_rows = []
        sign = "\\3" if mode=="3" else "\\2"
        for row, line in enumerate(array):
            if ("\\3" in line[4]) or ("\\2" in line[4]): continue
            start = int(line[2])
            stop = int(line[4].replace(sign, ""))
            if (mode == "3") and ((stop - start + 1) % 3 == 0):
                if row not in CDS_rows: CDS_rows.append(row)
            elif (mode == "2") and ((stop - start + 1) % 2 == 0):
                if row not in CDS_rows: CDS_rows.append(row)
        return CDS_rows

    def showEvent(self, event):
        self.textEdit.clear()

    def sortGenes(self):
        self.tableView_partition.sortByColumn(2, Qt.AscendingOrder)

    def GeneIndexIsOK(self, array):
        # 基因多的时候只展示前2个
        list_ = [] # [[cox1, 1, 867]]
        stop_error = False
        for row in array:
            try:
                geneName, start, stop = row[0], int(row[2]), int(row[4].replace("\\3", "").replace("\\2", ""))
                if "\\3" in row[4]:
                    if ((stop - start + 1) % 3 == 0): list_.append([geneName, start, stop])
                elif "\\2" in row[4]:
                    if ((stop - start + 1) % 2 == 0): list_.append([geneName, start, stop])
                else: list_.append([geneName, start, stop])
            except:
                stop_error = True
        if stop_error:
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>Only \"\\3\" or \"\\2\" are allowed in the stop position</p>")
            return
        overlap = [] # [[cox1, cox2]]
        space = [] # [[cox1, cox2]]
        startError = ""
        last = None
        for i in list_:
            if last:
                diff = i[1] - last[2] - 1
                if diff < 0:
                    overlap.append([last[0], i[0]])
                elif diff > 0:
                    space.append([last[0], i[0]])
            else:
                # 起始位置
                if i[1] != 1:
                    # 起始必须是1开始
                    startError = "&nbsp;&nbsp;&nbsp;<span style='font-weight:600'>*</span> <span style='font-weight:600; color:#ff0000;'>%s</span> must start with 1.<br>"%i[0]
            last = i
        error = ""
        if startError: error += startError
        if overlap:
            if len(overlap) > 2:
                overlap_ = overlap[:2]
                extra_text = "And %d more overlapping region(s)...<br><br>"%(len(overlap) - 2)
            else:
                overlap_ = overlap
                extra_text = ""
            text = "".join(["&nbsp;&nbsp;&nbsp;<span style='font-weight:600'>*</span> Positions overlapped between <span style='font-weight:600; color:#ff0000;'>%s</span> and <span style='font-weight:600; color:#ff0000;'>%s</span><br>"%(j[0], j[1]) for j in overlap_])
            error += text + extra_text
        if space:
            if len(overlap) > 2:
                space_ = space[:2]
                extra_text = "And %d more unassigned region(s)...<br><br>"%(len(space) - 2)
            else:
                space_ = space
                extra_text = ""
            text = "".join([
                               "&nbsp;&nbsp;&nbsp;<span style='font-weight:600'>*</span> Unassigned positions found between <span style='font-weight:600; color:#ff0000;'>%s</span> and <span style='font-weight:600; color:#ff0000;'>%s</span><br>" % (
                               j[0], j[1]) for j in space_])
            error += text + extra_text
        error = "Gene positions setting failed:<br>" + error if error else ""
        if error:
            QMessageBox.warning(
                self,
                "Warning",
                "<p style='line-height:25px; height:25px'>%s</p>" % error)


    # def fetchCodonrow(self, array):
    #     Codonrows = []
    #     for row, line in enumerate(array):
    #         if "\\3" in line[4]: Codonrows.append(row)
    #     return Codonrows


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = PartitionEditor()
    ui.show()
    sys.exit(app.exec_())
