# #START_LICENSE###########################################################
#
#
# This file is part of the Environment for Tree Exploration program
# (ETE).  http://etetoolkit.org
#
# ETE is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ETE is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ETE.  If not, see <http://www.gnu.org/licenses/>.
#
#
#                     ABOUT THE ETE PACKAGE
#                     =====================
#
# ETE is distributed under the GPL copyleft license (2008-2015).
#
# If you make use of ETE in published work, please cite:
#
# Jaime Huerta-Cepas, Joaquin Dopazo and Toni Gabaldon.
# ETE: a python Environment for Tree Exploration. Jaime BMC
# Bioinformatics 2010,:24doi:10.1186/1471-2105-11-24
#
# Note that extra references to the specific methods implemented in
# the toolkit may be available in the documentation.
#
# More info at http://etetoolkit.org. Contact: huerta@embl.de
#
#
# #END_LICENSE#############################################################
from __future__ import absolute_import
from __future__ import print_function

import copy
import math
import os.path
import re
import six

# try:
#     from .qt import QtOpenGL
#     USE_GL = True
# except ImportError:
#     USE_GL = False
# from ete3 import TreeFace

from ete3.treeview.Ui_ete_qt4app import Ui_MainWindow
from src.factory import Factory
from .Lg_attribute import Lg_attribute
from .Lg_compare_tree_setting import Lg_compare_tree_setting
from .qt4_face_render import _ItemFaceItem
from .Ui_compare_setting import Ui_compare_tree_setting

USE_GL = False # Temporarily disabled

from .qt import *
from . import _mainwindow, _search_dialog, _show_newick, _open_newick, _about, Ui_annotation_editor_attr, Ui_ete_qt4app, \
    Ui_annotation_selector, \
    Ui_annotation_editor, Ui_annotation_editor2, Ui_annotation_editor3, Ui_annotation_editor_tax
from .main import save, _leaf
from .qt4_render import render
from .node_gui_actions import NewickDialog
try:
    from .._ph import new_version
except Exception:
    pass
from .. import Tree, TreeStyle, PhyloTree
import time
from . import faces
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui, QtWidgets
from .CustomWidgets import ListItemWidget, MyAttributeTableModel, MyGeneralTableView, MyNodePropTableView, \
    MyTableModel, \
    CheckableTabWidget, ComboboxDelegate, \
    MyComboBox, \
    MyImgTableModel, MyPieTableModel, MyHeatmapTableModel, MystackedBarTableModel, \
    MySeqTableModel, MyMotifTableModel, MyTextTableModel, MyBarTableModel, MyStripTableModel, \
    MyHorizBarTableModel, MyShapeTableModel, QGraphicsLeftArrowItem, QGraphicsRightArrowItem, \
    QGraphicsLeftTriangleItem, QGraphicsRightTriangleItem, QGraphicsStarItem, QGraphicsStarItem2, \
    QGraphicsTopTriangleItem, \
    QGraphicsBottomTriangleItem, QGraphicsRoundRectItem, QGraphicsDiamondItem, MyNameTableModel, \
    MyTaxTableModel
from collections import OrderedDict
from urllib.request import urlopen
from .svg_colors import COLOR_SCHEMES
import random
from .faces import _aafgcolors, _aabgcolors, _ntfgcolors, _ntbgcolors, TreeFace
from ete3.treeview import qt4_circular_render as crender


def etime(f):
    def a_wrapper_accepting_arguments(*args, **kargs):
        global TIME
        t1 = time.time()
        f(*args, **kargs)
        print(time.time() - t1)
    return a_wrapper_accepting_arguments

class CheckUpdates(QThread):
    def run(self):
        try:
            current, latest, tag = new_version()
            if tag is None:
                tag = ""
            msg = ""
            if current and latest:
                if current < latest:
                    msg = "New version available (rev%s): %s More info at http://etetoolkit.org." %\
                        (latest, tag)
                elif current == latest:
                    msg = "Up to date"

            self.emit(SIGNAL("output(QString)"), msg)
        except Exception:
            pass

