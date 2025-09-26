
import re
import shutil

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from ete3 import NCBITaxa
import os

from uifiles.Ui_NCBI_db import Ui_NCBI_DB


class LG_NCBIdb(QDialog, Ui_NCBI_DB, object):
    downloadSig = pyqtSignal()
    closeSig = pyqtSignal(str, str)

    def __init__(self, db_file=None, db_path=None, parent=None, thisPath=None):
        super(LG_NCBIdb, self).__init__(parent)
        self.parent = parent
        self.db_file = db_file
        self.db_path = db_path
        os.makedirs(self.db_path, exist_ok=True)
        self.thisPath = thisPath
        self.setupUi(self)
        # 开始装载样式表
        qss_file = self.thisPath + os.sep + 'style.qss'
        if os.path.exists(qss_file) and os.access(qss_file, os.R_OK) and os.access(qss_file, os.W_OK):
            with open(qss_file, encoding="utf-8", errors='ignore') as f:
                qss_content = f.read()
            self.setStyleSheet(qss_content)
        self.pushButton.setFocus()
        self.lineEdit.installEventFilter(self)
        # self.label_4.linkActivated.connect(self.exe_link)

    @pyqtSlot()
    def on_toolButton_3_clicked(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Input File", filter="*;;")
        if fileName[0]:
            if os.path.isfile(fileName[0]):
                self.lineEdit.setText(fileName[0])
            else:
                QMessageBox.critical(
                    self,
                    "Settings",
                        "<p style='line-height:25px; height:25px'>Please specify the database file!</p>")

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
            "Please Wait", "Configuring...", parent=self, busy=True)
        self.progressDialog.show()
        self.worker = WorkThread(lambda : [shutil.copy(path, self.db_path),
                                           NCBITaxa(dbfile=self.db_file,
                                                   taxdump_file=path,
                                                   taxdump_path=self.db_path)],
                                 parent=self)
        self.progressDialog.canceled.connect(lambda : [self.worker.stopWork(),
                                                       self.progressDialog.close()])
        self.worker.finished.connect(lambda : [self.progressDialog.close(),
                                               self.close()])
        self.worker.start()

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        cancel
        """
        self.close()

    @pyqtSlot()
    def on_pushButton_5_clicked(self):
        """
        download
        """
        from src.factory import Factory, WorkThread
        self.factory = Factory()
        self.progressDialog = self.factory.myProgressDialog(
            "Please Wait", "Downloading...", parent=self, busy=True)
        self.progressDialog.show()
        self.worker = WorkThread(lambda : NCBITaxa(dbfile=self.db_file,
                                                   taxdump_file=None,
                                                   taxdump_path=self.db_path,
                                                   update=True),
                                 parent=self)
        self.progressDialog.canceled.connect(lambda : [self.worker.stopWork(),
                                                       self.progressDialog.close()])
        self.worker.finished.connect(lambda : [self.progressDialog.close(),
                                               self.close()])
        self.worker.start()

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
        return super(LG_NCBIdb, self).eventFilter(obj, event)  # 0

