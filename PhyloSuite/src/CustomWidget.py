#!/usr/bin/env python
# -*- coding: utf-8 -*-

import platform
import re
from collections import OrderedDict
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import operator  # used for sorting
import traceback, sip
import os
import time
from dateutil.parser import parse

# class MyTextEdit(QTextEdit, object):
#
#     def __init__(self, *args):
#         super().__init__(*args)
#
#     def focusInEvent(self, event):
#         if "One id per line, for example:" in self.toPlainText():
#             self.clear()
#             return True

class MyQtableView(QTableView, object):

    def __init__(self, *args):
        super().__init__(*args)
        self.undoStack = QUndoStack(self)

    def mousePressEvent(self, event):
        # 只让左键点击生效，右键不管
        if event.button() == Qt.LeftButton:
            QTableView.mousePressEvent(self, event)
            return
        else:
            pass

    def startDrag(self, supportedActions):
        listsQModelIndex = self.selectedIndexes()
        if listsQModelIndex:
            dataQMimeData = self.model().mimeData(listsQModelIndex)
            if not dataQMimeData:
                return None
            dragQDrag = QDrag(self)
            # <- For put your
            # dragQDrag.setPixmap(QPixmap(":/picture/resourses/DND.png"))
            # custom image here
            dragQDrag.setMimeData(dataQMimeData)
            defaultDropAction = Qt.IgnoreAction
            if ((supportedActions & Qt.CopyAction) and (self.dragDropMode() != QAbstractItemView.InternalMove)):
                defaultDropAction = Qt.CopyAction
            dragQDrag.exec_(supportedActions, defaultDropAction)
            # return True
    # def event(self, event):
    #     if (event.type() == QEvent.KeyPress) and (event.key() == Qt.RightButton):
    #         return True
    #     # elif (event.type() == QEvent.KeyPress) and (event.key() in self.list_residue):
    #     #     self.emit(SIGNAL(chr(event.key()) + "Pressed"), chr(event.key()))
    #     #     return True
    #     return QTableView.event(self, event)


class MyDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super(MyDoubleSpinBox, self).__init__(parent)
        # any RegExp that matches the allowed input
        self.validator = QRegExpValidator(QRegExp(r"\d+?\.[50]"), self)

    def validate(self, text, pos):
        # this decides if the entered value should be accepted
        return self.validator.validate(text, pos)


class CheckBoxHeader(QHeaderView):
    clicked=pyqtSignal(bool)

    _x_offset = 3
    _y_offset = 0  # This value is calculated later, based on the height of the paint rect
    _width = 20
    _height = 20

    def __init__(self,orientation=Qt.Horizontal,parent=None):
        super(CheckBoxHeader,self).__init__(orientation,parent)
        self.setSectionsClickable(True) ##有了这个才可以排序
        self.isChecked=False

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super(CheckBoxHeader, self).paintSection(painter, rect, logicalIndex)
        painter.restore()

        #
        self._y_offset = int((rect.height()-self._width)/2.)

        if logicalIndex == 0:
            option = QStyleOptionButton()
            option.rect = QRect(rect.x() + self._x_offset, rect.y() + self._y_offset, self._width, self._height)
            option.state = QStyle.State_Enabled | QStyle.State_Active
            if self.isChecked:
                option.state |= QStyle.State_On
            else:
                option.state |= QStyle.State_Off

            self.style().drawControl(QStyle.CE_CheckBox,option,painter)

    def mousePressEvent(self,event):
        index = self.logicalIndexAt(event.pos())
        if 0 <= index < self.count():
            x = self.sectionPosition(index)
            if x + self._x_offset < event.pos().x() < x + self._x_offset + self._width and self._y_offset < event.pos().y() < self._y_offset + self._height:
                if self.isChecked:
                    self.isChecked = False
                else:
                    self.isChecked = True

                self.clicked.emit(self.isChecked)
                self.viewport().update()
            else:
                super(CheckBoxHeader, self).mousePressEvent(event)
        else:
            super(CheckBoxHeader, self).mousePressEvent(event)


class MyTableModel(QAbstractTableModel):
    modifiedSig = pyqtSignal(list, int, int)

    def __init__(self, datain, highlightRepeat={}, parent=None, highlightIDs=[]):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.array = datain
        self.arraydata = datain[1:]
        self.headerdata = datain[0]
        # self.validatedIDs = validatedIDs
        self.highlightRepeat = highlightRepeat
        self.highlightIDs = highlightIDs
        self.un_editable_col = ["ID", "Length", "AT%", "Date",
                                "Latest modified", "author(s)", "title(s)",
                                "journal(s)", "pubmed ID(s)", "comment(s)",
                                "Keywords", "Molecule type", "Topology",
                                "Accessions", "Sequence version", "Source"]

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if len(self.arraydata) > 0:
            return len(self.arraydata[0])
        else:
            return 0

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        # elif role != Qt.DisplayRole:
        # if role == Qt.DisplayRole or role == Qt.EditRole:
        elif role == Qt.BackgroundRole and (self.arraydata[index.row()][0] in self.highlightIDs):
            return QColor("green")
        elif role == Qt.BackgroundRole and (self.arraydata[index.row()][0].split(".")[0] in self.highlightIDs):
            return QColor("green")
        elif role == Qt.BackgroundRole and (index.row() % 2 == 1):
            return QColor(255, 255, 255)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 0):
            return QColor(237, 243, 254)
        elif role == Qt.ForegroundRole:
            if self.highlightRepeat:
                if self.arraydata[index.row()][0] in self.highlightRepeat:
                    return QColor(self.highlightRepeat[self.arraydata[index.row()][0]])
            if (self.arraydata[index.row()][0] in self.highlightIDs) or \
                    (self.arraydata[index.row()][0].split(".")[0] in self.highlightIDs):
                return QColor("white")
        elif role == Qt.ToolTipRole:
            # if index.column() == 0:
            #     if self.arraydata[index.row()][index.column()] in self.validatedIDs:
            #         return "verified"
            #     else:
            #         return "not verified"
            if self.arraydata[index.row()][index.column()] == "N/A":
                toolTip = "not available"
            else:
                toolTip = self.arraydata[index.row()][index.column()]
            if self.headerdata[index.column()] not in self.un_editable_col:
                toolTip = "<html><head/><body>" + toolTip +\
                          '<br><span style="color: green">&#9733;Double-click to edit</span></body></html>    '
            return toolTip
        # elif role == Qt.DecorationRole:
        #     if index.column() == 0:
        #         if self.arraydata[index.row()][index.column()] in self.validatedIDs:
        #             return QIcon(":/picture/resourses/images_1.png")
        #         else:
        #             return QIcon(":/picture/resourses/unVlidated.png")
        elif role == Qt.EditRole:
            return self.arraydata[index.row()][index.column()]
        elif role == Qt.DisplayRole:
            return self.arraydata[index.row()][index.column()]
        # 这一项必须放在最后，不然其他项不生效
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None
        # if index.row() == 2 and index.column() == 3:
        #     print(self.arraydata)
        #     print(self.arraydata[index.row()][index.column()])
        # return (self.arraydata[index.row()][index.column()])

    def setData(self, index, value, role):
        if role == Qt.EditRole:
            if type(value) == QColor or (value in ["#edf3fe", "#ffffff"]):
                ## 有时候拖错了，就变成了color
                return True
            oldValue = self.arraydata[index.row()][index.column()]
            value = value.strip() if type(value) == str else value
            self.arraydata[index.row()][index.column()] = value
            if value != oldValue:
                self.dataChanged.emit(index, index)
                self.modifiedSig.emit([self.headerdata] + self.arraydata, index.row(), index.column())
        # print("new_data:%s, old data:%s" % (value, oldValue))
        # print("array row: ", self.arraydata[index.row()])
        # print("ID: %s" % self.arraydata[index.row()][0])
        return True

    def headerData(self, number, orientation, role):
        # 行表头
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headerdata[number]
        # 列表头
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(number + 1)

    def sort(self, Ncol, order):
        """
        Sort table by given column number.
        """
        self.layoutAboutToBeChanged.emit()
        reverse_ = True if order == Qt.DescendingOrder else False
        if self.headerdata[Ncol] in ["Date", "Latest modified"]:
            self.arraydata = sorted(self.arraydata,
                                    key=lambda x: int(time.mktime(parse(x[Ncol]).timetuple())), reverse=reverse_)
        elif self.headerdata[Ncol] == "Length":
            self.arraydata = sorted(self.arraydata, key=lambda x: int(x[Ncol]), reverse=reverse_)
        elif self.headerdata[Ncol] == "AT%":
            self.arraydata = sorted(self.arraydata, key=lambda x: float(x[Ncol]), reverse=reverse_)
        else:
            self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol), reverse=reverse_)
        self.layoutChanged.emit()

    def flags(self, index):
        if self.headerdata[index.column()] in self.un_editable_col:
            ##这几列不能编辑
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def updateModel(self, array):
        self.array = array
        self.arraydata = array[1:]
        self.headerdata = array[0]
        # self.validatedIDs = validatedIDs
        self.layoutChanged.emit()

class MyNCBITableModel(QAbstractTableModel):
    checkedChanged = pyqtSignal()

    def __init__(self, datain, list_checked=[], parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.array = datain
        self.arraydata = datain[1:]
        self.headerdata = datain[0]
        for num, i in enumerate(self.arraydata):
            self.arraydata[num][0] = QCheckBox(i[0])
        self.list_checked = list_checked

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if len(self.arraydata) > 0:
            return len(self.arraydata[0])
        else:
            return 0

    def data(self, index, role):
        if not index.isValid():
            return None
        if index.column() == 0:
            value = self.arraydata[index.row()][index.column()].text()
        else:
            value = self.arraydata[index.row()][index.column()]
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        # elif role != Qt.DisplayRole:
        # if role == Qt.DisplayRole or role == Qt.EditRole:
        elif role == Qt.BackgroundRole and (index.row() % 2 == 1):
            return QColor(255, 255, 255)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 0):
            return QColor(237, 243, 254)
        elif role == Qt.ToolTipRole:
            return value
        # elif role == Qt.DecorationRole:
        #     if index.column() == 0:
        #         if value in self.validatedIDs:
        #             return QIcon(":/picture/resourses/images_1.png")
        #         else:
        #             return QIcon(":/picture/resourses/unVlidated.png")
        elif role == Qt.EditRole:
            return value
        elif role == Qt.DisplayRole:
            return value
        elif role == Qt.CheckStateRole:
            if index.column() == 0:
                if value in self.list_checked:
                    return Qt.Checked
                else:
                    return Qt.Unchecked
        # 这一项必须放在最后，不然其他项不生效
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None
        # if index.row() == 2 and index.column() == 3:
        #     print(self.arraydata)
        #     print(value)
        # return (value)

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole and index.column() == 0:
            if value == Qt.Checked:
                self.arraydata[index.row()][index.column()].setChecked(True)
                # 必须要操作list_checked，不然会有各种问题
                self.list_checked.append(self.arraydata[index.row()][index.column()].text())
            else:
                self.arraydata[index.row()][index.column()].setChecked(False)
                self.list_checked.remove(self.arraydata[index.row()][index.column()].text())
            self.checkedChanged.emit()
            self.dataChanged.emit(index, index)
        return True

    def headerData(self, number, orientation, role):
        # 行表头
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headerdata[number]
        # 列表头
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(number + 1)

    def sort(self, Ncol, order):
        """
        Sort table by given column number.
        """
        self.layoutAboutToBeChanged.emit()
        reverse_ = True if order == Qt.DescendingOrder else False
        if self.headerdata[Ncol] == "ID":
            self.arraydata = sorted(self.arraydata,
                                    key=lambda x: x[Ncol].text(), reverse=reverse_)
        elif self.headerdata[Ncol] in ["Update date", "Create date"]:
            self.arraydata = sorted(self.arraydata,
                                    key=lambda x: int(time.mktime(parse(x[Ncol]).timetuple())), reverse=reverse_)
        elif self.headerdata[Ncol] == "Length":
            self.arraydata = sorted(self.arraydata, key=lambda x: int(x[Ncol]), reverse=reverse_)
        else:
            self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol), reverse=reverse_)
        self.layoutChanged.emit()

    def flags(self, index):
        # if self.headerdata[index.column()] in self.un_editable_col:
            ##这几列不能编辑
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        # else:
        #     return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def fetchAllIDs(self):
        return [i[0].text() for num, i in enumerate(self.arraydata)]

    def appendTable(self, newData):
        self.layoutAboutToBeChanged.emit()
        newData[0] = QCheckBox(newData[0])
        self.arraydata.append(newData)
        self.layoutChanged.emit()

    def init_table(self):
        self.arraydata = []
        self.layoutChanged.emit()


class MySettingTableModel(QAbstractTableModel):

    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = datain
        self.uniqueArray()
        self.headerdata = headerdata

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if len(self.arraydata) > 0:
            return len(self.arraydata[0])
        else:
            return 0

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        # elif role != Qt.DisplayRole:
        # if role == Qt.DisplayRole or role == Qt.EditRole:
        elif role == Qt.BackgroundRole and (index.row() % 2 == 1):
            return QColor(255, 255, 255)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 0):
            return QColor(237, 243, 254)
        elif role == Qt.ToolTipRole:
            return self.arraydata[index.row()][index.column()]
        # 这一项必须放在最后，不然其他项不生效
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None
        return (self.arraydata[index.row()][index.column()])

    def setData(self, index, value, role):
        self.arraydata[index.row()][index.column()] = value
        self.dataChanged.emit(index, index)
        return True

    def headerData(self, number, orientation, role):
        # 行表头
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headerdata[number]
        # 列表头
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(number + 1)

    def sort(self, Ncol, order):
        """
        Sort table by given column number.
        """
        self.layoutAboutToBeChanged.emit()
        # self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
        if order == Qt.DescendingOrder:
            self.arraydata.reverse()
        # self.emit(SIGNAL("layoutChanged()"))
        self.layoutChanged.emit()

    def flags(self, index):
        # | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def uniqueArray(self):
        list_unique = []
        for j in self.arraydata:
            if j not in list_unique:
                list_unique.append(j)
        self.arraydata = list_unique

class MyExtractSettingModel(MySettingTableModel, QAbstractTableModel):

    def __init__(self, datain, headerdata, parent=None):
        super(MyExtractSettingModel, self).__init__(datain, headerdata, parent)

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        # elif role != Qt.DisplayRole:
        # if role == Qt.DisplayRole or role == Qt.EditRole:
        elif role == Qt.BackgroundRole and (index.row() % 2 == 1):
            return QColor(255, 255, 255)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 0):
            return QColor(237, 243, 254)
        # 这一项必须放在最后，不然其他项不生效
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None
        return (self.arraydata[index.row()][index.column()])


