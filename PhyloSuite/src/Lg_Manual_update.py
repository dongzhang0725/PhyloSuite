
import re
import shutil

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ete3 import NCBITaxa
import os

from src.update import UpdateAPP
from uifiles.Ui_Manual_update import Ui_Manual_update
from uifiles.Ui_NCBI_db import Ui_NCBI_DB


class LG_Manual_update(QDialog, Ui_Manual_update, object):
    downloadSig = pyqtSignal()
    closeSig = pyqtSignal(str, str)

    def __init__(self, update_path=None, parent=None, thisPath=None):
        super(LG_Manual_update, self).__init__(parent)
        self.parent = parent
        self.thisPath = thisPath
        self.update_path = update_path
        self.setupUi(self)
        self.label_3.setText(re.sub(r'href="[^"]+"',
                                    f'href="{update_path}"',
                                    self.label_3.text()))
        # 开始装载样式表
        # with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
        #     self.qss_file = f.read()
        # self.setStyleSheet(self.qss_file)
        self.qss_file = self.factory.set_qss(self)
        self.pushButton.setFocus()
        self.lineEdit.installEventFilter(self)
        # self.label_4.linkActivated.connect(self.exe_link)

    @pyqtSlot()
    def on_toolButton_3_clicked(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Input update file", filter="*;;")
        if fileName[0]:
            if os.path.isfile(fileName[0]):
                self.lineEdit.setText(fileName[0])
            else:
                QMessageBox.critical(
                    self,
                    "Settings",
                        "<p style='line-height:25px; height:25px'>Please specify the update file!</p>")

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        ok
        """
        from src.factory import Factory, WorkThread
        self.factory = Factory()
        path = self.lineEdit.text()
        if (not path) or (not os.path.exists(path)):
            return
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "Unziping...", parent=self, busy=True)
        self.progressDialog.show()
        self.worker = WorkThread(lambda : UpdateAPP().unzipNewApp(path),
                                 parent=self)
        self.progressDialog.canceled.connect(lambda : [self.worker.stopWork(),
                                                       self.progressDialog.close()])
        self.worker.finished.connect(lambda : [self.progressDialog.close(),
                                               self.query_restart(),
                                               self.close()])
        self.worker.start()

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        cancel
        """
        self.close()

    def query_restart(self):
        reply = QMessageBox.information(
            self, "Settings",
            "<p style='line-height:25px;height:25px'>Unzip finished, "
            "do you want to restart PhyloSuite now?</p>",
            QMessageBox.Ok,
            QMessageBox.Cancel,
        )
        if reply == QMessageBox.Ok:
            UpdateAPP().exec_restart()

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
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
                if files:
                    if len(files) == 1:
                        obj.setText(files[0])
                    else:
                        QMessageBox.warning(
                            self,
                            "Settings",
                            "<p style='line-height:25px; height:25px'>Only one file is validated!</p>")
        # 其他情况会返回系统默认的事件处理方法。
        return super(LG_Manual_update, self).eventFilter(obj, event)  # 0

