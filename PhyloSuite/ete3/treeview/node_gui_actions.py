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

import inspect
import platform
from functools import partial

# from PyQt5 import QtWidgets, QtCore
# from PyQt5.QtCore import QSettings
# from PyQt5.QtWidgets import QFileDialog, QApplication
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ete3 import TextFace
from six.moves import range

from src.factory import Factory
from .qt import Qt, QDialog, QMenu, QCursor, QInputDialog
from .svg_colors import random_color
from . import  _show_newick
from ..evol import EvolTree
from uifiles.Ui_calibrate import Ui_Calibrate


class NewickDialog(QDialog):
    def __init__(self, node, *args):
        QDialog.__init__(self, *args)
        self.node = node

    def update_newick(self):
        f = int(self._conf.nwFormat.currentText())

        if self._conf.useAllFeatures.isChecked():
            features = []
        elif self._conf.features_list.count() == 0:
            features = None
        else:
            features = set()
            for i in range(self._conf.features_list.count()):
                features.add(str(self._conf.features_list.item(i).text()))

        nw = self.node.write(format=f, features=features)
        self._conf.newickBox.setText(nw)

    def add_feature(self):
        aName = str(self._conf.attrName.text()).strip()
        if aName != '' and not self._conf.features_list.findItems(aName, Qt.MatchCaseSensitive):
            self._conf.features_list.addItem(aName)
            self.update_newick()


    def del_feature(self):
        r = self._conf.features_list.currentRow()
        self._conf.features_list.takeItem(r)
        self.update_newick()

    def set_custom_features(self):
        state = self._conf.useAllFeatures.isChecked()
        self._conf.features_list.setDisabled(state)
        self._conf.attrName.setDisabled(state)
        self.update_newick()



