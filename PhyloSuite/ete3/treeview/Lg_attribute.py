
import os

from ete3.treeview.CustomWidgets import MyAttributeTableModel, MyCompareTableModel, QGraphicsBottomTriangleItem, \
    QGraphicsDiamondItem, \
    QGraphicsLeftArrowItem, \
    QGraphicsLeftTriangleItem, QGraphicsRightArrowItem, QGraphicsRightTriangleItem, QGraphicsRoundRectItem, \
    QGraphicsTopTriangleItem
from ete3.treeview.Ui_compare_setting import Ui_compare_tree_setting
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.factory import Factory
from .Ui_annotation_editor_attr import Ui_annotation_editor_attr
from .. import Tree

class Lg_attribute(QDialog, Ui_annotation_editor_attr, object):

    def __init__(self, parent=None):
        super(Lg_attribute, self).__init__(parent)
        self.parent_ = parent.parent()
        self.setupUi(parent)
        self.dict_map = {"Support": "support",
                         "Branch length": "dist",
                         "Name": "name"}
        self.comboBox.currentTextChanged.connect(self.switch_attribute)
        self.checkBox_2.toggled.connect(self.change_leaves)
        # font
        self.set_font_text(self.lineEdit_5, QFont("Arial", 12, QFont.Normal))
        self.lineEdit_5.clicked.connect(self.set_font)
        # text color
        self.pushButton_color.setStyleSheet("background-color:#000000")
        self.pushButton_color.setText("#000000")
        self.pushButton_color.clicked.connect(self.changePbColor)
        # shape fill color
        self.pushButton_color_2.setStyleSheet("background-color:#e34c00")
        self.pushButton_color_2.setText("#e34c00")
        self.pushButton_color_2.clicked.connect(self.changePbColor)
        # border color
        self.pushButton_color_3.setStyleSheet("background-color:#e34c00")
        self.pushButton_color_3.setText("#e34c00")
        self.pushButton_color_3.clicked.connect(self.changePbColor)
        self.groupBox.toggled.connect(lambda bool_: self.groupBox_2.setChecked(not bool_))
        self.groupBox_2.toggled.connect(lambda bool_: self.groupBox.setChecked(not bool_))
        # shape
        self.init_shapes()
        self.groupBox_2.toggled.connect(self.judge_attribute)
        # decimal
        self.spinBox.valueChanged.connect(self.change_value_decimal)
        # delete button
        self.pushButton_2.clicked.connect(self.on_pushButton_2_clicked)
        # list removed node ID
        self.list_removed_node_IDs = []

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        delete row
        """
        indices = self.tableView.selectedIndexes()
        if not indices:
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>Please select row(s) in the \"Atributes\" table first!</p>")
            return
        currentModel = self.tableView.model()
        if currentModel and indices:
            currentData = currentModel.arraydata
            rows = sorted(set(index.row() for index in indices), reverse=True)
            for row in rows:
                currentModel.layoutAboutToBeChanged.emit()
                self.list_removed_node_IDs.append(currentData.pop(row)[0])
                currentModel.layoutChanged.emit()

    def switch_attribute(self, text, decimal=None):
        header = ["Node ID", text]
        array = []
        for node in self.parent_.scene.tree.traverse():
            if node.id in self.list_removed_node_IDs:
                continue
            if decimal and type(getattr(node, self.dict_map[text])) != str:
                value = f"{getattr(node, self.dict_map[text]):.{decimal}f}"
            elif type(getattr(node, self.dict_map[text])) != str:
                value = str(getattr(node, self.dict_map[text])).rstrip('0').rstrip('.') # trim zeros
            else:
                value = getattr(node, self.dict_map[text])
            if node.is_leaf():
                if self.checkBox_2.isChecked():
                    array.append([node.id, value])
            else:
                array.append([node.id, value])
        model = MyAttributeTableModel(array, header, parent=self.tableView)
        self.tableView.setModel(model)
        self.update_range()

    def update_range(self):
        list_values = [float(row[1]) for row in self.tableView.model().arraydata if row[1].lstrip('-').replace('.','',1).isdigit()]
        if not list_values:
            return
        decimals = max([len(str(i).split(".")[1]) for i in list_values])
        if list_values:
            self.doubleSpinBox.setDecimals(decimals)
            self.doubleSpinBox.setValue(min(list_values))
            self.doubleSpinBox_2.setDecimals(decimals)
            self.doubleSpinBox_2.setValue(max(list_values))

    def change_leaves(self, bool_):
        if bool_:
            array = []
            for node in self.parent_.scene.tree.traverse():
                if node.is_leaf():
                    array.append([node.id, getattr(node, self.dict_map[self.comboBox.currentText()])])
            self.tableView.model().arraydata = self.tableView.model().arraydata + array
            self.tableView.model().layoutChanged.emit()
        else:
            leaf_ids = [node.id for node in self.parent_.scene.tree.traverse() if node.is_leaf()]
            new_array = [row for row in self.tableView.model().arraydata if row[0] not in leaf_ids]
            self.tableView.model().arraydata = new_array
            self.tableView.model().layoutChanged.emit()

    def set_font(self):
        line_editor = self.sender()
        font, ok = QFontDialog.getFont(line_editor.font_, self)
        if ok:
            self.set_font_text(self.sender(), font)

    def set_font_text(self, lineedit, font):
        family_ = font.family()
        size_ = str(font.pointSize())
        italic = "italic, " if font.italic() else ""
        bold = "bold, " if font.bold() else ""
        lineedit.setText(f"{family_}, {italic}{bold}{size_}")
        lineedit.font_ = font

    def changePbColor(self):
        button = self.sender()
        ini_color = button.palette().color(1)
        color = QColorDialog.getColor(QColor(ini_color), self)
        if color.isValid():
            button.setText(color.name())
            button.setStyleSheet("background-color:%s"%color.name())

    def init_shapes(self):
        dict_icon = {
                    "star2": ":/shape/resourses/shape/star2.svg",
                    "circle": ":/shape/resourses/shape/circle.svg",
                    "star": ":/shape/resourses/shape/star.svg",
                     "rectangle": ":/shape/resourses/shape/rectangle.svg",
                     "round corner rectangle": ":/shape/resourses/shape/round_rect.svg",
                     "diamond": ":/shape/resourses/shape/diamond.svg",
                     "left arrow": ":/shape/resourses/shape/left_arrow.svg",
                     "right arrow": ":/shape/resourses/shape/right_arrow.svg",
                     "left triangle": ":/shape/resourses/shape/left_tri.svg",
                     "right triangle": ":/shape/resourses/shape/right_tri.svg",
                     "top trangle": ":/shape/resourses/shape/top_tri.svg",
                     "bottom triangle": ":/shape/resourses/shape/bottom_tri.svg"}
        model = QStandardItemModel()
        for i in dict_icon.keys():
            item = QStandardItem(i)
            icon = dict_icon[i] if i in dict_icon else None
            item.setIcon(QIcon(icon))
            font = item.font()
            font.setPointSize(13)
            item.setFont(font)
            model.appendRow(item)
        self.comboBox_2.setModel(model)

    def get_parameters(self):
        dict_args = {}
        dict_args["range"] = (self.doubleSpinBox.value(), self.doubleSpinBox_2.value())
        dict_args["text color"] = self.pushButton_color.palette().color(1)
        dict_args["text font"] = self.lineEdit_5.font_
        dict_args["display as %"] = self.checkBox.isChecked()
        dict_args["display as"] = "text" if self.groupBox.isChecked() else "shape"
        dict_args["shape"] = self.comboBox_2.currentText()
        dict_args["shape fill color"] = self.pushButton_color_2.palette().color(1)
        dict_args["shape border color"] = self.pushButton_color_3.palette().color(1)
        dict_args["shape border size"] = self.doubleSpinBox_4.value()
        dict_args["shape max size"] = self.doubleSpinBox_3.value()
        dict_args["shape min size"] = self.doubleSpinBox_5.value()
        dict_args["current attribute"] = self.comboBox.currentText()
        return dict_args

    def resume_GUI(self, dict_args):
        if ("range" in dict_args) and dict_args["range"]:
            self.doubleSpinBox.setValue(dict_args["range"][0])
            self.doubleSpinBox_2.setValue(dict_args["range"][1])
        if ("text color" in dict_args) and dict_args["text color"]:
            self.pushButton_color.setText(dict_args["text color"].name())
            self.pushButton_color.setStyleSheet("background-color:%s"%dict_args["text color"].name())
        if ("text font" in dict_args) and dict_args["text font"]:
            self.set_font_text(self.lineEdit_5, dict_args["text font"])
        if ("display as %" in dict_args) and dict_args["display as %"]:
            self.checkBox.setChecked(dict_args["display as %"])
        if ("display as" in dict_args) and dict_args["display as"]:
            if dict_args["display as"] == "text":
                self.groupBox.setChecked(True)
            elif dict_args["display as"] == "shape":
                self.groupBox_2.setChecked(True)
        if ("shape" in dict_args) and dict_args["shape"]:
            self.comboBox_2.setCurrentText(dict_args["shape"])
        if ("shape fill color" in dict_args) and dict_args["shape fill color"]:
            self.pushButton_color_2.setText(dict_args["shape fill color"].name())
            self.pushButton_color_2.setStyleSheet("background-color:%s"%dict_args["shape fill color"].name())
        if ("shape border color" in dict_args) and dict_args["shape border color"]:
            self.pushButton_color_3.setText(dict_args["shape border color"].name())
            self.pushButton_color_3.setStyleSheet("background-color:%s"%dict_args["shape border color"].name())
        if ("shape border size" in dict_args) and dict_args["shape border size"]:
            self.doubleSpinBox_4.setValue(dict_args["shape border size"])
        if ("shape max size" in dict_args) and dict_args["shape max size"]:
            self.doubleSpinBox_3.setValue(dict_args["shape max size"])
        if ("shape min size" in dict_args) and dict_args["shape min size"]:
            self.doubleSpinBox_5.setValue(dict_args["shape min size"])
        if ("current attribute" in dict_args) and dict_args["current attribute"]:
            self.comboBox.setCurrentText(dict_args["current attribute"])

    def change_value_decimal(self, value):
        self.switch_attribute(self.comboBox.currentText(), value)

    def judge_attribute(self, bool_):
        if bool_ and self.comboBox.currentText() == "Name":
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>\"Name\" canot be drawn as shape!</p>")
            self.groupBox_2.setChecked(False)

    def update_(self):
        self.switch_attribute(self.comboBox.currentText(), decimal=self.spinBox.value())

