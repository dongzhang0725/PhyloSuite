import copy
import io
import os
import inspect
import re
import signal
import sys
import time
import traceback
from collections import OrderedDict

import matplotlib
from Bio import SeqIO
from Bio.SeqFeature import FeatureLocation, SeqFeature
from dna_features_viewer import BiopythonTranslator, GraphicFeature, load_record
from dna_features_viewer.CircularGraphicRecord import CircularGraphicRecord
from dna_features_viewer.GraphicRecord import GraphicRecord

from src.CustomWidget2 import MyNameTableModel, MyTaxTableModel, ListItemWidget, MyTableModel, MyStripTableModel
from src.Lg_extractSettings import ExtractSettings
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
from uifiles.Ui_DNA_view import Ui_DNAview
from src.PS_treeviz import PS_Treeviz

'''
https://github.com/Edinburgh-Genome-Foundry/DnaFeaturesViewer/issues/42
ax.figure.savefig(path + "custom_bopython_translator.pdf")
'''

class MyCustomGraphicRecord(GraphicFeature):
    # def __init__(
    #         self,
    #         sequence_length=None,
    #         sequence=None,
    #         features=(),
    #         feature_level_height=1,
    #         first_index=0,
    #         plots_indexing="biopython",
    #         labels_spacing=8,
    #         ticks_resolution="auto",
    # ):
    #     super().__init__(sequence_length,
    #                      sequence,
    #                      features,
    #                      feature_level_height,
    #                      first_index,
    #                      plots_indexing,
    #                      labels_spacing,
    #                      ticks_resolution)

    def annotate_feature(
            self,
            ax,
            feature,
            level,
            inline=False,
            max_label_length=50,
            max_line_length=30,
            padding=0,
            indicate_strand_in_label=False,
    ):
        """Create a Matplotlib Text with the feature's label.

        The x-coordinates of the text are determined by the feature's
        `x_center` while the y-coordinates are determined by the `level`.

        The text is horizontally and vertically centered.

        The Arrow points in the direction of the feature's strand.
        If the feature has no direction (strand==0), the returned patch will
        simply be a rectangle.

        The x-coordinates of the patch are determined by the feature's
        `start` and `end` while the y-coordinates are determined by the `level`.
        """
        return super().annotate_feature(ax, feature, level,
                                                                   inline, max_label_length,
                                 max_line_length, padding, indicate_strand_in_label)