class _NodeActions(object):
    """ Used to extend QGraphicsItem features """
    def __init__(self):
        #self.mcmcTree = MCMCTree()
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptHoverEvents(True)
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.Ui_calibration = Ui_Calibrate

    def mouseReleaseEvent(self, e):
        if not self.node:
            return

        if e.button() == Qt.RightButton:
            # when there are tree1 and tree2, auto switch them
            if hasattr(self.node, "parent"):
                if self.node.parent == "tree1":
                    self.scene().GUI.toolButton.setChecked(True)
                elif self.node.parent == "tree2":
                    self.scene().GUI.toolButton_2.setChecked(True)
            self.showActionPopup()
        elif e.button() == Qt.LeftButton:
            self.scene().view.set_focus(self.node)

            if isinstance(self.node, EvolTree) and self.node.get_tree_root()._is_mark_mode():
                root = self.node.get_tree_root()
                all_marks = set([getattr(n, "mark", '').replace('#', '').strip()
                                 for n in root.traverse() if n is not self.node])
                all_marks.discard('')

                max_value = max(map(int, all_marks)) if all_marks else 0

                current_mark = getattr(self.node, "mark", "")
                try:
                    current_mark = int(current_mark.replace('#', ''))
                except:
                    current_mark = 0

                if current_mark > max_value:
                    self._gui_unmark_node()
                else:
                    self._gui_mark_node('#%d'% (current_mark + 1))


            #self.scene().view.prop_table.update_properties(self.node)


    def hoverEnterEvent (self, e):
        if self.node:
            if self.node in self.scene().view.n2hl:
                pass
            else:
                self.scene().view.highlight_node(self.node, fullRegion=True)

    def hoverLeaveEvent(self,e):
        if self.node:
            if self.node in self.scene().view.n2hl:
                self.scene().view.unhighlight_node(self.node, reset=False)

    def mousePressEvent(self,e):
        pass

    def mouseDoubleClickEvent(self,e):
        if self.node:
            item = self.scene().n2i[self.node]
            if item.highlighted:
                self.scene().view.unhighlight_node(self.node, reset=True)
            else:
                self.scene().view.highlight_node(self.node, fullRegion=True,
                                                 bg=random_color(l=0.5, s=0.5), permanent=True)

    def showActionPopup(self):
        contextMenu = QMenu()
        contextMenu.addAction( "Set as outgroup (root tree)", self.set_as_outgroup)
        contextMenu.addAction( "Copy partition", self.copy_partition)
        contextMenu.addAction( "Cut partition", self.cut_partition)
        if self.scene().view.buffer_node:
            contextMenu.addAction( "Paste partition", self.paste_partition)

        contextMenu.addAction( "Delete node (collapse children)", self.delete_node)
        contextMenu.addAction( "Delete partition", self.detach_node)
        contextMenu.addAction( "Populate subtree", self.populate_partition)
        contextMenu.addAction( "Add children", self.add_children)
        contextMenu.addAction( "Swap branches", self.swap_branches)
        if self.node.img_style["draw_descendants"] == False:
            contextMenu.addAction( "Open", self.toggle_collapse)
        else:
            contextMenu.addAction( "Close", self.toggle_collapse)

        if self.node.up is not None and\
                self.scene().tree == self.node:
            contextMenu.addAction( "Back to parent", self.back_to_parent_node)
        else:
            contextMenu.addAction( "Extract", self.set_start_node)
        contextMenu.addAction( "Extract branch lengths", self.extract_branch_len)
        contextMenu.addAction( "Add calibration", self.add_calibration)
        contextMenu.addAction( "Remove calibration", self.rm_calibration)
        contextMenu.addAction( "Unroot tree", self.unroot_tree)
        contextMenu.addAction("Copy leaf labels", self.copy_leaf_labels)

        if isinstance(self.node, EvolTree):
            root = self.node.get_tree_root()
            all_marks = set([getattr(n, "mark", '').replace('#', '').strip()
                             for n in root.traverse() if n is not self.node])
            all_marks.discard('')
            max_value = max(map(int, all_marks)) if all_marks else 1

            current_mark = getattr(self.node, "mark", '').replace('#', '').strip()
            current_mark = int(current_mark) if current_mark != '' else 0

            if current_mark <= max_value:
                mark = "#%d" %(current_mark + 1)
                contextMenu.addAction("ETE-evol: mark node as " + mark, partial(
                    self._gui_mark_node, mark))
                contextMenu.addAction("ETE-evol: mark group as " + mark, partial(
                    self._gui_mark_group, mark))

            if getattr(self.node, "mark", None):
                contextMenu.addAction("ETE-evol: clear mark in node", partial(
                    self._gui_unmark_node))
                contextMenu.addAction("ETE-evol: clear mark in group", partial(
                    self._gui_unmark_group))


        contextMenu.addAction( "Show newick", self.show_newick)
        contextMenu.exec_(QCursor.pos())

    def _gui_mark_node(self, mark=None):
        if not mark:
            if self.node.mark:
                mark = '#' + str(int(self.node.mark.replace('#', '')) + 1)
            else:
                mark = '#1'
        self.node.mark_tree([self.node.node_id], marks=[mark])
        self.scene().GUI.redraw()


    def _gui_unmark_node(self):
        self.node.mark = ""
        self.scene().GUI.redraw()

    def _gui_mark_group(self, mark=None):
        self.node.mark_tree([self.node.node_id], marks=[mark])
        for leaf in self.node.iter_descendants():
            leaf.mark_tree([leaf.node_id], marks=[mark])
        self.scene().GUI.redraw()

    def _gui_unmark_group(self):
        self.node.mark = ""
        for leaf in self.node.iter_descendants():
            leaf.mark = ""
        self.scene().GUI.redraw()

    def show_newick(self):
        d = NewickDialog(self.node)
        d._conf = _show_newick.Ui_Newick()
        d._conf.setupUi(d)
        d.update_newick()
        d.exec_()
        return False

    def delete_node(self):
        self.node.delete()
        self.scene().GUI.redraw()

    def detach_node(self):
        self.node.detach()
        self.scene().GUI.redraw()

    def swap_branches(self):
        self.node.swap_children()
        self.scene().GUI.redraw()

    def add_children(self):
        n,ok = QInputDialog.getInt(None,"Add childs","Number of childs to add:",1,1)
        if ok:
            for i in range(n):
                ch = self.node.add_child()
        self.scene().GUI.redraw()

    def void(self):
        return True

    def copy_leaf_labels(self):
        labels = self.node.get_leaf_names()
        QApplication.clipboard().setText("\n".join(labels))

    def set_as_outgroup(self):
        self.scene().tree.set_outgroup(self.node)
        self.scene().GUI.number_node()
        self.scene().GUI.redraw()

    def toggle_collapse(self):
        self.node.img_style["draw_descendants"] ^= True
        self.scene().GUI.redraw()

    def cut_partition(self):
        self.scene().view.buffer_node = self.node
        self.node.detach()
        self.scene().GUI.redraw()

    def copy_partition(self):
        self.scene().view.buffer_node = self.node.copy('deepcopy')

    def paste_partition(self):
        if self.scene().view.buffer_node:
            self.node.add_child(self.scene().view.buffer_node)
            self.scene().view.buffer_node= None
            self.scene().GUI.redraw()

    def populate_partition(self):
        n, ok = QInputDialog.getInt(None,"Populate partition","Number of nodes to add:",2,1)
        if ok:
            self.node.populate(n)
            #self.scene().set_style_from(self.scene().tree,self.scene().layout_func)
            self.scene().GUI.redraw()

    def set_start_node(self):
        self.scene().start_node = self.node
        self.scene().GUI.redraw()

    def back_to_parent_node(self):
        self.scene().start_node = self.node.up
        self.scene().GUI.redraw()

    def extract_branch_len(self):
        if not self.node.is_leaf():
            # leaves = self.node.get_leaves()
            children = self.node.get_descendants()
            table_ = [["From", "To", "Distance"]]
            for child_node in children:
                table_.append([self.node.id, child_node.id, self.node.get_distance(child_node)])
            fname = QFileDialog.getSaveFileName(self.scene().view,"Save node distance",
                                                        "node_distance",
                                                        "CSV (*.csv)")
            if fname[0]:
                self.factory.write_csv_file(fname[0], table_, self.scene().view)

    def cal_gui_save(self):
        self.cal_gui_settings.setValue('size', self.calibrate_dialog.size())
        for name, obj in inspect.getmembers(self.calibrate_ui):
            if isinstance(obj, QCheckBox):
                state = obj.isChecked()
                self.cal_gui_settings.setValue(name, state)
            elif isinstance(obj, QRadioButton):
                state = obj.isChecked()
                self.cal_gui_settings.setValue(name, state)
            elif isinstance(obj,QSpinBox):
                int_ = obj.value()
                self.cal_gui_settings.setValue(name, int_)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.cal_gui_settings.setValue(name, float_)
            elif isinstance(obj, QTabWidget):
                index = obj.currentIndex()
                self.cal_gui_settings.setValue(name, index)

    def cal_gui_restore(self):
        self.calibrate_dialog.resize(self.cal_gui_settings.value('size', QSize(1150, 750)))
        self.factory.centerWindow(self.calibrate_dialog)
        for name, obj in inspect.getmembers(self.calibrate_ui):
            if isinstance(obj, QSpinBox):
                ini_int_ = obj.value()
                int_ = self.cal_gui_settings.value(name, ini_int_)
                obj.setValue(int(int_))
            elif isinstance(obj, QDoubleSpinBox):
                ini_float_ = obj.value()
                float_ = self.cal_gui_settings.value(name, ini_float_)
                obj.setValue(float(float_))
            elif isinstance(obj, QRadioButton):
                value = self.cal_gui_settings.value(
                    name, "true")  # get stored value from registry
                obj.setChecked(
                    self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QCheckBox):
                value = self.cal_gui_settings.value(
                    name, "no setting")  # get stored value from registry
                if value != "no setting":
                    obj.setChecked(
                        self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QTabWidget):
                index = self.cal_gui_settings.value(name, 0)
                obj.setCurrentIndex(int(index))

    def judge_system(self):
        if platform.system().lower() == "windows":
            QMessageBox.information(self.calibrate_dialog, "MDGUI",
                                    "Pyr8s doesn't allow 'CALIBRATE'! "
                                         "Please choose other modes.")
            self.calibrate_ui.radioButton_7.setChecked(False)

    def add_calibration(self):
        self.calibrate_dialog = QDialog(self.scene().GUI)
        self.calibrate_ui = self.Ui_calibration()
        self.calibrate_ui.setupUi(self.calibrate_dialog)
        self.cal_gui_settings = QSettings(
            self.thisPath + '/settings/cal_gui_settings.ini', QSettings.IniFormat)
        self.cal_gui_settings.setFallbacksEnabled(False)
        self.calibrate_ui.radioButton_7.clicked.connect(self.judge_system)
        self.calibrate_ui.pushButton.clicked.connect(lambda : [self.calibrate_dialog.close(),
                                                               self.check_radiobutton_action()])
        self.calibrate_ui.pushButton_2.clicked.connect(self.calibrate_dialog.close)
        self.cal_gui_restore()
        self.calibrate_dialog.finished.connect(self.cal_gui_save)
        self.calibrate_dialog.setWindowFlags(
            self.calibrate_dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.calibrate_dialog.show()

    def check_radiobutton_action(self):
        dict_radiobutton = {"modeFirst": self.calibrate_ui.radioButton.isChecked(),
                            "modeSecond": self.calibrate_ui.radioButton_2.isChecked(),
                            "modeThird": self.calibrate_ui.radioButton_3.isChecked(),
                            "modeForth": self.calibrate_ui.radioButton_4.isChecked(),
                            "modeFifth": self.calibrate_ui.radioButton_5.isChecked(),
                            "modeSixth": self.calibrate_ui.radioButton_6.isChecked(),
                            "r8sFirst": self.calibrate_ui.radioButton_7.isChecked(),
                            "r8sSecond": self.calibrate_ui.radioButton_8.isChecked(),
                            "r8sThird": self.calibrate_ui.radioButton_9.isChecked(),
                            "r8sForth": self.calibrate_ui.radioButton_10.isChecked(),
                            "rootFirst": self.calibrate_ui.radioButton_14.isChecked(),
                            "rootSecond": self.calibrate_ui.radioButton_12.isChecked(),
                            "rootThird": self.calibrate_ui.radioButton_15.isChecked(),
                            }
        self.add_calibration_to_node(**dict_radiobutton)

    def add_calibration_to_node(self,
                                modeFirst=None,
                                modeSecond=None,
                                modeThird=None,
                                modeForth=None,
                                modeFifth=None,
                                modeSixth=None,
                                r8sFirst=None,
                                r8sSecond=None,
                                r8sThird=None,
                                r8sForth=None,
                                rootFirst=None,
                                rootSecond=None,
                                rootThird=None,
                                ):
        # 删除已有的标记
        dict_faces = getattr(self.node.faces, "branch-top")
        dict_faces.clear()
        if self.calibrate_ui.tabWidget.tabText(self.calibrate_ui.tabWidget.currentIndex()) == "MCMCtree":
            if modeFirst:
                tl = "{:.4f}".format(self.calibrate_ui.doubleSpinBox.value())
                tu = "{:.4f}".format(self.calibrate_ui.doubleSpinBox_2.value())
                pl = "{:.3f}".format(self.calibrate_ui.doubleSpinBox_3.value())
                pu = "{:.3f}".format(self.calibrate_ui.doubleSpinBox_4.value())
                self.node.name = f"'B({tl},{tu},{pl},{pu})'"
                self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
            elif modeSecond:
                tl = "{:.4f}".format(self.calibrate_ui.doubleSpinBox_5.value())
                p = "{:.1f}".format(self.calibrate_ui.doubleSpinBox_6.value())
                c = "{:.1f}".format(self.calibrate_ui.doubleSpinBox_7.value())
                pl = "{:.3f}".format(self.calibrate_ui.doubleSpinBox_8.value())
                self.node.name = f"'L({tl},{p},{c},{pl})'"
                self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
            elif modeThird:
                tu = "{:.4f}".format(self.calibrate_ui.doubleSpinBox_9.value())
                pr = "{:.3f}".format(self.calibrate_ui.doubleSpinBox_10.value())
                self.node.name = f"'U({tu},{pr})'"
                self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
            elif modeForth:
                alpha = format(int(self.calibrate_ui.spinBox.value()))
                beta = format(int(self.calibrate_ui.spinBox_2.value()))
                self.node.name = f"'G({alpha},{beta})'"
                self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
            elif modeFifth:
                loc1 = format(int(self.calibrate_ui.spinBox_3.value()))
                scal1 = "{:.2f}".format(self.calibrate_ui.doubleSpinBox_21.value())
                shp1 = format(int(self.calibrate_ui.spinBox_4.value()))
                self.node.name = f"'SN({loc1},{scal1},{shp1})'"
                self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
            elif modeSixth:
                loc2 = format(int(self.calibrate_ui.spinBox_9.value()))
                scal2 = "{:.2f}".format(self.calibrate_ui.doubleSpinBox_22.value())
                shp2 = format(int(self.calibrate_ui.spinBox_10.value()))
                df = "{:.2f}".format(self.calibrate_ui.doubleSpinBox_23.value())
                self.node.name = f"'ST({loc2},{scal2},{shp2},{df})'"
                self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
        elif self.calibrate_ui.tabWidget.tabText(self.calibrate_ui.tabWidget.currentIndex()) == "r8s":
            if r8sFirst:
                ca_age = self.calibrate_ui.doubleSpinBox_27.value()
                self.node.name = f"cal[{ca_age}]"
                self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
            elif r8sSecond:
                min_age =  self.calibrate_ui.doubleSpinBox_28.value() if self.calibrate_ui.checkBox.isChecked() else ""
                max_age =  self.calibrate_ui.doubleSpinBox_29.value() if self.calibrate_ui.checkBox_2.isChecked() else ""
                self.node.name = f"con[{min_age}~{max_age}]"
                self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
            elif r8sThird:
                fix_age = self.calibrate_ui.doubleSpinBox_30.value()
                self.node.name = f"fix[{fix_age}]"
                self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
            elif r8sForth:
                unf_age = self.calibrate_ui.doubleSpinBox_31.value()
                self.node.name = f"unfix[{unf_age}]"
                self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
        elif self.calibrate_ui.tabWidget.tabText(self.calibrate_ui.tabWidget.currentIndex()) == "MCMCtree root node":
            root_node = self.scene().tree.get_tree_root()
            if rootFirst:
                minimum = "{:.4f}".format(self.calibrate_ui.doubleSpinBox_13.value())
                maximum = "{:.4f}".format(self.calibrate_ui.doubleSpinBox_15.value())
                pl = "{:.3f}".format(self.calibrate_ui.doubleSpinBox_12.value())
                pu = "{:.3f}".format(self.calibrate_ui.doubleSpinBox_16.value())
                root_node.name = f"'B({minimum},{maximum},{pl},{pu})'"
                root_node.add_face(TextFace(root_node.name), column=0, position="branch-top")
            elif rootSecond:
                lower = "{:.4f}".format(self.calibrate_ui.doubleSpinBox_11.value())
                upper = "{:.4f}".format(self.calibrate_ui.doubleSpinBox_14.value())
                root_node.name = f"'>{lower}<{upper}'"
                root_node.add_face(TextFace(root_node.name), column=0, position="branch-top")
            elif rootThird:
                maxBound = "{:.4f}".format(self.calibrate_ui.doubleSpinBox_19.value())
                root_node.name = f"'<{maxBound}'"
                root_node.add_face(TextFace(root_node.name), column=0, position="branch-top")
        self.scene().GUI.redraw()
        # self.calibrate_dialog.close()

    def rm_calibration(self):
        self.node.name = ""
        # dict_faces = getattr(self.node.faces, "branch-top")
        setattr(self.node.faces, "branch-top", {})
        self.scene().GUI.redraw()
        # self.node.add_face(TextFace(""), column=0, position = "branch-top")

    def unroot_tree(self):
        self.scene().tree.unroot()
        self.scene().GUI.redraw()