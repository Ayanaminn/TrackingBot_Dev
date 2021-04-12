from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QStyle, QApplication,QLabel,QWidget,QGraphicsLineItem
from PyQt5.QtGui import QImage, QPixmap,QPainter, QPen
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QObject, QMutex, QMutexLocker,QRect, QLine
from PyQt5.QtCore import QTimer

import cv2, imutils
import time
from collections import namedtuple
from datetime import datetime, timedelta
import mainGUI
import mainGUI_calibration as Calibration


class MainWindow(QtWidgets.QMainWindow, mainGUI.Ui_MainWindow):
    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2

    def __init__(self, video_file=''):
        super().__init__()
        self.setupUi(self)

        self.draw_scale = Calibration.Drawing()

        self.tabWidget.setTabEnabled(1, False)
        self.tabWidget.setTabEnabled(2, False)
        self.tabWidget.setTabEnabled(3, False)
        self.tabWidget.setTabEnabled(4, False)
        self.tabWidget.setTabEnabled(5, False)

        # add a canvas for drawing
        # self.VBoxCanvasLabel = Drawing(self.caliTab)
        self.VBoxCanvasLabel = Calibration.Drawing(self.caliTab)
        self.VBoxCanvasLabel.setEnabled(False)
        self.VBoxCanvasLabel.lower()
        self.VBoxCanvasLabel.setGeometry(QRect(0, 0, 1024, 576))
        self.VBoxCanvasLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.VBoxCanvasLabel.setFrameShape(QtWidgets.QFrame.Box)
        self.VBoxCanvasLabel.setCursor(Qt.CrossCursor)
        ####################################################
        # signals for the tab 0
        # need one button for back to main menu
        self.localModeButton.clicked.connect(self.enableLocalMode)
        self.liveModeButton.clicked.connect(self.enableLiveMode)
        #####################################################
        # signals for the tab 1
        self.loadVidButton.clicked.connect(self.selectVideoFile)

        self.playButton.clicked.connect(self.videoPlayControl)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.stopButton.clicked.connect(self.stopVideo)
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

        self.endVideo.clicked.connect(self.clearDrawing)

        self.caliTabLinkButton.clicked.connect(self.enableCalibration)

        # # video init
        self.video_file = video_file
        self.status = self.STATUS_INIT  # 0: init 1:playing 2: pause
        # timer
        self.videoThread = VideoThread()
        self.videoThread.timeSignal.signal[str].connect(self.displayVideo)

        # slider
        self.vidProgressBar.sliderPressed.connect(self.pauseFromSlider)
        # self.vidProgressBar.valueChanged.connect(self.updatePosition)
        self.vidProgressBar.sliderReleased.connect(self.resumeFromSlider)

        # init
        self.playCapture = cv2.VideoCapture()
        self.resetVideo()

        ##########################################
        # signal on tab 2
        self.drawScaleButton.clicked.connect(self.localCalibration)
        self.resetScaleButton.clicked.connect(self.VBoxCanvasLabel.earse)

    def selectMainMenu(self):
        self.tabWidget.setCurrentIndex(0)

    def enableLocalMode(self):
        self.tabWidget.setTabEnabled(1, True)
        self.tabWidget.setCurrentIndex(1)

    def enableLiveMode(self):
        self.tabWidget.setTabEnabled(5, True)
        self.tabWidget.setCurrentIndex(5)

    def enableCalibration(self):
        self.resetVideo()
        self.tabWidget.setTabEnabled(2, True)
        self.tabWidget.setCurrentIndex(2)


    def selectVideoFile(self):

        try:
            # set default directory for load files and set file type that only shown
            self.video_file = QFileDialog.getOpenFileName(directory='C:/Users/Public/Desktop',
                                                          filter='Videos(*.mp4 *.avi)')
            # if no file selected
            if self.video_file[0] == '':
                return

            else:
                # enable video control
                self.playButton.setEnabled(True)
                self.stopButton.setEnabled(True)

                # self.vidProgressBar.setEnabled(True)
                # display image on top of other widgets
                # can use either way
                self.VBoxCanvasLabel.raise_()
                self.loadImgButton.hide()
                self.loadVidButton.hide()

                # after select file, auto read and display its property
                print(self.video_file)
                self.readVideoFile(self.video_file[0])

        except:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('An error happened when trying to load video file.')
            self.error_msg.setInformativeText('Please ensure the video file is not corrupted.')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.setDetailedText('You caught a bug! \n'
                                           'Please submit this issue on GitHub to help us improve. ')
            self.error_msg.exec()

    def readVideoFile(self, file_path):

        try:
            video_cap = cv2.VideoCapture(file_path)
            video_prop = self.readVideoProp(video_cap)
            print(video_prop)

            self.videoThread.set_fps(video_prop.fps)

            self.setVidProgressBar(video_prop)
            self.caliTabLinkButton.setEnabled(True)
            self.reloadVidButton.setEnabled(True)

            # set a function here link to labels that display the parameters

            # display 1st frame of video in window as preview
            set_preview_frame = 1
            video_cap.set(cv2.CAP_PROP_POS_FRAMES, set_preview_frame)
            ret, preview_frame = video_cap.read()
            frame_rgb = cv2.cvtColor(preview_frame, cv2.COLOR_BGR2RGB)
            frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                               QImage.Format_RGB888)
            frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
            frame_display = QPixmap.fromImage(frame_scaled)
            self.VBoxLabel.setPixmap(frame_display)

            self.setCalibrationFrame(frame_display)
            video_cap.release()

        except:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Failed to read video file.')
            self.error_msg.setInformativeText('cv2.VideoCapture() does not execute correctly.\n'
                                              'QImage is not converted correctly')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.setDetailedText('You caught a bug! \n'
                                           'Please submit this issue on GitHub to help us improve. ')
            self.error_msg.exec()

    def readVideoProp(self, file_path):
        """
        read parameters of loaded video file and return all values
        Parameters
        ----------
        video_file

        Returns
        -------
        get_video_prop: a named tuple of video parameter
        """
        # calculate total number of seconds of file
        total_sec = file_path.get(cv2.CAP_PROP_FRAME_COUNT) / file_path.get(cv2.CAP_PROP_FPS)
        # convert total seconds to hh:mm:ss format
        video_duraion = str(timedelta(seconds=total_sec))
        video_prop = namedtuple('video_prop', ['width', 'height', 'fps', 'length', 'elapse', 'duration'])
        get_video_prop = video_prop(file_path.get(cv2.CAP_PROP_FRAME_WIDTH),
                                    file_path.get(cv2.CAP_PROP_FRAME_HEIGHT),
                                    file_path.get(cv2.CAP_PROP_FPS),
                                    file_path.get(cv2.CAP_PROP_FRAME_COUNT),
                                    file_path.get(cv2.CAP_PROP_POS_MSEC),
                                    video_duraion)

        return get_video_prop

    def displayVideo(self):
        # print('emited signal connected')
        self.vidProgressBar.setEnabled(True)

        if self.playCapture.isOpened():  # when click the play button that connected with playVideo function

            ret, frame = self.playCapture.read()
            if ret:
                print(self.playCapture.get(cv2.CAP_PROP_POS_FRAMES))
                play_elapse = self.playCapture.get(cv2.CAP_PROP_POS_FRAMES)
                # update slider position and label
                self.vidProgressBar.setSliderPosition(play_elapse)
                self.vidPosLabel.setText(f"{str(timedelta(seconds=play_elapse)).split('.')[0]}")

                # if frame.ndim == 3:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # elif frame.ndim == 2:
                # frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

                frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                   QImage.Format_RGB888)
                frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
                frame_display = QPixmap.fromImage(frame_scaled)
                self.VBoxLabel.setPixmap(frame_display)
            elif not ret:
                # video finished
                self.resetVideo()
                self.playButton.setEnabled(False)
                return
            else:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('Failed to read next video frame.')
                self.error_msg.setInformativeText('cv2.VideoCapture.read() does not return any frame.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()
        else:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Failed to read video file.')
            self.error_msg.setInformativeText('cv2.VideoCapture.isOpen() return false.\n'
                                              'Click "OK" to reset video.')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.setDetailedText('You caught a bug! \n'
                                           'Please submit this issue on GitHub to help us improve.')
            self.error_msg.exec()
            self.resetVideo()

    def videoPlayControl(self):

        if self.video_file[0] == '' or self.video_file[0] is None:
            print('No video is selected')
            return

        if self.status is MainWindow.STATUS_INIT:
            try:
                self.playVideo()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to play video file.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

        elif self.status is MainWindow.STATUS_PLAYING:
            try:
                self.pauseVideo()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to pause video file.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

            # if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
            #     self.playCapture.release()

        elif self.status is MainWindow.STATUS_PAUSE:
            try:
                self.resumeVideo()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to resume playing.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()
            # if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
            #     self.playCapture.open(self.video_url)
            # self.videoThread.start()

        '''
        study below structure
        '''
        # self.status = (MainWindow.STATUS_PLAYING,
        #                MainWindow.STATUS_PAUSE,
        #                MainWindow.STATUS_PLAYING)[self.status]

    def playVideo(self):

        self.playCapture.open(self.video_file[0])

        # current_frame = int(self.vidProgressBar.value())
        # self.playCapture.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

        self.videoThread.start()
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.status = MainWindow.STATUS_PLAYING

    def pauseVideo(self):

        self.videoThread.stop()
        # for camera
        # if self.video_type is MainWindow.VIDEO_TYPE_REAL_TIME:
        #     self.playCapture.release()
        print(self.playCapture.get(cv2.CAP_PROP_POS_FRAMES))
        self.status = MainWindow.STATUS_PAUSE
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def resumeVideo(self):

        self.videoThread.start()
        self.status = MainWindow.STATUS_PLAYING
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def pauseFromSlider(self):

        self.videoThread.stop()
        # self.playCapture.release()
        print(self.playCapture.get(cv2.CAP_PROP_POS_FRAMES))
        self.status = MainWindow.STATUS_PAUSE
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def resumeFromSlider(self):

        # self.playCapture.open(self.video_file[0])

        current_frame = int(self.vidProgressBar.value())
        self.playCapture.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

        self.videoThread.start()
        self.status = MainWindow.STATUS_PLAYING
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def stopVideo(self):
        is_stopped = self.videoThread.is_stopped()
        self.playButton.setEnabled(True)
        # reset when video is paused
        if is_stopped:
            self.playCapture.release()
            self.readVideoFile(self.video_file[0])
            self.status = MainWindow.STATUS_INIT
        # reset when video still playing
        elif not is_stopped:
            self.videoThread.stop()
            self.playCapture.release()
            self.readVideoFile(self.video_file[0])
            self.status = MainWindow.STATUS_INIT
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def resetVideo(self):
        self.videoThread.stop()
        self.playCapture.release()
        self.status = MainWindow.STATUS_INIT
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def setVidProgressBar(self,vid_prop):

        self.vidPosLabel.setText('0:00:00')
        self.vidLenLabel.setText(f'{str(vid_prop.duration).split(".")[0]}')
        self.vidProgressBar.setRange(1, vid_prop.length)
        self.vidProgressBar.setValue(1)

        self.vidProgressBar.setSingleStep(int(vid_prop.fps)*5) # 5 sec
        self.vidProgressBar.setPageStep(int(vid_prop.fps)*60) # 60 sec

        self.vidProgressBar.valueChanged.connect(self.updatePosition)

    def updatePosition(self):

        play_elapse = self.vidProgressBar.value()
        self.vidPosLabel.setText(f"{str(timedelta(seconds=play_elapse)).split('.')[0]}")
        self.endVideo.setText(str(play_elapse))

    def clearDrawing(self):
        self.VBoxCanvasLabel.earse()


    def setCalibrationFrame(self,frame):
        self.caliBoxLabel.setPixmap(frame)

    def localCalibration(self):

        self.caliBoxLabel.setEnabled(True)
        self.VBoxCanvasLabel.setEnabled(True)
        self.caliNumInput.setEnabled(True)
        self.resetScaleButton.setEnabled(True)
        self.VBoxCanvasLabel.raise_()











class Drawing(QLabel):


    def __init__(self, parent = None):
        QLabel.__init__(self,parent)

        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.draw_flag = False
        self.erase_flag = False

    # Mouse click event
    def mousePressEvent(self, event):
        self.draw_flag = True
        self.erase_flag = False
        self.x0 = event.x()
        self.y0 = event.y()
        self.x1 = self.x0
        self.y1 = self.y0
        print(self.x0,self.y0)

    # Mouse release event
    def mouseReleaseEvent(self, event):
        self.draw_flag = False
        self.erase_flag = False

    # Mouse movement events
    def mouseMoveEvent(self, event):
        if self.draw_flag:
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()

     #Draw events
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        # painter = QGraphicsLineItem(self)
        if self.erase_flag:
            # painter.clear()
            self.x0 = 0
            self.y0 = 0
            self.x1 = 0
            self.y1 = 0
            # self.update()
        else:
            # rect =QRect(self.x0, self.y0, abs(self.x1-self.x0), abs(self.y1-self.y0))
            self.newline = QLine(self.x0,self.y0,self.x1,self.y1)
            # painter = QPainter(self)
            painter.setPen(QPen(Qt.red,2,Qt.SolidLine))
            # painter.drawRect(rect)
            painter.drawLine(self.newline)

    def earse(self):
        self.erase_flag = True
        self.update()

class Communicate(QObject):
    signal = pyqtSignal(str)


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


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    # connect subclass with parent class
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
