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


"""Custom widgets for PyQt5"""

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui  as QtGui
import PyQt5.QtSvg  as QtSvg

import re

##############################################################################
### Phylogenetic Trees

class TreeWidgetPhylogenetic(QtWidgets.QTreeWidget):
    """Styled to draw the branches of phylogenetic trees."""
    def __init__(self):
        super().__init__()
        self._searchSelecting = False
        self.selectionModel().selectionChanged.connect(
            self._onSelectionChanged)
        # self.itemActivated.connect(self.editItem)
        palette = QtGui.QGuiApplication.palette()
        self.colorSolid = palette.color(QtGui.QPalette.Shadow)
        self.colorDisabled = palette.color(QtGui.QPalette.Midlight)
        self.colorSelected = palette.color(QtGui.QPalette.HighlightedText)
        self.colorAlter = palette.color(QtGui.QPalette.AlternateBase).lighter(105)
        self.radiusLeaf = 3
        self.radiusInternal = 5
        self.branchOffset = 1
        self.setIndentation(16)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(0,
            QtWidgets.QHeaderView.Stretch)
        # QtCore.QTimer.singleShot(0, lambda:
        #     self.header().setSectionResizeMode(0,
        #         QtWidgets.QHeaderView.Interactive))
        self.setUniformRowHeights(True)
        self.setStyleSheet(
            """
            QTreeView {
                show-decoration-selected: 1;
            }
            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: none;
            }
            QTreeView {
                alternate-background-color: """+self.colorAlter.name()+""";
            }
            QTreeView::item:selected:active,
            QTreeView::item:selected:!active,
            QTreeView::branch:selected:active,
            QTreeView::branch:selected:!active {
                color: """+self.colorSelected.name()+""";
                background: palette(Highlight);
            }
            QTreeView::branch:has-siblings:adjoins-item,
            QTreeView::branch:!has-children:!has-siblings:adjoins-item,
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings,
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings  {
                    border-image: none;
                    image: none;
            }
            """
            )


    # def scrollTo(self, index, hint):
    #     """Overloaded to prevent horizontal scroll on item select"""
    #     pass

    def setItemsDisabled(self, disable):
        """Disabled items but scrollbars remain enabled"""
        topItem = self.topLevelItem(0)
        if topItem is not None:
            topItem.setDisabled(disable)

    def idealWidth(self):
        """How much space is needed for all contents to be shown"""
        self.header().setSectionResizeMode(0,
            QtWidgets.QHeaderView.ResizeToContents)
        widthTree = self.viewportSizeHint().width()
        self.header().setSectionResizeMode(0,
            QtWidgets.QHeaderView.Stretch)
        # QtCore.QTimer.singleShot(0, lambda:
        #     self.header().setSectionResizeMode(0,
        #         QtWidgets.QHeaderView.Interactive))
        widthScrollbar = QtWidgets.qApp.style().pixelMetric(
            QtWidgets.QStyle.PM_ScrollBarExtent)
        widthPadding = 30
        return widthTree+widthScrollbar+widthPadding

    def _onSelectionChanged(self, selected, deselected):
        """Calls onSelect with selected data"""
        if not self._searchSelecting:
            data = {}
            for index in selected.indexes():
                data[index.column()] = index.data()
            if len(data) > 0:
                self.onSelect(data)

    def onSelect(self, data):
        """Overload to do something with selection"""
        pass

    def searchSelect(self, what, flag=QtCore.Qt.MatchContains):
        self._searchSelecting = True
        if what == '':
            self.clearSelection()
        else:
            self.clearSelection()
            found = self.findItems(what, flag | QtCore.Qt.MatchRecursive)
            for item in found:
                item.setSelected(True)
            if len(found) > 0:
                self.scrollToItem(found[-1])
        self._searchSelecting = False

    def drawBranches(self, painter, rect, index):
        """Manually paint branches and nodes"""
        super().drawBranches(painter, rect, index)

        rect.setRight(rect.right() + self.branchOffset)

        indent = self.indentation()
        item = self.itemFromIndex(index)

        color = None
        if item.isSelected():
            color = self.colorSelected
        elif item.isDisabled():
            color = self.colorDisabled
        else:
            color = self.colorSolid

        solidPen = QtGui.QPen(color)
        solidPen.setWidth(2)
        painter.setBrush(color)
        painter.setPen(solidPen)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        parent = item.parent()
        next = None
        if parent is not None:
            i = parent.indexOfChild(item)
            next = parent.child(i+1)
        child = item.child(0)

        isExpanded = item.isExpanded()
        hasChildren = child is not None
        hasMoreSiblings = next is not None

        # Paint own Node first
        segment = QtCore.QRect(rect)
        segment.setLeft(rect.right() - indent)
        if not hasChildren:
            radius = self.radiusLeaf
            center = segment.center()
            painter.drawEllipse(center, radius, radius)
            left = QtCore.QPoint(center.x()-int(segment.width()/2), center.y())
            leftMid = QtCore.QPoint(center.x()-radius, center.y())
            painter.drawLine(left, leftMid)
        else:
            radius = self.radiusInternal
            center = segment.center()
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawEllipse(center, radius, radius)
            if isExpanded:
                bottom = QtCore.QPoint(center.x(), int(center.y()+segment.height()/2+1))
                bottomMid = QtCore.QPoint(center.x(), center.y()+radius)
                painter.drawLine(bottom, bottomMid)
            else:
                painter.setBrush(color)
                painter.drawEllipse(center, 1, 1)
            if parent is None:
                return
            left = QtCore.QPoint(center.x()-int(segment.width()/2), center.y())
            leftMid = QtCore.QPoint(center.x()-radius, center.y())
            painter.drawLine(left, leftMid)

        # Branch towards direct parent
        segment.moveLeft(segment.left() - indent)
        if segment.right() < 0:
            return
        if hasMoreSiblings:
            center = segment.center()
            right = QtCore.QPoint(center.x()+int(segment.width()/2), center.y())
            painter.drawLine(center, right)
            top = QtCore.QPoint(center.x(), segment.top()+1)
            bottom = QtCore.QPoint(center.x(), segment.bottom()+1)
            painter.drawLine(top, bottom)
        else:
            center = segment.center()
            right = QtCore.QPoint(center.x()+int(segment.width()/2), center.y())
            painter.drawLine(center, right)
            top = QtCore.QPoint(center.x(), segment.top()+1)
            painter.drawLine(top, center)

        # Branch extensions for ancestors
        segment.moveLeft(segment.left() - indent)
        item = parent
        while parent is not None:
            if segment.right() < 0:
                return
            parent = item.parent()
            next = None
            if parent is not None:
                i = parent.indexOfChild(item)
                next = parent.child(i+1)
            hasMoreSiblings = next is not None
            if hasMoreSiblings:
                center = segment.center()
                top = QtCore.QPoint(center.x(), segment.top()+1)
                bottom = QtCore.QPoint(center.x(), segment.bottom()+1)
                painter.drawLine(top, bottom)
            segment.moveLeft(segment.left() - indent)
            item = parent