class MyModelTableModel(QAbstractTableModel):

    def __init__(self, datain, headerdata, list_checked, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = datain
        self.header = headerdata
        self.list_checked = list_checked

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        if index.column() == 0:
            value = self.arraydata[index.row()][index.column()].text()
        else:
            value = self.arraydata[index.row()][index.column()]
        if role == Qt.EditRole:
            return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.DisplayRole:
            return value
        elif role == Qt.BackgroundRole and (index.row() % 2 == 1):
            return QColor(255, 255, 255)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 0):
            return QColor(237, 243, 254)
        elif role == Qt.ToolTipRole:
            return value
        elif role == Qt.CheckStateRole:
            if index.column() == 0:
                if value in self.list_checked:
                    return Qt.Checked
                else:
                    return Qt.Unchecked
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

    def headerData(self, number, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[number]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(number + 1)
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        self.layoutAboutToBeChanged.emit()
        reverse_ = True if order == Qt.DescendingOrder else False
        if col != 0:
            self.arraydata = sorted(self.arraydata, key=operator.itemgetter(col), reverse=reverse_)
        else:
            self.arraydata = sorted(self.arraydata,
                                    key=lambda x: x[col].text(), reverse=reverse_)
        self.layoutChanged.emit()
        # # else:
        #     self.layoutAboutToBeChanged.emit()
        #     for num, i in enumerate(self.arraydata):
        #         self.arraydata[num][0] = i[0].text()
        #     self.arraydata = sorted(self.arraydata, key=operator.itemgetter(col))
        #     if order == Qt.DescendingOrder:
        #         self.arraydata.reverse()
        #     self.addCheckbox()
        #     self.layoutChanged.emit()

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role == Qt.CheckStateRole and index.column() == 0:
            if value == Qt.Checked:
                self.arraydata[index.row()][index.column()].setChecked(True)
                # 必须要操作list_checked，不然会有各种问题
                self.list_checked.append(self.arraydata[index.row()][index.column()].text())
            else:
                self.arraydata[index.row()][index.column()].setChecked(False)
                self.list_checked.remove(self.arraydata[index.row()][index.column()].text())
            self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        if not index.isValid():
            return None
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class MyPartitionTableModel(QAbstractTableModel):
    ##带checkbox的，可以设置CDS的版本
    def __init__(self, datain, headerdata, list_checked, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = datain
        self.header = headerdata
        self.list_checked = list_checked  #保存行号

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        if index.column() == 0:
            value = self.arraydata[index.row()][index.column()].text()
        elif index.column() == 2:
            value = "="
        elif index.column() == 4:
            value = "-"
        else:
            value = self.arraydata[index.row()][index.column()]
        if role == Qt.EditRole:
            return value
        if role == Qt.DisplayRole:
            return value
        elif role == Qt.BackgroundRole and (index.column() in [0, 2, 4]):
            return QColor("#F0F0F0")
        elif role == Qt.BackgroundRole and (index.row() % 2 == 1):
            return QColor(255, 255, 255)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 0):
            return QColor(237, 243, 254)
        elif role == Qt.ToolTipRole:
            return value
        elif role == Qt.CheckStateRole:
            if index.column() == 0:
                if index.row() in self.list_checked:
                    return Qt.Checked
                else:
                    return Qt.Unchecked
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
        if role == Qt.CheckStateRole and index.column() == 0:
            if value == Qt.Checked:
                self.arraydata[index.row()][index.column()].setChecked(True)
                # 必须要操作list_checked，不然会有各种问题
                self.list_checked.append(index.row())
            else:
                self.arraydata[index.row()][index.column()].setChecked(False)
                self.list_checked.remove(index.row())
            self.dataChanged.emit(index, index)
            return True
        elif role == Qt.EditRole:
            self.arraydata[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True

    def flags(self, index):
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        elif index.column() in [0, 2, 4]:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

class MyPartDisplayTableModel(QAbstractTableModel):
    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = datain
        self.header = headerdata

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.arraydata[index.row()][index.column()]
        if role == Qt.EditRole:
            return value
        if role == Qt.DisplayRole:
            return value
        elif role == Qt.BackgroundRole and (value in ["=", "-", " "]):
            return QColor("#F0F0F0")
        elif role == Qt.SizeHintRole and (value in ["=", "-", " "]):
            return QSize(20, 20)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 1):
            return QColor(255, 255, 255)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 0):
            return QColor(237, 243, 254)
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
        if role == Qt.EditRole:
            self.arraydata[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
        return True

    def flags(self, index):
        if index.row() <= len(self.arraydata) and index.column() <= len(self.arraydata[0]):
            if index.row() <= (len(self.arraydata) - 1):
                if self.arraydata[index.row()][index.column()] in ["=", "-", " "]:
                    return Qt.ItemIsEnabled | Qt.ItemIsSelectable
                else:
                    return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        return super(MyPartDisplayTableModel, self).flags(index)


class MyPartEditorTableModel(QAbstractTableModel):
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

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if self.arraydata: return len(self.arraydata[0])
        else: return 0

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.arraydata[index.row()][index.column()]
        if role == Qt.EditRole:
            return value
        if role == Qt.DisplayRole:
            return value
        elif role == Qt.BackgroundRole and (value in ["=", "-", " "]):
            return QColor("#F0F0F0")
        elif role == Qt.SizeHintRole and (value in ["=", "-", " "]):
            return QSize(20, 20)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 1):
            return QColor(255, 255, 255)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 0):
            return QColor(237, 243, 254)
        elif role == Qt.ToolTipRole:
            return value
        elif role == Qt.TextAlignmentRole:
            if index.column() == 0: return Qt.AlignVCenter | Qt.AlignRight
            else: return Qt.AlignCenter
        elif role == Qt.DecorationRole:
            if self.parent.data_type == "AA": return None
            if index.column() == 0:
                try:
                    start = int(self.arraydata[index.row()][2])
                    stop = int(self.arraydata[index.row()][4].replace("\\3", "").replace("\\2", ""))
                    if "\\3" in self.arraydata[index.row()][4]:
                        if (stop - start + 1)%3 == 0: return QIcon(":/picture/resourses/1.png")
                        elif (stop - start + 1)%3 == 2: return QIcon(":/picture/resourses/2.png")
                        elif (stop - start + 1)%3 == 1: return QIcon(":/picture/resourses/3.png")
                    elif "\\2" in self.arraydata[index.row()][4]:
                        if (stop - start + 1)%2 == 1: return QIcon(":/picture/resourses/2.png")
                        elif (stop - start + 1)%2 == 0: return QIcon(":/picture/resourses/1.png")
                    elif ((stop - start + 1) % 3 == 0) and ((stop - start + 1) % 2 == 0):
                        return QIcon(":/picture/resourses/2_3.png")
                    elif (stop - start + 1)%3 == 0:
                        return QIcon(":/picture/resourses/3.png")
                    elif (stop - start + 1) % 2 == 0:
                        return QIcon(":/picture/resourses/2.png")
                except: pass
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
        if role == Qt.EditRole:
            if index.column() == 0:
                value = self.parent.factory.refineName(value.strip(), remain_words="-")
            if index.column() == 2:
                if not value.isnumeric(): return False
            if index.column() == 4:
                if not re.search(r"^[0-9\\]*$", value): return False
            self.arraydata[index.row()][index.column()] = value
            if index.column() == 2: self.dataChanged.emit(index, index)
            self.parent.ctrlResizedColumn()
        return True

    def flags(self, index):
        if self.arraydata:
            if index.row() <= len(self.arraydata) and index.column() <= len(self.arraydata[0]):
                if index.row() <= (len(self.arraydata) - 1):
                    if self.arraydata[index.row()][index.column()] in ["=", "-", " "]:
                        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
                    else:
                        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        return super(MyPartEditorTableModel, self).flags(index)

    def sort(self, col, order):
        """sort table by given column number col"""
        if col == 2:
            self.layoutAboutToBeChanged.emit()
            try:
                self.arraydata = sorted(self.arraydata, key=lambda list_:
                                            int(list_[2]) if list_[2].isnumeric() else float("inf"))
            except: pass
            if order == Qt.DescendingOrder:
                self.arraydata.reverse()
            self.layoutChanged.emit()


