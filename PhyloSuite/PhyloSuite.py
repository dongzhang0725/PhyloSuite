#!/usr/bin/env python
#-*- coding:utf-8 -*-
import multiprocessing
import os
import platform
import re
import sys
import traceback
from copy import deepcopy

thisPath = os.path.abspath(os.path.dirname(sys.argv[0]))
thisPath = os.path.abspath(os.path.dirname(__file__)) if not os.path.exists(thisPath + os.sep + "style.qss") else thisPath
sys.path.append(thisPath)
# sys.path.append(os.path.abspath(os.path.dirname(__file__))) #不添加的话，setup安装时双击无法运行
# sys.path.append(thisPath + os.sep + "uifiles")
# sys.path.append(thisPath + os.sep + "src")

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from src.Launcher import Launcher
from src.factory import QSingleApplication
from src.main import MyMainWindow

def start():
    app = QSingleApplication(sys.argv)
    if platform.system().lower() == "windows":
        multiprocessing.freeze_support() # windows必须调用这个，不然会出错
    # 异常调试
    import cgitb
    sys.excepthook = cgitb.Hook(1, None, 5, sys.stderr, 'text')
    ##为了存路径到系统
    QApplication.setApplicationName("PhyloSuite_settings")
    QApplication.setOrganizationName("PhyloSuite")
    QSettings.setDefaultFormat(QSettings.IniFormat)
    path_settings = QSettings()
    path_settings.setValue("thisPath", thisPath)
    os.chdir(thisPath)
    with open(thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
        qss_file = f.read()
    dialog = QDialog()
    dialog.setStyleSheet(qss_file)
    # 异常处理
    def handle_exception(exc_type, exc_value, exc_traceback):
        rgx = re.compile(r'PermissionError.+?[\'\"](.+\.csv)[\'\"]')
        if issubclass(exc_type, KeyboardInterrupt):
            return sys.__excepthook__(exc_type, exc_value, exc_traceback)
        exception = str("".join(traceback.format_exception(
            exc_type, exc_value, exc_traceback)))
        print(exception)
        if rgx.search(exception):
            #忽略csv未关闭的报错
            return
        msg = QMessageBox(dialog)
        msg.setIcon(QMessageBox.Critical)
        msg.setText(
            'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> '
            'or send an email with the detailed traceback to dongzhang0725@gmail.com')
        msg.setWindowTitle("Error")
        msg.setDetailedText(exception)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    sys.excepthook = handle_exception
    # 避免重复运行程序
    if app.isRunning():
        QMessageBox.information(
            dialog,
            "PhyloSuite",
            "<p style='line-height:25px; height:25px'>App is running!</p>")
        sys.exit(0)

    # 界面运行选择
    launcher_settings = QSettings(
        thisPath + '/settings/launcher_settings.ini', QSettings.IniFormat)
    launcher_settings.setFallbacksEnabled(False)
    not_exe_lunch = launcher_settings.value("ifLaunch", "false")
    workPlace = launcher_settings.value(
        "workPlace", [thisPath + os.sep + "myWorkPlace"])
    # 删除无效的路径
    workPlace_copy = deepcopy(workPlace)
    for num,i in enumerate(workPlace_copy):
        if not os.path.exists(i):
            workPlace.remove(i)
        else:
            ##替换带.的路径
            if re.search(r"^\.", i):
                workPlace[num] = os.path.abspath(i)
    # 如果workPlace被删干净了
    if not workPlace:
        workPlace = [thisPath + os.sep + "myWorkPlace"]
    # 重新保存下路径
    if len(workPlace) > 15:
        workPlace = workPlace[:15]  # 只保留15个工作区
    launcher_settings.setValue(
        "workPlace", workPlace)
    if not_exe_lunch == "true":
        myMainWindow = MyMainWindow(workPlace)
        myMainWindow.show()
        sys.exit(app.exec_())
    else:
        launcher = Launcher()
        if launcher.exec_() == QDialog.Accepted:
            workPlace = launcher.WorkPlace
            myMainWindow = MyMainWindow(workPlace)
            myMainWindow.show()
            sys.exit(app.exec_())

if __name__ == "__main__":
    start()
