# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\works\ZD\phylosuite\uifiles\about.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_about(object):
    def setupUi(self, about):
        about.setObjectName("about")
        about.resize(488, 385)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(about.sizePolicy().hasHeightForWidth())
        about.setSizePolicy(sizePolicy)
        about.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.verticalLayout = QtWidgets.QVBoxLayout(about)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(about)
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(":/picture/resourses/about_fig.png"))
        self.label.setScaledContents(False)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.label_2 = QtWidgets.QLabel(about)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.label_2.setFont(font)
        self.label_2.setOpenExternalLinks(True)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(about)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(about)
        self.buttonBox.accepted.connect(about.accept)
        self.buttonBox.rejected.connect(about.reject)
        QtCore.QMetaObject.connectSlotsByName(about)

    def retranslateUi(self, about):
        _translate = QtCore.QCoreApplication.translate
        about.setWindowTitle(_translate("about", "About PhyloSuite"))
        self.label_2.setText(_translate("about", "<html><head/><body><p align=\"center\"><span style=\" font-size:14pt;\">PhyloSuite</span><span style=\" font-size:14pt; vertical-align:super;\">®</span><span style=\" font-size:14pt;\"> v1.2.3</span></p><p align=\"center\"><span style=\" font-size:14pt;\">Copyright © 2020 Zhang D., Gao F., Wang G. et al.</span></p><p align=\"center\"><span style=\" font-size:14pt;\">Presented by Zhang D., Gao F., Wang G. et al.</span></p><p align=\"center\"><span style=\" font-size:14pt;\">Email: dongzhang0725@gmail.com</span></p><p align=\"center\"><span style=\" font-size:14pt;\">WebSite: </span><a href=\"https://github.com/dongzhang0725/PhyloSuite\"><span style=\" font-size:14pt; text-decoration: underline; color:#0000ff;\">https://github.com/dongzhang0725/PhyloSuite</span></a></p></body></html>"))

from uifiles import myRes_rc

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    about = QtWidgets.QDialog()
    ui = Ui_about()
    ui.setupUi(about)
    about.show()
    sys.exit(app.exec_())