class MyOtherFileTableModel(QAbstractTableModel):

    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = datain
        self.header = headerdata

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if self.arraydata:
            return len(self.arraydata[0])
        else:
            return 0

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.arraydata[index.row()][index.column()]
        if role == Qt.EditRole:
            return value
        elif role == Qt.DisplayRole:
            return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.BackgroundRole and (index.row() % 2 == 1):
            return QColor(255, 255, 255)
        elif role == Qt.BackgroundRole and (index.row() % 2 == 0):
            return QColor(237, 243, 254)
        elif role == Qt.ForegroundRole and (index.column() == 3):
            if value == "aligned":
                return QColor("green")
            elif value == "unaligned":
                return QColor("red")
        elif role == Qt.ToolTipRole:
            return value
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

    def headerData(self, number, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[number]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(number + 1)
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        if col != 0:
            self.layoutAboutToBeChanged.emit()
            self.arraydata = sorted(self.arraydata, key=operator.itemgetter(col))
            if order == Qt.DescendingOrder:
                self.arraydata.reverse()
            self.layoutChanged.emit()
            # # else:
            #     self.layoutAboutToBeChanged.emit()
            #     for num, i in enumerate(self.arraydata):
            #         self.arraydata[num][0] = i[0].text()
            #     self.arraydata = sorted(self.arraydata, key=operator.itemgetter(col))
            #     if order == Qt.DescendingOrder:
            #         self.arraydata.reverse()
            #     self.addCheckbox()
            #     self.layoutChanged.emit()

    # def setData(self, index, value, role):
    #     if not index.isValid():
    #         return False
    #     if role == Qt.CheckStateRole and index.column() == 0:
    #         if value == Qt.Checked:
    #             self.arraydata[index.row()][index.column()].setChecked(True)
    #             # 必须要操作list_checked，不然会有各种问题
    #             self.list_checked.append(self.arraydata[index.row()][index.column()].text())
    #         else:
    #             self.arraydata[index.row()][index.column()].setChecked(False)
    #             self.list_checked.remove(self.arraydata[index.row()][index.column()].text())
    #         self.dataChanged.emit(index, index)
    #     return True

    def flags(self, index):
        # if not index.isValid():
        #     return None
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

class MyColorsetsTableModel(QAbstractTableModel):

    def __init__(self, datain, headerdata, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = datain
        self.header = headerdata
        self.parent = parent
        self.parent.horizontalHeader().setVisible(False)
        self.parent.doubleClicked.connect(self.handle_itemclicked)
        self.parent.verticalHeader().sectionDoubleClicked.connect(self.changeHorizontalHeader)

    def changeHorizontalHeader(self, index):
        oldHeader = self.headerData(index, Qt.Vertical, role=Qt.DisplayRole)
        newHeader, ok = QInputDialog.getText(self.parent,
            'Change header label for row %d' % index,
            'Header:',
            QLineEdit.Normal,
            oldHeader)
        if ok and (newHeader != oldHeader):
            if newHeader in self.header:
                QMessageBox.information(
                    self.parent,
                    "Color editor",
                    "<p style='line-height:25px; height:25px'>The name exists, please set a new name! </p>")
                return
            self.header[index] = newHeader
            self.setHeaderData(index, Qt.Vertical, newHeader, role=Qt.EditRole)

    def handle_itemclicked(self, index):
        tableview = self.sender()
        model = tableview.model()
        text = index.data(Qt.DisplayRole)
        text = text if text else "#ffffff"
        color = QColorDialog.getColor(QColor(text), self.parent)
        if color.isValid():
            model.setData(index, color.name(), Qt.BackgroundRole)

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.arraydata[index.row()][index.column()]
        if role in [Qt.EditRole, Qt.DisplayRole]:
            return value
        elif role == Qt.BackgroundRole:
            if value:
                return QColor(value)
        elif role == Qt.ToolTipRole:
            return value
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return None

    def headerData(self, number, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(number + 1)
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self.header[number]
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role in [Qt.EditRole, Qt.DisplayRole, Qt.BackgroundRole]:
            self.arraydata[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class MySeqTable(QAbstractTableModel):

    def __init__(self, array, font, dict_foreColor, dict_backColor, parent=None):
        """
        Args:
            datain: a list of lists\n
            headerdata: a list of strings
            [
            ['A', 'T', 'G', 'A', 'T', 'A', 'A', 'T'],
            ['A', 'T', 'G', 'A', 'T', 'A', 'A', 'T'],
            ['A', 'T', 'G', 'A', 'T', 'A', 'A', 'T']
            ]
        """
        QAbstractTableModel.__init__(self, parent)
        self.arraydata = array
        self.font = font
        self.dict_foreColor = dict_foreColor
        self.dict_backColor = dict_backColor
        self.makeColHeader()
        self.complementArray()

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if len(self.arraydata) > 0:
            return len(self.arraydata[0])
        else:
            return 0

    def data(self, index, role):
        try:
            indexText = self.arraydata[index.row()][index.column()]
        except IndexError:
            ##有时候有index错误就略过
            return
        if not index.isValid():
            return
        if role == Qt.TextAlignmentRole:
            if index.column() == 0:
                return Qt.AlignLeft
            return Qt.AlignCenter
        elif role == Qt.BackgroundRole:
            if index.column() != 0:  # 行头
                if indexText in self.dict_backColor:
                    return QColor(self.dict_backColor[indexText])
                else:
                    return QColor(self.dict_backColor["..."])
            else:
                return QColor("white")
        elif role == Qt.ForegroundRole:
            if index.column() != 0:
                if indexText in self.dict_foreColor:
                    return QColor(self.dict_foreColor[indexText])
                else:
                    return QColor(self.dict_foreColor["..."])
            else:
                return QColor("black")
        elif role == Qt.FontRole:
            # if index.column() == 0:
            #     return QFont("Courier New", 12)
            return self.font
        # 这一项必须放在最后，不然其他项不生效
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return
        return (indexText)

    def setData(self, index, value, role):
        oldValue = self.arraydata[index.row()][index.column()]
        if value != oldValue:
            if role == Qt.EditRole:
                self.textAfterEdit = value
                self.dataChanged.emit(index, index)
        return True

    def headerData(self, number, orientation, role):
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(number + 1)
        if orientation == Qt.Horizontal:
            if len(self.colHeaderdata) < number + 1:
                return
            if role == Qt.DisplayRole:
                return self.colHeaderdata[number]
            if role == Qt.TextAlignmentRole and number == 0:
                return Qt.AlignLeft
        if role == Qt.FontRole:
            return QFont("Courier New", 13)

    def sort(self, Ncol, order):
        """
        Sort table by given column number.
        """
        if Ncol == 0:
            self.layoutAboutToBeChanged.emit()
            # self.emit(SIGNAL("layoutAboutToBeChanged()"))
            self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
            if order == Qt.DescendingOrder:
                self.arraydata.reverse()
            # self.emit(SIGNAL("layoutChanged()"))
            self.layoutChanged.emit()

    def flags(self, index):
        # | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable  # | Qt.ItemIsDragEnabled # | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction

    def dropMimeData(self, data, action, row, col, parent):
        """
        Always move the entire row, and don't allow column "shifting"
        """
        return super().dropMimeData(data, action, row, 0, parent)

    def color(self, text):
        if (text.upper() in "-.") or (text == ""):
            # 必须在第一个执行，否则“”不生效
            return QColor("white")
        elif text.upper() in "FLMA":
            return QColor(153, 255, 0)
        elif text.upper() in "WSHTU":
            return QColor("red")
        elif text.upper() == "C":
            return QColor(51, 51, 255)
        elif text.upper() in "IVG":
            return QColor(255, 204, 0)
        elif text.upper() in "P":
            return QColor(60, 179, 113)
        elif text.upper() in "YDN":  # 天蓝色
            return QColor(135, 206, 235)
        elif text.upper() in "EQ":  # 紫色
            return QColor(255, 0, 255)
        elif text.upper() == "R":  # 紫红色
            return QColor(255, 105, 180)
        elif text.upper() == "K":  # 紫红色
            return QColor(0, 255, 255)
        else:
            return QColor("grey")

    def foreGroundColor(self, text):
        if text.upper() in "PEQRC":
            return QColor("white")
        else:
            return QColor("black")

    def makeColHeader(self):
        list_set_array = [set(k) for k in list(zip(*self.arraydata))]
        self.colHeaderdata = ["Taxon Name"]
        for num, j in enumerate(list_set_array):
            if num != 0:  # 第一列是序列名字，所以跳过
                header = "*" if len(j) == 1 else ""
                self.colHeaderdata.append(header)

    def complementArray(self):
        #扫描矩阵，如果有缺行就补上点
        arraydata = self.arraydata if len(self.arraydata) > 1 else self.arraydata + [[]]
        max_col = max(*arraydata, key=lambda x: len(x)-x.count("."))
        max_col_len = len(max_col) - max_col.count(".")
        for num, j in enumerate(self.arraydata):
            j_length = len(j)
            if j_length < max_col_len:
                addition = ["."] * (max_col_len - j_length)
                self.arraydata[num].extend(addition)
            elif j_length > max_col_len:
                self.arraydata[num] = self.arraydata[num][:max_col_len]

    def fetchCleanArray(self):
        newArray = []
        for i in self.arraydata:
            pointNum = 0
            for j in reversed(i):
                if j == ".":
                    pointNum += 1
                else:
                    break
            newArray.append(i[:len(i)-pointNum])
        return newArray

    def fetchDictTaxon(self):
        dict_taxon = OrderedDict()
        newArray = []
        for i in self.arraydata:
            name = i[0]
            seq = "".join(i[1:])
            seq = seq.replace(".", "-")
            dict_taxon[name] = "".join(seq)
        return dict_taxon

class MySeqSettingTable(QAbstractTableModel):

    def __init__(self, dict_foreColor, dict_backColor, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self.dict_foreColor = dict_foreColor
        self.dict_backColor = dict_backColor
        self.arraydata = [['F', 'L', 'M', 'A', 'W', 'S'],
                     ['H', 'T', 'U', 'C', 'I', 'V'],
                     ['G', 'P', 'Y', 'D', 'N', 'E'],
                     ['Q', 'R', 'K', '-', '.', '...']]

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        if len(self.arraydata) > 0:
            return len(self.arraydata[0])
        else:
            return 0

    def data(self, index, role):
        try:
            indexText = self.arraydata[index.row()][index.column()]
        except IndexError:
            ##有时候有index错误就略过
            return
        if not index.isValid():
            return
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.BackgroundRole:
            return QColor(self.dict_backColor[indexText])
        elif role == Qt.ForegroundRole:
            return QColor(self.dict_foreColor[indexText])
        elif role == Qt.FontRole:
            return QFont("Courier New", 30)
        # 这一项必须放在最后，不然其他项不生效
        elif not (role == Qt.DisplayRole or role == Qt.EditRole):
            return
        return (indexText)

    def setData(self, index, value, role):
        indexText = self.arraydata[index.row()][index.column()]
        if self.data(index, role).name() != value: #如果新的颜色与就颜色不一样
            if role == Qt.ForegroundRole:
                self.dict_foreColor[indexText] = value
                self.dataChanged.emit(index, index)
            elif role == Qt.BackgroundRole:
                self.dict_backColor[indexText] = value
                self.dataChanged.emit(index, index)
        return True



# class MyRSCUtable(QAbstractTableModel):
#
#     def __init__(self, datain=None, headerdata=None, parent=None):
#         """
#         Args:
#             datain: a list of lists\n
#             headerdata: a list of strings
#         """
#         QAbstractTableModel.__init__(self, parent)
#         self.arraydata = datain
#         self.headerdata = headerdata
#
#     def rowCount(self, parent):
#         return len(self.arraydata)
#
#     def columnCount(self, parent):
#         if len(self.arraydata) > 0:
#             return len(self.arraydata[0])
#         else:
#             return 0
#
#     def data(self, index, role):
#         if not index.isValid():
#             return None
#         if role == Qt.TextAlignmentRole:
#             return Qt.AlignCenter
#         # elif role != Qt.DisplayRole:
#         # if role == Qt.DisplayRole or role == Qt.EditRole:
#         elif role == Qt.BackgroundRole and (index.row() % 2 == 1):
#             return QColor(255, 255, 255)
#         elif role == Qt.BackgroundRole and (index.row() % 2 == 0):
#             return QColor(237, 243, 254)
#         elif role == Qt.ToolTipRole:
#             return self.arraydata[index.row()][index.column()]
#         # 这一项必须放在最后，不然其他项不生效
#         elif not (role == Qt.DisplayRole or role == Qt.EditRole):
#             return None
#         return (self.arraydata[index.row()][index.column()])
#
#     def setData(self, index, value, role):
#         self.arraydata[index.row()][index.column()] = value
#         self.dataChanged.emit(index, index)
#         return True
#
#     def headerData(self, number, orientation, role):
#         # 行表头
#         if orientation == Qt.Horizontal and role == Qt.DisplayRole:
#             return self.headerdata[number]
#         if role == Qt.TextAlignmentRole:
#             return Qt.AlignLeft
#
#     def sort(self, Ncol, order):
#         """
#         Sort table by given column number.
#         """
#         self.layoutAboutToBeChanged.emit()
#         # self.emit(SIGNAL("layoutAboutToBeChanged()"))
#         self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))
#         if order == Qt.DescendingOrder:
#             self.arraydata.reverse()
#         # self.emit(SIGNAL("layoutChanged()"))
#         self.layoutChanged.emit()
#
#     def flags(self, index):
#         baseflags = QAbstractTableModel.flags(self, index)
#         if index.column() == 0:
#             return baseflags | Qt.ItemIsEditable
#         else:
#             return baseflags
#             # | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
#         return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled # | Qt.ItemIsDropEnabled
#
#     def supportedDropActions(self):
#         return Qt.MoveAction
#
#     def dropMimeData(self, data, action, row, col, parent):
#         """
#         Always move the entire row, and don't allow column "shifting"
#         """
#         return super().dropMimeData(data, action, row, 0, parent)


class TreeModel(QAbstractItemModel):

    def __init__(self, data, parent=None):
        super(TreeModel, self).__init__(parent)
        self.parents = []
        self.dbdata = data
        self.rootItem = TreeItem([u""])
        self.setupModelData(self.dbdata, self.rootItem)

    def setData(self, index, value, role):
        if index.isValid() and role == Qt.EditRole:

            prev_value = self.getValue(index)

            item = index.internalPointer()

            item.setData(value)

            return True
        else:
            return False

    def removeRows(self, position=0, count=1, parent=QModelIndex()):
        node = self.nodeFromIndex(parent)
        self.beginRemoveRows(parent, position, position + count - 1)
        node.childItems.pop(position)
        self.endRemoveRows()

    def nodeFromIndex(self, index):
        if index.isValid():
            return index.internalPointer()
        else:
            return self.rootItem

    def getValue(self, index):
        item = index.internalPointer()
        return item.data(index.column())

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None
        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()
        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)[0]

        return None

    def index(self, row, column, parent):
        if row < 0 or column < 0 or row >= self.rowCount(
                parent) or column >= self.columnCount(parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def setupModelData(self, lines, parent):
        ind = []
        self.parents.append(parent)
        ind.append(0)
        col_numb = parent.columnCount()
        numb = 0

        for line in lines:
            numb += 1
            lineData = line[0]
            self.parents[-1].appendChild(TreeItem(lineData, self.parents[-1]))

            columnData = line[1]

            self.parents.append(
                self.parents[-1].child(self.parents[-1].childCount() - 1))

            for j in columnData:
                self.parents[-1].appendChild(TreeItem(j, self.parents[-1]))
            if len(self.parents) > 0:
                self.parents.pop()

class TreeItem(object):

    def __init__(self, data, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        try:
            return self.itemData

        except IndexError:
            return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

    def setData(self, data):
        self.itemData = data

class MyComboBox(QComboBox):
    def __init__(self, *args):
        super().__init__(*args)

    def wheelEvent(self, e):
        e.ignore()

class ComLineEdit(QLineEdit):
    clicked = pyqtSignal()

    def __init__(self, *args):
        super(ComLineEdit, self).__init__(*args)
        self.setReadOnly(True)

    def mouseReleaseEvent(self, e):
        self.clicked.emit()


class CheckableComboBox(QComboBox):
    def __init__(self, *args):
        super(CheckableComboBox, self).__init__(*args)
        LE = ComLineEdit(self)
        LE.clicked.connect(self.showPopup)
        self.activated.connect(self.setTopText)
        self.setLineEdit(LE)
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QStandardItemModel(self))
        self.sep = ", "

    def handleItemPressed(self, index):
        self.item = self.model().itemFromIndex(index)
        if self.item.checkState() == Qt.Checked:
            self.item.setCheckState(Qt.Unchecked)
        else:
            self.item.setCheckState(Qt.Checked)
        self.setTopText()

    def setTopText(self):
        selectedLNG = [self.itemText(i) for i in range(self.count())
                        if self.model().item(i).checkState() == Qt.Checked]
        self.topText = self.sep.join(selectedLNG) if selectedLNG else "N/A"
        self.lineEdit().setText(self.topText)
        self.lineEdit().setToolTip(self.topText)
        self.lineEdit().home(False)


class SingeleWidget(QWidget):
    '''
    菜单条的每个框。
    '''
    clicked = pyqtSignal()
    # 1
    def __init__(self, parent=None):
        '''
        _hideFlag__Button：  0 表明没有显示弹窗；1表示显示了弹窗。
        '''
        super(SingeleWidget, self).__init__(parent)

        self._hideFlag__Button = 0
        self.DropDownMenu = QWidget()
        self.setProperty("WID", "isTrue")
        self.setAttribute(Qt.WA_StyledBackground, True)
        #print("W实例化")

    #        self.setMaximumWidth(80)
    def _creatMenu(self, parent):
        '''
        Main.py中被调用。把LX类实例化。
        '''
        # self.DropDownMenu = L1(parent)
        self.DropDownMenu = MenuTable(parent)

    def enterEvent(self, e):
        '''鼠标移入label后 ， _hideFlag__Button=1，表明显示了弹窗。'''
        # 设置菜单窗体的宽度
        # self.DropDownMenu.setMinimumWidth(self.width())
        # self.DropDownMenu.setMaximumWidth(self.width())
        # 由于布局的leftMargin是9，所以要减去9
        a0 = self.mapToGlobal(QPoint(self.parent().x()-9, self.height()))

        self.DropDownMenu.move(a0)
        # self.DropDownMenu.move(QPoint(QPoint(471, 207)))

        # 设置table外容器的宽度
        if hasattr(self.DropDownMenu, "tableWidget") and self.DropDownMenu.tableWidget.rowCount() != 0:
            table = self.DropDownMenu.tableWidget
            font_ = table.font()
            height_ = QFontMetrics(QFont(font_.family(), font_.pointSize())).height()
            height = table.rowCount() * (height_ + 15)
            table.parent().setMinimumHeight(height)
            table.parent().setMaximumHeight(height)
            table.resizeColumnsToContents()
            self.DropDownMenu.show()

        # 表明显示了弹窗
        self._hideFlag__Button = 1

    def leaveEvent(self, e):
        '''
        离开时判断是否显示了窗体，80ms后发射到_jugement去检测。
        '''
        if self._hideFlag__Button == 1:  # 显示了窗体
            QTimer.singleShot(80, self._jugement)

    def focusOutEvent(self, e):
        if self._hideFlag__Button == 1:  # 显示了窗体
            QTimer.singleShot(80, self._jugement)

    def _jugement(self):
        '''
        离开上面窗体之后80ms, 1：进入旁边的菜单框；2：进入弹出的菜单。
        '''
        if hasattr(self.DropDownMenu, "_hideFlag__Menu") and self.DropDownMenu._hideFlag__Menu != 1:
            self.DropDownMenu.hide()
            self.DropDownMenu.close()
            self._hideFlag__Button = 0
        else:
            pass

    def mousePressEvent(self, e):
        self.clicked.emit()
        # super(SingeleWidget, self).mousePressEvent(self, e)  # 0

# ========================================================
class BaseMenuWidget(QWidget):
    # 2
    '''
    下拉菜单的基类。 被LX继承，父类在18L 实现。
    '''

    def __init__(self, parent=None):
        '''
        _hideFlag__Menu: 0时隐藏，1时显示；
        '''

        super(BaseMenuWidget, self).__init__(parent)
        # #无边框，隐藏任务栏；
        # self.setWindowFlags( Qt.FramelessWindowHint|Qt.Tool|Qt.Widget)
        # self.setupUi(self)
        self._hideFlag__Menu = 0
        #print("L实例化")

    def enterEvent(self, e):
        # 表明进入了弹窗
        self._hideFlag__Menu = 1

    def leaveEvent(self, e):
        self._hideFlag__Menu = 0
        self.hide()
        for i in self.children():
            if isinstance(i, BaseTable):  # 判断对象是否是tablewiget, 是则隐藏选中item颜色
                i.clearSelection()

    def _showSomething(self, **kwgs):
        MW = self.parent()

        if MW.objectName() == "MainWindow":

            try:
                #                    MW.Buttom_Vbox.setParent(None)#这是个严重的问题，如果用这个函数会造成78L无法成功
                _parent = MW.Buttom_Vbox.parent()  # 获取下面窗体对象的指针
                for obj in _parent.children():
                    #print(obj)
                    sip.delete(obj)

                MW.Buttom_Vbox = QVBoxLayout(_parent)
                MW.Buttom_Vbox.setContentsMargins(0, 0, 0, 0)
                MW.Buttom_Vbox.setSpacing(0)
                MW.Buttom_Vbox.setObjectName("Buttom_Vbox")

            except:
                showERROR()

    def _deleteSomething(self):
        pass


# ====================================================
class BaseButton(QPushButton):
    # 1
    '''
    主菜单的按钮的样式。
    '''

    def __init__(self, parent=None):
        super(BaseButton, self).__init__(parent)

        self.setFixedWidth(40)
        self.setFixedWidth(40)
        # self.setMaximumWidth(80)
        # self.setMinimumHeight(self.width())  # 保证是个正方形
        self.setFocusPolicy(Qt.NoFocus)  # 无焦点，防止背景卡色
        self.setFlat(True)  # 无凸起阴影

        self.clicked.connect(self._todo)

        # self.png = QLabel(self)
        # self.png.resize(self.size())
        # self.png.setScaledContents(True)
        #print("B实例化")

    def _todo(self, *args, **kwgs):
        '''
        每个按钮要重新实现的功能函数。
        '''
        pass

    def _createLabel(self, path):
        '''
        path：主菜单图标的路径。
        '''
        # self.png.resize(self.size())
        # self.png_pixmap = QPixmap(path)
        # self.png.setPixmap(self.png_pixmap)
        self.png.setScaledContents(True)
        pass

    def resizeEvent(self, e):
        self.setMinimumHeight(self.width())
        # self.png.resize(self.size())


# ==================================================
class BaseTable(QTableWidget):
    # 3
    '''
    下拉菜单中Table的样式。
    '''

    def __init__(self, parent=None):
        super(BaseTable, self).__init__(parent)

        self.horizontalHeader().setSectionResizeMode(3)  # 列宽设置
        self.horizontalHeader().setStretchLastSection(True);  # 充满列宽
        self.verticalHeader().setSectionResizeMode(1)  # 行高设置
        self.verticalHeader().setStretchLastSection(True);  # 充满行高
        self.setEditTriggers(QAbstractItemView.NoEditTriggers);  # 只读
        # self.resizeColumnsToContents()
        self.setTextElideMode(Qt.ElideMiddle)
        # 关闭滑动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        #print("T实例化")


class MenuTable(QDialog, BaseMenuWidget):
    def __init__(self, parent=None):
        super(MenuTable, self).__init__(parent)
        # self.resize(113, 119)
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.tableWidget = BaseTable(self)
        self.tableWidget.setColumnCount(1)
        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setHighlightSections(True)
        # 自动根据文本大小调整
        self.tableWidget.setSizeAdjustPolicy(
                        QAbstractScrollArea.AdjustToContents)
        self.verticalLayout.addWidget(self.tableWidget)
        # 无边框，隐藏任务栏；
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.Widget)

    def addMenuItem(self, iconPath="", text="New Item"):
        # 先获得当前有多少行，再添加
        rows = self.tableWidget.rowCount()
        item = QTableWidgetItem()
        item.setText(text)
        icon = QIcon(iconPath)
        item.setIcon(icon)
        self.tableWidget.insertRow(rows)
        self.tableWidget.setItem(rows, 0, item)
        # self.tableWidget.resizeColumnsToContents()

class ComboBoxWidget(QWidget):
    itemOpSignal = pyqtSignal(QListWidgetItem)
    viewAlnSigal = pyqtSignal(QListWidgetItem)

    def __init__(self, text, listwidgetItem, parent=None, is_cat=False):
        super(ComboBoxWidget, self).__init__(parent)
        self.text = text
        self.is_cat = is_cat
        self.listwidgetItem = listwidgetItem
        self.initUi()

    def initUi(self):
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.file_label = QLabel(self.text, self)
#         qss = '''QPushButton
# {
#     background-color: transparent;
#     border: none;
#     border-left: 1px solid #B9B9B9;
#     border-radius: 0px;
# }
#
# QPushButton:hover {
#     background:transparent;
#     }'''
#         self.file_label.setStyleSheet(qss)
        self.bt_close = QToolButton(self)
        if platform.system().lower() == "darwin":
            self.bt_close.setStyleSheet("QToolButton {background: transparent;}")
        self.bt_close.setIcon(QIcon(":/picture/resourses/if_Delete_1493279.png"))
        self.bt_close.setAutoRaise(True)
        self.bt_close.setCursor(Qt.PointingHandCursor)
        self.bt_close.setToolTip("Delete")
        self.bt_close.clicked.connect(lambda: self.itemOpSignal.emit(self.listwidgetItem))
        self.bt_view = QToolButton(self)
        if platform.system().lower() == "darwin":
            self.bt_view.setStyleSheet("QToolButton {background: transparent;}")
        self.bt_view.setIcon(QIcon(":/picture/resourses/file.png"))
        self.bt_view.setAutoRaise(True)
        self.bt_view.setCursor(Qt.PointingHandCursor)
        self.bt_view.setToolTip("View")
        self.bt_view.clicked.connect(lambda: self.viewAlnSigal.emit(self.listwidgetItem))
        if self.is_cat:
            self.PCGs = QCheckBox("PCG  ", self)
        self.horizontalLayout.addWidget(self.bt_close)
        self.horizontalLayout.addWidget(self.bt_view)
        if self.is_cat:
            self.horizontalLayout.addWidget(self.PCGs)
        self.horizontalLayout.addWidget(self.file_label)
        self.horizontalLayout.addStretch()


class QcomboLineEdit(QLineEdit):
    clicked = pyqtSignal()
    autoDetectSig = pyqtSignal()

    def __init__(self, *args):
        super(QcomboLineEdit, self).__init__(*args)
        self.DisplayNoChange = False
        self.setReadOnly(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.buttonFile = QToolButton(self)
        self.buttonFile.setAutoRaise(True)
        self.buttonFile.setToolTip("View")
        self.buttonFile.setCursor(Qt.PointingHandCursor)
        self.buttonFile.setFocusPolicy(Qt.NoFocus)
        self.buttonFile.setIcon(QIcon(":/picture/resourses/file.png"))
        self.buttonFile.setStyleSheet("QToolButton {border: none;}")
        self.deleteFile = QToolButton(self)
        self.deleteFile.setAutoRaise(True)
        self.deleteFile.setToolTip("Delete")
        self.deleteFile.setCursor(Qt.PointingHandCursor)
        self.deleteFile.setFocusPolicy(Qt.NoFocus)
        self.deleteFile.setIcon(QIcon(":/picture/resourses/if_Delete_1493279.png"))
        self.deleteFile.setStyleSheet("QToolButton {border: none;}")
        layout = QHBoxLayout(self)
        layout.addWidget(self.buttonFile, 0, Qt.AlignLeft)
        layout.addStretch()
        layout.addWidget(self.deleteFile, 0, Qt.AlignRight)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        leftbuttonwidth = self.buttonFile.sizeHint().width()
        rightButtonWidth = self.deleteFile.sizeHint().width()
        self.setTextMargins(leftbuttonwidth + frameWidth - 2, 0, rightButtonWidth + frameWidth - 2, 0)
        self.textChanged.connect(self.switchColor)

    def mousePressEvent(self, e):
        if self.text() == "Click to auto detect from workplace":
            self.autoDetectSig.emit()
        return super(QcomboLineEdit, self).mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self.clicked.emit()

    def setText(self, text):
        if text in ["No input files (Try to drag your file(s) and drop here)",
                    "Optional!",
                    "No input MSA (Improves previously computed alignments)"]:
            # self.setStyleSheet('QLineEdit {color: red; border: none;}')
            # palette = QPalette()
            # palette.setColor(QPalette.Text, Qt.red)
            # self.setPalette(palette)
            self.buttonFile.setIcon(QIcon(":/picture/resourses/nofile.png"))
        else:
            # palette = QPalette()
            # palette.setColor(QPalette.Text, Qt.black)
            # self.setPalette(palette)
            # self.setStyleSheet('QLineEdit {color: black; border: none;}')
            self.buttonFile.setIcon(QIcon(":/picture/resourses/file.png"))
        return super(QcomboLineEdit, self).setText(text)

    def setLineEditNoChange(self, bool):
        self.DisplayNoChange = bool

    def enterEvent(self, *args, **kwargs):
        if self.DisplayNoChange:
            return
        if self.text() == "No input files (Try to drag your file(s) and drop here)":
            # self.setStyleSheet("QLineEdit {background-color: rgb(160, 212, 236); border: none;}");
            self.setText("Click to auto detect from workplace")
            self.buttonFile.setIcon(QIcon(":/picture/resourses/detect.png"))

    def leaveEvent(self, *args, **kwargs):
        if self.DisplayNoChange:
            return
        if (self.text() == "No input files (Try to drag your file(s) and drop here)") or (self.text() == "Click to auto detect from workplace"):
            self.setText("No input files (Try to drag your file(s) and drop here)")
            # self.setStyleSheet("QLineEdit {background-color: white; border: none;}")

    def switchColor(self, text=""):
        if not self.isEnabled():
            #workflow的模式
            self.setStyleSheet('QLineEdit {font-weight: 600; color: gray; border: none;}')
            return
        if text in ["No input files (Try to drag your file(s) and drop here)",
                    "No input MSA (Improves previously computed alignments)"]:
            self.setStyleSheet('QLineEdit {font-weight: 600; color: red; border: none;}')
        elif text == "Click to auto detect from workplace":
            self.setStyleSheet("QLineEdit {background-color: rgb(160, 212, 236); border: none;}")
        elif text in ["Optional!"]:
            self.setStyleSheet("QLineEdit {color: black; border: none;}")
        else:
            self.setStyleSheet('QLineEdit {font-weight: 600; color: green; border: none;}')


class ListQCombobox(QComboBox):
    itemRemovedSig = pyqtSignal()

    def __init__(self, *args):
        super(ListQCombobox, self).__init__(*args)
        self.listw = QListWidget()
        # self.listw.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setModel(self.listw.model())
        self.setView(self.listw)
        self.activated.connect(self.setTopText)
        self.isPopup = False
        self.concatenate = False
        LE = QcomboLineEdit(self)
        LE.clicked.connect(self.switchPopup)
        LE.deleteFile.clicked.connect(lambda : self.removeCombo(self.view().item(0)))
        LE.buttonFile.clicked.connect(lambda : self.viewFile(self.view().item(0)))
        self.setLineEdit(LE)
        qss = '''QComboBox QAbstractItemView::item {
                    height: 25px;
                }

                QListView::item:hover {
                    background: #BDD7FD;
                }'''
        self.setStyleSheet(qss)
        self.installEventFilter(self)
        self.refreshIsCalling = False

    def switchPopup(self):
        if self.isPopup:
            self.hidePopup()
        else:
            self.showPopup()

    def user_select(self):
        # mainwindow_settings = QSettings(
        #     self.thisPath +
        #     '/settings/mainwindow_settings.ini',
        #     QSettings.IniFormat, parent=self)
        # mainwindow_settings.setFallbacksEnabled(False)
        # isAppend = mainwindow_settings.value(
        #     "append2old", "true")
        windInfo = Inputbox_message(":/picture/resourses/msg_info.png", parent=self)
        windInfo.appendOld.setChecked(True)
        # from factory import Factory
        # self.factory = Factory()
        # if self.factory.str2bool(isAppend):
        #     windInfo.appendOld.setChecked(True)
        # else:
        #     windInfo.clearOld.setChecked(True)
        # windInfo.appendOld.toggled.connect(
        #     lambda bool_: mainwindow_settings.setValue("append2old", bool_))
        if windInfo.exec_() == QDialog.Accepted:
            if windInfo.appendOld.isChecked():
                return "append"
            else:
                return "clear"
        else:
            return "cancel"

    def refreshInputs(self, list_inputs, sort=True, judge=True):
        '''判断是否删掉以前的再输入'''
        list_inputs = [os.path.normpath(i) for i in list_inputs] #标准化路径
        if judge:
            #判断是否已存在文件
            exist_files = self.fetchListsText()
            if exist_files and list_inputs:
                user_opt = self.user_select()
                if user_opt == "clear":
                    self.clear()
                elif user_opt == "append":
                    pass
                elif user_opt == "cancel":
                    return
        else:
            # 如果只需要输入新序列
            self.clear()
        def sort_def(file_name):
            base = os.path.basename(file_name).split(".")[0]
            if re.search(r"^\d+", base): return int(re.search(r"^\d+", base).group())
            elif re.search(r"\d+$", base): return int(re.search(r"\d+$", base).group())
            else: return base
        try:
            paths = sorted(list_inputs, key=lambda x: (isinstance(sort_def(x), str), sort_def(x))) if sort else list_inputs
            # sort数字与字母混合情况参考：https://stackoverflow.com/questions/53246253/python-list-sort-integers-and-then-strings
        except:
            paths = list_inputs
        path_num = len(paths)
        ##进度条
        if path_num > 70:
            from src.factory import Factory
            self.factory = Factory()
            self.progressDialog = self.factory.myProgressDialog(
                "Please Wait", "Importing...", parent=self)
            self.progressDialog.show()
        for num, path in enumerate(paths):
            if (not os.path.exists(path)) or (path in self.fetchListsText()):
                # 如果路径不存在，就跳过这个循环
               continue
            listwitem = QListWidgetItem(self.listw)
            listwitem.setToolTip(path)
            itemWidget = ComboBoxWidget(os.path.basename(path), listwitem, self,
                                        is_cat=self.concatenate)
            itemWidget.itemOpSignal.connect(self.removeCombo)
            itemWidget.viewAlnSigal.connect(self.viewFile)
            # 背景颜色
            if num % 2 == 0:
                listwitem.setBackground(QColor(255, 255, 255))
            else:
                listwitem.setBackground(QColor(237, 243, 254))
            listwitem.setSizeHint(itemWidget.sizeHint())
            self.listw.addItem(listwitem)
            self.listw.setItemWidget(listwitem, itemWidget)
            if path_num > 70:
                self.runProgressDialog(100*(num/len(paths)))
        if path_num > 70:
            self.progressDialog.close()
        self.setTopText()

    def setTopText(self):
        list_text = self.fetchListsText()
        list_names = self.fetchListNames()
        self.lineEdit().deleteFile.setVisible(False)
        if len(list_text) > 1:
            topText = "%d files: %s"%(len(list_text), ", ".join(list_names))
        elif len(list_text) == 1:
            self.lineEdit().deleteFile.setVisible(True)
            topText = os.path.basename(list_text[0])
        else:
            topText = "No input files (Try to drag your file(s) and drop here)"
        self.lineEdit().setText(topText)
        self.lineEdit().home(False)

    def refreshBackColors(self):
        for row in range(self.view().count()):
            if row % 2 == 0:
                self.view().item(row).setBackground(QColor(255, 255, 255))
            else:
                self.view().item(row).setBackground(QColor(237, 243, 254))

    def removeCombo(self, listwidgetItem):
        view = self.view()
        index = view.indexFromItem(listwidgetItem)
        view.takeItem(index.row())
        self.refreshBackColors()
        self.setTopText()
        self.itemRemovedSig.emit()

    # def removeLastCombo(self):
    #     view = self.view()
    #     view.takeItem(0)
    #     self.refreshBackColors()
    #     self.setTopText()

    def fetchListsText(self):
        return [self.view().item(row).toolTip() for row in range(self.view().count())]

    def fetchListNames(self):
        return [self.view().itemWidget(self.view().item(row)).text for row in range(self.view().count())]

    def switch_PCGs(self, bool_):
        [self.view().itemWidget(self.view().item(row)).PCGs.setChecked(bool_) for row in range(self.view().count())]

    def fetchPCGs(self):
        return {os.path.splitext(os.path.basename(self.view().item(row).toolTip()))[0]:
                    self.view().itemWidget(self.view().item(row)).PCGs.isChecked()
                for row in range(self.view().count())}

    def fetchCurrentText(self):
        if self.view().count():
            return self.view().item(0).toolTip()
        else:
            return ""

    def count(self):
        return self.view().count()

    def viewFile(self, listwidgetItem):
        from src.factory import Factory
        self.factory = Factory()
        if not listwidgetItem:
            return
        file = listwidgetItem.toolTip()
        if not file:
            return
        docxMode = True if os.path.splitext(file)[1].upper() in [".DOCX", ".DOC", ".ODT", ".DOCM", ".DOTX", ".DOTM", ".DOT", ".SBT"] else False
        if docxMode:
            self.factory.openPath(file, self)
        else:
            from src.Lg_seqViewer import Seq_viewer  #避免交叉引用放到了这里
            if hasattr(self, "seqViewer") and self.seqViewer.isVisible():
                self.seqViewer.addFiles([file])
                self.seqViewer.show()
            else:
                self.seqViewer = Seq_viewer(os.path.dirname(file), [file], parent=self)
                # 添加最大化按钮
                self.seqViewer.setWindowFlags(self.seqViewer.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.seqViewer.setWindowModality(Qt.ApplicationModal)
                self.seqViewer.show()

    def showPopup(self):
        self.isPopup = True
        return super(ListQCombobox, self).showPopup()

    def hidePopup(self):
        self.isPopup = False
        return super(ListQCombobox, self).hidePopup()

    def runProgressDialog(self, num):
        oldValue = self.progressDialog.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressDialog.setProperty("value", done_int)
            QCoreApplication.processEvents()
            if done_int == 100:
                self.progressDialog.close()

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        if event.type() == QEvent.MouseButtonRelease:
            if isinstance(obj, QLineEdit):
                event.accept()
                super(ListQCombobox, self).showPopup()
            if (obj != self.view()) and (obj!=self.view().window()):
                event.accept()
                super(ListQCombobox, self).hidePopup()
        return super(ListQCombobox, self).eventFilter(obj, event)

class InputQLineEdit(QLineEdit):
    autoDetectSig = pyqtSignal()

    def __init__(self, *args):
        super(InputQLineEdit, self).__init__(*args)
        self.DisplayNoChange = False
        self.setReadOnly(True)
        self.buttonFile = QToolButton(self)
        self.buttonFile.setAutoRaise(True)
        self.buttonFile.setToolTip("View")
        self.buttonFile.setCursor(Qt.PointingHandCursor)
        self.buttonFile.setFocusPolicy(Qt.NoFocus)
        self.buttonFile.setIcon(QIcon(":/picture/resourses/file.png"))
        self.buttonFile.setStyleSheet("QToolButton {border: none;}")
        self.buttonFile.clicked.connect(self.viewFileContent)
        self.deleteFile = QToolButton(self)
        self.deleteFile.setAutoRaise(True)
        self.deleteFile.setToolTip("Delete")
        self.deleteFile.setCursor(Qt.PointingHandCursor)
        self.deleteFile.setFocusPolicy(Qt.NoFocus)
        self.deleteFile.setIcon(QIcon(":/picture/resourses/if_Delete_1493279.png"))
        self.deleteFile.setStyleSheet("QToolButton {border: none;}")
        layout = QHBoxLayout(self)
        layout.addWidget(self.buttonFile, 0, Qt.AlignLeft)
        layout.addStretch()
        layout.addWidget(self.deleteFile, 0, Qt.AlignRight)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        leftbuttonwidth = self.buttonFile.sizeHint().width()
        rightButtonWidth = self.deleteFile.sizeHint().width()
        self.setTextMargins(leftbuttonwidth + frameWidth - 2, 0, rightButtonWidth + frameWidth - 2, 0) ##这里设置一下距离
        ##初始化一下
        self.setText(self.text())
        ##清除focus
        self.setFocusPolicy(0)
        # self.textChanged.connect(self.switchColor)

    def mousePressEvent(self, e):
        if self.text() == "Click to auto detect from workplace":
            self.autoDetectSig.emit()
        return super(InputQLineEdit, self).mousePressEvent(e)

    def enterEvent(self, *args, **kwargs):
        if self.DisplayNoChange:
            return
        if (self.text() == "No input file") or (self.text() == ""):
            self.setStyleSheet("QLineEdit {background-color: rgb(160, 212, 236);}")
            self.setText("Click to auto detect from workplace")
            self.buttonFile.setIcon(QIcon(":/picture/resourses/detect.png"))

    def leaveEvent(self, *args, **kwargs):
        if self.DisplayNoChange:
            return
        if (self.text() == "No input file") or (self.text() == "Click to auto detect from workplace") or (self.text() == ""):
            self.setText("")
        self.setStyleSheet("QLineEdit {background-color: white;}")

    def setLineEditNoChange(self, bool):
        self.DisplayNoChange = bool

    def setText(self, text):
        if (text == "No input file") or (text == "") or (text == "Click to auto detect from workplace"):
            self.buttonFile.setIcon(QIcon(":/picture/resourses/nofile.png"))
            self.deleteFile.setEnabled(False)
        else:
            self.buttonFile.setIcon(QIcon(":/picture/resourses/file.png"))
            self.deleteFile.setEnabled(True)
        return super(InputQLineEdit, self).setText(text)

    def viewFileContent(self):
        from src.factory import Factory
        self.factory = Factory()
        file = self.toolTip()
        if not file:
            return
        unAlignmentMode = True if os.path.splitext(file)[1].upper() not in\
                                  [".FAS", ".FASTA", ".PHY", ".PHYLIP", ".NEX", ".NXS", ".NEXUS"] else False
        unAlignmentMode = True if (os.path.basename(file) in ["IQ_partition.nex"]) \
                                  or file.endswith("best_scheme.nex") else unAlignmentMode
        if unAlignmentMode:
            self.factory.openPath(file, self)
        else:
            from src.Lg_seqViewer import Seq_viewer  #避免交叉引用放到了这里
            if hasattr(self, "seqViewer") and self.seqViewer.isVisible():
                self.seqViewer.addFiles([file])
                self.seqViewer.show()
            else:
                self.seqViewer = Seq_viewer(os.path.dirname(file), [file], parent=self)
                # 添加最大化按钮
                self.seqViewer.setWindowFlags(self.seqViewer.windowFlags() | Qt.WindowMinMaxButtonsHint)
                self.seqViewer.setWindowModality(Qt.ApplicationModal)
                self.seqViewer.show()

    def switchColor(self, text):
        ##暂时作废
        if text == "No input files (Try to drag your file(s) and drop here)":
            self.setStyleSheet('QLineEdit {font-weight: 600; color: red;}')
        elif text == "Click to auto detect from workplace":
            self.setStyleSheet("QLineEdit {background-color: rgb(160, 212, 236);}")
        else:
            self.setStyleSheet('QLineEdit {font-weight: 600; color: green; }')


class DetectItemWidget(QWidget):

    def __init__(self, pathText, rootPath, parent=None, dict_subRsults=None):
        super(DetectItemWidget, self).__init__(parent)
        self.pathText = pathText
        self.rootPath = rootPath
        self.dict_subRsults = dict_subRsults
        self.initUi()

    def initUi(self):
        from src.factory import Factory
        self.factory = Factory()
        self.resize(400, 86)
        self.verticalLayout = QVBoxLayout(self)
        self.gridLayout = QGridLayout()
        labelText = ".." + os.path.normpath(self.pathText).replace(os.path.normpath(self.rootPath), "")
        self.label_2 = QLabel("Work Dir: %s"%os.path.dirname(labelText), self)
        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)
        name = os.path.basename(labelText)
        self.label = QLabel("Results Dir: <span style='color: green; font-weight:600'>%s</span>"%name, self)
        self.label.setToolTip(self.pathText)
        self.label.setWordWrap(True)
        self.gridLayout.addWidget(self.label, 1, 1, 1, 1)
        self.hLayout = QHBoxLayout()
        self.label_name = QLabel("Name:", self)
        self.combobox = QComboBox(parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.combobox.sizePolicy().hasHeightForWidth())
        self.combobox.setSizePolicy(sizePolicy)
        model = self.combobox.model()
        self.combobox.clear()
        for num, i in enumerate(self.dict_subRsults):
            item = QStandardItem(os.path.basename(i))
            item.setToolTip(i)
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            model.appendRow(item)
        self.combobox.activated[int].connect(self.switchAutoInputs)
        self.hLayout.addWidget(self.label_name)
        self.hLayout.addWidget(self.combobox)
        self.gridLayout.addLayout(self.hLayout, 2, 1, 1, 1)
        self.toolButton = QToolButton(self)
        self.toolButton.setToolTip("Open folder")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton.sizePolicy().hasHeightForWidth())
        self.toolButton.setSizePolicy(sizePolicy)
        self.toolButton.setCursor(QCursor(Qt.PointingHandCursor))
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/folder-icon.png"), QIcon.Normal,
                       QIcon.Off)
        self.toolButton.setIcon(icon)
        self.toolButton.setIconSize(QSize(60, 60))
        self.toolButton.setAutoRaise(True)
        self.toolButton.clicked.connect(lambda : self.factory.openPath(self.pathText, self))
        self.gridLayout.addWidget(self.toolButton, 0, 0, 3, 1)
        self.verticalLayout.addLayout(self.gridLayout)

    def switchAutoInputs(self, index):
        path = self.combobox.itemData(index, role=Qt.ToolTipRole)
        self.autoInputs = self.dict_subRsults[path]


class NMLItemWidget(QWidget):
    setSig = pyqtSignal(str)

    def __init__(self, version, dict_extract_settings, parent=None):
        super(NMLItemWidget, self).__init__(parent)
        self.version = version
        self.dict_extract_settings = dict_extract_settings
        self.initUi()

    def initUi(self):
        self.resize(400, 86)
        self.verticalLayout = QVBoxLayout(self)
        self.gridLayout = QGridLayout()
        self.label_2 = QLabel("<span style='font-weight:600; color:purple;'>" + self.version + "</span>", self)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.addWidget(self.label_2)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.toolButton_2 = QToolButton(self)
        self.toolButton_2.setToolTip("Set")
        self.toolButton_2.setAutoRaise(True)
        self.toolButton_2.clicked.connect(lambda : self.setSig.emit(self.version))
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/cog.png"), QIcon.Normal,
                       QIcon.Off)
        self.toolButton_2.setIcon(icon)
        self.horizontalLayout.addWidget(self.toolButton_2)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 1, 1, 1)
        labelText = "<span style='font-weight:600; color:#ff0000;'>%d</span> features and <span style='font-weight:600; color:#ff0000;'>%d</span> names covered"%(len(self.dict_extract_settings["Features to be extracted"]),
                                                         len(self.dict_extract_settings["Names unification"])-1)
        self.label = QLabel(labelText, self)
        self.label.setWordWrap(True)
        self.gridLayout.addWidget(self.label, 1, 1, 1, 1)
        self.toolButton = QToolButton(self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton.sizePolicy().hasHeightForWidth())
        self.toolButton.setSizePolicy(sizePolicy)
        self.toolButton.setCursor(QCursor(Qt.PointingHandCursor))
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/images.png"), QIcon.Normal,
                       QIcon.Off)
        self.toolButton.setIcon(icon)
        self.toolButton.setIconSize(QSize(60, 60))
        # self.toolButton.setAutoRaise(True)
        # self.toolButton.clicked.connect(lambda : os.startfile(self.pathText.replace("/", "\\")))
        self.gridLayout.addWidget(self.toolButton, 0, 0, 2, 1)
        self.verticalLayout.addLayout(self.gridLayout)

