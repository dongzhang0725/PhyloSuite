# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'F:\Work\python\bioinfo_excercise\PhyloSuite\codes\PhyloSuite\uifiles\compareTable.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_compareTable(object):
    def setupUi(self, compareTable):
        compareTable.setObjectName("compareTable")
        compareTable.resize(558, 416)
        compareTable.setSizeGripEnabled(True)
        self.gridLayout_3 = QtWidgets.QGridLayout(compareTable)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.groupBox_4 = QtWidgets.QGroupBox(compareTable)
        self.groupBox_4.setObjectName("groupBox_4")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_4)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_4 = QtWidgets.QLabel(self.groupBox_4)
        self.label_4.setObjectName("label_4")
        self.verticalLayout.addWidget(self.label_4)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.gridLayout_2.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.listWidget = QtWidgets.QListWidget(self.groupBox_4)
        self.listWidget.setAcceptDrops(True)
        self.listWidget.setTabKeyNavigation(True)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setDragDropOverwriteMode(False)
        self.listWidget.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.listWidget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.listWidget.setAlternatingRowColors(True)
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.listWidget.setSelectionRectVisible(False)
        self.listWidget.setObjectName("listWidget")
        self.gridLayout_2.addWidget(self.listWidget, 0, 1, 1, 1)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.pushButton_3 = QtWidgets.QPushButton(self.groupBox_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton_3.sizePolicy().hasHeightForWidth())
        self.pushButton_3.setSizePolicy(sizePolicy)
        self.pushButton_3.setMinimumSize(QtCore.QSize(30, 30))
        self.pushButton_3.setMaximumSize(QtCore.QSize(30, 30))
        self.pushButton_3.setStyleSheet("")
        self.pushButton_3.setText("")
        self.pushButton_3.setObjectName("pushButton_3")
        self.verticalLayout_2.addWidget(self.pushButton_3)
        self.toolButton_T = QtWidgets.QToolButton(self.groupBox_4)
        self.toolButton_T.setMinimumSize(QtCore.QSize(30, 30))
        self.toolButton_T.setMaximumSize(QtCore.QSize(30, 30))
        self.toolButton_T.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/picture/resourses/delete.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.toolButton_T.setIcon(icon)
        self.toolButton_T.setIconSize(QtCore.QSize(26, 26))
        self.toolButton_T.setAutoRaise(True)
        self.toolButton_T.setObjectName("toolButton_T")
        self.verticalLayout_2.addWidget(self.toolButton_T)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem1)
        self.gridLayout_2.addLayout(self.verticalLayout_2, 0, 2, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_14 = QtWidgets.QLabel(self.groupBox_4)
        self.label_14.setOpenExternalLinks(True)
        self.label_14.setObjectName("label_14")
        self.horizontalLayout.addWidget(self.label_14)
        spacerItem2 = QtWidgets.QSpacerItem(135, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.label_3 = QtWidgets.QLabel(self.groupBox_4)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.label_2 = ClickedLableGif(self.groupBox_4)
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.gridLayout_2.addLayout(self.horizontalLayout, 1, 0, 1, 3)
        self.gridLayout_3.addWidget(self.groupBox_4, 0, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(compareTable)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.spinBox = QtWidgets.QSpinBox(self.groupBox)
        self.spinBox.setProperty("value", 2)
        self.spinBox.setObjectName("spinBox")
        self.gridLayout.addWidget(self.spinBox, 2, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.checkBox = QtWidgets.QCheckBox(self.groupBox)
        self.checkBox.setObjectName("checkBox")
        self.gridLayout.addWidget(self.checkBox, 1, 0, 1, 2)
        self.gridLayout_3.addWidget(self.groupBox, 1, 0, 1, 1)
        self.groupBox_3 = QtWidgets.QGroupBox(compareTable)
        self.groupBox_3.setObjectName("groupBox_3")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.groupBox_3)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.pushButton = ArrowPushButton(self.groupBox_3)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/picture/resourses/if_start_60207.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon1)
        self.pushButton.setObjectName("pushButton")
        self.gridLayout_5.addWidget(self.pushButton, 0, 0, 1, 1)
        self.pushButton_2 = QtWidgets.QPushButton(self.groupBox_3)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/picture/resourses/if_Delete_1493279.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton_2.setIcon(icon2)
        self.pushButton_2.setObjectName("pushButton_2")
        self.gridLayout_5.addWidget(self.pushButton_2, 0, 1, 1, 1)
        self.gridLayout_5.setColumnStretch(0, 1)
        self.gridLayout_5.setColumnStretch(1, 1)
        self.gridLayout_3.addWidget(self.groupBox_3, 2, 0, 1, 1)
        self.groupBox_2 = QtWidgets.QGroupBox(compareTable)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.progressBar = QtWidgets.QProgressBar(self.groupBox_2)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.gridLayout_4.addWidget(self.progressBar, 0, 0, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox_2, 3, 0, 1, 1)

        self.retranslateUi(compareTable)
        QtCore.QMetaObject.connectSlotsByName(compareTable)

    def retranslateUi(self, compareTable):
        _translate = QtCore.QCoreApplication.translate
        compareTable.setWindowTitle(_translate("compareTable", "Compare table"))
        self.groupBox_4.setTitle(_translate("compareTable", "Input"))
        self.label_4.setText(_translate("compareTable", "Tables:"))
        self.listWidget.setToolTip(_translate("compareTable", "try to drag to reorder"))
        self.toolButton_T.setShortcut(_translate("compareTable", "Del"))
        self.label_14.setText(_translate("compareTable", "<html><head/><body><p>Try to drag <span style=\" font-weight:600; color:#ff0105;\">two or more</span> tables (<span style=\" font-weight:600; color:#ff0026;\">.csv</span>) and drop here</p></body></html>"))
        self.label_3.setText(_translate("compareTable", "Demo:"))
        self.label_2.setToolTip(_translate("compareTable", "Brief example"))
        self.groupBox.setTitle(_translate("compareTable", "Parameters"))
        self.label.setText(_translate("compareTable", "Number of header rows (skip comparison):"))
        self.checkBox.setText(_translate("compareTable", "Calculate pairwise similarity (for organization table only)"))
        self.groupBox_3.setTitle(_translate("compareTable", "Run"))
        self.pushButton.setText(_translate("compareTable", "Start"))
        self.pushButton_2.setText(_translate("compareTable", "Cancel"))
        self.groupBox_2.setTitle(_translate("compareTable", "Progress"))

from src.CustomWidget import ArrowPushButton, ClickedLableGif
from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    compareTable = QtWidgets.QDialog()
    ui = Ui_compareTable()
    ui.setupUi(compareTable)
    compareTable.show()
    sys.exit(app.exec_())
