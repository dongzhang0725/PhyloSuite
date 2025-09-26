import sys
import traceback

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QFileDialog, QLabel, QAction, QStatusBar)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from dna_features_viewer import BiopythonTranslator, GraphicFeature
from Bio import SeqIO

GraphicFeature

class GenbankViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.gb_path = r"C:\Users\HUAWEI\works\Nematoda\example\21_flatworms_mtDNA.gb"
        color_map = {
            # "t": "yellow",
            "CDS": "orange",
            # "regulatory": "red",
            "tRNA": "green",
            "rRNA": "lightblue",
        }
        self.translator = BiopythonTranslator(features_filters=(lambda f:
                                                                f.type not in
                                                                ["gene", "source"],),
                                              features_properties=lambda f: {"color":
                                                                                 color_map.get(f.type,
                                                                                               "white")},)
        self.plotGenbank()

    def initUI(self):
        # 主窗口设置
        self.setWindowTitle('GenBank Viewer')
        self.setGeometry(100, 100, 800, 600)

        # 创建中央部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Matplotlib画布
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # 状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # 创建菜单栏
        self.createMenus()

    def createMenus(self):
        # 文件菜单
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        # 打开文件动作
        openAction = QAction('&Open...', self)
        openAction.triggered.connect(self.openFile)
        fileMenu.addAction(openAction)

        # 退出动作
        exitAction = QAction('&Exit', self)
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

    def openFile(self):
        # 文件对话框
        path, _ = QFileDialog.getOpenFileName(
            self, "Open GenBank File", "",
            "GenBank Files (*.gb *.gbk);;All Files (*)"
        )

        if path:
            try:
                self.gb_path = path
                self.plotGenbank()
                self.statusBar.showMessage(f"Loaded: {path}")
            except Exception as e:
                self.statusBar.showMessage(f"Error: {str(e)}")

    def plotGenbank(self):
        # 清空画布
        self.figure.clear()

        # 转换并绘制GenBank文件
        try:
            # 使用Biopython直接解析
            records= list(SeqIO.parse(self.gb_path, "genbank"))
            # record_count = SeqIO.count(self.gb_path, "genbank")

            record_count = len(records)
            for num, record in enumerate(records):
                # 创建子图
                graphic_record = self.translator.translate_record(record)
                ax = self.figure.add_subplot(record_count, 1, num+1)
                graphic_record.plot(ax=ax,
                                    # figure_width=10,
                                    # figure_height=10,
                                    # strand_in_label_threshold=20,
                                    elevate_outline_annotations=True)
            # 调整布局
            self.figure.tight_layout()
            self.canvas.draw()

        except Exception as e:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Error loading GenBank file",
                    ha='center', va='center')
            self.canvas.draw()
            exceptionInfo = ''.join(
                traceback.format_exception(
                    *sys.exc_info()))  # 捕获报错内容，只能在这里捕获，没有报错的地方无法捕获
            print(exceptionInfo)
            raise e

if __name__ == '__main__':
    app = QApplication(sys.argv)
    viewer = GenbankViewer()
    viewer.show()
    sys.exit(app.exec_())