class NMLPopupGui(QDialog):

    def __init__(self, parent=None):
        super(NMLPopupGui, self).__init__(parent)
        from src.factory import Factory
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.resize(380, 365)
        self.setWindowTitle("Choose Sequence Type")
        self.gridLayout = QGridLayout(self)
        self.horizontalLayout = QHBoxLayout()
        self.label = QLabel("Available Types:", self)
        self.horizontalLayout.addWidget(self.label)
        spacerItem = QSpacerItem(153, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.addVersion = QToolButton(self)
        self.addVersion.setAutoRaise(True)
        self.addVersion.setToolTip("Add New Type")
        self.addVersion.setCursor(Qt.PointingHandCursor)
        self.addVersion.setFocusPolicy(Qt.NoFocus)
        self.addVersion.setIcon(QIcon(":/picture/resourses/add-icon.png"))
        self.addVersion.clicked.connect(self.addVersion_func)
        self.horizontalLayout.addWidget(self.addVersion)
        # self.checkBox = QCheckBox("Do not ask again", self)
        # self.checkBox.stateChanged.connect(lambda x: QSettings(
        #     self.thisPath +
        #     '/settings/mainwindow_settings.ini',
        #     QSettings.IniFormat, parent=self).setValue('auto detect', x))
        # self.horizontalLayout.addWidget(self.checkBox)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 2)
        ##
        qss = '''QListView::item{height:30px; border-bottom:1px solid gray; border-radius: 2px}
QListView::item{background:white;}
QListView::item:hover{background: #E5F3FF;}
QListView::item:selected:active{background: #CDE8FF;}'''  #灰色：#F2F2F2，#EBEBEB
        self.listWidget_framless = QListWidget(self)
        self.listWidget_framless.setStyleSheet(qss)
        # self.listWidget.setItemDelegate()
        self.gridLayout.addWidget(self.listWidget_framless, 1, 0, 1, 2)
        self.pushButton = QPushButton("Ok", self)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_ok.png"), QIcon.Normal, QIcon.Off)
        self.pushButton.setIcon(icon)
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 1)
        self.pushButton_2 = QPushButton("Cancel", self)
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(":/picture/resourses/btn_close.png"), QIcon.Normal,
                        QIcon.Off)
        self.pushButton_2.setIcon(icon1)
        self.gridLayout.addWidget(self.pushButton_2, 2, 1, 1, 1)
        self.pushButton.clicked.connect(self.accept)
        self.pushButton.clicked.connect(self.close)
        self.pushButton_2.clicked.connect(self.close)

    def addItemWidgets(self, dict_gbExtract_set):
        self.listWidget_framless.clear()
        self.dict_gbExtract_set = dict_gbExtract_set
        all_versions = dict_gbExtract_set.keys()
        for version in all_versions:
            listItemWidget = NMLItemWidget(version, dict_gbExtract_set[version], self)
            listItemWidget.setSig.connect(self.changeVersion)
            listwitem = QListWidgetItem(self.listWidget_framless)
            listwitem.setSizeHint(listItemWidget.sizeHint())
            self.listWidget_framless.addItem(listwitem)
            self.listWidget_framless.setItemWidget(listwitem, listItemWidget)
        self.listWidget_framless.item(0).setSelected(True)
        # self.listWidget_framless.setItemSelected(self.listWidget_framless.item(0), True)
        self.listWidget_framless.setFocus()

    def changeVersion(self, version):
        # 改变version顺序
        self.GenBankExtract_settings = QSettings(
            self.thisPath + '/settings/GenBankExtract_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.GenBankExtract_settings.setFallbacksEnabled(False)
        allVersion = list(self.dict_gbExtract_set.keys())[:]
        allVersion.remove(version)
        reorder_list = [version] + allVersion
        self.dict_gbExtract_set = OrderedDict((i, self.dict_gbExtract_set[i]) for i in reorder_list)
        self.GenBankExtract_settings.setValue('set_version', self.dict_gbExtract_set)
        ##弹出窗口
        from src.Lg_extractSettings import ExtractSettings
        self.extract_setting = ExtractSettings(self)
        self.extract_setting.checkBox.setVisible(False)
        self.extract_setting.closeSig.connect(self.addItemWidgets)
        # 添加最大化按钮
        self.extract_setting.setWindowFlags(self.extract_setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.extract_setting.exec_()

    def addVersion_func(self):
        from src.Lg_extractSettings import ExtractSettings
        self.extract_setting = ExtractSettings(self)
        self.extract_setting.checkBox.setVisible(False)
        self.extract_setting.closeSig.connect(self.addItemWidgets)
        self.extract_setting.switchVersion(QAction("Add new version", self.extract_setting))
        # 添加最大化按钮
        self.extract_setting.setWindowFlags(self.extract_setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.extract_setting.exec_()


class DetectPopupGui(QDialog):

    def __init__(self, mode, parent=None):
        super(DetectPopupGui, self).__init__(parent)
        from src.factory import Factory
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.resize(460, 365)
        self.setWindowTitle("Choose Inputs")
        self.gridLayout = QGridLayout(self)
        self.horizontalLayout = QHBoxLayout()
        self.label = QLabel("Available inputs prepared for %s in workplace:"%mode, self)
        self.horizontalLayout.addWidget(self.label)
        spacerItem = QSpacerItem(153, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.checkBox = QCheckBox("Do not ask again", self)
        self.checkBox.toggled.connect(lambda x: QSettings(
            self.thisPath +
            '/settings/mainwindow_settings.ini',
            QSettings.IniFormat, parent=self).setValue('auto detect', not x))
        self.horizontalLayout.addWidget(self.checkBox)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 2)
        qss = '''QListView::item{height:30px;}
QListView::item{background:white;}
QListView::item:hover{background: #E5F3FF;}
QListView::item:selected:active{background: #CDE8FF;}'''  #灰色：#F2F2F2，#EBEBEB
        self.listWidget_framless = QListWidget(self)
        # self.listWidget_framless.setSortingEnabled(True)
        self.listWidget_framless.setStyleSheet(qss)
        # self.listWidget.setItemDelegate()
        self.gridLayout.addWidget(self.listWidget_framless, 1, 0, 1, 2)
        self.pushButton = QPushButton("Ok", self)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_ok.png"), QIcon.Normal, QIcon.Off)
        self.pushButton.setIcon(icon)
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 1)
        self.pushButton_2 = QPushButton("No, thanks", self)
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(":/picture/resourses/btn_close.png"), QIcon.Normal,
                        QIcon.Off)
        self.pushButton_2.setIcon(icon1)
        self.gridLayout.addWidget(self.pushButton_2, 2, 1, 1, 1)
        self.pushButton.clicked.connect(self.accept)
        self.pushButton.clicked.connect(self.close)
        self.pushButton_2.clicked.connect(self.close)


class UpdatePopupGui(QDialog):

    def __init__(self, version, description, parent=None):
        super(UpdatePopupGui, self).__init__(parent)
        from src.factory import Factory
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        # self.thisPath = os.path.dirname(os.path.realpath(__file__))
        self.resize(600, 400)
        self.setWindowTitle("Updates found")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.gridLayout = QGridLayout(self)
        self.horizontalLayout = QHBoxLayout()
        self.label = QLabel("New version <span style='font-weight:600; color:#ff0000;'>%s</span> found, update?"%version, self)
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.horizontalLayout.addWidget(self.label)
        spacerItem = QSpacerItem(153, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.checkBox = QCheckBox("Do not ask again", self)
        self.checkBox.stateChanged.connect(lambda x: QSettings(
            self.thisPath +
            '/settings/mainwindow_settings.ini',
            QSettings.IniFormat, parent=self).setValue('not auto check update', x))
        self.horizontalLayout.addWidget(self.checkBox)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 2)
        self.textBrowser = QTextBrowser(self)
        html = '''<html>
<head>
<style media=screen type=text/css>
li{
    margin-top: 10px;
}

li:first-child {
    margin-top:0;
}
</style>
</head>
<body>''' + description + '''</body></html>'''
        self.textBrowser.setHtml(html)
        self.gridLayout.addWidget(self.textBrowser, 1, 0, 1, 2)
        self.pushButton = QPushButton("Update now", self)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_ok.png"), QIcon.Normal, QIcon.Off)
        self.pushButton.setIcon(icon)
        self.gridLayout.addWidget(self.pushButton, 2, 0, 1, 1)
        self.pushButton_2 = QPushButton("No, thanks", self)
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(":/picture/resourses/btn_close.png"), QIcon.Normal,
                        QIcon.Off)
        self.pushButton_2.setIcon(icon1)
        self.gridLayout.addWidget(self.pushButton_2, 2, 1, 1, 1)
        self.pushButton.clicked.connect(self.accept)
        self.pushButton.clicked.connect(self.close)
        self.pushButton_2.clicked.connect(self.close)


