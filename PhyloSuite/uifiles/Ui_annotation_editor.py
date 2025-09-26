# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\works\ZD\phylosuite\PhyloSuite_gitee\PhyloSuite\uifiles\annotation_editor.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_annotation_editor(object):
    def setupUi(self, annotation_editor):
        annotation_editor.setObjectName("annotation_editor")
        annotation_editor.resize(892, 630)
        self.verticalLayout = QtWidgets.QVBoxLayout(annotation_editor)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(annotation_editor)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.tableView = MyTableView(annotation_editor)
        self.tableView.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.tableView.setObjectName("tableView")
        self.verticalLayout.addWidget(self.tableView)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(annotation_editor)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.pushButton = QtWidgets.QPushButton(annotation_editor)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(annotation_editor)
        QtCore.QMetaObject.connectSlotsByName(annotation_editor)

    def retranslateUi(self, annotation_editor):
        _translate = QtCore.QCoreApplication.translate
        annotation_editor.setWindowTitle(_translate("annotation_editor", "Annotation editor"))
        self.label_2.setText(_translate("annotation_editor", "Pie chart:"))
        self.label.setText(_translate("annotation_editor", "Double click to modify data"))
        self.pushButton.setText(_translate("annotation_editor", "Create"))

from src.CustomWidget2 import MyTableView

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    annotation_editor = QtWidgets.QDialog()
    ui = Ui_annotation_editor()
    ui.setupUi(annotation_editor)
    annotation_editor.show()
    sys.exit(app.exec_())

