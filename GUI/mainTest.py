from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QStyle, QApplication,QLabel,QWidget,QGraphicsLineItem
from PyQt5.QtGui import QImage, QPixmap,QPainter, QPen
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QObject, QMutex, QMutexLocker,QRect, QLine

import os
import cv2
import time
from collections import namedtuple
from datetime import datetime, timedelta
from scipy.spatial import distance
import threading
import concurrent.futures
import mainGUI
import mainGUI_calibration as Calibration
import mainGUI_detection as Detection

class MainWindow(QtWidgets.QMainWindow, mainGUI.Ui_MainWindow):
    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2

    def __init__(self, video_file=''):
        super().__init__()
        self.setupUi(self)

        self.thresh_vid = Detection.ThresholdVideo()
        # self.convert_scale = Calibration.Calibrate()

        self.tabWidget.setTabEnabled(1, False)
        self.tabWidget.setTabEnabled(2, False)
        self.tabWidget.setTabEnabled(3, True)
        self.tabWidget.setTabEnabled(4, False)
        self.tabWidget.setTabEnabled(5, False)

        # add a canvas for drawing
        # self.VBoxCanvasLabel = Drawing(self.caliTab)
        self.caliBoxCanvasLabel = Calibration.Drawing(self.caliTab)
        self.caliBoxCanvasLabel.setEnabled(False)
        self.caliBoxCanvasLabel.lower()
        self.caliBoxCanvasLabel.setGeometry(QRect(0, 0, 1024, 576))
        self.caliBoxCanvasLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.caliBoxCanvasLabel.setFrameShape(QtWidgets.QFrame.Box)
        self.caliBoxCanvasLabel.setCursor(Qt.CrossCursor)
        ####################################################
        # signals for the tab 0
        # need one button for back to main menu
        self.localModeButton.clicked.connect(self.enableLocalMode)
        self.liveModeButton.clicked.connect(self.enableLiveMode)
        #####################################################
        # signals for the tab 1
        self.loadVidButton.clicked.connect(self.selectVideoFile)
        self.loadNewVidButton.clicked.connect(self.selectNewFile)

        self.playButton.clicked.connect(self.videoPlayControl)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.stopButton.clicked.connect(self.stopVideo)
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

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
        self.resetScaleButton.clicked.connect(self.clearScale)
        self.applyScaleButton.clicked.connect(self.convertScale)
        self.threTabLinkButton.clicked.connect(self.enableThreshold)
        ###############################################
        # signal on tab 3

        self.threPlayButton.clicked.connect(self.thresh_vid.playControl)
        self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.threStopButton.clicked.connect(self.thresh_vid.stop)
        self.threStopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.thresh_vid.playClicked.connect(self.setPauseIcon)
        self.thresh_vid.pauseClicked.connect(self.setPlayIcon)
        self.thresh_vid.resumeClicked.connect(self.setPauseIcon)
        self.thresh_vid.stopClicked.connect(self.setPlayIcon)

        self.thresh_vid.updateThreshDisplay.connect(self.displayThresholdVideo)

        self.applyMaskcheckBox.stateChanged.connect(self.enalbleApplyMask)



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
                self.loadNewVidButton.setEnabled(True)
                # self.vidProgressBar.setEnabled(True)
                # display image on top of other widgets
                # can use either way
                # self.caliBoxCanvasLabel.raise_()
                self.loadImgButton.hide()
                self.loadVidButton.hide()

                # after select file, auto read and display its property
                print(self.video_file)
                self.readVideoFile(self.video_file[0])

                self.thresh_vid.updateVideoFile(self.video_file)

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
        # read file property and display the first frame
        try:
            video_cap = cv2.VideoCapture(file_path)
            video_prop = self.readVideoProp(video_cap)
            print(video_prop)

            self.thresh_vid.updateVideoProp(video_prop)

            video_name = os.path.split(file_path)

            self.videoThread.set_fps(video_prop.fps)

            self.setVidProgressBar(video_prop)
            self.caliTabLinkButton.setEnabled(True)
            self.loadNewVidButton.setEnabled(True)

            # set a function here link to labels that display the parameters
            self.vidNameText.setText(f'{str(video_name[1])}')
            self.vidDurText.setText(f'{str(video_prop.duration).split(".")[0]}')
            self.vidFpsText.setText(str(round(video_prop.fps,2)))
            self.vidResText.setText(f'{str(int(video_prop.width))} X {str(int(video_prop.height))}')
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
            self.setThresholdFrame(frame_display)
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

    def selectNewFile(self):
        self.resetVideo()
        self.selectVideoFile()

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
        self.status = MainWindow.STATUS_PLAYING
        self.setPauseIcon()

    def pauseVideo(self):

        self.videoThread.stop()
        # for camera
        # if self.video_type is MainWindow.VIDEO_TYPE_REAL_TIME:
        #     self.playCapture.release()
        # print(self.playCapture.get(cv2.CAP_PROP_POS_FRAMES))
        self.status = MainWindow.STATUS_PAUSE
        self.setPlayIcon()

    def resumeVideo(self):

        self.videoThread.start()
        self.status = MainWindow.STATUS_PLAYING
        self.setPauseIcon()

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
            self.setPlayIcon()

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

    def clearScale(self):
        self.caliBoxCanvasLabel.earse()
        self.metricNumInput.clear()
        self.drawScaleButton.setEnabled(True)
        self.caliBoxCanvasLabel.setEnabled(True)
        self.metricNumInput.setEnabled(True)
        self.threTabLinkButton.setEnabled(False)

    def setCalibrationFrame(self,frame):
        self.caliBoxLabel.setPixmap(frame)

    def localCalibration(self):

        self.caliBoxLabel.setEnabled(True)
        self.caliBoxCanvasLabel.setEnabled(True)
        self.metricNumInput.setEnabled(True)
        self.resetScaleButton.setEnabled(True)
        self.applyScaleButton.setEnabled(True)
        self.caliBoxCanvasLabel.raise_()

    def convertScale(self):
        # scale, metric = self.run()
        try:
            metric = int(self.metricNumInput.text())
            print(f'metric is {metric}')
            if (metric >= 1 and metric <= 1000):
                scale = self.caliBoxCanvasLabel.line_coordinates
                print(f'scale is {scale}')

                pixel_length = distance.euclidean(scale[0], scale[1])
                pixel_per_metric = round(pixel_length, 2) / metric
                print(f'pixel_per_metric{pixel_per_metric}')

                self.drawScaleButton.setEnabled(False)
                self.caliBoxCanvasLabel.setEnabled(False)
                self.metricNumInput.setEnabled(False)

                self.threTabLinkButton.setEnabled(True)
            else:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('Input value out of range.')
                self.error_msg.setInformativeText('Input can only numbers between 1 to 1000.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.exec()
        except Exception:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Must draw scale and input value, input and can only be an integer.')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.exec()

    def setThresholdFrame(self,frame):
        self.threBoxLabel.setPixmap(frame)

    def enableThreshold(self):
        # when enable cali tab, vid been reset, self.playCapture released
        # self.playCapture is closed now
        self.tabWidget.setTabEnabled(3, True)
        self.tabWidget.setCurrentIndex(3)
        print(self.video_file[0])
        print(self.playCapture.isOpened())

    def thresholdPlayControl(self, flag):

        if self.thresh_vid.video_file[0] == '' or self.thresh_vid.video_file[0] is None:
            print('No video is selected')
            return

        if self.thresh_vid.status is self.thresh_vid.STATUS_INIT:
            try:
                self.thresh_vid.play()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to play video file.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

        elif self.thresh_vid.status is self.thresh_vid.STATUS_PLAYING:
            try:
                self.pause()
                self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
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

        elif self.thresh_vid.status is self.thresh_vid.STATUS_PAUSE:
            try:
                self.thresh_vid.resume()
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


    # def localThreshold(self):
    #     self.playCapture.open(self.video_file[0])
    # #     self.th_masked = Detection.thresh_video(input_vid, block_size = 9, offset = 13)


    def run(self):
        """
        call input calibration scale function and draw scale function in separate thread
        """

        with concurrent.futures.ThreadPoolExecutor() as executor:

            cali_num_imput = executor.submit(self.metricNumInput.text())
            line_scale = executor.submit(self.caliBoxCanvasLabel.logdata(self))
            metric = cali_num_imput.result()
            scale = line_scale.result()
            print(f'metric is {metric}')
            print(f'scale is {scale}')

        return scale, metric


    def setPauseIcon(self):
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def setPlayIcon(self):
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def enalbleApplyMask(self):
        if self.applyMaskcheckBox.isChecked():
            self.thresh_vid.apply_mask = True
            self.thresh_vid.loadMask()
            # need to reset video
            # or force user select before threshold
        else:
            self.thresh_vid.apply_mask = False

    def displayThresholdVideo(self,frame):
        frame_display = QPixmap.fromImage(frame)
        self.threBoxLabel.setPixmap(frame_display)



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
