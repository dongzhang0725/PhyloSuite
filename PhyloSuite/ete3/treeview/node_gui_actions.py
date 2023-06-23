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
        self.calibrate_dialog.resize(450, 72)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.calibrate_dialog)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.label_3 = QtWidgets.QLabel(">", self.calibrate_dialog)
        self.horizontalLayout.addWidget(self.label_3)
        self.doubleSpinBox_2 = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.horizontalLayout.addWidget(self.doubleSpinBox_2)
        self.label_4 = QtWidgets.QLabel("100 MYA", self.calibrate_dialog)
        self.horizontalLayout.addWidget(self.label_4)
        self.line = QtWidgets.QFrame(self.calibrate_dialog)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.horizontalLayout.addWidget(self.line)
        self.label_2 = QtWidgets.QLabel("<", self.calibrate_dialog)
        self.horizontalLayout.addWidget(self.label_2)
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(self.calibrate_dialog)
        self.horizontalLayout.addWidget(self.doubleSpinBox)
        self.label = QtWidgets.QLabel("100 MYA", self.calibrate_dialog)
        self.horizontalLayout.addWidget(self.label)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.calibrate_dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)
        self.buttonBox.clicked.connect(self.add_calibration_to_node)
        self.calibrate_dialog.setWindowFlags(
            self.calibrate_dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.calibrate_dialog.show()

    def add_calibration_to_node(self, button):
        if button.text() == "OK":
            l = self.doubleSpinBox_2.value()
            h = self.doubleSpinBox.value()
            self.node.name = f"'>{l}<{h}'"
        self.node.add_face(TextFace(self.node.name), column=0, position = "branch-top")
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