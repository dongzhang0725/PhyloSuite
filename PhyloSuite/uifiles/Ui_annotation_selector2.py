# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\works\ZD\phylosuite\PhyloSuite_gitee\PhyloSuite\uifiles\annotation_selector2.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_annotation_selector(object):
    def setupUi(self, annotation_selector):
        annotation_selector.setObjectName("annotation_selector")
        annotation_selector.resize(298, 107)
        self.verticalLayout = QtWidgets.QVBoxLayout(annotation_selector)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(annotation_selector)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.comboBox = QtWidgets.QComboBox(annotation_selector)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.verticalLayout.addWidget(self.comboBox)
        self.pushButton = QtWidgets.QPushButton(annotation_selector)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)

        self.retranslateUi(annotation_selector)
        QtCore.QMetaObject.connectSlotsByName(annotation_selector)

    def retranslateUi(self, annotation_selector):
        _translate = QtCore.QCoreApplication.translate
        annotation_selector.setWindowTitle(_translate("annotation_selector", "Annotation selector"))
        self.label.setText(_translate("annotation_selector", "Select an annotation type:"))
        self.comboBox.setItemText(0, _translate("annotation_selector", "Auto show taxonomy"))
        self.comboBox.setItemText(1, _translate("annotation_selector", "Replace leaf name"))
        self.comboBox.setItemText(2, _translate("annotation_selector", "Color strip"))
        self.comboBox.setItemText(3, _translate("annotation_selector", "Text"))
        self.pushButton.setText(_translate("annotation_selector", "Create"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    annotation_selector = QtWidgets.QDialog()
    ui = Ui_annotation_selector()
    ui.setupUi(annotation_selector)
    annotation_selector.show()
    sys.exit(app.exec_())