class ListItemWidget(QWidget):

    itemOpSignal = pyqtSignal(QListWidgetItem, str)

    def __init__(self, text, listwidgetItem, parent=None):
        super(ListItemWidget, self).__init__(parent)
        self.text = text
        self.listwidgetItem = listwidgetItem
        self.initUi()

    def initUi(self):
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout.setSpacing(0)
        self.text_label = QLabel(self.text, self)
        self.bt_close = QToolButton(self)
        self.bt_close.setIcon(QIcon(":/picture/resourses/if_Delete_1493279.png"))
        self.bt_close.setAutoRaise(True)
        self.bt_close.setCursor(Qt.PointingHandCursor)
        self.bt_close.setToolTip("Delete")
        self.bt_close.clicked.connect(lambda: self.itemOpSignal.emit(self.listwidgetItem, self.text))
        self.horizontalLayout.addWidget(self.text_label)
        self.horizontalLayout.addStretch()
        self.horizontalLayout.addWidget(self.bt_close)

class AdvanceQlistwidget(QListWidget):

    itemRemoveSig = pyqtSignal(str)

    def __init__(self, *args):
        super(AdvanceQlistwidget, self).__init__(*args)

    def addItemWidget(self, text):
        item = QListWidgetItem(self)
        self.CurrentItemWidget = ListItemWidget(text, item, self)
        self.CurrentItemWidget.itemOpSignal.connect(self.removeListItem)
        if self.count() % 2 == 0:
            item.setBackground(QColor(255, 255, 255))
        else:
            item.setBackground(QColor(237, 243, 254))
        item.setSizeHint(self.CurrentItemWidget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, self.CurrentItemWidget)

    def refreshBackColors(self):
        for row in range(self.count()):
            if row % 2 == 0:
                self.item(row).setBackground(QColor(255, 255, 255))
            else:
                self.item(row).setBackground(QColor(237, 243, 254))

    def removeListItem(self, listwidgetItem, text):
        if self.count() > 1:
            index = self.indexFromItem(listwidgetItem)
            self.takeItem(index.row())
            self.refreshBackColors()
            self.itemRemoveSig.emit("")
        else:
            self.itemRemoveSig.emit("retain")

    def text(self, index):
        return self.itemWidget(self.item(index)).text


