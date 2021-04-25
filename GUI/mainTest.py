from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QStyle, QApplication,QLabel,QWidget,QGraphicsLineItem
from PyQt5.QtGui import QImage, QPixmap,QPainter, QPen
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QObject, QMutex, QMutexLocker,QRect, QLine
from qtwidgets import Toggle, AnimatedToggle

import os
import cv2
import numpy as np
import time
from collections import namedtuple
from datetime import datetime, timedelta
from scipy.spatial import distance
import threading
import concurrent.futures
import mainGUI
import mainGUI_calibration as Calibration
import mainGUI_detection as Det

class MainWindow(QtWidgets.QMainWindow, mainGUI.Ui_MainWindow):
    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2

    def __init__(self, video_file=''):
        super().__init__()
        self.setupUi(self)

        self.detection = Detection()
        self.thresh_vid = Det.ThresholdVideo()
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
        self.vidProgressBar.valueChanged.connect(self.updatePosition)
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
        self.is_thresholding = False
        # self.threPlayButton.clicked.connect(self.thresh_vid.playControl)
        self.threPlayButton.clicked.connect(self.videoPlayControl)
        self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        # self.threStopButton.clicked.connect(self.thresh_vid.stop)
        self.threStopButton.clicked.connect(self.stopVideo)
        self.threStopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        # receive signal when play button clicked to open current video file
        # self.thresh_vid.setVideo.connect(self.setThresholdVideo)
        # self.thresh_vid.playClicked.connect(self.setPauseIcon)
        # self.thresh_vid.pauseClicked.connect(self.setPlayIcon)
        # self.thresh_vid.resumeClicked.connect(self.setPauseIcon)
        # self.thresh_vid.stopClicked.connect(self.setPlayIcon)

        # receive signal emited from thread of detection module
        # self.thresh_vid.updateThreshDisplay.connect(self.displayThresholdVideo)
        # self.thresh_vid.updateThreshPreview.connect(self.displayThresholdPreview)
        # self.thresh_vid.updateThreshCanvas.connect(self.displayThresholdCanvas)

        self.blockSizeSlider.sliderPressed.connect(self.thresh_vid.pause)
        self.blockSizeSlider.valueChanged.connect(self.setBlockSizeSlider)
        self.blockSizeSlider.sliderReleased.connect(self.thresh_vid.resume)
        self.blockSizeSpin.valueChanged.connect(self.setBlockSizeSpin)

        self.offsetSlider.sliderPressed.connect(self.thresh_vid.pause)
        self.offsetSlider.valueChanged.connect(self.setOffsetSlider)
        self.offsetSlider.sliderReleased.connect(self.thresh_vid.resume)
        self.offsetSpin.valueChanged.connect(self.setOffsetSpin)

        self.cntMinSlider.sliderPressed.connect(self.thresh_vid.pause)
        self.cntMinSlider.valueChanged.connect(self.setMinCntSlider)
        self.cntMinSlider.sliderReleased.connect(self.thresh_vid.resume)
        self.cntMinSpin.valueChanged.connect(self.setMinCntSpin)

        self.cntMaxSlider.sliderPressed.connect(self.thresh_vid.pause)
        self.cntMaxSlider.valueChanged.connect(self.setMaxCntSlider)
        self.cntMaxSlider.sliderReleased.connect(self.thresh_vid.resume)
        self.cntMaxSpin.valueChanged.connect(self.setMaxCntSpin)

        self.previewBoxLabel.lower()
        self.previewToggle = Toggle(self.threTab)
        self.previewToggle.setGeometry(QRect(1150, 360, 60, 35))
        self.previewToggle.lower()
        self.previewToggle.stateChanged.connect(self.enableThrePreview)

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
            # pass video prop to threshold tab
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

                if not self.is_thresholding:
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

                elif self.is_thresholding:

                    th_masked = self.detection.thresh_video(frame,
                                                            13,
                                                            13)
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self.detection.detect_contours,
                                                 frame,
                                                 th_masked,
                                                 50,
                                                 150)
                        contour_vid, cnt, pos_detection, pos_archive = future.result()

                    frame_rgb = cv2.cvtColor(contour_vid, cv2.COLOR_BGR2RGB)

                    frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
                                       QImage.Format_RGB888)
                    frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
                    frame_display = QPixmap.fromImage(frame_scaled)
                    self.threBoxLabel.setPixmap(frame_display)

                    # preview thresholded video
                    thvid_rgb = cv2.cvtColor(th_masked, cv2.COLOR_BGR2RGB)
                    thvid_cvt = QImage(thvid_rgb, thvid_rgb.shape[1], thvid_rgb.shape[0], thvid_rgb.strides[0],
                                       QImage.Format_RGB888)
                    thvid_scaled = thvid_cvt.scaled(320, 180, Qt.KeepAspectRatio)
                    # self.updateThreshPreview.emit(thvid_scaled)
                    preview_display = QPixmap.fromImage(thvid_scaled)
                    self.previewBoxLabel.setPixmap(preview_display)

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

        # self.vidProgressBar.valueChanged.connect(self.updatePosition)

        self.threPosLabel.setText('0:00:00')
        self.threLenLabel.setText(f'{str(vid_prop.duration).split(".")[0]}')
        self.threProgressBar.setRange(1, vid_prop.length)
        self.threProgressBar.setValue(1)

        self.threProgressBar.setSingleStep(int(vid_prop.fps)*5) # 5 sec
        self.threProgressBar.setPageStep(int(vid_prop.fps)*60) # 60 sec

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
        print('thretab enabled')
        self.tabWidget.setTabEnabled(3, True)
        self.tabWidget.setCurrentIndex(3)
        self.is_thresholding = True
        self.resetVideo()
        print(self.video_file[0])
        print(self.playCapture.isOpened())

    def setBlockSizeSlider(self):
        block_size = self.blockSizeSlider.value()
        # block size must be an odd value
        if block_size % 2 == 0:
            block_size += 1
        if block_size < 3:
            block_size = 3
        self.blockSizeSpin.setValue(block_size)
        # self.thresh_vid.block_size = block_size
        self.thresh_vid.updateBlockSize(block_size)

    def setBlockSizeSpin(self):
        block_size = self.blockSizeSpin.value()
        if block_size % 2 == 0:
            block_size += 1
        if block_size < 3:
            block_size = 3
        self.blockSizeSlider.setValue(block_size)
        # self.thresh_vid.block_size = block_size
        self.thresh_vid.updateBlockSize(block_size)

    def setOffsetSlider(self):
        offset = self.offsetSlider.value()
        self.offsetSpin.setValue(offset)
        self.thresh_vid.updateOffset(offset)

    def setOffsetSpin(self):
        offset = self.offsetSpin.value()
        self.offsetSlider.setValue(offset)
        self.thresh_vid.updateOffset(offset)

    def setMinCntSlider(self):
        min_cnt = self.cntMinSlider.value()
        self.cntMinSpin.setValue(min_cnt)
        self.thresh_vid.updateMinCnt(min_cnt)

    def setMinCntSpin(self):
        min_cnt = self.cntMinSpin.value()
        self.cntMinSlider.setValue(min_cnt)
        self.thresh_vid.updateMinCnt(min_cnt)

    def setMaxCntSlider(self):
        max_cnt = self.cntMaxSlider.value()
        self.cntMaxSpin.setValue(max_cnt)
        self.thresh_vid.updateMaxCnt(max_cnt)

    def setMaxCntSpin(self):
        max_cnt = self.cntMaxSpin.value()
        self.cntMaxSlider.setValue(max_cnt)
        self.thresh_vid.updateMaxCnt(max_cnt)
    # def run(self):
    #     """
    #     call input calibration scale function and draw scale function in separate thread
    #     """
    #
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #
    #         cali_num_imput = executor.submit(self.metricNumInput.text())
    #         line_scale = executor.submit(self.caliBoxCanvasLabel.logdata(self))
    #         metric = cali_num_imput.result()
    #         scale = line_scale.result()
    #         print(f'metric is {metric}')
    #         print(f'scale is {scale}')
    #
    #     return scale, metric


    def setPauseIcon(self):

        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    def setPlayIcon(self):

        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.threPlayButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def setThresholdVideo(self):
        self.playCapture.open(self.video_file[0])

    def displayThresholdCanvas(self, canvas_frame):

        frame_display = QPixmap.fromImage(canvas_frame)
        self.threBoxLabel.setPixmap(frame_display)

    # def displayThresholdVideo(self):
    #
    #     print(self.playCapture.isOpened())
    #     if self.playCapture.isOpened():  # when click the play button that connected with playVideo function
    #
    #         ret, frame = self.playCapture.read()
    #         if ret:
    #             play_elapse = self.playCapture.get(cv2.CAP_PROP_POS_FRAMES)
    #             # # update slider position and label
    #             # self.threProgressBar.setSliderPosition(play_elapse)
    #             # self.threPosLabel.setText(f"{str(timedelta(seconds=play_elapse)).split('.')[0]}")
    #
    #             th_masked = self.detection.thresh_video(frame,
    #                                                     self.thresh_vid.block_size,
    #                                                     self.thresh_vid.offset)
    #
    #             with concurrent.futures.ThreadPoolExecutor() as executor:
    #                 future = executor.submit(self.detection.detect_contours,
    #                                          frame,
    #                                          th_masked,
    #                                          self.thresh_vid.min_contour,
    #                                          self.thresh_vid.max_contour)
    #                 contour_vid, cnt, pos_detection, pos_archive = future.result()
    #
    #             frame_rgb = cv2.cvtColor(contour_vid, cv2.COLOR_BGR2RGB)
    #
    #             frame_cvt = QImage(frame_rgb, frame_rgb.shape[1], frame_rgb.shape[0], frame_rgb.strides[0],
    #                                QImage.Format_RGB888)
    #             frame_scaled = frame_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
    #             frame_display = QPixmap.fromImage(frame_scaled)
    #             self.threBoxLabel.setPixmap(frame_display)
    #
    #             # preview thresholded video
    #             thvid_rgb = cv2.cvtColor(th_masked, cv2.COLOR_BGR2RGB)
    #             thvid_cvt = QImage(thvid_rgb, thvid_rgb.shape[1], thvid_rgb.shape[0], thvid_rgb.strides[0],
    #                                QImage.Format_RGB888)
    #             thvid_scaled = thvid_cvt.scaled(320, 180, Qt.KeepAspectRatio)
    #             # self.updateThreshPreview.emit(thvid_scaled)
    #             preview_display = QPixmap.fromImage(thvid_scaled)
    #             self.previewBoxLabel.setPixmap(preview_display)
    #         # elif not ret:
    #         #     # video finished
    #         #     self.thresh_vid.reset()
    #         #     self.setPlayIcon()
    #         #     print('thre vid reset')
    #         #     return

    def enableThrePreview(self):
        # enable real time preview window of threshold result
        if self.previewToggle.isChecked():
            self.previewBoxLabel.raise_()
        else:
            self.previewBoxLabel.lower()



    def enalbleApplyMask(self):
        if self.applyMaskcheckBox.isChecked():
            self.thresh_vid.apply_mask = True
            self.thresh_vid.loadMask()
            # need to reset video
            # or force user select before threshold
        else:
            self.thresh_vid.apply_mask = False



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


class Detection():

    def __init__(self):
        super().__init__()


    ## video thresholding
    def thresh_video(self,vid, block_size, offset):
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
        #vid = cv2.blur(vid, (5, 5))
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

        # print('contour lens is '+ str(len(contours)))
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
                # print(f'cnt area for i is {cnt_th}')
                ## delete contour if not meet the threshold
                if cnt_th < min_th or cnt_th > max_th:
                    del contours[i]
                ## draw contour if meet the threshold
                else:
                    print('cv2 draw contours')
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
                    ## continue to next contour
                    i += 1
                    print(f'i = {i}')
            ## when a number is divided by a zero
            except ZeroDivisionError:
                pass
        return vid_draw, contours , pos_detection, pos_archive

    def nothing(x):
        """
        call back function for track bar
        """
        pass

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)

    # connect subclass with parent class
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
