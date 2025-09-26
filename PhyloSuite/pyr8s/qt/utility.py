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


"""Utility functions for PyQt5"""

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui

import logging
import sys, os, io
import multiprocessing

##############################################################################
### Logging

class StdioLogger():
    """Redirect system stdout and stderr to logger"""
    def __init__(self, logger=None):
        if logger is None:
            logger = logging.getLogger()
        self.logger = logger

    def __enter__(self):
        self.err = sys.stderr.write
        self.out = sys.stdout.write
        sys.stderr.write = self.logger.error
        sys.stdout.write = self.logger.info

    def __exit__(self, et, ev, tr):
        sys.stderr.write = self.err
        sys.stdout.write = self.out

class PipeIO(io.IOBase):
    """File-like object that writes to a pipe connection"""
    #? There are possibly better waiys to do this
    #? Todo- implement read
    def __init__(self, connection, mode):
        super().__init__()
        self._pid = os.getpid()
        self._cache = ''
        self.connection = connection
        self.buffer = ''
        if not (mode == 'r' or mode == 'w'):
            raise ValueError("Invalid mode: '{}'".format(str(mode)))
        self.mode = mode

    @property
    def cache(self):
        """Fork-safe, discard cache, from multiprocessing doc"""
        pid = os.getpid()
        if pid != self._pid:
            self._pid = pid
            self._cache = ''
        return self._cache

    @cache.setter
    def cache(self, value):
        self._cache = value

    def close(self):
        self.flush()
        self.connection.close()
        self.closed = True

    def fileno(self):
        return self.connection.fileno()

    def readable(self):
        return self.mode == 'r'

    def read(self, size=-1):
        if not self.readable():
            raise io.UnsupportedOperation('not readable')
        if size < 0:
            if self.cache == '':
                self.cache = self.connection.recv()
            result = self.cache
            self.cache = ''
            return result
        while len(self.cache) < size:
            self.cache += self.connection.recv()
        result = self.cache[:size]
        self.cache = self.cache[size:]
        return result

    # To do if required:
    # def readline(size=-1):
    #     pass
    # def readlines(hint=-1):
    #     pass

    def writable(self):
        return self.mode == 'w'

    def write(self, text):
        if not self.writable():
            raise io.UnsupportedOperation('not writable')
        temp = self.buffer + text
        self.buffer = ''
        for line in temp.splitlines(True):
            if line[-1] == '\n':
                self.connection.send(line)
            else:
                self.buffer += line

    def writelines(self, lines):
        for line in lines:
            self.connection.send(line+'\n')

    def flush(self):
        if self.buffer != '':
            self.connection.send(self.buffer)
        self.buffer = ''

class TextEditLogger(QtWidgets.QPlainTextEdit):
    """Thread-safe log display in a QPlainTextEdit"""
    appendRecord = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.handler = logging.Handler()
        self.handler.emit = self.emit
        self.appendRecord.connect(self.appendTextInline)

    def appendTextInline(self, text):
        self.moveCursor(QtGui.QTextCursor.End);
        self.insertPlainText(text);
        self.moveCursor(QtGui.QTextCursor.End);

    def emit(self, record):
        text = self.handler.format(record)
        self.appendRecord.emit(text)

##############################################################################
### Multiprocessing

class UThread(QtCore.QThread):
    """
    Multithreaded function execution using PyQt5.
    Initialise with the function and parameters for execution.
    Signals are used to communicate with parent thread.
    Use self.start() to fork/spawn.

    Signals:
    ----------
    started():
        Inherited. Emitted on start.
    finished():
        Inherited. Emitted on finish, regardless of success.
    done(result):
        Emitted when the called function returned successfully.
        Passes the result.
    fail(exception):
        Emitted if an exception occured. Passes the exception.
    """
    done = QtCore.pyqtSignal(object)
    fail = QtCore.pyqtSignal(object)

    def __init__(self, function, *args, **kwargs):
        """
        Parameters
        ----------
        function : function
            The function to run on the new thread.
        \*args : positional argument, optional
            If given, it is passed on to the function.
        \*\*kwargs : keyword arguments, optional
            If given, it is passed on to the function.
        """
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        # self.kwargs['thread'] = self

    def run(self):
        """
        Overloads QThread. This is run on a new thread.
        Do not call this directly, call self.start() instead.
        """
        try:
            result = self.function(*self.args, **self.kwargs)
        except Exception as exception:
            self.fail.emit(exception)
        else:
            self.done.emit(result)