class CustomTreeIndexWidget(QWidget):

    def __init__(self, text, index=QModelIndex(), hoverMode=False, parent=None):
        super(CustomTreeIndexWidget, self).__init__(parent)
        self.hoverMode = hoverMode
        self.index = index
        self.layout = QHBoxLayout(self)
        self.btnGroup = []
        self.layout.addStretch()
        self.layout.setSpacing(0)
        textWidth = QFontMetrics(QApplication.font(self)).width(text)
        self.layout.setContentsMargins(textWidth+5, 0, 0, 0)
        # print(QApplication.font(self).toString())

    def addBtn(self, toolTip, icon, triggerSig=None):
        self.toolBtn = QToolButton(self)
        self.toolBtn.setAutoRaise(True)
        self.toolBtn.setToolTip(toolTip)
        self.toolBtn.setCursor(Qt.PointingHandCursor)
        self.toolBtn.setFocusPolicy(Qt.NoFocus)
        self.toolBtn.setIcon(icon)
        if triggerSig:
            self.toolBtn.clicked.connect(lambda : triggerSig.emit(self.index))
        self.layout.addWidget(self.toolBtn, 0, Qt.AlignRight)
        self.btnGroup.append(self.toolBtn)
        if self.hoverMode:
            self.toolBtn.setVisible(False)

    def enterEvent(self, e):
        if self.hoverMode:
            for btn in self.btnGroup:
                btn.setVisible(True)

    def leaveEvent(self, e):
        if self.hoverMode:
            for btn in self.btnGroup:
                btn.setVisible(False)


class ClickedLable(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args):
        super(ClickedLable, self).__init__(*args)

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        return super(ClickedLable, self).mouseReleaseEvent(event)


class ClickedLableGif(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args):
        super(ClickedLableGif, self).__init__(*args)
        movie = QMovie(":/picture/resourses/help.gif")
        self.setMovie(movie)
        movie.start()

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        return super(ClickedLableGif, self).mouseReleaseEvent(event)


class CircleProgressBar(QWidget):

    Color = QColor(24, 189, 155)  # 圆圈颜色
    Clockwise = True  # 顺时针还是逆时针
    Delta = 36

    def __init__(self, *args, color=None, clockwise=True, **kwargs):
        super(CircleProgressBar, self).__init__(*args, **kwargs)
        self.angle = 0
        self.Clockwise = clockwise
        if color:
            self.Color = color
        self._timer = QTimer(self, timeout=self.update)
        self._timer.start(100)

    def paintEvent(self, event):
        super(CircleProgressBar, self).paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        side = min(self.width(), self.height())
        painter.scale(side / 100.0, side / 100.0)
        painter.rotate(self.angle)
        painter.save()
        painter.setPen(Qt.NoPen)
        color = self.Color.toRgb()
        for i in range(11):
            color.setAlphaF(1.0 * i / 10)
            painter.setBrush(color)
            painter.drawEllipse(30, -10, 20, 20)
            painter.rotate(36)
        painter.restore()
        self.angle += self.Delta if self.Clockwise else -self.Delta
        self.angle %= 360

    @pyqtProperty(QColor)
    def color(self) -> QColor:
        return self.Color

    @color.setter
    def color(self, color: QColor):
        if self.Color != color:
            self.Color = color
            self.update()

    @pyqtProperty(bool)
    def clockwise(self) -> bool:
        return self.Clockwise

    @clockwise.setter
    def clockwise(self, clockwise: bool):
        if self.Clockwise != clockwise:
            self.Clockwise = clockwise
            self.update()

    @pyqtProperty(int)
    def delta(self) -> int:
        return self.Delta

    @delta.setter
    def delta(self, delta: int):
        if self.delta != delta:
            self.delta = delta
            self.update()

    def sizeHint(self) -> QSize:
        return QSize(100, 100)


class PercentProgressBar(QWidget):

    MinValue = 0
    MaxValue = 100
    Value = 0
    BorderWidth = 8
    Clockwise = True  # 顺时针还是逆时针
    ShowPercent = True  # 是否显示百分比
    ShowFreeArea = False  # 显示背后剩余
    ShowSmallCircle = False  # 显示带头的小圆圈
    TextColor = QColor(255, 255, 255)  # 文字颜色
    BorderColor = QColor(24, 189, 155)  # 边框圆圈颜色
    BackgroundColor = QColor(70, 70, 70)  # 背景颜色

    def __init__(self, *args, value=0, minValue=0, maxValue=100,
                 borderWidth=8, clockwise=True, showPercent=True,
                 showFreeArea=False, showSmallCircle=False,
                 textColor=QColor(255, 255, 255),
                 borderColor=QColor(24, 189, 155),
                 backgroundColor=QColor(70, 70, 70), **kwargs):
        super(PercentProgressBar, self).__init__(*args, **kwargs)
        self.Value = value
        self.MinValue = minValue
        self.MaxValue = maxValue
        self.BorderWidth = borderWidth
        self.Clockwise = clockwise
        self.ShowPercent = showPercent
        self.ShowFreeArea = showFreeArea
        self.ShowSmallCircle = showSmallCircle
        self.TextColor = textColor
        self.BorderColor = borderColor
        self.BackgroundColor = backgroundColor

    def setRange(self, minValue: int, maxValue: int):
        if minValue >= maxValue:  # 最小值>=最大值
            return
        self.MinValue = minValue
        self.MaxValue = maxValue
        self.update()

    def paintEvent(self, event):
        super(PercentProgressBar, self).paintEvent(event)
        width = self.width()
        height = self.height()
        side = min(width, height)

        painter = QPainter(self)
        # 反锯齿
        painter.setRenderHints(QPainter.Antialiasing |
                               QPainter.TextAntialiasing)
        # 坐标中心为中间点
        painter.translate(width / 2, height / 2)
        # 按照100x100缩放
        painter.scale(side / 100.0, side / 100.0)

        # 绘制中心园
        self._drawCircle(painter, 50)
        # 绘制圆弧
        self._drawArc(painter, 50 - self.BorderWidth / 2)
        # 绘制文字
        self._drawText(painter, 50)

    def _drawCircle(self, painter: QPainter, radius: int):
        # 绘制中心园
        radius = radius - self.BorderWidth
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.BackgroundColor)
        painter.drawEllipse(QRectF(-radius, -radius, radius * 2, radius * 2))
        painter.restore()

    def _drawArc(self, painter: QPainter, radius: int):
        # 绘制圆弧
        painter.save()
        painter.setBrush(Qt.NoBrush)
        # 修改画笔
        pen = painter.pen()
        pen.setWidthF(self.BorderWidth)
        pen.setCapStyle(Qt.RoundCap)

        arcLength = 360.0 / (self.MaxValue - self.MinValue) * self.Value
        rect = QRectF(-radius, -radius, radius * 2, radius * 2)

        if not self.Clockwise:
            # 逆时针
            arcLength = -arcLength

        # 绘制剩余进度圆弧
        if self.ShowFreeArea:
            acolor = self.BorderColor.toRgb()
            acolor.setAlphaF(0.2)
            pen.setColor(acolor)
            painter.setPen(pen)
            painter.drawArc(rect, (0 - arcLength) *
                            16, -(360 - arcLength) * 16)

        # 绘制当前进度圆弧
        pen.setColor(self.BorderColor)
        painter.setPen(pen)
        painter.drawArc(rect, 0, -arcLength * 16)

        # 绘制进度圆弧前面的小圆
        if self.ShowSmallCircle:
            offset = radius - self.BorderWidth + 1
            radius = self.BorderWidth / 2 - 1
            painter.rotate(-90)
            circleRect = QRectF(-radius, radius + offset,
                                radius * 2, radius * 2)
            painter.rotate(arcLength)
            painter.drawEllipse(circleRect)

        painter.restore()

    def _drawText(self, painter: QPainter, radius: int):
        # 绘制文字
        painter.save()
        painter.setPen(self.TextColor)
        painter.setFont(QFont('Arial', 25))
        strValue = '{}%'.format(int(self.Value / (self.MaxValue - self.MinValue)
                                    * 100)) if self.ShowPercent else str(self.Value)
        painter.drawText(QRectF(-radius, -radius, radius * 2,
                                radius * 2), Qt.AlignCenter, strValue)
        painter.restore()

    @pyqtProperty(int)
    def minValue(self) -> int:
        return self.MinValue

    @minValue.setter
    def minValue(self, minValue: int):
        if self.MinValue != minValue:
            self.MinValue = minValue
            self.update()

    @pyqtProperty(int)
    def maxValue(self) -> int:
        return self.MaxValue

    @maxValue.setter
    def maxValue(self, maxValue: int):
        if self.MaxValue != maxValue:
            self.MaxValue = maxValue
            self.update()

    @pyqtProperty(int)
    def value(self) -> int:
        return self.Value

    @value.setter
    def value(self, value: int):
        if self.Value != value:
            self.Value = value
            self.update()

    @pyqtProperty(float)
    def borderWidth(self) -> float:
        return self.BorderWidth

    @borderWidth.setter
    def borderWidth(self, borderWidth: float):
        if self.BorderWidth != borderWidth:
            self.BorderWidth = borderWidth
            self.update()

    @pyqtProperty(bool)
    def clockwise(self) -> bool:
        return self.Clockwise

    @clockwise.setter
    def clockwise(self, clockwise: bool):
        if self.Clockwise != clockwise:
            self.Clockwise = clockwise
            self.update()

    @pyqtProperty(bool)
    def showPercent(self) -> bool:
        return self.ShowPercent

    @showPercent.setter
    def showPercent(self, showPercent: bool):
        if self.ShowPercent != showPercent:
            self.ShowPercent = showPercent
            self.update()

    @pyqtProperty(bool)
    def showFreeArea(self) -> bool:
        return self.ShowFreeArea

    @showFreeArea.setter
    def showFreeArea(self, showFreeArea: bool):
        if self.ShowFreeArea != showFreeArea:
            self.ShowFreeArea = showFreeArea
            self.update()

    @pyqtProperty(bool)
    def showSmallCircle(self) -> bool:
        return self.ShowSmallCircle

    @showSmallCircle.setter
    def showSmallCircle(self, showSmallCircle: bool):
        if self.ShowSmallCircle != showSmallCircle:
            self.ShowSmallCircle = showSmallCircle
            self.update()

    @pyqtProperty(QColor)
    def textColor(self) -> QColor:
        return self.TextColor

    @textColor.setter
    def textColor(self, textColor: QColor):
        if self.TextColor != textColor:
            self.TextColor = textColor
            self.update()

    @pyqtProperty(QColor)
    def borderColor(self) -> QColor:
        return self.BorderColor

    @borderColor.setter
    def borderColor(self, borderColor: QColor):
        if self.BorderColor != borderColor:
            self.BorderColor = borderColor
            self.update()

    @pyqtProperty(QColor)
    def backgroundColor(self) -> QColor:
        return self.BackgroundColor

    @backgroundColor.setter
    def backgroundColor(self, backgroundColor: QColor):
        if self.BackgroundColor != backgroundColor:
            self.BackgroundColor = backgroundColor
            self.update()

    def setValue(self, value):
        self.value = value

    def sizeHint(self) -> QSize:
        return QSize(100, 100)


