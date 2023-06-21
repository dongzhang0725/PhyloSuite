import datetime
import multiprocessing
import re
import shutil
import traceback

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ete3 import NCBITaxa
from src.CustomWidget import MyTaxTableModel

from src.factory import Factory, WorkThread
import inspect
import os
import sys
from uifiles.Ui_mcmctree import Ui_MCMCTree

class MCMCTree(QDialog,Ui_MCMCTree,object):
    showSig = pyqtSignal(QDialog)
    closeSig = pyqtSignal(str, str)
    logGuiSig = pyqtSignal(str)
    startButtonStatusSig = pyqtSignal(list)
    mcmctree_exception = pyqtSignal(str)
    exception_signal = pyqtSignal(str)  # 定义所有类都可以使用的信号
    progressSig = pyqtSignal(int)  # 控制进度条

    def __init__(
            self,
            workPath=None,
            focusSig=None,
            mcmctreeEXE=None,
            parent=None):
        super(MCMCTree, self).__init__(parent)
        self.parent = parent
        self.function_name = "MCMCTree"
        self.factory = Factory()
        self.thisPath = self.factory.thisPath
        self.workPath = workPath
        self.focusSig = focusSig
        self.mcmctreeEXE = mcmctreeEXE
        self.seqFileName = ''
        self.treeFileName = ''
        self.setupUi(self)
        self.MCMCTree_settings = QSettings(
           self.thisPath + '/settings/MCMCTree_settings.ini', QSettings.IniFormat)
        # File only, no fallback to registry or or.
        self.MCMCTree_settings.setFallbacksEnabled(False)
        self.qss_file = self.factory.set_qss(self)
        # 恢复用户的设置
        self.guiRestore()
        self.log_gui = self.gui4Log()
        self.text_gui = self.gui4Text()
        # 槽函数
        self.startButtonStatusSig.connect(self.factory.ctrl_startButton_status)
        self.logGuiSig.connect(self.addText2Log)
        self.progressSig.connect(self.runProgress)
        # 给开始按钮添加菜单
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        self.work_action = QAction(QIcon(":/picture/resourses/work.png"), "", menu)
        self.work_action.triggered.connect(lambda: self.factory.swithWorkPath(self.work_action, parent=self))
        self.dir_action = QAction(QIcon(":/picture/resourses/folder.png"), "Output Dir: ", menu)
        self.dir_action.triggered.connect(lambda: self.factory.set_direct_dir(self.dir_action, self))
        menu.addAction(self.work_action)
        menu.addAction(self.dir_action)
        self.pushButton_5.toolButton.setMenu(menu)
        self.pushButton_5.toolButton.menu().installEventFilter(self)
        self.factory.swithWorkPath(self.work_action, init=True, parent=self)  # 初始化一下

    def input(self, file, which):
        base = os.path.basename(file)
        if which == 4:
            self.lineEdit.setText(base)
            self.lineEdit.setToolTip(os.path.abspath(file))
        if which == 3:
            self.lineEdit_2.setText(base)
            self.lineEdit_2.setToolTip(os.path.abspath(file))
        """tre = self.factory.read_tree(file)
        list_leaves = tre.get_leaf_names()
        self.init_table(list_leaves)"""

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Input tre file", filter="Newick Format(*.nwk *.newick *.tre);;")
        if fileName[0]:
            self.seqFileName = fileName[0]
            self.input(self.seqFileName, 4)

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        fileName = QFileDialog.getOpenFileName(
            self, "Input alignment file", filter="Phylip Format(*.txt);;")
        if fileName[0]:
            self.treeFileName = fileName[0]
            self.input(self.treeFileName, 3)

    @pyqtSlot()
    def on_pushButton_15_clicked(self):
        s_Values, ds_Values = self.getParas()
        print(f"s_Values:{s_Values}")
        print(f"ds_Values:{ds_Values}")
        self.ctl_generater()

    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        """
        show log
        """
        self.log_gui.show()

    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        self.text_gui.show()

    @pyqtSlot()
    def on_pushButton_5_clicked(self):
        """
        execute program
        """
        self.commands = self.prepare_for_run()
        print(self.commands)
        if self.commands:
            # 有数据才执行
            self.interrupt = False  # 如果是终止以后重新运行要刷新
            self.textEdit_log.clear()  # 清空log
            self.mcmctree_popen = self.factory.init_popen(self.commands)
            self.factory.emitCommands(self.logGuiSig, self.commands)
            self.worker = WorkThread(self.run_command, parent=self)
            self.worker.start()

    def run_command(self):
        try:
            time_start = datetime.datetime.now()
            self.startButtonStatusSig.emit(
                [
                    self.pushButton_5,
                    self.progressBar,
                    "start",
                    self.exportPath,
                    self.qss_file,
                    self])
            print(111)
            self.run_code()
            time_end = datetime.datetime.now()
            self.time_used = str(time_end - time_start)
            self.time_used_des = "Start at: %s\nFinish at: %s\nTotal time used: %s\n\n" % (str(time_start), str(time_end),
                                                                                           self.time_used)
            # 加上version信息
            with open(self.exportPath + os.sep + "PhyloSuite_PartitionFinder.log") as f:
                content = f.read()
            rgx_version = re.compile(r"-+\s+PartitionFinder.+?(\d+\.\d+\.\d+)")
            if rgx_version.search(content):
                self.version = rgx_version.search(content).group(1)
            else:
                self.version = ""
            self.description = self.description.replace("$version$", self.version)
            with open(self.exportPath + os.sep + "summary and citation.txt", "w", encoding="utf-8") as f:
                f.write(self.description +
                        f"\n\nIf you use PhyloSuite v1.2.3 v1.2.3, please cite:\n{self.factory.get_PS_citation()}\n\n"
                        "If you use PartitionFinder 2, please cite:\n" + self.reference + "\n\n" + self.time_used_des)
            if not self.interrupt:
                if self.workflow:
                    # work flow跑的
                    self.startButtonStatusSig.emit(
                        [
                            self.pushButton_5,
                            self.progressBar,
                            "workflow stop",
                            self.exportPath,
                            self.qss_file,
                            self])
                    self.workflow_finished.emit("finished")
                    return
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton_5,
                        self.progressBar,
                        "stop",
                        self.exportPath,
                        self.qss_file,
                        self])
            else:
                self.startButtonStatusSig.emit(
                    [
                        self.pushButton_5,
                        self.progressBar,
                        "except",
                        self.exportPath,
                        self.qss_file,
                        self])
            if not self.workflow:
                self.focusSig.emit(self.exportPath)
        except BaseException:
            self.exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            self.exception_signal.emit(self.exceptionInfo)  # 激发这个信号
            self.startButtonStatusSig.emit(
                [
                    self.pushButton_5,
                    self.progressBar,
                    "except",
                    self.exportPath,
                    self.qss_file,
                    self])

    def run_code(self):
        is_error = False  ##判断是否出了error
        error_text = ""
        self.progressSig.emit(99999)
        while True:
            QApplication.processEvents()
            if self.isRunning():
                try:
                    out_line = self.mcmctree_popen.stdout.readline().decode("utf-8", errors="ignore")
                except UnicodeDecodeError:
                    out_line = self.mcmctree_popen.stdout.readline().decode("gbk", errors="ignore")
                if out_line == "" and self.mcmctree_popen.poll() is not None:
                    break
                self.logGuiSig.emit(out_line.strip())
                if re.search(r"^ERROR", out_line):
                    is_error = True
                    error_text = "Error happened! Click <span style='font-weight:600; color:#ff0000;'>Show log</span> to see detail!"
            else:
                break
        if is_error:
            self.interrupt = True
            self.mcmctree_exception.emit(error_text)
        self.mcmctree_popen = None

    def showText(self, lst):
        self.tableView_2.setRowCount(len(lst))
        self.tableView_2.setColumnCount(1)
        for i in range(len(lst)):
            item = QTableWidgetItem(lst[i])
            self.tableView_2.setItem(i, 0, item)

    def guiSave(self):
        # Save geometry
        self.MCMCTree_settings.setValue('size', self.size())
        # self.MCMCTree_settings.setValue('pos', self.pos())

        for name, obj in inspect.getmembers(self):
            # if type(obj) is QComboBox:  # this works similar to isinstance, but
            # missed some field... not sure why?
            if isinstance(obj, QComboBox):
                # save combobox selection to registry
                index = obj.currentIndex()
                self.MCMCTree_settings.setValue(name, index)
            # if isinstance(obj, QCheckBox):
            #     state = obj.isChecked()
            #     self.MCMCTree_settings.setValue(name, state)
            elif isinstance(obj,QSpinBox):
                int_ = obj.value()
                self.MCMCTree_settings.setValue(name, int_)
            elif isinstance(obj, QDoubleSpinBox):
                float_ = obj.value()
                self.MCMCTree_settings.setValue(name, float_)

    def guiRestore(self):

        # Restore geometry
        self.resize(self.MCMCTree_settings.value('size', QSize(1000, 750)))
        self.factory.centerWindow(self)
        # self.move(self.MCMCTree_settings.value('pos', QPoint(875, 254)))

        for name, obj in inspect.getmembers(self):
            if isinstance(obj, QComboBox):
                if name == "comboBox_6":
                    cpu_num = multiprocessing.cpu_count()
                    list_cpu = [str(i + 1) for i in range(cpu_num)]
                    index = self.MCMCTree_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(list_cpu):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
                else:
                    allItems = [obj.itemText(i) for i in range(obj.count())]
                    index = self.MCMCTree_settings.value(name, "0")
                    model = obj.model()
                    obj.clear()
                    for num, i in enumerate(allItems):
                        item = QStandardItem(i)
                        # 背景颜色
                        if num % 2 == 0:
                            item.setBackground(QColor(255, 255, 255))
                        else:
                            item.setBackground(QColor(237, 243, 254))
                        model.appendRow(item)
                    obj.setCurrentIndex(int(index))
            # elif isinstance(obj, QCheckBox):
            #     value = self.MCMCTree_settings.value(
            #         name, "no setting")  # get stored value from registry
            #     if value != "no setting":
            #         obj.setChecked(
            #             self.factory.str2bool(value))  # restore checkbox
            elif isinstance(obj, QLineEdit):
                if name == "lineEdit_5" and self.autoInputs:
                    self.input(self.autoInputs, obj)
            elif isinstance(obj, QDoubleSpinBox):
                ini_float_ = obj.value()
                float_ = self.MCMCTree_settings.value(name, ini_float_)
                obj.setValue(float(float_))
            elif isinstance(obj,QSpinBox):
                ini_int_ = obj.value()
                int_ = self.MCMCTree_settings.value(name,ini_int_)
                obj.setValue(int(int_))

    def closeEvent(self, event):
        self.guiSave()
        # self.log_gui.close()  # 关闭子窗口
        # 断开showSig和closeSig的槽函数连接
        try:
            self.showSig.disconnect()
        except:
            pass
        try:
            self.closeSig.disconnect()
        except:
            pass

    def setWordWrap(self):
        button = self.sender()
        if button.isChecked():
            button.setChecked(True)
            self.textEdit_log.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            button.setChecked(False)
            self.textEdit_log.setLineWrapMode(QTextEdit.NoWrap)

    def save_log_to_file(self):
        content = self.textEdit_log.toPlainText()
        fileName = QFileDialog.getSaveFileName(
            self, "MrBayes", "log", "text Format(*.txt)")
        if fileName[0]:
            with open(fileName[0], "w", encoding="utf-8") as f:
                f.write(content)

    def gui4Text(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Preview configurations")
        para_s, para_ds = self.getParas()
        model = QStandardItemModel()
        #print(para_s[15])
        items_list = [("seed", para_s[15], "-", "-"),
                      ("ndata", para_s[0], "-", "-"),
                      ("seqtype", para_s[17], "-", "-"),
                      ("usedata", para_s[18], "-", "-"),
                      ("clock", para_s[19], "-", "-"),
                      ("RootAge <", para_ds[0], "-", "-"),
                      ("model", para_s[20], "-", "-"),
                      ("alpha", para_ds[5], "-", "-"),
                      ("ncatG", para_s[13], "-", "-"),
                      ("cleandata", para_s[16], "-", "-"),
                      ("BDparas", para_ds[2], para_ds[3], para_ds[4]),
                      ("kappa_gamma", para_s[22], para_s[23], "-"),
                      ("alpha_gamma", para_s[1], para_s[2], "-"),
                      ("rgene_gamma", para_s[3], para_s[4], para_s[5]),
                      ("sigma2_gamma", para_s[6], para_s[7], para_s[8]),
                      ("print", para_s[21], "-", "-"),
                      ("burnin", para_s[9], "-", "-"),
                      ("samefreq", para_s[10], "-", "-"),
                      ("nsample", para_s[12], "-", "-")]

        for row, item in enumerate(items_list):
            name_item = QStandardItem(item[0])
            param_item = QStandardItem(str(item[1]))
            param_item_rd = QStandardItem(str(item[2]))
            param_item_th = QStandardItem(str(item[3]))
            model.setItem(row, 0, name_item)
            model.setItem(row, 1, param_item)
            model.setItem(row, 2, param_item_rd)
            model.setItem(row, 3, param_item_th)
        verticalLayout_2 = QVBoxLayout(dialog)
        groupBox = QGroupBox("Configuration", dialog)
        verticalLayout = QVBoxLayout(groupBox)
        tableView = QTableView(groupBox)
        tableView.setModel(model)
        verticalLayout.addWidget(tableView)
        verticalLayout_2.addWidget(groupBox)
        gridLayout = QGridLayout()
        pushButton_2 = QPushButton("Save", dialog)
        gridLayout.addWidget(pushButton_2, 0, 0, 1, 1)
        pushButton = QPushButton("Cancel", dialog)
        gridLayout.addWidget(pushButton, 0, 1, 1, 1)
        verticalLayout_2.addLayout(gridLayout)
        pushButton.clicked.connect(dialog.close)
        pushButton_2.clicked.connect(lambda: self.updateParas(model))
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def updateParas(self, model):
        para_s, para_ds = self.getParas()
        for row in range(model.rowCount()):
            param_item = model.item(row, 1)
            if param_item:
                para_s[row] = float(param_item.text())
        return para_s, para_ds

    def gui4Log(self):
        dialog = QDialog(self)
        dialog.resize(800, 500)
        dialog.setWindowTitle("Log")
        gridLayout = QGridLayout(dialog)
        horizontalLayout_2 = QHBoxLayout()
        label = QLabel(dialog)
        label.setText("Log of MCMCTree:")
        horizontalLayout_2.addWidget(label)
        spacerItem = QSpacerItem(
            40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        horizontalLayout_2.addItem(spacerItem)
        toolButton = QToolButton(dialog)
        icon2 = QIcon()
        icon2.addPixmap(
            QPixmap(":/picture/resourses/interface-controls-text-wrap-512.png"))
        toolButton.setIcon(icon2)
        toolButton.setCheckable(True)
        toolButton.setToolTip("Use Wraps")
        toolButton.clicked.connect(self.setWordWrap)
        toolButton.setChecked(True)
        horizontalLayout_2.addWidget(toolButton)
        pushButton = QPushButton("Save to file", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/Save-icon.png"))
        pushButton.setIcon(icon)
        pushButton_2 = QPushButton("Close", dialog)
        icon = QIcon()
        icon.addPixmap(QPixmap(":/picture/resourses/if_Delete_1493279.png"))
        pushButton_2.setIcon(icon)
        self.textEdit_log = QTextEdit(dialog)
        self.textEdit_log.setReadOnly(True)
        gridLayout.addLayout(horizontalLayout_2, 0, 0, 1, 2)
        gridLayout.addWidget(self.textEdit_log, 1, 0, 1, 2)
        gridLayout.addWidget(pushButton, 2, 0, 1, 1)
        gridLayout.addWidget(pushButton_2, 2, 1, 1, 1)
        pushButton.clicked.connect(self.save_log_to_file)
        pushButton_2.clicked.connect(dialog.close)
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowMinMaxButtonsHint)
        return dialog

    def getParas(self):
        #filename =
        s_Values = []
        ds_Values = []
        for name, obj in inspect.getmembers(self):
            if isinstance(obj,QSpinBox):
                s_Values.append(obj.value())
            elif isinstance(obj,QDoubleSpinBox):
                ds_Values.append(obj.value())
        return s_Values, ds_Values

    def ctl_generater(self, file_path=None):
        def generate_ctl(seqfile, treefile):
            return f'''          seed = {s_Values[15]}
       seqfile = {seqfile}
      treefile = {treefile}
      mcmcfile = mcmc.txt
       outfile = out.txt

         ndata = {s_Values[0]}
       seqtype = {s_Values[17]}
       usedata = {s_Values[18]}
         clock = {s_Values[19]}
       RootAge = '<{ds_Values[0]}'
       
         model = {s_Values[20]}
         alpha = {ds_Values[5]}
         ncatG = {s_Values[13]}

     cleandata = {s_Values[16]}

       BDparas = {ds_Values[2]} {ds_Values[3]} {ds_Values[4]}
   kappa_gamma = {s_Values[22]} {s_Values[23]}
   alpha_gamma = {s_Values[1]} {s_Values[2]}

   rgene_gamma = {s_Values[3]} {s_Values[4]} {s_Values[5]}
  sigma2_gamma = {s_Values[6]} {s_Values[7]} {s_Values[8]}

         print = {s_Values[21]}
        burnin = {s_Values[9]}
      sampfreq = {s_Values[10]}
       nsample = {s_Values[12]}

*** Note: Make your window wider (100 columns) before running the program.'''
        s_Values, ds_Values = self.getParas()
        seqfile = os.path.basename(self.seqFileName)
        treefile = os.path.basename(self.treeFileName)
        if file_path:
            mcmctree_ctl = generate_ctl(seqfile, treefile)
            with open(file_path, "w", errors="ignore") as f:
                f.write(mcmctree_ctl)
        else:
            options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
            directory = QFileDialog.getExistingDirectory(self, "Choose folder", options=options)
            if directory:
                mcmctree_ctl = generate_ctl(seqfile, treefile)
                file_path = f"{directory}{os.sep}mcmctree.ctl"
                if os.path.exists(file_path):
                    reply = QMessageBox.question(self, "File Exists", f"文件 {file_path} 已存在，是否覆盖？",
                                                 QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        with open(file_path, "w", errors="ignore") as f:
                            f.write(mcmctree_ctl)
                else:
                    with open(file_path, "w", errors="ignore") as f:
                        f.write(mcmctree_ctl)

    def prepare_for_run(self):
        self.output_dir_name = self.factory.fetch_output_dir_name(self.dir_action)
        self.exportPath = self.factory.creat_dirs(self.workPath +
                                                  os.sep + "MCMCTREE_results" + os.sep + self.output_dir_name)
        ctl_file = f"{self.exportPath}{os.sep}mcmctree.ctl"
        self.ctl_generater(ctl_file)
        shutil.copy(self.seqFileName, self.exportPath + os.sep + os.path.basename(self.seqFileName))
        shutil.copy(self.treeFileName, self.exportPath + os.sep + os.path.basename(self.treeFileName))
        os.chdir(self.exportPath)
        cmds = f"{self.mcmctreeEXE} {ctl_file}"
        return cmds


    def eventFilter(self, obj, event):
        # modifiers = QApplication.keyboardModifiers()
        name = obj.objectName()
        if (event.type() == QEvent.Show) and (obj == self.pushButton_5.toolButton.menu()):
            if re.search(r"\d+_\d+_\d+\-\d+_\d+_\d+",
                         self.dir_action.text()) or self.dir_action.text() == "Output Dir: ":
                self.factory.sync_dir(self.dir_action)  ##同步文件夹名字
            menu_x_pos = self.pushButton_5.toolButton.menu().pos().x()
            menu_width = self.pushButton_5.toolButton.menu().size().width()
            button_width = self.pushButton_5.toolButton.size().width()
            pos = QPoint(menu_x_pos - menu_width + button_width,
                         self.pushButton_5.toolButton.menu().pos().y())
            self.pushButton_5.toolButton.menu().move(pos)
            return True
        # return QMainWindow.eventFilter(self, obj, event) #
        # 其他情况会返回系统默认的事件处理方法。
        return super(MCMCTree, self).eventFilter(obj, event)  # 0

    def isRunning(self):
        '''判断程序是否运行,依赖进程是否存在来判断'''
        return hasattr(self, "mcmctree_popen") and self.mcmctree_popen and not self.interrupt

    def addText2Log(self, text):
        if re.search(r"\w+", text):
            self.textEdit_log.append(text)
            with open(self.exportPath + os.sep + "PhyloSuite_MCMCTREE.log", "a", errors='ignore') as f:
                f.write(text + "\n")

    def runProgress(self, num):
        if num == 99999:
            self.progressBar.setMaximum(0)
            self.progressBar.setMinimum(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ui = MCMCTree()
    ui.show()
    sys.exit(app.exec_())