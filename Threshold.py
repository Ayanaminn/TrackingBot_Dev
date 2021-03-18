import cv2
import Detection as Detection
import concurrent.futures

class Threshold(object):
    '''
    This class enable threshold video and return the threshold parameters
    '''

    def __init__(self,video_source):

        self.video_source = video_source
        self.camera_num = [0,1,2] # used to set condition when select video source
        ## define constant for color threshold
        ## blocksize_ini: the initial value of block size used for adaptive thresholding
        ## blocksize_max: the max value of block size track bar
        ## offset_ini: the initial value of offset used for adaptive thresholding
        self.blocksize_ini = 13
        self.blocksize_max = 255
        self.offset_ini = 9
        self.offset_max = 100
        ## define constant for contour threshold
        ## cnt_min_th: minimum contour area for threshold
        ## cnt_max_th: maximum contour area for threshold
        self.cnt_lower_ini = 100
        self.cnt_lower_max = 5000
        self.cnt_upper_ini = 1000
        self.cnt_upper_max = 5000


    def selectVideoSource(self):
        # for live camera
        if self.video_source in self.camera_num:
            self.cap = cv2.VideoCapture(self.video_source,cv2.CAP_DSHOW)
        # for local video file
        else:
            self.cap = cv2.VideoCapture(self.video_source)

    def loadThresholdWindow(self):
        '''
        load live video or local file but only for thresholding
        '''
        self.selectVideoSource()
        cv2.namedWindow('Threshold', cv2.WINDOW_GUI_EXPANDED)

        ## create trackbar for blocksize adjust
        cv2.createTrackbar('block size', 'Threshold', self.blocksize_ini, self.blocksize_max, Detection.nothing)
        cv2.createTrackbar('offset', 'Threshold', self.offset_ini, self.offset_max, Detection.nothing)
        cv2.createTrackbar('min range', 'Threshold', self.cnt_lower_ini, self.cnt_lower_max, Detection.nothing)
        cv2.createTrackbar('max range', 'Threshold', self.cnt_upper_ini, self.cnt_upper_max, Detection.nothing)

        while True:
            ret, self.th_vid = self.cap.read()

            ## set parameter for thresholding
            ## read track bar position for each parameter
            self.set_blocksize = cv2.getTrackbarPos('block size', 'Threshold')




            cv2.imshow('Threshold', self.th_vid)


            # wait 1ms if no input continue
            key = cv2.waitKey(1)

            # pause
            if key == ord('p'):
                cv2.waitKey(-1)  # wait until any key is pressed

            # exit
            if key == ord('q'):
                cv2.destroyAllWindows()
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def run(self):
        """
        call input calibration scale function and draw scale function in separate thread
        """

        with concurrent.futures.ThreadPoolExecutor() as executor:
            load_threshold_window = executor.submit(self.loadThresholdWindow)



