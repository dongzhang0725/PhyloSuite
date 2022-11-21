import copy
import math
import operator
import os.path
import random

from PyQt5 import QtOpenGL
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import re
from collections import OrderedDict
from ete3 import NCBITaxa, Tree
from src.factory import Factory, WorkThread
from ..ncbi_taxonomy.ncbiquery import NCBITaxa
from ete3.treeview.svg_colors import random_color
from ete3.treeview import qt4_circular_render as crender

USE_GL = False # Temporarily disabled

class MyTableModel(QAbstractTableModel):
    detectCombobox = pyqtSignal(QModelIndex, list)
    comboboxTextChanged = pyqtSignal(QModelIndex, str) # index, text

    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.parent = parent
        self.arraydata = datain
        self.header = headerdata
        self.dataChanged.connect(self.init_tableview)
        self.detectCombobox.connect(self.makeCombobox)
        self.dict_combobox = {}
        self.init_tableview()
        try:
            self.parent.doubleClicked.disconnect()
        except:
            pass
        self.parent.doubleClicked.connect(self.handle_itemclicked)

    # def handle_itemclicked(self, index):
    #     tableview = self.sender()
    #     model = tableview.model()
    #     text = index.data(Qt.DisplayRole)
    #     if text and (re.search("^#[0-9ABCDEFabcdef]{6}$", str(text)) or (text == "None color")):
    #         text = text if text != "None color" else "#000000"
    #         color = QColorDialog.getColor(QColor(text), self.parent)
    #         if color.isValid():
    #             model.setData(index, color.name(), Qt.BackgroundRole)

    def handle_itemclicked(self, index):
        tableview = self.sender()
        model = tableview.model()
        left_index = model.index(index.row(), 0)
        text = index.data(Qt.DisplayRole)
        data = model.arraydata[index.row()][index.column()]
        left_text = left_index.data(Qt.DisplayRole)
        if text and (re.search("^#[0-9ABCDEFabcdef]{6}$", str(text)) or (text == "None color")):
            text = text if text != "None color" else "#000000"
            color = QColorDialog.getColor(QColor(text), tableview)
            if color.isValid():
                model.setData(index, color.name(), Qt.BackgroundRole)
                # tableview.selectionModel().select(model.index(0,0), QItemSelectionModel.Select)
        elif left_text and ("FONT" in left_text.upper()):
            font, ok = QFontDialog.getFont(data, tableview)
            if ok:
                model.arraydata[index.row()][index.column()] = font
                model.dataChanged.emit(index, index)

    def init_tableview(self):
        self.parent.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents),
        self.parent.horizontalHeader().setStretchLastSection(True)
        self.parent.verticalHeader().setVisible(False)

    def makeCombobox(self, index, items):
        if not self.parent.indexWidget(index):
            comb = MyComboBox()
            comb.addItems(items)
            comb.currentTextChanged.connect(lambda text:
                    [self.arraydata.__getitem__(index.row()).__setitem__(index.column(), [items[items.index(text)]] +
                                                                                         items[:items.index(text)] +
                                                                                         items[items.index(text)+1:]),
                     self.dataChanged.emit(index, index),
                     self.comboboxTextChanged.emit(index, text)])
            self.dict_combobox[f"{index.row()}, {index.column()}"] = comb
            self.parent.setIndexWidget(index, comb)

    def update_array(self, row, list_new, list_remove):
        self.layoutAboutToBeChanged.emit()
        # self.beginRemoveRows(QModelIndex(), 7, 7 + len(list_remove) - 1)
        self.arraydata = [i for i in self.arraydata if i not in list_remove]
        # self.endRemoveRows()
        dict_array = OrderedDict(self.arraydata)
        # replace
        for j in reversed(list_new):
            if j[0] in dict_array:
                row_ = list(dict_array).index(j[0])
                if j[1] != self.arraydata[row_][1]:
                    self.arraydata[row_][1] = j[1]
                    self.dataChanged.emit(self.index(row_, 1), self.index(row_, 1))
        # add new
        # position = list(dict_array.keys()).index()
        # self.beginInsertRows(QModelIndex(), 7, 7 + len(list_new) - 1)
        for j in reversed(list_new):
            if j[0] not in dict_array:
                self.arraydata.insert(row, j)
        # self.endInsertRows()
        self.layoutChanged.emit()

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.arraydata[index.row()][index.column()]
        if role in [Qt.EditRole, Qt.DisplayRole] and (type(value) != bool):
            if type(value) == list:
                self.detectCombobox.emit(index, value)
                return value
            elif type(value) == QFont:
                family_ = value.family()
                size_ = str(value.pointSize())
                italic = "italic, " if value.italic() else ""
                bold = "bold, " if value.bold() else ""
                return f"{family_}, {italic}{bold}{size_}"
            else:
                return value
        elif role == Qt.BackgroundRole and \
                ((type(value)==str and re.search("^#[0-9ABCDEFabcdef]{6}$", str(value))) \
                or (value == "None color")):
            if value == "None color":
                return None
            else:
                return QColor(value)
        elif role == Qt.CheckStateRole and (type(value) == bool):
            return Qt.Checked if value else Qt.Unchecked
        elif role == Qt.ToolTipRole:
            return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

    def headerData(self, number, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[number]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(number + 1)
        return None

    def setData(self, index, value, role, silent=False):
        if not index.isValid():
            return False
        if role in [Qt.EditRole, Qt.BackgroundRole, Qt.DisplayRole]:
            if self.arraydata[index.row()][index.column()] != value:
                self.arraydata[index.row()][index.column()] = value
                if not silent:
                    self.dataChanged.emit(index, index)
        elif role == Qt.CheckStateRole:
            if value == Qt.Checked:
                self.arraydata[index.row()][index.column()] = True
                if not silent:
                    self.dataChanged.emit(index, index)
            else:
                self.arraydata[index.row()][index.column()] = False
                if not silent:
                    self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        value = self.arraydata[index.row()][index.column()]
        if index.column() == 0:
            return Qt.ItemIsEnabled
        elif type(value) == bool:
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        elif (type(value)==str and re.search("^#[0-9ABCDEFabcdef]{6}$", str(value))) \
                or ("FONT" in self.arraydata[index.row()][0].upper()) \
                or (value == "None color"):
            return Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        return super(MyTableModel, self).flags(index)

class MyImgTableModel(QAbstractTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.parent = parent
        self.arraydata = datain
        self.header = headerdata
        self.dataChanged.connect(self.init_tableview)
        self.layoutChanged.connect(self.init_tableview)
        self.init_tableview()
        self.parent.doubleClicked.connect(self.handle_itemclicked)

    def handle_itemclicked(self, index):
        tableview = self.sender()
        model = tableview.model()
        text = index.data(Qt.DisplayRole)
        if text and (re.search("^#[0-9ABCDEFabcdef]{6}$", str(text)) or (text == "None color")):
            text = text if text != "None color" else "#000000"
            color = QColorDialog.getColor(QColor(text), self.parent)
            if color.isValid():
                model.setData(index, color.name(), Qt.BackgroundRole)

    def init_tableview(self):
        self.parent.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents),
        # self.parent.horizontalHeader().setStretchLastSection(True)
        self.parent.verticalHeader().setVisible(False)

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0]) if self.arraydata else 0

    def data(self, index, role):
        if not index.isValid():
            return None
        try:
            value = self.arraydata[index.row()][index.column()]
        except:
            print(index.column(), index.row(), self.arraydata)
        if role in [Qt.EditRole, Qt.DisplayRole]:
            if type(value) == QFont:
                family_ = value.family()
                size_ = str(value.pointSize())
                italic = "italic, " if value.italic() else ""
                bold = "bold, " if value.bold() else ""
                return f"{family_}, {italic}{bold}{size_}"
            else:
                return value
        elif role == Qt.BackgroundRole and \
                ((type(value)==str and re.search("^#[0-9ABCDEFabcdef]{6}$", str(value))) \
                 or (value == "None color")):
            if value == "None color":
                return None
            else:
                return QColor(value)
        elif role == Qt.ToolTipRole:
            return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

    def headerData(self, number, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[number]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(number + 1)
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role in [Qt.EditRole, Qt.BackgroundRole, Qt.DisplayRole]:
            if self.arraydata[index.row()][index.column()] != value:
                self.arraydata[index.row()][index.column()] = value
                self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


class MyPieTableModel(MyImgTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyImgTableModel.__init__(self, datain, headerdata, parent)
        self.parent.horizontalHeader().sectionDoubleClicked.connect(self.changeHorizontalHeader)

    def changeHorizontalHeader(self, index):
        oldHeader = self.headerData(index, Qt.Horizontal, role=Qt.DisplayRole)
        newHeader, ok = QInputDialog.getText(self.parent,
                                               'Change header label for column %d' % index,
                                               'Header:',
                                               QLineEdit.Normal,
                                               oldHeader)
        if ok:
            self.header[index] = newHeader
            self.setHeaderData(index, Qt.Horizontal, newHeader, role=Qt.EditRole)

class MystackedBarTableModel(MyPieTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyPieTableModel.__init__(self, datain, headerdata, parent)

class MyHeatmapTableModel(MyPieTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyPieTableModel.__init__(self, datain, headerdata, parent)

class MySeqTableModel(MyImgTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyImgTableModel.__init__(self, datain, headerdata, parent)

class MyBarTableModel(MyPieTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyPieTableModel.__init__(self, datain, headerdata, parent)

class MyHorizBarTableModel(MyImgTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyImgTableModel.__init__(self, datain, headerdata, parent)

class MyMotifTableModel(MyImgTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyImgTableModel.__init__(self, datain, headerdata, parent)

class MyStripTableModel(MyImgTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyImgTableModel.__init__(self, datain, headerdata, parent)
    #     self.parent.doubleClicked.connect(self.handle_itemclicked)
    #
    # def handle_itemclicked(self, index):
    #     tableview = self.sender()
    #     model = tableview.model()
    #     text = index.data(Qt.DisplayRole)
    #     if text and (re.search("^#[0-9ABCDEFabcdef]{6}$", str(text)) or (text == "None color")):
    #         text = text if text != "None color" else "#000000"
    #         color = QColorDialog.getColor(QColor(text), self.parent)
    #         if color.isValid():
    #             model.setData(index, color.name(), Qt.BackgroundRole)

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.arraydata[index.row()][index.column()]
        header = self.header[index.column()]
        if role in [Qt.EditRole, Qt.DisplayRole]:
            if type(value) == QFont:
                family_ = value.family()
                size_ = str(value.pointSize())
                italic = "italic, " if value.italic() else ""
                bold = "bold, " if value.bold() else ""
                return f"{family_}, {italic}{bold}{size_}"
            else:
                return value
        elif role == Qt.BackgroundRole and \
                ((type(value)==str and re.search("^#[0-9ABCDEFabcdef]{6}$", str(value))) \
                 or (value == "None color")):
            if value == "None color":
                return None
            else:
                return QColor(value)
        elif role == Qt.ToolTipRole:
            return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

class MyTextTableModel(MyStripTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyStripTableModel.__init__(self, datain, headerdata, parent)

    def flags(self, index):
        if index.column() in [0, 2]:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

class MyShapeTableModel(MyStripTableModel):
    detectCombobox = pyqtSignal(QModelIndex, list)
    comboboxTextChanged = pyqtSignal(QModelIndex, str) # index, text
    def __init__(self, datain, headerdata, parent=None, check_states=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyStripTableModel.__init__(self, datain, headerdata, parent)
        dict_cols = {2: False, 3: False}
        header = CheckBoxHeader(parent=self.parent, checked_cols=dict_cols)
        header.setMinimumSectionSize(150)
        header.clicked.connect(self.headerClick)
        self.parent.setHorizontalHeader(header)
        self.check_states = check_states
        self.dataChanged.connect(self.init_tableview)
        self.detectCombobox.connect(self.makeCombobox)
        self.dict_combobox = {}
        self.init_tableview()

    def headerClick(self, isOn, index):
        self.beginResetModel()
        if isOn:
            for row in range(len(self.check_states)):
                self.check_states[row][index] = True
        else:
            for row in range(len(self.check_states)):
                self.check_states[row][index] = False
        self.endResetModel()
        # self.init_tableview()
        # self.dataChanged.emit(self.index(0, index), self.index(0, index))

    def handle_itemclicked(self, index):
        tableview = self.sender()
        model = tableview.model()
        text = str(index.data(Qt.DisplayRole))
        if text and (re.search("^#[0-9ABCDEFabcdef]{6}$", str(text)) or (text == "None color")):
            text = text if text != "None color" else "#000000"
            color = QColorDialog.getColor(QColor(text), self.parent)
            if color.isValid():
                model.setData(index, color.name(), Qt.BackgroundRole)

    def makeCombobox(self, index, items):
        dict_icon = {"circle": ":/shape/resourses/shape/circle.svg",
                     "rectangle": ":/shape/resourses/shape/rectangle.svg",
                     "star2": ":/shape/resourses/shape/star2.svg",
                     "star": ":/shape/resourses/shape/star.svg",
                     "round corner rectangle": ":/shape/resourses/shape/round_rect.svg",
                     "diamond": ":/shape/resourses/shape/diamond.svg",
                     "line": ":/shape/resourses/shape/line.svg",
                     "left arrow": ":/shape/resourses/shape/left_arrow.svg",
                     "right arrow": ":/shape/resourses/shape/right_arrow.svg",
                     "left triangle": ":/shape/resourses/shape/left_tri.svg",
                     "right triangle": ":/shape/resourses/shape/right_tri.svg",
                     "top trangle": ":/shape/resourses/shape/top_tri.svg",
                     "bottom triangle": ":/shape/resourses/shape/bottom_tri.svg"}
        if not self.parent.indexWidget(index):
            comb = MyComboBox()
            model = QStandardItemModel()
            for i in items:
                item = QStandardItem(i)
                icon = dict_icon[i] if i in dict_icon else None
                item.setIcon(QIcon(icon))
                font = item.font()
                font.setPointSize(13)
                item.setFont(font)
                model.appendRow(item)
            comb.setModel(model)
            # comb.addItems(items)
            comb.currentTextChanged.connect(lambda text:
                                            [self.arraydata.__getitem__(index.row()).__setitem__(index.column(), [items[items.index(text)]] +
                                                                                                 items[:items.index(text)] +
                                                                                                 items[items.index(text)+1:]),
                                             self.dataChanged.emit(index, index),
                                             self.comboboxTextChanged.emit(index, text)])
            self.dict_combobox[f"{index.row()}, {index.column()}"] = comb
            self.parent.setIndexWidget(index, comb)

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.arraydata[index.row()][index.column()]
        check_value = self.check_states[index.row()][index.column()]
        if role in [Qt.EditRole, Qt.DisplayRole] and (type(value) != bool):
            if type(value) == list:
                self.detectCombobox.emit(index, value)
                return value
            elif type(value) == QFont:
                family_ = value.family()
                size_ = str(value.pointSize())
                italic = "italic, " if value.italic() else ""
                bold = "bold, " if value.bold() else ""
                return f"{family_}, {italic}{bold}{size_}"
            else:
                return value
        elif role == Qt.BackgroundRole and \
                ((type(value)==str and re.search("^#[0-9ABCDEFabcdef]{6}$", str(value))) \
                 or (type(value)==str and (value == "None color"))):
            if value == "None color":
                return None
            else:
                return QColor(value)
        elif role == Qt.CheckStateRole and (type(check_value) == bool) and (check_value in [True, False]):
            return Qt.Checked if check_value==True else Qt.Unchecked
        elif role == Qt.ToolTipRole:
            return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

    def setData(self, index, value, role, silent=False):
        if not index.isValid():
            return False
        if role in [Qt.EditRole, Qt.BackgroundRole, Qt.DisplayRole]:
            if self.arraydata[index.row()][index.column()] != value:
                self.arraydata[index.row()][index.column()] = value
                self.dataChanged.emit(index, index)
        elif role == Qt.CheckStateRole:
            if value == Qt.Checked:
                self.check_states[index.row()][index.column()] = True
                self.dataChanged.emit(index, index)
            else:
                self.check_states[index.row()][index.column()] = False
                self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        if index.column() in [4]:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        elif index.column() in [2, 3]:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

class MyNameTableModel(MyImgTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyImgTableModel.__init__(self, datain, headerdata, parent)

    def flags(self, index):
        if index.column() in [0, 2, 3]:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

class MyTaxTableModel(MyImgTableModel):
    def __init__(self, datain, headerdata, parent=None, dialog=None, header_state=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyImgTableModel.__init__(self, datain, headerdata, parent)
        self.dialog = dialog
        self.dataChanged.connect(lambda : [self.init_tableview(),
                                           self.set_example_text()])
        self.dialog.ui.lineEdit.textChanged.connect(self.showGenusName)
        self.dialog.ui.spinBox.valueChanged.connect(self.changeGenusName)
        self.dialog.ui.pushButton_6.clicked.connect(self.get_taxonomy)
        self.factory = Factory()
        self.set_example_text()
        self.dict_tax_color = {}
        self.parent.setContextMenuPolicy(Qt.CustomContextMenu)
        self.parent.customContextMenuRequested.connect(self.popup)
        # header
        dict_cols = {i:False for i in range(1, len(self.header))} if not header_state else header_state
        self.hheader = CheckBoxHeader(parent=self.parent, checked_cols=dict_cols) # list(range(1,len(self.header))))
        self.hheader.setMinimumSectionSize(150)
        self.parent.setHorizontalHeader(self.hheader)
        self.headerDataChanged.connect(lambda oritation, index1, index2: self.hheader.isOn.update({index1: False}))
        self.parent.horizontalHeader().sectionDoubleClicked.connect(self.changeHorizontalHeader)
        self.init_tableview()

    def changeHorizontalHeader(self, index):
        oldHeader = self.headerData(index, Qt.Horizontal, role=Qt.DisplayRole)
        newHeader, ok = QInputDialog.getText(self.parent,
            'Change header label for column %d' % index,
            'Header:',
            QLineEdit.Normal,
            oldHeader)
        if ok:
            self.header[index] = newHeader
            self.setHeaderData(index, Qt.Horizontal, newHeader, role=Qt.EditRole)

    def fetchIncludedTax(self):
        return [self.header[0]] + [i for num,i in enumerate(self.header[1:]) if self.hheader.isOn[num+1]]

    def fetchIncludedArray(self):
        checked_nums = [0] + [num+1 for num,i in enumerate(self.header[1:]) if self.hheader.isOn[num+1]]
        return [list(map(j.__getitem__, checked_nums)) for j in self.arraydata]

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
        current_text = self.dialog.ui.lineEdit.text()
        data_text = self.arraydata[0][0]
        if data_text != current_text:
            self.dialog.ui.lineEdit.setText(" ".join(re.split(r"[\W|_]", data_text)))

    def changeGenusName(self, value):
        list_names = re.split(r"[\W|_]", self.dialog.ui.lineEdit.text())
        index = len(list_names)-1 if value > len(list_names) else value-1
        genusName = list_names[index]
        self.dialog.ui.lineEdit_2.setText(genusName)

    def showGenusName(self, text):
        index = self.dialog.ui.spinBox.value()
        genusName = re.split(r"[\W|_]", text)[index-1]
        self.dialog.ui.lineEdit_2.setText(genusName)

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

    def get_taxonomy_slot(self):
        LineageNames = [i.upper() for i in self.header[1:]]
        ncbi = NCBITaxa()
        for row in range(len(self.arraydata)):
            index = self.dialog.ui.spinBox.value()
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

    def get_colors(self):
        dict_ = {}
        for row, list_row in enumerate(self.arraydata):
            for col, i in enumerate(list_row):
                if col != 0:
                    if self.hheader.isOn[col]:
                        if i:
                            dict_[i] = self.index(row, col).data(Qt.BackgroundRole).name()
        return dict_

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

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.arraydata[index.row()][index.column()]
        if role in [Qt.EditRole, Qt.DisplayRole]:
            return value
        elif role == Qt.BackgroundRole and index.column() != 0:
            if value:
                return QColor(self.colourPicker(value))
        # elif role == Qt.ForegroundRole:
        #     return QColor("#d8d8d8")
        elif role == Qt.ToolTipRole:
            return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

    def sort(self, Ncol, order):
        """
        Sort table by given column number.
        """
        self.layoutAboutToBeChanged.emit()
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        self.layoutChanged.emit()

    def flags(self, index):
        if index.column() in [0]:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsUserCheckable

class MyNodePropTableModel(MyTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyTableModel.__init__(self, datain, headerdata, parent)

class MyGeneralTableModel(MyTableModel):
    def __init__(self, datain, headerdata, parent=None, tooltip_map=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyTableModel.__init__(self, datain, headerdata, parent)
        self.tooltip_map = tooltip_map

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.arraydata[index.row()][index.column()]
        if role in [Qt.EditRole, Qt.DisplayRole] and (type(value) != bool):
            if type(value) == list:
                self.detectCombobox.emit(index, value)
                return value
            elif type(value) == QFont:
                family_ = value.family()
                size_ = str(value.pointSize())
                italic = "italic, " if value.italic() else ""
                bold = "bold, " if value.bold() else ""
                return f"{family_}, {italic}{bold}{size_}"
            else:
                return value
        elif role == Qt.BackgroundRole and \
                ((type(value)==str and re.search("^#[0-9ABCDEFabcdef]{6}$", str(value))) \
                 or (value == "None color")):
            if value == "None color":
                return None
            else:
                return QColor(value)
        elif role == Qt.CheckStateRole and (type(value) == bool):
            return Qt.Checked if value else Qt.Unchecked
        elif role == Qt.ToolTipRole:
            if type(value) == list:
                return value[0]
            elif value in self.tooltip_map:
                return self.tooltip_map[value]
            else:
                return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

class MyCompareTableModel(MyImgTableModel):
    detectCombobox = pyqtSignal(QModelIndex, list)
    comboboxTextChanged = pyqtSignal(QModelIndex, str) # index, text
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyImgTableModel.__init__(self, datain, headerdata, parent)
        self.parent.setContextMenuPolicy(Qt.CustomContextMenu)
        self.parent.customContextMenuRequested.connect(self.popup)
        self.dict_tax_color = {}
        self.list_colors = copy.deepcopy(self.parent.parent.get_color_set())
        self.detectCombobox.connect(self.makeCombobox)

    def makeCombobox(self, index, items):
        dict_icon = {"circle": ":/shape/resourses/shape/circle.svg",
                     "rectangle": ":/shape/resourses/shape/rectangle.svg",
                     "star2": ":/shape/resourses/shape/star2.svg",
                     "star": ":/shape/resourses/shape/star.svg",
                     "round corner rectangle": ":/shape/resourses/shape/round_rect.svg",
                     "diamond": ":/shape/resourses/shape/diamond.svg",
                     "line": ":/shape/resourses/shape/line.svg",
                     "left arrow": ":/shape/resourses/shape/left_arrow.svg",
                     "right arrow": ":/shape/resourses/shape/right_arrow.svg",
                     "left triangle": ":/shape/resourses/shape/left_tri.svg",
                     "right triangle": ":/shape/resourses/shape/right_tri.svg",
                     "top trangle": ":/shape/resourses/shape/top_tri.svg",
                     "bottom triangle": ":/shape/resourses/shape/bottom_tri.svg"}
        if not self.parent.indexWidget(index):
            comb = MyComboBox()
            model = QStandardItemModel()
            for i in items:
                item = QStandardItem(i)
                icon = dict_icon[i] if i in dict_icon else None
                item.setIcon(QIcon(icon))
                font = item.font()
                font.setPointSize(13)
                item.setFont(font)
                model.appendRow(item)
            comb.setModel(model)
            # comb.addItems(items)
            comb.currentTextChanged.connect(lambda text:
            [self.arraydata.__getitem__(index.row()).__setitem__(index.column(), [items[items.index(text)]] +
                                                                                 items[:items.index(text)] +
                                                                                 items[items.index(text)+1:]),
             self.dataChanged.emit(index, index),
             self.comboboxTextChanged.emit(index, text)])
            # self.dict_combobox[f"{index.row()}, {index.column()}"] = comb
            self.parent.setIndexWidget(index, comb)

    def popup(self, qpoint):
        popMenu = QMenu(self.parent)
        bgcolor = QAction("Set background color", self,
            statusTip="Set background color",
            triggered=self.set_bgcolor)
        popMenu.addAction(bgcolor)
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

    def get_colors(self):
        dict_ = {}
        for row, list_row in enumerate(self.arraydata):
            if list_row[2] == "":
                dict_["default"] = "black"
            else:
                dict_[list_row[2]] = self.index(row, 2).data(Qt.BackgroundRole).name()
        return dict_

    def colourPicker(self, group):
        colours = list(self.dict_tax_color.values())
        if group in self.dict_tax_color:
            colour = self.dict_tax_color[group]
        else:
            if self.list_colors:
                colour = self.list_colors.pop(0)
            else:
                colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
                while colour in colours:
                    colour = '#%06X' % random.randint(0, 256 ** 3 - 1)
            self.dict_tax_color[group] = colour
        return colour

    def refresh_colors(self):
        self.dict_tax_color = {}
        self.list_colors = copy.deepcopy(self.parent.parent.get_color_set())
        self.layoutChanged.emit()

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.arraydata[index.row()][index.column()]
        if role in [Qt.EditRole, Qt.DisplayRole] and (type(value) != bool):
            if type(value) == list:
                self.detectCombobox.emit(index, value)
            return value
        elif role == Qt.BackgroundRole and index.column() == 2:
            if value:
                return QColor(self.colourPicker(value))
        elif role == Qt.ToolTipRole:
            return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

    def sort(self, Ncol, order):
        """
        Sort table by given column number.
        """
        self.layoutAboutToBeChanged.emit()
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        self.layoutChanged.emit()

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

class MyAttributeTableModel(MyImgTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        MyImgTableModel.__init__(self, datain, headerdata, parent)


class CheckableTabWidget(QTabWidget):
    stateChanged = pyqtSignal(int, int, QWidget)
    # tabRemoved = pyqtSignal(QWidget)
    checkBoxList = []

    def __init__(self, parent=None):
        self.parent = parent
        QTabWidget.__init__(self, parent)
        self.tabCloseRequested.connect(self.removeTab_)

    def addTab(self, widget, title):
        if title != "Node features":
            super(CheckableTabWidget, self).addTab(widget, title)
            widget.text = title
            index = self.indexOf(widget)
            self.checkBox = QCheckBox()
            widget.index = index
            self.checkBox.setChecked(True)
            self.checkBoxList.append(self.checkBox)
            self.tabBar().setTabButton(self.tabBar().count()-1, QTabBar.LeftSide, self.checkBox)
            self.checkBox.stateChanged.connect(lambda checkState: self.__emitStateChanged(self.checkBox, checkState, widget))
        else:
            super(CheckableTabWidget, self).addTab(widget, title)

    def isChecked(self, index):
        return self.tabBar().tabButton(index, QTabBar.LeftSide).checkState() != Qt.Unchecked

    def setCheckState(self, index, checkState):
        self.tabBar().tabButton(index, QTabBar.LeftSide).setChecked(checkState)

    def __emitStateChanged(self, checkBox, checkState, widget):
        index = self.checkBoxList.index(checkBox)
        self.stateChanged.emit(index, checkState, widget)

    def get_checked_num(self):
        return len([index for index in range(self.count()) if (index not in [0, 1]) and self.isChecked(index)])

    def removeTab_(self, index):
        if index in [0, 1]:
            return
        widget = self.widget(index)
        if widget and widget.children():
            widget.deleteLater()
            self.removeTab(index)
            removed_col = self.parent.remove_faces(widget.tableview.allfaces)
            if hasattr(widget.tableview, "titlefaces"):
                self.parent.remove_title_faces(widget.tableview.titlefaces)
            self.parent.reorder_faces(removed_col)
            self.parent.redraw()
            # self.tabRemoved.emit(widget)

class ComboboxDelegate(QItemDelegate):
    def __init__(self, parent, choices, model):
        super().__init__(parent)
        self.items = choices
        self.model = model

    def createEditor(self, parent, option, index):
        value = index.data(Qt.DisplayRole)
        if type(value) == list:
            print(value)
            left_text = self.model.index(index.row(), 0).data(Qt.DisplayRole)
            comb_items = self.items[left_text]
            self.editor = QComboBox(parent)
            self.editor.addItems(comb_items)
            return self.editor
        else:
            QItemDelegate.createEditor(self, parent, option, index)

    def paint(self, painter, option, index):
        value = index.data(Qt.DisplayRole)
        if type(value) == list:
            style = QApplication.style()
            opt = QStyleOptionComboBox()
            opt.text = str(value)
            opt.rect = option.rect
            style.drawComplexControl(QStyle.CC_ComboBox, opt, painter)
            QItemDelegate.paint(self, painter, option, index)
        else:
            QItemDelegate.paint(self, painter, option, index)

    def setEditorData(self, editor, index):
        value = index.data(Qt.DisplayRole)
        if type(value) == list:
            left_text = self.model.index(index.row(), 0).data(Qt.DisplayRole)
            comb_items = self.items[left_text]
            num = comb_items.index(value[0])
            editor.setCurrentIndex(num)
        else:
            QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        index_value = index.data(Qt.DisplayRole)
        if type(index_value) == list:
            value = editor.currentText()
            # list_ = []
            # for i in range(editor.count()):
            #     list_.append(editor.itemText(i))
            # print(list_)
            model.setData(index, Qt.DisplayRole, [value]) #QVariant(value))
        else:
            QItemDelegate.setModelData(self, editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        value = index.data(Qt.DisplayRole)
        if type(value) == list:
            editor.setGeometry(option.rect)
        else:
            QItemDelegate.setModelData(self, editor, option, index)

class MyComboBox(QComboBox):
    def __init__(self, *args):
        super().__init__(*args)

    def wheelEvent(self, e):
        e.ignore()

class MyTableView(QTableView):
    
    def __init__(self, parent=None):
        super(MyTableView, self).__init__(parent)
        self.setStyleSheet("QTableView::item:selected {background: #a6e4ff; color: black; border: 0px;}")
        # self.resize(800, 600)
        # self.setContextMenuPolicy(Qt.ActionsContextMenu)# 右键菜单
        # self.setEditTriggers(self.NoEditTriggers)# 禁止编辑
        # self.addAction(QAction("复制", self, triggered=self.copyData))
        # self.myModel = QStandardItemModel()# model
        # self.setModel(self.myModel)

    def keyPressEvent(self, event):
        super(MyTableView, self).keyPressEvent(event)
        # Ctrl + C
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_C:
            self.copyData()
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_V:
            self.pastData()

    def copyData(self):
        rows = set()
        cols = set()
        for index in self.selectedIndexes():# 得到所有选择的
            rows.add(index.row())
            cols.add(index.column())
        if (not rows) or (not cols):
            return
        minrow = min(rows)
        maxrow = max(rows)
        mincol = min(cols)
        maxcol = max(cols)
        # print(mrow, mcol)
        arrays = [
            ["" for _ in range(mincol, maxcol+1)
             ] for _ in range(minrow, maxrow+1)
        ]# 创建二维数组
        # print(arrays, minrow, maxrow, mincol, maxcol)
        # 填充数据
        for index in self.selectedIndexes():# 遍历所有选择的
            arrays[index.row()-minrow][index.column()-mincol] = index.data()
        # print(arrays)
        data = ""# 最后的结果
        for row in arrays:
            data += "\t".join(row) + "\n"
        # print(data)
        QApplication.clipboard().setText(data)# 复制到剪贴板中
        QMessageBox.information(self, "Information", "Data copied")

    def pastData(self):
        old_array = self.model().arraydata
        old_col = len(old_array[0])
        old_row = len(old_array)
        text = QApplication.clipboard().text()
        array = [row.split("\t") for row in text.split("\n")]
        if array:
            reply = QMessageBox.information(
                self,
                "Confirmation",
                "<p style='line-height:25px; height:25px'>Are you sure that you want to paste the data here? "
                                                          "The old data will be replaced!</p>",
                QMessageBox.Ok,
                QMessageBox.Cancel)
            if reply == QMessageBox.Ok:
                indices = self.selectedIndexes()
                index = indices[0]
                for row, list_row in enumerate(array):
                    for col, value in enumerate(list_row):
                        if ((index.row() + row + 1) <= old_row) and ((index.column() + col + 1 <= old_col)):
                            old_array[index.row() + row][index.column() + col] = value
                            self.model().dataChanged.emit(index, index)

class MyNodePropTableView(QTableView):

    def __init__(self, parent=None):
        super(MyNodePropTableView, self).__init__(parent)
        self.parent = parent
        self._mode = 0
        # self.doubleClicked.connect(self.handle_itemclicked)

    def get_props_in_nodes(self, nodes):
        # sorts properties and faces of selected nodes
        self.prop2nodes = {}
        self.prop2values = {}
        self.style2nodes = {}
        self.style2values = {}

        for n in nodes:
            for pname in n.features:
                pvalue = getattr(n,pname)
                if type(pvalue) == int or \
                        type(pvalue) == float or \
                        type(pvalue) == str :
                    self.prop2nodes.setdefault(pname,n)
                    self.prop2values.setdefault(pname,pvalue)

            for pname,pvalue in n.img_style.items():
                if type(pvalue) == int or \
                        type(pvalue) == float or \
                        type(pvalue) == str :
                    self.style2nodes.setdefault(pname,n)
                    self.style2values.setdefault(pname,pvalue)

    def assign_list(self, prop, list_prop_values):
        dict_map = {0: "solid", 1: "dashed", 2: "dotted",
                    "solid": "solid", "dashed": "dashed", "dotted": "dotted",
                    "circle": "circle", "square": "square", "sphere": "sphere"}
        # print(self.style2values)
        value = dict_map[self.style2values[prop]]
        self.style2values[prop] = [value] + [i for i in list_prop_values if i != value]

    def update_properties(self, node):
        self.node = node
        if self._mode == 0: # node
            self.get_props_in_nodes([node])
        elif self._mode == 1: # childs
            self.get_props_in_nodes(node.get_leaves())
        elif self._mode == 2: # partition
            self.get_props_in_nodes([node]+node.get_descendants())

        dict_name_map = {"dist": "branch length",
                         "support": "support value",
                         "bgcolor": "background color",
                         "fgcolor": "node color",
                         "hz_line_color": "Horizontal line color",
                         "hz_line_type": "Horizontal line type",
                         "hz_line_width": "Horizontal line width",
                         "vt_line_color": "vertical line color",
                         "vt_line_type": "vertical line type",
                         "vt_line_width": "vertical line width",
                         "shape": "node shape",
                         "size": "node shape size",
                         "rad": "radius"
                         }
        # print(self.prop2values) # {'support': [1.0], 'id': ['Paratetraonchoides_inermis_KY856918'], 'name': ['Paratetraonchoides_inermis_KY856918'], 'dist': [0.9001669639]}
        self.assign_list("hz_line_type", ["solid", "dashed", "dotted"])
        self.assign_list("vt_line_type", ["solid", "dashed", "dotted"])
        self.assign_list("shape", ["circle", "square", "sphere"])

        prop_array = [[i if i not in dict_name_map else dict_name_map[i], self.prop2values[i]]
                       for i in sorted(self.prop2values.keys(),
                                       key=lambda x: dict_name_map[x] if x in dict_name_map else x)] + \
                     [[j if j not in dict_name_map else dict_name_map[j], self.style2values[j]]
                      for j in sorted(self.style2values.keys(),
                                      key=lambda x: dict_name_map[x] if x in dict_name_map else x)] # + \
                     # [["apply set. for", ["clade", "node"]]]
        self.model_ = MyNodePropTableModel(prop_array, ["Feature", "Value"], self)
        self.model_.dataChanged.connect(self.apply_changes)
        self.setModel(self.model_)

    # def handle_itemclicked(self, index):
    #     text = str(index.data(Qt.DisplayRole))
    #     if text and (re.search("^#[0-9ABCDEFabcdef]{6}$", text) or (text == "None color")):
    #         text = text if text != "None color" else "#000000"
    #         color = QColorDialog.getColor(QColor(text), self)
    #         if color.isValid():
    #             self.model_.setData(index, color.name(), Qt.BackgroundRole)

    def apply_changes(self, index1=None, index2=None):
        # if self.model_.index(index1.row(), 0).data(Qt.DisplayRole) == "apply set. for":
        #     return
        dict_name_map = {'branch length': 'dist',
         'support value': 'support',
         'background color': 'bgcolor',
         'node color': 'fgcolor',
         'Horizontal line color': 'hz_line_color',
         'Horizontal line type': 'hz_line_type',
         'Horizontal line width': 'hz_line_width',
         'vertical line color': 'vt_line_color',
         'vertical line type': 'vt_line_type',
         'vertical line width': 'vt_line_width',
         'node shape': 'shape',
         'node shape size': 'size',
         "radius": "rad"}
        left_props = self.model_.index(index1.row(), 0).data(Qt.DisplayRole)
        left_props = left_props if left_props not in dict_name_map else dict_name_map[left_props]
        right_value = index1.data(Qt.DisplayRole)
        # array = self.model_.arraydata
        dict_map = {"solid": 0, "dashed": 1, "dotted": 2,
                    "circle": "circle", "square": "square", "sphere": "sphere"}
        # apply_for = dict(array).pop("apply set. for")[0]
        list_mul_props = ["fgcolor", "hz_line_color", "hz_line_type", "hz_line_width",
                          "shape", "size", "vt_line_color", "vt_line_type", "vt_line_width"]
        apply_for = "clade"
        if left_props in list_mul_props:
            windInfo = Inputbox_message_tree(":/picture/resourses/msg_info.png", parent=self)
            windInfo.clade_btn.setChecked(True)
            if windInfo.exec_() == QDialog.Accepted:
                if windInfo.node_btn.isChecked():
                    apply_for = "node"
                elif windInfo.leaf_btn.isChecked():
                    apply_for = "leaves"
        # apply
        try:
            if left_props in self.style2values:
                if (left_props in list_mul_props):
                    if apply_for == "leaves":
                        for node in self.node.get_leaves():
                            node.img_style[left_props] = right_value if type(right_value) != list else dict_map[right_value[0]]
                    else:
                        self.node.img_style[left_props] = right_value if type(right_value) != list else dict_map[right_value[0]]
                        if apply_for == "clade":
                            for node in self.node.get_descendants():
                                node.img_style[left_props] = right_value if type(right_value) != list else dict_map[right_value[0]]
                else:
                    self.node.img_style[left_props] = right_value if type(right_value) != list else dict_map[right_value[0]]
            else:
                value = right_value if type(right_value) != list else dict_map[right_value[0]]
                if (left_props in list_mul_props):
                    if apply_for == "leaves":
                        for node in self.node.get_leaves():
                            setattr(node, left_props, value)
                    else:
                        setattr(self.node, left_props, value)
                        for node in self.node.get_descendants():
                            setattr(node, left_props, value)
                else:
                    setattr(self.node, left_props, value)
        except Exception as e:
            #logger(-1, "Wrong format for attribute:", name)
            print(e)
        # self.scene.img._scale = None
        self.parent.redraw()
        # self.parent.view.set_focus(self.node.id, by="id")
        return

class Inputbox_message_tree(QDialog, object):

    def __init__(self, icon, singleBtn=False, parent=None):
        super(Inputbox_message_tree, self).__init__(parent)
        self.setWindowTitle("PhyloSuite ETE3")
        # self.setMinimumWidth(520)
        self.gridLayout = QGridLayout(self)
        self.widget_layout = QWidget(self)
        self.widget_layout.setObjectName("widget_layout")
        self.widget_layout.setStyleSheet("QWidget#widget_layout {border: 1px ridge gray; background-color: white}")
        self.verticalLayout = QVBoxLayout(self.widget_layout)
        self.label = QLabel(self.widget_layout)
        self.label.resize(52, 52)
        self.label.setText("")
        self.label.setPixmap(QPixmap(icon).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(20)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.addWidget(self.label)
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3 = QVBoxLayout()
        self.clade_btn = QRadioButton("to the whole selected clade", self.widget_layout)
        self.leaf_btn = QRadioButton("to the selected leaf node(s)", self.widget_layout)
        self.node_btn = QRadioButton("to the current selected node", self.widget_layout)
        self.label_3 = QLabel(f"<p style='line-height:25px; height:25px'>Where do you want to apply this setting:{' '*8}</p>", self.widget_layout)
        self.verticalLayout_3.addWidget(self.label_3)
        self.verticalLayout_3.addWidget(self.clade_btn)
        self.verticalLayout_3.addWidget(self.leaf_btn)
        self.verticalLayout_3.addWidget(self.node_btn)
        # self.verticalLayout_3.addWidget(self.label_2)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem = QSpacerItem(20, 29, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2 = QHBoxLayout()
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.buttonBox = QDialogButtonBox(self.widget_layout)
        self.buttonBox.setOrientation(Qt.Horizontal)
        if singleBtn:
            self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        else:
            self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.horizontalLayout_2.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.gridLayout.addWidget(self.widget_layout, 0, 0, 1, 1)
        self.adjustSize()

class MyGeneralTableView(QTableView):

    def __init__(self, parent=None):
        super(MyGeneralTableView, self).__init__(parent)
        # self.parent = parent
        self.default_parms_array = [
            ["mode", ["Rectangular", "Circular"]],
            ["orientation", ["left-to-right", "right-to-left"]], # If 0, tree is drawn from left-to-right. If 1, tree is drawn from right-to-left. This property only makes sense when “r” mode is used.
            ["rotation", 0],
            ["min_leaf_separation", 1],
            ["branch_vertical_margin", 0],
            ["arc_start", 0], # 0-359 When circular trees are drawn, this defines the starting angle (in degrees) from which leaves are distributed (clock-wise) around the total arc span (0 = 3 o’clock).
            ["arc_span", 359], # 0-359
            ["margin_left", 0],
            ["margin_right", 0],
            ["margin_top", 0],
            ["margin_bottom", 0],
            ["scale", None], # None If None, it will be automatically calculated.
            ["optimal_scale_level", ["mid", "full"]],
            ["root_opening_factor", 0.25], # 0-1
            ["complete_branch_lines_when_necessary", True],
            ["extra_branch_line_type", ["dotted", "solid", "dashed"]], #  0=solid, 1=dashed, 2=dotted
            ["extra_branch_line_color", "#808080"],
            ["force_topology", False],
            ["draw_guiding_lines", True],
            ["guiding_lines_type", ["dotted", "solid", "dashed"]],
            ["guiding_lines_color", "#808080"],
            ["allow_face_overlap", False],
            ["draw_aligned_faces_as_table", True],
            ["children_faces_on_top", True],
            ["show_border", False],
            ["show_scale", True],
            ["show_leaf_name", False],
            ["show_branch_length", False],
            ["show_branch_support", True],
            ["legend_position", ["Bottom Right", "Bottom Left", "Top Left", "Top Right"]] # TopLeft corner if 1, TopRight if 2, BottomLeft if 3, BottomRight if 4
        ]
        # 还差几个：aligned_header/aligned_foot/legend/title
        self.long2short = {"complete_branch_lines_when_necessary": "auto_adjust_branch",
                          "branch_vertical_margin": "vertical_margin",
                          "extra_branch_line_type": "extra_branch_type",
                          "extra_branch_line_color": "extra_branch_color",
                          "draw_guiding_lines": "draw_guidelines",
                          "guiding_lines_type": "guidelines_type",
                          "guiding_lines_color": "guidelines_color",
                          "draw_aligned_faces_as_table": "aligned_face_as_table",
                          "children_faces_on_top": "children_face_top",
                          "show_branch_length": "branch_length",
                          "show_branch_support": "branch_support"}
        self.short2long = {self.long2short[i]:i for i in self.long2short}
        self.dict_value_map = { # mode
                               "Rectangular": "r",
                               "Circular": "c",
                                # orientation
                               "left-to-right": 0,
                               "right-to-left": 1,
                                # line type
                               "dotted": 2,
                               "solid": 0,
                               "dashed": 1,
                                # legend_position
                               "Bottom Right": 4,
                               "Bottom Left": 3,
                               "Top Left": 1,
                               "Top Right": 2
                        }

    def init_table(self):
        array = self.fetch_tree_style()
        self.model_ = MyGeneralTableModel(array, ["Parameters", "Value"], parent=self, tooltip_map=self.short2long)
        self.model_.dataChanged.connect(self.apply_changes)
        self.model_.layoutChanged.connect(self.apply_changes)
        self.setModel(self.model_)

    def fetch_tree_style(self):
        array = []
        for key in dict(self.default_parms_array):
            new_key = self.long2short[key] if key in self.long2short else key
            value = getattr(self.parent.scene.img, key)
            if key == "mode":
                dict_map = {"r": "Rectangular",
                            "c": "Circular"}
                array.append([new_key, [dict_map[value]] + [i for i in ["Rectangular",
                                                                     "Circular"] if i != dict_map[value]]])
            elif key == "orientation":
                dict_map = {0: "left-to-right",
                            1: "right-to-left"}
                array.append([new_key, [dict_map[value]] + [i for i in ["left-to-right",
                                                                     "right-to-left"] if i != dict_map[value]]])
            elif key == "optimal_scale_level":
                array.append([new_key, [value] + [i for i in ["mid", "full"] if i != value]])
            elif key in ["extra_branch_line_type", "guiding_lines_type"]:
                dict_map = {0: "solid",
                            1: "dashed",
                            2: "dotted"}
                array.append([new_key, [dict_map[value]] + [i for i in ["dotted", "solid",
                                                                     "dashed"] if i != dict_map[value]]])
            elif key == "legend_position":
                dict_map = {1: "Top Left",
                            2: "Top Right",
                            3: "Bottom Left",
                            4: "Bottom Right"}
                array.append([new_key, [dict_map[value]] + [i for i in ["Bottom Right", "Bottom Left",
                                                                     "Top Left", "Top Right"] if i != dict_map[value]]])
            elif key in ["extra_branch_line_color", "guiding_lines_color"]:
                array.append([new_key, value if value != "gray" else "#808080"])
            elif key == "scale":
                array.append([new_key, value if value != None else "auto scale"])
            else:
                array.append([new_key, value])
        return array

    def apply_changes(self):
        array = self.model_.arraydata
        for list_ in array:
            try:
                params = list_[0] if list_[0] not in self.short2long else self.short2long[list_[0]]
                if type(list_[1]) == list:
                    value = self.dict_value_map[list_[1][0]] if list_[1][0] in self.dict_value_map else list_[1][0]
                else:
                    value = self.dict_value_map[list_[1]] if list_[1] in self.dict_value_map else list_[1]
                if params == "scale":
                    value = int(value) if value not in ["auto scale", "auto"] else None
                setattr(self.parent.scene.img, params, value)
            except Exception as e:
                #logger(-1, "Wrong format for attribute:", name)
                print("Error happened!", e)
        # self.scene.img._scale = None
        self.parent.init_tree_props(ignore_init=True)
        self.parent.redraw()
        # self.parent.view.set_focus(self.node.id, by="id")
        return

    def set_style(self, style, value):
        for row_index,row in enumerate(self.model_.arraydata):
            style_ = row[0] if row[0] not in self.short2long else self.short2long[row[0]]
            if style_ == style:
                self.model_.arraydata[row_index][1] = value
                break
        self.model_.layoutChanged.emit()


class CheckBoxHeader(QHeaderView):
    clicked = pyqtSignal(bool, int)

    _x_offset = 4
    _y_offset = 0
    _width = 20
    _height = 20

    def __init__(self, orientation=Qt.Horizontal, parent=None, checked_cols=None):
        super(CheckBoxHeader, self).__init__(orientation, parent)
        self.isOn = checked_cols

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super(CheckBoxHeader, self).paintSection(painter, rect, logicalIndex)
        painter.restore()

        self._y_offset = int((rect.height()-self._width)/2.)

        if logicalIndex in self.isOn:
            option = QStyleOptionButton()
            option.rect = QRect(rect.x() + self._x_offset, rect.y() + self._y_offset, self._width, self._height)
            option.state = QStyle.State_Enabled | QStyle.State_Active
            if self.isOn[logicalIndex]:
                option.state |= QStyle.State_On
            else:
                option.state |= QStyle.State_Off
            self.style().drawControl(QStyle.CE_CheckBox, option, painter)

    def mousePressEvent(self, event):
        index = self.logicalIndexAt(event.pos())
        if index in self.isOn:
            x = self.sectionPosition(index)
            if x + self._x_offset < event.pos().x() < x + self._x_offset + self._width and self._y_offset < event.pos().y() < self._y_offset + self._height:
                if self.isOn[index]:
                    self.isOn[index] = False
                else:
                    self.isOn[index] = True
                self.clicked.emit(self.isOn[index], index)
                self.update()
        super(CheckBoxHeader, self).mousePressEvent(event)

class MyListWidget(QListWidget):

    def __init__(self, parent=None):
        super(MyListWidget, self).__init__(parent)

    def init_(self, stackedWidget, parent=None):
        self.parent = parent
        self.stackedWidget = stackedWidget
        self.itemClicked.connect(lambda item: [self.stackedWidget.setCurrentWidget(item.page_widget),
                                               self.parent.tabWidget.setCurrentIndex(2)])

    def get_checked_num(self):
        return len([index for index in range(self.count()) if index and self.itemWidget(self.item(index)).checkBox.isChecked()])

    def item_text(self, index):
        return self.itemWidget(self.item(index)).text_label.text()

    def isChecked(self, index):
        return self.itemWidget(self.item(index)).checkBox.isChecked()

    def get_page_widget(self, index):
        fac_item = self.item(index)
        return fac_item.page_widget

    def setItemChecked(self, item, bool_):
        self.itemWidget(item).checkBox.setChecked(bool_)

    def removeItem(self):
        sender = self.sender()
        item = sender.listwidgetItem
        reply = QMessageBox.information(
            self,
            "Confirmation",
            "<p style='line-height:25px; height:25px'>Are you sure that you want to remove this annotation? </p>",
            QMessageBox.Ok,
            QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            widget = item.page_widget
            removed_col = self.parent.remove_faces(widget.tableview.allfaces)
            if hasattr(widget.tableview, "titlefaces"):
                self.parent.remove_title_faces(widget.tableview.titlefaces)
            self.parent.reorder_faces(removed_col)
            self.takeItem(self.row(item))
            self.parent.redraw()
            self.stackedWidget.removeWidget(widget)
            widget.deleteLater()
            del widget


class ListItemWidget(QWidget):

    def __init__(self, text, listwidgetItem, parent=None, hide_btn=False, ifCheck=True):
        super(ListItemWidget, self).__init__(parent)
        self.text = text
        self.hide_btn = hide_btn
        self.ifCheck = ifCheck
        self.listwidgetItem = listwidgetItem
        self.initUi()

    def initUi(self):
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout.setSpacing(0)
        self.checkBox = QCheckBox(self)
        self.checkBox.listwidgetItem = self.listwidgetItem
        if self.ifCheck:
            self.checkBox.setChecked(True)
        self.text_label = QLabel(self.text, self)
        self.btn_close = QToolButton(self)
        self.btn_close.setIcon(QIcon(":/picture/resourses/if_Delete_1493279.png"))
        self.btn_close.setAutoRaise(True)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.parent_widget = self
        self.btn_close.listwidgetItem = self.listwidgetItem
        self.btn_close.setToolTip("Delete")
        self.btn_edit = QToolButton(self)
        self.btn_edit.setIcon(QIcon(":/picture/resourses/edit2.png"))
        self.btn_edit.setAutoRaise(True)
        self.btn_edit.setCursor(Qt.PointingHandCursor)
        self.btn_edit.setToolTip("Edit label")
        # self.btn_edit.clicked.connect(self.edit_label)
        self.horizontalLayout.addWidget(self.checkBox)
        self.horizontalLayout.addWidget(self.text_label)
        self.horizontalLayout.addStretch()
        self.horizontalLayout.addWidget(self.btn_edit)
        self.horizontalLayout.addWidget(self.btn_close)
        if self.hide_btn:
            self.btn_close.setHidden(True)

    def edit_label(self):
        oldLabel = self.text_label.text()
        newLabel, ok = QInputDialog.getText(self,
            'Change item label',
            'Label:',
            QLineEdit.Normal,
            oldLabel)
        if ok and (newLabel != oldLabel):
            self.text_label.setText(newLabel)

    def data(self):
        return [self.text, self.hide_btn, self.checkBox.isChecked()]


class _SelectorItem(QGraphicsRectItem):
    def __init__(self, parent=None):
        self.Color = QColor("blue")
        self._active = False
        QGraphicsRectItem.__init__(self, 0, 0, 0, 0)
        if parent:
            self.setParentItem(parent)

    def paint(self, p, option, widget):
        p.setPen(self.Color)
        p.setBrush(QBrush(Qt.NoBrush))
        p.drawRect(self.rect().x(),self.rect().y(),self.rect().width(),self.rect().height())
        return
        # Draw info text
        font = QFont("Arial",13)
        text = "%d selected."  % len(self.get_selected_nodes())
        textR = QFontMetrics(font).boundingRect(text)
        if  self.rect().width() > textR.width() and \
                self.rect().height() > textR.height()/2 and 0: # OJO !!!!
            p.setPen(QPen(self.Color))
            p.setFont(QFont("Arial",13))
            p.drawText(self.rect().bottomLeft().x(),self.rect().bottomLeft().y(),text)

    def get_selected_nodes(self):
        selPath = QPainterPath()
        selPath.addRect(self.rect())
        self.scene().setSelectionArea(selPath)
        return [i.node for i in self.scene().selectedItems()]

    def setActive(self,bool):
        self._active = bool

    def isActive(self):
        return self._active


class _TreeView(QGraphicsView):
    def __init__(self, *args, parent=None):
        QGraphicsView.__init__(self,*args)
        self.parent = parent
        self.setAcceptDrops(True)
        self.buffer_node = None
        # self.init_values()

        if USE_GL:
            print("USING GL")
            F = QtOpenGL.QGLFormat()
            F.setSampleBuffers(True)
            print(F.sampleBuffers())
            self.setViewport(QtOpenGL.QGLWidget(F))
            self.setRenderHints(QPainter.Antialiasing)
        else:
            self.setRenderHints(QPainter.Antialiasing or QPainter.SmoothPixmapTransform )

        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHints(QPainter.Antialiasing or QPainter.SmoothPixmapTransform )
        #self.setViewportUpdateMode(QGraphicsView.NoViewportUpdate)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        #self.setOptimizationFlag (QGraphicsView.DontAdjustForAntialiasing)
        self.setOptimizationFlag (QGraphicsView.DontSavePainterState)
        #self.setOptimizationFlag (QGraphicsView.DontClipPainter)
        #self.scene().setItemIndexMethod(QGraphicsScene.NoIndex)
        #self.scene().setBspTreeDepth(24)

    def init_values(self):
        master_item = self.scene().master_item
        self.n2hl = {}
        if self.scene().img.mode == "c":
            self.focus_highlight = crender._ArcItem()
        else:
            self.focus_highlight = QGraphicsRectItem(master_item)
        self.selected_highlight = self.focus_highlight
        #self.buffer_node = None
        self.focus_node = None
        self.selector = _SelectorItem(master_item)

    def resizeEvent(self, e):
        QGraphicsView.resizeEvent(self, e)

    def safe_scale(self, xfactor, yfactor):
        self.setTransformationAnchor(self.AnchorUnderMouse)
        xscale = self.transform().m11()
        yscale = self.transform().m22()
        srect = self.sceneRect()

        if (xfactor>1 and xscale>200000) or \
                (yfactor>1 and yscale>200000):
            QMessageBox.information(self, "!", \
                "I will take the microscope!")
            return

        # Do not allow to reduce scale to a value producing height or with smaller than 20 pixels
        # No restrictions to zoom in
        if (yfactor<1 and  srect.width() * yscale < 20):
            pass
        elif (xfactor<1 and  srect.width() * xscale < 20):
            pass
        else:
            self.scale(xfactor, yfactor)

    def highlight_node(self, n, fullRegion=False, fg="red", bg="gray", permanent=False):
        self.unhighlight_node(n)
        item = self.scene().n2i[n]
        if self.scene().img.mode == "c":
            if n.is_leaf():
                first_c = self.scene().n2i[n]
                last_c = self.scene().n2i[n]
            else:
                first_c = self.scene().n2i[n.children[0]]
                last_c = self.scene().n2i[n.children[-1]]
            h = item.effective_height
            angle_start = first_c.full_start
            angle_end = last_c.full_end
            parent_radius = getattr(self.scene().n2i.get(n.up, None), "radius", 0)
            hl = crender._ArcItem()
            # print(item.fullRegion.width(), item.nodeRegion.width())
            # base = parent_radius + item.fullRegion.width()
            max_r = self.scene().tree_item.rect().width()/2.0
            align_face_w = self.scene().tree_item.aligned_region_width
            base = max_r - align_face_w
            r = math.sqrt(base**2 + h**2)
            # bg.set_arc(0, 0, parent_radius, max_r, angle_start, angle_end)
            hl.set_arc(0, 0, parent_radius, r, angle_start, angle_end)
            hl.arc = (0, 0, parent_radius, r, angle_start, angle_end)
            hl.setParentItem(self.scene().tree_item.treeitem.bg_layer)
            hl.setZValue(item.zValue())
        else:
            hl = QGraphicsRectItem(item.content)
            if fullRegion:
                hl.setRect(item.fullRegion)
            else:
                hl.setRect(item.nodeRegion)
        hl.setPen(QColor(fg))
        hl.setBrush(QColor(bg))
        hl.setOpacity(0.2)
        # save info in Scene
        self.n2hl[n] = hl
        # self.selected_highlight = copy.deepcopy(hl)
        if permanent:
            item.highlighted = True

    def unhighlight_node(self, n, reset=False):
        if n in self.n2hl:
            item = self.scene().n2i[n]
            if not item.highlighted:
                self.scene().removeItem(self.n2hl[n])
                del self.n2hl[n]
            elif reset:
                self.scene().removeItem(self.n2hl[n])
                del self.n2hl[n]
                item.highlighted = False
            else:
                pass

    def wheelEvent(self,e):
        # qt4/5
        try:
            delta = e.delta()
        except AttributeError:
            delta = float(e.angleDelta().y())

        factor =  (-delta / 360.0)

        if abs(factor) >= 1:
            factor = 0.0

        # Ctrl+Shift -> Zoom in X
        if  (e.modifiers() & Qt.ControlModifier) and (e.modifiers() & Qt.ShiftModifier):
            self.safe_scale(1+factor, 1)

        # Ctrl+Alt -> Zomm in Y
        elif  (e.modifiers() & Qt.ControlModifier) and (e.modifiers() & Qt.AltModifier):
            self.safe_scale(1,1+factor)

        # Ctrl -> Zoom X,Y
        elif e.modifiers() & Qt.ControlModifier:
            self.safe_scale(1-factor, 1-factor)

        # Shift -> Horizontal scroll
        elif e.modifiers() &  Qt.ShiftModifier:
            if delta > 0:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-20 )
            else:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()+20 )
        # No modifiers ->  Vertival scroll
        else:
            if delta > 0:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value()-20 )
            else:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value()+20 )

    def set_focus(self, node):
        # node = node if by == "node" else self.scene().tree.search_nodes(id=node)[0]
        if node not in self.n2hl:
            return
        # when there are tree1 and tree2, auto switch them
        if hasattr(node, "parent"):
            if node.parent == "tree1":
                self.parent.toolButton.setChecked(True)
            elif node.parent == "tree2":
                self.parent.toolButton_2.setChecked(True)
        i = self.scene().n2i[node]
        self.focus_highlight.setPen(QColor("red"))
        self.focus_highlight.setBrush(QColor("SteelBlue"))
        self.focus_highlight.setOpacity(0.2)
        if self.scene().img.mode == "c":
            self.focus_highlight.setParentItem(self.scene().tree_item.treeitem.bg_layer)
            cxdist, cydist, r1, r2, angle_start, angle_end = self.n2hl[node].arc
            self.focus_highlight.set_arc(cxdist, cydist, r1, r2, angle_start, angle_end)
        else:
            self.focus_highlight.setParentItem(i.content)
            self.focus_highlight.setRect(self.n2hl[node].rect())
        self.focus_highlight.setVisible(True)
        self.node_prop_table.update_properties(node)
        #self.focus_highlight.setRect(i.nodeRegion)
        self.focus_node = node
        self.parent.tabWidget.setCurrentIndex(1)
        self.parent.update_tree_message(node)
        self.update()

    def hide_focus(self):
        return
        #self.focus_highlight.setVisible(False)

    def keyPressEvent(self,e):
        key = e.key()
        control = e.modifiers() & Qt.ControlModifier
        if control:
            if key  == Qt.Key_Left:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()-20 )
                self.update()
            elif key  == Qt.Key_Right:
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()+20 )
                self.update()
            elif key  == Qt.Key_Up:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value()-20 )
                self.update()
            elif key  == Qt.Key_Down:
                self.verticalScrollBar().setValue(self.verticalScrollBar().value()+20 )
                self.update()
        else:
            if not self.focus_node:
                self.focus_node = self.scene().tree

            if key == Qt.Key_Left:
                if self.focus_node.up:
                    new_focus_node = self.focus_node.up
                    self.set_focus(new_focus_node)
            elif key == Qt.Key_Right:
                if self.focus_node.children:
                    new_focus_node = self.focus_node.children[0]
                    self.set_focus(new_focus_node)
            elif key == Qt.Key_Up:
                if self.focus_node.up:
                    i = self.focus_node.up.children.index(self.focus_node)
                    if i>0:
                        new_focus_node = self.focus_node.up.children[i-1]
                        self.set_focus(new_focus_node)
                    elif self.focus_node.up:
                        self.set_focus(self.focus_node.up)

            elif key == Qt.Key_Down:
                if self.focus_node.up:
                    i = self.focus_node.up.children.index(self.focus_node)
                    if i < len(self.focus_node.up.children)-1:
                        new_focus_node = self.focus_node.up.children[i+1]
                        self.set_focus(new_focus_node)
                    elif self.focus_node.up:
                        self.set_focus(self.focus_node.up)

            elif key == Qt.Key_Escape:
                self.hide_focus()
            elif key == Qt.Key_Enter or \
                    key == Qt.Key_Return:
                if hasattr(self.node_prop_table, "tableView"):
                    self.node_prop_table.tableView.setFocus()
            elif key == Qt.Key_Space:
                self.highlight_node(self.focus_node, fullRegion=True,
                    bg=random_color(l=0.5, s=0.5),
                    permanent=True)
        QGraphicsView.keyPressEvent(self,e)

    def mouseReleaseEvent(self, e):
        self.scene().view.hide_focus()
        curr_pos = self.mapToScene(e.pos())
        if hasattr(self.selector, "startPoint"):
            x = min(self.selector.startPoint.x(),curr_pos.x())
            y = min(self.selector.startPoint.y(),curr_pos.y())
            w = max(self.selector.startPoint.x(),curr_pos.x()) - x
            h = max(self.selector.startPoint.y(),curr_pos.y()) - y
            if self.selector.startPoint == curr_pos:
                self.selector.setVisible(False)
            self.selector.setActive(False)
        QGraphicsView.mouseReleaseEvent(self,e)

    def mousePressEvent(self,e):
        if not self.scene().tree:
            return
        pos = self.mapToScene(e.pos())
        x, y = pos.x(), pos.y()
        try:
            self.selector.setRect(x, y, 0,0)
        except RuntimeError as e:
            print(e)
            return
        self.selector.setRect(x, y, 0,0)
        self.selector.startPoint = QPointF(x, y)
        self.selector.setActive(True)
        self.selector.setVisible(True)
        QGraphicsView.mousePressEvent(self,e)

    def mouseMoveEvent(self,e):
        curr_pos = self.mapToScene(e.pos())
        if self.selector.isActive():
            x = min(self.selector.startPoint.x(),curr_pos.x())
            y = min(self.selector.startPoint.y(),curr_pos.y())
            w = max(self.selector.startPoint.x(),curr_pos.x()) - x
            h = max(self.selector.startPoint.y(),curr_pos.y()) - y
            self.selector.setRect(x,y,w,h)
        QGraphicsView.mouseMoveEvent(self, e)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            # must accept the dragEnterEvent or else the dropEvent
            # can't occur !!!
            event.accept()
        super(_TreeView, self).dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file in files:
            self.parent.handle_iTOL_files(file)
        event.accept()
        super(_TreeView, self).dropEvent(event)

class QGraphicsRightArrowItem(QGraphicsPolygonItem):
    def __init__(self, width=10, height=10, height_factor=1/3, width_factor=1/3):
        self.width_factor = width_factor
        self.height_factor = height_factor
        width_ = width*(1-width_factor)
        height_ = height*(1-height_factor)
        eaves_height = height*(height_factor)/2
        self.shape = QPolygonF([
            QPointF(0, eaves_height),
            QPointF(width_, eaves_height),
            QPointF(width_, 0),
            QPointF(width, height/2),
            QPointF(width_, height),
            QPointF(width_, height_+eaves_height),
            QPointF(0, height_+eaves_height),
            QPointF(0, eaves_height),
        ])
        QGraphicsPolygonItem.__init__(self, self.shape)

class QGraphicsLeftArrowItem(QGraphicsPolygonItem):
    def __init__(self, width, height, height_factor=1/3, width_factor=1/3):
        self.width_factor = width_factor
        self.height_factor = height_factor
        width_ = width*(1-width_factor)
        height_ = height*(1-height_factor)
        eaves_height = height*(height_factor)/2
        self.shape = QPolygonF([
            QPointF(0, height/2),
            QPointF(width*width_factor, 0),
            QPointF(width*width_factor, eaves_height),
            QPointF(width, eaves_height),
            QPointF(width, height_ + eaves_height),
            QPointF(width*width_factor, height_+eaves_height),
            QPointF(width*width_factor, height),
            QPointF(0, height/2),
        ])
        QGraphicsPolygonItem.__init__(self, self.shape)

class QGraphicsLeftTriangleItem(QGraphicsPolygonItem):

    def __init__(self, width, height):
        self.tri = QPolygonF()
        self.tri.append(QPointF(0, height / 2.0))
        self.tri.append(QPointF(width, 0))
        self.tri.append(QPointF(width, height))
        self.tri.append(QPointF(0, height / 2.0))
        QGraphicsPolygonItem.__init__(self, self.tri)

class QGraphicsRightTriangleItem(QGraphicsPolygonItem):

    def __init__(self, width, height):
        self.tri = QPolygonF()
        self.tri.append(QPointF(0, 0))
        self.tri.append(QPointF(0, height))
        self.tri.append(QPointF(width, height / 2.0))
        self.tri.append(QPointF(0, 0))
        QGraphicsPolygonItem.__init__(self, self.tri)

class QGraphicsTopTriangleItem(QGraphicsPolygonItem):

    def __init__(self, width, height):
        self.tri = QPolygonF()
        self.tri.append(QPointF(0, height))
        self.tri.append(QPointF(width, height))
        self.tri.append(QPointF(width / 2.0, 0))
        self.tri.append(QPointF(0, height))
        QGraphicsPolygonItem.__init__(self, self.tri)

class QGraphicsBottomTriangleItem(QGraphicsPolygonItem):

    def __init__(self, width, height):
        self.tri = QPolygonF()
        self.tri.append(QPointF(0, 0))
        self.tri.append(QPointF(width, 0))
        self.tri.append(QPointF(width / 2.0, height))
        self.tri.append(QPointF(0, 0))
        QGraphicsPolygonItem.__init__(self, self.tri)

class QGraphicsRoundRectItem(QGraphicsRectItem):
    def __init__(self, x, y, width, height,  *args, **kargs):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        QGraphicsRectItem.__init__(self, x, y, width, height, *args, **kargs)
    def paint(self, p, option, widget):
        p.setPen(self.pen())
        p.setBrush(self.brush())
        p.drawRoundedRect(self.rect(),
            min([self.width, self.height])*(1/4), min([self.width, self.height])*(1/4))

class QGraphicsDiamondItem(QGraphicsPolygonItem):
    def __init__(self, width, height):
        self.pol = QPolygonF()
        self.pol.append(QPointF(width / 2.0, 0))
        self.pol.append(QPointF(width, height / 2.0))
        self.pol.append(QPointF(width / 2.0, height))
        self.pol.append(QPointF(0, height / 2.0))
        self.pol.append(QPointF(width / 2.0, 0))
        QGraphicsPolygonItem.__init__(self, self.pol)

class QGraphicsStarItem(QGraphicsPolygonItem):
    '''
    https://blog.csdn.net/weixin_42126427/article/details/105219245?spm=1035.2023.3001.6557&utm_medium=distribute.pc_relevant_bbs_down.none-task-blog-2~default~OPENSEARCH~default-2.nonecase&depth_1-utm_source=distribute.pc_relevant_bbs_down.none-task-blog-2~default~OPENSEARCH~default-2.nonecase
    '''
    def __init__(self, R):
        R = R/2
        pi = 3.1415926
        deg = pi * 72/180
        self.pol = QPolygonF()
        self.pol.append(QPointF(R,0)) # 0
        self.pol.append(QPointF(R * math.cos(2 * deg), -R * math.sin(2 * deg))) # 2
        self.pol.append(QPointF(R * math.cos(4 * deg), -R * math.sin(4 * deg))) # 4
        self.pol.append(QPointF(R * math.cos(deg), -R * math.sin(deg))) # 1
        self.pol.append(QPointF(R * math.cos(3 * deg), -R * math.sin(3 * deg))) # 3
        self.pol.append(QPointF(R,0)) # 0
        QGraphicsPolygonItem.__init__(self, self.pol)

class QGraphicsStarItem2(QGraphicsPolygonItem):
    '''
    https://blog.csdn.net/weixin_42126427/article/details/105219245?spm=1035.2023.3001.6557&utm_medium=distribute.pc_relevant_bbs_down.none-task-blog-2~default~OPENSEARCH~default-2.nonecase&depth_1-utm_source=distribute.pc_relevant_bbs_down.none-task-blog-2~default~OPENSEARCH~default-2.nonecase
    '''
    def __init__(self, R):
        alpha = R/200
        self.pol = QPolygonF()
        self.pol.append(QPointF(0*alpha, 85*alpha))
        self.pol.append(QPointF(75*alpha, 75*alpha))
        self.pol.append(QPointF(100*alpha, 10*alpha))
        self.pol.append(QPointF(125*alpha, 75*alpha))
        self.pol.append(QPointF(200*alpha, 85*alpha))
        self.pol.append(QPointF(150*alpha, 125*alpha))
        self.pol.append(QPointF(160*alpha, 190*alpha))
        self.pol.append(QPointF(100*alpha, 150*alpha))
        self.pol.append(QPointF(40*alpha, 190*alpha))
        self.pol.append(QPointF(50*alpha, 125*alpha))
        self.pol.append(QPointF(0*alpha, 85*alpha))
        QGraphicsPolygonItem.__init__(self, self.pol)

class QGraphicsLeftArrowItem2(QGraphicsPolygonItem):
    def __init__(self, width, height, width_factor=1/3):
        self.width_factor = width_factor
        self.shape = QPolygonF([
            QPointF(0, height/2),
            QPointF(width*width_factor, 0),
            QPointF(width, 0),
            QPointF(width, height),
            QPointF(width*width_factor, height),
            QPointF(0, height/2),
        ])
        QGraphicsPolygonItem.__init__(self, self.shape)

class QGraphicsRightArrowItem2(QGraphicsPolygonItem):
    def __init__(self, width, height, width_factor=1/3):
        self.width_factor = width_factor
        self.shape = QPolygonF([
            QPointF(0, 0),
            QPointF(width*(1-width_factor), 0),
            QPointF(width, height/2),
            QPointF(width*(1-width_factor), height),
            QPointF(0, height),
            QPointF(0, 0),
        ])
        QGraphicsPolygonItem.__init__(self, self.shape)

# 也试试下面这种方法？
# 这是用路径画的，searchlightRect是一个矩形区域，这个五角星大小就是这个区域的大小pentagonPath.moveTo(searchlightRect.x()+searchlightRect.width()/2 , searchlightRect.y()) ;        pentagonPath.lineTo(searchlightRect.x()+searchlightRect.width()/3 , searchlightRect.y() + searchlightRect.height()*0.36) ;        pentagonPath.lineTo(searchlightRect.x(), searchlightRect.y() + searchlightRect.height()*0.36) ;        pentagonPath.lineTo(searchlightRect.x()+searchlightRect.width()/4 , searchlightRect.y()+searchlightRect.height()*14/24) ;        pentagonPath.lineTo(searchlightRect.x()+searchlightRect.width()*0.19 , searchlightRect.y()+searchlightRect.height()) ;        pentagonPath.lineTo(searchlightRect.x()+searchlightRect.width()/2 , searchlightRect.y()+searchlightRect.height()*18/24) ;        pentagonPath.lineTo(searchlightRect.x()+searchlightRect.width()*0.81 , searchlightRect.y()+searchlightRect.height()) ;        pentagonPath.lineTo(searchlightRect.x()+searchlightRect.width()*3/4 , searchlightRect.y() + searchlightRect.height()*14/24) ;        pentagonPath.lineTo(searchlightRect.x()+searchlightRect.width() , searchlightRect.y()+searchlightRect.height()*0.36) ;        pentagonPath.lineTo(searchlightRect.x()+searchlightRect.width()*2/3 , searchlightRect.y()+searchlightRect.height()*0.36) ;        pentagonPath.closeSubpath();