class TreeWidgetNodeResults(QtWidgets.QTreeWidgetItem):
    """Analysis results on an extended dendropy tree"""
    def __init__(self, parent, node):
        """
        Creates a widget from a dendropy node and adds it to the parent.
        Recursively creates children widgets from children nodes.
        """
        super().__init__(parent)
        self.node = node
        label = str(node.label)
        age = '-' if node.age is None else '{:>1.2f}'.format(node.age)
        rate = '-' if node.rate is None else '{:>1.2e}'.format(node.rate)
        if node.rate == 0:
            rate = ' 0.00e-00'
        isMinMax = node.min is not None or node.max is not None
        isFixed = node.fix is not None
        if isFixed:
            type = '\u2219'
        elif isMinMax:
            type = '\u2217'
        else:
            type = ' '
        self.setText(0, label)
        self.setText(1, age)
        self.setText(2, rate)
        self.setText(3, type)
        self.setTextAlignment(1, QtCore.Qt.AlignRight)
        self.setTextAlignment(2, QtCore.Qt.AlignRight)
        self.setTextAlignment(3, QtCore.Qt.AlignCenter)
        self.setFlags(QtCore.Qt.ItemIsSelectable |
                      QtCore.Qt.ItemIsEnabled |
                      QtCore.Qt.ItemIsEditable)
        for child in node.child_node_iter():
            TreeWidgetNodeResults(self, child)
        self.setExpanded(True)


