import copy
import io
import os
import inspect
import re
import signal
import sys

import matplotlib

from src.CustomWidget2 import MyNameTableModel, MyTaxTableModel, ListItemWidget, MyTableModel, MyStripTableModel
# from typing import re

from src.Lg_settings import Setting
from src.factory import Factory, WorkThread, Parsefmt, Convertfmt
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

import matplotlib.patches as patches
from matplotlib.gridspec import GridSpec
from matplotlib.figure import Figure
from matplotlib.offsetbox import (AnnotationBbox, DrawingArea, OffsetImage,
                                  TextArea)

from uifiles import Ui_annotation_selector2, Ui_annotation_editor_tax
from uifiles.Ui_annotation_editor import Ui_annotation_editor
from uifiles.Ui_annotation_selector2 import Ui_annotation_selector
from uifiles.Ui_treeview import Ui_TreeView
from src.PS_treeviz import PS_Treeviz
from src.preset_values import timescaleGeo

class TreeViewer(QMainWindow,Ui_TreeView,object):
    showSig = pyqtSignal(QMainWindow)
    closeSig = pyqtSignal(str, str)
    treeview_exception = pyqtSignal(str)
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QMainWindow)
    def __init__(
            self,
            workPath=None,
            focusSig=None,
            autoInput=None,
            parent=None):
        super(TreeViewer, self).__init__(parent)
        self.parent = parent
        # self.figure = TreeViz.plotfig(ax=None)
        # FigureCanvas.__init__(self, self.figure)
        self.function_name = "TreeViewer"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig

        self.datingTreeName = ''
        self.tv = None
        self.tree = None
        self.Phylotree = None
        self.width = None
        self.height = None
        self.figure = Figure()
        self.x_max = 0.00
        self.y_max = 0.00
        self.new_dict = {}
        self.container = []
        self.timescaleGeo = timescaleGeo
        self.lastx = 0
        self.lasty = 0
        self.press = False
        self.fileName = None

        self.fig = plt.figure()#figsize=(4, 3)
        # self.gs = GridSpec(2, 1, width_ratios=[4], height_ratios=[8, 2], hspace=0.05)
        # self.ax1 = self.figure.add_subplot(self.gs[0, 0])
        self.ax1 = self.figure.add_subplot(111)
        self.ax1.patch.set_edgecolor('black')
        self.ax1.patch.set_linewidth(1)
        '''self.ax2 = self.figure.add_subplot(self.gs[1, 0])
        self.ax2.yaxis.set_ticks([])
        self.ax1.xaxis.set_visible(False)
        self.ax1.yaxis.set_visible(False)
        self.ax2.yaxis.set_visible(False)'''
        '''for spine in self.ax1.spines.values():
            spine.set_visible(False)'''
        '''for spine in self.ax2.spines.values():
            spine.set_visible(False)'''
        self.ax1.xaxis.set_visible(False)
        self.ax1.yaxis.set_visible(False)
        # for spine2 in self.ax2.spines.values():
        #     spine2.set_visible(False)

        self.setupUi(self)
        # 设置比例
        self.splitter.setStretchFactor(0, 9)
        self.splitter.setStretchFactor(1, 1)
        self.splitter_2.setStretchFactor(0, 1)
        self.splitter_2.setStretchFactor(1, 3)

        # 把ui中的widget换成figurecanvas控件
        self.figureCanvas = FigureCanvas(self.figure)
        self.figureCanvas.setAcceptDrops(True)
        self.horizontalLayout.replaceWidget(self.widget, self.figureCanvas)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.figureCanvas.setSizePolicy(sizePolicy)
        # figure根据获取控件大小显示
        canvas_width, canvas_height = self.figureCanvas.get_width_height()
        self.figure.set_size_inches(canvas_width / self.figureCanvas.figure.dpi,
                                    canvas_height / self.figureCanvas.figure.dpi)

        self.toolBar = NavigationToolbar(self.figureCanvas, self)
        self.addToolBar(Qt.TopToolBarArea, self.toolBar)
        input_action = QAction(QIcon.fromTheme(':/picture/resourses/Open_folder_add_512px_1186192_easyicon.net.png'), 'Input', self)
        input_action.triggered.connect(self.on_pushButton_3_clicked)  # 连接点击事件
        self.pushButton_ciid.clicked.connect(self.copy_internal_node_ids)
        self.pushButton_clid.clicked.connect(self.copy_leaf_node_ids)
        actions = self.toolBar.actions()
        # 添加到最左边（第一个位置）
        self.toolBar.insertAction(actions[0], input_action)
        # print(canvas_width, canvas_height)

        # self.figure.set_size_inches(self.figureCanvas.get_width_height()[0] / 80.0,
        #                             self.figureCanvas.get_width_height()[1] / 80.0)
        # print(self.figureCanvas.get_width_height())
        # 添加右键菜单
        self.figureCanvas.setContextMenuPolicy(3)  # Qt.CustomContextMenu
        self.figureCanvas.customContextMenuRequested.connect(self.show_context_menu)

        self.TreeViewer_settings = QSettings(
            self.thisPath + '/settings/TreeViewer_settings.ini', QSettings.IniFormat)
        self.TreeViewer_settings.setFallbacksEnabled(False)
        self.qss_file = self.factory.set_qss(self)
        if autoInput:
            datingTree = autoInput
            self.input(datingTree)

        self.lineEdit.installEventFilter(self)
        self.figureCanvas.installEventFilter(self)
        # self.comboBox_3.currentIndexChanged.connect(self.on_checkbox_13_clicked)
        # self.checkBox_16.clicked.connect(self.on_checkbox_16_clicked)
        # self.checkBox_4.clicked.connect(self.on_checkbox_4_clicked)
        # self.comboBox_5.currentIndexChanged.connect(self.on_checkbox_13_clicked)
        self.pushButton.clicked.connect(self.update_view)
        self.doubleSpinBox.valueChanged.connect(self.setScales)
        self.doubleSpinBox_2.valueChanged.connect(self.setScales)
        self.doubleSpinBox_4.valueChanged.connect(self.changeConfidenceHeight)
        # self.checkBox_3.stateChanged.connectcd
        # self.checkBox_7.stateChanged.connect(self.ctrlBGRec)
        self.actionsave_as.triggered.connect(self.save_as)
        self.actionFit_The_Window.triggered.connect(self.fit_to_window)
        # self.horizontalSlider.valueChanged.connect(self.ctrlHscale)
        # self.horizontalSlider_2.valueChanged.connect(self.ctrlVscale)
        # self.figureCanvas.mpl_connect('pick_event', self.on_pick)
        self.figureCanvas.mpl_connect('motion_notify_event', self.on_hover)
        self.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.figure.canvas.mpl_connect('motion_notify_event', self.on_move)
        self.figure.canvas.mpl_connect('scroll_event', self.call_back)
        self.figure.canvas.mpl_connect('resize_event', self.auto_set_scale)
        # self.treeview_exception.connect(self.popup_log_exception)
        # self.lineEdit_3.clicked.connect(self.setFont)
        self.lineEdit_2.clicked.connect(self.setFont)
        self.doubleSpinBox_3.valueChanged.connect(self.changeLineWidth)
        # self.comboBox_6.activated[str].connect(self.changeLineType)
        self.listWidget.installEventFilter(self)
        self.listWidget.init_(self.stackedWidget, parent=self)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.guiRestore()
        # menu = QMenu(self)
        # menu.setToolTipsVisible(True)
        self.cmap = None
        self.time_unit = None
        self.xmin = 0
        self.ymax = 0
        self.ymin = 0
        self.top_left = None
        self.top_right = None
        self.top_top = None
        self.min_down = None
        self.original_xmin = None
        self.original_xmax = None
        self.original_ymin = None
        self.original_ymax = None
        self.hscale = None
        self.vscale = None
        self.dict_font_style = {0: "normal", 1: "italic", 2: "oblique"}
        self.dict_style = {"solid": "-", "dashed": "--",
                           "dashdot": "-.", "dotted": ":"}
        self.leaf_label_style = "normal"
        self.leaf_font_bold = False
        self.list_faces = []
        self.face_base_parameters = [
            ["space_factor_left", 0.05],
            ["border.type", ["solid", "dashed", "dotted"]],
            ["border.width", 0],
            ["border.color", "#000000"]
        ]

    def show_context_menu(self, event):
        context_menu = QMenu(self)

        # 添加菜单项
        action1 = context_menu.addAction("Reroot tree here")
        action2 = context_menu.addAction("Swap/rotate children")

        # 显示右键菜单
        action = context_menu.exec_(self.mapToGlobal(event))

        # 处理菜单项的点击事件
        if action == action1:
            # 设置根节点
            node_out = self.current_highlight.__dict__['tree_node']
            self.tv.tree.root_with_outgroup(node_out.name, outgroup_branch_length=node_out.branch_length/2)
            self.set_tree(self.tv.tree, phylo_tree=True)
        elif action == action2:
            node_out = self.current_highlight.__dict__['tree_node']
            if len(node_out) > 1:
                node_out.clades = node_out.clades[::-1]
                self.set_tree(self.tv.tree, phylo_tree=True)
        self.fit_to_window()

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Input tre file", filter="Newick Format(*.nwk *.newick *.tre *.trees);;")
        if file:
            self.datingTreeName = file
            # print(self.datingTreeName)
            self.input(self.datingTreeName)
            self.load_tree(self.datingTreeName)

    @pyqtSlot()
    def on_add_ann_btn_clicked(self):
        annotation_selector = QDialog(self)
        ui = Ui_annotation_selector2.Ui_annotation_selector()
        ui.setupUi(annotation_selector)
        ui.pushButton.clicked.connect(lambda : [self.create_annotation_editor(ui.comboBox.currentText()),
                                                annotation_selector.close()])
        annotation_selector.setWindowFlags(annotation_selector.windowFlags() | Qt.WindowMinMaxButtonsHint)
        annotation_selector.show()

    @pyqtSlot()
    def on_checkbox_13_clicked(self):
        if self.checkBox_13.isChecked():
            self.ctrlBGRec()
        else:
            self.ctrlBGRec()

    @pyqtSlot()
    def on_checkbox_16_clicked(self):
        if self.checkBox_16.isChecked():
            self.geo_eon()
            self.figure.canvas.draw_idle()
        else:
            self.geo_eon()
            self.figure.canvas.draw_idle()

    @pyqtSlot()
    def on_checkbox_4_clicked(self):
        if self.checkBox_4.isChecked():
            self.ctrlConfidenceRec(True)
        else:
            self.ctrlConfidenceRec(False)

    def input(self, file):
        self.fileName = file
        self.base = os.path.basename(file)
        self.lineEdit.setText(self.base)
        self.lineEdit.setToolTip(os.path.abspath(file))


    def save_as(self):
        if self.tv is not None:
            options = QFileDialog.Options()
            options |= QFileDialog.HideNameFilterDetails
            file_name, _ = QFileDialog.getSaveFileName(self, "Save As", "", "JPEG Files (*.jpg);;PNG Files (*.png);;SVG Files (*.svg);;PDF Files (*.pdf)",
                                                       options=options)
            if file_name:
                self.figure.savefig(file_name)
        else:
            QMessageBox.warning(self, "no file", "No tree file is imported, please input the treefile!")

    def update_view(self):
        self.new_dict = {}
        fileName = self.fileName
        if self.tv is not None:
            self.set_tree(fileName)
        return

    def load_tree(self, fileName=None):
        if fileName:
            self.choose_unit()
            # print(self.time_unit)
            self.set_tree(fileName)
            # self.height = 200 + self.tree * 10
            # self.fit_to_window()

    def choose_unit(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("TreeAnno")
        msg_box.setText("Please select the time unit!")
        checkbox_1MYA = msg_box.addButton("1MYA", QMessageBox.RejectRole)
        checkbox_1MYA.setMinimumHeight(100)  # 设置最小高度为50像素
        checkbox_1MYA.setCheckable(True)
        checkbox_100MYA = msg_box.addButton("100MYA", QMessageBox.RejectRole)
        checkbox_100MYA.setCheckable(True)
        layout = QVBoxLayout()
        layout.addWidget(checkbox_1MYA)
        layout.addWidget(checkbox_100MYA)
        widget = QWidget()
        widget.setLayout(layout)
        # 将 QWidget 添加到消息框的布局中
        msg_box.layout().addWidget(widget,3,1)
        msg_box.exec_()
        if msg_box.clickedButton() == checkbox_1MYA:
            self.time_unit = '1MYA'
        elif msg_box.clickedButton() == checkbox_100MYA:
            self.time_unit = '100MYA'

    def set_tree(self, tree, phylo_tree=False):
        self.ax1.clear()
        self.Phylotree = self.factory.read_tree_phylo(tree) if not phylo_tree else tree
        print(self.Phylotree)
        # leaf label
        family_, size_, style_bool, bold_bool  = self.font_prop_bytext(self.lineEdit_2.text())
        dict_leaf_label = {"size": int(size_),
                           "family": family_,
                           "style": "italic" if style_bool else "normal",
                           "fontweight": "bold" if bold_bool else "normal"}
        # line properties
        dict_line_prop = {"color": self.pushButton_color.text(),
                          "lw": self.doubleSpinBox_3.value()}
        self.tv = PS_Treeviz(self.Phylotree,
                             align_leaf_label=True,
                             leaf_label_dict=dict_leaf_label,
                             line_prop=dict_line_prop)
        # self.fit_to_window()
        self.figure = self.tv.plotfig(ax=self.ax1, fig_=self.figure)
        self.set_axis()
        self.draw_sticks()
        self.timescaleGeo = timescaleGeo
        self.time_divided()
        self.geo_eon()
        self.ctrlConfidenceRec()
        self.load_tree_nodes()
        self.ctrlBGRec()
        self.top_sticks()
        self.unit_anno()
        # self.figure.tight_layout()
        # self.ax1.autoscale(enable=True)
        self.figure.canvas.draw_idle()
        # fit to screen 只有在这里设置才能生效
        self.fit_to_window()
        # for i in self.ax1.patches:
        #     print(i.__dict__)
        # self.ax1.axis('on')  # 关闭坐标轴
        # self.ax1.grid(True)  # 关闭网格
        # xmin, xmax = self.tv.xlim
        # xmin = self.xmin if self.xmin!=0 else -0.005
        # self.ax1.set(xlim=(xmin-xmin*0.05, xmax+xmax*0.05))
        # self.ax1.axis('scaled') #this line fits your images to screen

    def auto_set_scale(self, size=None):
        a = self.figure.get_size_inches()
        self.doubleSpinBox_2.setValue(a[1])
        self.doubleSpinBox.setValue(a[0])

    def fit_to_window(self):
        # if hasattr(self, "original_xlim"):
        #     self.ax1.set(xlim=self.original_xlim)
        #     return self.original_xlim
        # else:
        # 会获取当前状态下的min和max值
        # xmin, xmax = self.tv.xlim
        # xmin = self.xmin if self.xmin!=0 else -0.005
        if self.original_xmin:
            xmin = self.original_xmin
        elif self.top_left:
            xmin = self.get_element_rect2(self.top_left).x0
            self.original_xmin = xmin
        else:
            xmin = self.xmin if self.xmin!=0 else -0.005

        if self.original_xmax and self.original_xmax > self.tv.max_tree_depth:
            xmax = self.original_xmax
        elif self.tv.top_right:
            xmax = self.get_element_rect2(self.tv.top_right).x1
            self.original_xmax = xmax
        else:
            xmax = self.tv.max_tree_depth

        xmin_ = xmin + xmin * 0.1
        xmax_ = xmax + xmax * 0.05

        if self.original_ymin:
            ymin = self.original_ymin
        elif self.min_down:
            ymin = self.get_element_rect2(self.min_down).y0
            self.original_ymin = ymin
        else:
            ymin = self.ymin

        if self.original_ymax:
            ymax = self.original_ymax
        elif self.top_top:
            ymax = self.get_element_rect2(self.top_top).y1
            self.original_ymax = ymax
        else:
            ymax = self.y_max

        ymin_ = ymin + ymin * 0.1
        ymax_ = ymax + ymax * 0.05

        self.ax1.set(xlim=(xmin_, xmax_))
        self.ax1.set(ylim=(ymin_, ymax_))
        # self.ax1.set(ylim=self.tv.ylim)
        # 轴范围
        # print(self.ax1.axis())
        self.auto_set_scale()
        return xmin_, xmax_, ymin_, ymax_

    def set_axis(self):
        self.ax1.set_xbound(self.tv.max_tree_depth, 0.0)
        #self.ax2.set_xbound(self.tv.max_tree_depth, 0.0)
        # print(self.tv.max_tree_depth)
        self.x_max = float(self.tv.max_tree_depth)
        self.y_max = float(self.ax1.get_ylim()[1])
        #self.ax2.yaxis.set_visible(False)
        #self.ax2.xaxis.set_ticks_position('top')
        '''self.ax1.set_ylim(-0.5,)
        self.ax1.axhline(-0.35, 0, 1, lw=1)
        # self.xticks_ax1 = self.ax1.get_xticks()
        # xticks_ax1_reversed = self.xticks_ax1[::-1]
        for x in self.xticks_ax1_reversed:
            self.ax1.axvline(x, -0.02, 0.015, lw=1)  # 调整 y 起始和终止值
            self.ax1.text(x, -0.6, f'{x:.2f}', ha='center', va='top', fontsize=8, color='black')

        self.ax2.set_ylim(-0.5)'''

    def draw_sticks(self):
        x = self.tv.max_tree_depth
        self.ax1.hlines(0.05, 0, x, linewidth=1.5, color='black')
        num_segments = 10
        segment_length = x / num_segments
        x_start = 0

        for i in range(num_segments + 1):
            xpos = i * segment_length
            self.ax1.vlines(xpos, 0.04, 0.20, linewidth=1.5, color='black')
            self.ax1.text(self.x_max - x_start - xpos, 0.21, f'{xpos:.2f}', ha='center', va='bottom', fontsize=9)

    def load_tree_nodes(self):

        if self.tv is not None:
            self.tableWidget.clear()
            # 定义节点颜色
            root_color = QColor(173, 216, 230)  # 浅蓝色 - 根节点
            internal_color = QColor(255, 255, 153)  # 浅黄色 - 内部节点
            leaf_color = QColor(144, 238, 144)  # 浅绿色 - 叶节点

            # 收集所有节点信息
            node_info = []  # 存储元组 (name, is_root, is_leaf, branch_length)

            # 首先识别根节点
            root_node = self.tv.tree.root
            for clade in self.tv.tree.find_clades():
                # 获取分支长度
                branch_length = str(clade.branch_length) if hasattr(clade,
                                                                    'branch_length') and clade.branch_length is not None else "None"

                # 确定节点类型
                is_leaf = clade.is_terminal()
                # 修正：只有根节点本身才是根节点
                is_root = (clade == root_node)

                # 设置节点名称
                if is_leaf:
                    name = clade.name if clade.name else f"Unnamed_Leaf_{len([n for n in node_info if n[2]]) + 1}"
                else:
                    name = clade.name if clade.name else f"Internal_{len([n for n in node_info if not n[2]]) + 1}"

                node_info.append((name, is_root, is_leaf, branch_length))

            # 设置表格
            self.tableWidget.setRowCount(len(node_info))
            self.tableWidget.setColumnCount(2)
            self.tableWidget.setHorizontalHeaderLabels(["Node Name", "Branch Length"])

            # 填充表格
            for row, (name, is_root, is_leaf, branch_length) in enumerate(node_info):
                # 节点名称列
                item = QTableWidgetItem(name)

                # 根据节点类型设置颜色
                if is_root:
                    color = root_color
                    tooltip = "Root node"
                elif is_leaf:
                    color = leaf_color
                    tooltip = "Leaf node"
                else:
                    color = internal_color
                    tooltip = "Internal node"

                item.setBackground(color)
                item.setToolTip(tooltip)
                self.tableWidget.setItem(row, 0, item)

                # 分支长度列
                bl_item = QTableWidgetItem(branch_length)
                bl_item.setBackground(color)  # 使用相同的颜色
                self.tableWidget.setItem(row, 1, bl_item)

    def copy_internal_node_ids(self):
        """拷贝所有内部节点的ID到剪贴板"""
        if self.tv is not None:
            internal_nodes = []
            for clade in self.tv.tree.find_clades():
                if not clade.is_terminal():  # 内部节点
                    name = clade.name if clade.name else f"Unnamed_Internal_{len(internal_nodes) + 1}"
                    internal_nodes.append(name)

            if internal_nodes:
                # 将内部节点ID用换行符连接
                text_to_copy = "\n".join(internal_nodes)
                clipboard = QApplication.clipboard()
                clipboard.setText(text_to_copy)
                QMessageBox.information(self, "Success", f"Copied {len(internal_nodes)} internal node IDs to clipboard")
            else:
                QMessageBox.warning(self, "Info", "No internal nodes found")

    def copy_leaf_node_ids(self):
        """拷贝所有叶子节点的ID到剪贴板"""
        if self.tv is not None:
            leaf_nodes = []
            for clade in self.tv.tree.find_clades():
                if clade.is_terminal():  # 叶子节点
                    name = clade.name if clade.name else f"Unnamed_Leaf_{len(leaf_nodes) + 1}"
                    leaf_nodes.append(name)

            if leaf_nodes:
                # 将叶子节点ID用换行符连接
                text_to_copy = "\n".join(leaf_nodes)
                clipboard = QApplication.clipboard()
                clipboard.setText(text_to_copy)
                QMessageBox.information(self, "Success", f"Copied {len(leaf_nodes)} leaf node IDs to clipboard")
            else:
                QMessageBox.warning(self, "Info", "No leaf nodes found")

    def ctrlConfidenceRec(self):
        rgx = re.compile(r"&95%HPD=\{([^,]*),\s*([^,]*)\}")
        # f_color = str(self.comboBox_5.currentText())
        f_color = self.pushButton_color_2.text()
        e_color = self.pushButton_color_3.text()
        rec_height = self.doubleSpinBox_4.value()
        print(self.tv.tree)
        if self.tv is not None:
            if self.checkBox_4.isChecked():
                # 树的所有内部节点
                for clade in self.tv.tree.find_clades(terminal=False):
                    group1 = [terminal_clade.name for terminal_clade in clade.get_terminals()]
                    # ter = clade.get_terminals()
                    # # 内部节点对应的所有叶子节点
                    # for terminal_clade in ter:
                    #     group1.append(terminal_clade.name)
                    flag = False
                    if clade.comment and isinstance(clade.comment, str):
                        match = rgx.search(clade.comment)
                        if match:
                            # 将匹配到的字符串分割为两个数值
                            hpd_min, hpd_max = map(float, match.groups())
                            # 置信区间差值作为矩形长度
                            hpd_diff = hpd_max - hpd_min
                            flag = True
                    if not flag:
                        continue
                    # 通过TreeViz获取group1叶子节点的内部节点
                    target_node_name = self.tv._search_target_node_name(group1)
                    group1 = []
                    # 获取group1内部节点坐标
                    x, y = self.tv.name2xy_right[target_node_name]
                    CI = hpd_diff
                    x = x - CI / 2
                    y = y - rec_height / 2
                    # rectangle = patches.Rectangle((x, y), CI, 0.15,
                    #                               edgecolor='#333333',
                    #                               facecolor=f_color)
                    rectangle = plt.Rectangle((x, y), CI, rec_height,
                                              edgecolor=e_color,
                                              facecolor=f_color)
                    rectangle.__dict__["type"] = "confidence"
                    self.ax1.add_patch(rectangle)
                    # self.figure.canvas.draw_idle()
                    bbox = self.get_element_rect(rectangle)
                    if self.xmin>bbox.x0:
                        self.xmin = bbox.x0
                        self.top_left = rectangle
                    # data_to_figure = self.ax1.transData.transform
                    # data_to_axes = lambda x: self.ax1.transAxes.inverted().transform(data_to_figure(x))
                    # print(data_to_axes(bbox))
            else:
                return
                # if self.CRcontainer:
                #     for rect in self.CRcontainer:
                #         rect.remove()
                #         self.figure.canvas.draw_idle()
                #     self.CRcontainer.clear()

    def ctrlBGRec(self):
        if self.tv is not None:
            if self.checkBox_13.isChecked():
                self.new_dict = {}
                for period, age_str in self.timescaleGeo[3].items():
                    age = float(age_str)
                    self.new_dict[period] = age
                    if age > self.x_max:
                        break
                keys = list(self.new_dict.keys())
                rect_widths_3 = [self.new_dict[key] - self.new_dict[list(self.new_dict.keys())[i - 1]] if i > 0 else self.new_dict[key]
                                 for i, key in enumerate(self.new_dict)]
                x_start = 0
                self.y_max = float(self.tv.ylim[1] - 1)
                for i, (width, key) in enumerate(zip(rect_widths_3, keys)):
                    if self.comboBox_3.currentText() == 'Default':
                        if i % 2 != 0:
                            color = 'lightgrey'
                        else:
                            color = 'white'
                            # color = cmap(x_start / (x_start + width))
                    elif self.comboBox_3.currentText() == 'Invert':
                        if i % 2 != 0:
                            color = 'white'
                        else:
                            color = 'lightgrey'
                    else:
                        if i % 2 != 0:
                            color = 'darkgrey'
                        else:
                            color = 'lightgrey'

                    # 如果是最后一个矩形，调整宽度为剩余的可见部分
                    if i == len(rect_widths_3) - 1:
                        width = self.x_max - x_start

                    rect = plt.Rectangle((self.x_max - x_start - width, 0.6), width, self.y_max, edgecolor='None',
                                         facecolor=color, zorder=-1, alpha=0.4)
                    self.ax1.add_patch(rect)
                    # self.figure.canvas.draw_idle()
                    x_start += width
            else:
                return
                # if self.container:
                #     for rect in self.container:
                #         rect.remove()
                #         self.figure.canvas.draw_idle()
                #     self.container.clear()

    def unit_anno(self):
        if self.tv is not None:
            text = self.comboBox.currentText()
            t = self.ax1.text(0, self.y_max + 1.2, text,
                         ha="center", va="center", size=12,
                         bbox=dict(boxstyle="square,pad=0.3",
                                   fc="white", ec="black", lw=2))
            tbox = self.get_element_rect2(t)
            # print(f'Bounding box coordinates: (x0, y0) = ({tbox.x0}, {tbox.y0}), (x1, y1) = ({tbox.x1}, {tbox.y1})')
            if self.ymax < tbox.y1:
                self.ymax = tbox.y1
                self.top_top = t

    def dis_distance(self):
        return

    def time_divided(self):
        # self.time_unit = str(self.comboBox.currentText())
        if self.time_unit == '100MYA':
            self.timescaleGeo = [{key: value / 100 for key, value in sub_dict.items()} for sub_dict in self.timescaleGeo]
        else:
            return

    def geo_eon(self):
        if self.tv is not None:
            if self.checkBox_16.isChecked():
                ymin, ymax = self.tv.ylim
                tree_high = ymax - ymin
                self.new_dict = {}
                for period, age_str in self.timescaleGeo[1].items():
                    age = float(age_str)
                    self.new_dict[period] = age
                    if age > self.x_max:
                        break
                keys = list(self.new_dict.keys())
                rect_widths = [self.new_dict[key] - self.new_dict[list(self.new_dict.keys())[i - 1]] if i > 0 else self.new_dict[key] for i, key
                               in enumerate(self.new_dict)]
                x_start = 0
                geo_high = self.y_max/6
                self.cmap = plt.get_cmap(self.comboBox_4.currentText())
                for i, (width, key) in enumerate(zip(rect_widths, keys)):
                    color = self.cmap(x_start / (x_start + width))

                    # 如果是最后一个矩形，调整宽度为剩余的可见部分
                    if i == len(rect_widths) - 1:
                        width = self.x_max - x_start

                    rect = plt.Rectangle((self.x_max - x_start - width, -geo_high), width, geo_high*0.3, edgecolor='black', linewidth=0.8, facecolor=color,
                                         label=f'Width: {width:.4f}')
                    self.ax1.add_patch(rect)
                    clrect = self.get_element_rect(rect)
                    if self.ymin > clrect.y0:
                        self.ymin = clrect.y0
                        self.min_down = rect

                    text_object = self.ax1.text(self.x_max - x_start - width + width / 2, -geo_high*0.85, key, ha='center', va='center', color='black', fontsize=12)
                    x_start += width

                self.new_dict = {}
                for period, age_str in self.timescaleGeo[2].items():
                    age = float(age_str)
                    self.new_dict[period] = age
                    if age > self.x_max:
                        break
                keys = list(self.new_dict.keys())
                rect_widths_2 = [
                    self.new_dict[key] - self.new_dict[list(self.new_dict.keys())[i - 1]] if i > 0 else self.new_dict[
                        key]
                    for i, key in enumerate(self.new_dict)]
                x_start = 0
                self.cmap = plt.get_cmap(self.comboBox_4.currentText())
                for i, (width, key) in enumerate(zip(rect_widths_2, keys)):
                    color = self.cmap(x_start / (x_start + width))

                    # 如果是最后一个矩形，调整宽度为剩余的可见部分
                    if i == len(rect_widths_2) - 1:
                        width = self.x_max - x_start

                    rect = plt.Rectangle((self.x_max - x_start - width, -geo_high*0.7), width, geo_high*0.3, edgecolor='black', linewidth=0.8, facecolor=color,
                                         label=f'Width: {width:.4f}')
                    self.ax1.add_patch(rect)
                    rect_bbox_data = rect.get_bbox()

                    # 转换为像素坐标
                    rect_bbox = rect_bbox_data.transformed(self.ax1.transData).transformed(
                        self.fig.dpi_scale_trans.inverted())
                    rect_width = rect_bbox.width
                    rect_height = rect_bbox.height

                    text_object = self.ax1.text(self.x_max - x_start - width + width / 2, -geo_high*0.55, key, ha='center', va='center', color='black',
                                                fontsize=12)
                    # 转换为像素坐标
                    text_bbox_data = text_object.get_window_extent()
                    text_bbox = text_bbox_data.transformed(self.fig.dpi_scale_trans.inverted())
                    text_width = text_bbox.width
                    text_height = text_bbox.height

                    text_object.set_visible(False)

                    if rect_width > text_width and rect_height > text_height:
                        text_object.set_visible(True)
                    else:
                        text_object.set_visible(False)
                        abbreviated_key = key[:2]
                        new_text_object = self.ax1.text(self.x_max - x_start - width + width / 2, -geo_high*0.55, abbreviated_key+'.', ha='center', va='center',
                                               color='black', fontsize=12)
                        new_text_object.set_visible(True)
                        # text_object.set_visible(True)'''
                        '''text_object.set_visible(False)
                        rect_c = rect.get_center()
                        offsetbox = TextArea(key)
                        ab = AnnotationBbox(offsetbox, rect_c,
                                            xybox=(-28., -80),
                                            xycoords='data',
                                            boxcoords="offset points",
                                            pad=0.5,
                                            arrowprops=dict(arrowstyle="->"),
                                            box_alignment=(0., 0.5),

                                            )
                        self.ax1.add_artist(ab)'''
                    x_start += width

                self.new_dict = {}
                for period, age_str in self.timescaleGeo[3].items():
                    age = float(age_str)
                    self.new_dict[period] = age
                    if age > self.x_max:
                        break
                keys = list(self.new_dict.keys())
                rect_widths_3 = [
                    self.new_dict[key] - self.new_dict[list(self.new_dict.keys())[i - 1]] if i > 0 else self.new_dict[
                        key]
                    for i, key in enumerate(self.new_dict)]
                x_start = 0
                self.cmap = plt.get_cmap(self.comboBox_4.currentText())
                for i, (width, key) in enumerate(zip(rect_widths_3, keys)):
                    color = self.cmap(x_start / (x_start + width))

                    # 如果是最后一个矩形，调整宽度为剩余的可见部分
                    if i == len(rect_widths_3) - 1:
                        width = self.x_max - x_start

                    rect = plt.Rectangle((self.x_max - x_start - width, -geo_high*0.4), width, geo_high*0.4, edgecolor='black', linewidth=0.8, facecolor=color,
                                         label=f'Width: {width:.4f}')
                    self.ax1.add_patch(rect)

                    rect_bbox_data = rect.get_bbox()
                    # 转换为像素坐标
                    rect_bbox = rect_bbox_data.transformed(self.ax1.transData).transformed(
                        self.fig.dpi_scale_trans.inverted())
                    rect_width = rect_bbox.width
                    rect_height = rect_bbox.height
                    text_object = self.ax1.text(self.x_max - x_start - width + width / 2, -geo_high*0.2, key, ha='center', va='center', color='black',
                                                fontsize=12)
                    text_bbox_data = text_object.get_window_extent()
                    # 转换为像素坐标
                    text_bbox = text_bbox_data.transformed(self.fig.dpi_scale_trans.inverted())
                    text_width = text_bbox.width
                    text_height = text_bbox.height
                    text_object.set_visible(False)

                    if rect_width > text_width and rect_height > text_height:
                        text_object.set_visible(True)
                    else:
                        # text_object.set_visible(False)
                        abbreviated_key = key[:2]
                        # print(abbreviated_key)
                        new_text_object = self.ax1.text(self.x_max - x_start - width + width / 2, -geo_high * 0.2, abbreviated_key+'.', ha='center',
                                                   va='center',
                                                   color='black', fontsize=12)
                        '''abbreviated_key = key[0:3]
                        text_object1 = plt.text(self.x_max - x_start - width + width / 2, 0.8, abbreviated_key, ha='center', va='center',
                                               color='black', fontsize=12)
                        text_object1.set_visible(False)'''
                    x_start += width
            else:
                return
                # for rec in self.eoncontainer:
                #     rec.remove()
                #     self.eoncontainer.clear()
                # for txt in self.eontxt:
                #     txt.remove()
                #     self.eontxt.clear()

    def ctrlBranchlength(self):
        if self.tv is not None:
            if self.checkBox_5.isChecked():
                self.tv.show_branch_length(label_formatter=lambda v: f"{v:.4f}")
            else:
                self.tv.show_branch_length(label_formatter=None)

    def top_sticks(self):
        if self.tv is not None:
            x = self.tv.max_tree_depth
            y_line = self.y_max + 0.6
            self.ax1.hlines(y_line, 0, x, linewidth=1.2, color='black')
            num_segments = 10
            segment_length = x / num_segments
            x_start = 0

            for i in range(num_segments + 1):
                xpos = i * segment_length
                self.ax1.vlines(xpos, y_line, y_line + 0.14, linewidth=1.5, color='black')
                self.ax1.text(self.x_max - x_start - xpos, y_line + 0.14, f'{xpos:.2f}', ha='center', va='bottom', fontsize=9)
                if i < num_segments:
                    for j in range(1, 21):
                        short_xpos = xpos + j * (segment_length / 20)

                        if j % 10 == 0:  # 每间隔十个画一条稍长的线
                            self.ax1.vlines(short_xpos, y_line, y_line + 0.12, linewidth=1.2, color='gray')
                        else:
                            self.ax1.vlines(short_xpos, y_line, y_line + 0.09, linewidth=1.0, color='gray')

    def setScales(self):
        if self.tv is not None:
            self.hscale = self.doubleSpinBox.value()
            self.vscale = self.doubleSpinBox_2.value()
            '''axes = self.figure.gca()
            # 调整Axes对象的长宽比例
            axes.set_aspect(self.hscale / self.vscale)'''
            self.figure.set_size_inches(self.hscale, self.vscale)
            self.figure.canvas.draw()
            # self.fit_to_window()

    def on_pick(self, event):
        # 高亮选中的图形元素
        if isinstance(event.artist, plt.Line2D) or isinstance(event.artist, plt.Text):
            event.artist.set_color('blue')
            self.figure.canvas.draw()

    def on_hover(self, event):
        if event.inaxes == self.ax1:
            for line in self.ax1.lines:
                if line.contains(event)[0]:
                    xy, w, h = line.__dict__.get("rect_parms", (None, None, None))
                    if xy and w and h:
                        if not hasattr(line, 'rect'):
                            self.highlight_rect = patches.Rectangle(xy, w, h, edgecolor="grey", facecolor="blue", alpha=0.3)
                            self.ax1.add_patch(self.highlight_rect)
                            self.current_highlight = line
                            line.rect = self.highlight_rect
                else:
                    if hasattr(line, 'rect'):
                        line.rect.remove()
                        del line.rect
            for text in self.ax1.texts:
                if text.contains(event)[0]:
                    leaf_node = text.__dict__.get("tree_node", None)
                    # 只给leaf label产生该效果
                    if not leaf_node:
                        continue
                    trans_bbox = self.tv.get_text_rect(text)
                    w = trans_bbox.width
                    h = trans_bbox.height
                    xy = (trans_bbox.x0, trans_bbox.y0)
                    if xy and w and h:
                        if not hasattr(text, 'rect'):
                            self.highlight_rect = patches.Rectangle(xy, w, h, edgecolor="grey", facecolor="red", alpha=0.3)
                            self.ax1.add_patch(self.highlight_rect)
                            self.current_highlight = text
                            text.rect = self.highlight_rect
                else:
                    if hasattr(text, 'rect'):
                        text.rect.remove()
                        del text.rect
            self.figure.canvas.draw_idle()

    def on_press(self, event):
        # if event.inaxes:
        if event.button == 1:
            self.press = True
            self.lastx = event.xdata
            self.lasty = event.ydata

    def on_move(self, event):
        if self.press:  # 按下状态
            # 计算新的坐标原点并移动
            # 获取当前最新鼠标坐标与按下时坐标的差值
            x = event.xdata - self.lastx
            y = event.ydata - self.lasty
            # 获取当前所有子图的坐标范围
            for ax in self.figure.axes:
                if ax:
                    x_min, x_max = ax.get_xlim()
                    y_min, y_max = ax.get_ylim()

                    x_min = x_min - x
                    x_max = x_max - x
                    y_min = y_min - y
                    y_max = y_max - y

                    ax.set_xlim(x_min, x_max)
                    ax.set_ylim(y_min, y_max)

            self.figure.canvas.draw()
        '''axtemp = event.inaxes
        if axtemp:
            if self.press:  # 按下状态
                # 计算新的坐标原点并移动
                # 获取当前最新鼠标坐标与按下时坐标的差值
                x = event.xdata - self.lastx
                y = event.ydata - self.lasty
                # 获取当前原点和最大点的4个位置
                x_min, x_max = axtemp.get_xlim()
                y_min, y_max = axtemp.get_ylim()

                x_min = x_min - x
                x_max = x_max - x
                y_min = y_min - y
                y_max = y_max - y

                axtemp.set_xlim(x_min, x_max)
                axtemp.set_ylim(y_min, y_max)
                self.figure.canvas.draw()'''

    def on_release(self, event):
        if self.press:
            self.press = False

    def call_back(self, event):
        axtemp = event.inaxes
        if not axtemp:
            return
        x_min, x_max = axtemp.get_xlim()
        y_min, y_max = axtemp.get_ylim()
        xfanwei = (x_max - x_min) / 10
        yfanwei = (y_max - y_min) / 10
        for ax in self.figure.axes:
            if event.button == 'up':
                ax.set(xlim=(x_min + xfanwei, x_max - xfanwei))
                ax.set(ylim=(y_min + yfanwei, y_max - yfanwei))
            elif event.button == 'down':
                ax.set(xlim=(x_min - xfanwei, x_max + xfanwei))
                ax.set(ylim=(y_min - yfanwei, y_max + yfanwei))
            self.figure.canvas.draw_idle()
        # self.auto_set_scale()

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        name = obj.objectName()
        if isinstance(
                obj,
                QLineEdit):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                self.datingTreeName = files[0]
                # print(self.datingTreeName)
                self.input(self.datingTreeName)
                self.load_tree(self.datingTreeName)
                # self.input(file_f)
                return True

        if isinstance(
                obj,
                FigureCanvas):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                self.datingTreeName = files[0]
                # print(self.datingTreeName)
                self.input(self.datingTreeName)
                self.load_tree(self.datingTreeName)
                return True

        return super(TreeViewer, self).eventFilter(obj, event)
    # def update_multitree(self):
    #    style = self.style
    #    c, a, m = self.datingTreetree.draw(ncols=3, nrows=3, ts=self.ts,
    #                                        width=self.width,
    #                                        height=self.height * 3, **style)
    #    toyplot.html.render(c, "temp.html")
    #    with open('temp.html', 'r') as f:
    #        html = f.read()
    #        self.webEngineView.setHtml(html)
    #    self.canvas = c
    #    return

    # def get_node_colors(tre, df, col, cmap):
    #     """Node colors from tree and dataframe labels"""
    #
    #     node_colors = []
    #     for n in tre.find_clades('name', True, True):
    #         if n in df.index:
    #             val = df.loc[n][col]
    #             if val in cmap:
    #                 node_colors.append(cmap[val])
    #             else:
    #                 node_colors.append('black')
    #         else:
    #             node_colors.append('black')
    #     return node_colors

    def ctrlHscale(self):
        self.width = self.horizontalSlider.value()
        self.update()
        return

    def ctrlVscale(self):
        self.height = self.horizontalSlider_2.value()
        self.update()
        return


    '''def ctrlBranch(self, tree):
        if self.tv is not None:
            self.tree.show_branch_length(color="blue")'''


    def ctlSclaeBar(self):
        if self.tv is not None:
            return

    def clear_lineEdit(self):
        sender = self.sender()
        lineEdit = sender.parent()
        lineEdit.setText("")
        lineEdit.setToolTip("")

    def guiSave(self):
        self.TreeViewer_settings.setValue('size', self.size())

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.TreeViewer_settings.setValue(name, state)
            elif isinstance(obj, QPushButton):
                if name in ["pushButton_color",
                            "pushButton_color_2"]:
                    color = obj.palette().color(1)
                    self.TreeViewer_settings.setValue(name, color.name())

    def guiRestore(self):
        # self.resize(self.TreeViewer_settings.value('size', QSize(1286, 785)))
        self.resize(self.factory.judgeWindowSize(self.TreeViewer_settings, 1286, 785))
        self.factory.centerWindow(self)

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QCheckBox):
                ini_state_ = obj.isChecked()
                state_ = self.TreeViewer_settings.value(name, ini_state_)
                obj.setChecked(bool(state_))
            elif isinstance(obj, QPushButton):
                if name in ["pushButton_color",
                            "pushButton_color_2",
                            "pushButton_color_3"
                            ]:
                    dict_ini_colors = {"pushButton_color": "#000000",
                                       "pushButton_color_2": "#554a97",
                                       "pushButton_color_3": '#333333'}
                    dict_slot_fun = {"pushButton_color": self.changeLineColor,
                                     "pushButton_color_2": self.changeConfidenceColorF,
                                     "pushButton_color_3": self.changeConfidenceColorE
                                     }
                    ini_color = dict_ini_colors[name]
                    color = self.TreeViewer_settings.value(name, ini_color)
                    obj.setStyleSheet("background-color:%s"%color)
                    obj.setText(color)
                    obj.clicked.connect(dict_slot_fun[name])

    def closeEvent(self, event):
        self.guiSave()

    def ctrlAnnotate(self):
        return
    def ctrlPointmarker(self):
        return

    def get_element_rect(self, element):
        bbox = element.get_bbox()
        return bbox
        # print(bbox)
        # data_to_figure = self.ax1.transData.transform
        # return self.ax1.transAxes.inverted().transform(data_to_figure(bbox))

    def get_element_rect2(self, element):
        if not element:
            return
        try:
            return element.get_bbox()
        except:
            return self.tv.get_text_rect(element)

    def setFont(self):
        text_ = self.lineEdit_2.text()
        family_, size_, style_bool, bold_bool = self.font_prop_bytext(text_)
        font_ = QFont(family_, int(size_))
        font_.setBold(bold_bool)
        font_.setItalic(style_bool)
        font, ok = QFontDialog.getFont(font_, self)
        if ok:
            # self.lineEdit_2.setFont(font)
            family_, size_, style, bold = self.get_font_prop(font)
            self.lineEdit_2.setText(f"{family_};{size_}"
                                    f"{';italic' if style=='italic' else ''}"
                                    f"{';bold' if bold else ''}")
            for text in self.ax1.texts:
                if text.__dict__.get("type", None) == "leaf":
                    text.__dict__["_fontproperties"].__dict__["_weight"] = "bold" if bold else "normal"
                    text.__dict__["_fontproperties"].__dict__["_size"] = size_
                    text.__dict__["_fontproperties"].__dict__["_slant"] = style
                    text.__dict__["_fontproperties"].__dict__["_family"] = family_

    def font_prop_bytext(self, text):
        list_text = text.split(";")
        return list_text[0],list_text[1],True if "italic" in text else False,True if "bold" in text else False

    def get_font_prop(self, font):
        family_ = font.family()
        size_ = font.pointSize()
        style = self.dict_font_style[font.style()]
        bold = font.bold()
        return family_, size_, style, bold

    def changeLineColor(self):
        button = self.sender()
        ini_color = button.palette().color(1)
        color = QColorDialog.getColor(QColor(ini_color), self)
        if color.isValid():
            button.setText(color.name())
            button.setStyleSheet("background-color:%s"%color.name())
        # 修改线段颜色
        for line in self.ax1.lines:
            if line.__dict__.get("type", None) == "branch":
                line.__dict__["_color"] = color.name()

    def changeLineWidth(self, value):
        for line in self.ax1.lines:
            if line.__dict__.get("type", None) == "branch":
                line.__dict__["_linewidth"] = value

    def changeLineType(self, type):
        type = type.split()[0]
        for line in self.ax1.lines:
            if line.__dict__.get("type", None) == "branch":
                line.__dict__["_linestyle"] = type

    def changeConfidenceColorF(self):
        button = self.sender()
        ini_color = button.palette().color(1)
        color = QColorDialog.getColor(QColor(ini_color), self)
        if color.isValid():
            button.setText(color.name())
            button.setStyleSheet("background-color:%s"%color.name())
        # 修改矩形颜色
        for patch in self.ax1.patches:
            if patch.__dict__.get("type", None) == "confidence":
                patch.__dict__["_facecolor"] = matplotlib.colors.to_rgba(color.name())

    def changeConfidenceColorE(self):
        button = self.sender()
        ini_color = button.palette().color(1)
        color = QColorDialog.getColor(QColor(ini_color), self)
        if color.isValid():
            button.setText(color.name())
            button.setStyleSheet("background-color:%s"%color.name())
        # 修改矩形颜色
        for patch in self.ax1.patches:
            if patch.__dict__.get("type", None) == "confidence":
                patch.__dict__["_edgecolor"] = matplotlib.colors.to_rgba(color.name())

    def changeConfidenceHeight(self, value):
        for patch in self.ax1.patches:
            if patch.__dict__.get("type", None) == "confidence":
                y0 = patch.__dict__["_y0"]
                y1 = patch.__dict__["_y1"]
                mean_y = (y0 + y1)/2
                patch.__dict__["_height"] = value
                patch.__dict__["_y0"] = mean_y - value/2
                patch.__dict__["_y1"] = mean_y + value/2
                # print(patch.__dict__)

    def create_annotation_editor(self, type, header=None, include_inner_nodes=False, configs=None):
        if type == "Replace leaf name":
            header = ["Node ID", "New name"] if not header else header
            array = [[leaf_name, leaf_name] for leaf_name in self.tv.leaf_labels]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyNameTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.replace_leaf_name(model.arraydata),
                                                           editor.close()])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.show()
        elif type == "Auto show taxonomy":
            header = ["Node ID", "Genus", "Subfamily", "Family", "Order", "Subclass",
                      "Class", "Phylum"] if not header else header
            array = [[leaf_name] + [""]*7 for leaf_name in self.tv.leaf_labels]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor_tax.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyTaxTableModel(array, header, parent=editor.ui.tableView, dialog=editor)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda: [self.make_taxonomy_face1(
                                                            editor.ui.tableView.model().fetchIncludedArray(),
                                                            editor.ui.tableView.model().fetchIncludedTax(),
                                                            editor.ui.tableView.model().get_colors(),
                                                            mode="rep"),
                                                          editor.close()])

            editor.ui.pushButton_13.clicked.connect(lambda: [self.checkboxes_action(editor)])

            # add column
            editor.ui.pushButton_2.clicked.connect(lambda : [model.header.append(f"Taxonomy{len(model.header)}"),
                                                             model.headerDataChanged.emit(Qt.Horizontal, len(model.header)-1, len(model.header)-1),
                                                             setattr(model, "arraydata", [row + [""] for row in model.arraydata]),
                                                             model.dataChanged.emit(model.index(0, 0), model.index(0, 0)),
                                                             editor.ui.tableView.scrollTo(model.index(0, len(model.header)-1))])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            editor.show()
        elif type == "Text":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_text_face(editor.tab.tableview, array, mode="rep")
            else:
                configs = [
                              ["Font", QFont("Arial", 12, QFont.Normal)],
                              # ["Text color", "#000000"],
                              ["Pen width", 0],
                              ["Tight text", False],
                          ] + copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Text")
                # tab_tableview.list_item.name = "text"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                          self.make_text_face(tab_tableview,
                                                                              editor.ui.tableView.model().arraydata,
                                                                              mode="rep"))
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_text_face(tab_tableview, array, mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_text_face(tab_tableview, array, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Color strip":
            header = ["Node ID", "Color"] if not header else header
            array = [[leaf_name, "None color"] for leaf_name in self.tv.leaf_labels]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyStripTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda: [self.create_annotation(type, model.arraydata,
                                                                                 editor=editor),
                                                          editor.close()])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            # if array_:
            #     self.create_annotation(type, model.arraydata, editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            # else:
            editor.show()

    def create_annotation(self, type, array, header=None, editor=None,
                          check_array=None, configs=None,
                          tabIsChecked=None, nodraw=False):
        if type == "Text":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_text_face(editor.tab.tableview, array, mode="rep")
            else:
                configs = [
                              ["Font", QFont("Arial", 12, QFont.Normal)],
                              # ["Text color", "#000000"],
                              ["Pen width", 0],
                              ["Tight text", False],
                          ] + copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Text")
                # tab_tableview.list_item.name = "text"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                          self.make_text_face(tab_tableview,
                                                                              editor.ui.tableView.model().arraydata,
                                                                              mode="rep"))
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_text_face(tab_tableview, array, mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_text_face(tab_tableview, array, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Color strip":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_strip_face(editor.tab.tableview, array,
                                     row=self.listWidget.row(editor.tab.tableview.refresh_btn.item),
                                     mode="rep")
            else:
                configs = [
                              ["Height", 1],
                              ["Width", self.tv.xlim[1] * 0.02]
                          ] + copy.deepcopy(self.face_base_parameters)
                tab_tableview = self.add_tableView(configs, "Color strip")
                # tab_tableview.list_item.name = "color strip"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                          [self.make_strip_face(tab_tableview,
                                                                               editor.ui.tableView.model().arraydata,
                                                                               row=self.listWidget.row(tab_tableview.refresh_btn.item),
                                                                               mode="rep"),
                                                           self.update_face_pos()])
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_text_face(tab_tableview, array, mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_strip_face(tab_tableview, array, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)


    def replace_leaf_name(self, array):
        dict_names = {old_name:new_name for old_name, new_name in array}
        for text in self.ax1.texts:
            if text.__dict__.get("type", None) == "leaf":
                text.__dict__["_text"] = dict_names.get(text.__dict__["_text"],
                                                        text.__dict__["_text"])

    def get_leaf_texts(self):
        return [text.__dict__["_text"] for text in self.ax1.texts
                if text.__dict__.get("type", None) == "leaf"]

    def make_taxonomy_face1(self, array, included_tax, dict_tax_color, mode="new"):
        self.dict_tax_strip = {}
        # {Benedenia_hoshinai_NC_014591: {Family: [Capsalidae, #000000]}}
        self.dict_id_tax_value_color = {}
        # self.displayed_names = []
        for num, tax in enumerate(included_tax):
            if num != 0:
                for list_line in array:
                    if list_line[num]:
                        self.dict_tax_strip.setdefault(tax, []).append([list_line[0], dict_tax_color[list_line[num]]])
                        # {Benedenia_hoshinai_NC_014591: {Family: [Capsalidae, #000000]}}
                        self.dict_id_tax_value_color.setdefault(list_line[0], {}).setdefault(tax, [list_line[num],
                                                                                                   dict_tax_color[list_line[num]]])
        # TEXT
        self.dict_tax_text = {}
        dict_node_tax_setting = {} # {node1: [[Family, Capsalidae, #000000], ]}
        ete_tree = self.factory.read_tree(self.fileName)
        for node in ete_tree.traverse("preorder"):
            leaves = node.get_leaves()
            for tax in reversed(included_tax[1:]):
                list_ = []
                flag = True
                for leaf in leaves:
                    if (leaf.id in self.dict_id_tax_value_color) and (tax in self.dict_id_tax_value_color[leaf.id]):
                        list_.append(self.dict_id_tax_value_color[leaf.id][tax])
                    else:
                        flag = False
                        break
                if not flag:
                    continue
                if len(set([j[0] for j in list_])) == 1:
                    if not self.tax_has_displayed(node, tax, dict_node_tax_setting):
                        tax_name, color = list_[0]
                        dict_node_tax_setting.setdefault(node, []).append([tax, tax_name, dict_tax_color[tax_name]])
                        # choose species in center to display
                        middle_index = int(len(leaves)/2) if len(leaves)%2 == 0 else int(len(leaves)/2-0.5)
                        represent_node = leaves[middle_index]
                        self.dict_tax_text.setdefault(tax, []).append([represent_node.id, tax_name, color])
        for tax in self.dict_tax_strip:
            self.create_annotation_editor("Color strip",
                                          array_=self.dict_tax_strip[tax],
                                          include_inner_nodes=True)
            self.create_annotation_editor("Text",
                                          array_=self.dict_tax_text[tax],
                                          include_inner_nodes=True)

    def update_face_pos(self):
        if not self.list_faces:
            return
        l_text_box = []
        for text in self.ax1.texts:
            if text.__dict__.get("type", None) == "leaf":
                bbox = self.get_element_rect2(text)
                l_text_box.append(bbox.x1)
        self.top_right = max(l_text_box)
        for face in self.list_faces:  # [[element1, element2],]
            l_ = []
            for element in face:
                width = element.__dict__["_x1"] - element.__dict__["_x0"]
                element.__dict__["_x0"] = self.top_right + element.__dict__["_space"]
                element.__dict__["_x1"] = element.__dict__["_x0"] + width
                bbox = self.get_element_rect2(element)
                l_.append(bbox.x1)
            if self.top_right < max(l_):
                self.top_right = max(l_)

    def add_tableView(self, configs, label, hide_button=False):
        ### add list item
        face_item = QListWidgetItem(self.listWidget)
        face_widget = ListItemWidget(label, face_item, parent=self.listWidget, hide_btn=hide_button)
        face_item.widget = face_widget
        # Set size hint
        face_item.setSizeHint(face_widget.sizeHint())
        face_item.name = label
        # Add QListWidgetItem into QListWidget
        self.listWidget.addItem(face_item)
        self.listWidget.setItemWidget(face_item, face_widget)
        ### add tableview page
        tab = QWidget(self.stackedWidget)
        Layout = QVBoxLayout(tab)
        Layout.setContentsMargins(0, 0, 0, 0)
        tableview = QTableView(tab)
        tableview.data_edit_btn = QPushButton("Data editor", tab)
        tableview.data_edit_btn.setIcon(QIcon(":/picture/resourses/edit2.png"))
        tableview.refresh_btn = QPushButton("Refresh tree", tab)
        tableview.refresh_btn.setIcon(QIcon(":/picture/resourses/refresh-icon.png"))
        tableview.refresh_btn.item = face_item
        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(tableview.data_edit_btn)
        horizontalLayout.addWidget(tableview.refresh_btn)
        Layout.addWidget(tableview)
        Layout.addLayout(horizontalLayout)
        tab.tableview = tableview
        tableview.tab = tab
        # self.tabWidget.addTab(tab, tab_text)
        # self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(tab))
        self.stackedWidget.addWidget(tab)
        tableview.page_widget = tab
        tableview.list_item = face_item
        face_item.page_widget = tab
        header = ["Parameters", "Value"]
        model = MyTableModel(configs, header, parent=tableview)
        tableview.setModel(model)
        # tableview.doubleClicked.connect(self.handle_itemclicked)
        face_widget.checkBox.stateChanged.connect(lambda state: self.judge_remove(state, tab))
        face_widget.btn_close.clicked.connect(lambda : self.listWidget.removeItem(mode="non ete"))
        return tableview

    def judge_remove(self):
        pass

    def make_strip_face(self, tableview, array, row=None, mode="new"):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        width = float(dict_configs["Width"])
        height = float(dict_configs["Height"])
        space_factor_left = float(dict_configs["space_factor_left"])
        space = self.tv.xlim[1] * space_factor_left
        edge_color = dict_configs["border.color"]
        linestyle = self.dict_style[dict_configs["border.type"][0]]
        linewidth = dict_configs["border.width"]
        if mode == "new":
            dict_name_xy = self.tv.name2xy_center
            l_ = []
            for list_line in array:
                name, color_ = list_line
                if color_ == "None color":
                    continue
                xy = dict_name_xy.get(name, None)
                if xy:
                    y = xy[1]
                    rect = plt.Rectangle((0, y - 0.5),
                                         width, height,
                                         edgecolor=edge_color,
                                         linestyle=linestyle,
                                         linewidth=linewidth,
                                         color=color_, alpha=0.5)
                    rect.__dict__["_space"] = space
                    rect.__dict__["_name"] = name
                    self.ax1.add_patch(rect)
                    l_.append(rect)
            self.list_faces.append(l_)
            self.update_face_pos()
        else:
            # 替换元素
            dict_name_color = dict(array)
            for element in self.list_faces[row]:
                element.__dict__["_width"] = width
                element.__dict__["_height"] = height
                element.__dict__["_space"] = space
                element.__dict__["_edgecolor"] = matplotlib.colors.to_rgba(edge_color)
                element.__dict__["_original_edgecolor"] = edge_color
                element.__dict__["_linestyle"] = linestyle
                element.__dict__["_linewidth"] = linewidth
                element.__dict__["_original_facecolor"] = dict_name_color[element.__dict__["_name"]]
                element.__dict__["_facecolor"] = matplotlib.colors.to_rgba(dict_name_color[element.__dict__["_name"]])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = TreeViewer()
    ui.show()
    sys.exit(app.exec_())




