##################################################################
# This module manages video playing
#
##################################################################
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QThread,QObject,QMutex,QMutexLocker
import time


class VideoThread(QThread):

    def __init__(self, default_fps=25):
        QThread.__init__(self)
        self.stopped = False
        self.fps = default_fps
        self.timeSignal = Communicate()
        self.mutex = QMutex()

    def run(self):
        with QMutexLocker(self.mutex):
            self.stopped = False

        while True:
            if self.stopped:
                return
            self.timeSignal.signal.emit('1')
            time.sleep(1 / self.fps)

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, video_fps):
        self.fps = video_fps
        print(f'set fps to {self.fps}')

class Communicate(QObject):
    signal = pyqtSignal(str)

# class SecondWindow(QtWidgets.QMainWindow):
#     def __init__(self, Mainwindow, parent=None):
#         super(SecondWindow, self).__init__(parent)
#         self.Mainwindow = Mainwindow
#         self.loadVidButton.clicked.connect(self.selectVideoFile)
#
#     def selectVideoFile(self):
#         print('hello world')