class ProgressDialog(QDialog):

    def __init__(self, window_title="Please wait", label_text="Percent ProgressBar", mode="percent", parent=None):
        super(ProgressDialog, self).__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(Qt.WindowModal)
        # aniEffect = AnimationShadowEffect(QColor("purple"))
        # self.setGraphicsEffect(aniEffect)
        # radius = 40
        # self.resize(250, 250)
        # path = QPainterPath()
        # path.addRoundedRect(QRectF(self.rect()), radius, radius)
        # mask = QRegion(path.toFillPolygon().toPolygon());
        # self.setMask(mask)
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.label_title = QLabel("<span style='font-weight:600; color:white; font: 15px;'>%s</span>"%window_title, self)
        self.horizontalLayout.addWidget(self.label_title)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.toolButton = QToolButton(self)
        self.toolButton.setIcon(QIcon(":/picture/resourses/Delete_white.png"))
        self.toolButton.setAutoRaise(True)
        self.toolButton.clicked.connect(self.close)
        # self.toolButton.setVisible(False)
        # self.enterSig.connect(lambda : self.toolButton.setVisible(True))
        # self.leaveSig.connect(lambda : self.toolButton.setVisible(False))
        self.horizontalLayout.addWidget(self.toolButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        if mode == "percent":
            self.progressBar = PercentProgressBar(self, showSmallCircle=True)
        else:
            self.progressBar = CircleProgressBar(
            self, color=QColor(255, 0, 0), clockwise=False)
        self.verticalLayout.addWidget(self.progressBar)
        self.label = QLabel("<span style='font-weight:600; color:white; font: 25px;'>%s</span>"%label_text, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.verticalLayout.addWidget(self.label)
        # self.verticalLayout_2.addWidget(self.widget)

    def value(self):
        return self.progressBar.Value

    def setValue(self, num):
        self.progressBar.setValue(num)
        QCoreApplication.processEvents()
        if num == 100:
            self.close()
        #     self.deleteLater()
        #     del self

    def paintEvent(self, event=None):
        painter = QPainter(self)
        painter.setOpacity(0.3)
        painter.setBrush(Qt.black)
        painter.setPen(QPen(Qt.black))
        painter.drawRect(self.rect())

    # def enterEvent(self, *args, **kwargs):
    #     self.toolButton.setVisible(True)
    #
    # def leaveEvent(self, *args, **kwargs):
    #     self.toolButton.setVisible(False)


class AnimationShadowEffect(QGraphicsDropShadowEffect):
    def __init__(self, color, *args, **kwargs):
        super(AnimationShadowEffect, self).__init__(*args, **kwargs)
        self.setColor(color)
        self.setOffset(0, 0)
        self.setBlurRadius(0)
        self._radius = 0
        self.animation = QPropertyAnimation(self)
        self.animation.setTargetObject(self)
        self.animation.setDuration(2000)  # 一次循环时间
        self.animation.setLoopCount(-1)  # 永久循环
        self.animation.setPropertyName(b'radius')
        # 插入线行值
        self.animation.setKeyValueAt(0, 1)
        self.animation.setKeyValueAt(0.5, 30)
        self.animation.setKeyValueAt(1, 1)
        self.animation.start()

    def start(self):
        self.animation.start()

    def stop(self, r=0):
        # 停止动画并修改半径值
        self.animation.stop()
        # self._radius = r
        self.setBlurRadius(1)

    @pyqtProperty(int)
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, r):
        self._radius = r
        self.setBlurRadius(r)


class NoteMessage(QDialog, object):

    def __init__(self, message, icon, checkboxText="Do not remind again  ", singleBtn=False, parent=None, hideReminder=False):
        super(NoteMessage, self).__init__(parent)
        self.setWindowTitle("Information")
        self.setMinimumWidth(520)
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
        self.label_2 = QLabel(self.widget_layout)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(11)
        self.label_2.setFont(font)
        self.label_2.setWordWrap(True)
        self.horizontalLayout.addWidget(self.label_2)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem = QSpacerItem(20, 29, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2 = QHBoxLayout()
        self.checkBox = QCheckBox(self.widget_layout)
        self.horizontalLayout_2.addWidget(self.checkBox)
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
        self.label_2.setText("<p style='line-height:25px; height:25px'>" + message + "</p>")
        self.checkBox.setText(checkboxText)
        self.gridLayout.addWidget(self.widget_layout, 0, 0, 1, 1)
        self.adjustSize()
        if hideReminder:
            self.checkBox.setVisible(False)


class NoteMessage_option(QDialog, object):

    def __init__(self, message, icon, checkboxText="Do not remind again  ", singleBtn=False, parent=None,
                 hideReminder=False):
        super(NoteMessage_option, self).__init__(parent)
        self.setWindowTitle("Information")
        self.setMinimumWidth(520)
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
        self.clearResults = QRadioButton("Clear the results folder", self.widget_layout)
        self.retainResults = QRadioButton("Retain the previous results, but the same file(s) will be overwritten", self.widget_layout)
        self.label_2 = QLabel(self.widget_layout)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(11)
        self.label_2.setFont(font)
        self.label_2.setWordWrap(True)
        self.label_2.setText("Note that if you need the previous results, please copy them to another folder or cancel "
                             "this task and conduct it in a new work folder (or workplace)!")
        self.label_3 = QLabel("<p style='line-height:25px; height:25px'>" + message + "</p>", self.widget_layout)
        self.verticalLayout_3.addWidget(self.label_3)
        self.verticalLayout_3.addWidget(self.clearResults)
        self.verticalLayout_3.addWidget(self.retainResults)
        self.verticalLayout_3.addWidget(self.label_2)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem = QSpacerItem(20, 29, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2 = QHBoxLayout()
        self.checkBox = QCheckBox(self.widget_layout)
        self.horizontalLayout_2.addWidget(self.checkBox)
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
        self.checkBox.setText(checkboxText)
        self.gridLayout.addWidget(self.widget_layout, 0, 0, 1, 1)
        self.adjustSize()
        if hideReminder:
            self.checkBox.setVisible(False)


class Inputbox_message(QDialog, object):

    def __init__(self, icon, singleBtn=False, parent=None):
        super(Inputbox_message, self).__init__(parent)
        self.setWindowTitle("Information")
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
        self.appendOld = QRadioButton("Append to the old files", self.widget_layout)
        self.clearOld = QRadioButton("Remove the old files then import the new files", self.widget_layout)
        # self.label_2 = QLabel(self.widget_layout)
        # sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        # self.label_2.setSizePolicy(sizePolicy)
        # font = QFont()
        # font.setPointSize(11)
        # self.label_2.setFont(font)
        # self.label_2.setWordWrap(True)
        # self.label_2.setText("Note that if you need the previous results, please copy them to another folder or cancel "
        #                      "this task and conduct it in a new work folder (or workplace)!")
        self.label_3 = QLabel("<p style='line-height:25px; height:25px'>Some files exist in the input box, you can choose to:</p>", self.widget_layout)
        self.verticalLayout_3.addWidget(self.label_3)
        self.verticalLayout_3.addWidget(self.appendOld)
        self.verticalLayout_3.addWidget(self.clearOld)
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


class ArrowPushButton(QPushButton):
    def __init__(self, *args):
        super(ArrowPushButton, self).__init__(*args)
        self.horizontalLayout = QHBoxLayout(self)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.toolButton = QToolButton(self)
        #"QToolButton {background-color: transparent;} "
        self.toolButton.setStyleSheet("QToolButton {border: none;} "
                                      "QToolButton::menu-indicator {image: None;}")
        self.toolButton.setAutoFillBackground(True)
        # 透明背景
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor(192, 253, 123, 100))
        self.toolButton.setPalette(palette)
        # self.toolButton.setAttribute(Qt.WA_TranslucentBackground)
        # self.toolButton.setWindowFlags(Qt.FramelessWindowHint)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolButton.sizePolicy().hasHeightForWidth())
        self.toolButton.setSizePolicy(sizePolicy)
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(":/picture/resourses/down_arrow_red.png"), QIcon.Normal,
                        QIcon.Off)
        self.toolButton.setIcon(icon1)
        self.toolButton.setObjectName("toolButton")
        self.toolButton.setPopupMode(QToolButton.InstantPopup)
        self.horizontalLayout.addWidget(self.toolButton)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

class SearchQLineEdit(QLineEdit):
    clicked = pyqtSignal()

    def __init__(self, *args):
        super(SearchQLineEdit, self).__init__(*args)
        self.buttonSearch = QToolButton(self)
        self.buttonSearch.setAutoRaise(True)
        self.buttonSearch.setToolTip("Search")
        self.buttonSearch.setCursor(Qt.PointingHandCursor)
        self.buttonSearch.setFocusPolicy(Qt.NoFocus)
        self.buttonSearch.setIcon(QIcon(":/picture/resourses/search.png"))
        self.buttonSearch.setStyleSheet("QToolButton {border: none;}")
        self.buttonStop = QToolButton(self)
        self.buttonStop.setAutoRaise(True)
        self.buttonStop.setToolTip("Stop")
        self.buttonStop.setCursor(Qt.PointingHandCursor)
        self.buttonStop.setFocusPolicy(Qt.NoFocus)
        self.buttonStop.setIcon(QIcon(":/picture/resourses/delete.png"))
        self.buttonStop.setStyleSheet("QToolButton {border: none;}")
        self.buttonStop.setDisabled(True)
        # self.buttonSearch.clicked.connect(self.viewFileContent)
        layout = QHBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.buttonSearch, 0, Qt.AlignRight)
        layout.addWidget(self.buttonStop, 0, Qt.AlignRight)
        layout.setSpacing(6)
        layout.setContentsMargins(5, 0, 5, 0)
        frameWidth = self.style().pixelMetric(QStyle.PM_DefaultFrameWidth)
        rightButtonWidth1 = self.buttonSearch.sizeHint().width()
        rightButtonWidth2 = self.buttonStop.sizeHint().width()
        self.setTextMargins(5, 0, rightButtonWidth1 + rightButtonWidth2 + frameWidth + 7, 0) ##这里设置一下距离

    def mouseReleaseEvent(self, e):
        self.clicked.emit()


class FileIconProvider(QFileIconProvider):

    def __init__(self, trashMode=False, *args, **kwargs):
        super(FileIconProvider, self).__init__(*args, **kwargs)
        self.isTrashMode = trashMode
        self.TrashIcon = QIcon(
            ":/picture/resourses/if_icon-27-trash-can_315225.png")
        self.itemIcon = QIcon(
            ":/picture/resourses/caribbean-blue-clipart-12.png")
        self.WorkTableIcon = QIcon(
            ":/picture/resourses/introduction-to-excel-gridlines.png")
        self.reportIcon = QIcon(":/picture/resourses/workreport.png")

    def icon(self, type_info):
        '''
        :param fileInfo: 参考http://doc.qt.io/qt-5/qfileinfo.html
        '''
        if self.isTrashMode and isinstance(type_info, QFileInfo):
            return self.TrashIcon
        elif isinstance(type_info, QFileInfo):
            # 如果type_info是QFileInfo类型则用getInfoIcon来返回图标(可以查查QFileInfo类有哪些方法)
            return self.getInfoIcon(type_info)
        # 如果type_info是QFileIconProvider自身的IconType枚举类型则执行下面的方法
        # 这里只能自定义通用的几种类型，参考http://doc.qt.io/qt-5/qfileiconprovider.html#IconType-enum
        '''
        QFileIconProvider::Computer     0
        QFileIconProvider::Desktop      1
        QFileIconProvider::Trashcan     2
        QFileIconProvider::Network      3
        QFileIconProvider::Drive        4
        QFileIconProvider::Folder       5
        QFileIconProvider::File         6
        '''
        return super(FileIconProvider, self).icon(type_info)

    def getInfoIcon(self, type_info):
        if type_info.isDir() and ("recycled" in type_info.filePath()):  # 文件夹
            return self.TrashIcon
        # if type_info.isFile() and type_info.suffix() == "txt":  # 文件并且是txt
        #     return self.TxtIcon
        elif type_info.isDir() and type_info.fileName() in ["Other_File", "GenBank_File"]:
            return self.itemIcon
        elif type_info.isDir() and os.path.basename(os.path.dirname(type_info.filePath())) in ["Other_File", "GenBank_File"]:
            return self.WorkTableIcon
        elif type_info.isDir() and type_info.fileName() == "Flowchart_reports":
            return self.reportIcon
        return super(FileIconProvider, self).icon(type_info)


class MyQProgressDialog(QProgressDialog):

    def __init__(self, *args):
        super(MyQProgressDialog, self).__init__(*args)

    def closeEvent(self, event):
        return QDialog().closeEvent(event)


class JobFinishMessageBox(QDialog, object):

    def __init__(self, icon, singleBtn=False, parent=None):
        super(JobFinishMessageBox, self).__init__(parent)
        self.setWindowTitle("Information")
        self.gridLayout = QGridLayout(self)
        self.widget_layout = QWidget(self)
        self.widget_layout.setObjectName("widget_layout")
        self.widget_layout.setStyleSheet("QWidget#widget_layout {border: 1px ridge gray; background-color: white}")
        self.verticalLayout = QVBoxLayout(self.widget_layout)
        self.label = QLabel(self.widget_layout)
        self.label.resize(52, 52)
        self.label.setText("Task completed! You can choose to:")
        self.label.setPixmap(QPixmap(icon).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(20)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.addWidget(self.label)
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_3 = QVBoxLayout()
        # self.openFolder = QRadioButton("Open the results folder", self.widget_layout)
        self.label_3 = QLabel("<p style='line-height:25px; height:25px'>Task completed! You can choose to:"
                              "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                              "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</p>", self.widget_layout)
        self.combox = QComboBox(self)
        self.verticalLayout_3.addWidget(self.label_3)
        # self.verticalLayout_3.addWidget(self.openFolder)
        self.verticalLayout_3.addWidget(self.combox)
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

    def refreshCombo(self, list_):
        if (platform.system().lower() == "windows") and ("Import the results to HmmCleaner" in list_):
            # windows 屏蔽HmmCleaner
            list_.remove("Import the results to HmmCleaner")
        model = self.combox.model()
        self.combox.clear()
        for num, i in enumerate(list_):
            item = QStandardItem(i)
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            model.appendRow(item)
        self.combox.setCurrentIndex(0)


class DblClickTexedit(QTextEdit):
    dblclicked = pyqtSignal()

    def __init__(self, *args):
        super(DblClickTexedit, self).__init__(*args)
        self.buttonEdit = QToolButton(self)
        self.buttonEdit.setAutoRaise(True)
        self.buttonEdit.setToolTip("View")
        self.buttonEdit.setCursor(Qt.PointingHandCursor)
        self.buttonEdit.setFocusPolicy(Qt.NoFocus)
        self.buttonEdit.setIcon(QIcon(":/picture/resourses/edit2.png"))
        self.buttonEdit.setStyleSheet("QToolButton {border: none;}")
        self.buttonWrap = QToolButton(self)
        self.buttonWrap.setCheckable(True)
        self.buttonWrap.setToolTip("Delete")
        self.buttonWrap.setCursor(Qt.PointingHandCursor)
        self.buttonWrap.setFocusPolicy(Qt.NoFocus)
        self.buttonWrap.setIcon(QIcon(":/picture/resourses/interface-controls-text-wrap-512.png"))
        self.buttonWrap.clicked.connect(self.wrapText)
        layout = QHBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.buttonEdit, 0, Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self.buttonWrap, 0, Qt.AlignLeft | Qt.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 20, 0)

    def wrapText(self, bool_):
        if self.buttonWrap.isChecked():
            self.buttonWrap.setChecked(True)
            self.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            self.buttonWrap.setChecked(False)
            self.setLineWrapMode(QTextEdit.NoWrap)

    def mouseDoubleClickEvent(self, e):
        self.dblclicked.emit()
        return QTextEdit().mouseDoubleClickEvent(e)

class ListItemsOption(QDialog, object):

    def __init__(self, message1, message2, text, icon, singleBtn=False, parent=None):
        super(ListItemsOption, self).__init__(parent)
        self.gridLayout = QGridLayout(self)
        self.verticalLayout = QVBoxLayout()
        self.label = QLabel(self)
        self.label.resize(52, 52)
        self.label.setText("")
        self.label.setPixmap(QPixmap(icon).scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.verticalLayout.addWidget(self.label)
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 2, 1)
        self.label_2 = QLabel("<p style='line-height:25px; height:25px'>" + message1 + "</p>", self)
        self.label_2.setWordWrap(True)
        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)
        self.label_3 = QLabel(message2, self)
        spacerItem1 = QSpacerItem(369, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Horizontal)
        if singleBtn:
            self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        else:
            self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.textEdit = QTextEdit(self)
        self.textEdit.setAcceptRichText(False)
        self.textEdit.setText(text)
        self.gridLayout.addWidget(self.textEdit, 1, 1, 1, 1)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.addWidget(self.label_3)
        self.horizontalLayout.addItem(spacerItem1)
        self.horizontalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 2)
        QMetaObject.connectSlotsByName(self)
        self.adjustSize()