class MyCustomTranslator(BiopythonTranslator):
    """Custom translator implementing the following theme:

    - Color terminators in green, CDS in blue, all other features in gold.
    - Do not display features that are restriction sites unless they are BamHI
    - Do not display labels for restriction sites
    - For CDS labels just write "CDS here" instead of the name of the gene.

    """
    def __init__(self, features_filters=(),
                 features_properties=None,
                 parent=None,
                 **dict_args):
        self.parent = parent
        self.dict_args = dict_args
        super().__init__(features_filters, features_properties)

    def compute_feature_color(self, feature):
        real_gene_name = self.compute_feature_label(feature)
        Fcolor, Bcolor, Tcolor, Length = self.parent.fetch_gene_params(
                                      self.dict_args["checked gene names"],
                                      real_gene_name.strip(" "),
                                      feature.type)
        return Fcolor

    def compute_feature_label(self, feature):
        label = feature.type
        key0 = f"Qualifiers to be recognized ({feature.type}):"
        if key0 in self.dict_args["qualifiers"]:
            for key in self.dict_args["qualifiers"][key0]:
                if key in feature.qualifiers and len(feature.qualifiers[key]):
                    label = feature.qualifiers[key]
                    break
        if isinstance(label, list):
            label = "|".join(label)
        return f'{self.dict_args["replace"][label]}{" "*self.dict_args["label right space"]}' if (
                label in self.dict_args["replace"]) else f'{label}{" "*self.dict_args["label right space"]}'

    def compute_feature_fontdict(self, feature):
        """Compute a font dict for this feature."""
        return self.dict_args["font"]

    def compute_feature_linewidth(self, feature):
        """Compute the edge width of the feature's arrow/rectangle."""
        return 1

    def translate_feature(self, feature):
        """Translate a Biopython feature into a Dna Features Viewer feature."""
        properties = dict(
            label=self.compute_feature_label(feature),
            color=self.compute_feature_color(feature),
            html=self.compute_feature_html(feature),
            fontdict=self.compute_feature_fontdict(feature),
            box_linewidth=self.compute_feature_box_linewidth(feature),
            box_color=self.compute_feature_box_color(feature),
            linewidth=self.compute_feature_linewidth(feature),
            label_link_color=self.compute_feature_label_link_color(feature),
            legend_text=self.compute_feature_legend_text(feature),
            thickness=self.dict_args["thickness"]
        )
        if self.features_properties is not None:
            other_properties = self.features_properties
            if hasattr(other_properties, "__call__"):
                other_properties = other_properties(feature)
            properties.update(other_properties)

        return GraphicFeature(
            start=feature.location.start,
            end=feature.location.end,
            strand=feature.location.strand,
            **properties
        )

    def translate_record(self, record, record_class=None, filetype=None):
        """Create a new GraphicRecord from a BioPython Record object.

        Parameters
        ----------

        record
          A BioPython Record object or the path to a Genbank or a GFF file.

        record_class
          The graphic record class to use, e.g. GraphicRecord (default) or
          CircularGraphicRecord. Strings 'circular' and 'linear' can also be
          provided.

        filetype
          Used only when a Genbank or a GFF file is provided; one of "genbank"
          or "gff" to be used. Default None infers from file extension.
        """
        classes = {
            "linear": GraphicRecord, # MyCustomGraphicRecord,
            "circular": CircularGraphicRecord,
            None: GraphicRecord # MyCustomGraphicRecord,
        }
        if record_class in classes:
            record_class = classes[record_class]

        if isinstance(record, str) or hasattr(record, "read"):
            record = load_record(record, filetype=filetype)
        filtered_features = self.compute_filtered_features(record.features)
        return record_class(
            sequence_length=len(record),
            sequence=str(record.seq) if record.seq else None,
            features=[
                self.translate_feature(feature)
                for feature in filtered_features
                if feature.location is not None
            ],
            **self.graphic_record_parameters
        )


