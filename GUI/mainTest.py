from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QStyle, \
    QVBoxLayout, QLabel, QWidget, QHBoxLayout, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QPixmapCache
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QObject, QMutex, QMutexLocker, QRect, QPoint
from qtwidgets import Toggle, AnimatedToggle

import os

import subprocess
import cv2
import time
import numpy as np
import pandas as pd
from collections import namedtuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scipy.spatial import distance
from shapely.geometry import Point, Polygon
import serial
import serial.tools.list_ports
import mainGUI
from video_player import SecondWindow
from video_player import VideoThread
import mainGUI_calibration as Calibration
from Tracking import TrackingMethod
from Datalog import TrackingDataLog


# try:
#     # Include in try/except block if you're also targeting Mac/Linux
#     from PyQt5.QtWinExtras import QtWin
#     myappid = 'neurotoxlab'
#     QtWin.setCurrentProcessExplicitAppUserModelID(myappid)
# except ImportError:
#     pass

# import mainGUI_detection as Detection

class MainWindow(QtWidgets.QMainWindow, mainGUI.Ui_MainWindow):
    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2

    def __init__(self, video_file=''):
        super().__init__()
        self.setupUi(self)
        # fileh = QtCore.QFile(':/ui/mainGUI.ui')
        # fileh.open(QtCore.QFile.ReadOnly)
        # uic.loadUi(fileh, self)
        # fileh.close()
        # # Need be full path, otherwise complier cannot found file
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        # self.thresh_vid = Detection.ThresholdVideo()
        # self.convert_scale = Calibration.Calibrate()

        # # video init
        self.video_file = video_file
        self.preview_frame = None
        self.video_prop = None
        self.camera_prop = None
        self.status = self.STATUS_INIT  # 0: init 1:playing 2: pause
        self.playCapture = cv2.VideoCapture()
        self.verticalLayoutWidget.lower()
        # timer for video player on load tab
        self.videoThread = VideoThread()
        self.videoThread.timeSignal.signal[str].connect(self.displayVideo)
        self.secondwin = SecondWindow(MainWindow)

        # timer for camera source
        self.cameraThread = CameraThread()
        # self.cameraThread.setPixmap.connect(self.displayCamera)
        self.cameraThread.timeSignal.cam_signal.connect(self.displayCamera)
        self.cameraThread.timeSignal.cam_alarm.connect(self.reloadCamera)

        # timer for threshold video player on load tab
        self.threshThread = ThreshVidThread()
        self.threshThread.timeSignal.thresh_signal.connect(self.displayThresholdVideo)
        self.threshThread.timeSignal.thresh_preview.connect(self.displayThresholdPreview)
        self.threshThread.timeSignal.updateSliderPos.connect(self.updateThreSlider)
        self.threshThread.timeSignal.thresh_reset.connect(self.resetVideo)

        # timer for tracking video
        self.trackingThread = TrackingThread()
        self.trackingThread.timeSignal.tracking_signal.connect(self.displayTrackingVideo)
        self.trackingThread.timeSignal.updateSliderPos.connect(self.updateTrackSlider)
        self.trackingThread.timeSignal.tracked_object.connect(self.updateTrackResult)
        self.trackingThread.timeSignal.tracked_index.connect(self.updateTrackIndex)
        self.trackingThread.timeSignal.tracked_elapse.connect(self.updateTrackElapse)

        self.trackingThread.timeSignal.track_reset.connect(self.resetVideo)
        self.trackingThread.timeSignal.track_reset_alarm.connect(self.completeTracking)

        self.threshCamThread = ThreshCamThread()
        self.threshCamThread.timeSignal.cam_thresh_signal.connect(self.displayThresholdCam)
        self.threshCamThread.timeSignal.cam_thresh_preview.connect(self.displayThresholdCamPreview)
        self.threshCamThread.timeSignal.cam_alarm.connect(self.reloadCamera)

        self.trackingCamThread = TrackingCamThread()
        self.trackingCamThread.timeSignal.cam_tracking_signal.connect(self.displayTrackingCam)
        self.trackingCamThread.timeSignal.cam_tracked_object.connect(self.updateLiveTrackResult)

        self.controllerThread = ControllerThread()


        self.dataLogThread = DataLogThread()
        self.dataframe = None

        self.resetVideo()

        self.tabWidget.setTabEnabled(1, False)
        self.tabWidget.setTabEnabled(2, False)
        self.tabWidget.setTabEnabled(3, False)
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
        # force trasparent to override application style
        self.caliBoxCanvasLabel.setStyleSheet("background-color: rgba(0,0,0,0%)")

        ##############################################################
        # signals and widgets for the tab 0
        # need one button for back to main menu
        self.localModeButton.clicked.connect(self.enableLocalMode)
        self.liveModeButton.clicked.connect(self.enableLiveMode)
        self.backToMenuButton.clicked.connect(self.selectMainMenu)

        #############################################################
        # signals and widgets for the tab 1
        # self.loadVidButton.clicked.connect(self.selectVideoFile)
        self.loadNewVidButton.clicked.connect(self.selectNewFile)

        self.playButton.clicked.connect(self.videoPlayControl)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.stopButton.clicked.connect(self.stopVideo)
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

        self.caliTabLinkButton.clicked.connect(self.enableCalibration)
        self.backToLoadButton.clicked.connect(self.selectVidTab)

        # slider for video player on load tab
        self.vidProgressBar.sliderPressed.connect(self.pauseFromSlider)
        self.vidProgressBar.valueChanged.connect(self.updatePosition)
        self.vidProgressBar.sliderReleased.connect(self.resumeFromSlider)

        ###################################################################
        # signal on tab 2
        # init pixel unit convert ratio
        self.pixel_per_metric = 1
        self.drawScaleButton.clicked.connect(self.drawScale)
        self.resetScaleButton.clicked.connect(self.clearScale)
        self.applyScaleButton.clicked.connect(self.convertScale)
        self.threTabLinkButton.clicked.connect(self.enableThreshold)
        ###############################################
        # signal on tab 3
        self.mask_file = ''
        # self.mask_image = '' # cv2 read image
        self.binary_mask = ''
        self.apply_mask = False
        self.detection = Detection()

        self.object_num = 1
        self.block_size = ''
        self.offset = ''
        self.min_contour = ''
        self.max_contour = ''
        self.invert_contrast = False

        # self.threMaskLabel = QtWidgets.QLabel(self.threTab)
        # self.threMaskLabel.setGeometry(QtCore.QRect(0, 0, 1024, 576))
        # self.threMaskLabel.setFrameShape(QtWidgets.QFrame.Box)
        # self.threMaskLabel.setText("")
        # self.threMaskLabel.setAlignment(QtCore.Qt.AlignCenter)
        # self.threMaskLabel.setObjectName("threBoxLabel")

        self.backToCaliButton.clicked.connect(self.selectCaliTab)

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


        self.enableMaskToggle = Toggle(self.threTab)
        self.enableMaskToggle.setGeometry(QRect(1036, 105, 90, 35))
        self.enableMaskToggle.stateChanged.connect(self.enableApplyMask)
        self.selectMaskButton.clicked.connect(self.loadMask)

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
        self.backToThreButton.clicked.connect(self.selectThreTab)

        self.trackStartButton.clicked.connect(self.trackingVidControl)
        self.trackStartButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        self.trackProgressBar.valueChanged.connect(self.updateTrackVidPosition)
        # self.trackStopButton.clicked.connect(self.stopTracking)
        # self.trackStopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))

        self.exportDataButton.clicked.connect(self.exportData)
        self.exportGraphButton.clicked.connect(self.exportGraph)
        self.visualizeToggle = Toggle(self.trackinTab)
        self.visualizeToggle.setEnabled(False)
        self.visualizeToggle.setGeometry(QRect(1070, 585, 85, 35))
        self.visualizeToggle.stateChanged.connect(self.generateGraph)

        self.figure = Figure()
        self.figure.set_facecolor("black")
        self.canvas = FigureCanvas(self.figure)

        # self.graphCanvas = QVBoxLayout(self.trackinTab)
        # self.graphCanvas.addWidget(self.canvas)
        self.verticalLayout_3.addWidget(self.canvas)
        # 4 self.graphCanvas.addStretch(2)
        # self.graphCanvas.setContentsMargins(0, 0,0, 0)
        self.canvas.setFixedSize(1024, 576)
        # self.canvas.setGeometry(QRect(0,0,1024,576))
        # self.canvas.lower()
        # self.graphCanvas.setGeometry(QRect(50,50,1,1))
        self.graph = None

        #############################################################
        # signals and widgets for the tab 5
        self.openCamButton.clicked.connect(self.readCamera)
        self.closeCamButton.clicked.connect(self.closeCamera)
        self.backToMenuButton_2.clicked.connect(self.selectMainMenu)

        self.camBoxCanvasLabel = Calibration.DefineROI(self.loadCamTab)

        self.camPreviewBoxLabel.lower()
        self.previewToggle_2 = Toggle(self.loadCamTab)
        self.previewToggle_2.setGeometry(QRect(1150, 370, 60, 35))
        self.previewToggle_2.setEnabled(False)
        self.previewToggle_2.stateChanged.connect(self.enableCamThrePreview)

        self.invertContrastToggle_2 = Toggle(self.loadCamTab)
        self.invertContrastToggle_2.setGeometry(QRect(1050, 190, 220, 35))
        self.invertContrastToggle_2.setEnabled(False)
        self.invertContrastToggle_2.stateChanged.connect(self.invertCamContrast)

        self.camBlockSizeSlider.valueChanged.connect(self.setCamBlockSizeSlider)
        self.camBlockSizeSpin.valueChanged.connect(self.setCamBlockSizeSpin)
        #
        self.camOffsetSlider.valueChanged.connect(self.setCamOffsetSlider)
        self.camOffsetSpin.valueChanged.connect(self.setCamOffsetSpin)
        #
        self.camCntMinSlider.valueChanged.connect(self.setCamMinCntSlider)
        self.camCntMinSpin.valueChanged.connect(self.setCamMinCntSpin)
        #
        self.camCntMaxSlider.valueChanged.connect(self.setCamMaxCntSlider)
        self.camCntMaxSpin.valueChanged.connect(self.setCamMaxCntSpin)

        self.applyCamThreButton.clicked.connect(self.applyThreCamPara)
        self.resetCamThreButton.clicked.connect(self.resetThreCamPara)

        self.camTrackingButton.clicked.connect(self.startCamTracking)

        #############################################################
        # signals and widgets for the hardware control
        self.active_device = None
        # self.comboBox.addItem('')
        self.comboBox.currentIndexChanged.connect(self.changePort)
        self.portRefreshButton.clicked.connect(self.getPort)
        self.portConnectButton.clicked.connect(self.connectPort)
        self.portDisconnectButton.clicked.connect(self.disconnectPort)

        self.drawLineButton.setIcon(QtGui.QIcon('line.png'))
        self.drawLineButton.setIconSize(QtCore.QSize(25,25))
        self.drawRectButton.setIcon(QtGui.QIcon('rectangle.png'))
        self.drawRectButton.setIconSize(QtCore.QSize(25,25))
        self.drawCircButton.setIcon(QtGui.QIcon('circle.png'))
        self.drawCircButton.setIconSize(QtCore.QSize(24,24))

        self.drawLineButton.clicked.connect(self.drawLineROI)
        self.drawRectButton.clicked.connect(self.drawRectROI)
        self.drawCircButton.clicked.connect(self.drawCircROI)

        self.applyROIButton.clicked.connect(self.applyROI)

        self.resetROIButton.clicked.connect(self.clearControlROI)



    def selectMainMenu(self):
        self.tabWidget.setTabEnabled(0, True)
        self.tabWidget.setTabEnabled(1, False)
        self.tabWidget.setTabEnabled(5, False)
        self.tabWidget.setCurrentIndex(0)
        self.resetVideo()
        self.closeCamera()

    def enableLocalMode(self):
        '''
        activate select video file tab
        '''
        self.tabWidget.setTabEnabled(0, False)
        self.tabWidget.setTabEnabled(1, True)
        self.tabWidget.setCurrentIndex(1)
        self.backToMenuButton.setEnabled(True)

    def enableLiveMode(self):
        '''
        activate load camera source tab
        '''
        self.tabWidget.setTabEnabled(0, False)
        self.tabWidget.setTabEnabled(5, True)
        self.tabWidget.setCurrentIndex(5)
        self.backToMenuButton_2.setEnabled(True)
        self.getPort()

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

            self.video_fps = int(video_prop.fps)
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
            self.preview_frame = preview_frame
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
        self.video_prop = get_video_prop
        return get_video_prop

    def selectNewFile(self):
        '''
        release current file and select new file
        '''
        self.resetVideo()
        self.threshThread.mask_img = None
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
        self.trackingThread.stop()
        self.dataLogThread.stop()
        self.playCapture.release()
        self.threshThread.playCapture.release()
        self.trackingThread.playCapture.release()
        self.status = MainWindow.STATUS_INIT
        self.setPlayIcon()
        self.trackStartButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def setVidProgressBar(self, vid_prop):

        self.vidPosLabel.setText('0:00:00')
        self.vidLenLabel.setText(f'{str(vid_prop.duration).split(".")[0]}')
        # total SECONDS ( total frames/fps) use numeric, not timedelta format for range
        self.vidProgressBar.setRange(0, int(vid_prop.length / vid_prop.fps))
        self.vidProgressBar.setValue(0)

        self.vidProgressBar.setSingleStep(int(vid_prop.fps) * 5)  # 5 sec
        self.vidProgressBar.setPageStep(int(vid_prop.fps) * 60)  # 60 sec

        # self.vidProgressBar.valueChanged.connect(self.updatePosition)

        self.threPosLabel.setText('0:00:00')
        self.threLenLabel.setText(f'{str(vid_prop.duration).split(".")[0]}')
        # total SECONDS, use numeric, not timedelta format for range
        self.threProgressBar.setRange(0, int(vid_prop.length / vid_prop.fps))
        self.threProgressBar.setValue(0)

        self.threProgressBar.setSingleStep(int(vid_prop.fps) * 5)  # 5 sec
        self.threProgressBar.setPageStep(int(vid_prop.fps) * 60)  # 60 sec

        self.trackPosLabel.setText('0:00:00')
        self.trackLenLabel.setText(f'{str(vid_prop.duration).split(".")[0]}')
        # # use numeric, not timedelta format for range
        self.trackProgressBar.setRange(0, int(vid_prop.length / vid_prop.fps))
        self.trackProgressBar.setValue(0)
        #
        self.trackProgressBar.setSingleStep(int(vid_prop.fps) * 5)  # 5 sec
        self.trackProgressBar.setPageStep(int(vid_prop.fps) * 60)  # 60 sec

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

    #####################################Functions for load camera#############

    def readCamera(self):

        self.camBoxLabel.show()

        try:
            # camera_cap = self.playCapture.open(0,cv2.CAP_DSHOW)
            camera_prop = self.readCamProp(cv2.VideoCapture(0, cv2.CAP_DSHOW))
            print(camera_prop)
            cv2.VideoCapture(0, cv2.CAP_DSHOW).release()
            # self.cameraThread.start()
            self.threshCamThread.start()
            # self.trackingCamThread.start()
            self.openCamButton.hide()
            self.closeCamButton.setEnabled(True)

            self.drawLineButton.setEnabled(True)
            self.drawRectButton.setEnabled(True)
            self.drawCircButton.setEnabled(True)

            self.previewToggle_2.setEnabled(True)
            self.invertContrastToggle_2.setEnabled(True)
            self.camBlockSizeSlider.setEnabled(True)
            self.camBlockSizeSpin.setEnabled(True)
            self.camOffsetSlider.setEnabled(True)
            self.camOffsetSpin.setEnabled(True)
            self.camCntMinSlider.setEnabled(True)
            self.camCntMinSpin.setEnabled(True)
            self.camCntMaxSlider.setEnabled(True)
            self.camCntMaxSpin.setEnabled(True)

        except:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Failed to open camera.')
            self.error_msg.setInformativeText('readCamera() failed\n'
                                              'Please make sure camera is connected with computer.\n')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.setDetailedText('You caught a bug! \n'
                                           'Please submit this issue on GitHub to help us improve. ')
            self.error_msg.exec()

    def readCamProp(self, cam):
        video_prop = namedtuple('video_prop', ['width', 'height'])
        get_camera_prop = video_prop(cam.get(cv2.CAP_PROP_FRAME_WIDTH),
                                     cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

        return get_camera_prop

    def displayCamera(self, frame):

        frame_display = QPixmap.fromImage(frame)
        self.camBoxLabel.setPixmap(frame_display)

    def reloadCamera(self):
        '''
        auto execute when received no ret alarm signal from cam thread
        '''

        self.cameraThread.stop()
        self.threshCamThread.stop()
        self.trackingCamThread.stop()
        self.error_msg = QMessageBox()
        self.error_msg.setWindowTitle('Error')
        self.error_msg.setText('No camera frame returned.')
        self.error_msg.setInformativeText('cv2.VideoCapture() does not return frame\n'
                                          'Please make sure camera is working and try to reload camera.\n')
        self.error_msg.setIcon(QMessageBox.Warning)
        self.error_msg.setDetailedText('You caught a bug! \n'
                                       'Please submit this issue on GitHub to help us improve. ')
        self.error_msg.exec()
        self.openCamButton.show()

    def closeCamera(self):

        self.cameraThread.stop()
        self.threshCamThread.stop()
        self.trackingCamThread.stop()
        self.controllerThread.stop()
        self.trackingCamThread.ROI_coordinate = None
        self.controllerThread.ROI_coordinate = None

        QPixmapCache.clear()
        self.camBoxLabel.hide()

        self.openCamButton.show()
        self.closeCamButton.setEnabled(False)
        self.drawLineButton.setEnabled(False)
        self.applyROIButton.setEnabled(False)
        self.resetROIButton.setEnabled(False)
        self.camBoxCanvasLabel.setEnabled(False)
        self.camBoxCanvasLabel.lower()
        self.camPreviewBoxLabel.hide()

        self.previewToggle_2.setChecked(False)
        self.previewToggle_2.setEnabled(False)
        self.invertContrastToggle_2.setEnabled(False)
        self.camBlockSizeSlider.setEnabled(False)
        self.camBlockSizeSpin.setEnabled(False)
        self.camOffsetSlider.setEnabled(False)
        self.camOffsetSpin.setEnabled(False)
        self.camCntMinSlider.setEnabled(False)
        self.camCntMinSpin.setEnabled(False)
        self.camCntMaxSlider.setEnabled(False)
        self.camCntMaxSpin.setEnabled(False)


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
        self.backToLoadButton.setEnabled(True)

    def selectVidTab(self):
        self.tabWidget.setTabEnabled(1, True)
        self.resetVideo()
        self.tabWidget.setTabEnabled(2, False)
        self.tabWidget.setCurrentIndex(1)
        self.clearScale()
        self.caliBoxLabel.setEnabled(False)
        self.caliBoxCanvasLabel.setEnabled(False)
        self.metricNumInput.setEnabled(False)
        self.resetScaleButton.setEnabled(False)
        self.applyScaleButton.setEnabled(False)
        self.caliBoxCanvasLabel.lower()

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
            # print(f'metric is {metric}')
            if (metric >= 1 and metric <= 1000):
                scale = self.caliBoxCanvasLabel.line_coordinates
                # print(f'scale is {scale}')

                pixel_length = distance.euclidean(scale[0], scale[1])
                self.pixel_per_metric = round(pixel_length, 2) / metric
                print(f'pixel_per_metric{self.pixel_per_metric}')

                self.caliTabText3.setText(str(self.pixel_per_metric))
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
        self.backToCaliButton.setEnabled(True)
        self.resetVideo()
        print(f'enable threshold{self.video_file[0]}')
        print(f'enable threshold playcapture opened{self.playCapture.isOpened()}')

    def selectCaliTab(self):
        # when enable cali tab, vid been reset, self.playCapture released
        # self.playCapture is closed now
        self.tabWidget.setTabEnabled(2, True)
        self.tabWidget.setTabEnabled(3, False)
        self.tabWidget.setCurrentIndex(2)
        self.resetVideo()
        self.resetThrePara()
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

    def enableApplyMask(self):
        # self.pauseThreshVid()

        if self.enableMaskToggle.isChecked():
            # 1st time select mask image
            if self.mask_file == '':
                self.apply_mask = self.threshThread.apply_mask = True
                # button linked to loadmask()
                self.selectMaskButton.setEnabled(True)
                self.loadMask()
            # already selected mask, call file, convert and apply again
            else:
                print(self.mask_file)
                self.apply_mask = self.threshThread.apply_mask = True
                self.selectMaskButton.setEnabled(True)
                # store binary mask image and pass to thre thread
                mask = self.detection.create_mask(self.mask_file[0])
                self.binary_mask = mask
                self.threshThread.mask_img = mask
        # Disable mask, clear bianry image but still store mask file path
        # for tracking thread unless reset all parameters
        else:
            self.apply_mask = self.threshThread.apply_mask = False
            self.threshThread.mask_img = None
            self.selectMaskButton.setEnabled(False)
            print(self.threshThread.mask_img)

    def loadMask(self):

        try:
            # set default directory for load files and set file type that only shown
            self.mask_file = QFileDialog.getOpenFileName(directory='C:/Users/Public/Pictures',
                                                          filter='Images(*.png *.jpg *.jpeg)')
            # if no file selected
            if self.mask_file[0] == '':
                return
            else:
                # display biwised first frame

                # # self.threMaskLabel.raise_()
                # mask = cv2.imread(self.mask_file[0])
                # mask_rgb = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
                # mask_cvt = QImage(mask_rgb, mask_rgb.shape[1], mask_rgb.shape[0], mask_rgb.strides[0],
                #                    QImage.Format_RGB888)
                # mask_scaled = mask_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
                # mask_display = QPixmap.fromImage(mask_scaled)
                # # self.threMaskLabel.setPixmap(mask_display)

                # store binary mask image and pass to thre thread
                mask = self.detection.create_mask(self.mask_file[0])
                self.binary_mask = mask
                self.threshThread.mask_img = mask

        except:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('An error happened when trying to load and convert the mask image.')
            self.error_msg.setInformativeText('Please ensure the mask file is not corrupted.')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.setDetailedText('You caught a bug! \n'
                                           'Please submit this issue on GitHub to help us improve. ')
            self.error_msg.exec()


    def applyThrePara(self):
        '''
        Store current threshold parameter settings and activate next step
        then pass stored settings to tracking thread
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
        self.enableMaskToggle.setEnabled(False)
        self.previewBoxLabel.lower()
        self.previewToggle.setEnabled(False)
        self.previewToggle.setChecked(False)
        self.invertContrastToggle.setEnabled(False)

        self.trackTabLinkButton.setEnabled(True)

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
        # reset mask status
        self.mask_file = ''
        self.enableMaskToggle.setChecked(False)
        self.enableMaskToggle.setEnabled(True)

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
        self.backToThreButton.setEnabled(True)
        self.trackStartButton.setEnabled(True)
        self.trackingThread.block_size = self.block_size
        self.trackingThread.offset = self.offset
        self.trackingThread.min_contour = self.min_contour
        self.trackingThread.max_contour = self.max_contour
        self.trackingThread.apply_mask = self.apply_mask
        self.trackingThread.mask_img = self.binary_mask
        self.trackingThread.invert_contrast = self.invert_contrast

        self.resetVideo()

        # set canvas
        if self.apply_mask:
            # bitwise operation
            masked_frame = self.detection.apply_mask(self.binary_mask, self.preview_frame)
            mask_frame_rgb = cv2.cvtColor(masked_frame, cv2.COLOR_BGR2RGB)
            mask_frame_cvt = QImage(mask_frame_rgb, mask_frame_rgb.shape[1], mask_frame_rgb.shape[0], mask_frame_rgb.strides[0],
                                    QImage.Format_RGB888)
            mask_frame_scaled = mask_frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
            mask_frame_display = QPixmap.fromImage(mask_frame_scaled)
            self.setTrackingCanvas(mask_frame_display)

        elif not self.apply_mask:

            frame_rgb = cv2.cvtColor(self.preview_frame, cv2.COLOR_BGR2RGB)
            frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                    QImage.Format_RGB888)
            frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
            frame_display = QPixmap.fromImage(frame_scaled)
            self.setTrackingCanvas(frame_display)
            # self.setTrackingCanvas(self.preview_frame)

        print(f'enable tracking{self.video_file[0]}')
        print(f'enable tracking{self.playCapture.isOpened()}')

    def selectThreTab(self):
        self.tabWidget.setTabEnabled(3, True)
        self.tabWidget.setTabEnabled(4, False)
        self.tabWidget.setCurrentIndex(3)
        self.trackStartButton.setEnabled(False)
        self.resetVideo()

    def setTrackingCanvas(self, frame):
        self.trackingeBoxLabel.setPixmap(frame)

    def trackingVidControl(self):
        if self.video_file[0] == '' or self.video_file[0] is None:
            print('No video is selected')
            return

        if self.status is MainWindow.STATUS_INIT:
            try:
                self.startTracking()
                self.trackingThread.trackingMethod.registration = []

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
                    self.warning_msg = QMessageBox()
                    self.warning_msg.setWindowTitle('Error')
                    self.warning_msg.setText('An error happened when trying to stop tracking.')
                    self.warning_msg.setInformativeText('stopTracking() does not execute correctly.')
                    self.warning_msg.setIcon(QMessageBox.Warning)
                    self.warning_msg.setDetailedText('You caught a bug! \n'
                                                     'Please submit this issue on GitHub to help us improve. ')
                    self.warning_msg.exec()

    def startTracking(self):
        self.trackingThread.playCapture.open(self.video_file[0])
        self.trackingThread.start()
        self.status = MainWindow.STATUS_PLAYING

        self.trackStartButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.backToThreButton.setEnabled(False)

    def stopTracking(self):
        '''
        cancel and reset tracking progress when stop clicked during ongoing task
        :return:
        '''
        try:
            self.trackingThread.stop()
            self.trackingThread.playCapture.release()
            self.dataLogThread.stop()

            # self.dataLogThread.df_archive = []
            # self.trackingThread.trackingMethod.registration = []

            self.readVideoFile(self.video_file[0])
            self.status = MainWindow.STATUS_INIT
            self.trackStartButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.backToThreButton.setEnabled(True)

        except Exception as e:
            print(e)
        finally:
            self.info_msg = QMessageBox()
            self.info_msg.setWindowTitle('TrackingBot')
            self.info_msg.setIcon(QMessageBox.Information)
            self.info_msg.setText('Tracking task cancelled.')
            self.info_msg.exec()

            print(f'pixel_per_metric{self.pixel_per_metric}')

    def displayTrackingVideo(self, frame):
        frame_display = QPixmap.fromImage(frame)
        self.trackingeBoxLabel.setPixmap(frame_display)

    def updateTrackSlider(self, elapse):
        self.trackProgressBar.setSliderPosition(elapse)
        self.trackPosLabel.setText(f"{str(timedelta(seconds=elapse)).split('.')[0]}")

    def updateTrackVidPosition(self):
        play_elapse = self.trackProgressBar.value()
        self.trackPosLabel.setText(f"{str(timedelta(seconds=play_elapse)).split('.')[0]}")

    def updateTrackResult(self, tracked_object):
        '''
        pass the list of registered object information to datalog thread
        '''

        # reset df list

        self.dataLogThread.track_data(tracked_object)
        # self.tracked_object = object
        # print(f'thread data is {self.tracked_object}')
        self.dataLogThread.start()

    def updateTrackIndex(self, tracked_index):
        '''
        pass the index of timestamp to datalog thread
        '''
        self.dataLogThread.track_index(tracked_index)

    def updateTrackElapse(self, tracked_elapse):
        '''
        pass video time elapsed when timestamp is true to datalog thread
        '''
        self.dataLogThread.track_elapse(tracked_elapse)

    def completeTracking(self):

        self.info_msg = QMessageBox()
        self.info_msg.setWindowTitle('TrackingBot')
        self.info_msg.setIcon(QMessageBox.Information)
        self.info_msg.setText('Tracking finished.')
        self.info_msg.exec()

        self.trackStartButton.setEnabled(False)
        self.backToThreButton.setEnabled(True)

        # enable export data button
        self.exportDataButton.setEnabled(True)
        self.exportGraphButton.setEnabled(True)
        self.visualizeToggle.setEnabled(True)

    def exportData(self):
        # dialog = QtGui.QFileDialog()
        self.folder_path = QFileDialog.getExistingDirectory(None, 'Select Folder', 'C:/Users/Public/Documents')
        print(self.folder_path)
        if self.folder_path == '':
            return
        else:
            try:
                self.convertData(self.folder_path)
                # dataframe = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                #                    columns=['a', 'b', 'c'])
                #
                # full_path = self.folder_path + '/data_export_test.xlsx'
                # writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
                # dataframe.to_excel(writer, sheet_name='Sheet1',index=False)
                #
                # writer.save()
                # return folder_path

                self.info_msg = QMessageBox()
                self.info_msg.setWindowTitle('TrackingBot')
                self.info_msg.setIcon(QMessageBox.Information)
                self.info_msg.setText('Successfully saved data')
                self.info_msg.addButton('OK', QMessageBox.RejectRole)
                self.info_msg.addButton('Open folder', QMessageBox.AcceptRole)
                self.info_msg.buttonClicked.connect(self.openDataFolder)
                self.info_msg.exec()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to export tracking data.')
                self.error_msg.setInformativeText('convertData() does not execute correctly.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

    def exportGraph(self):
        print(self.figure)
        print(self.graph)
        self.folder_path = QFileDialog.getExistingDirectory(None, 'Select Folder', 'C:/Users/Public/Documents')
        print(self.folder_path)
        if self.folder_path == '':
            return
        else:
            try:

                # self.convertData(self.folder_path)
                # dataframe = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                #                    columns=['a', 'b', 'c'])
                #
                full_path = self.folder_path + '/Heatmap.png'
                # writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
                # dataframe.to_excel(writer, sheet_name='Sheet1',index=False)
                self.figure.savefig(full_path, dpi=150, bbox_inches=None)
                # writer.save()
                # return folder_path

                self.info_msg = QMessageBox()
                self.info_msg.setWindowTitle('TrackingBot')
                self.info_msg.setIcon(QMessageBox.Information)
                self.info_msg.setText('Successfully saved graph')
                self.info_msg.addButton('OK', QMessageBox.RejectRole)
                self.info_msg.addButton('Open folder', QMessageBox.AcceptRole)
                self.info_msg.buttonClicked.connect(self.openDataFolder)
                self.info_msg.exec()
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('An error happened when trying to export graph.')
                self.error_msg.setInformativeText('exportGraph() does not execute correctly.')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.setDetailedText('You caught a bug! \n'
                                               'Please submit this issue on GitHub to help us improve. ')
                self.error_msg.exec()

    def convertData(self, save_path):
        self.save_path = save_path
        # self.tracked_result = self.dataLogThread.df_archive.copy()

        print(f'df archive end length {len(self.dataLogThread.df_archive)}')
        print(self.dataLogThread.df_archive)
        print(f'number of obj is {self.object_num}')

        # pay attention to dtype!!!
        # otherwise can not perform calculation betwteen different datatype
        # such as str and float
        self.dataframe = pd.DataFrame(np.array(self.dataLogThread.df_archive),
                                      columns=['Result(Frame)', 'Video elapse', 'Subject', 'pos_x', 'pos_y'])

        self.dataframe['Result(Frame)'] = self.dataframe['Result(Frame)'].astype(int)
        self.dataframe['Video elapse'] = self.dataframe['Video elapse'].astype(str)
        self.dataframe['Subject'] = 'Subject ' + self.dataframe['Subject'].astype(str)
        self.dataframe['pos_x'] = self.dataframe['pos_x'].astype(float)
        self.dataframe['pos_y'] = self.dataframe['pos_y'].astype(float)

        dataframe_per_sec = self.dataframe.copy().loc[self.dataframe['Result(Frame)'] % self.video_prop.fps == 0]

        dx = self.dataframe['pos_x'] - self.dataframe['pos_x'].shift(self.object_num)
        dy = self.dataframe['pos_y'] - self.dataframe['pos_y'].shift(self.object_num)
        self.dataframe['Distance moved (mm)'] = (np.sqrt(dx ** 2 + dy ** 2)) / self.pixel_per_metric
        print(self.dataframe)
        self.dataframe['Distance moved (mm)'] = self.dataframe['Distance moved (mm)'].astype(float)

        dx_per_sec = dataframe_per_sec['pos_x'] - dataframe_per_sec['pos_x'].shift(self.object_num)
        dy_per_sec = dataframe_per_sec['pos_y'] - dataframe_per_sec['pos_y'].shift(self.object_num)
        dataframe_per_sec['Distance moved (mm)'] = (np.sqrt(dx_per_sec ** 2 + dy_per_sec ** 2)) / self.pixel_per_metric
        dataframe_per_sec['Distance moved (mm)'] = dataframe_per_sec['Distance moved (mm)'].astype(float)
        print(dataframe_per_sec)
        full_path = self.save_path + '/data_export_test.xlsx'
        print(full_path)
        # dataframe.to_csv('C:/Users/phenomicslab/Documents/data_export_test.csv',encoding='utf-8')
        with pd.ExcelWriter(full_path, engine='xlsxwriter') as writer:
            dataframe_per_sec.to_excel(writer, sheet_name='Result', index=False)
            self.dataframe.to_excel(writer, sheet_name='Raw_data', index=False)
        # writer = pd.ExcelWriter(full_path, engine='xlsxwriter')

        # dataframe.to_excel(writer, sheet_name='Sheet1', index=False, options={'strings_to_numbers': True})
        # worksheet1 = writer.sheets['Sheet1']
        # workbook = writer.book
        # # time_format = workbook.add_format()
        # # float_format = workbook.add_format()
        # # format1 = workbook.add_format({'num_format': '0.00'})
        # #
        # # time_format.set_num_format('mm:ss:00')
        # # float_format.set_num_format(2)
        # worksheet1.set_column('B:B', 14)
        # worksheet.set_column('D:D', None, format1)

    def generateGraph(self):

        if self.visualizeToggle.isChecked():
            if self.graph is None:
                # make it a true/flase flag
                # self.figure = Figure()
                # self.canvas = FigureCanvas(self.figure)
                ax = self.figure.add_subplot(111)
                if self.dataframe is None:

                    self.dataframe = pd.DataFrame(np.array(self.dataLogThread.df_archive),
                                                  columns=['Result(Frame)', 'Video elapse', 'Subject', 'pos_x',
                                                           'pos_y'])

                    self.dataframe['Result(Frame)'] = self.dataframe['Result(Frame)'].astype(int)
                    self.dataframe['Video elapse'] = self.dataframe['Video elapse'].astype(str)
                    self.dataframe['Subject'] = 'Subject ' + self.dataframe['Subject'].astype(str)
                    self.dataframe['pos_x'] = self.dataframe['pos_x'].astype(float)
                    self.dataframe['pos_y'] = self.dataframe['pos_y'].astype(float)

                    self.heatmap = ax.hist2d(self.dataframe['pos_x'], self.dataframe['pos_y'],
                                             bins=[np.arange(0, self.video_prop.width, 5),
                                                   np.arange(0, self.video_prop.height, 5)],
                                             cmap='hot')

                    tick_locator = ticker.LinearLocator(2)
                    cb = plt.colorbar(self.heatmap[3], ax=ax)

                    cb.locator = tick_locator
                    cb.update_ticks()
                    plt.setp(plt.getp(cb.ax.axes, 'yticklabels'), color='red')
                    cb.set_label(label='Frequency', weight='bold', color='red')
                    ax.invert_yaxis()
                    ax.axis('off')
                    self.canvas.draw()
                    self.graph = ax
                    # plt.show()

                else:
                    self.heatmap = ax.hist2d(self.dataframe['pos_x'], self.dataframe['pos_y'],
                                             bins=[np.arange(0, self.video_prop.width, 5),
                                                   np.arange(0, self.video_prop.height, 5)],
                                             cmap='hot')

                    tick_locator = ticker.LinearLocator(2)
                    cb = plt.colorbar(self.heatmap[3], ax=ax)

                    cb.locator = tick_locator
                    cb.update_ticks()
                    plt.setp(plt.getp(cb.ax.axes, 'yticklabels'), color='red')
                    cb.set_label(label='Frequency', weight='bold', color='red')
                    ax.invert_yaxis()
                    ax.axis('off')
                    self.canvas.draw()
                    self.graph = ax

                self.verticalLayoutWidget.raise_()

            else:
                self.verticalLayoutWidget.raise_()
            #     self.canvas = FigureCanvas(self.graph)
            #     self.canvas.draw()
            #
            # self.verticalLayoutWidget.raise_()

        else:
            self.verticalLayoutWidget.lower()

    def openDataFolder(self):
        '''
        open system directory that data file saved
        for both Win and OS system

        '''
        try:
            os.startfile(self.folder_path)
        except:
            subprocess.Popen(['xdg-open', self.folder_path])

    ###############################################Function for cam threshold###############

    def displayThresholdCam(self, frame):

        frame_display = QPixmap.fromImage(frame)
        self.camBoxLabel.setPixmap(frame_display)

    def displayThresholdCamPreview(self, preview_frame):
        preview_display = QPixmap.fromImage(preview_frame)
        self.camPreviewBoxLabel.setPixmap(preview_display)

    def invertCamContrast(self):

        if self.invertContrastToggle_2.isChecked():
            self.threshCamThread.invert_contrast = True
        else:
            self.threshCamThread.invert_contrast = False

    def enableCamThrePreview(self):

        if self.previewToggle_2.isChecked():
            self.camPreviewBoxLabel.show()
            self.camPreviewBoxLabel.raise_()
        else:
            self.camPreviewBoxLabel.lower()

    def setCamBlockSizeSlider(self):
        block_size = self.camBlockSizeSlider.value()
        # block size must be an odd value
        if block_size % 2 == 0:
            block_size += 1
        if block_size < 3:
            block_size = 3
        # update spin control to same value
        self.camBlockSizeSpin.setValue(block_size)
        # pass value to thread
        self.threshCamThread.block_size = block_size

    def setCamBlockSizeSpin(self):
        block_size = self.camBlockSizeSpin.value()
        if block_size % 2 == 0:
            block_size += 1
        if block_size < 3:
            block_size = 3
        # update slider control to same value
        self.camBlockSizeSlider.setValue(block_size)
        # pass value to thread
        self.threshCamThread.block_size = block_size

    def setCamOffsetSlider(self):
        offset = self.camOffsetSlider.value()
        self.camOffsetSpin.setValue(offset)
        self.threshCamThread.offset = offset

    def setCamOffsetSpin(self):
        offset = self.camOffsetSpin.value()
        self.camOffsetSlider.setValue(offset)
        self.threshCamThread.offset = offset

    def setCamMinCntSlider(self):
        min_cnt = self.camCntMinSlider.value()
        self.camCntMinSpin.setValue(min_cnt)
        self.threshCamThread.min_contour = min_cnt

    def setCamMinCntSpin(self):
        min_cnt = self.camCntMinSpin.value()
        self.camCntMinSlider.setValue(min_cnt)
        self.threshCamThread.min_contour = min_cnt

    def setCamMaxCntSlider(self):
        max_cnt = self.camCntMaxSlider.value()
        self.camCntMaxSpin.setValue(max_cnt)
        self.threshCamThread.max_contour = max_cnt

    def setCamMaxCntSpin(self):
        max_cnt = self.camCntMaxSpin.value()
        self.camCntMaxSlider.setValue(max_cnt)
        self.threshCamThread.max_contour = max_cnt

    def applyThreCamPara(self):
        '''
        Apply current threshold parameter settings and activate next step
        '''
        # self.object_num = self.objNumBox.value()
        self.block_size = self.threshCamThread.block_size
        self.offset = self.threshCamThread.offset
        self.min_contour = self.threshCamThread.min_contour
        self.max_contour = self.threshCamThread.max_contour
        self.invert_contrast = self.threshCamThread.invert_contrast
        #
        self.applyCamThreButton.setEnabled(False)
        self.camPreviewBoxLabel.lower()
        self.previewToggle_2.setEnabled(False)
        self.invertContrastToggle_2.setEnabled(False)
        self.camBlockSizeSlider.setEnabled(False)
        self.camBlockSizeSpin.setEnabled(False)
        self.camOffsetSlider.setEnabled(False)
        self.camOffsetSpin.setEnabled(False)
        self.camCntMinSlider.setEnabled(False)
        self.camCntMinSpin.setEnabled(False)
        self.camCntMaxSlider.setEnabled(False)
        self.camCntMaxSpin.setEnabled(False)

        print(self.object_num, self.block_size, self.offset, self.min_contour, self.max_contour)

    def resetThreCamPara(self):
        '''
        Reset current threshold parameter settings
        '''

        # self.applyThreButton.setEnabled(True)
        # self.objNumBox.setEnabled(True)
        # self.blockSizeSlider.setEnabled(True)
        # self.blockSizeSpin.setEnabled(True)
        # self.offsetSlider.setEnabled(True)
        # self.offsetSpin.setEnabled(True)
        # self.cntMinSlider.setEnabled(True)
        # self.cntMinSpin.setEnabled(True)
        # self.cntMaxSlider.setEnabled(True)
        # self.cntMaxSpin.setEnabled(True)
        # # self.previewBoxLabel.lower()
        # self.previewToggle.setEnabled(True)
        # # self.previewToggle.setChecked(True)
        # self.invertContrastToggle.setEnabled(True)
        #
        # self.trackTabLinkButton.setEnabled(False)
        self.applyCamThreButton.setEnabled(True)
        self.previewToggle_2.setEnabled(True)
        self.invertContrastToggle_2.setEnabled(True)
        self.camBlockSizeSlider.setEnabled(True)
        self.camBlockSizeSpin.setEnabled(True)
        self.camOffsetSlider.setEnabled(True)
        self.camOffsetSpin.setEnabled(True)
        self.camCntMinSlider.setEnabled(True)
        self.camCntMinSpin.setEnabled(True)
        self.camCntMaxSlider.setEnabled(True)
        self.camCntMaxSpin.setEnabled(True)

    #   ############################################Functions for feedback control

    def startCamTracking(self):
        self.threshCamThread.stop()
        self.trackingCamThread.block_size = self.block_size
        self.trackingCamThread.offset = self.offset
        self.trackingCamThread.min_contour = self.min_contour
        self.trackingCamThread.max_contour = self.max_contour
        self.trackingCamThread.invert_contrast = self.invert_contrast
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.release()
        # print(cap.isOpened())
        time.sleep(1)
        self.trackingCamThread.start()
        # print(cv2.VideoCapture(0, cv2.CAP_DSHOW).isOpened())


        # self.status = MainWindow.STATUS_PLAYING

    def displayTrackingCam(self, frame):

        frame_display = QPixmap.fromImage(frame)
        self.camBoxLabel.setPixmap(frame_display)

    def updateLiveTrackResult(self, tracked_object):
        '''
        pass the list of registered object information to datalog thread
        '''

        # reset and store df list

        self.dataLogThread.track_data(tracked_object)
        self.dataLogThread.start()

        self.controllerThread.track_data(tracked_object)

        self.controllerThread.start()


    ###############################################Functions for hardware#################################

    def getPort(self):
        self.comboBox.addItem('')
        ports = serial.tools.list_ports.comports()
        available_ports = []

        for p in ports:
            available_ports.append([p.description,p.device])
            # print(str(p.description)) # device name + port name
            # print(str(p.device)) # port name

        for info in available_ports:
            self.comboBox.addItem(info[0])

        print(available_ports)
        return available_ports

    def changePort(self):
        # 1st empty line
        selected_port_index = self.comboBox.currentIndex()-1
        return selected_port_index

    def connectPort(self):

        available_ports = self.getPort()
        selected_port_index = self.changePort()
        print(selected_port_index)

        if available_ports and selected_port_index != 0:
            try:
                # portOpen = True
                self.active_device = serial.Serial(available_ports[selected_port_index][1], 9600, timeout=1)
                print(f'Connected to port {available_ports[selected_port_index][1]}!')
                # self.active_device.open()
                time.sleep(0.5)
                # thread start
                print(self.active_device.isOpen())
                self.comboBox.setEnabled(False)
                self.portConnectButton.setEnabled(False)
                self.portDisconnectButton.setEnabled(True)
                # print(f'Connected to port {available_ports[selected_port_index][1]}!')
                # device_control(activeDevice)
            except:
                self.error_msg = QMessageBox()
                self.error_msg.setWindowTitle('Error')
                self.error_msg.setText('Cannot connect to selected port.')
                self.error_msg.setInformativeText('Failed to execute connectPort()\n'
                                                  'Please select a valid port')
                self.error_msg.setIcon(QMessageBox.Warning)
                self.error_msg.exec()

        elif not available_ports:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Cannot read available port.')
            self.error_msg.setInformativeText('Please try reload port list by click refresh button .')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.exec()

        elif selected_port_index == 0:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Please select a valid port.')
            self.error_msg.setInformativeText('selected_port_index is empty.')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.exec()

    def disconnectPort(self):
        try:
            self.active_device.close()

        except Exception as e:
            print(e)
        if not self.active_device.isOpen():
            print('Connection with port closed')
            print(self.active_device.isOpen())
            # thread stop
            self.comboBox.clear()
            self.comboBox.setEnabled(True)
            self.portConnectButton.setEnabled(True)
            self.portDisconnectButton.setEnabled(False)

    def drawLineROI(self):
        # self.caliBoxLabel.setEnabled(True)
        self.camBoxCanvasLabel.setEnabled(True)
        self.applyROIButton.setEnabled(True)
        self.resetROIButton.setEnabled(True)

        # highlight the line button and gray the rest
        self.drawLineButton.setStyleSheet("QPushButton"
                                         "{"
                                         "background-color : QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);"
                                         "}"
                                         )
        self.drawRectButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )
        self.drawCircButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )
        # self.camBoxLabel.lower()
        self.camBoxCanvasLabel.raise_()
        self.camBoxCanvasLabel.drawLine()

    def drawRectROI(self):
        '''
        set rectangle flag to true to draw circle shape
        '''
        self.camBoxCanvasLabel.setEnabled(True)
        self.applyROIButton.setEnabled(True)
        self.resetROIButton.setEnabled(True)
        # highlight the rect button and gray the rest
        self.drawRectButton.setStyleSheet("QPushButton"
                                          "{"
                                          "background-color : QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);"
                                          "}"
                                          )
        self.drawLineButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )
        self.drawCircButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )
        # self.camBoxLabel.lower()
        self.camBoxCanvasLabel.raise_()
        self.camBoxCanvasLabel.drawRect()

    def drawCircROI(self):
        '''
        set circle flag to true to draw circle shape
        '''
        self.camBoxCanvasLabel.setEnabled(True)
        self.applyROIButton.setEnabled(True)
        self.resetROIButton.setEnabled(True)

        # Highlight circ button and gray the rest
        self.drawCircButton.setStyleSheet("QPushButton"
                                          "{"
                                          "background-color : QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);"
                                          "}"
                                          )
        self.drawLineButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )
        self.drawRectButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )
        # self.camBoxLabel.lower()
        self.camBoxCanvasLabel.raise_()
        self.camBoxCanvasLabel.drawCirc()


    def applyROI(self):

        # print(self.camBoxCanvasLabel.zones[0].contains(100, 100))
        self.trackingCamThread.zones = self.camBoxCanvasLabel.zones
        self.controllerThread.zones = self.camBoxCanvasLabel.zones

        print(self.controllerThread.zones)

        self.applyROIButton.setEnabled(False)
        self.drawLineButton.setEnabled(False)
        self.drawRectButton.setEnabled(False)
        self.drawCircButton.setEnabled(False)
        #
        self.camBoxCanvasLabel.setEnabled(False)
        # gray all button
        self.drawLineButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )
        self.drawRectButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )
        self.drawCircButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )

    def clearControlROI(self):

        # self.trackingCamThread.ROI_coordinate = None
        # self.controllerThread.ROI_coordinate = None
        self.applyROIButton.setEnabled(False)
        self.drawLineButton.setEnabled(True)
        self.drawRectButton.setEnabled(True)
        self.drawCircButton.setEnabled(True)
        self.camBoxCanvasLabel.erase()
        self.camBoxCanvasLabel.setEnabled(False)
        self.camBoxCanvasLabel.lower()

        # Gray all button
        self.drawLineButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )
        self.drawRectButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )
        self.drawCircButton.setStyleSheet("QPushButton"
                                         "{"
                                         "QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);"
                                         "}"
                                         )


class Detection():

    def __init__(self):
        super().__init__()

    def create_mask(self,mask_file):
        """
        this function is to create a mask image for analyzed frame
        Parameters
        ----------
        mask_file : the colored image used as mask, must have same shape with the frame
        """
        mask = cv2.imread(mask_file, 1)
        # mask_resize = cv2.resize(mask_gray,(1024,576))
        mask_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        # cv2.threshold() return 2 values
        ret,mask_th = cv2.threshold(mask_gray, 10, 255, cv2.THRESH_BINARY_INV)
        return mask_th

    def apply_mask(self,raw_mask, raw_vid):
        """
        this function perform biwise operation
        apply mask on video
        Parameters
        ----------
        raw_mask : inverted mask image created by create_mask()
        raw_vid : the source video which mask will be apply on

        """
        mask_inv = cv2.bitwise_not(raw_mask)
        bitwise_mask = cv2.bitwise_and(raw_vid, raw_vid, mask=mask_inv)
        return bitwise_mask

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
    cam_signal = pyqtSignal(QImage)
    thresh_signal = pyqtSignal(QImage)
    cam_thresh_signal = pyqtSignal(QImage)
    thresh_preview = pyqtSignal(QImage)
    cam_thresh_preview = pyqtSignal(QImage)
    thresh_reset = pyqtSignal(str)
    updateSliderPos = QtCore.pyqtSignal(float)
    tracking_signal = pyqtSignal(QImage)
    cam_tracking_signal = pyqtSignal(QImage)
    tracked_object = pyqtSignal(list)
    cam_tracked_object = pyqtSignal(list)
    tracked_index = pyqtSignal(int)
    tracked_elapse = pyqtSignal(str)
    track_reset = pyqtSignal(str)
    track_reset_alarm = pyqtSignal(str)
    cam_alarm = pyqtSignal(str)


class CameraThread(QThread):

    def __init__(self):
        QThread.__init__(self)
        self.timeSignal = Communicate()
        self.mutex = QMutex()
        self.stopped = False

    def run(self):
        with QMutexLocker(self.mutex):
            self.stopped = False
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            while True:
                if self.stopped:
                    cap.release()
                    return
                else:
                    ret, frame = cap.read()
                    if ret:
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                           QImage.Format_RGB888)
                        frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
                        self.setPixmap.emit(frame_scaled)
                        self.timeSignal.cam_signal.emit(frame_scaled)
                    else:
                        # call reloadCamera() to try reload camera
                        self.timeSignal.cam_alarm.emit('1')
                        return
        except:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Failed to open camera.')
            self.error_msg.setInformativeText('ThreshCamThread.run() failed\n'
                                              'Please make sure camera is connected with computer.\n')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.setDetailedText('You caught a bug! \n'
                                           'Please submit this issue on GitHub to help us improve. ')
            self.error_msg.exec()

    def stop(self):
        # self.setPixmap.emit(QImage())
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped


class ThreshVidThread(QThread):

    def __init__(self, default_fps=25):
        QThread.__init__(self)
        self.file = ''
        self.mask_img = None
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
        self.apply_mask = False


    def run(self):

        print(type(self.mask_img))
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

                    if self.apply_mask:
                        # bitwise operation
                        masked_frame = self.detection.apply_mask(self.mask_img, frame)

                        if self.invert_contrast:
                            invert_vid = cv2.bitwise_not(masked_frame)

                            thre_vid = self.detection.thresh_video(invert_vid,
                                                                   self.block_size,
                                                                   self.offset)

                            contour_vid, _ = self.detection.detect_contours(masked_frame,
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
                            thre_vid = self.detection.thresh_video(masked_frame,
                                                                   self.block_size,
                                                                   self.offset)

                            contour_vid, _ = self.detection.detect_contours(masked_frame,
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

                    elif not self.apply_mask:

                        if self.invert_contrast:
                            invert_vid = cv2.bitwise_not(frame)

                            thre_vid = self.detection.thresh_video(invert_vid,
                                                                   self.block_size,
                                                                   self.offset)

                            contour_vid, _ = self.detection.detect_contours(frame,
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

                            contour_vid, _ = self.detection.detect_contours(frame,
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
        self.mask_img = None
        self.stopped = False
        self.fps = default_fps
        self.frame_count = -1  # first frame start from 0
        self.timeSignal = Communicate()
        self.mutex = QMutex()
        self.detection = Detection()
        self.trackingMethod = TrackingMethod(30, 60, 100)
        self.trackingDataLog = TrackingDataLog()
        self.playCapture = cv2.VideoCapture()
        self.block_size = 11
        self.offset = 11
        self.min_contour = 1
        self.max_contour = 100
        self.apply_mask = False
        self.invert_contrast = False
        # self.obj_id = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
        #           'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        # create a list of numbers to mark subject indentity
        self.id_list = list(range(1, 100))
        # the elements in this list needs to be in string format
        self.obj_id = [format(x, '01d') for x in self.id_list]
        self.video_elapse = 0

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
                    get_clock = self.trackingDataLog.updateClock()
                    # current position in milliseconds
                    pos_elapse = self.playCapture.get(cv2.CAP_PROP_POS_MSEC)
                    # current position calculated using current frame/fps, used for slider progress
                    play_elapse = self.playCapture.get(cv2.CAP_PROP_POS_FRAMES) / self.playCapture.get(cv2.CAP_PROP_FPS)

                    self.timeSignal.updateSliderPos.emit(play_elapse)

                    self.frame_count += 1

                    # get time stamp mark and store as thread instance
                    # then pass to datalog thread when conditon met
                    is_timeStamp, video_elapse = self.trackingDataLog.localTimeStamp(pos_elapse, interval=None)
                    self.video_elapse = video_elapse

                    if self.apply_mask:

                        # bitwise operation
                        masked_frame = self.detection.apply_mask(self.mask_img, frame)

                        if self.invert_contrast:
                            invert_vid = cv2.bitwise_not(masked_frame)

                            thre_vid = self.detection.thresh_video(invert_vid,
                                                                   self.block_size,
                                                                   self.offset)

                            contour_vid, pos_detection = self.detection.detect_contours(masked_frame,
                                                                                        thre_vid,
                                                                                        self.min_contour,
                                                                                        self.max_contour)

                            self.trackingMethod.identify(pos_detection)

                            ## mark indentity of each objects
                            self.trackingMethod.visualize(contour_vid, self.obj_id, is_centroid=True,
                                                          is_mark=True, is_trajectory=True)

                            # # # pass tracking data to datalog thread when local tracking
                            if is_timeStamp:
                                self.timeSignal.tracked_object.emit(self.trackingMethod.registration)
                                self.timeSignal.tracked_index.emit(self.trackingDataLog.result_index)
                                self.timeSignal.tracked_elapse.emit(self.video_elapse)

                            frame_rgb = cv2.cvtColor(contour_vid, cv2.COLOR_BGR2RGB)

                            frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                               QImage.Format_RGB888)
                            frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)

                            self.timeSignal.tracking_signal.emit(frame_scaled)
                            # time.sleep(1/25)


                        elif not self.invert_contrast:
                            thre_vid = self.detection.thresh_video(masked_frame,
                                                                   self.block_size,
                                                                   self.offset)

                            contour_vid, pos_detection = self.detection.detect_contours(masked_frame,
                                                                                        thre_vid,
                                                                                        self.min_contour,
                                                                                        self.max_contour)

                            self.trackingMethod.identify(pos_detection)

                            ## mark indentity of each objects
                            self.trackingMethod.visualize(contour_vid, self.obj_id, is_centroid=True,
                                                          is_mark=True, is_trajectory=True)

                            # #  pass tracking data to datalog thread when local tracking
                            if is_timeStamp:
                                self.timeSignal.tracked_object.emit(self.trackingMethod.registration)
                                # index of time stamp
                                self.timeSignal.tracked_index.emit(self.trackingDataLog.result_index)
                                self.timeSignal.tracked_elapse.emit(self.video_elapse)
                                print(self.trackingDataLog.result_index)

                            # frame_rgb = cv2.cvtColor(thre_vid, cv2.COLOR_BGR2RGB)
                            frame_rgb = cv2.cvtColor(contour_vid, cv2.COLOR_BGR2RGB)

                            frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                               QImage.Format_RGB888)
                            frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)

                            self.timeSignal.tracking_signal.emit(frame_scaled)
                            # time.sleep(1/25)

                    elif not self.apply_mask:

                        if self.invert_contrast:
                            invert_vid = cv2.bitwise_not(frame)

                            thre_vid = self.detection.thresh_video(invert_vid,
                                                                   self.block_size,
                                                                   self.offset)

                            contour_vid, pos_detection = self.detection.detect_contours(frame,
                                                                                        thre_vid,
                                                                                        self.min_contour,
                                                                                        self.max_contour)

                            self.trackingMethod.identify(pos_detection)

                            ## mark indentity of each objects
                            self.trackingMethod.visualize(contour_vid, self.obj_id, is_centroid=True,
                                                          is_mark=True, is_trajectory=True)

                            # # # pass tracking data to datalog thread when local tracking
                            if is_timeStamp:
                                self.timeSignal.tracked_object.emit(self.trackingMethod.registration)
                                self.timeSignal.tracked_index.emit(self.trackingDataLog.result_index)
                                self.timeSignal.tracked_elapse.emit(self.video_elapse)

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

                            self.trackingMethod.identify(pos_detection)

                            ## mark indentity of each objects
                            self.trackingMethod.visualize(contour_vid, self.obj_id, is_centroid=True,
                                                          is_mark=True, is_trajectory=True)

                            # #  pass tracking data to datalog thread when local tracking
                            if is_timeStamp:
                                self.timeSignal.tracked_object.emit(self.trackingMethod.registration)
                                # index of time stamp
                                self.timeSignal.tracked_index.emit(self.trackingDataLog.result_index)
                                self.timeSignal.tracked_elapse.emit(self.video_elapse)
                                print(self.trackingDataLog.result_index)

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
                    self.timeSignal.track_reset_alarm.emit('1')
                    self.timeSignal.track_reset.emit('1')

                    return

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True
        # print(self.trackingMethod.registration)
        # self.trackingMethod.registration.clear()
        # print(self.trackingMethod.registration)
        # print(self.trackingMethod.registration)
        # self.trackingMethod.registration = []

    def set_fps(self, video_fps):
        self.fps = video_fps


class ThreshCamThread(QThread):

    def __init__(self):
        QThread.__init__(self)
        # self.file = ''
        self.stopped = False
        self.timeSignal = Communicate()
        self.mutex = QMutex()
        self.detection = Detection()
        self.block_size = 3
        self.offset = 2
        self.min_contour = 1
        self.max_contour = 100
        self.invert_contrast = False

    def run(self):

        with QMutexLocker(self.mutex):
            self.stopped = False
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            while True:
                if self.stopped:
                    cap.release()
                    return
                else:
                    ret, frame = cap.read()
                    if ret:
                        # play_elapse = self.playCapture.get(cv2.CAP_PROP_POS_FRAMES) / self.playCapture.get(cv2.CAP_PROP_FPS)
                        # self.timeSignal.updateSliderPos.emit(play_elapse)

                        if self.invert_contrast:
                            invert_cam = cv2.bitwise_not(frame)

                            thre_cam = self.detection.thresh_video(invert_cam,
                                                                   self.block_size,
                                                                   self.offset)

                            contour_cam, _ = self.detection.detect_contours(frame,
                                                                            thre_cam,
                                                                            self.min_contour,
                                                                            self.max_contour)

                            frame_rgb = cv2.cvtColor(contour_cam, cv2.COLOR_BGR2RGB)

                            frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                               QImage.Format_RGB888)
                            frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)

                            self.timeSignal.cam_thresh_signal.emit(frame_scaled)
                            # time.sleep(1/25)

                            # preview thresholded video
                            thcam_rgb = cv2.cvtColor(thre_cam, cv2.COLOR_BGR2RGB)
                            thcam_cvt = QImage(thcam_rgb, thcam_rgb.shape[1], thcam_rgb.shape[0], thcam_rgb.strides[0],
                                               QImage.Format_RGB888)
                            thcam_scaled = thcam_cvt.scaled(320, 180, Qt.KeepAspectRatio)
                            self.timeSignal.cam_thresh_preview.emit(thcam_scaled)

                        elif not self.invert_contrast:
                            thre_cam = self.detection.thresh_video(frame,
                                                                   self.block_size,
                                                                   self.offset)

                            contour_cam, _ = self.detection.detect_contours(frame,
                                                                            thre_cam,
                                                                            self.min_contour,
                                                                            self.max_contour)

                            frame_rgb = cv2.cvtColor(contour_cam, cv2.COLOR_BGR2RGB)

                            frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                               QImage.Format_RGB888)
                            frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)

                            self.timeSignal.cam_thresh_signal.emit(frame_scaled)
                            # time.sleep(1/25)

                            # preview thresholded video
                            thcam_rgb = cv2.cvtColor(thre_cam, cv2.COLOR_BGR2RGB)
                            thcam_cvt = QImage(thcam_rgb, thcam_rgb.shape[1], thcam_rgb.shape[0], thcam_rgb.strides[0],
                                               QImage.Format_RGB888)
                            thcam_scaled = thcam_cvt.scaled(320, 180, Qt.KeepAspectRatio)
                            self.timeSignal.cam_thresh_preview.emit(thcam_scaled)

                    elif not ret:
                        # call reloadCamera() to try reload camera
                        self.timeSignal.cam_alarm.emit('1')
                        return
        except:
            self.error_msg = QMessageBox()
            self.error_msg.setWindowTitle('Error')
            self.error_msg.setText('Failed to open camera.')
            self.error_msg.setInformativeText('ThreshCamThread.run() failed\n'
                                              'Please make sure camera is connected with computer.\n')
            self.error_msg.setIcon(QMessageBox.Warning)
            self.error_msg.setDetailedText('You caught a bug! \n'
                                           'Please submit this issue on GitHub to help us improve. ')
            self.error_msg.exec()

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def set_fps(self, video_fps):
        self.fps = video_fps


class DataLogThread(QThread):

    def __init__(self):
        QThread.__init__(self)
        self.stopped = False
        self.mutex = QMutex()
        # self.trackingDataLog = TrackingDataLog()
        self.df = []
        self.df_archive = []
        # self.dataframe = []
        # self.dataframe_archive = pd.DataFrame()
        # create a list of numbers to mark subject indentity
        self.id_list = list(range(1, 100))
        # the elements in this list needs to be in string format
        self.obj_id = [format(x, '01d') for x in self.id_list]
        self.tracked_object = None
        self.tracked_index = None
        self.tracked_elapse = None

        ## need init object id list
        # self.obj_id = []

    def run(self):
        tic = time.perf_counter()
        with QMutexLocker(self.mutex):
            self.stopped = False
        if self.stopped:
            return
        else:
            # print(range(len(self.tracked_object)))
            for i in range(len(self.tracked_object)):
                self.df.append([self.tracked_index,
                                self.tracked_elapse,
                                self.obj_id[i],
                                self.tracked_object[i].pos_prediction[0][0],
                                self.tracked_object[i].pos_prediction[1][0]])
            # self.dataframe = pd.DataFrame(np.array(self.df),
            #                          columns=['pos_x', 'pos_y'])

            if len(self.df) >= 1000:
                print('len limit 1000')
                # self.df_archive = pd.concat(self.df.copy())
                self.df_archive.extend(self.df.copy())
                del self.df[:]
                # del self.dataframe[:]
                # self.dataframe.clear()
                # return
                # self.dataframe_archive.append(self.df_archive)
            # print(f'log thread update {self.tracked_object}')
            # print(f' datalog thread df len {len(self.df)}')
            # print(f'df{self.df}')
            # print(f'df archive{self.df_archive}')
            # print(self.dataframe_archive)
            # print(self.dataframe_saved)
            # print(len(self.dataframe_saved))
        toc = time.perf_counter()
        # print(f'df archive length {len(self.df_archive)}')
        # print(f'Time Elapsed Per datalog Loop {toc - tic:.3f}')

    def track_data(self, tracked_object):
        '''
        receive the list of registered object information passed
        from tracking thread
        '''
        self.tracked_object = tracked_object

    def track_index(self, tracked_index):
        '''
        receive the index of timestamp passed
        from tracking thread
        '''
        self.tracked_index = tracked_index

    def track_elapse(self, tracked_elapse):
        '''
        receive video time elapsed when time stamp is true passed
        from tracking thread
        '''
        self.tracked_elapse = tracked_elapse

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True


class TrackingCamThread(QThread):

    def __init__(self):
        QThread.__init__(self)

        self.stopped = False
        self.timeSignal = Communicate()
        self.mutex = QMutex()
        self.detection = Detection()
        self.trackingMethod = TrackingMethod(30, 60, 100)
        self.trackingDataLog = TrackingDataLog()

        self.block_size = 3
        self.offset = 2
        self.min_contour = 1
        self.max_contour = 100
        self.invert_contrast = False

        # create a list of numbers to mark subject indentity
        self.id_list = list(range(1, 100))
        # the elements in this list needs to be in string format
        self.obj_id = [format(x, '01d') for x in self.id_list]

        self.fps = 25
        self.video_elapse = 0
        self.frame_count = -1  # first frame start from 0
        self.start_delta = time.perf_counter()

        self.ROI_coordinate = None
        self.zones = None

    def run(self):

        with QMutexLocker(self.mutex):
            self.stopped = False
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

            while True:
                tic = time.perf_counter()
                if self.stopped:
                    cap.release()
                    return
                else:
                    ret, frame = cap.read()
                    if ret:

                        # print(self.ROI_coordinate) # test ROI coordinate is passed

                        # get current date and time
                        get_clock = self.trackingDataLog.updateClock()

                        # absolute time elapsed after start capturing
                        self.end_delta = time.perf_counter()
                        self.elapse_delta = timedelta(seconds=self.end_delta - self.start_delta).total_seconds()

                        self.frame_count += 1
                        # calculate frame rate of living camera source accordingly
                        self.fps = round(self.frame_count / self.elapse_delta)

                        # get time stamp mark
                        is_timeStamp, camera_elapse = self.trackingDataLog.liveTimeStamp(self.fps, self.elapse_delta,
                                                                                   self.frame_count,
                                                                                   interval=None)

                        if self.invert_contrast:
                            invert_cam = cv2.bitwise_not(frame)

                            thre_cam = self.detection.thresh_video(invert_cam,
                                                                   self.block_size,
                                                                   self.offset)

                            contour_cam, pos_detection = self.detection.detect_contours(frame,
                                                                                        thre_cam,
                                                                                        self.min_contour,
                                                                                        self.max_contour)

                            self.trackingMethod.identify(pos_detection)

                            ## mark indentity of each objects
                            self.trackingMethod.visualize(contour_cam, self.obj_id, is_centroid=True,
                                                          is_mark=True, is_trajectory=True)

                            # # # # pass tracking data to datalog thread when local tracking
                            if is_timeStamp:
                                self.timeSignal.cam_tracked_object.emit(self.trackingMethod.registration)
                            #     self.timeSignal.tracked_index.emit(self.trackingDataLog.result_index)
                            #     self.timeSignal.tracked_elapse.emit(self.video_elapse)

                            frame_rgb = cv2.cvtColor(contour_cam, cv2.COLOR_BGR2RGB)

                            frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                               QImage.Format_RGB888)
                            frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)

                            self.timeSignal.cam_tracking_signal.emit(frame_scaled)
                            # time.sleep(1/25)


                        elif not self.invert_contrast:
                            thre_cam = self.detection.thresh_video(frame,
                                                                   self.block_size,
                                                                   self.offset)

                            contour_cam, pos_detection = self.detection.detect_contours(frame,
                                                                                        thre_cam,
                                                                                        self.min_contour,
                                                                                        self.max_contour)

                            self.trackingMethod.identify(pos_detection)

                            ## mark indentity of each objects
                            self.trackingMethod.visualize(contour_cam, self.obj_id, is_centroid=True,
                                                          is_mark=True, is_trajectory=True)

                            # # # # pass tracking data to datalog thread when local tracking
                            if is_timeStamp:
                                 self.timeSignal.cam_tracked_object.emit(self.trackingMethod.registration)
                            #     self.timeSignal.tracked_index.emit(self.trackingDataLog.result_index)
                            #     self.timeSignal.tracked_elapse.emit(self.video_elapse)

                            frame_rgb = cv2.cvtColor(contour_cam, cv2.COLOR_BGR2RGB)

                            frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                               QImage.Format_RGB888)
                            frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)

                            self.timeSignal.cam_tracking_signal.emit(frame_scaled)
                            # time.sleep(1/25)

                        toc = time.perf_counter()
                        # print(f'Time Elapsed Per Loop {toc - tic:.3f}')
                    elif not ret:
                        # video finished
                        print('not ret')
                        # self.timeSignal.track_reset_alarm.emit('1')
                        # self.timeSignal.track_reset.emit('1')

        except:
            print('no cam')

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True
        # print(self.trackingMethod.registration)
        # self.trackingMethod.registration.clear()
        # print(self.trackingMethod.registration)
        # print(self.trackingMethod.registration)
        # self.trackingMethod.registration = []

    def set_fps(self, video_fps):
        self.fps = video_fps


class ControllerThread(QThread):

    def __init__(self):
        QThread.__init__(self)
        self.stopped = False
        self.device = None
        # self.timeSignal = Communicate()
        self.mutex = QMutex()
        self.ROI_coordinate = None
        self.zones = None
        self.tracked_object = []

    def run(self):
        # print('controller thread run')
        with QMutexLocker(self.mutex):
            self.stopped = False

        if self.stopped:
            return

        else:

            for i in range(len(self.tracked_object)):
                    # print(len(TrackingMethod.registration)) # examine number of registrated objects
                # print(f'realtime tracked obj pos {(self.tracked_object[i].pos_prediction[0][0],self.tracked_object[i].pos_prediction[1][0])}')
                if self.zones[0].contains(self.tracked_object[i].pos_prediction[0][0],self.tracked_object[i].pos_prediction[1][0]):

                    print('trigger!')



        #     if self.stopped:
        #         return
        #     self.timeSignal.signal.emit('1')
        #     time.sleep(1 / self.fps)

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def is_stopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped

    def track_data(self, tracked_object):
        '''
        receive the list of registered object information passed
        from live tracking thread
        '''
        self.tracked_object = tracked_object

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    app.setStyleSheet((open('stylesheet.qss').read()))
    # connect subclass with parent class
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