class UProcess(QtCore.QThread):
    """
    Multiprocess function execution using PyQt5.
    Unlike QtCore.QProcess, this launches python functions, not programs.
    Use self.start() to fork/spawn.

    Example
    ----------

    def work(number):
        print('This runs on the child process.')
        print('Trying to use PyQt in here won\'t work.')
        return number * 2

    def success(result):
        print('This runs on the parent process.')
        print('You can spawn dialog messages here.')
        QMessageBox.information(None, 'Success',
            'Result = '+str(result), QMessageBox.Ok)
        print('This prints 42: ', result)

    self.process = UProcess(work, 21)
    self.process.done.connect(success)
    self.process.start()
    return

    """
    done = QtCore.pyqtSignal(object)
    fail = QtCore.pyqtSignal(object)

    def __getstate__(self):
        """Required for process spawning."""
        state = self.__dict__.copy()
        state['logger'] = None
        state['handleOut'] = self._loggerNone
        state['handleErr'] = self._loggerNone
        return state

    def __setstate__(self, state):
        """Required for process spawning."""
        # super(UProcess, self).__init__(None)
        self.__dict__ = state
        return

    def __init__(self, function, *args, **kwargs):
        """
        Parameters
        ----------
        function : function
            The function to run on the new process.
        *args : positional argument, optional
            If given, it is passed on to the function.
        **kwargs : keyword arguments, optional
            If given, it is passed on to the function.
        """
        super().__init__()
        self.logger = None
        self.pipeControl = multiprocessing.Pipe(duplex=True)
        self.pipeData = multiprocessing.Pipe(duplex=True)
        self.pipeOut = multiprocessing.Pipe(duplex=False)
        self.pipeErr = multiprocessing.Pipe(duplex=False)
        self.pipeIn = multiprocessing.Pipe(duplex=False)
        self.process = multiprocessing.Process(
            target=self.target, daemon=True,
            args=(function,)+args, kwargs=kwargs)

    def setLogger(self, logger):
        """Send process output to given logger"""
        self.logger = logger
        # return
        if logger is not None:
            self.handleOut = self._loggerOut
            self.handleErr = self._loggerErr
        else:
            self.handleOut = self._loggerNone
            self.handleErr = self._loggerNone

    def _loggerNone(self, data):
        pass

    def _loggerOut(self, data):
        self.logger.info(data)

    def _loggerErr(self, data):
        self.logger.error(data)

    def target(self, function, *args, **kwargs):
        """
        This is executed as a new process.
        Alerts parent process via pipe.
        """
        self.pipeIn[1].close()
        self.pipeControl = self.pipeControl[1]
        self.pipeData = self.pipeData[1]
        self.pipeOut = self.pipeOut[1]
        self.pipeErr = self.pipeErr[1]
        self.pipeIn = self.pipeIn[0]

        out = PipeIO(self.pipeOut, 'w')
        err = PipeIO(self.pipeErr, 'w')
        inp = PipeIO(self.pipeIn, 'r')

        # import sys
        sys.stdout = out
        sys.stderr = err
        sys.stdin = inp

        print('PROCESS STDIO CONFIGURED SUCCESSFULLY')

        try:
            result = function(*args, **kwargs)
            self.pipeControl.send('RESULT')
            self.pipeData.send(result)
        except Exception as exception:
            self.pipeControl.send('EXCEPTION')
            self.pipeData.send(exception)

    def run(self):
        """
        Overloads QThread. This is run on a new thread.
        Do not call this directly, call self.start() instead.
        Starts and watches the process.
        """
        self.process.start()
        self.pipeData[1].close()
        self.pipeOut[1].close()
        self.pipeErr[1].close()
        self.pipeControl = self.pipeControl[0]
        self.pipeData = self.pipeData[0]
        self.pipeOut = self.pipeOut[0]
        self.pipeErr = self.pipeErr[0]
        self.pipeIn = self.pipeIn[1]

        waitList = {
            self.pipeControl: self.handleControl,
            self.pipeOut: self.handleOut,
            self.pipeErr: self.handleErr,
            }
        while waitList:
            for pipe in multiprocessing.connection.wait(waitList.keys()):
                try:
                    data = pipe.recv()
                except EOFError:
                    waitList.pop(pipe)
                else:
                    waitList[pipe](data)
        # Nothing left to do
        return

    def handleControl(self, data):
        """Handle control pipe signals"""
        if data == 'RESULT':
            result = self.pipeData.recv()
            self.done.emit(result)
            self.process.join()
        elif data == 'EXCEPTION':
            exception = self.pipeData.recv()
            self.fail.emit(exception)
            self.process.join()

    def handleOut(self, data):
        """Overload this to handle process stdout"""
        pass

    def handleErr(self, data):
        """Overload this to handle process stderr"""
        pass

    def quit(self):
        """Clean exit"""
        self.process.terminate()
        super().quit()

##############################################################################
### States and Events

class NamedEvent(QtCore.QEvent):
    """Custom event for use in state machines"""
    userEvent = QtCore.QEvent.User + 1042
    def __init__(self, name, *args, **kwargs):
        """Pass name and args"""
        super().__init__(self.userEvent)
        self.name = name
        self.args = args
        self.kwargs = kwargs

class NamedTransition(QtCore.QAbstractTransition):
    """Custom transition for use in state machines"""
    def __init__(self, name):
        """Only catch events with given name"""
        super().__init__()
        self.name = name
    def eventTest(self, event):
        """Check for NamedEvents"""
        if event.type() == NamedEvent.userEvent:
            return event.name == self.name
        return False
    def onTransition(self, event):
        """Override virtual function"""
        pass