class AllListWidget(QListWidget):

    def __init__(self, *args, **kwargs):
        super(AllListWidget, self).__init__(*args, **kwargs)
        # 不能编辑
        self.setEditTriggers(self.NoEditTriggers)
        self.setAcceptDrops(True)
        self._rubberPos = None
        self._rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        # 设置角落的文字
        self.gridLayout = QGridLayout(self)
        spacerItem = QSpacerItem(20, 249, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 0, 1, 1, 1)
        spacerItem1 = QSpacerItem(350, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 1, 0, 1, 1)
        self.corner_label = QLabel("Variables", self)
        self.corner_label.setAlignment(Qt.AlignBottom | Qt.AlignRight | Qt.AlignTrailing)
        self.corner_label.setStyleSheet("QLabel { background-color: transparent; "
                                                "color: grey;"
                                                "font: 14px;}")
        self.gridLayout.addWidget(self.corner_label, 1, 1, 1, 1)

    # 实现拖拽的时候预览效果图
    # 这里演示拼接所有的item截图(也可以自己写算法实现堆叠效果)
    def startDrag(self, supportedActions):
        items = self.selectedItems()
        drag = QDrag(self)
        mimeData = self.mimeData(items)
        # 由于QMimeData只能设置image、urls、str、bytes等等不方便
        # 这里添加一个额外的属性直接把item放进去,后面可以根据item取出数据
        mimeData.setProperty('myItems', items)
        drag.setMimeData(mimeData)
        pixmap = QPixmap(self.viewport().visibleRegion().boundingRect().size())
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        for item in items:
            rect = self.visualRect(self.indexFromItem(item))
            painter.drawPixmap(rect, self.viewport().grab(rect))
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.viewport().mapFromGlobal(QCursor.pos()))
        drag.exec_(supportedActions)

    def mousePressEvent(self, event):
        # 列表框点击事件,用于设置框选工具的开始位置
        super(AllListWidget, self).mousePressEvent(event)
        if event.buttons() != Qt.LeftButton or self.itemAt(event.pos()):
            return
        self._rubberPos = event.pos()
        self._rubberBand.setGeometry(QRect(self._rubberPos, QSize()))
        self._rubberBand.show()

    def mouseReleaseEvent(self, event):
        # 列表框点击释放事件,用于隐藏框选工具
        super(AllListWidget, self).mouseReleaseEvent(event)
        self._rubberPos = None
        self._rubberBand.hide()

    def mouseMoveEvent(self, event):
        # 列表框鼠标移动事件,用于设置框选工具的矩形范围
        super(AllListWidget, self).mouseMoveEvent(event)
        if self._rubberPos:
            pos = event.pos()
            lx, ly = self._rubberPos.x(), self._rubberPos.y()
            rx, ry = pos.x(), pos.y()
            size = QSize(abs(rx - lx), abs(ry - ly))
            self._rubberBand.setGeometry(
                QRect(QPoint(min(lx, rx), min(ly, ry)), size))

    def makeItem(self, cname, type_):
        font_ = self.font()
        length = QFontMetrics(QFont(font_.family(), font_.pointSize())).width(cname)
        height = QFontMetrics(QFont(font_.family(), font_.pointSize())).height()
        size = QSize(length + 25, height + 10)
        item = QListWidgetItem(self)
        item.setData(Qt.UserRole + 1, cname)  # 把颜色放进自定义的data里面
        item.setSizeHint(size)
        item.variable_name = QLabel(cname, self)  # 自定义控件
        item.variable_name.setMargin(2)  # 往内缩进2
        item.variable_name.resize(size)
        item.variable_name.setAlignment(Qt.AlignCenter)
        item.type = type_
        color = "#009900" if type_ == "object" else "#0c4c8a"
        item.variable_name.setStyleSheet(f"""QLabel {{background-color: {color}; 
                                                    color : white; 
                                                    border-radius: 7px;
                                                    font: 14px;}}
                                            QLabel:selected {{
                                                border-radius: 10px;
                                                border: 1px solid rgb(0, 170, 255);
                                            }}
                                            QLabel:selected:!active {{
                                                border-radius: 10px;
                                                border: 1px solid transparent;
                                            }}
                                            QLabel:selected:active {{
                                                border-radius: 10px;
                                                border: 1px solid rgb(0, 170, 255);
                                            }}
                                            QLabel:hover {{
                                                border-radius: 10px;
                                                border: 1px solid rgb(0, 170, 255);}}""")
        self.setItemWidget(item, item.variable_name)

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        event.accept()
        sender = event.mimeData().property('sender')
        if sender:
            sender.clear()


class SingleListWidget(QListWidget):
    # 可以拖进来的QListWidget

    def __init__(self, *args, **kwargs):
        super(SingleListWidget, self).__init__(*args, **kwargs)
        self.resize(400, 400)
        self.setAcceptDrops(True)
        # 设置从左到右、自动换行、依次排列
        self.setFlow(self.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(self.Adjust)
        # item的间隔
        self.setSpacing(5)
        self._rubberPos = None
        self._rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        # 设置角落的文字
        self.gridLayout = QGridLayout(self)
        spacerItem = QSpacerItem(20, 249, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 0, 1, 1, 1)
        spacerItem1 = QSpacerItem(350, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 1, 0, 1, 1)
        self.corner_label = QLabel(self)
        self.corner_label.setAlignment(Qt.AlignBottom|Qt.AlignRight|Qt.AlignTrailing)
        # self.corner_label.setStyleSheet("Qlabel {color: white; font: 14px;}")
        self.corner_label.setStyleSheet("QLabel { background-color: transparent; "
                                        "color: grey;"
                                        "font: 14px;}")
        self.gridLayout.addWidget(self.corner_label, 1, 1, 1, 1)

    def setCornerText(self, text):
        self.corner_label.setText(text)

    # 实现拖拽的时候预览效果图
    # 这里演示拼接所有的item截图(也可以自己写算法实现堆叠效果)
    def startDrag(self, supportedActions):
        items = self.selectedItems()
        drag = QDrag(self)
        mimeData = self.mimeData(items)
        # 由于QMimeData只能设置image、urls、str、bytes等等不方便
        # 这里添加一个额外的属性直接把item放进去,后面可以根据item取出数据
        mimeData.setProperty('myItems', items)
        mimeData.setProperty('sender', self)
        drag.setMimeData(mimeData)
        pixmap = QPixmap(self.viewport().visibleRegion().boundingRect().size())
        pixmap.fill(Qt.transparent)
        painter = QPainter()
        painter.begin(pixmap)
        for item in items:
            rect = self.visualRect(self.indexFromItem(item))
            painter.drawPixmap(rect, self.viewport().grab(rect))
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.viewport().mapFromGlobal(QCursor.pos()))
        drag.exec_(supportedActions)

    def makeItem(self, cname, type_):
        font_ = self.font()
        length = QFontMetrics(QFont(font_.family(), font_.pointSize())).width(cname)
        height = QFontMetrics(QFont(font_.family(), font_.pointSize())).height()
        size = QSize(length + 25, height + 10)
        item = QListWidgetItem(self)
        item.setData(Qt.UserRole + 1, cname)  # 把颜色放进自定义的data里面
        item.setSizeHint(size)
        item.variable_name = QLabel(cname, self)  # 自定义控件
        item.variable_name.setMargin(2)  # 往内缩进2
        item.variable_name.resize(size)
        item.variable_name.setAlignment(Qt.AlignCenter)
        color = "#009900" if type_ == "object" else "#0c4c8a"
        item.variable_name.setStyleSheet(f"""QLabel {{background-color: {color}; 
                                                            color : white; 
                                                            border-radius: 7px;
                                                            font: 14px;}}
                                                    QLabel:selected {{
                                                        border-radius: 10px;
                                                        border: 1px solid rgb(0, 170, 255);
                                                    }}
                                                    QLabel:selected:!active {{
                                                        border-radius: 10px;
                                                        border: 1px solid transparent;
                                                    }}
                                                    QLabel:selected:active {{
                                                        border-radius: 10px;
                                                        border: 1px solid rgb(0, 170, 255);
                                                    }}
                                                    QLabel:hover {{
                                                        border-radius: 10px;
                                                        border: 1px solid rgb(0, 170, 255);}}""")
        self.setItemWidget(item, item.variable_name)

    def dragEnterEvent(self, event):
        mimeData = event.mimeData()
        if not mimeData.property('myItems'):
            event.ignore()
        else:
            event.acceptProposedAction()

    def dropEvent(self, event):
        # 获取拖放的items
        event.accept()
        items = event.mimeData().property('myItems')
        sender = event.mimeData().property('sender')
        if sender == self: return
        self.clear()
        for item in items:
            # 取出item里的data并生成item
            self.makeItem(item.data(Qt.UserRole + 1), item.type)
        if sender:
            if sender.objectName() != "listWidget":
                sender.clear()

    def mousePressEvent(self, event):
        # 列表框点击事件,用于设置框选工具的开始位置
        super(SingleListWidget, self).mousePressEvent(event)
        if event.buttons() != Qt.LeftButton or self.itemAt(event.pos()):
            return
        self._rubberPos = event.pos()
        self._rubberBand.setGeometry(QRect(self._rubberPos, QSize()))
        self._rubberBand.show()

    def mouseReleaseEvent(self, event):
        # 列表框点击释放事件,用于隐藏框选工具
        super(SingleListWidget, self).mouseReleaseEvent(event)
        self._rubberPos = None
        self._rubberBand.hide()

    def mouseMoveEvent(self, event):
        # 列表框鼠标移动事件,用于设置框选工具的矩形范围
        super(SingleListWidget, self).mouseMoveEvent(event)
        if self._rubberPos:
            pos = event.pos()
            lx, ly = self._rubberPos.x(), self._rubberPos.y()
            rx, ry = pos.x(), pos.y()
            size = QSize(abs(rx - lx), abs(ry - ly))
            self._rubberBand.setGeometry(
                QRect(QPoint(min(lx, rx), min(ly, ry)), size))


class RangeSlider(QWidget):
    valueChanged = pyqtSignal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.first_position = 1
        self.second_position = 8

        self.opt = QStyleOptionSlider()
        self.opt.minimum = 0
        self.opt.maximum = 10

        self.setTickPosition(QSlider.TicksAbove)
        self.setTickInterval(1)

        self.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed, QSizePolicy.Slider)
        )

    def setRangeLimit(self, minimum: float, maximum: float):
        self.opt.minimum = minimum
        self.opt.maximum = maximum

    def setRange(self, start: float, end: float):
        self.first_position = start
        self.second_position = end

    def getRange(self):
        return (self.first_position, self.second_position)

    def setTickPosition(self, position: QSlider.TickPosition):
        self.opt.tickPosition = position

    def setTickInterval(self, ti: float):
        self.opt.tickInterval = ti

    def paintEvent(self, event: QPaintEvent):

        painter = QPainter(self)

        # Draw rule
        self.opt.initFrom(self)
        self.opt.rect = self.rect()
        self.opt.sliderPosition = 0
        self.opt.subControls = QStyle.SC_SliderGroove | QStyle.SC_SliderTickmarks

        #   Draw GROOVE
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

        #  Draw INTERVAL

        color = self.palette().color(QPalette.Highlight)
        color.setAlpha(160)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)

        self.opt.sliderPosition = self.first_position
        x_left_handle = (
            self.style()
            .subControlRect(QStyle.CC_Slider, self.opt, QStyle.SC_SliderHandle)
            .right()
        )

        self.opt.sliderPosition = self.second_position
        x_right_handle = (
            self.style()
            .subControlRect(QStyle.CC_Slider, self.opt, QStyle.SC_SliderHandle)
            .left()
        )

        groove_rect = self.style().subControlRect(
            QStyle.CC_Slider, self.opt, QStyle.SC_SliderGroove
        )

        selection = QRect(
            x_left_handle,
            groove_rect.y(),
            x_right_handle - x_left_handle,
            groove_rect.height(),
        ).adjusted(-1, 1, 1, -1)

        painter.drawRect(selection)

        # Draw first handle

        self.opt.subControls = QStyle.SC_SliderHandle
        self.opt.sliderPosition = self.first_position
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

        # Draw second handle
        self.opt.sliderPosition = self.second_position
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

    def mousePressEvent(self, event: QMouseEvent):

        self.opt.sliderPosition = self.first_position
        self._first_sc = self.style().hitTestComplexControl(
            QStyle.CC_Slider, self.opt, event.pos(), self
        )

        self.opt.sliderPosition = self.second_position
        self._second_sc = self.style().hitTestComplexControl(
            QStyle.CC_Slider, self.opt, event.pos(), self
        )

    def mouseMoveEvent(self, event: QMouseEvent):

        distance = self.opt.maximum - self.opt.minimum

        pos = self.style().sliderValueFromPosition(
            0, distance, event.pos().x(), self.rect().width()
        )

        if self._first_sc == QStyle.SC_SliderHandle:
            if pos <= self.second_position:
                self.first_position = pos
                self.update()
                self.valueChanged.emit((self.first_position, self.second_position))
                return

        if self._second_sc == QStyle.SC_SliderHandle:
            if pos >= self.first_position:
                self.second_position = pos
                self.update()
                self.valueChanged.emit((self.first_position, self.second_position))

    def sizeHint(self):
        """ override """
        SliderLength = 84
        TickSpace = 5

        w = SliderLength
        h = self.style().pixelMetric(QStyle.PM_SliderThickness, self.opt, self)

        if (
            self.opt.tickPosition & QSlider.TicksAbove
            or self.opt.tickPosition & QSlider.TicksBelow
        ):
            h += TickSpace

        return (
            self.style()
            .sizeFromContents(QStyle.CT_Slider, self.opt, QSize(w, h), self)
            .expandedTo(QApplication.globalStrut())
        )


class RemovedListWidget(QListWidget):

    def __init__(self, dataframe, column_name, list_data, parent=None):
        super(RemovedListWidget, self).__init__(parent)
        self.dataframe = dataframe
        self.column_name = column_name
        self.setAcceptDrops(True)
        # 设置从左到右、自动换行、依次排列
        self.setFlow(self.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(self.Adjust)
        # item的间隔
        self.setSpacing(5)
        # 创建item
        for item in list_data:
            self.addItem(str(item))

    def addItem(self, text):
        font_ = self.font()
        length = QFontMetrics(QFont(font_.family(), font_.pointSize())).width(text)
        height = QFontMetrics(QFont(font_.family(), font_.pointSize())).height()
        size_all = QSize(length + 45, height + 13)
        size_btn = QSize(length + 20, height + 10)
        item = QListWidgetItem(self)
        item.setSizeHint(size_all)
        item.widget = QWidget(self)
        item.horizontalLayout = QHBoxLayout(item.widget)
        item.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        item.horizontalLayout.setSpacing(0)
        item.pushButton = QPushButton(item.widget)
        item.pushButton.setText(text)
        item.pushButton.resize(size_btn)
        item.horizontalLayout.addWidget(item.pushButton)
        item.rmvbutton = QToolButton(item.widget)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/btn_close.png"), QIcon.Normal, QIcon.Off)
        item.rmvbutton.setIcon(icon)
        item.rmvbutton.setAutoRaise(True)
        item.rmvbutton.clicked.connect(lambda : self.takeItem(self.row(item)))
        item.horizontalLayout.addWidget(item.rmvbutton)
        self.setItemWidget(item, item.widget)

    def getAllItemsText(self):
        return [self.item(row).pushButton.text() for row in range(self.count())]

class MyCopiedTableView(QTableView):

    def __init__(self, parent=None):
        super(MyCopiedTableView, self).__init__(parent)
        self.setStyleSheet("QTableView::item:selected {background: #a6e4ff; color: black; border: 0px;}")
        # self.resize(800, 600)
        # self.setContextMenuPolicy(Qt.ActionsContextMenu)# 右键菜单
        # self.setEditTriggers(self.NoEditTriggers)# 禁止编辑
        # self.addAction(QAction("复制", self, triggered=self.copyData))
        # self.myModel = QStandardItemModel()# model
        # self.setModel(self.myModel)

    def keyPressEvent(self, event):
        super(MyCopiedTableView, self).keyPressEvent(event)
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

def showERROR():
    errmsg = traceback.format_exc()
    QMessageBox.warning(QWidget(), '请确认', errmsg,
                        QMessageBox.Ok)
