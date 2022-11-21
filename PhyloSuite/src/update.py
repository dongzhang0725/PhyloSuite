#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import zipfile
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

from src.factory import WorkThread, Factory
import platform


class HttpWindowDownload(QDialog):
    finishSig = pyqtSignal()

    def __init__(self, parent=None, **dict_args):
        super(HttpWindowDownload, self).__init__(parent)
        self.dict_args = dict_args

    def ini_args(self):
        self.url = QUrl(self.dict_args["url"])
        self.exportPath = self.dict_args["downloadPath"]
        # self.totalSize = self.dict_args["totalSize"]
        self.progressSig = self.dict_args["progressSig"]
        self.outFile = QFile(self.exportPath)
        self.httpGetId = 0
        self.httpRequestAborted = False
        self.qnam = QNetworkAccessManager()
        self.qnam.authenticationRequired.connect(
            self.slotAuthenticationRequired)
        self.qnam.sslErrors.connect(self.sslErrors)
        self.downloadFile()

    def startRequest(self, url):
        self.reply = self.qnam.get(QNetworkRequest(url))
        self.reply.finished.connect(self.httpFinished)
        self.reply.readyRead.connect(self.httpReadyRead)
        self.reply.downloadProgress.connect(self.updateDataReadProgress)

    def downloadFile(self):
        fileName = os.path.splitext(os.path.basename(self.exportPath))[0]
        if QFile.exists(fileName):
            try:
                QFile.remove(fileName)
            except:
                pass
        if not self.outFile.open(QIODevice.WriteOnly):
            QSettings.setDefaultFormat(QSettings.IniFormat)
            settings = QSettings()
            country = settings.value("country", "UK")
            url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#7-1-Update-failed-how-to-revert-to-previous-settings-and-plugins" if \
                country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#7-1-Update-failed-how-to-revert-to-previous-settings-and-plugins"
            QMessageBox.information(self, "HTTP",
                                          "Unable to save the file %s: %s."
                                          "See <a href=\"%s\">here</a> for how to update manually." % (fileName, self.outFile.errorString(), url))
            self.outFile = None
            return

        self.httpRequestAborted = False
        self.startRequest(self.url)

    def cancelDownload(self):
        self.httpRequestAborted = True
        self.reply.abort()

    def httpFinished(self):
        if self.httpRequestAborted:
            if self.outFile is not None:
                self.outFile.close()
                self.outFile.remove()
                self.outFile = None
            self.reply.deleteLater()
            self.reply = None
            self.progressSig.emit(0)
            return
        self.outFile.flush()
        self.outFile.close()
        redirectionTarget = self.reply.attribute(QNetworkRequest.RedirectionTargetAttribute)
        if self.reply.error():
            self.outFile.remove()
            QSettings.setDefaultFormat(QSettings.IniFormat)
            settings = QSettings()
            country = settings.value("country", "UK")
            url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#7-1-Update-failed-how-to-revert-to-previous-settings-and-plugins" if \
                country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#7-1-Update-failed-how-to-revert-to-previous-settings-and-plugins"
            QMessageBox.information(self, "HTTP",
                                          "Download failed: %s."
                                          "See <a href=\"%s\">here</a> for how to update manually." % (self.reply.errorString(), url))
        elif redirectionTarget is not None:
            newUrl = self.url.resolved(redirectionTarget)
            ret = QMessageBox.question(self, "HTTP",
                    "Redirect to %s?" % newUrl.toString(),
                    QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.url = newUrl
                self.reply.deleteLater()
                self.reply = None
                self.outFile.open(QIODevice.WriteOnly)
                self.outFile.resize(0)
                self.startRequest(self.url)
                return
        self.reply.deleteLater()
        self.reply = None
        self.outFile = None
        self.finishSig.emit()

    def httpReadyRead(self):
        if self.outFile is not None:
            self.outFile.write(self.reply.readAll())

    def updateDataReadProgress(self, bytesRead, totalBytes):
        if self.httpRequestAborted:
            return

        # maxmum = totalBytes if totalBytes else int(self.totalSize)
        QCoreApplication.processEvents()
        done = 95 * (bytesRead / totalBytes) if totalBytes else 0

        self.progressSig.emit(done)

    def slotAuthenticationRequired(self, authenticator):
        import os
        from PyQt5 import uic

        ui = os.path.join(os.path.dirname(self.exportPath) + os.sep + "uifiles", 'authenticationdialog.ui')
        dlg = uic.loadUi(ui)
        dlg.adjustSize()
        dlg.siteDescription.setText("%s at %s" % (authenticator.realm(), self.url.host()))

        dlg.userEdit.setText(self.url.userName())
        dlg.passwordEdit.setText(self.url.password())

        if dlg.exec_() == QDialog.Accepted:
            authenticator.setUser(dlg.userEdit.text())
            authenticator.setPassword(dlg.passwordEdit.text())

    def sslErrors(self, reply, errors):
        errorString = ", ".join([str(error.errorString()) for error in errors])
        QSettings.setDefaultFormat(QSettings.IniFormat)
        settings = QSettings()
        country = settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#7-1-Update-failed-how-to-revert-to-previous-settings-and-plugins" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#7-1-Update-failed-how-to-revert-to-previous-settings-and-plugins"
        ret = QMessageBox.warning(self, "HTTP",
                                "One or more SSL errors has occurred: %s. "
                                "See <a href=\"%s\">here</a> for how to update manually." % (errorString, url),
                                QMessageBox.Ignore | QMessageBox.Abort)
        if ret == QMessageBox.Ignore:
            self.reply.ignoreSslErrors()

class UpdateAPP(QDialog):
    '''
    1.先下载新的app
    2.然后解压，由于github下载的，解压会自动解压到一个新的文件夹
    3.从解压的文件夹把文件移动到跟文件夹，此时判断一下文件是否存在，如果存在，就重命名.old（主程序每次启动，都会判断是否有.old文件存在，
      如果有就删除；这一步如果无法重命名的话，有可能会造成失败），然后再把文件移动过去（settings和plugins文件夹会跳过）
    4.重新启动程序，然后删除.old文件
    '''
    progressSig = pyqtSignal(int)  # 控制进度条

    def __init__(self, parent=None):
        super(UpdateAPP, self).__init__(parent)
        self.factory = Factory()
        self.rootPath = self.factory.thisPath
        #os.path.dirname(os.path.realpath(__file__))
        # self.totalSize = totalSize if totalSize else "42389760"
        # self.verticalLayout = QVBoxLayout(self)
        # self.setWindowTitle("Update")
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        # # self.setModal(Qt.WindowModal)
        # self.progressBar = PercentProgressBar(self, showSmallCircle=True)
        # self.verticalLayout.addWidget(self.progressBar)
        # self.label = QLabel("<span style='font-weight:600; color:white; font: 35px;'>Downloading...</span>", self)
        # self.verticalLayout.addWidget(self.label)
        # self.progressSig.connect(self.downloadProgress)

    def exec_unzip(self):
        # self.label.setText("<span style='font-weight:600; color:white; font: 35px;'>Unpacking new file</span>")
        self.worker = WorkThread(self.unzipNewApp, parent=self)
        self.worker.start()
        self.worker.finished.connect(self.exec_restart)

    def exec_restart(self):
        # self.label.setText("Update successfully")
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def downloadNewAPP(self):
        url = self.factory.get_update_path()
        self.downloadPath = self.rootPath + os.sep + "update.zip"
        ###qhttp下载
        dict_args = {}
        dict_args["url"] = url
        dict_args["downloadPath"] = self.downloadPath
        # dict_args["totalSize"] = self.totalSize
        dict_args["progressSig"] = self.progressSig
        httpwindow = HttpWindowDownload(parent=self, **dict_args)
        httpwindow.finishSig.connect(self.exec_unzip)
        httpwindow.ini_args()

    def unzipNewApp(self, downloaded_zipfile=None):
        self.downloadPath = downloaded_zipfile if downloaded_zipfile else self.downloadPath
        file_zip = zipfile.ZipFile(self.downloadPath, 'r')
        namelists = file_zip.namelist()
        for num, file in enumerate(namelists):
            path_root = self.rootPath + os.sep + file #os.path.basename(file)
            if os.path.exists(path_root):
                ##如果已经存在的文件夹就替换名字
                if os.path.basename(file) not in ["settings", "plugins"]:
                    ##SRC和插件保留
                    try:
                        ##如果重命名失败，也不能移动文件，这里是可能造成更新失败的地方
                        os.rename(path_root, path_root + ".old")
                    except:
                        pass
            try:
                file_zip.extract(file, self.rootPath)
                # if platform.system().lower() in ["darwin", "linux"]:
                #     os.system("chmod 755 %s"%(self.rootPath + os.sep + file))
            except:
                pass
            if not downloaded_zipfile:
                # 软件更新
                self.progressSig.emit(95 + 5 * ((num+1)/len(namelists)))
        file_zip.close()
        # assign permission
        if platform.system().lower() in ["darwin", "linux"]:
            os.system(f"bash {self.rootPath}{os.sep}assign_permission.sh")
        try:
            os.remove(self.downloadPath)
        except:
            pass

    # def downloadProgress(self, num):
    #     self.progressBar.setValue(num)
    #     QCoreApplication.processEvents()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    updateApp = UpdateAPP()
    updateApp.downloadNewAPP()
    updateApp.show()
    sys.exit(app.exec_())
