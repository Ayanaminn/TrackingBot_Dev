from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QStyle, QApplication, QLabel, QWidget, QGraphicsLineItem
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QObject, QMutex, QMutexLocker, QRect, QLine
from qtwidgets import Toggle, AnimatedToggle

import os
import cv2
import time
import numpy as np
from collections import namedtuple
from datetime import datetime, timedelta
from scipy.spatial import distance
import threading
import concurrent.futures
import mainGUI
import mainGUI_calibration as Calibration
from Tracking import TrackingMethod


# import mainGUI_detection as Detection

class MainWindow(QtWidgets.QMainWindow, mainGUI.Ui_MainWindow):
    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2

    def __init__(self, video_file=''):
        super().__init__()
        self.setupUi(self)

        # self.thresh_vid = Detection.ThresholdVideo()
        # self.convert_scale = Calibration.Calibrate()

        # # video init
        self.video_file = video_file
        self.status = self.STATUS_INIT  # 0: init 1:playing 2: pause
        self.playCapture = cv2.VideoCapture()

        # timer for video player on load tab
        self.videoThread = VideoThread()
        self.videoThread.timeSignal.signal[str].connect(self.displayVideo)

        # timer for threshold video player on load tab
        self.threshThread = ThreshVidThread()
        self.threshThread.timeSignal.thresh_signal.connect(self.displayThresholdVideo)
        self.threshThread.timeSignal.thresh_preview.connect(self.displayThresholdPreview)
        self.threshThread.timeSignal.updateSliderPos.connect(self.updateThreSlider)
        self.threshThread.timeSignal.thresh_reset.connect(self.resetVideo)
        # self.detection = Detection()

        self.trackingThread = TrackingThread()
        self.trackingThread.timeSignal.tracking_signal.connect(self.displayTrackingVideo)

        self.resetVideo()

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

        ##############################################################
        # signals and widgets for the tab 0
        # need one button for back to main menu
        self.localModeButton.clicked.connect(self.enableLocalMode)
        self.liveModeButton.clicked.connect(self.enableLiveMode)

        #############################################################
        # signals and widgets for the tab 1
        self.loadVidButton.clicked.connect(self.selectVideoFile)
        self.loadNewVidButton.clicked.connect(self.selectNewFile)

        self.playButton.clicked.connect(self.videoPlayControl)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.stopButton.clicked.connect(self.stopVideo)
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

        self.caliTabLinkButton.clicked.connect(self.enableCalibration)

        # slider for video player on load tab
        self.vidProgressBar.sliderPressed.connect(self.pauseFromSlider)
        self.vidProgressBar.valueChanged.connect(self.updatePosition)
        self.vidProgressBar.sliderReleased.connect(self.resumeFromSlider)

        ###################################################################
        # signal on tab 2
        self.drawScaleButton.clicked.connect(self.drawScale)
        self.resetScaleButton.clicked.connect(self.clearScale)
        self.applyScaleButton.clicked.connect(self.convertScale)
        self.threTabLinkButton.clicked.connect(self.enableThreshold)
        ###############################################
        # signal on tab 3
        self.mask_file = ''
        self.apply_mask = False

        self.object_num = 1
        self.block_size = ''
        self.offset = ''
        self.min_contour = ''
        self.max_contour = ''
        self.invert_contrast = False

        self.threPlayButton.clicked.connect(self.threshVidControl)
        self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.threStopButton.clicked.connect(self.stopThreshVid)
        self.threStopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

        self.objNumBox.valueChanged.connect(self.setObjectNum)

        self.blockSizeSlider.sliderPressed.connect(self.pauseThreshVid)
        self.blockSizeSlider.valueChanged.connect(self.setBlockSizeSlider)
        self.blockSizeSlider.sliderReleased.connect(self.resumeThreshVid)
        self.blockSizeSpin.valueChanged.connect(self.setBlockSizeSpin)
        #
        self.offsetSlider.sliderPressed.connect(self.pauseThreshVid)
        self.offsetSlider.valueChanged.connect(self.setOffsetSlider)
        self.offsetSlider.sliderReleased.connect(self.resumeThreshVid)
        self.offsetSpin.valueChanged.connect(self.setOffsetSpin)
        #
        self.cntMinSlider.sliderPressed.connect(self.pauseThreshVid)
        self.cntMinSlider.valueChanged.connect(self.setMinCntSlider)
        self.cntMinSlider.sliderReleased.connect(self.resumeThreshVid)
        self.cntMinSpin.valueChanged.connect(self.setMinCntSpin)
        #
        self.cntMaxSlider.sliderPressed.connect(self.pauseThreshVid)
        self.cntMaxSlider.valueChanged.connect(self.setMaxCntSlider)
        self.cntMaxSlider.sliderReleased.connect(self.resumeThreshVid)
        self.cntMaxSpin.valueChanged.connect(self.setMaxCntSpin)

        # slider for video player on load tab
        self.threProgressBar.sliderPressed.connect(self.pauseThreshVid)
        self.threProgressBar.valueChanged.connect(self.updateThrePosition)
        self.threProgressBar.sliderReleased.connect(self.resumeThreshSlider)

        self.previewBoxLabel.lower()
        self.previewToggle = Toggle(self.threTab)
        self.previewToggle.setGeometry(QRect(1150, 390, 60, 35))
        self.previewToggle.stateChanged.connect(self.enableThrePreview)

        self.invertContrastToggle = Toggle(self.threTab)
        self.invertContrastToggle.setGeometry(QRect(1050, 210, 220, 35))
        self.invertContrastToggle.stateChanged.connect(self.invertContrast)

        self.applyThreButton.clicked.connect(self.applyThrePara)
        self.resetThreButton.clicked.connect(self.resetThrePara)
        #
        # self.applyMaskcheckBox.stateChanged.connect(self.enalbleApplyMask)

        ###############################################
        # signal on tab 4
        self.trackTabLinkButton.clicked.connect(self.enableTracking)

        self.trackStartButton.clicked.connect(self.trackingVidControl)
        self.trackStartButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        # self.trackStopButton.clicked.connect(self.stopTracking)
        # self.trackStopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

    # not yet activated
    def selectMainMenu(self):
        self.tabWidget.setCurrentIndex(0)

    def enableLocalMode(self):
        '''
        activate select video file tab
        '''
        self.tabWidget.setTabEnabled(0, False)
        self.tabWidget.setTabEnabled(1, True)
        self.tabWidget.setCurrentIndex(1)

    def enableLiveMode(self):
        '''
        activate load camera source tab
        '''
        self.tabWidget.setTabEnabled(0, False)
        self.tabWidget.setTabEnabled(5, True)
        self.tabWidget.setCurrentIndex(5)

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

                # display image on top of other widgets
                # can use either way
                # self.caliBoxCanvasLabel.raise_()
                self.loadImgButton.hide()
                self.loadVidButton.hide()

                # after select file, auto read and display its property
                print(self.video_file)
                self.readVideoFile(self.video_file[0])

                self.threshThread.file = self.video_file

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
        '''
        read property of selected video file and display the first frame
        '''
        self.caliTabLinkButton.setEnabled(True)
        self.loadNewVidButton.setEnabled(True)
        try:
            video_cap = cv2.VideoCapture(file_path)
            video_prop = self.readVideoProp(video_cap)
            video_name = os.path.split(file_path)
            print(video_prop)

            self.videoThread.set_fps(video_prop.fps)
            self.threshThread.set_fps(video_prop.fps)
            self.trackingThread.set_fps(video_prop.fps)

            self.setVidProgressBar(video_prop)

            # set a function here link to labels that display the parameters
            self.vidNameText.setText(f'{str(video_name[1])}')
            self.vidDurText.setText(f'{str(video_prop.duration).split(".")[0]}')
            self.vidFpsText.setText(str(round(video_prop.fps, 2)))
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

            self.setCalibrationCanvas(frame_display)
            self.setThresholdCanvas(frame_display)
            self.setTrackingCanvas(frame_display)
            video_cap.release()

        except:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Failed to read video file.')
            self.error_msg.setInformativeText('readVideoFile() failed\n'
                                              'cv2.VideoCapture() does not execute correctly.\n'
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
        '''
        release current file and select new file
        '''
        self.resetVideo()
        self.selectVideoFile()

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
                self.error_msg.setInformativeText('playVideo() does not execute correctly.')
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
                self.error_msg.setInformativeText('pauseVideo() does not execute correctly.')
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
                self.error_msg.setInformativeText('resumeVideo() does not execute correctly.')
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

    def displayVideo(self):
        '''
        managed by the video thread
        '''

        self.vidProgressBar.setEnabled(True)

        # click play button will execute playVideo() and open the file
        if self.playCapture.isOpened():

            ret, frame = self.playCapture.read()
            if ret:

                # convert total seconds to timedelta format, not total frames to timedelta
                play_elapse = self.playCapture.get(cv2.CAP_PROP_POS_FRAMES) / self.playCapture.get(cv2.CAP_PROP_FPS)
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

    def playVideo(self):

        self.playCapture.open(self.video_file[0])
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
        self.threshThread.stop()
        self.playCapture.release()
        self.threshThread.playCapture.release()
        self.status = MainWindow.STATUS_INIT
        self.setPlayIcon()

    def setVidProgressBar(self, vid_prop):

        self.vidPosLabel.setText('0:00:00')
        self.vidLenLabel.setText(f'{str(vid_prop.duration).split(".")[0]}')
        # use numeric, not timedelta format for range
        self.vidProgressBar.setRange(0, int(vid_prop.length / vid_prop.fps))
        self.vidProgressBar.setValue(0)

        self.vidProgressBar.setSingleStep(int(vid_prop.fps) * 5)  # 5 sec
        self.vidProgressBar.setPageStep(int(vid_prop.fps) * 60)  # 60 sec

        # self.vidProgressBar.valueChanged.connect(self.updatePosition)

        self.threPosLabel.setText('0:00:00')
        self.threLenLabel.setText(f'{str(vid_prop.duration).split(".")[0]}')
        # use numeric, not timedelta format for range
        self.threProgressBar.setRange(0, int(vid_prop.length / vid_prop.fps))
        self.threProgressBar.setValue(0)

        self.threProgressBar.setSingleStep(int(vid_prop.fps) * 5)  # 5 sec
        self.threProgressBar.setPageStep(int(vid_prop.fps) * 60)  # 60 sec

    def updatePosition(self):
        '''
        when drag slider to new position, update it
        '''

        play_elapse = self.vidProgressBar.value()
        self.vidPosLabel.setText(f"{str(timedelta(seconds=play_elapse)).split('.')[0]}")

    def pauseFromSlider(self):

        self.videoThread.stop()
        self.status = MainWindow.STATUS_PAUSE
        self.setPlayIcon()

    def resumeFromSlider(self):

        # convert current seconds back to frame number
        current_frame = self.playCapture.get(cv2.CAP_PROP_FPS) * int(self.vidProgressBar.value())
        self.playCapture.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

        self.videoThread.start()
        self.status = MainWindow.STATUS_PLAYING
        self.setPauseIcon()

    #####################################Functions for calibaration##########################

    def enableCalibration(self):
        '''
        reset status from video player in load video tab and disable tab
        activate calibration tab
        '''
        self.tabWidget.setTabEnabled(1, False)
        self.resetVideo()
        self.tabWidget.setTabEnabled(2, True)
        self.tabWidget.setCurrentIndex(2)

    def setCalibrationCanvas(self, frame):
        self.caliBoxLabel.setPixmap(frame)

    def drawScale(self):
        '''
        enable canvas label for mouse and paint event
        '''
        self.caliBoxLabel.setEnabled(True)
        self.caliBoxCanvasLabel.setEnabled(True)
        self.metricNumInput.setEnabled(True)
        self.resetScaleButton.setEnabled(True)
        self.applyScaleButton.setEnabled(True)
        self.caliBoxCanvasLabel.raise_()

    def clearScale(self):
        self.caliBoxCanvasLabel.earse()
        self.metricNumInput.clear()
        self.drawScaleButton.setEnabled(True)
        self.caliBoxCanvasLabel.setEnabled(True)
        self.metricNumInput.setEnabled(True)
        self.threTabLinkButton.setEnabled(False)

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
                self.error_msg.setInformativeText('Input can only be numbers between 1 to 1000.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.exec()
        except Exception:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Must draw a scale and define its value, input value and can only be an integer.')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.exec()

    #####################################Functions for threshold##########################

    def setThresholdCanvas(self, frame):

        self.threBoxLabel.setPixmap(frame)

    def enableThreshold(self):
        # when enable cali tab, vid been reset, self.playCapture released
        # self.playCapture is closed now
        self.tabWidget.setTabEnabled(2, False)
        self.tabWidget.setTabEnabled(3, True)
        self.tabWidget.setCurrentIndex(3)
        self.resetVideo()
        print(f'enable threshold{self.video_file[0]}')
        print(f'enable threshold{self.playCapture.isOpened()}')

    def threshVidControl(self):

        if self.video_file[0] == '' or self.video_file[0] is None:
            print('No video is selected')
            return

        if self.status is MainWindow.STATUS_INIT:
            try:
                self.playThreshVid()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to play video file.')
                self.error_msg.setInformativeText('playThreshVid() does not execute correctly.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

        elif self.status is MainWindow.STATUS_PLAYING:
            try:
                self.pauseThreshVid()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to pause video file.')
                self.error_msg.setInformativeText('pauseThreshVid() does not execute correctly.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

            # if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
            #     self.playCapture.release()

        elif self.status is MainWindow.STATUS_PAUSE:
            try:
                self.resumeThreshVid()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to resume playing.')
                self.error_msg.setInformativeText('resumeThreshVid() does not execute correctly.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

            # if self.video_type is VideoBox.VIDEO_TYPE_REAL_TIME:
            #     self.playCapture.open(self.video_url)
            # self.videoThread.start()

    def playThreshVid(self):
        self.threshThread.playCapture.open(self.video_file[0])
        self.threshThread.start()
        self.status = MainWindow.STATUS_PLAYING
        self.setPauseIcon()

    def pauseThreshVid(self):

        self.threshThread.stop()
        # for camera
        # if self.video_type is MainWindow.VIDEO_TYPE_REAL_TIME:
        #     self.playCapture.release()
        # print(self.playCapture.get(cv2.CAP_PROP_POS_FRAMES))
        self.status = MainWindow.STATUS_PAUSE
        self.setPlayIcon()

    def resumeThreshVid(self):

        self.threshThread.start()
        self.status = MainWindow.STATUS_PLAYING
        self.setPauseIcon()

    def resumeThreshSlider(self):

        # convert current seconds back to frame number
        current_frame = self.threshThread.playCapture.get(cv2.CAP_PROP_FPS) * int(self.threProgressBar.value())
        self.threshThread.playCapture.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

        self.threshThread.start()
        self.status = MainWindow.STATUS_PLAYING
        self.setPauseIcon()

    def stopThreshVid(self):
        is_stopped = self.threshThread.is_stopped()
        self.threPlayButton.setEnabled(True)
        # reset when video is paused
        if is_stopped:
            self.threshThread.playCapture.release()
            self.readVideoFile(self.video_file[0])
            self.status = MainWindow.STATUS_INIT
        # reset when video still playing
        elif not is_stopped:
            self.threshThread.stop()
            self.threshThread.playCapture.release()
            self.readVideoFile(self.video_file[0])
            self.status = MainWindow.STATUS_INIT
            self.setPlayIcon()

    def updateThreSlider(self, elapse):
        self.threProgressBar.setSliderPosition(elapse)
        self.threPosLabel.setText(f"{str(timedelta(seconds=elapse)).split('.')[0]}")

    def updateThrePosition(self):
        '''
        when drag slider to new position, update it
        '''

        play_elapse = self.threProgressBar.value()
        self.threPosLabel.setText(f"{str(timedelta(seconds=play_elapse)).split('.')[0]}")

    def setObjectNum(self):
        self.object_num = self.objNumBox.value()

    def setBlockSizeSlider(self):
        block_size = self.blockSizeSlider.value()
        # block size must be an odd value
        if block_size % 2 == 0:
            block_size += 1
        if block_size < 3:
            block_size = 3
        # update spin control to same value
        self.blockSizeSpin.setValue(block_size)
        # pass value to thread
        self.threshThread.block_size = block_size

    def setBlockSizeSpin(self):
        block_size = self.blockSizeSpin.value()
        if block_size % 2 == 0:
            block_size += 1
        if block_size < 3:
            block_size = 3
        # update slider control to same value
        self.blockSizeSlider.setValue(block_size)
        # pass value to thread
        self.threshThread.block_size = block_size

    def setOffsetSlider(self):
        offset = self.offsetSlider.value()
        self.offsetSpin.setValue(offset)
        self.threshThread.offset = offset

    def setOffsetSpin(self):
        offset = self.offsetSpin.value()
        self.offsetSlider.setValue(offset)
        self.threshThread.offset = offset

    def setMinCntSlider(self):
        min_cnt = self.cntMinSlider.value()
        self.cntMinSpin.setValue(min_cnt)
        self.threshThread.min_contour = min_cnt

    def setMinCntSpin(self):
        min_cnt = self.cntMinSpin.value()
        self.cntMinSlider.setValue(min_cnt)
        self.threshThread.min_contour = min_cnt

    def setMaxCntSlider(self):
        max_cnt = self.cntMaxSlider.value()
        self.cntMaxSpin.setValue(max_cnt)
        self.threshThread.max_contour = max_cnt

    def setMaxCntSpin(self):
        max_cnt = self.cntMaxSpin.value()
        self.cntMaxSlider.setValue(max_cnt)
        self.threshThread.max_contour = max_cnt

    def setPauseIcon(self):
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def setPlayIcon(self):
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def displayThresholdVideo(self, frame):

        frame_display = QPixmap.fromImage(frame)
        self.threBoxLabel.setPixmap(frame_display)

    def enableThrePreview(self):
        # enable real time preview window of threshold result
        if self.previewToggle.isChecked():
            self.previewBoxLabel.raise_()
        else:
            self.previewBoxLabel.lower()

    def displayThresholdPreview(self, preview_frame):

        preview_display = QPixmap.fromImage(preview_frame)
        self.previewBoxLabel.setPixmap(preview_display)

    def invertContrast(self):
        # invert contrast of video
        # defalut white background dark object
        if self.invertContrastToggle.isChecked():
            self.threshThread.invert_contrast = True
        else:
            self.threshThread.invert_contrast = False

    def enalbleApplyMask(self):
        pass
        # if self.applyMaskcheckBox.isChecked():
        #     self.thresh_vid.apply_mask = True
        #     self.thresh_vid.loadMask()
        #     # need to reset video
        #     # or force user select before threshold
        # else:
        #     self.thresh_vid.apply_mask = False

    def applyThrePara(self):
        '''
        Apply current threshold parameter settings and activate next step
        '''
        self.object_num = self.objNumBox.value()
        self.block_size = self.threshThread.block_size
        self.offset = self.threshThread.offset
        self.min_contour = self.threshThread.min_contour
        self.max_contour = self.threshThread.max_contour
        self.invert_contrast = self.threshThread.invert_contrast

        self.applyThreButton.setEnabled(False)
        self.objNumBox.setEnabled(False)
        self.blockSizeSlider.setEnabled(False)
        self.blockSizeSpin.setEnabled(False)
        self.offsetSlider.setEnabled(False)
        self.offsetSpin.setEnabled(False)
        self.cntMinSlider.setEnabled(False)
        self.cntMinSpin.setEnabled(False)
        self.cntMaxSlider.setEnabled(False)
        self.cntMaxSpin.setEnabled(False)
        self.previewBoxLabel.lower()
        self.previewToggle.setEnabled(False)
        self.previewToggle.setChecked(False)
        self.invertContrastToggle.setEnabled(False)

        self.trackTabLinkButton.setEnabled(True)

        print(self.object_num, self.block_size, self.offset, self.min_contour, self.max_contour)

    def resetThrePara(self):
        '''
        Reset current threshold parameter settings
        '''

        self.applyThreButton.setEnabled(True)
        self.objNumBox.setEnabled(True)
        self.blockSizeSlider.setEnabled(True)
        self.blockSizeSpin.setEnabled(True)
        self.offsetSlider.setEnabled(True)
        self.offsetSpin.setEnabled(True)
        self.cntMinSlider.setEnabled(True)
        self.cntMinSpin.setEnabled(True)
        self.cntMaxSlider.setEnabled(True)
        self.cntMaxSpin.setEnabled(True)
        # self.previewBoxLabel.lower()
        self.previewToggle.setEnabled(True)
        # self.previewToggle.setChecked(True)
        self.invertContrastToggle.setEnabled(True)

        self.trackTabLinkButton.setEnabled(False)

    ###############################################Functions for tracking#################################

    def enableTracking(self):
        # when enable cali tab, vid been reset, self.playCapture released
        # self.playCapture is closed now
        self.tabWidget.setTabEnabled(3, False)
        self.tabWidget.setTabEnabled(4, True)
        self.tabWidget.setCurrentIndex(4)
        self.trackStartButton.setEnabled(True)
        self.trackingThread.block_size = self.block_size
        self.trackingThread.offset = self.offset
        self.trackingThread.min_contour = self.min_contour
        self.trackingThread.max_contour = self.max_contour
        self.trackingThread.invert_contrast = self.invert_contrast
        self.resetVideo()
        print(f'enable tracking{self.video_file[0]}')
        print(f'enable tracking{self.playCapture.isOpened()}')

    def setTrackingCanvas(self, frame):
        self.trackingeBoxLabel.setPixmap(frame)

    def trackingVidControl(self):
        if self.video_file[0] == '' or self.video_file[0] is None:
            print('No video is selected')
            return
        if self.status is MainWindow.STATUS_INIT:
            try:
                self.startTracking()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to track video file.')
                self.error_msg.setInformativeText('trackingVid() does not execute correctly.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

        elif self.status is MainWindow.STATUS_PLAYING:
            self.warning_msg = QMessageBox()
            self.warning_msg.setWindowTitle('Warning')
            self.warning_msg.setIcon(QMessageBox.Warning)
            self.warning_msg.setText('A tracking task is in progress, all data will be lost if stop now.\n'
                                     'Do you want continue to abort current task?')
            self.warning_msg.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes)
            returnValue = self.warning_msg.exec()
            if returnValue == QMessageBox.Yes:
                try:
                    self.stopTracking()
                except:
                    self.error_msg = QMessageBox()
                    self.error_msg.setWindowTitle('Error')
                    self.error_msg.setText('An error happened when trying to stop tracking.')
                    self.error_msg.setInformativeText('stopTracking() does not execute correctly.')
                    self.error_msg.setIcon(QMessageBox.Warning)
                    self.error_msg.setDetailedText('You caught a bug! \n'
                                                   'Please submit this issue on GitHub to help us improve. ')
                    self.error_msg.exec()

    def startTracking(self):
        self.trackingThread.playCapture.open(self.video_file[0])
        self.trackingThread.start()
        self.status = MainWindow.STATUS_PLAYING

        self.trackStartButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

    def stopTracking(self):
        '''
        reset tracking progress when stop clicked during task
        :return:
        '''
        self.trackingThread.stop()
        self.trackingThread.playCapture.release()
        self.readVideoFile(self.video_file[0])
        self.status = MainWindow.STATUS_INIT

        self.trackStartButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def displayTrackingVideo(self, frame):
        frame_display = QPixmap.fromImage(frame)
        self.trackingeBoxLabel.setPixmap(frame_display)


class Detection():

    def __init__(self):
        super().__init__()

    ## video thresholding
    def thresh_video(self, vid, block_size, offset):
        """
        This function retrieves a video frame and preprocesses it for object tracking.
        The code 1) blurs image to reduce noise
                 2) converts it to greyscale
                 3) returns a thresholded version of the original image.
                 4) perform morphological operation to closing small holes inside objects
        Parameters
        ----------
        vid : source image containing all three colour channels
        block_size: int(optional), default = blocksize_ini
        offset: int(optional), default = offset_ini
        """
        vid = cv2.GaussianBlur(vid, (5, 5), 1)
        # vid = cv2.blur(vid, (5, 5))
        vid_gray = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
        vid_th = cv2.adaptiveThreshold(vid_gray,
                                       255,
                                       cv2.ADAPTIVE_THRESH_MEAN_C,
                                       cv2.THRESH_BINARY_INV,
                                       block_size,
                                       offset)

        ## Dilation followed by erosion to closing small holes inside the foreground objects
        kernel = np.ones((5, 5), np.uint8)
        vid_closing = cv2.morphologyEx(vid_th, cv2.MORPH_CLOSE, kernel)

        return vid_closing

    def detect_contours(self, vid, vid_th, min_th, max_th):

        """
        vid : original video source for drawing and visualize contours
        vid_detect : the masked video for detect contours
        min_th: minimum contour area threshold used to identify object of interest
        max_th: maximum contour area threshold used to identify object of interest

        :return
        contours: list
            a list of all detected contours that pass the area based threshold criterion
        pos_archive: a list of (2,1) array, dtype=float
            individual's location on previous frame
        pos_detection: a list of (2,1) array, dtype=float
            individual's location detected on current frame
            (  [[x0],[y0]]  ,  [[x1],[y1]]  , [[x2],[y2]] .....)
        """

        contours, _ = cv2.findContours(vid_th.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        vid_draw = vid.copy()

        ## initialize contour number

        ## roll current position to past
        ## clear current position to accept updated value
        pos_detection = []
        pos_archive = pos_detection.copy()
        del pos_detection[:]

        i = 0

        while i < len(contours):

            try:
                ## calculate contour area for current contour
                cnt_th = cv2.contourArea(contours[i])

                ## delete contour if not meet the threshold
                if cnt_th < min_th or cnt_th > max_th:
                    del contours[i]
                ## draw contour if meet the threshold
                else:
                    cv2.drawContours(vid_draw, contours, i, (0, 0, 255), 2, cv2.LINE_8)
                    ## calculate the centroid of current contour
                    M = cv2.moments(contours[i])
                    if M['m00'] != 0:
                        cx = M['m10'] / M['m00']
                        cy = M['m01'] / M['m00']
                    else:
                        cx = 0
                        cy = 0
                    ## update current position to new centroid
                    centroids = np.array([[cx], [cy]])
                    # pos_detection become a list of (2,1) array
                    pos_detection.append(centroids)
                    # continue to next contour
                    i += 1
            ## when a number is divided by a zero
            except ZeroDivisionError:
                pass
        return vid_draw, pos_detection  # , contours # , pos_detection, pos_archive


class Communicate(QObject):
    signal = pyqtSignal(str)
    thresh_signal = pyqtSignal(QImage)
    thresh_preview = pyqtSignal(QImage)
    thresh_reset = pyqtSignal(str)
    updateSliderPos = QtCore.pyqtSignal(float)
    tracking_signal = pyqtSignal(QImage)


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


class ThreshVidThread(QThread):

    def __init__(self, default_fps=25):
        QThread.__init__(self)
        self.file = ''
        self.stopped = False
        self.fps = default_fps
        self.timeSignal = Communicate()
        self.mutex = QMutex()
        self.detection = Detection()
        self.playCapture = cv2.VideoCapture()
        self.block_size = 11
        self.offset = 11
        self.min_contour = 1
        self.max_contour = 100
        self.invert_contrast = False

    def run(self):

        # video = self.playCapture.open(self.file[0])
        with QMutexLocker(self.mutex):
            self.stopped = False
        while True:
            tic = time.perf_counter()
            if self.stopped:
                return
            else:
                ret, frame = self.playCapture.read()
                if ret:
                    play_elapse = self.playCapture.get(cv2.CAP_PROP_POS_FRAMES) / self.playCapture.get(cv2.CAP_PROP_FPS)
                    self.timeSignal.updateSliderPos.emit(play_elapse)

                    if self.invert_contrast:
                        invert_vid = cv2.bitwise_not(frame)

                        thre_vid = self.detection.thresh_video(invert_vid,
                                                               self.block_size,
                                                               self.offset)

                        contour_vid,_ = self.detection.detect_contours(frame,
                                                                     thre_vid,
                                                                     self.min_contour,
                                                                     self.max_contour)

                        frame_rgb = cv2.cvtColor(contour_vid, cv2.COLOR_BGR2RGB)

                        frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                           QImage.Format_RGB888)
                        frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)

                        self.timeSignal.thresh_signal.emit(frame_scaled)
                        # time.sleep(1/25)

                        # preview thresholded video
                        thvid_rgb = cv2.cvtColor(thre_vid, cv2.COLOR_BGR2RGB)
                        thvid_cvt = QImage(thvid_rgb, thvid_rgb.shape[1], thvid_rgb.shape[0], thvid_rgb.strides[0],
                                           QImage.Format_RGB888)
                        thvid_scaled = thvid_cvt.scaled(320, 180, Qt.KeepAspectRatio)
                        self.timeSignal.thresh_preview.emit(thvid_scaled)

                    elif not self.invert_contrast:
                        thre_vid = self.detection.thresh_video(frame,
                                                               self.block_size,
                                                               self.offset)

                        contour_vid,_ = self.detection.detect_contours(frame,
                                                                     thre_vid,
                                                                     self.min_contour,
                                                                     self.max_contour)
                        # frame_rgb = cv2.cvtColor(thre_vid, cv2.COLOR_BGR2RGB)
                        frame_rgb = cv2.cvtColor(contour_vid, cv2.COLOR_BGR2RGB)

                        frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                           QImage.Format_RGB888)
                        frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)

                        self.timeSignal.thresh_signal.emit(frame_scaled)
                        # time.sleep(1/25)

                        # preview thresholded video
                        thvid_rgb = cv2.cvtColor(thre_vid, cv2.COLOR_BGR2RGB)
                        thvid_cvt = QImage(thvid_rgb, thvid_rgb.shape[1], thvid_rgb.shape[0], thvid_rgb.strides[0],
                                           QImage.Format_RGB888)
                        thvid_scaled = thvid_cvt.scaled(320, 180, Qt.KeepAspectRatio)
                        self.timeSignal.thresh_preview.emit(thvid_scaled)

                    toc = time.perf_counter()
                    print(f'Time Elapsed Per Loop {toc - tic:.3f}')
                elif not ret:
                    # video finished
                    self.timeSignal.thresh_reset.emit('1')

                    return

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, video_fps):
        self.fps = video_fps


class TrackingThread(QThread):

    def __init__(self, default_fps=25):
        QThread.__init__(self)
        self.file = ''
        self.stopped = False
        self.fps = default_fps
        self.timeSignal = Communicate()
        self.mutex = QMutex()
        self.detection = Detection()
        self.TrackingMethod = TrackingMethod(30, 60, 100)
        self.playCapture = cv2.VideoCapture()
        self.block_size = 11
        self.offset = 11
        self.min_contour = 1
        self.max_contour = 100
        self.invert_contrast = False
        self.obj_id = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
                  'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    def run(self):

        # video = self.playCapture.open(self.file[0])
        with QMutexLocker(self.mutex):
            self.stopped = False
        while True:
            tic = time.perf_counter()
            if self.stopped:
                return
            else:
                ret, frame = self.playCapture.read()
                if ret:
                    play_elapse = self.playCapture.get(cv2.CAP_PROP_POS_FRAMES) / self.playCapture.get(cv2.CAP_PROP_FPS)
                    # self.timeSignal.updateSliderPos.emit(play_elapse)

                    if self.invert_contrast:
                        invert_vid = cv2.bitwise_not(frame)

                        thre_vid = self.detection.thresh_video(invert_vid,
                                                               self.block_size,
                                                               self.offset)

                        contour_vid, pos_detection = self.detection.detect_contours(frame,
                                                                     thre_vid,
                                                                     self.min_contour,
                                                                     self.max_contour)

                        self.TrackingMethod.identify(pos_detection)

                        ## mark indentity of each objects
                        self.TrackingMethod.visualize(contour_vid, self.obj_id, is_centroid=True,
                                                 is_mark=True, is_trajectory=True)

                        frame_rgb = cv2.cvtColor(contour_vid, cv2.COLOR_BGR2RGB)

                        frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                           QImage.Format_RGB888)
                        frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)

                        self.timeSignal.tracking_signal.emit(frame_scaled)
                        # time.sleep(1/25)


                    elif not self.invert_contrast:
                        thre_vid = self.detection.thresh_video(frame,
                                                               self.block_size,
                                                               self.offset)

                        contour_vid, pos_detection = self.detection.detect_contours(frame,
                                                                     thre_vid,
                                                                     self.min_contour,
                                                                     self.max_contour)

                        self.TrackingMethod.identify(pos_detection)

                        ## mark indentity of each objects
                        self.TrackingMethod.visualize(contour_vid, self.obj_id, is_centroid=True,
                                                 is_mark=True, is_trajectory=True)

                        # frame_rgb = cv2.cvtColor(thre_vid, cv2.COLOR_BGR2RGB)
                        frame_rgb = cv2.cvtColor(contour_vid, cv2.COLOR_BGR2RGB)

                        frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                           QImage.Format_RGB888)
                        frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)

                        self.timeSignal.tracking_signal.emit(frame_scaled)
                        # time.sleep(1/25)

                    toc = time.perf_counter()
                    print(f'Time Elapsed Per Loop {toc - tic:.3f}')
                elif not ret:
                    # video finished
                    # self.timeSignal.thresh_reset.emit('1')

                    return

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    # def is_stopped(self):
    #     with QMutexLocker(self.mutex):
    #         return self.stopped

    def set_fps(self, video_fps):
        self.fps = video_fps


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    # connect subclass with parent class
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
