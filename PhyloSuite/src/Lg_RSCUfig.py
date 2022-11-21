#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.Lg_settings import Setting
from src.factory import Factory, WorkThread
from uifiles.Ui_RSCUfig import Ui_RSCUfig
import inspect
import os
import sys
import traceback
from collections import OrderedDict
import subprocess
import re
import platform
try:
    import plotly
    import pandas as pd
    import plotly.express as px
    from plotly.subplots import make_subplots
except:
    pass

class DrawRSCUfig(QDialog, Ui_RSCUfig, object):
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    warning_signal = pyqtSignal(str)
    progressSig = pyqtSignal(int)  # 控制进度条
    startButtonStatusSig = pyqtSignal(list)

    def __init__(
            self,
            autoInputs=None,
            workPath=None,
            focusSig=None,
            # RscriptPath=None,
            parent=None):
        super(DrawRSCUfig, self).__init__(parent)
        self.parent = parent
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.autoInputs = autoInputs
        self.setupUi(self)
        # 保存设置
        self.DrawRSCUfig_settings = QSettings(
            self.thisPath +
            '/settings/DrawRSCUfig_settings.ini',
            QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.DrawRSCUfig_settings.setFallbacksEnabled(False)
        # 开始装载样式表
        with open(self.thisPath + os.sep + 'style.qss', encoding="utf-8", errors='ignore') as f:
            self.qss_file = f.read()
        self.setStyleSheet(self.qss_file)
        # 恢复用户的设置
        self.guiRestore()
        self.autoParameters(len(self.autoInputs))
        self.exception_signal.connect(self.popupException)
        self.warning_signal.connect(self.popupWarning)
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.progressSig.connect(self.runProgress)
        self.listWidget_3.installEventFilter(self)
        self.tabWidget.setCurrentIndex(0)
        # 给开始按钮添加菜单
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        self.work_action = QAction(QIcon(":/picture/resourses/work.png"), "", menu)
        self.work_action.triggered.connect(lambda: self.factory.swithWorkPath(self.work_action, parent=self))
        self.dir_action = QAction(QIcon(":/picture/resourses/folder.png"), "Output Dir: ", menu)
        self.dir_action.triggered.connect(lambda: self.factory.set_direct_dir(self.dir_action, self))
        menu.addAction(self.work_action)
        menu.addAction(self.dir_action)
        self.pushButton.toolButton.setMenu(menu)
        self.pushButton.toolButton.menu().installEventFilter(self)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下
        # 信号槽
        self.tabWidget.currentChanged.connect(self.judgeRinstallation)
        self.lineEdit.clicked.connect(self.setFont)
        self.lineEdit_2.clicked.connect(self.setFont)
        ## brief demo
        country = self.factory.path_settings.value("country", "UK")
        url = "http://phylosuite.jushengwu.com/dongzhang0725.github.io/documentation/#5-14-3-1-Brief-example" if \
            country == "China" else "https://dongzhang0725.github.io/dongzhang0725.github.io/documentation/#5-14-3-1-Brief-example"
        self.label_2.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        open files
        """
        fileNames = QFileDialog.getOpenFileNames(
            self, "Input Files", filter="CSV Format(*.csv);;")
        if fileNames[0]:
            dict_inputs = OrderedDict()
            for i in fileNames[0]:
                dict_inputs[i] = os.path.splitext(os.path.basename(i))[0]
            self.inputListWidget_3(dict_inputs)

    @pyqtSlot()
    def on_toolButton_T_clicked(self):
        '''
        delete
        '''
        listItems = self.listWidget_3.selectedItems()
        if not listItems:
            return
        for item in listItems:
            self.listWidget_3.takeItem(self.listWidget_3.row(item))
        self.autoParameters(self.listWidget_3.count())

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        '''
        cancel
        '''
        # ctypes.windll.kernel32.TerminateThread(  # @UndefinedVariable
        #     self.worker.handle, 0)
        self.close()

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        execute program
        """
        dict_inputs = OrderedDict()
        for i in range(self.listWidget_3.count()):
            dict_inputs[self.listWidget_3.item(i).toolTip()] = self.listWidget_3.item(i).text()
        if dict_inputs:
            # 有数据才执行
            self.dict_args = {}
            self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
            self.exportPath = self.factory.creat_dirs(self.workPath +
                                        os.sep + "RSCUfig_results" + os.sep + self.output_dir_name)
            self.dict_args["exportPath"] = self.exportPath
            self.RSCUpath = os.path.normpath(self.exportPath + os.sep + "RSCU.pdf").replace("\\", "/")
            self.RSCUhtml = os.path.normpath(self.exportPath + os.sep + "RSCU_interactive.html").replace("\\", "/")
            self.dict_args["dict_files_title"] = dict_inputs
            self.dict_args["exception_signal"] = self.exception_signal
            self.dict_args["progressSig"] = self.progressSig
            xItems = [
                self.listWidget_2.item(i).text() for i in range(self.listWidget_2.count())]
            self.dict_args["Order of x-axis"] = xItems
            colorItems = [
                i.text() for i in [self.pushButton_color, self.pushButton_color_2,
                                   self.pushButton_color_3, self.pushButton_color_4,
                                   self.pushButton_color_5, self.pushButton_color_6,
                                   self.pushButton_color_7, self.pushButton_color_8
                                   ]]
            self.dict_args["Color of stacks"] = colorItems
            self.dict_args["Figure height"] = self.spinBox_5.value()
            self.dict_args["Figure width"] = self.spinBox_6.value()
            self.dict_args["height proportion"] = self.doubleSpinBox_2.value()
            self.dict_args["ylim"] = self.doubleSpinBox_3.value()
            self.dict_args["plot_exe"] = self.tabWidget.tabText(self.tabWidget.currentIndex())
            # plotly
            self.dict_args["Figure height plotly"] = self.spinBox_7.value()
            self.dict_args["Figure width plotly"] = self.spinBox_8.value()
            self.dict_args["Figure interval"] = self.doubleSpinBox.value()
            self.dict_args["RSCU offset"] = self.doubleSpinBox_4.value()
            self.dict_args["font family"] = self.lineEdit.text()
            self.dict_args["font size"] = int(self.lineEdit_2.text())
            self.dict_args["bar width"] = self.doubleSpinBox_5.value()
            ok = self.factory.remove_dir(self.exportPath, parent=self)
            if not ok:
                #提醒是否删除旧结果，如果用户取消，就不执行
                return
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()
        else:
            QMessageBox.critical(
                self,
                "Draw RSCU figure",
                "<p style='line-height:25px; height:25px'>Please input files first!</p>")

    def run_command(self):
        try:
            # 清空文件夹，放在这里方便统一报错
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            if self.dict_args["plot_exe"] == "ggplot (R)":
                rscriptPath = self.rscu2fig()
                subprocess.call("%s --vanilla %s"%(self.RscriptPath, rscriptPath), shell=True)
                self.progressSig.emit(100)
                if not os.path.exists(self.RSCUpath):
                    self.warning_signal.emit("No RSCU figure generated! The R packages \"ggplot2\" or \"ggpubr\" may not be installed properly. You may:<br>"
                        "&nbsp;&nbsp;&nbsp;<span style='font-weight:600'>1</span>. Install \"ggplot2\" and \"ggpubr\" manually, restart PhyloSuite and try again<br>"
                        "&nbsp;&nbsp;&nbsp;<span style='font-weight:600'>2</span>. Execute \"rscu_scripts.r\" script: <span style='font-weight:600; color:#ff0000;'>Rscript rscu_scripts.r</span><br>"
                        "&nbsp;&nbsp;&nbsp;<span style='font-weight:600'>3</span>. Copy the content of \"rscu_scripts.r\" and paste it into Rstudio or Rgui to execute")
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton,
                            self.progressBar,
                            "except",
                            self.exportPath,
                            self.qss_file,
                            self])
                else:
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton,
                            self.progressBar,
                            "stop",
                            self.exportPath,
                            self.qss_file,
                            self])
                if os.path.exists(self.exportPath + os.sep + "Rplots.pdf"):
                    os.remove(self.exportPath + os.sep + "Rplots.pdf")
            else:
                self.plotly_rscu()
                self.progressSig.emit(100)
                if not os.path.exists(self.RSCUpath):
                    self.warning_signal.emit(
                        "No RSCU figure generated! The R packages \"ggplot2\" or \"ggpubr\" may not be installed properly. You may:<br>"
                        "&nbsp;&nbsp;&nbsp;<span style='font-weight:600'>1</span>. Install \"ggplot2\" and \"ggpubr\" manually, restart PhyloSuite and try again<br>"
                        "&nbsp;&nbsp;&nbsp;<span style='font-weight:600'>2</span>. Execute \"rscu_scripts.r\" script: <span style='font-weight:600; color:#ff0000;'>Rscript rscu_scripts.r</span><br>"
                        "&nbsp;&nbsp;&nbsp;<span style='font-weight:600'>3</span>. Copy the content of \"rscu_scripts.r\" and paste it into Rstudio or Rgui to execute")
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton,
                            self.progressBar,
                            "except",
                            self.exportPath,
                            self.qss_file,
                            self])
                else:
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton,
                            self.progressBar,
                            "stop",
                            self.exportPath,
                            self.qss_file,
                            self])
            self.focusSig.emit(self.exportPath)
            time_end = datetime.datetime.now()
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                  str(time_end - time_start))
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write("If you use PhyloSuite v1.2.3, please cite:\nZhang, D., F. Gao, I. Jakovlić, H. Zou, J. Zhang, W.X. Li, and G.T. Wang, PhyloSuite: An integrated and scalable desktop platform for streamlined molecular sequence data management and evolutionary phylogenetics studies. Molecular Ecology Resources, 2020. 20(1): p. 348–355. DOI: 10.1111/1755-0998.13096.\n\n" + self.time_used_des)
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.startButtonStatusSig.emit(
                [
                    self.pushButton,
                    self.progressBar,
                    "except",
                    self.exportPath,
                    self.qss_file,
                    self])

    def guiSave(self):
        # Save geometry
        self.DrawRSCUfig_settings.setValue('size', self.size())
        # self.DrawRSCUfig_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QListWidget):
                if name == "listWidget_3":
                    dict_inputs = OrderedDict()
                    for i in range(obj.count()):
                        dict_inputs[obj.item(i).toolTip()] = obj.item(i).text()
                    self.DrawRSCUfig_settings.setValue(name, dict_inputs)
                else:
                    allItems = [
                        obj.item(i).text() for i in range(obj.count())]
                    self.DrawRSCUfig_settings.setValue(name, allItems)
            if isinstance(obj, QSpinBox):
                value = obj.value()
                self.DrawRSCUfig_settings.setValue(name, value)
            if isinstance(obj, QDoubleSpinBox):
                value = obj.value()
                self.DrawRSCUfig_settings.setValue(name, value)
            if isinstance(obj, QPushButton):
                if name in ["pushButton_color", "pushButton_color_2",
                            "pushButton_color_3", "pushButton_color_4",
                            "pushButton_color_5", "pushButton_color_6",
                            "pushButton_color_7", "pushButton_color_8",
                            ]:
                    color = obj.palette().color(1)
                    self.DrawRSCUfig_settings.setValue(name, color.name())
            # if isinstance(obj, QTabWidget):
            #     value = obj.currentIndex()
            #     self.DrawRSCUfig_settings.setValue(name, value)
            if isinstance(obj, QLineEdit):
                value = obj.text()
                self.DrawRSCUfig_settings.setValue(name, value)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.factory.judgeWindowSize(self.DrawRSCUfig_settings, 746, 566))
        self.factory.centerWindow(self)
        # self.move(self.DrawRSCUfig_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QListWidget):
                if name == "listWidget_2":
                    ini_list = ["Gln", "His", "Asn", "Pro", "Thr", "Leu1", "Glu", "Met", "Arg", "Tyr", "Asp", "Lys",
                                "Ala", "Ile", "Ser1", "Ser2", "Leu2", "Cys", "Trp", "Val", "Gly", "Phe"]
                    values = self.DrawRSCUfig_settings.value(name, ini_list)
                    self.inputListWidget(values, obj)
                elif name == "listWidget_3":
                    ini_dict_input = OrderedDict()
                    dict_inputs = self.DrawRSCUfig_settings.value(name, ini_dict_input)
                    if self.autoInputs:
                        dict_inputs = OrderedDict()
                        for i in self.autoInputs:
                            dict_inputs[i] = os.path.splitext(os.path.basename(i))[0]
                    self.inputListWidget_3(dict_inputs)
            if isinstance(obj, QSpinBox):
                value = self.DrawRSCUfig_settings.value(name, obj.value())
                obj.setValue(int(value))
            if isinstance(obj, QDoubleSpinBox):
                value = self.DrawRSCUfig_settings.value(name, None)
                if value:
                    obj.setValue(float(value))
            if isinstance(obj, QPushButton):
                if obj in [self.pushButton_color, self.pushButton_color_2,
                           self.pushButton_color_3, self.pushButton_color_4,
                           self.pushButton_color_5, self.pushButton_color_6,
                           self.pushButton_color_7, self.pushButton_color_8,
                           ]:
                    dict_ini_colors = {"pushButton_color":"#6598C9",
                                       "pushButton_color_2":"#CB4A28",
                                       "pushButton_color_3":"#9AC664",
                                       "pushButton_color_4":"#7F5499",
                                       "pushButton_color_5":"#6060C6",
                                       "pushButton_color_6":"#69D1B1",
                                       "pushButton_color_7":"#222a2a",
                                       "pushButton_color_8":"#750d86",
                                       }
                    ini_color = dict_ini_colors[name]
                    color = self.DrawRSCUfig_settings.value(name, ini_color)
                    obj.setStyleSheet("background-color:%s"%color)
                    obj.setText(color)
                    obj.clicked.connect(self.changePbColor)
            # if isinstance(obj, QTabWidget):
            #     value = int(self.DrawRSCUfig_settings.value(name, 0))
            #     obj.setCurrentIndex(value)
            #     self.judgeRinstallation(value)
            if isinstance(obj, QLineEdit):
                value = self.DrawRSCUfig_settings.value(name, obj.text())
                obj.setText(value)

    def runProgress(self, num):
        oldValue = self.progressBar.value()
        done_int = int(num)
        if done_int > oldValue:
            self.progressBar.setProperty("value", done_int)
            QCoreApplication.processEvents()

    def popupException(self, exception):
        rgx = re.compile(r'Permission.+?[\'\"](.+\.pdf)[\'\"]')
        if rgx.search(exception):
            pdffile = rgx.search(exception).group(1)
            reply = QMessageBox.critical(
                self,
                "Draw RSCU figure",
                "<p style='line-height:25px; height:25px'>Please close 'pdf' file first!</p>",
                QMessageBox.Yes,
                QMessageBox.Cancel)
            if reply == QMessageBox.Yes and platform.system().lower() == "windows":
                os.startfile(pdffile)
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setText(
                'The program encountered an unforeseen problem, please report the bug at <a href="https://github.com/dongzhang0725/PhyloSuite/issues">https://github.com/dongzhang0725/PhyloSuite/issues</a> or send an email with the detailed traceback to dongzhang0725@gmail.com')
            msg.setWindowTitle("Error")
            msg.setDetailedText(exception)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()

    def closeEvent(self, event):
        self.guiSave()

    def inputListWidget(self, items, listwidget):
        listwidget.clear()
        for num, i in enumerate(items):
            item = QListWidgetItem(i)
            # 背景颜色
            if num % 2 == 0:
                item.setBackground(QColor(255, 255, 255))
            else:
                item.setBackground(QColor(237, 243, 254))
            listwidget.addItem(item)

    def inputListWidget_3(self, dict_items):
        if not dict_items:
            return
        # 自动根据文件数调整参数

        self.autoParameters(len(dict_items))
        self.listWidget_3.clear()
        for num, i in enumerate(dict_items):
            if os.path.exists(i):
                item = QListWidgetItem(dict_items[i])
                item.setToolTip(i)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                # 背景颜色
                if num % 2 == 0:
                    item.setBackground(QColor(255, 255, 255))
                else:
                    item.setBackground(QColor(237, 243, 254))
                self.listWidget_3.addItem(item)

    def rscu2fig(self):
        script = '''# auto install missing packages
list.of.packages <- c("ggplot2", "ggpubr")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[,"Package"])]
if(length(new.packages)) install.packages(new.packages, repos="http://cran.us.r-project.org")

library("ggplot2")
scaleFUN <- function(x) sprintf("%.2f", x)  #可以设置坐标轴显示的小数点位数，为了与图注保持一致\n'''
        allfig = [] # [1,2,3,4]
        sums = len(self.dict_args["dict_files_title"])
        for num, i in enumerate(self.dict_args["dict_files_title"]):
            self.Order_name = self.factory.int2word(num + 1).strip().replace(" ","_")
            self.rscu_file = os.path.normpath(i).replace("\\", "/")
            self.latin_name = self.dict_args["dict_files_title"][i]
            self.spe_number = str(num + 1)
            allfig.append(self.spe_number)
            self.Xaxis = '"'+'","'.join(self.dict_args["Order of x-axis"]) + '"'
            self.ylim = "%.1f"%self.dict_args["ylim"]
            # 生成RSCU堆积条形图代码
            script_i = '''
{self.Order_name} <- read.table("{self.rscu_file}",header = TRUE,sep=",")
f{self.Order_name} <- factor({self.Order_name}$Fill, levels = unique(rev({self.Order_name}$Fill)))   #填充的颜色的factor
#自定义横坐标顺序
x{self.Order_name} <- factor({self.Order_name}$AA, levels=c({self.Xaxis}))  #横坐标
y{self.Order_name} <- {self.Order_name}$RSCU  #Y值
z{self.Order_name} <- {self.Order_name}$Equality  #图注的Y值
l{self.Order_name} <- {self.Order_name}$Codon  #图注打标签
p{self.spe_number} <- ggplot(data = {self.Order_name}, mapping = aes(x = x{self.Order_name}, y = y{self.Order_name}, fill = f{self.Order_name},width = .7)) + geom_bar(stat = 'identity', position = 'stack')+ ggtitle("{self.latin_name}")+theme(axis.title.x=element_blank(),axis.title.y=element_text(size=10),legend.position="none",panel.background=element_blank(),panel.grid.minor=element_blank(),plot.background=element_blank(),axis.line.x = element_line(color="black", size = 0.5),axis.line.y = element_line(color="black", size = 0.5),axis.text.x=element_blank(), plot.title=element_text(family="sans",face="italic",hjust=0,size=10)) + scale_fill_manual("legend", values = c("1" = "{self.dict_args[Color of stacks][0]}", "2" = "{self.dict_args[Color of stacks][1]}", "3" = "{self.dict_args[Color of stacks][2]}", "4" = "{self.dict_args[Color of stacks][3]}"))+geom_text(mapping = aes(label = factor({self.Order_name}$aaRatio)), size = 2.5, vjust=-.2,position = position_stack()) + ylim(0,{self.ylim})+ylab("RSCU")\n'''.format(
                self=self)
            if num == (len(self.dict_args["dict_files_title"])-1):
                #最后一个要添加横坐标
                script_i = script_i.replace("axis.text.x=element_blank(),", "")
            script += script_i
            if num == 0:
                bottom = '''
p <- ggplot(data = {self.Order_name}, mapping = aes(x = x{self.Order_name}, y = z{self.Order_name}, fill = f{self.Order_name},width = .9)) + geom_bar(stat = 'identity', position = 'stack') + geom_text(mapping = aes(label = l{self.Order_name}), size = 2.4, colour = 'white', position = position_stack(vjust=.5))+theme(axis.text.x=element_blank(),axis.text.y=element_blank(),axis.ticks=element_blank(),axis.title.x=element_blank(),axis.title.y=element_blank(),legend.position="none",panel.background=element_blank(),panel.border=element_blank(),panel.grid.major=element_blank(),panel.grid.minor=element_blank(),plot.background=element_blank(),axis.line.y = element_blank()) + scale_fill_manual("legend", values = c("1" = "{self.dict_args[Color of stacks][0]}", "2" = "{self.dict_args[Color of stacks][1]}", "3" = "{self.dict_args[Color of stacks][2]}", "4" = "{self.dict_args[Color of stacks][3]}"))\n'''.format(
                    self=self)
            self.progressSig.emit((num+1)*50/sums)
        script += bottom
        allfig.append("")
        self.allfignum = "p" + ",p".join(allfig)
        self.str_matrix = ",".join(["1"]*len(self.dict_args["dict_files_title"]) + ["%.2f" %(1/self.dict_args["height proportion"])])  # (1,1,1,0.5)
        self.nrow = str(len(self.dict_args["dict_files_title"]) + 1)
        script += '''
library("ggpubr")
pall <- ggarrange({self.allfignum}, heights=c({self.str_matrix}), ncol=1, nrow={self.nrow}, align ="v")
pdf("{self.RSCUpath}",width={self.dict_args[Figure width]},height={self.dict_args[Figure height]}) 
pall
dev.off() 
'''.format(self=self)
        scriptPath = self.exportPath + os.sep + "rscu_scripts.r"
        with open(scriptPath, "w", encoding="utf-8") as f:
            f.write(script)
        self.progressSig.emit(60)
        return scriptPath

    def changePbColor(self):
        button = self.sender()
        ini_color = button.palette().color(1)
        color = QColorDialog.getColor(QColor(ini_color), self)
        if color.isValid():
            button.setText(color.name())
            button.setStyleSheet("background-color:%s"%color.name())

    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        if isinstance(
                obj,
                QListWidget):
            if event.type() == QEvent.DragEnter:
                if event.mimeData().hasUrls():
                    # must accept the dragEnterEvent or else the dropEvent
                    # can't occur !!!
                    event.accept()
                    return True
            if event.type() == QEvent.Drop:
                files = [u.toLocalFile() for u in event.mimeData().urls()]
                dict_inputs = {}
                for i in files:
                    dict_inputs[i] = os.path.splitext(os.path.basename(i))[0]
                self.inputListWidget_3(dict_inputs)
        if (event.type() == QEvent.Show) and (obj == self.pushButton.toolButton.menu()):
            if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+",
                         self.dir_action.text()) or self.dir_action.text() == "Output Dir: ":
                self.factory.sync_dir(self.dir_action)  ##同步文件夹名字
            menu_x_pos = self.pushButton.toolButton.menu().pos().x()
            menu_width = self.pushButton.toolButton.menu().size().width()
            button_width = self.pushButton.toolButton.size().width()
            pos = QPoint(menu_x_pos - menu_width + button_width,
                         self.pushButton.toolButton.menu().pos().y())
            self.pushButton.toolButton.menu().move(pos)
            return True
        # 其他情况会返回系统默认的事件处理方法。
        return super(DrawRSCUfig, self).eventFilter(obj, event)  # 0

    def popupWarning(self, text):
        QMessageBox.warning(
            self,
            "Warning",
            "<p style='line-height:25px; height:25px'>%s</p>" % text)

    def add_fig_to_row(self, figall, fig, row_, col_, hover_text):
        # add all the traces to appropriate subplot
        for f in fig.data:
            # manually modify hover
            f["hovertemplate"] = hover_text
            figall.add_trace(f, row=row_, col=col_)
        # in order to make layout set here work in final figure
        fig.for_each_trace(lambda trace_: trace_.update(xaxis=f"x{row_}", yaxis=f"y{row_}"))
        fig.layout[f"xaxis{row_}"] = fig.layout.pop("xaxis")
        fig.layout[f"yaxis{row_}"] = fig.layout.pop("yaxis")
        fig.layout[f"xaxis{row_}"]["anchor"] = f"y{row_}"
        fig.layout[f"yaxis{row_}"]["anchor"] = f"x{row_}"
        fig.layout[f"yaxis{row_}"].pop("domain")  # otherwise it will affect figall's domain
        figall.update_layout(fig.layout)
        return figall

    def plotly_rscu(self):
        '''
        TODO: space, offset, hover, color?, text family？ size? bar width?
        spacing 调好了图会比较好看
        每副正图需要215的高度？
        space 好像也最好跟着图的数量增加而改变
        :return:
        '''
        files, titles = [], []
        for file in self.dict_args["dict_files_title"]:
            files.append(file)
            titles.append(self.dict_args["dict_files_title"][file])
        fig_n = len(files)
        space_figs = self.dict_args["Figure interval"]
        y_offset = self.dict_args["RSCU offset"]
        text_size = self.dict_args["font size"] - 1
        width_ = self.dict_args["Figure width plotly"]
        height_ = self.dict_args["Figure height plotly"]
        bottom2fig_ratio = 1/self.dict_args["height proportion"]
        row_heights_ = [1 / (fig_n + bottom2fig_ratio)] * fig_n + [
            1 / (fig_n + bottom2fig_ratio) * bottom2fig_ratio]  # [1/2.5]*2 + [1/2.5*0.5] = [0.4, 0.4, 0.2]

        # subplots figure...
        figall = make_subplots(rows=fig_n + 1, row_heights=row_heights_, vertical_spacing=space_figs,
                               subplot_titles=titles)
        self.progressSig.emit(5)
        for num, file in enumerate(files):
            row_ = num + 1
            rscu = pd.read_csv(file)
            rscu = rscu.astype({"Fill": "category"})
            rscu = rscu.astype({"aaRatio": "object"})
            # change nan to str to avoid nan text
            rscu.loc[rscu["aaRatio"].isna(), "aaRatio"] = ""
            max_rscu = rscu.groupby(by=["AA"]).sum().max()["RSCU"]
            color_map = {i+1: self.dict_args["Color of stacks"][i] for i in range(8)}
            fig = px.bar(rscu,
                         x="AA",
                         y="RSCU",
                         color="Fill",
                         barmode='stack',
                         text="aaRatio",
                         custom_data=["AA", "RSCU", "Codon"],
                         color_discrete_map=color_map)
            # set x text order
            fig.update_layout(xaxis={'categoryorder': 'array',
                                     'categoryarray': self.dict_args["Order of x-axis"]})
            # show text to outside
            fig.update_traces(textposition='outside')
            if row_ != fig_n:
                fig.update_xaxes(showline=True,
                                 linewidth=1,
                                 linecolor="black",
                                 ticks="outside",
                                 tickangle=0,
                                 title=None,
                                 showticklabels=False)
            else:
                fig.update_xaxes(showline=True,
                                 linewidth=1,
                                 linecolor="black",
                                 ticks="outside",
                                 title=None)
            # set y range
            fig.update_yaxes(showline=True,
                             linewidth=1,
                             linecolor="black",
                             ticks="outside",
                             range=[0, max_rscu + y_offset])
            # add all the traces to appropriate subplot
            figall = self.add_fig_to_row(figall,
                                         fig,
                                         row_,
                                         1,
                                         "AA=%{x}<br>RSCU=%{y}<br>Codon=%{customdata[2]}<extra></extra>")
            # for f in fig.data:
            #     # manually modify hover
            #     f["hovertemplate"] = "AA=%{x}<br>RSCU=%{y}<br>Codon=%{customdata[2]}<extra></extra>"
            #     figall.add_trace(f, row=row_, col=1)
            # # in order to make layout set here work in final figure
            # fig.for_each_trace(lambda trace_: trace_.update(xaxis=f"x{row_}",
            #                                                 yaxis=f"y{row_}"))
            # fig.layout[f"xaxis{row_}"] = fig.layout.pop("xaxis")
            # fig.layout[f"yaxis{row_}"] = fig.layout.pop("yaxis")
            # fig.layout[f"xaxis{row_}"]["anchor"] = f"y{row_}"
            # fig.layout[f"yaxis{row_}"]["anchor"] = f"x{row_}"
            # fig.layout[f"yaxis{row_}"].pop("domain")  # otherwise it will affect figall's domain
            # figall.update_layout(fig.layout)
            self.progressSig.emit(5 + 80*row_/fig_n)
        fig_bottom = px.bar(rscu,
                            x="AA",
                            y="Equality",
                            color="Fill",
                            barmode='stack',
                            text="Codon",
                            custom_data=['AA', "Codon"],
                            color_discrete_map=color_map)
        # set x text order
        fig_bottom.update_layout(xaxis={'categoryorder': 'array',
                                        'categoryarray': self.dict_args["Order of x-axis"]})
        # show text to inside
        fig_bottom.update_traces(textposition='inside')
        bottom_row = fig_n + 1
        # add all the traces to appropriate subplot
        figall = self.add_fig_to_row(figall,
                                     fig_bottom,
                                     bottom_row,
                                     1,
                                     "AA=%{x}<br>Codon=%{customdata[1]}<extra></extra>")
        # for f in fig_bottom.data:
        #     # manually modify hover
        #     f["hovertemplate"] = "AA=%{x}<br>Codon=%{customdata[1]}<extra></extra>"
        #     figall.add_trace(f, row=bottom_row, col=1)
        # # in order to make layout set here work in final figure
        # fig_bottom.for_each_trace(lambda trace_: trace_.update(xaxis=f"x{bottom_row}", yaxis=f"y{bottom_row}"))
        # fig_bottom.layout[f"xaxis{bottom_row}"] = fig_bottom.layout.pop("xaxis")
        # fig_bottom.layout[f"yaxis{bottom_row}"] = fig_bottom.layout.pop("yaxis")
        # fig_bottom.layout[f"xaxis{bottom_row}"]["anchor"] = f"y{bottom_row}"
        # fig_bottom.layout[f"yaxis{bottom_row}"]["anchor"] = f"x{bottom_row}"
        # fig_bottom.layout[f"yaxis{bottom_row}"].pop("domain")  # otherwise it will affect figall's domain
        # figall.update_layout(fig_bottom.layout)
        self.progressSig.emit(95)

        # 设置整体的layout
        dict_layout = {"barmode": "stack",
                        "autosize": False,
                        "showlegend": False,
                        "plot_bgcolor": "white",
                        "paper_bgcolor": "white",
                        "uniformtext_minsize": text_size,
                        "uniformtext_mode": "show",
                        "width": width_,
                        "height": height_}
        # 最下面的图注单独设置
        dict_layout[f"yaxis{fig_n + 1}"] = {"title": None, "showticklabels": False}
        dict_layout[f"xaxis{fig_n + 1}"] = {"title": None, "showticklabels": False}
        figall.update_layout(dict_layout)
        # adjust title of each sub-figure
        figall.for_each_annotation(lambda x: x.update(x=0,
                                                      align="left",
                                                      xanchor="left",
                                                      font={"size": self.dict_args["font size"],
                                                            "family": self.dict_args["font family"],
                                                            "color": "black"}))
        # set all the bar width
        figall.for_each_trace(lambda trace_: trace_.update(width=self.dict_args["bar width"]))
        self.progressSig.emit(98)
        # figall.show()
        # print(figall)
        plotly.io.write_image(figall, self.RSCUpath, format='pdf')
        figall.write_html(self.RSCUhtml)

    def judgeRinstallation(self, index):
        tab_text = self.tabWidget.tabText(index)
        if tab_text == "ggplot (R)":
            RscriptPath = self.factory.programIsValid("RscriptPath", mode="tool")
            if RscriptPath:
                self.RscriptPath = RscriptPath
            else:
                reply = QMessageBox.information(
                    self,
                    "Information",
                    "<p style='line-height:25px; height:25px'>Please install Rscript and reopen the window.</p>",
                    QMessageBox.Ok,
                    QMessageBox.Cancel)
                if reply == QMessageBox.Ok:
                    self.close()
                    self.setting = Setting(self)
                    self.setting.display_table(self.setting.listWidget.item(1))
                    # 隐藏？按钮
                    self.setting.setWindowFlags(self.setting.windowFlags() | Qt.WindowMinMaxButtonsHint)
                    self.setting.exec_()
                else:
                    self.tabWidget.setCurrentIndex(0)

    def setFont(self):
        family = self.lineEdit.text()
        size = int(self.lineEdit_2.text())
        font, ok = QFontDialog.getFont(QFont(family, size), self)
        if ok:
            family_ = font.family()
            size_ = str(font.pointSize())
            self.lineEdit.setText(family_)
            self.lineEdit_2.setText(size_)

    def autoParameters(self, file_n):
        if file_n == 1:
            self.spinBox_7.setValue(410)
            self.doubleSpinBox.setValue(0.11)
        elif file_n == 2:
            self.spinBox_7.setValue(620)
            self.doubleSpinBox.setValue(0.07)
        elif file_n == 3:
            self.spinBox_7.setValue(820)
            self.doubleSpinBox.setValue(0.05)
        elif file_n == 4:
            self.spinBox_7.setValue(1040)
            self.doubleSpinBox.setValue(0.035)
        elif file_n == 5:
            self.spinBox_7.setValue(1240)
            self.doubleSpinBox.setValue(0.03)
        elif file_n == 6:
            self.spinBox_7.setValue(1440)
            self.doubleSpinBox.setValue(0.025)
        elif file_n == 7:
            self.spinBox_7.setValue(1640)
            self.doubleSpinBox.setValue(0.020)
        elif file_n == 8:
            self.spinBox_7.setValue(1840)
            self.doubleSpinBox.setValue(0.015)
        elif file_n == 9:
            self.spinBox_7.setValue(2040)
            self.doubleSpinBox.setValue(0.015)