class TreeWidgetNodeConstraints(QtWidgets.QTreeWidgetItem):
    """Constraints on an extended dendropy tree"""
    def __init__(self, parent, node):
        """
        Creates a widget from a dendropy node and adds it to the parent.
        Recursively creates children widgets from children nodes.
        Updates node when values are changed.
        """
        super().__init__(parent)
        self.node = node
        label = str(node.label)
        min = '-' if node.min is None else str(node.min)
        max = '-' if node.max is None else str(node.max)
        fix = '-' if node.fix is None else str(node.fix)
        self.setText(0, label)
        self.setText(1, min)
        self.setText(2, max)
        self.setText(3, fix)
        self.setTextAlignment(1, QtCore.Qt.AlignCenter)
        self.setTextAlignment(2, QtCore.Qt.AlignCenter)
        self.setTextAlignment(3, QtCore.Qt.AlignCenter)
        self.setFlags(QtCore.Qt.ItemIsSelectable |
                      QtCore.Qt.ItemIsEnabled |
                      QtCore.Qt.ItemIsEditable)
        for child in node.child_node_iter():
            TreeWidgetNodeConstraints(self, child)
        self.setExpanded(True)

    def showWarning(self, message):
        QtWidgets.QMessageBox.warning(None, 'Warning',
            message, QtWidgets.QMessageBox.Ok)

    def showException(self, message):
        print(message)
        QtWidgets.QMessageBox.critical(None, 'Error',
            message, QtWidgets.QMessageBox.Ok)

    def checkConstraints(self):
        if self.node.fix is not None:
            if self.node.min is not None or self.node.max is not None:
                self.showWarning('Min/Max constraints are ignored if node is Fixed.')
        if (self.node.min is not None and
            self.node.max is not None and
            self.node.min > self.node.max):
            self.showWarning('Impossible constraints: Min > Max.')

    def editFloat(self, value):
        if value == '' or value == '-':
            return (None, '-')
        value = float(value)
        label = str(int(value)) if value.is_integer() else str(value)
        return (value, label)

    def setNodeMin(self, value):
        (self.node.min, label) = self.editFloat(value)
        self.checkConstraints()
        return label

    def setNodeMax(self, value):
        (self.node.max, label) = self.editFloat(value)
        self.checkConstraints()
        return label

    def setNodeFix(self, value):
        (self.node.fix, label) = self.editFloat(value)
        self.checkConstraints()
        return label

    def setNodeLabel(self, value):
        indexString = self.node.decorator.format(self.node.index)
        if value == '' or value == indexString:
            self.node.label = ''
            return indexString
        if re.match('^[^,;()\[\]\r\n]*$', value) is None:
            raise ValueError('Label contains invalid characters.')
        self.node.label = value
        return value

    def setData(self, column, role, value):
        try:
            if role == QtCore.Qt.ItemDataRole.EditRole:
                if column == 0:
                    value = self.setNodeLabel(value)
                elif column == 1:
                    value = self.setNodeMin(value)
                elif column == 2:
                    value = self.setNodeMax(value)
                elif column == 3:
                    value = self.setNodeFix(value)
        except Exception as exception:
            self.showException('Error: ' + str(exception))
        else:
            super().setData(column, role, value)


##############################################################################
### Layout

class TabWidget(QtWidgets.QGroupBox):
    """Tab-like to be used as corner widget of QTabWidget"""
    def __init__(self, widget):
        """Add widget to self"""
        super().__init__()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setStyleSheet(
        """
        QGroupBox {
            border: 1px solid palette(dark);
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: 1ex;
            padding: 2px;
            margin: 0px;
        }
        QGroupBox:enabled  {
            background: palette(Light);
        }
        QGroupBox:!enabled  {
            background: palette(Window);
        }
        """)

class SearchWidget(QtWidgets.QLineEdit):
    """Embedded line edit with search button"""
    def setSearchAction(self, pixmap, function):
        """Icon is the path to a black solid image"""
        def search():
            function(self.text())

        searchAction = QtWidgets.QAction(QtGui.QIcon(pixmap), 'Search', self)
        searchAction.triggered.connect(search)
        self.returnPressed.connect(search)
        self.addAction(searchAction, QtWidgets.QLineEdit.TrailingPosition)


class SyncedWidget(QtWidgets.QWidget):
    """Sync height with other widgets"""
    syncSignal = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.myhint = 0
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.size().height() != event.oldSize().height():
            self.syncSignal.emit()

    def syncHandle(self):
        other = self.sender().height()
        # self.setMinimumHeight(other)
        self.myhint = other

    def minimumSizeHint(self):
        size = super().minimumSizeHint()
        height = max(self.myhint, size.height())
        size.setHeight(height)
        return size


    def sync(self, widget):
        self.syncSignal.connect(widget.syncHandle)
        widget.syncSignal.connect(self.syncHandle)

