#-----------------------------------------------------------------------------
# Pyr8s - Divergence Time Estimation
# Copyright (C) 2021  Patmanidis Stefanos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------


import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui

import sys
import logging
import re
import pickle

from .. import core
from .. import parse
from ..param import qt as param_qt

from . import utility
from . import widgets
from . import resources

class Main(QtWidgets.QDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, init=None):
        super(Main, self).__init__(parent)

        logging.getLogger().setLevel(logging.DEBUG)
        self.analysis = core.RateAnalysis()

        self.setWindowTitle("pyr8s")
        self.resize(854,480)
        self.machine = None
        self.skin()
        self.draw()
        self.act()
        self.stateInit()

        if init is not None:
            self.machine.started.connect(init)

    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state

    def reject(self):
        """Called on dialog close or <ESC>"""
        if self.stateCheck('STATE_RUNNING'):
            self.handleCancel()
            return
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText('Are you sure you want to quit?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Yes)
        confirm = msgBox.exec()
        if confirm == QtWidgets.QMessageBox.Yes:
            super().reject()

    def closeMessages(self):
        """Rejects any open QMessageBoxes"""
        for widget in self.children():
            if widget.__class__ == QtWidgets.QMessageBox:
                widget.reject()

    def fail(self, exception):
        # raise exception
        self.closeMessages()
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setText('An exception occured:')
        msgBox.setInformativeText(str(exception))
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.exec()
        logger = logging.getLogger()
        logger.error(str(exception))

    def stateCheck(self, name):
        """Check if given state is currently running"""
        if self.machine is not None:
            for state in list(self.machine.configuration()):
                if state.objectName() == name:
                    return True
        return False

    def stateInit(self):
        """Initialize state machine"""
        self.machine = QtCore.QStateMachine(self)

        idle = QtCore.QState()
        idle_none = QtCore.QState(idle)
        idle_open = QtCore.QState(idle)
        idle_done = QtCore.QState(idle)
        idle_updated = QtCore.QState(idle)
        idle_last = QtCore.QHistoryState(idle)
        idle.setInitialState(idle_none)
        running = QtCore.QState()

        idle.setObjectName('STATE_IDLE')
        idle.assignProperty(self.paramWidget.container, 'enabled', True)
        idle.assignProperty(self.actionStop, 'visible', False)
        idle.assignProperty(self.actionRun, 'visible', True)
        def onEntry(event):
            self.treeConstraints.setItemsDisabled(False)
            self.treeResults.setItemsDisabled(False)
            self.setFocus()
        idle.onEntry = onEntry

        idle_none.setObjectName('STATE_IDLE_NONE')
        idle_none.assignProperty(self.searchWidget, 'enabled', False)
        idle_none.assignProperty(self.tabConstraints, 'enabled', False)
        idle_none.assignProperty(self.tabParams, 'enabled', False)
        idle_none.assignProperty(self.tabResults, 'enabled', False)
        idle_none.assignProperty(self.tabDiagram, 'enabled', False)
        idle_none.assignProperty(self.tabTable, 'enabled', False)
        idle_none.assignProperty(self.actionRun, 'enabled', False)
        idle_none.assignProperty(self.actionSave, 'enabled', False)
        idle_none.assignProperty(self.actionExport, 'enabled', False)
        idle_none.assignProperty(self.barFlags, 'enabled', False)
        idle_none.assignProperty(self.labelFlagInfo, 'text', 'Nothing to display.')
        idle_none.assignProperty(self.labelFlagInfo, 'visible', True)
        idle_none.assignProperty(self.labelFlagWarn, 'visible', False)

        idle_open.setObjectName('STATE_IDLE_OPEN')
        idle_open.assignProperty(self.searchWidget, 'enabled', True)
        idle_open.assignProperty(self.tabConstraints, 'enabled', True)
        idle_open.assignProperty(self.tabParams, 'enabled', True)
        idle_open.assignProperty(self.tabResults, 'enabled', False)
        idle_open.assignProperty(self.tabDiagram, 'enabled', False)
        idle_open.assignProperty(self.tabTable, 'enabled', False)
        idle_open.assignProperty(self.actionRun, 'enabled', True)
        idle_open.assignProperty(self.actionSave, 'enabled', True)
        idle_open.assignProperty(self.actionExport, 'enabled', False)
        idle_open.assignProperty(self.barFlags, 'enabled', True)
        idle_open.assignProperty(self.labelFlagInfo, 'text', 'Ready to run rate analysis.')
        idle_open.assignProperty(self.labelFlagInfo, 'visible', True)
        idle_open.assignProperty(self.labelFlagWarn, 'visible', False)
        def onEntry(event):
            self.tabContainerAnalysis.setCurrentIndex(0)
            self.setFocus()
        idle_open.onEntry = onEntry

        idle_done.setObjectName('STATE_IDLE_DONE')
        idle_done.assignProperty(self.searchWidget, 'enabled', True)
        idle_done.assignProperty(self.tabConstraints, 'enabled', True)
        idle_done.assignProperty(self.tabParams, 'enabled', True)
        idle_done.assignProperty(self.tabResults, 'enabled', True)
        idle_done.assignProperty(self.tabDiagram, 'enabled', True)
        idle_done.assignProperty(self.tabTable, 'enabled', True)
        idle_done.assignProperty(self.actionRun, 'enabled', True)
        idle_done.assignProperty(self.actionSave, 'enabled', True)
        idle_done.assignProperty(self.actionExport, 'enabled', True)
        idle_done.assignProperty(self.barFlags, 'enabled', True)
        idle_done.assignProperty(self.labelFlagInfo, 'text', 'Analysis complete.')
        idle_done.assignProperty(self.labelFlagInfo, 'visible', False)
        idle_done.assignProperty(self.labelFlagWarn, 'visible', True)
        def onEntry(event):
            self.tabContainerAnalysis.setCurrentIndex(0)
            self.tabContainerResults.setCurrentIndex(0)
        idle_done.onEntry = onEntry

        running.setObjectName('STATE_RUNNING')
        running.assignProperty(self.actionRun, 'visible', False)
        running.assignProperty(self.actionStop, 'visible', True)
        running.assignProperty(self.paramWidget.container, 'enabled', False)
        running.assignProperty(self.barFlags, 'enabled', True)
        running.assignProperty(self.labelFlagInfo, 'text', 'Please wait...')
        running.assignProperty(self.labelFlagWarn, 'visible', False)
        def onEntry(event):
            self.tabContainerResults.setCurrentIndex(1)
            self.treeConstraints.setItemsDisabled(True)
            self.treeResults.setItemsDisabled(True)
        running.onEntry = onEntry

        idle_updated.assignProperty(self.barFlags, 'enabled', True)
        idle_updated.assignProperty(self.labelFlagInfo, 'visible', False)
        idle_updated.assignProperty(self.labelFlagWarn, 'visible', True)
        idle_updated.assignProperty(self.labelFlagWarn, 'text',
            'Parameters have changed, re-run analysis to update results.')

        transition = utility.NamedTransition('OPEN')
        def onTransition(event):
            fileInfo = QtCore.QFileInfo(event.kwargs['file'])
            labelText = fileInfo.baseName()
            treeName = self.analysis.tree.label
            if treeName is not None:
                if len(treeName) > 0 and treeName != labelText:
                    labelText += ': ' + treeName
            self.labelTree.setText(labelText)
            self.treeResults.clear()
            self.treeConstraints.clear()
            widgets.TreeWidgetNodeConstraints(
                self.treeConstraints, self.analysis.tree.seed_node)
            idealWidth = self.treeConstraints.idealWidth()
            width = min([self.width()/2, idealWidth])
            self.splitter.setSizes([int(width), 1, int(self.width()/2)])
            if self.analysis.results is not None:
                self.machine.postEvent(utility.NamedEvent('LOAD'))
        transition.onTransition = onTransition
        transition.setTargetState(idle_open)
        idle.addTransition(transition)

        transition = utility.NamedTransition('LOAD')
        def onTransition(event):
            warning = self.analysis.results.flags['warning']
            self.labelFlagWarn.setText(warning)
            self.treeResults.clear()
            widgets.TreeWidgetNodeResults(
                self.treeResults, self.analysis.results.tree.seed_node)
        transition.onTransition = onTransition
        transition.setTargetState(idle_done)
        idle.addTransition(transition)

        transition = utility.NamedTransition('RUN')
        transition.setTargetState(running)
        idle.addTransition(transition)

        transition = utility.NamedTransition('DONE')
        def onTransition(event):
            warning = self.analysis.results.flags['warning']
            self.labelFlagWarn.setText(warning)
            self.treeResults.clear()
            widgets.TreeWidgetNodeResults(
                self.treeResults, self.analysis.results.tree.seed_node)
            self.closeMessages()
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle(self.windowTitle())
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setText('Analysis complete.')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgBox.exec()
        transition.onTransition = onTransition
        transition.setTargetState(idle_done)
        running.addTransition(transition)

        transition = utility.NamedTransition('UPDATE')
        transition.setTargetState(idle_updated)
        idle_done.addTransition(transition)

        transition = utility.NamedTransition('FAIL')
        def onTransition(event):
            self.tabContainerResults.setCurrentIndex(1)
            self.fail(event.args[0])
        transition.onTransition = onTransition
        transition.setTargetState(idle_last)
        running.addTransition(transition)

        transition = utility.NamedTransition('CANCEL')
        transition.setTargetState(idle_last)
        running.addTransition(transition)

        self.machine.addState(idle)
        self.machine.addState(running)
        self.machine.setInitialState(idle)
        self.machine.start()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if (source == self.treeConstraints and
                event.key() == QtCore.Qt.Key_Return and
                self.treeConstraints.state() !=
                    QtWidgets.QAbstractItemView.EditingState):
                self.handleRun()
                return True
        return QtCore.QObject.eventFilter(self, source, event)

    def skin(self):
        """Configure widget appearance"""
        color = {
            'white':  '#ffffff',
            'light':  '#eff1ee',
            'beige':  '#e1e0de',
            'gray':   '#abaaa8',
            'iron':   '#8b8d8a',
            'black':  '#454241',
            'red':    '#ee4e5f',
            'pink':   '#eb9597',
            'orange': '#eb6a4a',
            'brown':  '#655c5d',
            'green':  '#00ff00',
            }
        # using green for debugging
        palette = QtGui.QGuiApplication.palette()
        scheme = {
            QtGui.QPalette.Active: {
                QtGui.QPalette.Window: 'light',
                QtGui.QPalette.WindowText: 'black',
                QtGui.QPalette.Base: 'white',
                QtGui.QPalette.AlternateBase: 'light',
                QtGui.QPalette.PlaceholderText: 'brown',
                QtGui.QPalette.Text: 'black',
                QtGui.QPalette.Button: 'light',
                QtGui.QPalette.ButtonText: 'black',
                QtGui.QPalette.Light: 'white',
                QtGui.QPalette.Midlight: 'beige',
                QtGui.QPalette.Mid: 'gray',
                QtGui.QPalette.Dark: 'iron',
                QtGui.QPalette.Shadow: 'brown',
                QtGui.QPalette.Highlight: 'red',
                QtGui.QPalette.HighlightedText: 'white',
                # These work on linux only?
                QtGui.QPalette.ToolTipBase: 'beige',
                QtGui.QPalette.ToolTipText: 'brown',
                # These seem bugged anyway
                QtGui.QPalette.BrightText: 'green',
                QtGui.QPalette.Link: 'green',
                QtGui.QPalette.LinkVisited: 'green',
                },
            QtGui.QPalette.Disabled: {
                QtGui.QPalette.Window: 'light',
                QtGui.QPalette.WindowText: 'iron',
                QtGui.QPalette.Base: 'white',
                QtGui.QPalette.AlternateBase: 'light',
                QtGui.QPalette.PlaceholderText: 'green',
                QtGui.QPalette.Text: 'iron',
                QtGui.QPalette.Button: 'light',
                QtGui.QPalette.ButtonText: 'gray',
                QtGui.QPalette.Light: 'white',
                QtGui.QPalette.Midlight: 'beige',
                QtGui.QPalette.Mid: 'gray',
                QtGui.QPalette.Dark: 'iron',
                QtGui.QPalette.Shadow: 'brown',
                QtGui.QPalette.Highlight: 'pink',
                QtGui.QPalette.HighlightedText: 'white',
                # These seem bugged anyway
                QtGui.QPalette.BrightText: 'green',
                QtGui.QPalette.ToolTipBase: 'green',
                QtGui.QPalette.ToolTipText: 'green',
                QtGui.QPalette.Link: 'green',
                QtGui.QPalette.LinkVisited: 'green',
                },
            }
        scheme[QtGui.QPalette.Inactive] = scheme[QtGui.QPalette.Active]
        for group in scheme:
            for role in scheme[group]:
                palette.setColor(group, role,
                    QtGui.QColor(color[scheme[group][role]]))
        QtGui.QGuiApplication.setPalette(palette)

        self.colormap = {
            widgets.VectorIcon.Normal: {
                '#000': color['black'],
                '#f00': color['red'],
                },
            widgets.VectorIcon.Disabled: {
                '#000': color['gray'],
                '#f00': color['orange'],
                },
            }
        self.colormap_icon =  {
            '#000': color['black'],
            '#ff0000': color['red'],
            '#ffa500': color['pink'],
            }
        self.colormap_icon_light =  {
            '#000': color['iron'],
            '#ff0000': color['red'],
            '#ffa500': color['pink'],
            }
        self.colormap_graph =  {
            'abgd': {
                'black':   color['black'],
                '#D82424': color['red'],
                '#EBE448': color['gray'],
                },
            'disthist': {
                'black':   color['black'],
                '#EBE448': color['beige'],
                },
            'rank': {
                'black':   color['black'],
                '#D82424': color['red'],
                },
            }

    def draw(self):
        """Draw all widgets"""

        self.header = widgets.Header()
        self.header.logoTool = widgets.VectorPixmap(':/resources/logo-pyr8s.svg',
            colormap=self.colormap_icon)
        self.header.logoProject = QtGui.QPixmap(':/resources/itaxotools-micrologo.png')
        self.header.description = (
            'Pyr8s - Computing timetrees' + '\n'
            'using non-parametric rate-smoothing'
            )
        self.header.citation = (
            'Pyr8s code by Stefanos Patmanidis' + '\n'
            'Based on r8s written by Mike Sanderson'
        )

        self.line = widgets.Subheader()

        self.line.icon = QtWidgets.QLabel()
        self.line.icon.setPixmap(widgets.VectorPixmap(':/resources/arrow-right.svg',
            colormap=self.colormap_icon_light))
        self.line.icon.setStyleSheet('border-style: none;')

        self.labelTree = QtWidgets.QLabel("Open a file to begin")
        self.labelTree.setStyleSheet("""
            QLabel {
                color: palette(Shadow);
                font-size: 14px;
                letter-spacing: 1px;
                padding: 2px 4px 2px 4px;
                border: none;
                }
            """)
        self.labelTree.setAlignment(QtCore.Qt.AlignCenter)
        self.labelTree.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

        def search(what):
            self.treeConstraints.searchSelect(what)
            self.treeResults.searchSelect(what)
        self.searchWidget = widgets.SearchWidget()
        pixmap = widgets.VectorPixmap(':/resources/search.svg',
            colormap=self.colormap_icon_light)
        self.searchWidget.setSearchAction(pixmap, search)
        layout = QtWidgets.QHBoxLayout()
        layout.addSpacing(4)
        layout.addWidget(self.line.icon)
        layout.addSpacing(2)
        layout.addWidget(self.labelTree)
        layout.addSpacing(14)
        layout.addStretch(1)
        layout.addWidget(self.searchWidget)
        layout.addSpacing(8)
        layout.setContentsMargins(4, 4, 4, 4)
        self.line.setLayout(layout)

        self.leftPane = self.createPaneEdit()
        self.rightPane  = self.createPaneResults()

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.leftPane)
        self.splitter.addWidget(self.rightPane)
        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setCollapsible(0,False)
        self.splitter.setCollapsible(1,False)
        self.splitter.setStyleSheet("QSplitter::handle { height: 8px; }")
        self.splitter.setContentsMargins(8, 4, 8, 4)

        layoutFlags = QtWidgets.QHBoxLayout()
        layoutFlags.addWidget(self.labelFlagInfo)
        layoutFlags.addWidget(self.labelFlagWarn)
        self.barFlags = QtWidgets.QGroupBox()
        self.barFlags.setObjectName('barFlags')
        self.barFlags.setLayout(layoutFlags)
        self.barFlags.setStyleSheet("""
            QGroupBox {
                color: palette(Shadow);
                background: palette(Window);
                border-top: 1px solid palette(Mid);
                padding: 5px 10px 5px 10px;
                }
            QGroupBox:disabled {
                color: palette(Mid);
                background: palette(Window);
                border-top: 1px solid palette(Mid);
                }
            """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.header, 0)
        layout.addWidget(self.line, 0)
        layout.addSpacing(8)
        layout.addWidget(self.splitter, 1)
        layout.addSpacing(8)
        layout.addWidget(self.barFlags, 0)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def act(self):
        """Populate dialog actions"""

        self.actionOpen = QtWidgets.QAction('&Open', self)
        self.actionOpen.setIcon(widgets.VectorIcon(':/resources/open.svg', self.colormap))
        self.actionOpen.setShortcut(QtGui.QKeySequence.Open)
        self.actionOpen.setStatusTip('Open an existing file')
        self.actionOpen.triggered.connect(self.handleOpen)

        self.actionSave = QtWidgets.QAction('&Save', self)
        self.actionSave.setIcon(widgets.VectorIcon(':/resources/save.svg', self.colormap))
        self.actionSave.setShortcut(QtGui.QKeySequence.Save)
        self.actionSave.setStatusTip('Save analysis state')
        self.actionSave.triggered.connect(self.handleSaveAnalysis)

        self.actionRun = QtWidgets.QAction('&Run', self)
        self.actionRun.setIcon(widgets.VectorIcon(':/resources/run.svg', self.colormap))
        self.actionRun.setShortcut('Ctrl+R')
        self.actionRun.setStatusTip('Run rate analysis')
        self.actionRun.triggered.connect(self.handleRun)

        self.actionStop = QtWidgets.QAction('&Stop', self)
        self.actionStop.setIcon(widgets.VectorIcon(':/resources/stop.svg', self.colormap))
        self.actionStop.setStatusTip('Cancel analysis')
        self.actionStop.triggered.connect(self.handleCancel)

        self.actionExport = QtWidgets.QAction('&Export', self)
        self.actionExport.setIcon(widgets.VectorIcon(':/resources/export.svg', self.colormap))
        self.actionExport.setStatusTip('Export results')

        self.actionExportChrono = QtWidgets.QAction('&Chronogram', self)
        self.actionExportChrono.setShortcut('Ctrl+E')
        self.actionExportChrono.setStatusTip('Export chronogram (ultrametric)')
        self.actionExportChrono.triggered.connect(self.handleExportChrono)

        self.actionExportRato = QtWidgets.QAction('&Ratogram', self)
        self.actionExportRato.setStatusTip('Export ratogram')
        self.actionExportRato.triggered.connect(self.handleExportRato)

        self.actionExportTable = QtWidgets.QAction('&Table', self)
        self.actionExportTable.setStatusTip('Export ages and rates table')
        self.actionExportTable.triggered.connect(self.handleExportTable)

        exportButton = QtWidgets.QToolButton(self)
        exportButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        exportButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        exportMenu = QtWidgets.QMenu(exportButton)
        exportMenu.addAction(self.actionExportChrono)
        exportMenu.addAction(self.actionExportRato)
        exportMenu.addAction(self.actionExportTable)
        exportButton.setDefaultAction(self.actionExport)
        exportButton.setMenu(exportMenu)

        self.header.toolbar.addAction(self.actionOpen)
        self.header.toolbar.addAction(self.actionSave)
        self.header.toolbar.addWidget(exportButton)
        self.header.toolbar.addAction(self.actionRun)
        self.header.toolbar.addAction(self.actionStop)

    def createTabConstraints(self):
        tab = QtWidgets.QWidget()

        self.treeConstraints = widgets.TreeWidgetPhylogenetic()
        self.treeConstraints.onSelect = (lambda data:
            self.treeResults.searchSelect(data[0],
                flag=QtCore.Qt.MatchExactly))
        self.treeConstraints.setColumnCount(4)
        self.treeConstraints.setAlternatingRowColors(True)
        self.treeConstraints.setHeaderLabels(['Taxon', 'Min', 'Max', 'Fix'])
        headerItem = self.treeConstraints.headerItem()
        headerItem.setTextAlignment(0, QtCore.Qt.AlignLeft)
        headerItem.setTextAlignment(1, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(2, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(3, QtCore.Qt.AlignCenter)
        self.treeConstraints.installEventFilter(self)

        #! BUGGED, should be fixed and restored
        # self.treeConstraints.itemChanged.connect(
            # lambda i, c: self.machine.postEvent(utility.NamedEvent('UPDATE')))

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.treeConstraints)
        tab.setLayout(layout)

        return tab

    def createTabParams(self):
        tab = QtWidgets.QWidget()
        self.paramWidget = param_qt.ParamContainer(self.analysis.param)
        self.paramWidget.paramChanged.connect(
            lambda e: self.machine.postEvent(utility.NamedEvent('UPDATE')))

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.paramWidget)
        tab.setLayout(layout)

        return tab

    def createPaneEdit(self):
        pane = QtWidgets.QWidget()

        self.tabContainerAnalysis = QtWidgets.QTabWidget()

        self.tabConstraints = self.createTabConstraints()
        self.tabParams = self.createTabParams()
        self.tabContainerAnalysis.addTab(self.tabConstraints, "&Constraints")
        self.tabContainerAnalysis.addTab(self.tabParams, "&Parameters")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabContainerAnalysis)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane

    def createTabResults(self):
        tab = QtWidgets.QWidget()

        self.treeResults = widgets.TreeWidgetPhylogenetic()
        self.treeResults.onSelect = (lambda data:
            self.treeConstraints.searchSelect(data[0],
            flag=QtCore.Qt.MatchExactly))
        self.treeResults.setColumnCount(3)
        self.treeResults.setAlternatingRowColors(True)
        self.treeResults.setHeaderLabels(['Taxon', 'Age', 'Rate', 'C'])
        headerItem = self.treeResults.headerItem()
        headerItem.setTextAlignment(0, QtCore.Qt.AlignLeft)
        headerItem.setTextAlignment(1, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(2, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(3, QtCore.Qt.AlignCenter)
        self.treeResults.installEventFilter(self)
        self.treeResults.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.treeResults)
        tab.setLayout(layout)

        return tab

    def createTabTable(self):
        tab = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # layout.addWidget(paramWidget)
        tab.setLayout(layout)

        return tab

    def createTabLogs(self):
        tab = QtWidgets.QWidget()

        logWidget = utility.TextEditLogger()
        fixedFont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        logWidget.setFont(fixedFont)
        # logWidget.handler.setFormatter(
        #     logging.Formatter(
        #         '%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s'))
        logging.getLogger().addHandler(logWidget.handler)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(logWidget)
        layout.setContentsMargins(5, 5, 5, 5)
        tab.setLayout(layout)

        return tab

    def createPaneResults(self):
        pane = QtWidgets.QWidget()

        self.tabContainerResults = QtWidgets.QTabWidget()

        self.tabResults = self.createTabResults()
        self.tabDiagram = self.createTabTable()
        self.tabTable = self.createTabTable()
        self.tabLogs = self.createTabLogs()
        self.tabContainerResults.addTab(self.tabResults, "&Results")
        # self.tabContainerResults.addTab(self.tabDiagram , "&Diagram")
        # self.tabContainerResults.addTab(self.tabTable, "&Table")
        self.tabContainerResults.addTab(self.tabLogs, "&Logs")

        self.labelFlagInfo = QtWidgets.QLabel('No results to display.')
        self.labelFlagInfo.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFlagWarn = QtWidgets.QLabel('All seems good.')
        self.labelFlagWarn.setAlignment(QtCore.Qt.AlignCenter)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabContainerResults)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane

    def handleRunWork(self):
        """Runs on the UProcess, defined here for pickability"""
        self.analysis.run()
        return self.analysis.results

    def handleRun(self):
        """Called by Run button"""
        try:
            self.paramWidget.applyParams()
        except Exception as exception:
            self.fail(exception)
            return

        if self.analysis.param.general.scalar:
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle(self.windowTitle())
            msgBox.setIcon(QtWidgets.QMessageBox.Question)
            msgBox.setText('Scalar mode activated, all time constraints will be ignored.')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            confirm = msgBox.exec()
            if confirm == QtWidgets.QMessageBox.Cancel:
                return

        def done(result):
            with utility.StdioLogger():
                result.print()
                print(result.chronogram.as_string(schema='newick'))
            self.analysis.results = result
            self.machine.postEvent(utility.NamedEvent('DONE', True))

        def fail(exception):
            self.machine.postEvent(utility.NamedEvent('FAIL', exception))

        self.launcher = utility.UProcess(self.handleRunWork)
        self.launcher.done.connect(done)
        self.launcher.fail.connect(fail)
        self.launcher.setLogger(logging.getLogger())
        self.launcher.start()
        self.machine.postEvent(utility.NamedEvent('RUN'))

    def handleCancel(self):
        """Called by cancel button"""
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText('Cancel ongoing analysis?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        confirm = msgBox.exec()
        if confirm == QtWidgets.QMessageBox.Yes:
            logging.getLogger().info('\nAnalysis aborted by user.')
            self.launcher.quit()
            self.machine.postEvent(utility.NamedEvent('CANCEL'))

    def handleOpen(self):
        """Called by toolbar action"""
        (fileName, _) = QtWidgets.QFileDialog.getOpenFileName(self,
            'pyr8s - Open File',
            QtCore.QDir.currentPath(),
            'All Files (*) ;; Newick (*.nwk) ;; Rates Analysis (*.r8s)')
        if len(fileName) == 0:
            return
        suffix = QtCore.QFileInfo(fileName).suffix()
        if suffix == 'r8s':
            self.handleOpenAnalysis(fileName)
        else:
            self.handleOpenFile(fileName)

    def handleOpenAnalysis(self, fileName):
        """Open pickled analysis"""
        #! THIS IS UNSAFE: Only open trusted files
        try:
            with open(fileName, 'rb') as file:
                obj = pickle.load(file)
                if obj.__class__ != core.RateAnalysis:
                    raise ValueError('Not a valid Analysis file.')
                self.analysis = obj
                self.paramWidget.setParams(self.analysis.param)
                self.machine.postEvent(utility.NamedEvent('OPEN',file=fileName))
        except Exception as exception:
            self.fail(exception)
        else:
            logging.getLogger().info(
                'Loaded analysis from: {}\n'.format(fileName))

    def handleOpenFile(self, fileName):
        """Load tree from a newick or nexus file"""
        try:
            with utility.StdioLogger():
                self.analysis = parse.from_file(fileName)
            self.paramWidget.setParams(self.analysis.param)
        except Exception as exception:
            self.fail(exception)
        else:
            logging.getLogger().info(
                'Loaded tree from: {}\n'.format(fileName))
            self.machine.postEvent(utility.NamedEvent('OPEN',file=fileName))

    def handleSaveAnalysis(self):
        """Pickle and save current analysis"""
        (fileName, _) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Save Analysis',
            QtCore.QDir.currentPath() + '/' + self.analysis.tree.label + '.r8s',
            'Rates Analysis (*.r8s)')
        if len(fileName) == 0:
            return
        try:
            self.paramWidget.applyParams()
            with open(fileName, 'wb') as file:
                pickle.dump(self.analysis, file)
        except Exception as exception:
            self.fail(exception)
        else:
            logging.getLogger().info(
                'Saved analysis to file: {}\n'.format(fileName))
        pass

    def handleExportChrono(self):
        """Called by toolbar menu button"""
        (fileName, _) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Export Chronogram',
            QtCore.QDir.currentPath() + '/' + self.analysis.tree.label + '_chronogram.nwk',
            'Newick (*.nwk);;  All files (*.*)')
        if len(fileName) == 0:
            return
        try:
            with open(fileName, 'w') as file:
                file.write(self.analysis.results.chronogram.
                    as_string(schema='newick'))
        except Exception as exception:
            self.fail(exception)
        else:
            logging.getLogger().info(
                'Exported chronogram to file: {}\n'.format(fileName))

    def handleExportRato(self):
        """Called by toolbar menu button"""
        (fileName, _) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Export Ratogram',
            QtCore.QDir.currentPath() + '/' + self.analysis.tree.label + '_ratogram.nwk',
            'Newick (*.nwk);;  All files (*.*)')
        if len(fileName) == 0:
            return
        try:
            with open(fileName, 'w') as file:
                file.write(self.analysis.results.ratogram.
                    as_string(schema='newick'))
        except Exception as exception:
            self.fail(exception)
        else:
            logging.getLogger().info(
                'Exported ratogram to file: {}\n'.format(fileName))

    def handleExportTable(self):
        """Called by toolbar menu button"""
        (fileName, _) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Export Table',
            QtCore.QDir.currentPath() + '/' + self.analysis.tree.label + '_rates.tsv',
            'Tab Separated Values (*.tsv);;  All files (*.*)')
        if len(fileName) == 0:
            return
        try:
            with open(fileName, 'w') as file:
                table = self.analysis.results.table
                for i in range(table['n']):
                    file.write(str(table['Node'][i]) + '\t')
                    file.write(str(table['Age'][i]) + '\t')
                    file.write(str(table['Rate'][i]) + '\n')
        except Exception as exception:
            self.fail(exception)
        else:
            logging.getLogger().info(
                'Exported table to file: {}\n'.format(fileName))

def show():
    """Entry point"""
    def init():
        if len(sys.argv) >= 2:
            main.handleOpenFile(sys.argv[1])

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    main = Main(init=init)
    main.setWindowFlags(QtCore.Qt.Window)
    main.setModal(True)
    main.show()
    sys.exit(app.exec_())
