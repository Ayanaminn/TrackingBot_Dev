##################################################################
# This module manages thresholding
#
##################################################################
from PyQt5 import QtWidgets
import cv2
import numpy as np
from PyQt5 import  QtCore
from PyQt5.QtCore import Qt,pyqtSignal, QThread,QObject,QMutex,QMutexLocker
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import  QWidget
import time
import mainGUI

class ThreshVidThread(QThread):

    def __init__(self, default_fps=25):
        QThread.__init__(self)

        self.mutex = QMutex()
        self.timeSignal = Communicate()
        self.detection = Detection()
        self.playCapture = cv2.VideoCapture()

        self.mask_img = None
        self.stopped = False
        self.fps = default_fps

        self.block_size = 11
        self.offset = 11
        self.min_contour = 1
        self.max_contour = 100
        self.invert_contrast = False
        self.apply_mask = False
        self.apply_roi_flag = False

        self.roi_coords = (100,100,924,476)

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
                    # get and update video elapse time
                    play_elapse = self.playCapture.get(cv2.CAP_PROP_POS_FRAMES) / self.playCapture.get(cv2.CAP_PROP_FPS)
                    self.timeSignal.updateSliderPos.emit(play_elapse)

                    scale_frame = self.scaleImage(frame)
                    h1,w1 = scale_frame.shape[:2]
                    print(f'scale size {w1,h1}')
                    print(f'roi coords {(self.roi_coords[1],self.roi_coords[3]),(self.roi_coords[0],self.roi_coords[2])}')
                    roi_frame = scale_frame[self.roi_coords[1]:self.roi_coords[3],
                                self.roi_coords[0]:self.roi_coords[2]]

                    h2,w2 = roi_frame.shape[:2]
                    print(f'roi frmae size {w2,h2}')
                    cv2.imshow('roi',roi_frame)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()


                    thre_frame = self.detection.thresh_video(roi_frame,
                                                             self.block_size,
                                                             self.offset)

                    contour_frame, _ = self.detection.detect_contours(scale_frame,
                                                                      thre_frame,
                                                                      self.min_contour,
                                                                      self.max_contour)

                    display_frame = self.convertImage(contour_frame)

                    preview_frame = self.convertPreviewImage(thre_frame)


                    self.timeSignal.thresh_signal.emit(display_frame)  # QPixmap
                    self.timeSignal.thresh_preview.emit(preview_frame)  # QPixmap

                    time.sleep(0.03)


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

    def scaleImage(self,image):
        h,w = image.shape[:2]
        if w > 1024: # shrink
            self._interpolation_flag = cv2.INTER_AREA
        elif w < 1024: # enlarge
            self._interpolation_flag = cv2.INTER_LINEAR

        scale_img = cv2.resize(image, (1024, 576), interpolation=self._interpolation_flag)
        return scale_img

    def convertImage(self, image):
        '''
        convert image to QImage
        :param image:
        :return:
        '''

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_cvt = QImage(image_rgb, image_rgb.shape[1], image_rgb.shape[0], image_rgb.strides[0],
                           QImage.Format_RGB888)
        image_scaled = image_cvt.scaled(1024, 576, Qt.KeepAspectRatio)
        image_display = QPixmap.fromImage(image_scaled)
        return image_display

    def convertPreviewImage(self, image):
        '''
        convert image to QImage
        :param image:
        :return:
        '''

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_cvt = QImage(image_rgb, image_rgb.shape[1], image_rgb.shape[0], image_rgb.strides[0],
                           QImage.Format_RGB888)
        image_scaled = image_cvt.scaled(320, 180, Qt.KeepAspectRatio)
        image_display = QPixmap.fromImage(image_scaled)
        return image_display



class Detection():
    '''
    adaptive thresholding and contour filtering
    '''

    def __init__(self):
        super().__init__()

    def load_mask(self, mask_file):
        """
        this function is to load a mask image for analyzed frame
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

    def apply_ROI(self):
        pass


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
    # thresh_signal = pyqtSignal(QImage)
    thresh_signal = pyqtSignal(QPixmap)
    thresh_preview = pyqtSignal(QPixmap)
    thresh_reset = pyqtSignal(str)
    updateSliderPos = pyqtSignal(float)