class DNAViewer(QMainWindow, Ui_DNAview, object):
    showSig = pyqtSignal(QMainWindow)
    closeSig = pyqtSignal(str, str)
    treeview_exception = pyqtSignal(str)
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    ##弹出识别输入文件的信号
    auto_popSig = pyqtSignal(QMainWindow)
    def __init__(
            self,
            dict_name_GB_path=None,
            # list_names=None,
            workPath=None,
            totleID=None,
            focusSig=None,
            parent=None):
        super(DNAViewer, self).__init__(parent)
        self.parent = parent
        # self.figure = TreeViz.plotfig(ax=None)
        # FigureCanvas.__init__(self, self.figure)
        self.function_name = "DNAViewer"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.dict_name_GB_path = dict_name_GB_path
        self.totleID = totleID
        self.press = False

        self.figure = Figure()
        # self.fig = plt.figure() #figsize=(4, 3)
        # self.ax1 = self.figure.add_subplot(111)
        # self.ax1.patch.set_edgecolor('black')
        # self.ax1.patch.set_linewidth(1)'
        # self.ax1.xaxis.set_visible(False)
        # self.ax1.yaxis.set_visible(False)

        self.setupUi(self)
        # 设置比例
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 9)

        # 把ui中的widget换成figurecanvas控件
        self.figureCanvas = FigureCanvas(self.figure)
        self.figureCanvas.setAcceptDrops(True)
        self.verticalLayout.replaceWidget(self.widget, self.figureCanvas)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.figureCanvas.setSizePolicy(sizePolicy)
        # figure根据获取控件大小显示
        canvas_width, canvas_height = self.figureCanvas.get_width_height()
        # self.figure.set_size_inches(canvas_width / self.figureCanvas.figure.dpi,
        #                             canvas_height / self.figureCanvas.figure.dpi)

        # 添加右键菜单
        self.figureCanvas.setContextMenuPolicy(3)  # Qt.CustomContextMenu
        self.figureCanvas.customContextMenuRequested.connect(self.show_context_menu)

        self.DNAViewer_settings = QSettings(
            self.thisPath + '/settings/DNAViewer_settings.ini', QSettings.IniFormat)
        self.DNAViewer_settings.setFallbacksEnabled(False)
        self.qss_file = self.factory.set_qss(self)

        self.actionsave_as.triggered.connect(self.save_as)
        self.actionFit_The_Window.triggered.connect(self.fit_to_window)
        self.actionUpdate_figure.triggered.connect(lambda : self.plotGenbank(self.fetch_name_GB_path()))
        self.actionsettings.triggered.connect(lambda : self.show_hide_setting(self.actionsettings))
        self.actionsettings.setChecked(False)
        self.show_hide_setting(self.actionsettings)
        self.lineEdit.clicked.connect(self.setFont)
        self.exception_signal.connect(self.popupException)

        self.figureCanvas.mpl_connect('motion_notify_event', self.on_hover)
        self.figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.figure.canvas.mpl_connect('motion_notify_event', self.on_move)
        self.figure.canvas.mpl_connect('scroll_event', self.call_back)
        # self.figure.canvas.mpl_connect('resize_event', self.auto_set_scale)

        # 恢复用户的设置
        self.displaySettings()
        self.comboBox_6.activated[str].connect(self.switchSeqType)
        self.switchSeqType(self.comboBox_6.currentText())
        self.guiRestore()
        # self.actionUpdate_figure.trigger()
        self.plotGenbank(self.fetch_name_GB_path())

    def show_hide_setting(self, action):
        if action.isChecked():
            self.tabWidget.setVisible(True)
        else:
            self.tabWidget.setVisible(False)

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

    def qfont_to_fontdict(self, qfont):
        fontdict = {}
        # 获取字体族
        fontdict['family'] = qfont.family()
        # 获取字体大小
        fontdict['size'] = qfont.pointSize()
        # 获取字体粗细
        weight_value = qfont.weight()
        if weight_value == QFont.Light:
            fontdict['weight'] = 'light'
        elif weight_value == QFont.Normal:
            fontdict['weight'] = 'normal'
        elif weight_value == QFont.Bold:
            fontdict['weight'] = 'bold'
        else:
            fontdict['weight'] = str(weight_value)
        # 获取是否为斜体
        fontdict['style'] = 'italic' if qfont.italic() else 'normal'
        return fontdict

    def plotGenbank(self, dict_name_GB_path=None):
        if not dict_name_GB_path:
            return

        try:
            self.dict_args = {}
            self.dict_args["seq type"] = str(self.comboBox_6.currentText())
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
            name_unify = dict_extract_settings.pop("Names unification")
            self.dict_args["replace"] = {i[0]: i[1] for i in name_unify}
            self.dict_args["extract_list_gene"] = dict_extract_settings.pop("extract listed gene") if "extract listed gene" \
                                                                                                      in dict_extract_settings else False
            self.dict_args["qualifiers"] = dict_extract_settings  ###只剩下qualifier的设置

            self.dict_args["checked gene names"] = self.fetch_checked_gene_names()
            self.dict_args["go_parms"] = OrderedDict()
            for row, gene_name in enumerate(self.dict_args["checked gene names"]):
                Fcolor = self.tableWidget.item(row, 1).text()
                Bcolor = self.tableWidget.item(row, 2).text()
                Tcolor = self.tableWidget.item(row, 3).text()
                Length = int(self.tableWidget.item(row, 4).text())
                self.dict_args["go_parms"][gene_name] = [Fcolor, Bcolor, Tcolor, Length]
            self.dict_args["font"] = self.qfont_to_fontdict(self.lineEdit.font_)
            self.dict_args["thickness"] = self.doubleSpinBox.value()
            self.dict_args["feture_level"] = self.spinBox.value()
            self.dict_args["annotation_level"] = self.spinBox_2.value()
            self.dict_args["plot tick and labels"] = self.checkBox.isChecked()
            self.dict_args["use uniform length"] = self.checkBox_2.isChecked()
            self.dict_args["label right space"] = self.spinBox_3.value()

            self.translator = MyCustomTranslator(features_filters=(lambda f:
                                                                   f.type in
                                                                   self.dict_args["features"] if
                                                                   self.dict_args["features"] != "All" else
                                                                   lambda f: True, ),
                                                 parent=self,
                                                 **self.dict_args)
            # 清空画布
            self.figure.clear()
            # self.dict_name_ax = {}
            # 转换并绘制GenBank文件
            num = 1
            # list_title = []
            max_x = 0
            min_x = 0
            for name, gb_file in dict_name_GB_path.items():
                record = SeqIO.read(gb_file, "genbank")
                if self.dict_args["use uniform length"]:
                    record = self.uniform_gb(record, self.dict_args["features"])
                # 创建子图
                graphic_record = self.translator.translate_record(record)
                if len(self.figure.axes) > 0:
                    ax = self.figure.add_subplot(self.totleID, 1, num,
                                                 sharex=self.figure.axes[0]
                                                 # xlim=[0, len(record.seq)]
                                                 )
                else:
                    ax = self.figure.add_subplot(self.totleID, 1, num)
                # ax.set_title(name, loc='left', weight='bold',
                #              fontsize=self.dict_args["font"]["size"] + 6,
                #              fontfamily=self.dict_args["font"]["family"]
                #              )
                # ax.text(0, -0.15, name, ha='left', va='center', transform=ax.transAxes,
                #         fontsize=self.dict_args["font"]["size"] + 6,
                #         fontfamily=self.dict_args["font"]["family"],
                #         fontweight='bold')
                graphic_record.annotation_height = self.dict_args["annotation_level"] # 控制注释文本的高度
                graphic_record.feature_level_height = self.dict_args["feture_level"] # 0所有feature会画在同一行
                # 绘图这一步在plot这里
                # translate_feature 控制各个绘图的参数
                # plot_feature里面的feature是translate_feature返回的GraphicFeature，各种画图参数都在上面控制
                graphic_record.plot(ax=ax,
                                    # figure_width=20,
                                    # figure_height=20,
                                    # strand_in_label_threshold=20,
                                    # x_lim=[0, len(record.seq)],
                                    # elevate_outline_annotations=True
                                    )
                if self.dict_args["plot tick and labels"] and (not self.dict_args["use uniform length"]):
                    # 设置 x 轴和 y 轴刻度标签的字体大小
                    ax.tick_params(axis='x', which='major',
                                   labelsize=self.dict_args["font"]["size"] + 3)
                else:
                    ax.axis('off')
                # 避免有些颜色块下面被隐藏了
                ymin, ymax = ax.get_ylim()
                ax.set_ylim(ymin-self.dict_args["thickness"]*0.15, ymax)

                # title，必须在设置完ylim以后再绘制title，ax.transAxes的对应位置会变
                # transform=ax.transAxes：(0, 0) 是轴的左下角，(1, 1) 是轴的右上角。
                # 得到feature图形的rect位置
                # PLOT THE LABEL-TO-FEATURE LINK  画link的地方
                # text.set_position((x, new_y)) 这是设置label的地方
                patch_rect = ax.transAxes.inverted().transform_bbox(ax.patches[0].get_window_extent())
                y_ = (patch_rect.y0 + patch_rect.y1)/2
                title = ax.text(-0.005, y_, name, transform=ax.transAxes,
                                    ha='right', va='center',
                                    fontdict=self.dict_args["font"])
                # title_rect = ax.transData.inverted().transform_bbox(title.get_window_extent())
                # title_x0 = title_rect.x0
                xmin, xmax = ax.get_xlim()
                if xmax > max_x:
                    max_x = xmax
                if xmin < min_x:
                    min_x = xmin

                num += 1

            # 避免有些长度大于axis0的图片看不见
            self.figure.axes[0].set_xlim(min_x, max_x)
            # 调整布局
            self.figure.tight_layout() # rect=[1,0.1,0,0.1]
            # self.figure.canvas.draw_idle()
            self.figureCanvas.draw_idle()

            # self.figure.set_figheight(12)
            # self.figure.set_figwidth(12)

        except Exception as e:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号

    def uniform_gb(self, record, features):
        current_position = 0
        new_features = []
        # 遍历所有特征
        for feature in record.features:
            feature_type = feature.type
            if (features != "All") and (feature_type not in features):
                continue
            real_gene_name = self.translator.compute_feature_label(feature)
            Fcolor, Bcolor, Tcolor, Length = self.fetch_gene_params(self.dict_args["checked gene names"],
                                                                           real_gene_name.strip(" "),
                                                                           feature_type)
            # 创建新的特征位置，从当前位置开始，长度根据类型确定
            new_location = FeatureLocation(current_position, current_position + Length,
                                           strand=feature.location.strand)
            new_feature = SeqFeature(new_location, type=feature.type,
                                     qualifiers=feature.qualifiers)
            new_features.append(new_feature)
            # 更新当前位置
            current_position += Length

        # 更新 record 的特征
        record.features = new_features
        # 更新 record 的总长度
        record.seq = "A"*current_position # record.seq[:current_position]
        return record

    def guiSave(self):
        self.DNAViewer_settings.setValue('size', self.size())

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                text = obj.currentText()
                if text:
                    allItems = [
                        obj.itemText(i) for i in range(obj.count())]
                    allItems.remove(text)
                    sortItems = [text] + allItems
                    self.DNAViewer_settings.setValue(name, sortItems)
            elif isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.DNAViewer_settings.setValue(name, state)
            elif isinstance(obj, QLineEdit):
                if name == "lineEdit":
                    font = obj.font_
                    self.DNAViewer_settings.setValue(name, font)
                else:
                    text = obj.text()
                    self.DNAViewer_settings.setValue(name, text)
            elif isinstance(obj, QTableWidget):
                if name == "tableWidget":
                    array = []  # 每一行存：[gene_name, checked], Fcolor, Bcolor, Tcolor, width, height, shape
                    for row in range(obj.rowCount()):
                        gene_name = obj.item(row, 0).text()
                        checked = "true" if obj.item(
                            row, 0).checkState() == Qt.Checked else "false"
                        Fcolor = obj.item(row, 1).text()
                        Bcolor = obj.item(row, 2).text()
                        Tcolor = obj.item(row, 3).text()
                        Length = obj.item(row, 4).text()
                        array.append([[gene_name, checked], Fcolor, Bcolor, Tcolor, Length])
                    self.DNAViewer_settings.setValue(name, array)

    def guiRestore(self):
        # self.resize(self.DNAViewer_settings.value('size', QSize(1286, 785)))
        self.resize(self.factory.judgeWindowSize(self.DNAViewer_settings, 1286, 785))
        self.factory.centerWindow(self)

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                allItems = [obj.itemText(i) for i in range(obj.count())]
                values = self.DNAViewer_settings.value(name, allItems)
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
            elif isinstance(obj, QCheckBox):
                ini_state_ = obj.isChecked()
                state_ = self.DNAViewer_settings.value(name, ini_state_)
                obj.setChecked(bool(state_))
            elif isinstance(obj, QLineEdit):
                if name == "lineEdit":
                    font = self.DNAViewer_settings.value(name, QFont("Arial", 16, QFont.Normal))
                    self.setFonttext(font)
            elif isinstance(obj, QListWidget):
                if self.dict_name_GB_path:
                    for name, path in self.dict_name_GB_path.items():
                        item = QListWidgetItem(name)
                        item.setFlags(item.flags() | Qt.ItemIsEditable)
                        item.setToolTip(path)
                        self.listWidget.addItem(item)
            elif isinstance(obj, QTableWidget):
                if name == "tableWidget":
                    ini_array = [
                        [
                            ["ATP6|ATP8", 'true'], '#ffff33', '#bfbfbf', "black", "700"], [
                            ["NAD1-6|NAD4L", 'true'], '#99ffff', '#bfbfbf', "black", "800"], [
                            ["CYTB", 'true'], '#ff9999', '#bfbfbf', "black", "700"], [
                            ["COX1-3", 'true'], '#6699ff', '#bfbfbf', "black", "700"], [
                            ["CDS", 'true'], 'orange', '#bfbfbf', "black", "700"], [
                            ["tRNA", 'true'], 'green', '#bfbfbf', "black", "400"], [
                            ["rRNA", 'true'], 'lightblue', '#bfbfbf', "black", "700"], [
                            ["misc_feature", 'false'], '#bfbfbf', '#bfbfbf', "black", "700"]]
                    array = self.DNAViewer_settings.value(name, ini_array)
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
                        item.setBackground(QColor(list_row[2]))
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                        obj.setItem(row, 2, item)
                        # col 4
                        item = QTableWidgetItem(list_row[3])
                        item.setBackground(QColor(list_row[3]))
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                        obj.setItem(row, 3, item)
                        # col 5
                        item = QTableWidgetItem(list_row[4])
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                        obj.setItem(row, 4, item)
                    obj.itemClicked.connect(self.handleItemClicked)
                    obj.resizeColumnsToContents()
                    obj.verticalHeader().setVisible(False)

    def closeEvent(self, event):
        self.guiSave()
        super().closeEvent(event)

    def handleItemClicked(self, item):
        if item.column() in [1, 2, 3]:
            color = QColorDialog.getColor(QColor(item.text()), self)
            if color.isValid():
                item.setText(color.name())
                item.setBackground(color)
            self.tableWidget.clearSelection()

    def fetch_checked_gene_names(self):
        list_names = []
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row, 0) and \
                    self.tableWidget.item(row, 0).checkState() == Qt.Checked:
                list_names.append(self.tableWidget.item(row, 0).text())
        return list_names

    def displaySettings(self):
        ###提取的设置
        self.GenBankExtract_settings = QSettings(
            self.thisPath + '/settings/GenBankExtract_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.GenBankExtract_settings.setFallbacksEnabled(False)
        self.dict_gbExtract_set = self.GenBankExtract_settings.value("set_version")
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
        # self.tabWidget.setCurrentIndex(0)

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

    def fetch_used_colors(self, col):
        list_colors = []
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row, col):
                list_colors.append(self.tableWidget.item(row, col).text())
        return list_colors

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
        color = self.factory.colorPicker(self.fetch_used_colors(1))
        item = QTableWidgetItem(color)
        item.setBackground(QColor(color))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 1, item)
        # col3
        color = self.fetch_used_colors(2)[-1]
        item = QTableWidgetItem(color)
        item.setBackground(QColor(color))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 2, item)
        # col4
        color = self.fetch_used_colors(3)[-1]
        item = QTableWidgetItem(color)
        item.setBackground(QColor(color))
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 3, item)
        # col5
        item = QTableWidgetItem("1000")
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.tableWidget.setItem(rowPosition, 4, item)
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

    @pyqtSlot()
    def on_pushButton_12_clicked(self):
        """
        move up
        """
        self.move_row_up()

    @pyqtSlot()
    def on_pushButton_13_clicked(self):
        """
        move down
        """
        self.move_row_down()

    def move_row_up(self):
        # 获取当前选中的行
        current_row = self.tableWidget.currentRow()
        if current_row > 0:
            # 获取当前行的数据
            current_row_data = []
            for col in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(current_row, col)
                if col == 0:
                    is_checked = True if item.checkState() == Qt.Checked else False
                    if item:
                        current_row_data.append([item.text(), is_checked])
                    else:
                        current_row_data.append(["", False])
                else:
                    if item:
                        current_row_data.append(item.text())
                    else:
                        current_row_data.append("")

            # 删除当前行
            self.tableWidget.removeRow(current_row)

            # 在当前行的上一行插入新行
            self.tableWidget.insertRow(current_row - 1)

            # 将数据填充到新行
            rowPosition = current_row - 1
            # col1
            item = QTableWidgetItem(current_row_data[0][0])
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
            if current_row_data[0][1]:
                item.setCheckState(Qt.Checked)
            self.tableWidget.setItem(rowPosition, 0, item)
            # col2
            item = QTableWidgetItem(current_row_data[1])
            item.setBackground(QColor(current_row_data[1]))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition, 1, item)
            # col3
            item = QTableWidgetItem(current_row_data[2])
            item.setBackground(QColor(current_row_data[2]))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition, 2, item)
            # col4
            item = QTableWidgetItem(current_row_data[3])
            item.setBackground(QColor(current_row_data[3]))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition, 3, item)
            # col5
            item = QTableWidgetItem(current_row_data[4])
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition, 4, item)
            # for col in range(self.tableWidget.columnCount()):
            #     item = QTableWidgetItem(current_row_data[col])
            #     self.tableWidget.setItem(current_row - 1, col, item)
            # 设置新的当前行
            self.tableWidget.setCurrentCell(current_row - 1, 0)

    def move_row_down(self):
        # 获取当前选中的行
        current_row = self.tableWidget.currentRow()
        if current_row < self.tableWidget.rowCount() - 1:
            # 获取当前行的数据
            current_row_data = []
            for col in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(current_row, col)
                if col == 0:
                    is_checked = True if item.checkState() == Qt.Checked else False
                    if item:
                        current_row_data.append([item.text(), is_checked])
                    else:
                        current_row_data.append(["", False])
                else:
                    if item:
                        current_row_data.append(item.text())
                    else:
                        current_row_data.append("")

            # 删除当前行
            self.tableWidget.removeRow(current_row)

            # 在当前行的下一行插入新行
            self.tableWidget.insertRow(current_row + 1)

            # 将数据填充到新行
            rowPosition = current_row + 1
            # col1
            item = QTableWidgetItem(current_row_data[0][0])
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)
            if current_row_data[0][1]:
                item.setCheckState(Qt.Checked)
            self.tableWidget.setItem(rowPosition, 0, item)
            # col2
            item = QTableWidgetItem(current_row_data[1])
            item.setBackground(QColor(current_row_data[1]))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition, 1, item)
            # col3
            item = QTableWidgetItem(current_row_data[2])
            item.setBackground(QColor(current_row_data[2]))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition, 2, item)
            # col4
            item = QTableWidgetItem(current_row_data[3])
            item.setBackground(QColor(current_row_data[3]))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition, 3, item)
            # col5
            item = QTableWidgetItem(current_row_data[4])
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition, 4, item)

            # # 将数据填充到新行
            # for col in range(self.tableWidget.columnCount()):
            #     item = QTableWidgetItem(current_row_data[col])
            #     self.tableWidget.setItem(current_row + 1, col, item)

            # 设置新的当前行
            self.tableWidget.setCurrentCell(current_row + 1, 0)

    # def setFont(self):
    #     # family = self.lineEdit.text()
    #     # size = int(self.lineEdit_2.text())
    #     font, ok = QFontDialog.getFont(QFont("Arial", 12, QFont.Normal), self)
    #     # print(font.family(), font.style(), font.weight(), font.pointSize(), font.key(), font.toString())
    #     if ok:
    #         family_ = font.family()
    #         size_ = str(font.pointSize())
    #         italic = "italic, " if font.italic() else ""
    #         bold = "bold, " if font.bold() else ""
    #         self.lineEdit.setText(f"{family_}, {italic}{bold}{size_}")
    #         self.lineEdit.font_ = font

    def fetch_name_GB_path(self):
        items_info = {}
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            text = item.text()
            tooltip = item.toolTip()
            items_info[text] = tooltip
        return items_info

    def font_prop_bytext(self, text):
        list_text = text.split(";")
        return list_text[0],list_text[1],True if "italic" in text else False,True if "bold" in text else False

    def get_font_prop(self, font):
        dict_font_style = {0: "normal", 1: "italic", 2: "oblique"}
        family_ = font.family()
        size_ = font.pointSize()
        style = dict_font_style[font.style()]
        bold = font.bold()
        return family_, size_, style, bold

    def setFont(self):
        text_ = self.lineEdit.text()
        family_, size_, style_bool, bold_bool = self.font_prop_bytext(text_)
        font_ = QFont(family_, int(size_))
        font_.setBold(bold_bool)
        font_.setItalic(style_bool)
        font, ok = QFontDialog.getFont(font_, self)
        if ok:
            self.setFonttext(font)

    def setFonttext(self, font):
        family_, size_, style, bold = self.get_font_prop(font)
        self.lineEdit.font_ = font
        self.lineEdit.setText(f"{family_};{size_}"
                              f"{';italic' if style=='italic' else ''}"
                              f"{';bold' if bold else ''}")

    def save_as(self):
        options = QFileDialog.Options()
        options |= QFileDialog.HideNameFilterDetails
        file_name, _ = QFileDialog.getSaveFileName(self, "Save As", "DNA viewer",
                                                   "PDF Files (*.pdf);;JPEG Files (*.jpg);;PNG Files (*.png);;SVG Files (*.svg)",
                                                   options=options)
        if file_name:
            # matplotlib.rcParams['figure.figsize'] = 20, 3
            self.figure.savefig(file_name)

    def fetch_gene_params(self, checked_genes, real_gene_name, feature_type):
        Fcolor, Bcolor, Tcolor, Length = "#bfbfbf", "#ff9999", "black", 1000
        for gene_name in checked_genes:
            rgx_gene_name = "-?" + "$|-?".join(gene_name.split("|")) + "$"
            num_range = re.search(r"(\d+)\-(\d+)", gene_name)
            # if num_range:
            #     nums = f'({"|".join([str(num) for num in range(int(num_range[0][0]), int(num_range[0][1])+1)])})'
            #     rgx_gene_name = re.sub(r"\d+\-\d+", nums, rgx_gene_name) # COX1-3 --> COX(1|2|3)
            word_range = re.search(r"[a-zA-Z]\-[a-zA-Z]", gene_name)
            if num_range:
                rgx_gene_name = re.sub(num_range.group(),
                                       "[%s]"%num_range.group(), rgx_gene_name, re.I)
            if word_range:
                rgx_gene_name = re.sub(word_range.group(),
                                       "[%s]"%word_range.group(), rgx_gene_name, re.I)
            rgx = re.compile(rgx_gene_name, re.I)
            # print(rgx_gene_name, real_gene_name, feature_type)
            if rgx.match(real_gene_name) or rgx.match(feature_type):
                Fcolor, Bcolor, Tcolor, Length = self.dict_args["go_parms"][gene_name]
                break
        return Fcolor, Bcolor, Tcolor, Length

    def popupException(self, exception):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, '
            'please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">'
            'https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the '
            'detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

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
        # self.auto_set_scale()
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

    def setScales(self):
        if self.tv is not None:
            self.hscale = self.doubleSpinBox.value()
            self.vscale = self.doubleSpinBox_2.value()
            '''axes = self.figure.gca()
            # 调整Axes对象的长宽比例
            axes.set_aspect(self.hscale / self.vscale)'''
            self.figure.set_size_inches(self.hscale, self.vscale)
            self.figure.canvas.draw_idle()
            # self.fit_to_window()

    def on_pick(self, event):
        # 高亮选中的图形元素
        if isinstance(event.artist, plt.Line2D) or isinstance(event.artist, plt.Text):
            event.artist.set_color('blue')
            self.figure.canvas.draw_idle()

    def on_hover(self, event):
        # if event.inaxes in self.dict_name_ax.values():
        for ax in self.figure.axes:
            for line in ax.lines:
                if line.contains(event)[0]:
                    xy, w, h = line.__dict__.get("rect_parms", (None, None, None))
                    if xy and w and h:
                        if not hasattr(line, 'rect'):
                            self.highlight_rect = patches.Rectangle(xy, w, h, edgecolor="grey", facecolor="blue", alpha=0.3)
                            ax.add_patch(self.highlight_rect)
                            self.current_highlight = line
                            line.rect = self.highlight_rect
                else:
                    if hasattr(line, 'rect'):
                        line.rect.remove()
                        del line.rect
            for text in ax.texts:
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

            self.figure.canvas.draw_idle()
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
                self.figure.canvas.draw_idle()'''

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

    # def update_multitree(self):
    #    style = self.style
    #    c, a, m = self.datingTreetree.draw_idle(ncols=3, nrows=3, ts=self.ts,
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = DNAViewer()
    ui.show()
    sys.exit(app.exec_())




