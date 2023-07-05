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
from functools import partial

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog
from ete3 import TextFace
from six.moves import range

from src.factory import Factory
from .qt import Qt, QDialog, QMenu, QCursor, QInputDialog
from .svg_colors import random_color
from . import  _show_newick
from ..evol import EvolTree

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
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptHoverEvents(True)
        self.factory = Factory()

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

    def add_calibration(self):
        self.calibrate_dialog = QDialog(self.scene().GUI)
        self.calibrate_dialog.resize(570, 290)
        self.gridLayout = QtWidgets.QGridLayout(self.calibrate_dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.radioButton = QtWidgets.QRadioButton("Bound only", self.calibrate_dialog)
        self.radioButton.setChecked(True)
        self.radioButton.setObjectName("radioButton")
        self.gridLayout.addWidget(self.radioButton, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_1 = QtWidgets.QLabel(">", self.calibrate_dialog)
        self.label_1.setObjectName("label_1")
        self.horizontalLayout_2.addWidget(self.label_1)
        self.doubleSpinBox_1 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_1.setSingleStep(0.01)
        self.doubleSpinBox_1.setObjectName("doubleSpinBox_1")
        self.horizontalLayout_2.addWidget(self.doubleSpinBox_1)
        self.label_2 = QtWidgets.QLabel("100MYA", self.calibrate_dialog)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.line_13 = QtWidgets.QFrame(self.calibrate_dialog)
        self.line_13.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_13.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_13.setObjectName("line_13")
        self.horizontalLayout_2.addWidget(self.line_13)
        self.label_3 = QtWidgets.QLabel("<", self.calibrate_dialog)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.doubleSpinBox_2 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_2.setSingleStep(0.01)
        self.doubleSpinBox_2.setObjectName("doubleSpinBox_2")
        self.horizontalLayout_2.addWidget(self.doubleSpinBox_2)
        self.label_4 = QtWidgets.QLabel("100MYA", self.calibrate_dialog)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_2.addWidget(self.label_4)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 1, 1, 3)
        self.line_14 = QtWidgets.QFrame(self.calibrate_dialog)
        self.line_14.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_14.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_14.setObjectName("line_14")
        self.gridLayout.addWidget(self.line_14, 1, 0, 1, 4)
        self.radioButton_2 = QtWidgets.QRadioButton("params-bound", self.calibrate_dialog)
        self.radioButton_2.setObjectName("radioButton_2")
        self.gridLayout.addWidget(self.radioButton_2, 2, 0, 1, 1)
        self.gridLayout_14 = QtWidgets.QGridLayout()
        self.gridLayout_14.setObjectName("gridLayout_14")
        self.label_14 = QtWidgets.QLabel("B", self.calibrate_dialog)
        self.label_14.setObjectName("label_14")
        self.gridLayout_14.addWidget(self.label_14, 0, 0, 1, 1)
        self.doubleSpinBox_3 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_3.setSingleStep(0.01)
        self.doubleSpinBox_3.setObjectName("doubleSpinBox_3")
        self.gridLayout_14.addWidget(self.doubleSpinBox_3, 0, 1, 1, 1)
        self.label_15 = QtWidgets.QLabel("100MYA", self.calibrate_dialog)
        self.label_15.setObjectName("label_15")
        self.gridLayout_14.addWidget(self.label_15, 0, 2, 1, 1)
        self.label_18 = QtWidgets.QLabel("pL:", self.calibrate_dialog)
        self.label_18.setObjectName("label_18")
        self.gridLayout_14.addWidget(self.label_18, 1, 0, 1, 1)
        self.doubleSpinBox_5 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_5.setDecimals(3)
        self.doubleSpinBox_5.setSingleStep(0.001)
        self.doubleSpinBox_5.setProperty("value", 0.025)
        self.doubleSpinBox_5.setObjectName("doubleSpinBox_5")
        self.gridLayout_14.addWidget(self.doubleSpinBox_5, 1, 1, 1, 1)
        self.label_19 = QtWidgets.QLabel(self.calibrate_dialog)
        self.label_19.setText("")
        self.label_19.setObjectName("label_19")
        self.gridLayout_14.addWidget(self.label_19, 1, 2, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_14, 2, 1, 1, 1)
        self.line_17 = QtWidgets.QFrame(self.calibrate_dialog)
        self.line_17.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_17.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_17.setObjectName("line_17")
        self.gridLayout.addWidget(self.line_17, 2, 2, 1, 1)
        self.gridLayout_15 = QtWidgets.QGridLayout()
        self.gridLayout_15.setObjectName("gridLayout_15")
        self.label_16 = QtWidgets.QLabel(self.calibrate_dialog)
        self.label_16.setText("")
        self.label_16.setObjectName("label_16")
        self.gridLayout_15.addWidget(self.label_16, 0, 0, 1, 1)
        self.doubleSpinBox_4 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_4.setSingleStep(0.01)
        self.doubleSpinBox_4.setObjectName("doubleSpinBox_4")
        self.gridLayout_15.addWidget(self.doubleSpinBox_4, 0, 1, 1, 1)
        self.label_17 = QtWidgets.QLabel("100MYA", self.calibrate_dialog)
        self.label_17.setObjectName("label_17")
        self.gridLayout_15.addWidget(self.label_17, 0, 2, 1, 1)
        self.label_20 = QtWidgets.QLabel("pU:", self.calibrate_dialog)
        self.label_20.setObjectName("label_20")
        self.gridLayout_15.addWidget(self.label_20, 1, 0, 1, 1)
        self.doubleSpinBox_6 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_6.setDecimals(3)
        self.doubleSpinBox_6.setSingleStep(0.001)
        self.doubleSpinBox_6.setProperty("value", 0.025)
        self.doubleSpinBox_6.setObjectName("doubleSpinBox_6")
        self.gridLayout_15.addWidget(self.doubleSpinBox_6, 1, 1, 1, 1)
        self.label_21 = QtWidgets.QLabel(self.calibrate_dialog)
        self.label_21.setText("")
        self.label_21.setObjectName("label_21")
        self.gridLayout_15.addWidget(self.label_21, 1, 2, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_15, 2, 3, 1, 1)
        self.line_16 = QtWidgets.QFrame(self.calibrate_dialog)
        self.line_16.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_16.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_16.setObjectName("line_16")
        self.gridLayout.addWidget(self.line_16, 3, 0, 1, 4)
        self.radioButton_3 = QtWidgets.QRadioButton("Minimum only", self.calibrate_dialog)
        self.radioButton_3.setObjectName("radioButton_3")
        self.gridLayout.addWidget(self.radioButton_3, 4, 0, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.label_5 = QtWidgets.QLabel("L", self.calibrate_dialog)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_9.addWidget(self.label_5)
        self.doubleSpinBox_7 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_7.setSingleStep(0.01)
        self.doubleSpinBox_7.setObjectName("doubleSpinBox_7")
        self.horizontalLayout_9.addWidget(self.doubleSpinBox_7)
        self.label_6 = QtWidgets.QLabel("100MYA", self.calibrate_dialog)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_9.addWidget(self.label_6)
        self.verticalLayout.addLayout(self.horizontalLayout_9)
        self.gridLayout_12 = QtWidgets.QGridLayout()
        self.gridLayout_12.setObjectName("gridLayout_12")
        self.label_11 = QtWidgets.QLabel("pL:", self.calibrate_dialog)
        self.label_11.setObjectName("label_11")
        self.gridLayout_12.addWidget(self.label_11, 0, 4, 1, 1)
        self.label_10 = QtWidgets.QLabel("c:", self.calibrate_dialog)
        self.label_10.setObjectName("label_10")
        self.gridLayout_12.addWidget(self.label_10, 0, 2, 1, 1)
        self.doubleSpinBox_8 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_8.setSingleStep(0.01)
        self.doubleSpinBox_8.setProperty("value", 0.1)
        self.doubleSpinBox_8.setObjectName("doubleSpinBox_8")
        self.gridLayout_12.addWidget(self.doubleSpinBox_8, 0, 1, 1, 1)
        self.doubleSpinBox_10 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_10.setDecimals(3)
        self.doubleSpinBox_10.setSingleStep(0.001)
        self.doubleSpinBox_10.setStepType(QtWidgets.QAbstractSpinBox.DefaultStepType)
        self.doubleSpinBox_10.setProperty("value", 0.025)
        self.doubleSpinBox_10.setObjectName("doubleSpinBox_10")
        self.gridLayout_12.addWidget(self.doubleSpinBox_10, 0, 5, 1, 1)
        self.doubleSpinBox_9 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_9.setSingleStep(0.01)
        self.doubleSpinBox_9.setProperty("value", 0.5)
        self.doubleSpinBox_9.setObjectName("doubleSpinBox_9")
        self.gridLayout_12.addWidget(self.doubleSpinBox_9, 0, 3, 1, 1)
        self.label_9 = QtWidgets.QLabel("p:", self.calibrate_dialog)
        self.label_9.setObjectName("label_9")
        self.gridLayout_12.addWidget(self.label_9, 0, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_12)
        self.gridLayout.addLayout(self.verticalLayout, 4, 1, 1, 3)
        self.line_18 = QtWidgets.QFrame(self.calibrate_dialog)
        self.line_18.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_18.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_18.setObjectName("line_18")
        self.gridLayout.addWidget(self.line_18, 5, 0, 1, 4)
        self.radioButton_4 = QtWidgets.QRadioButton("Maximum only", self.calibrate_dialog)
        self.radioButton_4.setObjectName("radioButton_4")
        self.gridLayout.addWidget(self.radioButton_4, 6, 0, 1, 1)
        self.gridLayout_13 = QtWidgets.QGridLayout()
        self.gridLayout_13.setObjectName("gridLayout_13")
        self.label_7 = QtWidgets.QLabel("U", self.calibrate_dialog)
        self.label_7.setObjectName("label_7")
        self.gridLayout_13.addWidget(self.label_7, 0, 0, 1, 1)
        self.doubleSpinBox_11 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_11.setSingleStep(0.01)
        self.doubleSpinBox_11.setObjectName("doubleSpinBox_11")
        self.gridLayout_13.addWidget(self.doubleSpinBox_11, 0, 1, 1, 1)
        self.label_8 = QtWidgets.QLabel("100MYA", self.calibrate_dialog)
        self.label_8.setObjectName("label_8")
        self.gridLayout_13.addWidget(self.label_8, 0, 2, 1, 1)
        self.label_12 = QtWidgets.QLabel("pR:", self.calibrate_dialog)
        self.label_12.setObjectName("label_12")
        self.gridLayout_13.addWidget(self.label_12, 1, 0, 1, 1)
        self.doubleSpinBox_12 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.doubleSpinBox_12.setDecimals(3)
        self.doubleSpinBox_12.setSingleStep(0.001)
        self.doubleSpinBox_12.setProperty("value", 0.025)
        self.doubleSpinBox_12.setObjectName("doubleSpinBox_12")
        self.gridLayout_13.addWidget(self.doubleSpinBox_12, 1, 1, 1, 1)
        self.label_13 = QtWidgets.QLabel(self.calibrate_dialog)
        self.label_13.setText("")
        self.label_13.setObjectName("label_13")
        self.gridLayout_13.addWidget(self.label_13, 1, 2, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_13, 6, 1, 1, 3)
        self.line_19 = QtWidgets.QFrame(self.calibrate_dialog)
        self.line_19.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_19.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_19.setObjectName("line_19")
        self.gridLayout.addWidget(self.line_19, 7, 0, 1, 4)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton = QtWidgets.QPushButton("OK", self.calibrate_dialog)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton("CANCEL", self.calibrate_dialog)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout.addWidget(self.pushButton_2)
        self.gridLayout.addLayout(self.horizontalLayout, 8, 0, 1, 4)
        self.pushButton.clicked.connect(self.check_radiobutton_action)
        self.pushButton_2.clicked.connect(self.calibrate_dialog.close)
        self.calibrate_dialog.setWindowFlags(
            self.calibrate_dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.calibrate_dialog.show()

    def check_radiobutton_action(self):
        dict_radiobutton = {"modeFirst": self.radioButton.isChecked(),
                            "modeSecond": self.radioButton_2.isChecked(),
                            "modeThird": self.radioButton_3.isChecked(),
                            "modeForth": self.radioButton_4.isChecked()
                            }

        self.add_calibration_to_node(**dict_radiobutton)

    def add_calibration_to_node(self,
                                modeFirst=None,
                                modeSecond=None,
                                modeThird=None,
                                modeForth=None):
        #if .text() == "OK":
        if modeFirst:
            l = self.doubleSpinBox_1.value()
            h = self.doubleSpinBox_2.value()
            self.node.name = f"'>{l}<{h}'"
            self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
        if modeSecond:
            tl = self.doubleSpinBox_3.value()
            tu = self.doubleSpinBox_4.value()
            pl = self.doubleSpinBox_5.value()
            pu = self.doubleSpinBox_6.value()
            self.node.name = f"'B({tl},{tu},{pl},{pu})'"
            self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
        if modeThird:
            tl = self.doubleSpinBox_7.value()
            p = self.doubleSpinBox_8.value()
            c = self.doubleSpinBox_9.value()
            pl = self.doubleSpinBox_10.value()
            self.node.name = f"'L({tl},{p},{c},{pl})'"
            self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
        if modeForth:
            tu = self.doubleSpinBox_11.value()
            pr = self.doubleSpinBox_12.value()
            self.node.name = f"'U({tu},{pr})'"
            self.node.add_face(TextFace(self.node.name), column=0, position="branch-top")
        self.scene().GUI.redraw()
        self.calibrate_dialog.close()

    def rm_calibration(self):
        self.node.name = ""
        dict_faces = getattr(self.node.faces, "branch-top")
        setattr(self.node.faces, "branch-top", {})
        self.scene().GUI.redraw()
        # self.node.add_face(TextFace(""), column=0, position = "branch-top")

    def unroot_tree(self):
        self.scene().tree.unroot()
        self.scene().GUI.redraw()