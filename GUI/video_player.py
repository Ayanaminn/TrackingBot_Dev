##################################################################
# This module manages video playing
#
##################################################################
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, QThread,QObject,QMutex,QMutexLocker
from PyQt5.QtWidgets import  QWidget
import time
import mainGUI

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