class _GUI(QMainWindow, Ui_MainWindow):
    def _updatestatus(self, msg):
        # self.main.statusbar.showMessage(msg)
        self.statusbar.showMessage(msg)

    def redraw(self):
        self.scene.draw()
        self.view.init_values()

    def __init__(self, scene, *args):
        QMainWindow.__init__(self, *args)
        screenSize = QApplication.primaryScreen().size()
        self.setupUi(self)
        self.setWindowTitle("PhyloSuite (ETE Tree Browser)")
        self.setAcceptDrops(True)
        self.installEventFilter(self)
        self.factory = Factory()

        # compare mode
        self.compare_mode = False
        self.toolButton.setHidden(True)
        self.toolButton_2.setHidden(True)
        self.toolButton_3.setHidden(True)
        self.toolButton.toggled.connect(lambda bool_: [self.toolButton_2.setChecked(not bool_),
                                                       self.tree_switch()])
        self.toolButton_2.toggled.connect(lambda bool_: [self.toolButton.setChecked(not bool_),
                                                         self.tree_switch()])
        self.dict_tree_names = {"tree": [], "tree1": [], "tree2": []}

        self.scene = scene
        self.scene.GUI = self
        self.view.parent = self
        self.view.setScene(scene)
        self.view.init_values()
        self.scene.view = self.view
        self.listWidget.installEventFilter(self)
        self.listWidget.init_(self.stackedWidget, parent=self)
        # for comparison mode
        self.listWidget.itemChanged.connect(self.store_faces)
        self.listWidget.itemDoubleClicked.connect(lambda item: self.listWidget.itemWidget(item).edit_label())

        self.node_prop_table.parent = self
        self.view.node_prop_table = self.node_prop_table

        # basic parameters table
        self.general_table.parent = self

        self.add_ann_btn.clicked.connect(self.on_annotation_btn_clicked)
        self.add_ann_btn.installEventFilter(self)

        # Don't resize left panel if it's not needed
        self.tabWidget.setMinimumWidth(screenSize.width() * 0.20) # make
        self.splitter_2.setStretchFactor(0, 5)
        self.splitter_2.setStretchFactor(1, 1)
        self.listWidget.setMinimumWidth(screenSize.width() * 0.14) # make
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 20)

        # I create a single dialog to keep the last search options
        self.searchDialog = QDialog()
        # Don't know if this is the best way to set up the dialog and
        # its variables
        self.searchDialog._conf = _search_dialog.Ui_Dialog()
        self.searchDialog._conf.setupUi(self.searchDialog)

        self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)

        self.setGeometry(
            screenSize.width() * 0.2,
            screenSize.height() * 0.2,
            screenSize.width() * 0.9,
            screenSize.height() * 0.85,
            )
        self.centerWindow(self)

        # Shows the whole tree by default
        # self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

        self.face_base_parameters = [
            ["Position", ["aligned", "branch-right", "branch-top", "branch-bottom", "float", "float-behind"]],
            ["margin_left", 3],
            ["margin_right", 0],
            ["margin_top", 0],
            ["margin_bottom", 0],
            ["opacity", 1.0],
            ["rotable", True],
            ["rotation", 0],
            ["horizontal align", ["left", "center", "right"]],
            ["vertical align", ["center", "top", "bottom"]],
            ["background", "None color"],
            ["inner_background", "None color"],
            ["border", False],
            ["border.type", ["solid", "dashed", "dotted"]],
            ["border.width", 0],
            ["border.color", "#000000"],
            ["inner_border", False],
            ["inner_border.type", ["solid", "dashed", "dotted"]],
            ["inner_border.width", 0],
            ["inner_border.color", "#000000"],
        ]
        if self.scene.tree:
            self.init_GUI()
            self.view.fitInView(0, 0, self.scene.sceneRect().width(), 200, Qt.KeepAspectRatio)

    def number_node(self):
        if self.compare_mode == "tree1":
            tree_type = "tree1"
        elif self.compare_mode == "tree2":
            tree_type = "tree2"
        else:
            tree_type = "tree"
        for node in self.scene.tree.traverse():
            if not hasattr(node, "id"):
                name = node.name if node.name else "node"
                suffix = "_" if node.name else ""
                new_name, self.dict_tree_names[tree_type] = self.factory.numbered_Name(self.dict_tree_names[tree_type],
                    name, omit=True, suffix=suffix)
                node.add_feature("id", new_name)
                # node.name = new_name
            else:
                if node.id not in self.dict_tree_names[tree_type]:
                    self.dict_tree_names[tree_type].append(node.id)

    def init_GUI(self, force_new=False, nodraw=False):
        self.init_tree_props()
        # number node
        self.number_node()
        self.on_actionLeafName_triggered(auto_array=True)
        # array = [[node.id, node.name, "#000000", "None color"] for node in self.scene.tree.traverse() if node.is_leaf()]
        # self.create_annotation_editor("Leaf name", array_=array,
        #                                         include_inner_nodes=False,
        #                                         force_new=force_new,
        #                                         nodraw=nodraw)

    def init_tree_props(self, ignore_init=False):
        # if self.scene.img.show_branch_length:
        #     self.actionBranchLength.setChecked(True)
        # else:
        #     self.actionBranchLength.setChecked(False)
        # if self.scene.img.show_branch_support:
        #     self.actionBranchSupport.setChecked(True)
        # else:
        #     self.actionBranchSupport.setChecked(False)
        # if self.scene.img.show_leaf_name:
        #     self.main.actionLeafName.setChecked(True)
        if self.scene.img.force_topology:
            self.actionForceTopology.setChecked(True)
        else:
            self.actionForceTopology.setChecked(False)
        if self.scene.img.mode == "c":
            self.actionCircularTree.setChecked(True)
        else:
            self.actionCircularTree.setChecked(False)
        if not ignore_init:
            self.general_table.init_table()

    def centerWindow(self, window):
        frameGm = window.frameGeometry()
        screen = QApplication.desktop().screenNumber(
            QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        window.move(frameGm.topLeft())

    @QtCore.pyqtSlot()
    def on_actionETE_triggered(self):
        try:
            __version__
        except:
            __version__= "development branch"

        d = QDialog()
        d._conf = _about.Ui_About()
        d._conf.setupUi(d)
        d._conf.version.setText("Version: %s" %__version__)
        d._conf.version.setAlignment(Qt.AlignHCenter)
        d.exec_()

    @QtCore.pyqtSlot()
    def on_actionZoomOut_triggered(self):
        self.view.safe_scale(0.8,0.8)

    @QtCore.pyqtSlot()
    def on_actionZoomIn_triggered(self):
        self.view.safe_scale(1.2,1.2)

    @QtCore.pyqtSlot()
    def on_actionZoomInX_triggered(self):
        # self.scene.img._scale += self.scene.img._scale * 0.05
        if not self.scene.img.scale:
            self.scene.img.scale = 80
        self.scene.img.scale += self.scene.img.scale * 0.05
        self.general_table.init_table()
        self.redraw()

    @QtCore.pyqtSlot()
    def on_actionZoomOutX_triggered(self):
        if not self.scene.img.scale:
            self.scene.img.scale = 80
        self.scene.img.scale -= self.scene.img.scale * 0.05
        self.general_table.init_table()
        self.redraw()

    @QtCore.pyqtSlot()
    def on_actionZoomInY_triggered(self):
        self.scene.img.branch_vertical_margin += 5
        self.scene.img._scale = None
        self.general_table.init_table()
        self.redraw()

    @QtCore.pyqtSlot()
    def on_actionZoomOutY_triggered(self):
        if self.scene.img.branch_vertical_margin > 0:
            margin = self.scene.img.branch_vertical_margin - 5
            if margin > 0:
                self.scene.img.branch_vertical_margin = margin
            else:
                self.scene.img.branch_vertical_margin = 0.0
            self.scene.img._scale = None
            self.general_table.init_table()
            self.redraw()

    @QtCore.pyqtSlot()
    def on_actionFit2tree_triggered(self):
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    @QtCore.pyqtSlot()
    def on_actionFit2region_triggered(self):
        R = self.view.selector.rect()
        if R.width()>0 and R.height()>0:
            self.view.fitInView(R.x(), R.y(), R.width(),\
                                    R.height(), Qt.KeepAspectRatio)

    @QtCore.pyqtSlot()
    def on_actionSearchNode_triggered(self):
        setup = self.searchDialog._conf
        setup.attrValue.setFocus()
        ok = self.searchDialog.exec_()
        if ok:
            mType = setup.attrType.currentIndex()
            aName = str(setup.attrName.text())
            if mType >= 2 and mType <=6:
                try:
                    aValue =  float(setup.attrValue.text())
                except ValueError:
                    QMessageBox.information(self, "!",\
                                              "A numeric value is expected")
                    return
            elif mType == 7:
                aValue = re.compile(str(setup.attrValue.text()))
            elif mType == 0 or mType == 1:

                aValue =  str(setup.attrValue.text())

            if mType == 1 or mType == 2: #"is or =="
                cmpFn = lambda x,y: x == y
            elif mType == 0: # "contains"
                cmpFn = lambda x,y: y in x
            elif mType == 3:
                cmpFn = lambda x,y: x >= y
            elif mType == 4:
                cmpFn = lambda x,y: x > y
            elif mType == 5:
                cmpFn = lambda x,y: x <= y
            elif mType == 6:
                cmpFn = lambda x,y: x < y
            elif mType == 7:
                cmpFn = lambda x,y: re.search(y, x)

            last_match_node = None
            for n in self.scene.tree.traverse(is_leaf_fn=_leaf):
                if setup.leaves_only.isChecked() and not _leaf(n):
                    continue
                if hasattr(n, aName) \
                        and cmpFn(getattr(n, aName), aValue ):
                    self.scene.view.highlight_node(n, permanent=True)
                    last_match_node = n

            if last_match_node:
                item = self.scene.n2i[last_match_node]
                R = item.mapToScene(item.fullRegion).boundingRect()
                R.adjust(-60, -60, 60, 60)
                self.view.fitInView(R.x(), R.y(), R.width(),\
                                    R.height(), Qt.KeepAspectRatio)


    @QtCore.pyqtSlot()
    def on_actionClear_search_triggered(self):
        # This could be much more efficient
        for n in list(self.view.n2hl.keys()):
            self.scene.view.unhighlight_node(n)

    @QtCore.pyqtSlot()
    def on_actionBranchLength_triggered(self):
        # if self.actionBranchLength.isChecked():
        #     self.general_table.set_style("show_branch_length", True)
        # else:
        #     self.general_table.set_style("show_branch_length", False)
        # # self.scene.img.show_branch_length ^= True
        # self.scene.img._scale = None
        # self.redraw()
        # self.view.centerOn(0,0)
        editor_dict_args = {"current attribute": "Branch length"}
        self.create_annotation_editor("Attributes", editor_dict_args=editor_dict_args)

    @QtCore.pyqtSlot()
    def on_actionBranchSupport_triggered(self):
        # if self.actionBranchSupport.isChecked():
        #     self.general_table.set_style("show_branch_support", True)
        # else:
        #     self.general_table.set_style("show_branch_support", False)
        # # self.scene.img.show_branch_support ^= True
        # self.scene.img._scale = None
        # self.redraw()
        # self.view.centerOn(0,0)
        editor_dict_args = {"current attribute": "Support"}
        self.create_annotation_editor("Attributes", editor_dict_args=editor_dict_args)

    @QtCore.pyqtSlot()
    def on_actionLeafName_triggered(self, auto_array=False):
        if auto_array:
            array = [[node.id, node.name, "#000000", "None color"] for node in self.scene.tree.traverse() if node.is_leaf()]
        else:
            array = None
        self.create_annotation_editor("Leaf name", array_=array, include_inner_nodes=False)
        # self.scene.img.show_leaf_name ^= True
        # self.scene.img._scale = None
        # self.redraw()
        # self.view.centerOn(0,0)

    @QtCore.pyqtSlot()
    def on_actionForceTopology_triggered(self):
        # self.scene.img.mode = "r"
        if self.actionForceTopology.isChecked():
            self.general_table.set_style("force_topology", True)
        else:
            self.general_table.set_style("force_topology", False)
        self.scene.img._scale = None
        self.redraw()
        self.view.centerOn(0,0)

    @QtCore.pyqtSlot()
    def on_actionUltrametric_triggered(self):
        reply = QMessageBox.question(
            self,
            "PhyloSuite ETE3",
            "<p style='line-height:25px; height:25px'>Are you certain that you want to convert the tree to ultrametric? "
            "It cannot be reversed! </p>",
            QMessageBox.Yes,
            QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            self.scene.tree.convert_to_ultrametric(strategy="fixed")
            self.scene.img._scale = None
            self.redraw()
            self.view.centerOn(0,0)

    @QtCore.pyqtSlot()
    def on_actionShow_newick_triggered(self):
        d = NewickDialog(self.scene.tree)
        d._conf = _show_newick.Ui_Newick()
        d._conf.setupUi(d)
        d.update_newick()
        d.exec_()

    @QtCore.pyqtSlot()
    def on_actionChange_orientation_triggered(self):
        self.scene.props.orientation ^= 1
        self.redraw()

    @QtCore.pyqtSlot()
    def on_actionShow_phenogram_triggered(self):
        self.scene.props.style = 0
        self.redraw()

    @QtCore.pyqtSlot()
    def on_actionShowCladogram_triggered(self):
        self.scene.props.style = 1
        self.redraw()

    @QtCore.pyqtSlot()
    def on_actionOpen_triggered(self):
        # d = QFileDialog()
        # d._conf = _open_newick.Ui_OpenNewick()
        # d._conf.setupUi(d)
        # d.exec_()
        # return
        fname = QFileDialog.getOpenFileName(self, "Open Tree File")
        t = self.factory.read_tree(fname[0], parent=self)
        if t:
            self.clear_trees()
            self.clear_faces()
            self.scene.tree = t
            self.scene.img = TreeStyle()
            self.init_GUI()
            # self.redraw()

    @QtCore.pyqtSlot()
    def on_actionSave_newick_triggered(self):
        fname = QFileDialog.getSaveFileName(self ,"Save tree File",
                                                 "tree",
                                                 "Newick (*.nwk *.nh *.nhx *.nw )")
        nw = self.scene.tree.write()
        try:
            OUT = open(fname[0],"w")
        except Exception as e:
            print(e)
        else:
            OUT.write(nw)
            OUT.close()
            QMessageBox.information(
                self,
                "PhyloSuite ETE3",
                "<p style='line-height:25px; height:25px'>The tree are saved successfully! </p>")

    @QtCore.pyqtSlot()
    def on_actionRenderPDF_triggered(self):
        fname = QFileDialog.getSaveFileName(self ,"Save to PDF File",
                                        "tree",
                                        "PDF (*.pdf)")
        if fname[0]:
            save(self.scene, fname[0])
            QMessageBox.information(
                self,
                "PhyloSuite ETE3",
                "<p style='line-height:25px; height:25px'>The tree figure are saved successfully! </p>")

    @QtCore.pyqtSlot()
    def on_actionSave_as_figure_triggered(self):
        fname = QFileDialog.getSaveFileName(
                                self, "Save tree to file", "tree",
                                        "SVG format (*.svg);;"
                                        "PDF Format (*.pdf);;"
                                        "PNG format (*.png);;")
        if fname[0]:
            save(self.scene, fname[0])
            QMessageBox.information(
                self,
                "PhyloSuite ETE3",
                "<p style='line-height:25px; height:25px'>The tree figure are saved successfully! </p>")

    @QtCore.pyqtSlot()
    def on_actionRender_selected_region_triggered(self):
        if not self.scene.selector.isVisible():
            return QMessageBox.information(self, "!",\
                                              "You must select a region first")

        F = QFileDialog(self)
        if F.exec_():
            imgName = str(F.selectedFiles()[0])
            if not imgName.endswith(".pdf"):
                imgName += ".pdf"
            save(imgName, take_region=True)

    @QtCore.pyqtSlot()
    def on_actionPaste_newick_triggered(self):
        text,ok = QInputDialog.getText(self,\
                                                 "Paste Newick",\
                                                 "Newick:")
        if ok:
            try:
                t = Tree(str(text))
            except Exception as e:
                print(e)
            else:
                self.scene.tree = t
                self.redraw()
                self.view.centerOn(0,0)

    @QtCore.pyqtSlot()
    def on_actionCircularTree_triggered(self):
        # if self.main.actionCircularTree.isChecked():
        if self.actionCircularTree.isChecked():
            self.general_table.set_style("mode", ["Circular", "Rectangular"])
        else:
            self.general_table.set_style("mode", ["Rectangular", "Circular"])
        self.scene.img._scale = None
        self.redraw()
        self.view.centerOn(0,0)

    @QtCore.pyqtSlot()
    def on_actionload_session_triggered(self):
        fname = QFileDialog.getOpenFileName(self, "Open tree annotation File",
                                                    filter="PhyloSuite Format(*.phst);;")
        if fname[0]:
            settings = QSettings(fname[0], QSettings.IniFormat)
            # File only, no fallback to registry or or.
            settings.setFallbacksEnabled(False)
        else:
            return
        self.clear_trees()
        type_ = settings.value("type")
        if type_ == "tanglegram":
            self.actioncompare_mode.setChecked(True)
            self.on_actioncompare_mode_triggered(show=False)
            # self.dict_compare_args = settings.value("setting parameters")
            self.compare_setting.resume_GUI(settings.value("setting parameters"))
            self.dict_compare_args = self.compare_setting.get_parameters() # tree1\tree2\dict_shape were removed when saving, so need to retrieve them again
            # space
            space = settings.value("tree space")
            # tree2
            ts2 = TreeStyle()
            ts2.legend_position = 2
            ts2.orientation = 1
            # delete faces, must call this function before we set self.compare_mode
            self.clear_faces()
            self.compare_mode = "tree2"
            settings.beginGroup("tree2")
            tre2 = self.load_tree_annotation(settings, ts2)
            settings.endGroup()
            # tree1
            ts1 = TreeStyle()
            ts1.margin_right = space
            ts1.legend_position = 1
            # add t2 to the right of t1
            tree_face2 = TreeFace(tre2, ts2)
            ts1.aligned_treeface_hz.add_face(tree_face2, column=0)
            # delete faces, must call this function before we set self.compare_mode
            self.clear_faces()
            self.compare_mode = "tree1"
            settings.beginGroup("tree1")
            self.load_tree_annotation(settings, ts1)
            settings.endGroup()
            self.toolButton.setChecked(True)
        else:
            self.clear_faces()
            settings.beginGroup("tree")
            self.load_tree_annotation(settings, TreeStyle())
            settings.endGroup()
        settings.beginGroup("Transform")
        self.view.setTransform(settings.value("transform"))
        settings.endGroup()

    @QtCore.pyqtSlot()
    def on_action_style_brush_triggered(self):
        fname = QFileDialog.getOpenFileName(self, "Open tree annotation File",
            filter="PhyloSuite Format(*.phst);;")
        if fname[0]:
            settings = QSettings(fname[0], QSettings.IniFormat)
            # File only, no fallback to registry or or.
            settings.setFallbacksEnabled(False)
        else:
            return
        self.clear_faces()
        settings.beginGroup("tree")
        self.load_tree_annotation(settings, TreeStyle(), type="brush")
        settings.endGroup()
        settings.beginGroup("Transform")
        self.view.setTransform(settings.value("transform"))
        settings.endGroup()

    def load_tree_annotation(self, settings, ts, type="normal"):
        if type != "brush":
            settings.beginGroup("NHX tree")
            tree_str = settings.value("Tree NHX")
            settings.endGroup()
            try:
                t = Tree(tree_str, format=2) # PhyloTree not work
            except Exception as e:
                print(e)
                QMessageBox.critical(
                    self,
                    "Tree file",
                    "<p style='line-height:25px; height:25px'>Bad format of the tree!</p>",
                    QMessageBox.Yes)
            else:
                del self.scene.tree
                self.scene.tree = t
                self.scene.img = ts # TreeStyle()
        # assign id
        settings.beginGroup("Nodes")
        node_ids = settings.childKeys()
        load_node_ids = [node.id for node in self.scene.tree.traverse() if hasattr(node, "id")]
        list_empty_ids = list(set(node_ids).difference(set(load_node_ids)))
        settings.endGroup()
        if self.compare_mode == "tree1":
            tree_type = "tree1"
        elif self.compare_mode == "tree2":
            tree_type = "tree2"
        else:
            tree_type = "tree"
        for node in self.scene.tree.traverse():
            if not hasattr(node, "id"):
                if list_empty_ids:
                    id = list_empty_ids.pop()
                    self.dict_tree_names[tree_type].append(id)
                    node.add_feature("id", id)
                else:
                    new_name, self.dict_tree_names[tree_type] = self.factory.numbered_Name(self.dict_tree_names[tree_type],
                        "node", omit=True, suffix="")
                    node.add_feature("id", new_name)
            else:
                if node.id not in self.dict_tree_names[tree_type]:
                    self.dict_tree_names[tree_type].append(node.id)
        settings.beginGroup("Tree style")
        self.scene.img.__dict__.update(settings.value("tree style dict"))
        self.general_table.init_table()
        settings.endGroup()
        settings.beginGroup("Nodes")
        node_ids = settings.childKeys()
        for node_id in node_ids:
            nodes = self.scene.tree.search_nodes(id=node_id)
            if nodes:
                node = nodes[0]
                node.__dict__.update(settings.value(node_id))
            else:
                print(f"{node_id} not have id!")
        settings.endGroup()
        settings.beginGroup("Faces")
        editor_index = settings.childKeys()
        for index in editor_index:
            dict_params = settings.value(index)
            tab_text = dict_params["tab_text"]
            # if (type == "brush") and (tab_text == "Leaf name"):
            #     continue
            tab_check_State = dict_params["tab_check_State"]
            tab_tableView_array = dict_params["tab_tableView_array"]
            editor_tableView_array = dict_params["editor_tableView_array"]
            editor_tableView_header = dict_params["editor_tableView_header"]
            editor_tableheader_checkstate = dict_params["editor_tableheader_checkstate"]
            editor_dict_args = dict_params["editor_dict_args"]
            array_check_states = dict_params["array_check_states"]
            include_inner_nodes = dict_params["include_inner_nodes"]
            tab_check_State = True if tab_check_State in ["true", True] else False
            self.create_annotation_editor(tab_text, array_=editor_tableView_array,
                                                    header=editor_tableView_header,
                                                    configs=tab_tableView_array,
                                                    force_new=True,
                                                    tabIsChecked=tab_check_State,
                                                    header_state=editor_tableheader_checkstate,
                                                    array_check_states=array_check_states,
                                                    include_inner_nodes=include_inner_nodes,
                                                    editor_dict_args=editor_dict_args)
        settings.endGroup()
        # self.redraw()
        return self.scene.tree

    @QtCore.pyqtSlot()
    def on_actionsaveSession_triggered(self):
        if not self.scene.tree:
            QMessageBox.information(
                self,
                "PhyloSuite ETE3",
                "<p style='line-height:25px; height:25px'>No trees! </p>")
            return
        fname = QFileDialog.getSaveFileName(self, "Save current annotation to File",
            "tree_annotation",
            "PHST (*.phst)")
        if fname[0]:
            settings = QSettings(fname[0], QSettings.IniFormat)
            # File only, no fallback to registry or or.
            settings.setFallbacksEnabled(False)
            settings.clear()
        else:
            return
        if self.compare_mode:
            settings.setValue("type", "tanglegram")
            settings.setValue("tree space", self.dict_compare_args["space"])
            parameters = self.compare_setting.get_parameters()
            # parameters.pop("dict_shape")
            parameters.pop("tree1")
            parameters.pop("tree2")
            settings.setValue("setting parameters", parameters)
            # tree2
            self.toolButton_2.setChecked(True)
            settings.beginGroup("tree2")
            self.save_tree_annotations(settings)
            settings.endGroup()
            # tree1
            self.toolButton.setChecked(True)
            settings.beginGroup("tree1")
            self.save_tree_annotations(settings)
            settings.endGroup()
        else:
            settings.setValue("type", "normal tree")
            settings.beginGroup("tree")
            self.save_tree_annotations(settings)
            settings.endGroup()
        settings.beginGroup("Transform")
        settings.setValue("transform", self.view.transform())
        settings.endGroup()
        QMessageBox.information(
            self,
            "PhyloSuite ETE3",
            "<p style='line-height:25px; height:25px'>The tree and the annotation are saved successfully! </p>")

    def save_tree_annotations(self, settings):
        settings.beginGroup("Tree style")
        dict_style = {attr:self.scene.img.__dict__[attr] for attr in self.scene.img.__dict__ if
                                                                  attr not in ['aligned_header',
                                                                                 'aligned_foot',
                                                                                 'aligned_treeface_vt',
                                                                                 'aligned_treeface_hz',
                                                                                 'legend',
                                                                                 'title']} # _layout_handler?
        settings.setValue("tree style dict", dict_style)
        settings.endGroup()
        settings.beginGroup("Nodes")
        for node in self.scene.tree.traverse():
            # how to reserve lambda function?
            # face will be saved independently,must remove _up and _children too
            if not hasattr(node, "id"):
                if self.compare_mode == "tree1":
                    tree_type = "tree1"
                elif self.compare_mode == "tree2":
                    tree_type = "tree2"
                else:
                    tree_type = "tree"
                new_name, self.dict_tree_names[tree_type] = self.factory.numbered_Name(self.dict_tree_names[tree_type],
                    "node", omit=True, suffix="")
                node.add_feature("id", new_name)
            dict_node_attr = {attr:node.__dict__[attr] for attr in node.__dict__ if attr not in ['_speciesFunction',
                                                                                                 '_faces',
                                                                                                 '_up',
                                                                                                 '_children',
                                                                                                 '_temp_faces']}
            # print(dict_node_attr)
            settings.setValue(node.id, dict_node_attr)
            # node.__dict__["_speciesFunction"] = _speciesFunction
            # node.__dict__["_faces"] = _faces
            # if not hasattr(node, "id"):
            #     node.add_feature("id", f"node{self.inner_node_ID}")
            #     self.inner_node_ID += 1
            # settings.beginGroup(node.id)
            # for attr in node.__dict__:
            #     if attr not in ['_speciesFunction', '_faces']:
            #         settings.setValue(attr, node.__dict__[attr])
            # settings.endGroup()
        settings.endGroup()
        settings.beginGroup("NHX tree")
        settings.setValue("Tree NHX", self.scene.tree.write(features=[], format=2))
        settings.endGroup()
        settings.beginGroup("Faces")
        for item_index in range(self.listWidget.count()):
            tab_text = self.listWidget.item_text(item_index)
            tab_check_State = self.listWidget.isChecked(item_index)
            tab_widget = self.listWidget.get_page_widget(item_index)
            tab_tableView_array = tab_widget.tableview.model().arraydata
            editor = tab_widget.tableview.editor
            editor_tableView_array = editor.ui.tableView.model().arraydata
            editor_tableView_header = editor.ui.tableView.model().header
            editor_tableheader_checkstate = editor.ui.tableView.model().hheader.isOn if hasattr(editor.ui.tableView.model(), "hheader") else None
            editor_dict_args = editor.ui.get_parameters() if hasattr(editor.ui, "get_parameters") else None
            array_check_states = editor.ui.tableView.model().check_states if hasattr(editor.ui.tableView.model(), "check_states") else None
            dict_params = {"tab_text": tab_text,
                           "tab_check_State": tab_check_State,
                           "tab_tableView_array": tab_tableView_array,
                           "editor_tableView_array": editor_tableView_array,
                           "editor_tableView_header": editor_tableView_header,
                           "editor_dict_args": editor_dict_args,
                           "editor_tableheader_checkstate": editor_tableheader_checkstate,
                           "array_check_states": array_check_states,
                           "include_inner_nodes": editor.include_inner_nodes}
            settings.setValue(str(item_index), dict_params)
        settings.endGroup()

    @QtCore.pyqtSlot()
    def on_actioncompare_mode_triggered(self, show=True, ignore_clear_tree=False):
        if self.actioncompare_mode.isChecked():
            self.clear_trees(init_mode=False)
            self.toolButton.setHidden(False)
            self.toolButton_2.setHidden(False)
            self.toolButton_3.setHidden(False)
            self.compare_setting = Lg_compare_tree_setting(self)
            self.compare_setting.pushButton.clicked.connect(lambda :
                                                                [self.init_two_trees(self.compare_setting.get_parameters()),
                                                                 self.compare_setting.close()])
            self.compare_setting.setWindowFlags(self.compare_setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
            self.toolButton_3.clicked.connect(self.compare_setting.show)
            if ["Position", ["aligned", "branch-right",
                             "branch-top", "branch-bottom", "float", "float-behind"]] in self.face_base_parameters:
                index_pos = self.face_base_parameters.index(["Position",
                                                             ["aligned", "branch-right", "branch-top",
                                                              "branch-bottom", "float", "float-behind"]])
                self.face_base_parameters[index_pos] = ["Position",
                                                        ["branch-right", "aligned", "branch-top",
                                                         "branch-bottom", "float", "float-behind"]]
            if show:
                self.compare_setting.show()
        else:
            # in order to remove tree correctly
            if not ignore_clear_tree:
                self.clear_trees(init_mode=False)
            self.clear_faces()
            self.toolButton.setChecked(True)
            self.compare_mode = False
            self.toolButton.setHidden(True)
            self.toolButton_2.setHidden(True)
            self.toolButton_3.setHidden(True)
            try:
                self.toolButton_3.clicked.disconnect()
            except:
                pass
            if ["Position", ["branch-right", "aligned", "branch-top",
                             "branch-bottom", "float", "float-behind"]] in self.face_base_parameters:
                index_pos = self.face_base_parameters.index(["Position",
                                                             ["branch-right", "aligned", "branch-top",
                                                              "branch-bottom", "float", "float-behind"]])
                self.face_base_parameters[index_pos] = ["Position",
                                                        ["aligned", "branch-right",
                                                         "branch-top", "branch-bottom", "float", "float-behind"]]

    def on_annotation_btn_clicked(self):
        annotation_selector = QDialog(self)
        ui = Ui_annotation_selector.Ui_annotation_selector()
        ui.setupUi(annotation_selector)
        ui.pushButton.clicked.connect(lambda : [self.create_annotation_editor(ui.comboBox.currentText(),
                                                                include_inner_nodes=ui.checkBox.isChecked()),
                                                                    annotation_selector.close()])
        annotation_selector.setWindowFlags(annotation_selector.windowFlags() | Qt.WindowMinMaxButtonsHint)
        annotation_selector.show()

    def keyPressEvent(self,e):
        key = e.key()
        control = e.modifiers() & Qt.ControlModifier
        if key == 77:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        elif key >= 49 and key <= 58:
            key = key - 48
            m = self.view.transform()
            m.reset()
            self.view.setTransform(m)
            self.view.scale(key, key)

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        if type(obj) in [QGraphicsView, QListWidget, QPushButton]:
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                for file in files:
                    self.handle_iTOL_files(file)
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(_GUI, self).eventFilter(obj, event)  # 0

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
        tab = QtWidgets.QWidget(self.stackedWidget)
        Layout = QtWidgets.QVBoxLayout(tab)
        tableview = QtWidgets.QTableView(tab)
        tableview.data_edit_btn = QPushButton("Data editor", tab)
        tableview.data_edit_btn.setIcon(QIcon(":/picture/resourses/edit2.png"))
        tableview.refresh_btn = QPushButton("Refresh tree", tab)
        tableview.refresh_btn.setIcon(QIcon(":/picture/resourses/refresh-icon.png"))
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
        face_widget.btn_close.clicked.connect(self.listWidget.removeItem)
        return tableview

    def handle_iTOL_files(self, file):
        with open(file) as f:
            content = f.read()
        dataset_type = re.search(r"DATASET_\w+|^LABELS", content).group() if re.search(r"DATASET_\w+|^LABELS", content) else None
        separator = re.search(r"SEPARATOR (\w+)", content).group(1) if re.search(r"SEPARATOR (\w+)", content) else ","
        if separator == "COMMA":
            separator = ","
        elif separator == "SPACE":
            separator = " "
        elif separator == "TAB":
            separator = "\t"
        label = re.search(r"DATASET_LABEL%s(.+)\n"%separator, content).group(1) if re.search(r"DATASET_LABEL%s(.+)\n"%separator, content) else "DATA"
        if not dataset_type:
            return
        if dataset_type == "DATASET_DOMAINS":
            configs = [
                            ["Width factor", 1.2],
                            ["Height", 40],
                            ["Height factor", 0.7],
                            ["Margin", 10],
                            ["Label font", QFont("Arial", 9, QFont.Normal)],
                            ["Label color", "#000000"],
                            ["Border size", 1],
                            ["Border color", "#d7dada"],
                            ["Show backbone", True],
                            ["Show strand", True],
                        ] + copy.deepcopy(self.face_base_parameters)
            tableview = self.add_tableView(configs, label)
            # tableview.list_item.name = "domains"
            # tableview.model().dataChanged.connect(lambda :
            #                                       self.draw_domain(tableview, content,
            #                                                                separator, mode="rep"))
            tableview.refresh_btn.clicked.connect(lambda : self.draw_domain(tableview, content,
                                                                                        separator, mode="rep"))
            self.draw_domain(tableview, content, separator, mode="new")
        elif dataset_type == "LABELS":
            data = re.search(r"(?sm)^DATA(\s+.+)", content).group(1) if re.search(r"(?sm)^DATA(\s+.+)", content) else None
            if data:
                array = []
                for i in data.split("\n"):
                    list_line = i.split(separator)
                    if len(list_line) == 2:
                        array.append(list_line + ["#000000", "None color"])
                self.create_annotation_editor("Leaf name",
                                            array_=array,
                                            include_inner_nodes=False)
        elif dataset_type == "DATASET_COLORSTRIP":
            data = re.search(r"(?sm)^DATA(\s+.+)", content).group(1) if re.search(r"(?sm)^DATA(\s+.+)", content) else None
            if data:
                array = []
                for i in data.split("\n"):
                    list_line = i.split(separator)
                    if len(list_line) == 3:
                        array.append([list_line[0], list_line[1]])
                self.create_annotation_editor("Color strip",
                                              array_=array,
                                              include_inner_nodes=True)
        elif dataset_type == "DATASET_TEXT":
            data = re.search(r"(?sm)^DATA(\s+.+)", content).group(1) if re.search(r"(?sm)^DATA(\s+.+)", content) else None
            if data:
                array = []
                for i in data.split("\n"):
                    list_line = i.split(separator)
                    if len(list_line) == 7:
                        array.append([list_line[0], list_line[1], list_line[3]])
                self.create_annotation_editor("Text",
                                              array_=array,
                                              include_inner_nodes=True)
        elif dataset_type == "DATASET_SIMPLEBAR":
            data = re.search(r"(?sm)^DATA(\s+.+)", content).group(1) if re.search(r"(?sm)^DATA(\s+.+)", content) else None
            if data:
                array = []
                for i in data.split("\n"):
                    list_line = i.split(separator)
                    if len(list_line) == 2:
                        array.append([list_line[0], list_line[1]])
                self.create_annotation_editor("Horizontal bar chart",
                                              array_=array,
                                              include_inner_nodes=True)

    def add_base_parameters(self, configs, face, model):
        dict_configs = dict(configs)
        setattr(face, "margin_left", float(dict_configs["margin_left"]))
        setattr(face, "margin_right", float(dict_configs["margin_right"]))
        setattr(face, "margin_top", float(dict_configs["margin_top"]))
        setattr(face, "margin_bottom", float(dict_configs["margin_bottom"]))
        setattr(face, "opacity", float(dict_configs["opacity"]))
        setattr(face, "rotable", dict_configs["rotable"])
        if dict_configs["rotable"]:
            setattr(face, "rotation", int(dict_configs["rotation"]))
        comb_map1 = {"left": 0, "center": 1, "right": 2}
        setattr(face, "hz_align", comb_map1[dict_configs["horizontal align"][0]])
        comb_map2 = {"top": 0, "center": 1, "bottom": 2}
        setattr(face, "vt_align", comb_map2[dict_configs["vertical align"][0]])
        setattr(face.background, "color", dict_configs["background"] if dict_configs["background"] != "None color" else None)
        setattr(face.inner_background, "color", dict_configs["inner_background"] if dict_configs["inner_background"] != "None color" else None)
        comb_map3 = {"solid": 0, "dashed": 1, "dotted": 2}
        if dict_configs["border"]:
            setattr(face.border, "type", comb_map3[dict_configs["border.type"][0]])
            setattr(face.border, "width", float(dict_configs["border.width"]))
            setattr(face.border, "color", dict_configs["border.color"])
        if dict_configs["inner_border"]:
            setattr(face.inner_border, "type", comb_map3[dict_configs["inner_border.type"][0]])
            setattr(face.inner_border, "width", float(dict_configs["inner_border.width"]))
            setattr(face.inner_border, "color", dict_configs["inner_border.color"])
        return face

    def bar_plot(self, node, width, height, color, value, height_factor, min_value, max_value):
        # show text
        # Add node name within the ellipse
        text = QGraphicsSimpleTextItem(str(value))
        th = text.boundingRect().height()
        tw = text.boundingRect().width()
        masterItem = _ItemFaceItem(0, 0, width, height)
        # Keep a link within the item to access node info
        masterItem.node = node
        # I dont want a border around the masterItem
        masterItem.setPen(QPen(QtCore.Qt.NoPen))
        # bar shape
        width_ = (width-tw-5) * ((value-min_value)/(max_value-min_value))
        height_ = height*height_factor
        center = masterItem.boundingRect().center()
        barItem = QGraphicsRectItem(0, center.y()-height_/2, width_, height_)
        barItem.setParentItem(masterItem)
        barItem.setPen(QPen(QtCore.Qt.NoPen))
        brush = QBrush(QColor(color))
        barItem.setBrush(brush)
        bar_width = barItem.boundingRect().width()
        center_bar = barItem.boundingRect().center()
        x_pos = bar_width+5 if value>0 else 5
        text.setParentItem(masterItem)
        text.setPos(x_pos, center_bar.y()-th/2)
        # text.setPen(QPen(QPen(QColor("white"))))
        return masterItem

    def drawStrip(self, node, width, height, color):
        if height == "auto":
            if self.scene.n2i:
                item = self.scene.n2i[node]
                if self.scene.img.mode == "r":
                    node_height = item.fullRegion.height()
                else:
                    node_height = 20 # item.effective_height
            else:
                node_height = 20
        else:
            node_height = height
        masterItem = _ItemFaceItem(0, 0, width, node_height)
        # Keep a link within the item to access node info
        masterItem.node = node
        # I dont want a border around the masterItem
        masterItem.setPen(QPen(QtCore.Qt.NoPen))
        # if self.scene.img.mode == "r":
        color_bar = QGraphicsRectItem(0, 0, width, node_height) #height*height_factor)
        # else:
        #     angle_start = item.full_start
        #     angle_end = item.full_end
        #     parent_r = item.boundingRect().x()
        #     color_bar = crender._ArcItem()
        #     print(width, node_height)
        #     color_bar.set_arc(0,0,parent_r,parent_r+width,angle_start, angle_end)
        brush = QBrush(QColor(color))
        color_bar.setBrush(brush)
        color_bar.setParentItem(masterItem)
        color_bar.setPen(QPen(QtCore.Qt.NoPen))
        masterItem.setRect(color_bar.rect())
        return masterItem

    def make_strip_face(self, tableview, array, mode="new"):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        width = float(dict_configs["Width"])
        height = float(dict_configs["Height"]) if dict_configs["Height"].isnumeric() else dict_configs["Height"]
        # height_factor = float(dict_configs["Height factor"])
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_line in array:
            name, color = list_line
            if color == "None color":
                continue
            node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
            if node:
                F = faces.DynamicItemFace(self.drawStrip, width, height, color)
                F.name = "strip"
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                # node.img_style["vt_line_color"] = color
                # node.img_style["hz_line_color"] = color
                face_added = True
        if face_added:
            self.redraw()

    def make_name_face(self, tableview, array, mode="new", nodraw=False):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        label_font = dict_configs["Name font"]
        # color = dict_configs["Name color"]
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        # self.scene.img.draw_guiding_lines = True
        face_added = False
        for list_row in array:
            old_name, new_name, fgcolor, bgcolor = list_row
            node = self.scene.tree.search_nodes(id=old_name)[0]
            if node:
                F = faces.TextFace(new_name)
                F = self.add_base_parameters(configs, F, tableview.model())
                F.fgcolor = fgcolor
                if bgcolor != "None color":
                    F.background.color = bgcolor
                F.ftype = label_font.family()
                F.fsize = label_font.pointSize()
                if label_font.italic():
                    F.fstyle = "italic"
                if label_font.bold():
                    F.bold = True
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                face_added = True
        # F = faces.TextFace()
        # self.scene.img.layout_fn = lambda node: \
        #     [faces.add_face_to_node(F, node, column=0, position=position) if node.is_leaf() else print,
        #      tableview.allfaces.append([node, position, F])]
        # self.scene.img.legend.add_face(faces.CircleFace(10, "red"), column=0)
        # self.scene.img.legend.add_face(faces.TextFace("0.5 support"), column=1)
        if not nodraw and face_added:
            self.redraw()

    def domain_face(self, node, list_, go_line_len,
                    width_factor, height, height_factor, label_font, label_color,
                    border_size, border_color, show_backbone, show_strand):
        '''

        :param list_: [('RE', '642.0', '656.0', '#ccff00', 'S1'), ('RE', '657.0', '671.0', '#ccff00', 'W')]
        :return:
        '''
        # list_, go_line_len, height = args[:3]
        # Or your custom Items, in which you can re-implement interactive
        # functions, etc. Check QGraphicsItem doc for details.
        list_for_judge = ["has_minus" if go_info[-1].startswith("-") else "has_plus" for go_info in list_]
        has_plus = True if "has_plus" in list_for_judge else False
        has_minus = True if "has_minus" in list_for_judge else False
        height_f = height*height_factor
        masterItem = _ItemFaceItem(0, 0, 100, height*len(set(list_for_judge)))
        center = masterItem.boundingRect().center()
        # Keep a link within the item to access node info
        masterItem.node = node
        # I dont want a border around the masterItem
        masterItem.setPen(QPen(QtCore.Qt.NoPen))
        for go_info in list_:
            shape, start, stop, color, go = go_info
            start = float(start)
            stop = float(stop)
            width = stop - start
            drawEngine = QGraphicsRectItem if shape == "RE" else QGraphicsEllipseItem
            if len(set(list_for_judge)) == 2:
                if go.startswith("-"):
                    go_shape = drawEngine(start*width_factor, center.y(), width*width_factor, height_f)
                    minus_go_shape_center = go_shape.boundingRect().center()
                else:
                    go_shape = drawEngine(start*width_factor, center.y()-height_f, width*width_factor, height_f)
                    plus_go_shape_center = go_shape.boundingRect().center()
            else:
                go_shape = drawEngine(start*width_factor, center.y()-(height_f/2), width*width_factor, height_f)
                if go.startswith("-"):
                    minus_go_shape_center = go_shape.boundingRect().center()
                else:
                    plus_go_shape_center = go_shape.boundingRect().center()
            go_shape.setParentItem(masterItem)
            go_shape.setZValue(1)
            # Define the brush (fill).
            # if self.dict_args["use fill color"]:
            brush = QBrush(QColor(color))
            go_shape.setBrush(brush)
            # Define the pen (line)
            # if self.dict_args["use border color"]:
            pen = QPen(QColor(border_color))
            pen.setWidth(border_size)
            go_shape.setPen(pen)
            ## draw go name
            go_name = QGraphicsTextItem(go.lstrip("-"))
            go_name.setTextInteractionFlags(Qt.TextEditorInteraction)
            go_name.setFont(label_font)
            tw = go_name.boundingRect().width()
            th = go_name.boundingRect().height()
            shape_center = go_shape.boundingRect().center()
            go_name.setPos(shape_center.x() - tw / 2, shape_center.y() - th / 2)
            # set text color
            go_name.setDefaultTextColor(QColor(label_color))
            go_name.setZValue(2)
            go_name.setParentItem(masterItem)
        # backbone line
        # if self.dict_args["show backbone line"]:
        if has_plus and show_backbone:
            backbone_plus = QGraphicsLineItem(0,
                                              plus_go_shape_center.y(),
                                              go_line_len*width_factor,
                                              plus_go_shape_center.y())
            pen = QPen(QColor("grey"))
            pen.setWidth(0.5)
            backbone_plus.setPen(pen)
            backbone_plus.setParentItem(masterItem)
            backbone_plus.setZValue(0)
        if has_minus and show_backbone:
            backbone_minus = QGraphicsLineItem(0,
                                               minus_go_shape_center.y(),
                                               go_line_len*width_factor,
                                               minus_go_shape_center.y())
            pen = QPen(QColor("grey"))
            pen.setWidth(0.5)
            backbone_minus.setPen(pen)
            backbone_minus.setParentItem(masterItem)
            backbone_minus.setZValue(0)
        # strand name
        # if self.dict_args["show strands"]:
        list_strand_text_width = []
        if has_plus and show_strand:
            strand_plus = QGraphicsTextItem("(+)")
            strand_plus.setFont(label_font)
            tw_plus = strand_plus.boundingRect().width()
            th_plus = strand_plus.boundingRect().height()
            strand_plus.setPos(go_line_len*width_factor, plus_go_shape_center.y()-(th_plus/2))
            strand_plus.setParentItem(masterItem)
            list_strand_text_width.append(tw_plus)
        if has_minus and show_strand:
            strand_minus = QGraphicsTextItem("(-)")
            strand_minus.setFont(label_font)
            tw_minus = strand_minus.boundingRect().width()
            th_minus = strand_minus.boundingRect().height()
            strand_minus.setPos(go_line_len*width_factor, minus_go_shape_center.y()-(th_minus/2))
            strand_minus.setParentItem(masterItem)
            list_strand_text_width.append(tw_minus)
        if show_strand:
            width_all = go_line_len*width_factor + (max(list_strand_text_width) if list_strand_text_width else 0)
        else:
            width_all = go_line_len*width_factor
        masterItem.setRect(0, 0, width_all, height*len(set(list_for_judge)))
        return masterItem

    def draw_domain(self, tableview, content, separator, mode="new"):
        # 基因顺序，[('Aglaiogyrodactylus_forficulatus_KU679421','671', 'RE|0.0|25.0|#6699ff|....')]
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        width_factor = float(dict_configs["Width factor"])
        height = float(dict_configs["Height"])
        height_factor = float(dict_configs["Height factor"])
        margin = float(dict_configs["Margin"])
        label_font = dict_configs["Label font"]
        label_color = dict_configs["Label color"]
        border_size = float(dict_configs["Border size"])
        border_color = dict_configs["Border color"]
        show_backbone = dict_configs["Show backbone"]
        show_strand = dict_configs["Show strand"]
        list_fgo = re.findall(r"(?m)([^{S}\n\|]+?){S}([^{S}\n\|]+?){S}([^{S}\n\|]+?\|[^{S}\n\|]+?\|[^{S}\n\|]+?\|[^{S}\n\|]+?\|[^{S}\n\|]+?.+)$".format(S=separator), content)
        if list_fgo:
            if mode == "new":
                column = self.listWidget.get_checked_num()
            else:
                column = self.remove_faces(tableview.allfaces)
            tableview.allfaces = [] # init faces container
            face_added = False
            for fgo in list_fgo:
                spe_name = fgo[0]
                go_line_len = int(fgo[1])
                # [('RE', '642.0', '656.0', '#ccff00', 'S1', ','),
                #  ('RE', '657.0', '671.0', '#ccff00', 'W', '')]
                list_go_info = re.findall(r"([^{S}\n\|]+?)\|([^{S}\n\|]+?)\|([^{S}\n\|]+?)\|([^{S}\n\|]+?)\|([^{S}\n\|]+?)({S}|$)".format(S=separator), fgo[-1])
                list_go_info = [i[:5] for i in list_go_info]
                node = self.scene.tree.search_nodes(id=spe_name)[0] if self.scene.tree.search_nodes(id=spe_name) else None
                if node:
                    F = faces.DynamicItemFace(self.domain_face, list_go_info, go_line_len,
                                              width_factor, height, height_factor, label_font, label_color,
                                              border_size, border_color, show_backbone, show_strand)
                    F.margin_left = margin
                    tableview.allfaces.append([node, position, F])
                    node.add_face(F, column=column, position=position)
                    face_added = True
            if face_added:
                self.redraw()

    def make_img_face(self, tableview, array, mode):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        width = float(dict_configs["Width"]) if dict_configs["Width"] else None
        height = float(dict_configs["Height"]) if dict_configs["Height"] else None
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_row in array:
            if len(list_row) == 2:
                name, url = list_row
                url = url.lstrip('"').rstrip('"') #.replace("\\", "/")
                if url:
                    # print(os.path.exists(url), url)
                    if os.path.exists(url):
                        # is a file
                        is_url = False
                    else:
                        try:
                            urlopen(url).read()
                            is_url = True
                            # print(is_url, url)
                        except:
                            continue
                    node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
                    if node:
                        # for i in ["aligned", "branch-right", "branch-top", "branch-bottom", "float", "float-behind"]:
                        #     print(i, self.scene.n2f[node][i].column2faces)
                        F = faces.ImgFace(url, width, height, is_url=is_url)
                        F = self.add_base_parameters(configs, F, tableview.model())
                        tableview.allfaces.append([node, position, F])
                        node.add_face(F, column=column, position=position)
                        face_added = True
        if face_added:
            self.redraw()

    def make_piechart_face(self, tableview, array, header, mode):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        width = float(dict_configs["Width"])
        height = float(dict_configs["Height"])
        line_color = dict_configs["Pie chart border"] if dict_configs["Pie chart border"] != "None color" else None
        list_colors = [dict_configs[f"{head} color"] for head in header[1:]]
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_row in array:
            name = list_row[0]
            percents = [float(j) for j in list_row[1:] if j]
            if len(percents) != len(header[1:]):
                continue
            sum_percents = sum(percents)
            if sum_percents != 100:
                percents = [100*(i/sum_percents) for i in percents]
            node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
            if node:
                F = faces.PieChartFace(percents, width, height, colors=list_colors, line_color=line_color)
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                face_added = True
        if face_added:
            self.redraw()

    def make_stackbar_face(self, tableview, array, header, mode):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        width = float(dict_configs["Width"])
        height = float(dict_configs["Height"])
        line_color = dict_configs["Pie chart border"] if dict_configs["Pie chart border"] != "None color" else None
        list_colors = [dict_configs[f"{head} color"] for head in header[1:]]
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_row in array:
            name = list_row[0]
            percents = [float(j) for j in list_row[1:] if j]
            if len(percents) != len(header[1:]):
                continue
            sum_percents = sum(percents)
            if sum_percents != 100:
                percents = [100*(i/sum_percents) for i in percents]
            node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
            if node:
                F = faces.StackedBarFace(percents, width, height, colors=list_colors, line_color=line_color)
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                face_added = True
        if face_added:
            self.redraw()

    def make_vbar_face(self, tableview, array, header, mode):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        width = float(dict_configs["Width"])
        height = float(dict_configs["Height"])
        min_value = float(dict_configs["min value"])
        max_value = float(dict_configs["max value"]) if dict_configs["max value"] else None
        scale_size = float(dict_configs["Scale size"])
        label_font = dict_configs["Label font"]
        list_colors = [dict_configs[f"{head} color"] for head in header[1:]]
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_row in array:
            name = list_row[0]
            values = [float(j) for j in list_row[1:] if j]
            if len(values) != len(header[1:]):
                continue
            node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
            if node:
                deviations = [0 for i in values] # need to change
                F = faces.BarChartFace(values, deviations, width, height, colors=list_colors, labels=header[1:],
                                       min_value=min_value, max_value=max_value, label_font=label_font,
                                       scale_fsize=scale_size)
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                face_added = True
        if face_added:
            self.redraw()

    def make_hbar_face(self, tableview, array, mode="new"):
        '''
        TODO: 负数的时候怎么处理
        :param content:
        :param separator:
        :return:
        '''
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        width = float(dict_configs["Width"])
        height = float(dict_configs["Height"])
        height_factor = float(dict_configs["Height factor"])
        min_value = float(dict_configs["Min value"])
        color = dict_configs["Color"]
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        values = [float(i) for i in dict(array).values() if i]
        max_value = max(values) if values else None
        if not max_value:
            return
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_row in array:
            name, value = list_row
            if value:
                value = int(value) if value.lstrip("-+").isdigit() else float(value)
                node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
                if node:
                    F = faces.DynamicItemFace(self.bar_plot, width, height, color, value,
                                              height_factor, min_value, max_value=max_value)
                    F = self.add_base_parameters(configs, F, tableview.model())
                    tableview.allfaces.append([node, position, F])
                    node.add_face(F, column=column, position=position)
                    face_added = True
        if face_added:
            self.redraw()

    def make_heatmap_title(self, node, width, labels, font, rotation):
        masterItem = QGraphicsRectItem(0, 0, width, 50)
        # Keep a link within the item to access node info
        masterItem.node = node
        # I dont want a border around the masterItem
        masterItem.setPen(QPen(Qt.NoPen))
        list_heights = []
        each_width = width/len(labels)
        for num, label in enumerate(labels):
            text = QGraphicsSimpleTextItem(label)
            text.setFont(font)
            text.setRotation(rotation)
            text.setParentItem(masterItem)
            th = text.boundingRect().height()
            tw = text.boundingRect().width()
            list_heights.append(th)
            text.setPos(num*each_width+tw/2, 0)
        masterItem.setRect(0, 0, width, max(list_heights))
        return masterItem

    def make_heatmap_face(self, tableview, array, header, mode):
        model = tableview.model()
        configs = model.arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        width = float(dict_configs["Width"])
        height = float(dict_configs["Height"])
        max_v = float(dict_configs["max value"])
        center_v = float(dict_configs["center value"])
        min_v = float(dict_configs["min value"])
        style = dict_configs["style"][0]
        scheme = dict_configs["Color scheme"][0]
        dict_ = {"green & blue": 0, "green & red": 1, "red & blue": 2}
        scheme = dict_[scheme]
        draw_title = dict_configs["Draw value title"]
        title_pos = dict_configs["Value title position"][0]
        title_font = dict_configs["Value title font"]
        title_rotation = float(dict_configs["Value title rotation"])
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
            self.remove_title_faces(tableview.titlefaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_row in array:
            name = list_row[0]
            values = [float(j) for j in list_row[1:] if j]
            if len(values) != len(header[1:]):
                continue
            node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
            if node:
                node.add_features(profile = values)
                node.add_features(deviation = [0 for x in range(len(values))])
                F = faces.ProfileFace(max_v, min_v, center_v, width, height, style, scheme)
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                face_added = True
        if draw_title:
            tableview.titlefaces = [] # init faces container
            labels = header[1:]
            F = faces.DynamicItemFace(self.make_heatmap_title, width, labels, title_font, title_rotation)
            container = self.scene.img.aligned_header if title_pos == "Top" else self.scene.img.aligned_foot
            container.add_face(F, column)
            tableview.titlefaces.append([F, container])
        # if face_added:
        self.redraw()

    def make_seq_face(self, tableview, array, mode, link):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        font = dict_configs["Font"]
        col_width = float(dict_configs["Column width"]) if dict_configs["Column width"] else None
        special_col = [[int(j) for j in i.strip().split("-")] for i in dict_configs["Special column"].split(",")] \
                            if dict_configs["Special column"] else None
        special_col_w = float(dict_configs["Special column width"])
        interactive = dict_configs["Interactive"]
        dict_fg_colors = {}
        dict_bg_colors = {}
        for item in dict_configs:
            if re.search(r"\S+ foreground color", item):
                dict_fg_colors[item.replace(" foreground color", "")] = dict_configs[item]
            if re.search(r"\S+ background color", item):
                dict_bg_colors[item.replace(" background color", "")] = dict_configs[item]
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_row in array:
            name, aa, nt = list_row
            if (not aa) and (not nt):
                continue
            if (aa or link):
                seq_type = "aa"
                seq = aa
            else:
                seq_type = "nt"
                seq = nt
            node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
            if node:
                F = faces.SequenceFace(seq, seqtype=seq_type, fg_colors=dict_fg_colors, bg_colors=dict_bg_colors,
                                       codon=nt if link else None, col_w=col_width, alt_col_w=special_col_w, font=font,
                                       special_col=special_col, interactive=interactive)
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                face_added = True
        if face_added:
            self.redraw()

    def make_motif_face(self, tableview, array, mode):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        seq_type = dict_configs["Sequence type"][0]
        gap_format = dict_configs["Gap format"][0]
        seq_format = dict_configs["Sequence format"][0]
        scale_factor = float(dict_configs["Scale factor"])
        Height = float(dict_configs["Height"])
        Width = float(dict_configs["Width"])
        fg_color = dict_configs["Motif foreground color"]
        bg_color = dict_configs["Motif background color"]
        gap_color = dict_configs["Gap color"]
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_row in array:
            name = list_row[0]
            seq = list_row[1]
            motifs = list_row[2:]
            list_motifs = []
            if (len(set(motifs))==1 and (not list(set(motifs))[0])):
                continue
            for i in motifs:
                list_i = i.split("@", maxsplit=8)
                if len(list_i) == 8:
                    list_i[0] = int(list_i[0]) if list_i[0] else None
                    list_i[1] = int(list_i[1]) if list_i[1] else None
                    list_i[3] = float(list_i[3]) if list_i[3] else None
                    list_i[4] = float(list_i[4]) if list_i[4] else None
                    list_motifs.append(list_i)
                else:
                    continue
            node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
            if node:
                F = faces.SeqMotifFace(seq, list_motifs, seq_type, gap_format, seq_format,
                                       scale_factor, Height, Width, fg_color, bg_color, gap_color)
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                face_added = True
        if face_added:
            self.redraw()

    def make_text_face(self, tableview, array, mode):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        font_ = dict_configs["Font"]
        ftype = font_.family()
        fsize = font_.pointSize()
        fstyle = "italic" if font_.italic() else "normal"
        bold = True if font_.bold() else False
        tight_text = dict_configs["Tight text"]
        # text_color = dict_configs["Text color"]
        pen_width = float(dict_configs["Pen width"])
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_row in array:
            name, text, text_color = list_row
            if not text:
                continue
            node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
            if node:
                F = faces.TextFace(text, ftype, fsize, text_color, pen_width,
                                    fstyle, tight_text, bold)
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                face_added = True
        if face_added:
            self.redraw()

    def draw_shape(self, node, shape, width, height, shape_color, border_color, border_size):
        masterItem = _ItemFaceItem(0, 0, width, height)
        # Keep a link within the item to access node info
        masterItem.node = node
        # I dont want a border around the masterItem
        masterItem.setPen(QPen(QtCore.Qt.NoPen))
        # shape
        dict_shape = {"circle": QGraphicsEllipseItem,
                      "rectangle": QGraphicsRectItem,
                      "round corner rectangle": QGraphicsRoundRectItem,
                      "diamond": QGraphicsDiamondItem,
                      "star": QGraphicsStarItem,
                      "star2": QGraphicsStarItem2,
                      "line": QGraphicsLineItem,
                      "left arrow": QGraphicsLeftArrowItem,
                      "right arrow": QGraphicsRightArrowItem,
                      "left triangle": QGraphicsLeftTriangleItem,
                      "right triangle": QGraphicsRightTriangleItem,
                      "top trangle": QGraphicsTopTriangleItem,
                      "bottom triangle": QGraphicsBottomTriangleItem}
        shape_graph = dict_shape[shape]
        if shape in ["circle", "rectangle", "line", "round corner rectangle"]:
            shapeItem = shape_graph(0, 0, width, height)
        elif shape in ["star", "star2"]:
            shapeItem = shape_graph(width)
            shapeItem.setPos(0, 0)
        else:
            shapeItem = shape_graph(width, height)
            shapeItem.setPos(0, 0)
        shapeItem.setParentItem(masterItem)
        if border_color:
            pen = QPen(QColor(border_color))
            pen.setWidth(border_size)
            shapeItem.setPen(pen)
        else:
            shapeItem.setPen(QPen(QtCore.Qt.NoPen))
        if shape_color:
            if shape != "line":
                brush = QBrush(QColor(shape_color))
                shapeItem.setBrush(brush)
        return masterItem

    def make_shape_face(self, tableview, array, check_array, mode):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        width = float(dict_configs["Width"])
        height = float(dict_configs["Height"])
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        # print(column)
        tableview.allfaces = [] # init faces container
        face_added = False
        for row, list_row in enumerate(array):
            name, list_shape, shape_color, border_color, border_size = list_row
            shape_color = shape_color if check_array[row][2] else None
            border_color = border_color if check_array[row][3] else None
            if list_shape[0] == "None":
                continue
            node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
            if node:
                F = faces.DynamicItemFace(self.draw_shape, list_shape[0], width, height, shape_color, border_color,
                                          float(border_size))
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                face_added = True
        if face_added:
            self.redraw()

    def draw_attribute(self, node, value, dict_args):
        masterItem = _ItemFaceItem(0, 0, 20, 20)
        # Keep a link within the item to access node info
        masterItem.node = node
        # I dont want a border around the masterItem
        masterItem.setPen(QPen(QtCore.Qt.NoPen))
        if dict_args["display as"] == "text":
            str_ = str(value) if not dict_args["display as %"] else f"{value}%"
            text = QGraphicsTextItem(str_)
            text.setFont(dict_args["text font"])
            text.setDefaultTextColor(QColor(dict_args["text color"]))
            text.setParentItem(masterItem)
            width = text.boundingRect().width()
            height = text.boundingRect().height()
            # text.setPos(masterItem.boundingRect().x(), masterItem.boundingRect().y())
        elif dict_args["display as"] == "shape":
            # shape
            shape = dict_args["shape"]
            max_value = dict_args["range"][1]
            diff_size = dict_args["shape max size"] - dict_args["shape min size"]
            width = diff_size*(float(value)/max_value) + dict_args["shape min size"]
            height = width
            dict_shape = {"circle": QGraphicsEllipseItem,
                          "rectangle": QGraphicsRectItem,
                          "round corner rectangle": QGraphicsRoundRectItem,
                          "diamond": QGraphicsDiamondItem,
                          "star": QGraphicsStarItem,
                          "star2": QGraphicsStarItem2,
                          "line": QGraphicsLineItem,
                          "left arrow": QGraphicsLeftArrowItem,
                          "right arrow": QGraphicsRightArrowItem,
                          "left triangle": QGraphicsLeftTriangleItem,
                          "right triangle": QGraphicsRightTriangleItem,
                          "top trangle": QGraphicsTopTriangleItem,
                          "bottom triangle": QGraphicsBottomTriangleItem}
            shape_graph = dict_shape[shape]
            if shape in ["circle", "rectangle", "line", "round corner rectangle"]:
                shapeItem = shape_graph(0, 0, width, height)
            elif shape in ["star", "star2"]:
                shapeItem = shape_graph(width)
                shapeItem.setPos(0, 0)
            else:
                shapeItem = shape_graph(width, height)
                shapeItem.setPos(0, 0)
            shapeItem.setParentItem(masterItem)
            if dict_args["shape border size"]:
                pen = QPen(QColor(dict_args["shape border color"]))
                pen.setWidth(dict_args["shape border size"])
                shapeItem.setPen(pen)
            else:
                shapeItem.setPen(QPen(Qt.NoPen))#pen)
            brush = QBrush(QColor(dict_args["shape fill color"]))
            shapeItem.setBrush(brush)
        masterItem.setRect(0, 0, width, height)
        return masterItem

    def make_attribute_face(self, tableview, array, mode="new", dict_args=None, redraw=True):
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for list_line in array:
            name, value = list_line
            if value.lstrip('-').replace('.','',1).isdigit():
                if not (dict_args["range"][0] <= float(value) <= dict_args["range"][1]):
                    continue
            node = self.scene.tree.search_nodes(id=name)[0] if self.scene.tree.search_nodes(id=name) else None
            if node:
                F = faces.DynamicItemFace(self.draw_attribute, value, dict_args)
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                # faces.add_face_to_node(F, node, column, position=position)
                face_added = True
        if face_added and redraw:
            self.redraw()

    def tax_has_displayed(self, node, tax, dict_node_tax):
        for node2 in dict_node_tax:
            list_ = dict_node_tax[node2]
            for i in list_:
                tax2, tax_name2, color = i
                if (tax == tax2) and (node in node2):
                    return True
        return False

    def make_taxonomy_face1(self, array, included_tax, dict_tax_color, mode="new"):
        self.dict_tax_strip = OrderedDict()
        # {Benedenia_hoshinai_NC_014591: {Family: [Capsalidae, #000000]}}
        self.dict_id_tax_value_color = OrderedDict()
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
        self.dict_tax_text = OrderedDict()
        dict_node_tax_setting = {} # {node1: [[Family, Capsalidae, #000000], ]}
        for node in self.scene.tree.traverse("preorder"):
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

    def draw_taxnomy_box(self, node, tax, tax_name, color):
        masterItem = QGraphicsRectItem()
        # Keep a link within the item to access node info
        masterItem.node = node
        # I dont want a border around the masterItem
        masterItem.setPen(QPen(QtCore.Qt.NoPen))
        color_bar = QGraphicsRectItem()
        brush = QBrush(QColor(color))
        color_bar.setBrush(brush)
        color_bar.setParentItem(masterItem)
        color_bar.setPen(QPen(QtCore.Qt.NoPen))
        return masterItem

    def make_taxonomy_face2(self, tableview, array, included_tax, dict_tax_color, mode):
        # {Benedenia_hoshinai_NC_014591: {Family: [Capsalidae, #000000]}}
        self.dict_id_tax_value_color = OrderedDict()
        for num, tax in enumerate(included_tax):
            if num != 0:
                for list_line in array:
                    if list_line[num]:
                        # {Benedenia_hoshinai_NC_014591: {Family: [Capsalidae, #000000]}}
                        self.dict_id_tax_value_color.setdefault(list_line[0], {}).setdefault(tax, [list_line[num],
                                                                                                   dict_tax_color[list_line[num]]])
        dict_node_tax_setting = {} # {node1: [[Family, Capsalidae, #000000], ]}
        for node in self.scene.tree.traverse("preorder"):
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
        configs = tableview.model().arraydata
        dict_configs = dict(configs)
        position = dict_configs["Position"][0]
        if mode == "new":
            column = self.listWidget.get_checked_num()
        else:
            column = self.remove_faces(tableview.allfaces)
        tableview.allfaces = [] # init faces container
        face_added = False
        for node in dict_node_tax_setting:
            for num, tax_setting in enumerate(dict_node_tax_setting[node]):
                if num%2==0:
                    position = "branch-top" if position in ["branch-top", "branch-bottom"] else position
                else:
                    position = "branch-bottom" if position in ["branch-top", "branch-bottom"] else position
                tax, tax_name, color = tax_setting
                # tax_name = f'''<span style=\"color:red\">family</span>{tax_name}'''
                F = faces.TextFace(tax_name, fgcolor=color)
                F = self.add_base_parameters(configs, F, tableview.model())
                tableview.allfaces.append([node, position, F])
                node.add_face(F, column=column, position=position)
                face_added = True
        if face_added:
            self.redraw()


    # def handle_itemclicked(self, index):
    #     tableview = self.sender()
    #     model = tableview.model()
    #     left_index = model.index(index.row(), 0)
    #     text = index.data(Qt.DisplayRole)
    #     data = model.arraydata[index.row()][index.column()]
    #     left_text = left_index.data(Qt.DisplayRole)
    #     if text and (re.search("^#[0-9ABCDEFabcdef]{6}$", str(text)) or (text == "None color")):
    #         text = text if text != "None color" else "#000000"
    #         color = QColorDialog.getColor(QColor(text), self)
    #         if color.isValid():
    #             model.setData(index, color.name(), Qt.BackgroundRole)
    #             # tableview.selectionModel().select(model.index(0,0), QItemSelectionModel.Select)
    #     elif left_text and ("FONT" in left_text.upper()):
    #         font, ok = QFontDialog.getFont(data, self)
    #         if ok:
    #             model.arraydata[index.row()][index.column()] = font
    #             model.dataChanged.emit(index, index)

    def is_name_face(self, item):
        row = self.listWidget.row(item)
        return (row==0) and (self.listWidget.itemWidget(item).checkBox.isHidden())

    def judge_remove(self, checkState, widget):
        faces_ = widget.tableview.allfaces
        if checkState:
            # 重新加上
            # if not self.is_name_face(widget.tableview.list_item):
            #     column = self.listWidget.get_checked_num()
            # else:
            #     column = 0
            column = self.listWidget.get_checked_num()
            for node, position_, face in faces_:
                node.add_face(face, column=column, position=position_)
            if hasattr(widget.tableview, "titlefaces"):
                for face, container in widget.tableview.titlefaces:
                    container.add_face(face, column)
        else:
            # 从树中删掉
            removed_col = self.remove_faces(faces_)
            if hasattr(widget.tableview, "titlefaces"):
                self.remove_title_faces(widget.tableview.titlefaces)
            self.reorder_faces(removed_col)
        self.redraw()

    def reorder_faces(self, removed_col):
        '''
        reorder node's faces and self.label_faces
        :return:
        '''
        for node in self.scene.tree.traverse():
            for i in set(["branch-right", "branch-top", "branch-bottom", "float", "float-behind", "aligned"]):
                dict_faces = getattr(node.faces, i) # {0: [Attribute Face [name] (0x2755892486)], 1: [Attribute Face [name] (0x2755892486)]}
                if dict_faces:
                    # base_col = 0
                    dict_new_faces = {}
                    for col in sorted(list(dict_faces.keys())):
                        if col < removed_col:
                            dict_new_faces[col] = dict_faces[col]
                        else:
                            dict_new_faces[col-1] = dict_faces[col]
                        # base_col += 1
                    setattr(node.faces, i, dict_new_faces)

    def remove_title_faces(self, faces):
        for container in [self.scene.img.aligned_header, self.scene.img.aligned_foot]:
            if container:
                for col in list(container.keys()):
                    for face1 in container[col]: # [Attribute Face [name] (0x2755892486)]
                        for list_node_face in faces:
                            face2 = list_node_face[0]
                            if face1 == face2:
                                container[col].remove(face1)
                                if not container[col]:
                                    container.pop(col)
                                break
        for container in [self.scene.img.aligned_header, self.scene.img.aligned_foot]:
            if container:
                base_col = 1
                dict_new_faces = {}
                for col in sorted(list(container.keys())):
                    dict_new_faces[base_col] = container[col]
                    base_col += 1
                container = dict_new_faces

    def remove_faces(self, faces):
        target_col = 1
        for node in self.scene.tree.traverse():
            for i in set(["branch-right", "branch-top", "branch-bottom", "float", "float-behind", "aligned"]):
                dict_faces = getattr(node.faces, i) # {0: [Attribute Face [name] (0x2755892486)], 1: [Attribute Face [name] (0x2755892486)]}
                if dict_faces:
                    for col in list(dict_faces.keys()):
                        for face1 in dict_faces[col]: # [Attribute Face [name] (0x2755892486)]
                            for list_node_face in faces:
                                face2 = list_node_face[-1]
                                if face1 == face2:
                                    dict_faces[col].remove(face1)
                                    if not dict_faces[col]:
                                        dict_faces.pop(col)
                                    target_col = col
                                    break
        return target_col

    def create_annotation_editor(self, type, array_=None, header=None, include_inner_nodes=False,
                                        configs=None, force_new=False, tabIsChecked=None,
                                        header_state=None, array_check_states=None, nodraw=False,
                                        editor_dict_args=None):
        # create initial table contents
        list_leaves = []
        list_inner_nodes = []
        for node in self.scene.tree.traverse("postorder"):
            if node.is_leaf():
                list_leaves.append(node)
            else:
                if include_inner_nodes:
                    list_inner_nodes.append(node)
        if type == "Leaf name":
            # if hasattr(self, "name_editor") and not force_new:
            #     self.name_editor.show()
                # self.create_annotation(type, self.name_editor.ui.tableView.model().arraydata,
                #                         editor=self.name_editor, configs=configs)
            # else:
            header = ["Node ID", "New name", "Foreground color", "Background color"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                array = [[node.id, node.id, "#000000", "None color"] if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, node.id, "#000000", "None color"] for node in list_leaves+list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyNameTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.create_annotation(type, model.arraydata,
                                                                         editor=editor, configs=configs,
                                                                         tabIsChecked=tabIsChecked, nodraw=nodraw),
                                                           editor.close()])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata,
                                            editor=editor, configs=configs,
                                            tabIsChecked=tabIsChecked, nodraw=nodraw)
            else:
                editor.show()
        elif type == "Image":
            header = ["Node ID", "Image path"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                array = [[node.id, ""] if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, ""] for node in list_leaves+list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyImgTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.create_annotation(type, model.arraydata,
                                                                                editor=editor, configs=configs,
                                                                                tabIsChecked=tabIsChecked),
                                                    editor.close()])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata,
                    editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Pie chart":
            header = ["Node ID", "Value1"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                length = len(array_[0])-1
                array = [[node.id] + [""]*length if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, ""] for node in list_leaves+list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor2.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyPieTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.create_annotation(type, model.arraydata,
                                                                                  model.header, editor=editor,
                                                                                  configs=configs, tabIsChecked=tabIsChecked),
                                                    editor.close()])
            # add column
            editor.ui.pushButton_2.clicked.connect(lambda : [model.header.append(f"Value{len(model.header)}"),
                                                      setattr(model, "arraydata", [row + [""] for row in model.arraydata]),
                                                      model.dataChanged.emit(model.index(0, 0), model.index(0, 0)),
                                                      editor.ui.tableView.scrollTo(model.index(0, len(model.header)-1))])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata,
                    model.header, editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Stacked bar chart":
            header = ["Node ID", "Value1"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                length = len(array_[0])-1
                array = [[node.id] + [""]*length if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, ""] for node in list_leaves+list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor2.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MystackedBarTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.create_annotation(type, model.arraydata,
                                                                                  model.header, editor=editor,
                                                                                  configs=configs, tabIsChecked=tabIsChecked),
                                                    editor.close()])
            # add column
            editor.ui.pushButton_2.clicked.connect(lambda : [model.header.append(f"Value{len(model.header)}"),
                                                      setattr(model, "arraydata", [row + [""] for row in model.arraydata]),
                                                      model.dataChanged.emit(model.index(0, 0), model.index(0, 0)),
                                                      editor.ui.tableView.scrollTo(model.index(0, len(model.header)-1))])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata,
                    model.header, editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Horizontal bar chart":
            header = ["Node ID", "Value"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                array = [[node.id, ""] if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, ""] for node in list_leaves+list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyHorizBarTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.create_annotation(type, model.arraydata,
                                                                editor=editor, configs=configs, tabIsChecked=tabIsChecked),
                                                           editor.close()])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata, editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Vertical bar chart":
            header = ["Node ID", "Value1"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                length = len(array_[0])-1
                array = [[node.id] + [""]*length if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, ""] for node in list_leaves+list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor2.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyBarTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.create_annotation(type, model.arraydata,
                                                                                  model.header, editor=editor,
                                                                                  configs=configs, tabIsChecked=tabIsChecked),
                                                           editor.close()])
            # add column
            editor.ui.pushButton_2.clicked.connect(lambda : [model.header.append(f"Value{len(model.header)}"),
                                                             setattr(model, "arraydata", [row + [""] for row in model.arraydata]),
                                                             model.dataChanged.emit(model.index(0, 0), model.index(0, 0)),
                                                             editor.ui.tableView.scrollTo(model.index(0, len(model.header)-1))])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata,
                    model.header, editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Heatmap":
            header = ["Node ID", "Value1"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                length = len(array_[0])-1
                array = [[node.id] + [""]*length if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, ""] for node in list_leaves+list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor2.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyHeatmapTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.create_annotation(type, model.arraydata,
                                                                                  model.header, editor=editor,
                                                                                  configs=configs, tabIsChecked=tabIsChecked),
                                                    editor.close()])
            # add column
            editor.ui.pushButton_2.clicked.connect(lambda : [model.header.append(f"Value{len(model.header)}"),
                                                      setattr(model, "arraydata", [row + [""] for row in model.arraydata]),
                                                      model.dataChanged.emit(model.index(0, 0), model.index(0, 0)),
                                                      editor.ui.tableView.scrollTo(model.index(0, len(model.header)-1))])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata,
                    model.header, editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Sequence":
            header = ["Node ID", "AA (amino acid sequence)", "NT (nucleotide sequence)"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                array = [[node.id, "", ""] if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, "", ""] for node in list_leaves+list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor3.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MySeqTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.create_annotation(type, model.arraydata,
                                                                editor=editor, configs=configs, tabIsChecked=tabIsChecked),
                                                    editor.close()])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata,
                                            editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Motif":
            header = ["Node ID", "Sequence", "Motif1"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                length = len(array_[0])-1
                array = [[node.id] + [""]*length if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, "", ""] for node in list_leaves+list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor2.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyMotifTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.create_annotation(type, model.arraydata,
                                                                editor=editor, configs=configs, tabIsChecked=tabIsChecked),
                                                           editor.close()])
            # add column
            editor.ui.pushButton_2.clicked.connect(lambda : [model.header.append(f"Motif{len(model.header)-1}"),
                                                             setattr(model, "arraydata", [row + [""] for row in model.arraydata]),
                                                             model.dataChanged.emit(model.index(0, 0), model.index(0, 0)),
                                                             editor.ui.tableView.scrollTo(model.index(0, len(model.header)-1))])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata,
                                             editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Text":
            header = ["Node ID", "Text", "Text color"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                array = [[node.id, "", "#000000"] if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, "", "#000000"] for node in list_leaves + list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyTextTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda: [self.create_annotation(type, model.arraydata,
                                                            editor=editor, configs=configs, tabIsChecked=tabIsChecked),
                                                          editor.close()])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata, editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Color strip":
            header = ["Node ID", "Color"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                array = [[node.id, "None color"] if node.id not in dict_array_ else dict_array_[node.id]
                                                        for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id, "None color"] for node in list_leaves + list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyStripTableModel(array, header, parent=editor.ui.tableView)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda: [self.create_annotation(type, model.arraydata,
                                                                editor=editor, configs=configs, tabIsChecked=tabIsChecked),
                                                          editor.close()])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata, editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Shape":
            header = ["Node ID", "Shape", "  Shape color", "  Border color", "Border size"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                array = [[node.id,
                          ["None", "circle", "rectangle", "star", "star2", "round corner rectangle",
                           "right triangle", "left triangle",
                           "top trangle", "bottom triangle", "diamond",
                           "line", "left arrow", "right arrow"],
                          "#f07464", "#d8d8d8", 1
                          ] if node.id not in dict_array_ else dict_array_[node.id]
                                    for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id,
                          ["None", "circle", "rectangle", "star", "star2", "round corner rectangle",
                              "right triangle", "left triangle",
                              "top trangle", "bottom triangle", "diamond",
                              "line", "left arrow", "right arrow"],
                                "#f07464", "#d8d8d8", 1
                                      ] for node in list_leaves+list_inner_nodes]
            check_states = [[node.id, "", True, False, ""] for node in list_leaves+list_inner_nodes] if \
                                                            not array_check_states else array_check_states
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyShapeTableModel(array, header, parent=editor.ui.tableView, check_states=check_states)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda : [self.create_annotation(type, model.arraydata,
                                                                                  editor=editor,
                                                                                  check_array=model.check_states,
                                                                                  configs=configs,
                                                                                  tabIsChecked=tabIsChecked),
                                                           editor.close()])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.arraydata, editor=editor,
                                       check_array=model.check_states, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Auto-assign taxonomy (style 1)":
            header = ["Node ID", "Genus", "Subfamily", "Family", "Order", "Subclass", "Class", "Phylum"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                length = len(array_[0])-1
                array = [[node.id] + [""]*length if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id] + [""]*7 for node in list_leaves + list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor_tax.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyTaxTableModel(array, header, parent=editor.ui.tableView, dialog=editor)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda: [self.create_annotation(type, model.fetchIncludedArray(),
                                                        editor=editor, configs=configs, tabIsChecked=tabIsChecked),
                                                          editor.close()])
            # add column
            editor.ui.pushButton_2.clicked.connect(lambda : [model.header.append(f"Taxonomy{len(model.header)}"),
                                                             model.headerDataChanged.emit(Qt.Horizontal, len(model.header)-1, len(model.header)-1),
                                                             setattr(model, "arraydata", [row + [""] for row in model.arraydata]),
                                                             model.dataChanged.emit(model.index(0, 0), model.index(0, 0)),
                                                             editor.ui.tableView.scrollTo(model.index(0, len(model.header)-1))])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.fetchIncludedArray(), editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Auto-assign taxonomy (style 2)":
            header = ["Node ID", "Genus", "Subfamily", "Family", "Order", "Subclass", "Class", "Phylum"] if not header else header
            if array_:
                dict_array_ = {i[0]:i for i in array_}
                length = len(array_[0])-1
                array = [[node.id] + [""]*length if node.id not in dict_array_ else dict_array_[node.id]
                         for node in list_leaves + list_inner_nodes]
            else:
                array = [[node.id] + [""]*7 for node in list_leaves + list_inner_nodes]
            editor = QDialog(self)
            editor.ui = Ui_annotation_editor_tax.Ui_annotation_editor()
            editor.ui.setupUi(editor)
            editor.ui.label_2.setText(f"{type}:")
            model = MyTaxTableModel(array, header, parent=editor.ui.tableView, dialog=editor, header_state=header_state)
            editor.ui.tableView.setModel(model)
            editor.ui.pushButton.clicked.connect(lambda: [self.create_annotation(type, model.fetchIncludedArray(),
                                                                editor=editor, configs=configs, tabIsChecked=tabIsChecked),
                                                                                                          editor.close()])
            # add column
            editor.ui.pushButton_2.clicked.connect(lambda : [model.header.append(f"Taxonomy{len(model.header)}"),
                                                             model.headerDataChanged.emit(Qt.Horizontal, len(model.header)-1, len(model.header)-1),
                                                             setattr(model, "arraydata", [row + [""] for row in model.arraydata]),
                                                             model.dataChanged.emit(model.index(0, 0), model.index(0, 0)),
                                                             editor.ui.tableView.scrollTo(model.index(0, len(model.header)-1))])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, model.fetchIncludedArray(), editor=editor,
                                configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()
        elif type == "Attributes":
            editor = QDialog(self)
            editor.ui = Lg_attribute(parent=editor)
            if editor_dict_args:
                editor.ui.resume_GUI(editor_dict_args)
            # editor.ui.setupUi(editor)
            editor.ui.switch_attribute(editor.ui.comboBox.currentText())
            editor.ui.pushButton.clicked.connect(lambda: [self.create_annotation(type, editor.ui.tableView.model().arraydata,
                                                          editor=editor, configs=configs, tabIsChecked=tabIsChecked),
                                                          editor.close()])
            editor.setWindowFlags(editor.windowFlags() | Qt.WindowMinMaxButtonsHint)
            editor.include_inner_nodes = include_inner_nodes
            if array_:
                self.create_annotation(type, editor.ui.tableView.model().arraydata,
                                        editor=editor, configs=configs, tabIsChecked=tabIsChecked)
            else:
                editor.show()

    def create_annotation(self, type, array, header=None, editor=None,
                                check_array=None, configs=None,
                                tabIsChecked=None, nodraw=False):
        if type == "Leaf name":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_name_face(editor.tab.tableview, array, mode="rep", nodraw=nodraw)
            else:
                configs = [
                              ["Name font", QFont("Arial", 9, QFont.Normal)],
                              # ["Name color", "#000000"]
                          ] + copy.deepcopy(self.face_base_parameters) if not configs else configs
                if ["Position", ["branch-right", "aligned", "branch-top", "branch-bottom", "float", "float-behind"]] in configs:
                    index_pos = configs.index(["Position", ["branch-right", "aligned", "branch-top", "branch-bottom", "float", "float-behind"]])
                    configs[index_pos] = ["Position", ["aligned", "branch-right", "branch-top", "branch-bottom", "float", "float-behind"]]
                if ["margin_left", 3] in configs:
                    index_ml = configs.index(["margin_left", 3])
                    configs[index_ml] = ["margin_left", 0]
                tab_tableview = self.add_tableView(configs, "Leaf name")#, hide_button=True)
                # tab_tableview.list_item.name = "leaf name"
                tab_tableview.refresh_btn.clicked.connect(lambda : self.make_name_face(tab_tableview,
                                                                    editor.ui.tableView.model().arraydata,
                                                                    mode="rep", nodraw=nodraw))
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_img_face(tab_tableview, array, mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_name_face(tab_tableview, array, mode="new", nodraw=nodraw)
                # close tab if not tabIsChecked
                # print(tabIsChecked)
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Image":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_img_face(editor.tab.tableview, array, mode="rep")
            else:
                configs = [
                              ["Width", ""],
                              ["Height", ""],
                          ] + copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Image")
                # tab_tableview.list_item.name = "attributes"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                      self.make_img_face(tab_tableview,
                                                                         editor.ui.tableView.model().arraydata,
                                                                         mode="rep"))
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_img_face(tab_tableview, array, mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_img_face(tab_tableview, array, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Pie chart":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_piechart_face(editor.tab.tableview, array, header, mode="rep")
            else:
                color_schemes = list(COLOR_SCHEMES.keys())
                color_schemes.remove("set1")
                color_schemes.insert(0, "set1")
                list_value_colors = [[f"{value} color",
                                      COLOR_SCHEMES[color_schemes[0]][num] if
                                        num < len(COLOR_SCHEMES[color_schemes[0]]) else
                                            '#%06X' % random.randint(0, 256 ** 3 - 1)]
                                                for num, value in enumerate(header[1:])]
                configs = [
                              ["Width", 40],
                              ["Height", 40],
                              ["Pie chart border", "None color"],
                              ["Color scheme", color_schemes]
                          ] + list_value_colors + \
                            copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Pie chart")
                # tab_tableview.list_item.name = "attributes"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                      self.make_piechart_face(tab_tableview,
                                                                              editor.ui.tableView.model().arraydata,
                                                                              header,
                                                                              mode="rep"))
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_piechart_face(tab_tableview, array, header, mode="rep"))
                # change value colors according to set
                tab_tableview.model().comboboxTextChanged.connect(lambda index, text:
                                                                self.changeItemsColor(tab_tableview, index, text, header))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_piechart_face(tab_tableview, array, header, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Stacked bar chart":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_stackbar_face(editor.tab.tableview, array, header, mode="rep")
            else:
                color_schemes = list(COLOR_SCHEMES.keys())
                color_schemes.remove("set1")
                color_schemes.insert(0, "set1")
                list_value_colors = [[f"{value} color",
                                      COLOR_SCHEMES[color_schemes[0]][num] if
                                      num < len(COLOR_SCHEMES[color_schemes[0]]) else
                                      '#%06X' % random.randint(0, 256 ** 3 - 1)]
                                     for num, value in enumerate(header[1:])]
                configs = [
                              ["Width", 40],
                              ["Height", 40],
                              ["Pie chart border", "None color"],
                              ["Color scheme", color_schemes]
                          ] + list_value_colors + \
                          copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Stacked bar chart")
                # tab_tableview.list_item.name = "Stacked bar chart"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                      self.make_stackbar_face(tab_tableview,
                                                                              editor.ui.tableView.model().arraydata,
                                                                              header,
                                                                              mode="rep"))
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_stackbar_face(tab_tableview, array, header, mode="rep"))
                # change value colors according to set
                tab_tableview.model().comboboxTextChanged.connect(lambda index, text:
                                                              self.changeItemsColor(tab_tableview, index, text, header))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_stackbar_face(tab_tableview, array, header, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Horizontal bar chart":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_hbar_face(editor.tab.tableview, array, mode="rep")
            else:
                configs = [
                              ["Color", "#f07464"],
                              ["Width", 100],
                              ["Height", 20],
                              ["Height factor", 0.7],
                              ["Min value", 0],
                          ] + copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Horizontal bar chart")
                # tab_tableview.list_item.name = "horizontal bar chart"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                          self.make_hbar_face(tab_tableview,
                                                                             editor.ui.tableView.model().arraydata,
                                                                             mode="rep"))
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_img_face(tab_tableview, array, mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_hbar_face(tab_tableview, array, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Vertical bar chart":
            color_schemes = list(COLOR_SCHEMES.keys())
            if hasattr(editor, "tab"):
                for num, i in enumerate(editor.tab.tableview.model().arraydata):
                    if i[0] == "Color scheme":
                        color_schemes_row = num
                        current_scheme = i[1][0]
                        break
                list_value_colors = [[f"{value} color",
                                      COLOR_SCHEMES[current_scheme][num] if
                                      num < len(COLOR_SCHEMES[current_scheme]) else
                                      '#%06X' % random.randint(0, 256 ** 3 - 1)]
                                            for num, value in enumerate(header[1:])]
                # update existing table view
                editor.tab.tableview.model().update_array(color_schemes_row+1, list_value_colors,
                                                          editor.tab.tableview.list_value_colors)
                editor.tab.tableview.list_value_colors = list_value_colors
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_vbar_face(editor.tab.tableview, array, header, mode="rep")
            else:
                color_schemes.remove("set1")
                color_schemes.insert(0, "set1")
                list_value_colors = [[f"{value} color",
                                      COLOR_SCHEMES[color_schemes[0]][num] if
                                      num < len(COLOR_SCHEMES[color_schemes[0]]) else
                                      '#%06X' % random.randint(0, 256 ** 3 - 1)]
                                     for num, value in enumerate(header[1:])]
                configs = [
                              ["Width", 200],
                              ["Height", 100],
                              ["min value", 0],
                              ["max value", ""],
                              ["Scale size", 6],
                              ["Label font", QFont("Arial", 6, QFont.Normal)],
                              ["Color scheme", color_schemes]
                          ] + list_value_colors + \
                          copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Vertical bar chart")
                # tab_tableview.list_item.name = "vertical bar chart"
                # in order to remove rows
                tab_tableview.list_value_colors = list_value_colors
                tab_tableview.refresh_btn.clicked.connect(lambda:
                                                          self.make_vbar_face(tab_tableview,
                                                                             editor.ui.tableView.model().arraydata,
                                                                             header,
                                                                             mode="rep"))
                # tab_tableview.model().layoutChanged.connect(lambda:
                #                                             self.make_vbar_face(tab_tableview, array, header,
                #                                                                     mode="rep"))
                # change value colors according to set
                tab_tableview.model().comboboxTextChanged.connect(lambda index, text:
                                                                  self.changeItemsColor(tab_tableview, index, text, header))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_vbar_face(tab_tableview, array, header, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Heatmap":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_heatmap_face(editor.tab.tableview, array, header, mode="rep")
            else:
                configs = [
                              ["Width", 200],
                              ["Height", 40],
                              ["max value", 1],
                              ["center value", 0],
                              ["min value", -1],
                              ["style", ["heatmap", "lines", "bars", "cbars"]],
                              ["Color scheme", ["red & blue", "green & blue", "green & red"]],
                              ["Draw value title", True],
                              ["Value title position", ["Top", "Bottom"]],
                              ["Value title font", QFont("Arial", 9, QFont.Normal)],
                              ["Value title rotation", -45]
                          ] + copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Heatmap")
                # tab_tableview.list_item.name = "heatmap"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                      self.make_heatmap_face(tab_tableview,
                                                                             editor.ui.tableView.model().arraydata,
                                                                             header,
                                                                             mode="rep"))
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_heatmap_face(tab_tableview, array, header, mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_heatmap_face(tab_tableview, array, header, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Sequence":
            has_aa = False
            has_nt = False
            for list_row in array:
                if list_row[1]:
                    has_aa = True
                if list_row[2]:
                    has_nt = True
            if (not has_aa) and (not has_nt):
                return
            bg_colors = _aabgcolors if has_aa or (has_nt and has_aa) else _ntbgcolors
            fg_colors = _aafgcolors if has_aa or (has_nt and has_aa) else _ntfgcolors
            seq_type = "aa" if has_aa or (has_nt and has_aa) else "nt"
            list_bg_colors = [[f"{residue} background color", bg_colors[residue]] for residue in bg_colors]
            list_fg_colors = [[f"{residue} foreground color", fg_colors[residue]] for residue in fg_colors]
            if hasattr(editor, "tab"):
                # update existing table view
                editor.tab.tableview.model().update_array(5, list_bg_colors+list_fg_colors,
                                                          editor.tab.tableview.list_bg_colors+editor.tab.tableview.list_fg_colors)
                editor.tab.tableview.list_bg_colors = list_bg_colors
                editor.tab.tableview.list_fg_colors = list_fg_colors
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_seq_face(editor.tab.tableview, array, mode="rep", link=editor.ui.checkBox.isChecked())
            else:
                configs = [
                              ["Font", QFont("Arial", 9, QFont.Normal)],
                              ["Column width", ""],
                              ["Special column", ""],
                              ["Special column width", 3],
                              ["Interactive", False],
                              # ["Sequence type", seq_type],
                          ] + list_bg_colors + \
                              list_fg_colors + \
                                copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Sequence")
                # tab_tableview.list_item.name = "sequence"
                # in order to remove rows
                tab_tableview.list_bg_colors = list_bg_colors
                tab_tableview.list_fg_colors = list_fg_colors
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                      self.make_seq_face(tab_tableview,
                                                                         editor.ui.tableView.model().arraydata,
                                                                         mode="rep",
                                                                         link=editor.ui.checkBox.isChecked()))
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_seq_face(tab_tableview, array, mode="rep",
                #                                                          link=editor.ui.checkBox.isChecked()))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_seq_face(tab_tableview, array, mode="new", link=editor.ui.checkBox.isChecked())
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Motif":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_motif_face(editor.tab.tableview, array, mode="rep")
            else:
                configs = [
                              ["Sequence type", ["aa", "nt"]],
                              ["Gap format", ["line", "blank", "o", ">", "v", "<", "^", "<>", "[]", "()"]],
                              ["Sequence format", ["()", "o", ">", "v", "<", "^", "<>", "[]", "", "line", "seq", "compactseq", "blank"]],
                              ["Scale factor", 1],
                              ["Height", 10],
                              ["Width", 10],
                              ["Motif foreground color", "#708090"],
                              ["Motif background color", "#708090"],
                              ["Gap color", "#000000"],
                          ] + copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Motif")
                # tab_tableview.list_item.name = "motif"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                          self.make_motif_face(tab_tableview,
                                                                               editor.ui.tableView.model().arraydata,
                                                                               mode="rep"))
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                             self.make_motif_face(tab_tableview, array, mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_motif_face(tab_tableview, array, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
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
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_strip_face(editor.tab.tableview, array, mode="rep")
            else:
                configs = [
                              # ["Height factor", 1],
                              ["Height", "auto"],
                              ["Width", 10]
                          ] + copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Color strip")
                # tab_tableview.list_item.name = "color strip"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                          self.make_strip_face(tab_tableview,
                                                                              editor.ui.tableView.model().arraydata,
                                                                              mode="rep"))
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
        elif type == "Shape":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_shape_face(editor.tab.tableview, array, check_array, mode="rep")
            else:
                configs = [
                              ["Height", 13],
                              ["Width", 13]
                          ] + copy.deepcopy(self.face_base_parameters) if not configs else configs
                tab_tableview = self.add_tableView(configs, "Shape")
                # tab_tableview.list_item.name = "shape"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                          self.make_shape_face(tab_tableview,
                                                                               editor.ui.tableView.model().arraydata,
                                                                               editor.ui.tableView.model().check_states,
                                                                               mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_shape_face(tab_tableview, array, check_array, mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Auto-assign taxonomy (style 1)":
            self.make_taxonomy_face1(
                                editor.ui.tableView.model().fetchIncludedArray(),
                                editor.ui.tableView.model().fetchIncludedTax(),
                                editor.ui.tableView.model().get_colors(),
                                mode="rep")
        elif type == "Auto-assign taxonomy (style 2)":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.make_taxonomy_face2(editor.tab.tableview, array,
                                editor.ui.tableView.model().fetchIncludedTax(),
                                editor.ui.tableView.model().get_colors(),
                                mode="rep")
            else:
                configs = [
                              # ["Strip height", 20],
                              # ["Strip width", 10]
                          ] + copy.deepcopy(self.face_base_parameters) if not configs else configs
                if ["Position", ["aligned", "branch-right", "branch-top", "branch-bottom", "float", "float-behind"]] in configs:
                    index_pos = configs.index(["Position", ["aligned", "branch-right", "branch-top", "branch-bottom", "float", "float-behind"]])
                    configs[index_pos] = ["Position", ["branch-top", "branch-right", "aligned", "branch-bottom", "float", "float-behind"]]
                tab_tableview = self.add_tableView(configs, "Auto-assign taxonomy (style 2)")
                # tab_tableview.list_item.name = "Auto-assign taxonomy (style 2)"
                tab_tableview.refresh_btn.clicked.connect(lambda :
                                                                self.make_taxonomy_face2(tab_tableview,
                                                                    editor.ui.tableView.model().fetchIncludedArray(),
                                                                    editor.ui.tableView.model().fetchIncludedTax(),
                                                                    editor.ui.tableView.model().get_colors(),
                                                                    mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_taxonomy_face2(tab_tableview, array,
                    editor.ui.tableView.model().fetchIncludedTax(),
                    editor.ui.tableView.model().get_colors(),  mode="new")
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
                    # self.tabWidget.setCheckState(self.tabWidget.indexOf(tab_tableview.tab), tabIsChecked)
        elif type == "Attributes":
            if hasattr(editor, "tab"):
                # update existing table view
                self.tabWidget.setCurrentIndex(2)
                self.stackedWidget.setCurrentWidget(editor.tab)
                self.redraw() # make_attribute_face will be exeuted here
                # self.make_attribute_face(editor.tab.tableview, array, mode="rep", dict_args=editor.ui.get_parameters())
            else:
                configs = copy.deepcopy(self.face_base_parameters) if not configs else configs
                if ["Position", ["aligned", "branch-right",
                                 "branch-top", "branch-bottom", "float", "float-behind"]] in configs:
                    index_pos = configs.index(["Position",
                                                 ["aligned", "branch-right", "branch-top",
                                                  "branch-bottom", "float", "float-behind"]])
                    configs[index_pos] = ["Position",
                                            ["branch-top", "branch-right", "aligned",
                                             "branch-bottom", "float", "float-behind"]]
                tab_tableview = self.add_tableView(configs, "Attributes")
                # tab_tableview.list_item.name = "attributes"
                tab_tableview.refresh_btn.clicked.connect(lambda : self.redraw()
                                        # self.make_attribute_face(tab_tableview,
                                        #     editor.ui.tableView.model().arraydata,
                                        #     mode="rep",
                                        #     dict_args=editor.ui.get_parameters())
                                                            )
                # tab_tableview.model().layoutChanged.connect(lambda :
                #                                       self.make_text_face(tab_tableview, array, mode="rep"))
                tab_tableview.data_edit_btn.clicked.connect(editor.show)
                tab_tableview.list_item.widget.btn_edit.clicked.connect(editor.show)
                editor.tab = tab_tableview.tab
                tab_tableview.editor = editor
                self.make_attribute_face(tab_tableview, array, mode="new", dict_args=editor.ui.get_parameters())
                if tabIsChecked != None:
                    self.listWidget.setItemChecked(tab_tableview.list_item, tabIsChecked)
        # select the item
        if type != "Auto-assign taxonomy (style 1)":
            self.listWidget.setCurrentItem(editor.tab.tableview.list_item)
            self.listWidget.itemClicked.emit(editor.tab.tableview.list_item)

    def changeItemsColor(self, tab_tableview, index, text, header):
        model = tab_tableview.model()
        left_index = model.index(index.row(), 0)
        if left_index.data(Qt.DisplayRole) == "Color scheme":
            model.layoutAboutToBeChanged.emit()
            for i in range(len(header[1:])):
                color = COLOR_SCHEMES[text][i] if i < len(COLOR_SCHEMES[text]) else '#%06X' % random.randint(0, 256 ** 3 - 1)
                model.arraydata[index.row()+i+1][1] = color
            model.layoutChanged.emit()

    def init_two_trees(self, dict_compare_args):
        # 已有的face如何保留？
        # if hasattr(self.scene, "tree"):
        #     del self.scene.tree
        # if hasattr(self.scene, "img"):
        #     del self.scene.img
        # if hasattr(self.scene, "n2i"):
        #     del self.scene.n2i
        # if hasattr(self.scene, "n2f"):
        #     del self.scene.n2f
        if not dict_compare_args:
            QMessageBox.information(
                self,
                "PhyloSuite",
                "<p style='line-height:25px; height:25px'>Please input two trees and connections first!</p>")
            self.actioncompare_mode.setChecked(False)
            self.on_actioncompare_mode_triggered()
            return
        self.dict_compare_args = dict_compare_args
        if not self.compare_mode:
            tre1 = dict_compare_args["tree1"]
            tre2 = dict_compare_args["tree2"]
            ts1 = TreeStyle()
            ts1.margin_right = dict_compare_args["space"]
            ts1.legend_position = 1
            ts2 = TreeStyle()
            ts2.legend_position = 2
            ts2.orientation = 1
            self.scene.tree = tre2
            self.scene.img = ts2
            # clear face
            self.clear_faces()
            self.compare_mode = "tree2"
            self.init_GUI(force_new=True) #, nodraw=True)
            # add t2 to the right of t1
            tree_face2 = TreeFace(tre2, ts2)
            ts1.aligned_treeface_hz.add_face(tree_face2, column=0)
            self.scene.tree = tre1
            # print(tre2 == tre1) False
            self.scene.img = ts1
            # clear face
            self.clear_faces()
            self.compare_mode = "tree1"
            self.toolButton.setChecked(True)
            # this function will redraw the tree
            self.init_GUI(force_new=True)  # , nodraw=True)
            # add t2 to the right of t1
            # tree_face2 = TreeFace(tre2, ts2)
            # ts1.aligned_treeface_hz.add_face(tree_face2, column=0)
            # self.scene.tree = tre1
            # # print(tre2 == tre1) False
            # self.scene.img = ts1
            # # clear face
            # self.clear_faces()
            # self.compare_mode = "tree1"
            # self.toolButton.setChecked(True)
            # # this function will redraw the tree
            # self.init_GUI(force_new=True)  # , nodraw=True)
            # self.scene.tree = tre2
            # self.scene.img = ts2
            # # clear face
            # self.clear_faces()
            # self.compare_mode = "tree2"
            # self.init_GUI(force_new=True) #, nodraw=True)
        else:
            self.scene.img.margin_right = dict_compare_args["space"]
            self.redraw()

    def update_tree2(self, tre2, ts2):
        tree_face2 = self.toolButton.treestyle.aligned_treeface_hz[0][0]
        tree_face2.root_node = tre2
        tree_face2.img = ts2
        self.toolButton.treestyle.aligned_treeface_hz[0][0] = tree_face2

    def show_two_trees(self):
        # parameters
        line_len = self.dict_compare_args["h_line_len"]
        line_width = self.dict_compare_args["line_width"]
        margin = self.dict_compare_args["margin"]
        dict_connections = {}
        dict_connections2 = {}
        for row in self.compare_setting.model.arraydata:
            dict_connections[row[0]] = row
            dict_connections2[row[1]] = row
            # dict_connections_rev[row[1]] = row[0]
        # dict_connections = {row[0]:row for row in self.compare_setting.model.arraydata}
        # dict_connections2 = {row[1]:row for row in self.compare_setting.model.arraydata}
        self.dict_group_colors = self.compare_setting.model.get_colors()
        tre1 = self.toolButton.tree
        tre1_style = self.toolButton.treestyle
        # n2i1 = self.scene.n2i
        tree1_n2f = self.scene.n2f
        # tree_face2 = self.toolButton.tree_face2
        # self.redraw()
        # connection
        # remove old connectons
        if hasattr(self, "list_connection_items") and self.list_connection_items:
            for i in self.list_connection_items:
                self.scene.removeItem(i)
        else:
            self.list_connection_items = []
        self.list_connection_items = []
        dict_tre1_position = {}
        dict_tre1_items = {}
        # id2i = {j.id:self.scene.n2i[j] for j in self.scene.n2i}
        # get max x
        pos = None
        list_tre1_items = []
        list_tre1_x = []
        for node in tre1.traverse():
            if node.is_leaf():
                if not hasattr(node, "id") or (node.id not in dict_connections):
                    continue
                pos = self.get_used_pos(tree1_n2f, node) if not pos else pos
                item = tree1_n2f[node][pos]
                x1, y1, x2, y2 = item.mapToScene(item.boundingRect()).boundingRect().getCoords()
                list_tre1_x.append(x2)
                # item_scene_rect = item.mapToScene(self.scene.n2i[node].boundingRect()).boundingRect()
                x = x2# +item.fullRegion.width()
                y = (y1+y2)/2 #+ item.fullRegion.height()/2
                color = self.dict_group_colors[dict_connections[node.id][2]] if dict_connections[node.id][2] else Qt.black
                # draw horizontal line
                h_line = QGraphicsLineItem(x, y, x + line_len, y)
                pen = QPen(QColor(color))
                pen.setWidth(line_width)
                pen.setCapStyle(Qt.FlatCap)
                h_line.setPen(pen)
                # shape
                if self.dict_compare_args["draw_shape"]:
                    shape_name = dict_connections[node.id][3][0]
                    if shape_name in ["circle", "rectangle", "line", "round corner rectangle"]:
                        shape1 = self.dict_compare_args["dict_shape"][shape_name](0, 0, self.dict_compare_args["shape width"],
                                                                       self.dict_compare_args["shape height"])
                    elif shape_name in ["star", "star2"]:
                        shape1 = self.dict_compare_args["dict_shape"][shape_name](self.dict_compare_args["shape width"])
                        shape1.setPos(0, 0)
                    else:
                        shape1 = self.dict_compare_args["dict_shape"][shape_name](self.dict_compare_args["shape width"],
                                                                 self.dict_compare_args["shape height"])
                    shape1.setParentItem(h_line)
                    shape1.setPen(QPen(QColor(color)))
                    shape1.setBrush(QBrush(QColor(color)))
                dict_tre1_items.setdefault(node.id, []).append(h_line)
                dict_tre1_position[node.id] = [x + line_len, y] # x, y
                list_tre1_items.append(h_line)
                # list_tre1_items.append(shape1)
        if not list_tre1_x:
            # when input two tree and connection when close last compare mode, init_GUI (tre2) will call this method,
            # wheres tree1 is still belonging to last compare mode, cause empty list_tre1_x
            return
        # to make sure line start with the longest name
        keys = list(dict_tre1_position.keys())
        max_x = max(list_tre1_x) + margin + self.dict_compare_args["shape width"]/2
        for num in range(len(list_tre1_items)):
            line_item = list_tre1_items[num]
            lineF = line_item.line()
            x1, y1, x2, y2 = lineF.x1(), lineF.y1(), lineF.x2(), lineF.y2()
            line_item.setLine(max_x, y1, x2+(max_x-x1), y2)
            x, y = dict_tre1_position[keys[num]]
            dict_tre1_position[keys[num]] = [x+(max_x-x1), y]
            # child item's position (shape)
            child_items = line_item.childItems()
            for child_item in child_items:
                penWidth = child_item.pen().width()
                child_item.setPos(max_x-child_item.boundingRect().width()/2,
                    line_item.boundingRect().center().y() - child_item.boundingRect().height()/2 + penWidth/2)
        self.list_connection_items.extend(list_tre1_items)
        # print(dict_tre1_position)
        dict_tre2_position = {}
        dict_tre2_items = {}
        tree_face2 = tre1_style.aligned_treeface_hz[0][0]
        tre2 = tree_face2.root_node
        tre2_n2f = tree_face2.n2f
        pos = None
        list_tre2_items = []
        list_tre2_x = []
        for node in tre2.traverse():
            if node.is_leaf():
                if node.id not in dict_connections2:
                    continue
                pos = self.get_used_pos(tre2_n2f, node) if not pos else pos
                if not pos:
                    continue
                item = tre2_n2f[node][pos]
                x1, y1, x2, y2 = item.mapToScene(item.boundingRect()).boundingRect().getCoords()
                list_tre2_x.append(x1)
                x = x1 # -item.fullRegion.width()
                y = (y1+y2)/2 # + item.fullRegion.height()/2
                color = self.dict_group_colors[dict_connections2[node.id][2]] if dict_connections2[node.id][2] else Qt.black
                # draw horizontal line
                h_line2 = QGraphicsLineItem(x, y, x - line_len, y)
                pen = QPen(QColor(color))
                pen.setWidth(line_width)
                pen.setCapStyle(Qt.FlatCap)
                h_line2.setPen(pen)
                # shape
                if self.dict_compare_args["draw_shape"]:
                    shape_name2 = dict_connections2[node.id][4][0]
                    if shape_name2 in ["circle", "rectangle", "line", "round corner rectangle"]:
                        shape2 = self.dict_compare_args["dict_shape"][shape_name2](0, 0, self.dict_compare_args["shape width"],
                                                                       self.dict_compare_args["shape height"])
                    elif shape_name2 in ["star", "star2"]:
                        shape2 = self.dict_compare_args["dict_shape"][shape_name2](self.dict_compare_args["shape width"])
                        shape2.setPos(0, 0)
                    else:
                        shape2 = self.dict_compare_args["dict_shape"][shape_name2](self.dict_compare_args["shape width"],
                            self.dict_compare_args["shape height"])
                    shape2.setParentItem(h_line2)
                    shape2.setPen(QPen(QColor(color)))
                    shape2.setBrush(QBrush(QColor(color)))
                dict_tre2_items.setdefault(node.id, []).append(h_line2)
                dict_tre2_position[node.id] = [x - line_len, y]
                list_tre2_items.append(h_line2)
                # list_tre2_items.append(shape2)
        # to make sure line start with the longest name
        keys = list(dict_tre2_position.keys())
        min_x = min(list_tre2_x) - margin - self.dict_compare_args["shape width"]/2
        for num in range(len(list_tre2_items)):
            line_item = list_tre2_items[num]
            lineF = line_item.line()
            x1, y1, x2, y2 = lineF.x1(), lineF.y1(), lineF.x2(), lineF.y2()
            line_item.setLine(min_x, y1, x2-(x1-min_x), y2)
            x, y = dict_tre2_position[keys[num]]
            dict_tre2_position[keys[num]] = [x-(x1-min_x), y]
            # child item's position (shape)
            child_items = line_item.childItems()
            for child_item in child_items:
                penWidth = child_item.pen().width()
                child_item.setPos(min_x-child_item.boundingRect().width()/2+penWidth,
                    line_item.boundingRect().center().y() - child_item.boundingRect().height()/2 + penWidth/2)
        self.list_connection_items.extend(list_tre2_items)
        # print(dict_tre2_position)
        # draw connect line
        connected_leafs = []
        for tre1_ID in dict_tre1_position:
            tre2_ID = dict_connections[tre1_ID][1]
            if tre2_ID in dict_tre2_position:
                tre2_pos = dict_tre2_position[tre2_ID]
                tre1_pos = dict_tre1_position[tre1_ID]
                connect_line = QGraphicsLineItem(tre1_pos[0], tre1_pos[1], tre2_pos[0], tre2_pos[1])
                color = self.dict_group_colors[dict_connections[tre1_ID][2]] if dict_connections[tre1_ID][2] else Qt.black
                pen = QPen(QColor(color))
                pen.setWidth(line_width)
                pen.setCapStyle(Qt.FlatCap)
                connect_line.setPen(pen)
                # self.scene.addItem(connect_line)
                self.list_connection_items.append(connect_line)
                connected_leafs.append([tre1_ID, tre2_ID])
            else:
                for item in dict_tre1_items[tre1_ID]:
                    # self.scene.removeItem(item)
                    self.list_connection_items.remove(item)
        # connected remaining leaf
        for tre2_ID in dict_tre2_position:
            tre1_ID = dict_connections2[tre2_ID][0]
            if ([tre1_ID, tre2_ID] not in connected_leafs):
                if (tre1_ID in dict_tre1_position):
                    tre2_pos = dict_tre2_position[tre2_ID]
                    tre1_pos = dict_tre1_position[tre1_ID]
                    connect_line = QGraphicsLineItem(tre1_pos[0], tre1_pos[1], tre2_pos[0], tre2_pos[1])
                    color = self.dict_group_colors[dict_connections2[tre2_ID][2]] if dict_connections2[tre2_ID][2] else Qt.black
                    pen = QPen(QColor(color))
                    pen.setWidth(line_width)
                    pen.setCapStyle(Qt.FlatCap)
                    connect_line.setPen(pen)
                    # self.scene.addItem(connect_line)
                    self.list_connection_items.append(connect_line)
                    # connected_leafs.append([tre1_ID, tre2_ID])
                else:
                    for item in dict_tre2_items[tre2_ID]:
                        # self.scene.removeItem(item)
                        self.list_connection_items.remove(item)
        for item in self.list_connection_items:
            self.scene.addItem(item)
            item.setZValue(100)

    def tree_switch(self):
        if self.toolButton.isChecked():
            self.scene.tree = self.toolButton.tree
            self.scene.img = self.toolButton.treestyle
            # restore faces
            self.clear_faces()
            self.compare_mode = "tree1"
            for page in self.toolButton.list_pages:
                self.stackedWidget.addWidget(page)
            for num, item in enumerate(self.toolButton.list_items):
                # Set size hint
                label, ifhidden, ifcheck = self.toolButton.list_widgets_data[num]
                widget = ListItemWidget(label, item, parent=self.listWidget, hide_btn=ifhidden, ifCheck=ifcheck)
                widget.checkBox.stateChanged.connect(lambda state: self.judge_remove(state,
                                                                        self.sender().listwidgetItem.page_widget))
                widget.btn_close.clicked.connect(self.listWidget.removeItem)
                item.setSizeHint(widget.sizeHint())
                self.listWidget.addItem(item)
                self.listWidget.setItemWidget(item, widget)
        elif self.toolButton_2.isChecked():
            self.scene.tree = self.toolButton_2.tree
            self.scene.img = self.toolButton_2.treestyle
            # restore faces
            self.clear_faces()
            self.compare_mode = "tree2"
            for page in self.toolButton_2.list_pages:
                self.stackedWidget.addWidget(page)
            for num, item in enumerate(self.toolButton_2.list_items):
                # Set size hint
                label, ifhidden, ifcheck = self.toolButton_2.list_widgets_data[num]
                widget = ListItemWidget(label, item, parent=self.listWidget, hide_btn=ifhidden, ifCheck=ifcheck)
                widget.checkBox.stateChanged.connect(lambda state: self.judge_remove(state,
                                                                        self.sender().listwidgetItem.page_widget))
                widget.btn_close.clicked.connect(self.listWidget.removeItem)
                item.setSizeHint(widget.sizeHint())
                self.listWidget.addItem(item)
                self.listWidget.setItemWidget(item, widget)
        self.init_tree_props()

    def store_faces(self):
        if not self.compare_mode:
            return
        list_items = [self.listWidget.item(i) for i in range(self.listWidget.count())
                      if self.listWidget.itemWidget(self.listWidget.item(i))]
        list_widgets_data = [self.listWidget.itemWidget(self.listWidget.item(i)).data() for i in
                             range(self.listWidget.count()) if self.listWidget.itemWidget(self.listWidget.item(i))]
        list_pages = [self.stackedWidget.widget(i) for i in range(self.stackedWidget.count())]
        if self.compare_mode == "tree1":
            self.toolButton.list_items = list_items
            self.toolButton.list_widgets_data = list_widgets_data
            self.toolButton.list_pages = list_pages
        elif self.compare_mode == "tree2":
            self.toolButton_2.list_items = list_items
            self.toolButton_2.list_widgets_data = list_widgets_data
            self.toolButton_2.list_pages = list_pages

    def clear_faces(self):
        self.store_faces()
        # delete faces
        # self.listWidget.clear()
        for i in reversed(range(self.listWidget.count())):
            item = self.listWidget.takeItem(i)
            # del item
        for i in reversed(range(self.stackedWidget.count())):
            widget = self.stackedWidget.widget(i)
            self.stackedWidget.removeWidget(widget)
            # widget.deleteLater()
            # del widget

    def clear_trees(self, init_mode=True):
        # self.toolButton.tree = None
        # self.toolButton.treestyle = TreeStyle()
        # self.toolButton_2.tree = None
        # self.toolButton_2.treestyle = TreeStyle()
        if self.scene.tree:
            reply = QMessageBox.question(
                self,
                "Confirmation",
                "<p style='line-height:25px; height:25px'>Would you like to save current tree and its annotation first?</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.on_actionsaveSession_triggered()
        if init_mode:
            self.actioncompare_mode.setChecked(False)
            self.on_actioncompare_mode_triggered(ignore_clear_tree=True)
        self.scene.tree = None
        self.dict_tree_names = {"tree": [], "tree1": [], "tree2": []}
        self.scene.img = TreeStyle()
        if self.scene.master_item:
            # delete old items
            self.scene.removeItem(self.scene.master_item)
        if hasattr(self, "list_connection_items") and self.list_connection_items:
            for i in self.list_connection_items:
                self.scene.removeItem(i)
        self.view.update()

    def make_trangle_legend(self):
        for column in list(self.scene.img.legend.keys()):
            for legend in self.scene.img.legend[column]:
                if legend.name == "tangle tree legend":
                    self.scene.img.legend.pop(column)
        if not self.dict_compare_args["draw legend"]:
            return
        # self.dict_compare_args["dict_group_colors"] = self.compare_setting.model.get_colors()
        # list_groups = list(set([list_row[2] for list_row in self.compare_setting.model.arraydata if list_row[2]]))
        # self.dict_compare_args["list_groups"] = list(self.dict_compare_args["dict_group_colors"].keys())
        F = faces.DynamicItemFace(self.make_trangle_legend_slot)
        F.name = "tangle tree legend"
        self.scene.img.legend.legend_position = 4
        self.scene.img.legend.add_face(F, column=0)

    def make_trangle_legend_slot(self, node):
        dict_colors = self.dict_compare_args["dict_group_colors"]
        list_groups = self.dict_compare_args["list_groups"]
        title = self.dict_compare_args["legend title"]
        title_font = self.dict_compare_args["title font"]
        text_font = self.dict_compare_args["text font"]
        margin = self.dict_compare_args["box margin"]
        group_line_width = self.dict_compare_args["line width"]
        master_rect = QGraphicsRectItem(0, 0, 50, 50)
        master_rect.setPen(QPen(QColor(Qt.gray)))
        master_rect.node = node
        master_bounding_r = master_rect.boundingRect()
        list_items = []
        height = 0
        # legend title
        Title = QGraphicsTextItem(title)
        Title.setTextInteractionFlags(Qt.TextEditorInteraction)
        Title.setFont(title_font)
        Title.setPos(master_bounding_r.x()+margin, master_bounding_r.y()+margin)
        list_items.append(Title)
        height += Title.boundingRect().height() + 1
        # space line
        x1, y1, x2, y2 = Title.boundingRect().getCoords()
        space_line = QGraphicsLineItem(master_bounding_r.x()+margin, y2+1, master_bounding_r.x()+margin+5, y2+1)
        space_line.setPen(QPen(Qt.gray))
        space_line.pen().setWidth(0.5)
        list_items.append(space_line)
        height += space_line.boundingRect().height() + 1
        # 记得设置线的长度
        # legend box
        last_item = space_line
        max_group_width = Title.boundingRect().width() + margin
        for group in list_groups:
            x1, y1, x2, y2 = last_item.boundingRect().getCoords()
            color = dict_colors[group]
            group_rect = QGraphicsRectItem()
            text = QGraphicsTextItem(group)
            text.setTextInteractionFlags(Qt.TextEditorInteraction)
            text.setFont(text_font)
            th = text.boundingRect().height()
            tw = text.boundingRect().width()
            # set group_rect pos
            group_rect.setRect(x1+1, y2+1, th, th)
            group_rect.setPen(QPen(Qt.NoPen))
            group_line = QGraphicsLineItem()
            group_line.setLine(group_rect.boundingRect().x()+1,
                               group_rect.boundingRect().center().y()-group_line.boundingRect().height()/2,
                               group_rect.boundingRect().x()+group_rect.boundingRect().width()-1,
                               group_rect.boundingRect().center().y()-group_line.boundingRect().height()/2)
            # set text pos
            text.setPos(group_rect.boundingRect().width()+1, group_rect.boundingRect().y())
            pen = QPen(QColor(color))
            pen.setWidth(group_line_width)
            group_line.setPen(pen)
            # set group_rect pos
            last_item = group_rect
            list_items.extend([group_rect, text, group_line])
            height += group_rect.boundingRect().height() + 1
            group_width = 1+group_rect.boundingRect().width()+1+tw
            if group_width > max_group_width:
                max_group_width = group_width
        x1, y1, x2, y2 = Title.boundingRect().getCoords()
        space_line.setLine(master_bounding_r.x()+margin, y2+1, master_bounding_r.x()+margin+max_group_width, y2+1)
        master_rect.setRect(0, 0, space_line.boundingRect().width()+2*margin, height+2*margin)
        for item in list_items:
            item.setParentItem(master_rect)
        return master_rect

    def get_used_pos(self, n2f, node):
        for i in ["aligned", "branch-right", "branch-top", "branch-bottom", "float", "float-behind"]:
            if len(set(n2f[node][i].boundingRect().getCoords())) != 1:
                return i

    def update_tree_message(self, node):
        # if not self.compare_mode:
        leaf_num = len(node.get_leaves())
        node_num = len(node.get_descendants())+1
        # root_info = "rooted tree" if self.scene.tree.is_root() else "unrooted tree"
        self.statusBar().showMessage(f"Leaf: {leaf_num}; node: {node_num}")
        # else:
        #     leaf_num1 = len(self.scene.tree.get_leaves())
        #     node_num1 = len(self.scene.tree.get_descendants())+1
        #     # root_info1 = "rooted tree" if self.scene.tree.is_root() else "unrooted tree"
        #     tree_face2 = self.scene.img.aligned_treeface_hz[0][0]
        #     tre2 = tree_face2.root_node
        #     leaf_num2 = len(tre2.get_leaves())
        #     node_num2 = len(tre2.get_descendants())+1
        #     # root_info2 = "rooted tree" if tre2.is_root() else "unrooted tree"
        #     self.statusBar().showMessage(f"Tree1: leaf: {leaf_num1}, node: {node_num1}. "
        #                                  f"Tree2: leaf: {leaf_num2}, node: {node_num2}")

    def update_faces(self):
        # color strip
        for node in self.scene.tree.traverse():
            for i in set(["branch-right", "branch-top", "branch-bottom", "float", "float-behind", "aligned"]):
                dict_faces = getattr(node.faces, i) # {0: [Attribute Face [name] (0x2755892486)], 1: [Attribute Face [name] (0x2755892486)]}
                if dict_faces:
                    for col in list(dict_faces.keys()):
                        for face in dict_faces[col]: # [Attribute Face [name] (0x2755892486)]
                            if face.name == "strip":
                                face.node = node
                                face.update_items(node=node)


class _BasicNodeActions(object):
    """ Should be added as ActionDelegator """

    @staticmethod
    def init(obj):
        obj.setCursor(Qt.PointingHandCursor)
        obj.setAcceptHoverEvents(True)

    @staticmethod
    def hoverEnterEvent (obj, e):
        print("HOLA")

    @staticmethod
    def hoverLeaveEvent(obj, e):
        print("ADIOS")

    @staticmethod
    def mousePressEvent(obj, e):
        print("Click")

    @staticmethod
    def mouseReleaseEvent(obj, e):
        if e.button() == Qt.RightButton:
            obj.showActionPopup()
        elif e.button() == Qt.LeftButton:
            obj.scene().view.set_focus(obj.node)
            #obj.scene().view.node_prop_table.update_properties(obj.node)

    @staticmethod
    def hoverEnterEvent (self, e):
        # print(f"{self.node.id} hover enter")
        self.scene().view.highlight_node(self.node, fullRegion=True)

    @staticmethod
    def hoverLeaveEvent(self,e):
        # print(f"{self.node.id} hover enter")
        self.scene().view.unhighlight_node(self.node)