class UToolBar(QtWidgets.QToolBar, SyncedWidget):
    syncSignal = QtCore.pyqtSignal()
    pass

class UGroupBox(QtWidgets.QGroupBox, SyncedWidget):
    syncSignal = QtCore.pyqtSignal()
    pass

##############################################################################
### Vector Graphics

class VectorPixmap(QtGui.QPixmap):
    """A colored vector pixmap"""
    def __init__(self, fileName, size=None, colormap=None):
        """
        Load an SVG resource file and replace colors according to
        provided dictionary `colormap`. Only fill and stroke is replaced.
        Also scales the pixmap if a QSize is provided.
        """
        data = self.loadAndMap(fileName, colormap)

        renderer = QtSvg.QSvgRenderer(data)
        size = renderer.defaultSize() if size is None else size
        super().__init__(size)
        self.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(self)
        renderer.render(painter)
        painter.end()

    @staticmethod
    def loadAndMap(fileName, colormap):
        file = QtCore.QFile(fileName)
        if not file.open(QtCore.QIODevice.ReadOnly):
            raise FileNotFoundError('Vector resource not found: ' + fileName)
        text = file.readAll().data().decode()
        file.close()

        # old code that also checks prefixes
        # if colormap is not None:
        #     # match options fill|stroke followed by a key color
        #     regex = '(?P<prefix>(fill|stroke)\:)(?P<color>' + \
        #         '|'.join(map(re.escape, colormap.keys()))+')'
        #     # replace just the color according to colormap
        #     print(regex)
        #     text = re.sub(regex, lambda mo: mo.group('prefix') + colormap[mo.group('color')], text)

        if colormap is not None:
            regex = '(?P<color>' + '|'.join(map(re.escape, colormap.keys()))+')'
            text = re.sub(regex, lambda mo: colormap[mo.group('color')], text)

        return QtCore.QByteArray(text.encode())

class VectorIcon(QtGui.QIcon):
    """A colored vector icon"""
    def __init__(self, fileName, colormap_modes):
        """Create pixmaps with colormaps matching the dictionary modes"""
        super().__init__()
        for mode in colormap_modes.keys():
            self.addPixmap(VectorPixmap(fileName,colormap=colormap_modes[mode]), mode)

##############################################################################
### Helpful widgets

class VLineSeparator(QtWidgets.QFrame):
    """Vertical line separator"""
    def __init__(self, width=2):
        super().__init__()
        self.setFixedWidth(width)
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Plain)
        self.setStyleSheet("""
            background: palette(Mid);
            border: none;
            margin: 4px;
            """)

