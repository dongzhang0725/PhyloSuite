
import os

from ete3.treeview.CustomWidgets import MyCompareTableModel, QGraphicsBottomTriangleItem, QGraphicsDiamondItem, \
    QGraphicsLeftArrowItem, \
    QGraphicsLeftTriangleItem, QGraphicsRightArrowItem, QGraphicsRightTriangleItem, QGraphicsRoundRectItem, \
    QGraphicsStarItem, QGraphicsStarItem2, QGraphicsTopTriangleItem
from ete3.treeview.Ui_compare_setting import Ui_compare_tree_setting
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.factory import Factory
from .. import Tree

class Lg_compare_tree_setting(QDialog, Ui_compare_tree_setting, object):

    def __init__(self, parent=None):
        super(Lg_compare_tree_setting, self).__init__(parent)
        self.setupUi(self)
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.color_settings = QSettings(
            self.thisPath +
            '/settings/color_sets.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.color_settings.setFallbacksEnabled(False)
        self.init_color_set()
        self.comboBox.currentTextChanged.connect(lambda text: [self.model.refresh_colors()
                                                               if hasattr(self, "model") and text != ">>>More<<<" else print,
                                                               self.get_more_colors(text)])
        self.tableView.parent = self
        # self.init_combobox()
        self.lineEdit.installEventFilter(self)
        self.lineEdit_2.installEventFilter(self)
        self.lineEdit_3.installEventFilter(self)
        self.set_font_text(self.lineEdit_5, QFont("Arial", 12, QFont.Normal))
        self.lineEdit_5.clicked.connect(self.set_font)
        self.set_font_text(self.lineEdit_6, QFont("Arial", 9, QFont.Normal))
        self.lineEdit_6.clicked.connect(self.set_font)
        self.toolBox.setMinimumHeight(200)
        self.splitter.setStretchFactor(0, 20)
        self.splitter.setStretchFactor(1, 1)

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

    # def init_combobox(self):
    #     dict_icon = {"circle": ":/shape/resourses/shape/circle.svg",
    #                  "rectangle": ":/shape/resourses/shape/rectangle.svg",
    #                  "round corner rectangle": ":/shape/resourses/shape/round_rect.svg",
    #                  "diamond": ":/shape/resourses/shape/diamond.svg",
    #                  "left arrow": ":/shape/resourses/shape/left_arrow.svg",
    #                  "right arrow": ":/shape/resourses/shape/right_arrow.svg",
    #                  "left triangle": ":/shape/resourses/shape/left_tri.svg",
    #                  "right triangle": ":/shape/resourses/shape/right_tri.svg",
    #                  "top trangle": ":/shape/resourses/shape/top_tri.svg",
    #                  "bottom triangle": ":/shape/resourses/shape/bottom_tri.svg"}
    #     model = QStandardItemModel()
    #     for i in dict_icon.keys():
    #         item = QStandardItem(i)
    #         icon = dict_icon[i] if i in dict_icon else None
    #         item.setIcon(QIcon(icon))
    #         font = item.font()
    #         font.setPointSize(13)
    #         item.setFont(font)
    #         model.appendRow(item)
    #     self.comboBox_2.setModel(model)

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        open tree 1
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input tree file1")
        # fileName = [r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\myWorkPlace\GenBank_File\test_extract\trees\coevolution\finch_host.nwk"]
        if fileName[0]:
            self.input_tree(fileName[0], self.lineEdit, mode="tre1")

    @pyqtSlot()
    def on_pushButton_22_clicked(self):
        """
        open tree 2
        """
        fileName = QFileDialog.getOpenFileName(
            self, "Input tree file2")
        # fileName = [r"E:\F\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\myWorkPlace\GenBank_File\test_extract\trees\coevolution\parasite.nwk"]
        if fileName[0]:
            self.input_tree(fileName[0], self.lineEdit_2, mode="tre2")

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        """
        open connection file
        """
        if not hasattr(self, "tre1") and not hasattr(self, "tre2"):
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>Please input trees first!</p>")
            return
        fileName = QFileDialog.getOpenFileName(
            self, "Input connection file")
        if fileName[0]:
            self.input_connection(fileName[0])

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        """
        delete row
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
    def on_pushButton_6_clicked(self):
        """
        add row
        """
        currentModel = self.tableView.model()
        if currentModel:
            currentData = currentModel.arraydata
            currentModel.layoutAboutToBeChanged.emit()
            length = len(currentData[0])
            shape = ["circle", "rectangle", "star", "star2",
                     "round corner rectangle",
                     "right triangle", "left triangle",
                     "top trangle", "bottom triangle", "diamond",
                     "line", "left arrow", "right arrow"]
            currentData.append([""] * (length-2)+[shape, shape])
            currentModel.layoutChanged.emit()
            self.tableView.scrollToBottom()

    def init_table(self, tree, mode="tre1"):
        header = ["Tree1 names", "Tree2 names", "Group", "Tree1 shape", "Tree2 shape"]
        array = []
        for node in tree.traverse():
            if node.is_leaf():
                if mode == "tre1":
                    array.append([node.name, "", "", ["None", "circle", "rectangle", "star", "star2",
                                                      "round corner rectangle",
                                                      "right triangle", "left triangle",
                                                      "top trangle", "bottom triangle", "diamond",
                                                      "line", "left arrow", "right arrow"],
                                                      ["None", "circle", "rectangle", "star", "star2",
                                                       "round corner rectangle",
                                                       "right triangle", "left triangle",
                                                       "top trangle", "bottom triangle", "diamond",
                                                       "line", "left arrow", "right arrow"]])
                elif mode == "tre2":
                    array.append(["", node.name, "", ["None", "circle", "rectangle", "star", "star2",
                                                      "round corner rectangle",
                                                      "right triangle", "left triangle",
                                                      "top trangle", "bottom triangle", "diamond",
                                                      "line", "left arrow", "right arrow"],
                                                      ["None", "circle", "rectangle", "star", "star2",
                                                       "round corner rectangle",
                                                       "right triangle", "left triangle",
                                                       "top trangle", "bottom triangle", "diamond",
                                                       "line", "left arrow", "right arrow"]])
        self.model = MyCompareTableModel(array, header, parent=self.tableView)
        self.tableView.setModel(self.model)

    def init_color_set(self):
        self.color_sets = self.color_settings.value("PhyloSuite colors")
        items = list(self.color_sets.keys()) + [">>>More<<<"]
        self.comboBox.addItems(items)

    def get_more_colors(self, text):
        if text == ">>>More<<<":
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>After editing colors, you may need to reopen the window!</p>")
            self.parent().parent().on_colorsets_triggered()
            self.comboBox.setCurrentIndex(0)

    def input_tree(self, treefile, lineEdit, mode="tre1"):
        # test all format and quoted_node_names = True
        flag = False
        for format in list(range(10)) + [100]:
            try:
                tre = Tree(treefile, format=format)
                flag=True
                break
            except: pass
            try:
                tre = Tree(treefile, format=format, quoted_node_names=True)
                flag=True
                break
            except: pass
        if not flag:
            QMessageBox.information(
                self,
                "Import tree",
                "<p style='line-height:25px; height:25px'>Tree imported failed, please check the format!</p>")
            return None
        lineEdit.setText(os.path.basename(treefile))
        lineEdit.setToolTip(treefile)
        if mode == "tre1":
            self.tre1 = self.assign_ID(tre)
            self.list_tre1_leaves = []
            for node in self.tre1.traverse():
                if node.is_leaf():
                    self.list_tre1_leaves.append(node.id)
                node.add_feature("parent", "tree1")
            # self.list_tre1_leaves = [node.id for node in self.tre1.traverse() if node.is_leaf()]
            # if not hasattr(self, "model"):
            #     self.init_table(self.tre1, mode="tre1")
            # else:
            #     list_leaves = [node.name for node in self.tre1.traverse() if node.is_leaf()]
            #     for row in range(len(self.model.arraydata)):
            #         if self.model.arraydata[row][1] in list_leaves:
            #             list_leaves.remove(self.model.arraydata[row][1])
            #             self.model.arraydata[row][0] = self.model.arraydata[row][1]
            #     if list_leaves:
            #         for name in list_leaves:
            #             self.model.arraydata.append([name, "", ""])
            #     self.model.layoutChanged.emit()
        elif mode == "tre2":
            self.tre2 = self.assign_ID(tre)
            self.list_tre2_leaves = []
            for node in self.tre2.traverse():
                if node.is_leaf():
                    self.list_tre2_leaves.append(node.id)
                node.add_feature("parent", "tree2")

            # self.tre2.marker = "tree2"
            # self.list_tre2_leaves = [node.id for node in self.tre2.traverse() if node.is_leaf()]
            # if not hasattr(self, "model"):
            #     self.init_table(self.tre2, mode="tre2")
            # else:
            #     list_leaves = [node.name for node in self.tre2.traverse() if node.is_leaf()]
            #     for row in range(len(self.model.arraydata)):
            #         if self.model.arraydata[row][0] in list_leaves:
            #             list_leaves.remove(self.model.arraydata[row][0])
            #             self.model.arraydata[row][1] = self.model.arraydata[row][0]
            #     if list_leaves:
            #         for name in list_leaves:
            #             self.model.arraydata.append(["", name, ""])
            #     self.model.layoutChanged.emit()
        if hasattr(self, "list_tre1_leaves") and hasattr(self, "list_tre2_leaves"):
            list_shapes = ["circle", "rectangle", "star", "star2", "round corner rectangle",
                           "right triangle", "left triangle",
                           "top trangle", "bottom triangle", "diamond",
                           "line", "left arrow", "right arrow"]
            intersect = list(set(self.list_tre1_leaves).intersection(set(self.list_tre2_leaves)))
            if intersect:
                header = ["Tree1 names", "Tree2 names", "Group", "Tree1 shape", "Tree2 shape"]
                array = []
                for name in intersect:
                    array.append([name, name, "", list_shapes, list_shapes])
                self.model = MyCompareTableModel(array, header, parent=self.tableView)
                self.tableView.setModel(self.model)
        return tre

    def input_connection(self, file):


        self.lineEdit_3.setText(os.path.basename(file))
        self.lineEdit_3.setToolTip(file)
        with open(file) as f:
            content = f.read()
        # self.dict_mapping1 = {}
        # self.dict_mapping2 = {}
        list_shapes = ["circle", "rectangle", "star", "star2", "round corner rectangle",
                       "right triangle", "left triangle",
                       "top trangle", "bottom triangle", "diamond",
                       "line", "left arrow", "right arrow"]
        array = []
        for i in content.split("\n"):
            i = i.replace(":", "\t")
            list_i = i.split("\t")
            tre1_shape = None
            tre2_shape = None
            if len(list_i) == 2:
                name1, name2, group = list_i[0].strip(), list_i[1].strip(), ""
            elif len(list_i) == 3:
                name1, name2, group = list_i[0].strip(), list_i[1].strip(), list_i[2].strip()
            elif len(list_i) == 4:
                name1, name2, group, tre1_shape = list_i[0].strip(), list_i[1].strip(), list_i[2].strip(), list_i[3].strip()
            elif len(list_i) == 5:
                name1, name2, group, tre1_shape, tre2_shape = list_i[0].strip(), list_i[1].strip(), \
                                                              list_i[2].strip(), list_i[3].strip(), list_i[4].strip()
            else:
                name1, name2, group = None, None, ""
            list_shape1 = [list_shapes[list_shapes.index(tre1_shape)]] + \
                          list_shapes[:list_shapes.index(tre1_shape)] + \
                          list_shapes[list_shapes.index(tre1_shape)+1:] if (tre1_shape and tre1_shape in list_shapes) \
                                    else list_shapes
            list_shape2 = [list_shapes[list_shapes.index(tre2_shape)]] + \
                          list_shapes[:list_shapes.index(tre2_shape)] + \
                          list_shapes[list_shapes.index(tre2_shape)+1:] if (tre2_shape and tre2_shape in list_shapes) \
                                    else list_shapes
            if (name1 in self.list_tre1_leaves) and (name2 in self.list_tre2_leaves):
                array.append([name1, name2, group, list_shape1, list_shape2])
            elif (name2 in self.list_tre1_leaves) and (name1 in self.list_tre2_leaves):
                array.append([name2, name1, group, list_shape1, list_shape2])
                # self.dict_mapping1[list_i[0].strip()] = list_i[1].strip()
                # self.dict_mapping2[list_i[1].strip()] = list_i[0].strip()
        if array:
            # if not hasattr(self, "model"):
            header = ["Tree1 names", "Tree2 names", "Group", "Tree1 shape", "Tree2 shape"]
            self.model = MyCompareTableModel(array, header, parent=self.tableView)
            self.tableView.setModel(self.model)
            # else:
            #     list_ = [[i[0], i[1]] for i in self.model.arraydata]
            #     for i in array:
            #         if i not in list_:
            #             self.model.arraydata.append(i)
            #     # self.model.arraydata.extend(array)
            #     self.model.layoutChanged.emit()

        # # get all IDs of tree1
        # list_tre1_IDs = [row[0] for row in self.model.arraydata if row[0]]
        # list_tre2_IDs = [row[1] for row in self.model.arraydata if row[1]]
        # # read tre1
        # list_connected_ids = []
        # list_rm_IDs = []
        # for row in range(len(self.model.arraydata)):
        #     list_row = self.model.arraydata[row]
        #     node_id = list_row[0]
        #     node_id2 = list_row[1]
        #     if node_id in self.dict_mapping1 and (self.dict_mapping1[node_id] in list_tre2_IDs):
        #         self.model.arraydata[row][1] = self.dict_mapping1[node_id]
        #         list_connected_ids.append(self.dict_mapping1[node_id])
        #     elif node_id in self.dict_mapping2 and (self.dict_mapping2[node_id] in list_tre2_IDs):
        #         self.model.arraydata[row][1] = self.dict_mapping2[node_id]
        #         list_connected_ids.append(self.dict_mapping2[node_id])
        #     # delete tre2 IDs if has been connected
        #     if node_id2 and (node_id2 in list_connected_ids) and (not node_id):
        #         list_rm_IDs.append(row)
        # for row in reversed(sorted(list_rm_IDs)):
        #     self.model.arraydata.pop(row)
        # self.model.layoutChanged.emit()
        # # READ tre2
        # list_connected_ids = []
        # list_rm_IDs = []
        # for row in reversed(range(len(self.model.arraydata))):
        #     list_row = self.model.arraydata[row]
        #     node_id = list_row[1]
        #     node_id1 = list_row[0]
        #     if node_id and node_id1:
        #         continue
        #     if node_id in self.dict_mapping1 and (self.dict_mapping1[node_id] in list_tre1_IDs):
        #         self.model.arraydata[row][0] = self.dict_mapping1[node_id]
        #         list_connected_ids.append(self.dict_mapping1[node_id])
        #     elif node_id in self.dict_mapping2 and (self.dict_mapping2[node_id] in list_tre1_IDs):
        #         self.model.arraydata[row][0] = self.dict_mapping2[node_id]
        #         list_connected_ids.append(self.dict_mapping2[node_id])
        #     # delete tre1 IDs if has been connected
        #     if node_id1 and (node_id1 in list_connected_ids) and (not node_id):
        #         list_rm_IDs.append(row)
        # for row in reversed(sorted(list_rm_IDs)):
        #     self.model.arraydata.pop(row)
        # self.model.layoutChanged.emit()

    def get_color_set(self):
        return self.color_sets[self.comboBox.currentText()]

    def get_parameters(self):
        dict_args = {}
        if hasattr(self, "tre1") and hasattr(self, "tre2") and hasattr(self, "model"):
            dict_args["tree1"] = self.tre1
            dict_args["tree2"] = self.tre2
            dict_args["tree1 file"] = self.lineEdit.toolTip()
            dict_args["tree2 file"] = self.lineEdit_2.toolTip()
            dict_args["connection file"] = self.lineEdit_3.toolTip()
            dict_args["connection array"] = self.model.arraydata
            dict_args["connection header"] = self.model.header
            dict_args["h_line_len"] = self.doubleSpinBox.value()
            dict_args["margin"] = self.doubleSpinBox_2.value()
            dict_args["line_width"] = self.doubleSpinBox_3.value()
            dict_args["space"] = self.doubleSpinBox_4.value()
            # shape
            dict_args["draw_shape"] = self.checkBox.isChecked()
            dict_args["color set"] = self.comboBox.currentText()
            dict_shape = {"circle": QGraphicsEllipseItem,
                          "rectangle": QGraphicsRectItem,
                          "round corner rectangle": QGraphicsRoundRectItem,
                          "diamond": QGraphicsDiamondItem,
                          "star": QGraphicsStarItem,
                          "star2": QGraphicsStarItem2,
                          "left arrow": QGraphicsLeftArrowItem,
                          "right arrow": QGraphicsRightArrowItem,
                          "left triangle": QGraphicsLeftTriangleItem,
                          "right triangle": QGraphicsRightTriangleItem,
                          "top trangle": QGraphicsTopTriangleItem,
                          "bottom triangle": QGraphicsBottomTriangleItem}
            dict_args["dict_shape"] = dict_shape
            # dict_args["shape name"] = self.comboBox_2.currentText()
            # dict_args["shape"] = dict_shape[self.comboBox_2.currentText()]
            dict_args["shape width"] = self.doubleSpinBox_5.value()
            dict_args["shape height"] = self.doubleSpinBox_6.value()
            dict_args["draw legend"] = self.checkBox_2.isChecked()
            dict_args["legend title"] = self.lineEdit_4.text()
            dict_args["title font"] = self.lineEdit_5.font_
            dict_args["text font"] = self.lineEdit_6.font_
            dict_args["box margin"] = self.doubleSpinBox_7.value()
            dict_args["line width"] = self.doubleSpinBox_8.value()
            # color
            dict_args["color set name"] = self.comboBox.currentText()
            dict_args["dict_group_colors"] = self.model.get_colors()
            dict_args["list_groups"] = list(dict_args["dict_group_colors"].keys())
        return dict_args

    def resume_GUI(self, dict_args):
        if dict_args["tree1 file"]:
            self.input_tree(dict_args["tree1 file"], self.lineEdit, mode="tre1")
        if dict_args["tree2 file"]:
            self.input_tree(dict_args["tree2 file"], self.lineEdit_2, mode="tre2")
        if dict_args["connection file"]:
            self.input_connection(dict_args["connection file"])
        self.comboBox.setCurrentText(dict_args["color set"])
        self.model = MyCompareTableModel(dict_args["connection array"],
                                            dict_args["connection header"],
                                            parent=self.tableView)
        self.tableView.setModel(self.model)
        self.doubleSpinBox.setValue(dict_args["h_line_len"])
        self.doubleSpinBox_2.setValue(dict_args["margin"])
        self.doubleSpinBox_3.setValue(dict_args["line_width"])
        self.doubleSpinBox_4.setValue(dict_args["space"])
        # shape
        self.checkBox.setChecked(dict_args["draw_shape"])
        self.doubleSpinBox_5.setValue(dict_args["shape width"])
        self.doubleSpinBox_6.setValue(dict_args["shape height"])
        # legend
        self.checkBox_2.setChecked(dict_args["draw legend"])
        self.lineEdit_4.setText(dict_args["legend title"])
        self.set_font_text(self.lineEdit_5, dict_args["title font"])
        self.set_font_text(self.lineEdit_6, dict_args["text font"])
        self.doubleSpinBox_7.setValue(dict_args["box margin"])
        self.doubleSpinBox_8.setValue(dict_args["line width"])
        # color
        self.comboBox.setCurrentText(dict_args["color set name"])

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        name = obj.objectName()
        if type(obj) in [QLineEdit]:
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                if name == "lineEdit":
                    self.input_tree(files[0], self.lineEdit, mode="tre1")
                elif name == "lineEdit_2":
                    self.input_tree(files[0], self.lineEdit_2, mode="tre2")
                elif name == "lineEdit_3":
                    if not hasattr(self, "tre1") and not hasattr(self, "tre2"):
                        QMessageBox.information(
                            self,
                            "PhyloSuite",
                            "<p style='line-height:25px; height:25px'>Please input trees first!</p>")
                    else:
                        self.input_connection(files[0])
        # 其他情况会返回系统默认的事件处理方法。
        return super(Lg_compare_tree_setting, self).eventFilter(obj, event)

    def assign_ID(self, tre):
        list_names = []
        for node in tre.traverse():
            if not hasattr(node, "id"):
                name = node.name if node.name else "node"
                suffix = "_" if node.name else ""
                new_name, list_names = self.factory.numbered_Name(list_names,
                                                                    name, omit=True, suffix=suffix)
                node.add_feature("id", new_name)
        return tre

