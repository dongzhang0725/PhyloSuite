#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt5 import QtGui, QtCore
import re


class Find(QtGui.QDialog):
    def __init__(self, parent=None, target=None, sig=None):

        QtGui.QDialog.__init__(self, parent)

        self.parent = parent

        self.lastMatch = None

        self.target = target

        self.findSig = sig
        #如果传入了要匹配的目标，就直接执行find
        if self.target:
            self.find()
        else:
            self.initUI()

    def initUI(self):

        # Button to search the document for something
        findButton = QtGui.QPushButton("Find", self)
        findButton.clicked.connect(self.find)

        # Button to replace the last finding
        replaceButton = QtGui.QPushButton("Replace", self)
        replaceButton.clicked.connect(self.replace)

        # Button to remove all findings
        allButton = QtGui.QPushButton("Replace all", self)
        allButton.clicked.connect(self.replaceAll)

        # Normal mode - radio button
        self.normalRadio = QtGui.QRadioButton("Normal", self)
        self.normalRadio.toggled.connect(self.normalMode)

        # Regular Expression Mode - radio button
        self.regexRadio = QtGui.QRadioButton("RegEx", self)
        self.regexRadio.toggled.connect(self.regexMode)

        # The field into which to type the query
        self.findField = QtGui.QTextEdit(self)
        self.findField.resize(250, 50)

        # The field into which to type the text to replace the
        # queried text
        self.replaceField = QtGui.QTextEdit(self)
        self.replaceField.resize(250, 50)

        optionsLabel = QtGui.QLabel("Options: ", self)

        # Case Sensitivity option
        self.caseSens = QtGui.QCheckBox("Case sensitive", self)

        # Whole Words option
        self.wholeWords = QtGui.QCheckBox("Whole words", self)

        # Layout the objects on the screen
        layout = QtGui.QGridLayout()

        layout.addWidget(self.findField, 1, 0, 1, 4)
        layout.addWidget(self.normalRadio, 2, 2)
        layout.addWidget(self.regexRadio, 2, 3)
        layout.addWidget(findButton, 2, 0, 1, 2)

        layout.addWidget(self.replaceField, 3, 0, 1, 4)
        layout.addWidget(replaceButton, 4, 0, 1, 2)
        layout.addWidget(allButton, 4, 2, 1, 2)

        # Add some spacing
        spacer = QtGui.QWidget(self)

        spacer.setFixedSize(0, 10)

        layout.addWidget(spacer, 5, 0)

        layout.addWidget(optionsLabel, 6, 0)
        layout.addWidget(self.caseSens, 6, 1)
        layout.addWidget(self.wholeWords, 6, 2)

        self.setGeometry(300, 300, 360, 250)
        self.setWindowTitle("Find and Replace")
        self.setLayout(layout)

        # By default the normal mode is activated
        self.normalRadio.setChecked(True)

    def find(self):

        # Grab the parent's text
        text = self.parent.toPlainText()

        # And the text to find
        query = self.findField.toPlainText() if self.target is None else self.target

        # If the 'Whole Words' checkbox is checked, we need to append
        # and prepend a non-alphanumeric character
        if self.target is None:
            if self.wholeWords.isChecked():
                query = r'\W' + query + r'\W'

        # By default regexes are case sensitive but usually a search isn't
        # case sensitive by default, so we need to switch this around here
        if self.target is None:
            flags = 0 if self.caseSens.isChecked() else re.I
        else:
            flags = 0
            for i in "[]*.?+$^(){}|\/":
                query = query.replace(i, "[" + i + "]")

        # Compile the pattern
        pattern = re.compile(query, flags)

        # If the last match was successful, start at position after the last
        # match's start, else at 0
        start = self.lastMatch.start() + 1 if self.lastMatch else 0

        # The actual search
        self.lastMatch = pattern.search(text, start)

        if self.lastMatch:

            start = self.lastMatch.start()
            end = self.lastMatch.end()

            # If 'Whole words' is checked, the selection would include the two
            # non-alphanumeric characters we included in the search, which need
            # to be removed before marking them.
            if self.target is None:
                if self.wholeWords.isChecked():
                    start += 1
                    end -= 1

            self.moveCursor(start, end)

        else:
            if self.findSig is None:
                # We set the cursor to the end if the search was unsuccessful
                self.parent.moveCursor(QtGui.QTextCursor.End)
            else:
                self.findSig.emit()

    def replace(self):

        # Grab the text cursor
        cursor = self.parent.textCursor()

        # Security
        if self.lastMatch and cursor.hasSelection():

            # We insert the new text, which will override the selected
            # text
            cursor.insertText(self.replaceField.toPlainText())

            # And set the new cursor
            self.parent.setTextCursor(cursor)

    def replaceAll(self):

        # Set lastMatch to None so that the search
        # starts from the beginning of the document
        self.lastMatch = None

        # Initial find() call so that lastMatch is
        # potentially not None anymore
        self.find()

        # Replace and find until find is None again
        while self.lastMatch:
            self.replace()
            self.find()

    def regexMode(self):

        # First uncheck the checkboxes
        self.caseSens.setChecked(False)
        self.wholeWords.setChecked(False)

        # Then disable them (gray them out)
        self.caseSens.setEnabled(False)
        self.wholeWords.setEnabled(False)

    def normalMode(self):

        # Enable checkboxes (un-gray them)
        self.caseSens.setEnabled(True)
        self.wholeWords.setEnabled(True)

    def moveCursor(self, start, end):

        # We retrieve the QTextCursor object from the parent's QTextEdit
        cursor = self.parent.textCursor()
        # 先把目标位置顶到中间，对waring效果不好
        # cursor.setPosition(start+1000)
        # self.parent.setTextCursor(cursor)

        # Then we set the position to the beginning of the last match
        cursor.setPosition(start)

        # Next we move the Cursor by over the match and pass the KeepAnchor parameter
        # which will make the cursor select the the match's text
        cursor.movePosition(
            QtGui.QTextCursor.Right,
            QtGui.QTextCursor.KeepAnchor,
            end - start)

        # And finally we set this new cursor as the parent's
        self.parent.setTextCursor(cursor)