class ScalingImage(QtWidgets.QLabel):
    """Keep aspect ratio, width adjusts with height"""
    def __init__(self, pixmap=None):
        """Remember given pixmap and ratio"""
        super().__init__()
        self.setScaledContents(False)
        self._polished = False
        self._logo = None
        self._ratio = 0
        if pixmap is not None:
            self.logo = pixmap

    @property
    def logo(self):
        return self._logo

    @logo.setter
    def logo(self, logo):
        """Accepts logo as a new pixmap to show"""
        self._logo = logo
        self._ratio = logo.width()/logo.height()
        self._scale()

    def _scale(self):
        """Create new pixmap to match new sizes"""
        if self._logo is None:
            return
        h = self.height()
        w = h * self._ratio
        self.setPixmap(self._logo.scaled(int(w), int(h),
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def minimumSizeHint(self):
        return QtCore.QSize(1, 1)

    def sizeHint(self):
        if self._polished is True and self._ratio != 0:
            h = self.height()
            return QtCore.QSize(int(h * self._ratio), int(h))
        else:
            return QtCore.QSize(1, 1)

    def resizeEvent(self, event):
        self._scale()
        super().resizeEvent(event)

    def event(self, ev):
        """Let sizeHint know that sizes are now real"""
        if ev.type() == QtCore.QEvent.PolishRequest:
            self._polished = True
            self.updateGeometry()
        return super().event(ev)

##############################################################################
### Taxotool Layout

class Header(QtWidgets.QFrame):
    """
    The Taxotools toolbar, with space for a title, description,
    citations and two logos.
    """
    def __init__(self):
        """ """
        super().__init__()

        self._title = None
        self._description = None
        self._citation = None
        self._logoTool = None

        self.logoSize = 64

        self.draw()

    def draw(self):
        """ """
        self.setStyleSheet("""
            Header {
                background: palette(Light);
                border-top: 2px solid palette(Mid);
                border-bottom: 1px solid palette(Dark);
                }
            """)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)

        self.labelDescription = QtWidgets.QLabel('DESCRIPTION')
        self.labelDescription.setAlignment(QtCore.Qt.AlignBottom)
        self.labelDescription.setStyleSheet("""
            color: palette(Text);
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1px;
            """)

        self.labelCitation = QtWidgets.QLabel('CITATION')
        self.labelCitation.setAlignment(QtCore.Qt.AlignTop)
        self.labelCitation.setStyleSheet("""
            color: palette(Shadow);
            font-size: 12px;
            """)

        labels = QtWidgets.QVBoxLayout()
        labels.addWidget(self.labelDescription)
        labels.addWidget(self.labelCitation)
        labels.setSpacing(4)

        self.labelLogoTool = QtWidgets.QLabel()
        self.labelLogoTool.setAlignment(QtCore.Qt.AlignCenter)

        self.labelLogoProject = ScalingImage()
        layoutLogoProject = QtWidgets.QHBoxLayout()
        layoutLogoProject.addWidget(self.labelLogoProject)
        layoutLogoProject.setContentsMargins(2,4,2,4)

        self.toolbar = QtWidgets.QToolBar()
        self.toolbar.setIconSize(QtCore.QSize(32,32))
        self.toolbar.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.toolbar.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolbar.setStyleSheet("""
            QToolBar {
                spacing: 2px;
                }
            QToolButton {
                color: palette(ButtonText);
                background: transparent;
                border: 2px solid transparent;
                border-radius: 3px;
                font-size: 14px;
                min-width: 50px;
                min-height: 60px;
                padding: 6px 0px 0px 0px;
                margin: 4px 0px 4px 0px;
                }
            QToolButton:hover {
                background: palette(Window);
                border: 2px solid transparent;
                }
            QToolButton:pressed {
                background: palette(Midlight);
                border: 2px solid palette(Mid);
                border-radius: 3px;
                }
            QToolButton[popupMode="2"]:pressed {
                padding-bottom: 5px;
                border: 1px solid palette(Dark);
                margin: 5px 1px 0px 1px;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 0px;
                }
            QToolButton::menu-indicator {
                image: none;
                width: 30px;
                border-bottom: 2px solid palette(Mid);
                subcontrol-origin: padding;
                subcontrol-position: bottom;
                }
            QToolButton::menu-indicator:disabled {
                border-bottom: 2px solid palette(Midlight);
                }
            QToolButton::menu-indicator:pressed {
                border-bottom: 0px;
                }
            """)

        layout = QtWidgets.QHBoxLayout()
        layout.addSpacing(8)
        layout.addWidget(self.labelLogoTool)
        layout.addSpacing(2)
        layout.addWidget(VLineSeparator())
        layout.addSpacing(12)
        layout.addLayout(labels, 0)
        layout.addSpacing(12)
        layout.addWidget(VLineSeparator())
        layout.addSpacing(8)
        layout.addWidget(self.toolbar, 0)
        layout.addStretch(1)
        layout.addWidget(VLineSeparator())
        layout.addLayout(layoutLogoProject, 0)
        # layout.addWidget(self.labelLogoProject)
        layout.addSpacing(2)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        self.labelDescription.setText(description)
        self._description = description

    @property
    def citation(self):
        return self._citation

    @citation.setter
    def citation(self, citation):
        self.labelCitation.setText(citation)
        self._citation = citation

    @property
    def logoTool(self):
        return self._logoTool

    @logoTool.setter
    def logoTool(self, logo):
        self.labelLogoTool.setPixmap(logo)
        self._logoTool = logo

    @property
    def logoProject(self):
        return self.labelLogoProject.logo

    @logoProject.setter
    def logoProject(self, logo):
        self.labelLogoProject.logo = logo


class Subheader(QtWidgets.QFrame):
    """A simple styled frame"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        self.setStyleSheet("""
            QFrame {
                background-color: palette(Midlight);
                border-style: solid;
                border-width: 1px 0px 1px 0px;
                border-color: palette(Mid);
                }
            """)


class Panel(QtWidgets.QWidget):
    """
    A stylized panel with title, footer and body.
    Set `self.title`, `self.footer` and `self.flag` with text.
    Use `self.body.addWidget()`` to populate the pane.
    """
    def __init__(self, parent):
        """Initialize internal vars"""
        super().__init__(parent=parent)
        self._title = None
        self._foot = None
        self._flag = None
        self._flagTip = None

        # if not hasattr(parent, '_pane_foot_height'):
        #     parent._pane_foot_height = None
        self.draw()

    def draw(self):
        """ """
        self.labelTitle = QtWidgets.QLabel('TITLE GO HERE')
        self.labelTitle.setIndent(4)
        self.labelTitle.setMargin(2)
        self.labelTitle.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
                color: palette(Light);
                background: palette(Shadow);
                border-right: 1px solid palette(Dark);
                border-bottom: 2px solid palette(Dark);
                border-bottom-left-radius: 1px;
                border-top-right-radius: 1px;
                padding-top: 2px;
                }
            QLabel:disabled {
                background: palette(Mid);
                border-right: 1px solid palette(Midlight);
                border-bottom: 2px solid palette(Midlight);
                }
            """)

        self.labelFlag = QtWidgets.QLabel('')
        self.labelFlag.setVisible(False)
        self.labelFlag.setIndent(4)
        self.labelFlag.setMargin(2)
        self.labelFlag.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
                color: palette(Light);
                background: palette(Mid);
                border-right: 1px solid palette(Midlight);
                border-bottom: 2px solid palette(Midlight);
                border-bottom-left-radius: 1px;
                border-top-right-radius: 1px;
                padding-top: 1px;
                }
            QLabel:disabled {
                background: palette(Midlight);
                border-right: 1px solid palette(Light);
                border-bottom: 2px solid palette(Light);
                }
            """)

        # To be filled by user
        self.body = QtWidgets.QVBoxLayout()

        self.labelFoot = QtWidgets.QLabel('FOOTER')
        self.labelFoot.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFoot.setStyleSheet("""
            QLabel {
                color: palette(Shadow);
                background: palette(Window);
                border: 1px solid palette(Mid);
                padding: 5px 10px 5px 10px;
                }
            QLabel:disabled {
                color: palette(Mid);
                background: palette(Window);
                border: 1px solid palette(Mid);
                }
            """)


        layoutTop = QtWidgets.QHBoxLayout()
        layoutTop.addWidget(self.labelTitle, 1)
        layoutTop.addWidget(self.labelFlag, 0)
        layoutTop.setSpacing(4)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layoutTop, 0)
        layout.addLayout(self.body, 1)
        layout.addWidget(self.labelFoot, 0)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self.labelTitle.setText(title)
        self._title = title

    @property
    def flag(self):
        return self._flag

    @flag.setter
    def flag(self, flag):
        if flag is not None:
            self.labelFlag.setText(flag)
            self.labelFlag.setVisible(True)
        else:
            self.labelFlag.setVisible(False)
        self._flag = flag

    @property
    def flagTip(self):
        return self._flagTip

    @flagTip.setter
    def flagTip(self, flagTip):
        if flagTip is not None:
            self.labelFlag.setToolTip(flagTip)
        else:
            self.labelFlag.setToolTip('')
        self._flagTip = flagTip

    @property
    def footer(self):
        return self._foot

    @footer.setter
    def footer(self, footer):
        self.labelFoot.setText(footer)
        self._foot = footer

class ToolDialog(QtWidgets.QDialog):
    """
    For use as the main window of a tool.
    Handles notification sub-dialogs.
    Asks for verification before closing.
    """
    def reject(self):
        """Called on dialog close or <ESC>"""
        if self.onReject() is not None:
            return
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText('Are you sure you want to quit?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Yes)
        confirm = self.msgShow(msgBox)
        if confirm == QtWidgets.QMessageBox.Yes:
            super().reject()

    def onReject(self):
        """
        Overload this to handle reject events.
        Return None to continue with rejection, anything else to cancel.
        """
        return None

    def msgCloseAll(self):
        """Rejects any open QMessageBoxes"""
        for widget in self.children():
            if widget.__class__ == QtWidgets.QMessageBox:
                widget.reject()

    def msgShow(self, dialog):
        """Exec given QMessageBox after closing all others"""
        self.msgCloseAll()
        return dialog.exec()

    def fail(self, exception):
        """Show exception dialog"""
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setText('An exception occured:')
        msgBox.setInformativeText(str(exception))
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        self.msgShow(msgBox)
        logger = logging.getLogger()
        logger.error(str(exception))
