
# try:
#     import numpy as np
# except Exception as e:
#     print(e, "\nPlease Install the package")

import cv2
import numpy as np
import pandas as pd
import time
import concurrent.futures
from collections import namedtuple
import memory_profiler
# from Kalman import KalmanFilter
#from Kalman_branch import KalmanFilter
from Threshold import Threshold
from KF_Track import TrackingMethod
from Interactive import DrawObjectWidget
from datetime import datetime, timedelta
from Datalog import TrackingDataLog,CalibrateScale
# import serial
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from sklearn.cluster import MiniBatchKMeans

# video_source = 'zebrafish_video.mp4'
video_source = 0

recording_save_path = datetime.now().strftime('%Y-%m-%d-%H:%M') + '_recording.mp4' # living function
data_save_path = 'data_export_test' + '_tracked.csv'


Mask_file_load = 'mask1.png'

debug = 0 # for debugging script only

mask_on = False

obj_num = 5 #is this still useful?# yes, this will used for data convert
obj_id = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'
          'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
colours = [(0, 0, 255), (0, 255, 255), (255, 0, 255), (255, 255, 255), (255, 255, 0),
           (255, 0, 0),
           (0, 255, 0),
           (0, 0, 0),
           (54, 0, 7),
           (0, 72, 0),
           (8, 77, 134),
           (130, 56, 99),
           (255, 0, 0)]

## define constant for color threshold
## blocksize_ini: the initial value of block size used for adaptive thresholding
## blocksize_max: the max value of block size track bar
## offset_ini: the initial value of offset used for adaptive thresholding
blocksize_ini = 13
offset_ini = 9

# (100,1500)for zebrafish video
cnt_min_th = 100
cnt_max_th = 1500

scaling = 1.0

# for test parameter of kalman filter on the predicted position and updated position
# directly using Kalman.py, do not need if using import from KF_track
# KF = KalmanFilter(0.1, 1, 1, 0.5, 0.1, 0.1)

# same as above but for Kalmanfilter_branch.py test
#KF=KalmanFilter(0.1)

# for KF_track
# dist_thresh, max_undetected_frames, max_trajectory_len
TrackingMethod = TrackingMethod(50, 60, 100)

TrackingDataLog = TrackingDataLog()
CalibrateScale=CalibrateScale(video_source)
Threshold=Threshold(video_source)

codec = 'mp4v' # for living only

## video thresholding
def thresh_video(vid, block_size, offset):
    """
    This function retrieves a video frame and preprocesses it for object tracking.
    The code 1) blurs image to reduce noise
             2) converts it to greyscale
             3) returns a thresholded version of the original image.
             4) perform morphological operation to closing small holes inside objects
    """
    vid = cv2.GaussianBlur(vid, (5, 5), 1)
    # vid = cv2.bilateralFilter(vid,5,50,50)

    vid_gray = cv2.cvtColor(vid, cv2.COLOR_BGR2GRAY)
    vid_th = cv2.adaptiveThreshold(vid_gray,
                                   255,
                                   cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY_INV,
                                   block_size,
                                   offset)
    ## debug mode
    ## tune threshold parameters
    if debug == 1:
        # cv2.namedWindow('blur', cv2.WINDOW_NORMAL)
        # cv2.imshow('blur',vid)
        cv2.namedWindow('gray', cv2.WINDOW_NORMAL)
        cv2.imshow('gray',vid_gray)
        cv2.namedWindow('threshold', cv2.WINDOW_NORMAL)
        cv2.imshow('threshold',vid_th)
    ## Dilation followed by erosion to closing small holes inside the foreground objects
    kernel = np.ones((5, 5), np.uint8)
    vid_closing = cv2.morphologyEx(vid_th, cv2.MORPH_CLOSE, kernel)
    return vid_closing
    # return vid_th


def create_mask(mask_file):
    """
    this function is to create a mask image for analyzed frame
    """
    mask_gray = cv2.cvtColor(mask_file, cv2.COLOR_BGR2GRAY)
    mask_th = cv2.threshold(mask_gray, 10, 255, cv2.THRESH_BINARY_INV)
    return mask_th


def apply_mask(raw_mask, raw_vid):
    """
    this function perform biwise operation
    apply mask on video
    """
    mask_inv = cv2.bitwise_not(raw_mask)
    bitwise_mask = cv2.bitwise_and(raw_vid, raw_vid, mask=mask_inv)
    return bitwise_mask


def detect_contours(vid, masked_th, min_th, max_th):
    """
    vid : original video source
    vid_detect : the masked video
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

    #contours, _ = cv2.findContours(masked_th.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours, _ = cv2.findContours(masked_th.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    vid_draw = vid.copy()
    ## initialize contour number
    i = 0
    ## roll current position to past
    ## clear current position to accept updated value
    pos_detection = []
    pos_archive = pos_detection.copy()
    del pos_detection[:]

    while i < len(contours):
        try:
            ## calculate contour area for current contour
            cnt_th = cv2.contourArea(contours[i])
            ## Under debug mode, print contour area for threshold tuning reference
            if debug == 1:
                print(cnt_th)
            ## delete contour if not meet the threshold
            if cnt_th < min_th or cnt_th > max_th:
                del contours[i]
            ## draw contour if meet the threshold
            else:
                cv2.drawContours(vid_draw, contours, i, (0, 0, 255), 1)
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
        ## when a number is divided by a zero
        except ZeroDivisionError:
            pass
    return vid_draw, contours, pos_detection, pos_archive

def local_video_prop(video_source):

    #total_sec = video_source.get(cv2.CAP_PROP_FRAME_COUNT) / video_source.get(cv2.CAP_PROP_FPS)
    total_sec = video_source.get(cv2.CAP_PROP_FRAME_COUNT) / 25
    video_duraion = str(timedelta(seconds=total_sec))
    video_prop = namedtuple('video_prop',['width','height','fps','length','elapse','duration'])
    get_video_prop= video_prop(video_source.get(cv2.CAP_PROP_FRAME_WIDTH),
                               video_source.get(cv2.CAP_PROP_FRAME_HEIGHT),
                               video_source.get(cv2.CAP_PROP_FPS),
                               video_source.get(cv2.CAP_PROP_FRAME_COUNT),
                               video_source.get(cv2.CAP_PROP_POS_MSEC),
                               video_duraion)

    return get_video_prop

def display_video_prop(video_souce,clock,frame,elapse,video_prop):

    # display current time on video
    cv2.putText(video_souce,
                '{}'.format(clock), (10, int(video_prop.height - 10)),
                1, 1, (0, 0, 255), 2)

    # display current frame on video
    cv2.putText(video_souce,
                'current frame: {}'.format(frame), (250, int(video_prop.height - 10)),
                1, 1, (0, 0, 255), 2)

    # display elapsed video time
    cv2.putText(video_souce,
                f'elapsed time: {elapse}', (450, int(video_prop.height - 10)),
                1, 1, (0, 0, 255), 2)



def main():

    video = cv2.VideoCapture(video_source)
    mask_img = cv2.imread(Mask_file_load, 1)

    get_video_prop = local_video_prop(video)

    cv2.namedWindow('Tracking', cv2.WINDOW_NORMAL)

    print(get_video_prop.fps)
    print(get_video_prop.duration)

    frame_count = -1

    drawingMode = 'Line'
    resetDrawing = False

    #default drawing start coordinates
    ini_start = (0, 0)
    ini_end = (0, 0)

    tracking_data=[]



    print('Memory consumption (before): {}Mb'.format(memory_profiler.memory_usage()))

    # for living only
    fourcc = cv2.VideoWriter_fourcc(*codec)
    output_framesize = (int(video.read()[1].shape[1] * scaling), int(video.read()[1].shape[0] * scaling))
    out = cv2.VideoWriter(filename=recording_save_path, fourcc=fourcc,
                          fps=get_video_prop.fps, frameSize=output_framesize,
                          isColor=True)

    # # test , so direct connect
    # arduino = serial.Serial('COM9', 9600)
    # time.sleep(1)

    # # main for real time
    # while (video.isOpened()):
    #     print('Capturing from real-time camera source')
    #     ret, input_vid = video.read()
    #
    #     cv2.imshow('Test',input_vid)
    #
    #     key = cv2.waitKey(1)
    #
    #     # pause
    #     if key == ord('p'):
    #         cv2.waitKey(-1) # wait until any key is pressed
    #
    #     # exit
    #     if key == ord('q'):
    #         cv2.destroyAllWindows()
    #         break
    # video.release()
    # cv2.destroyAllWindows()

    while True:
        tic = time.perf_counter()
        ret, input_vid = video.read()
        invert_vid = cv2.bitwise_not(input_vid)

        # out.write(input_vid) # for living only
        update_video_prop = local_video_prop(video)

        frame_count += 1

        # pass time stamp parameters to datalog module
        # and return time stamp mark
        get_clock = TrackingDataLog.updateClock()


        is_timeStamp,video_elapse = TrackingDataLog.localTimeStamp(get_video_prop.fps,
                                                                   update_video_prop.elapse,
                                                                   frame_count,
                                                                   interval= None)

        # input_vid = cv2.resize(input_vid,
        #                        None,
        #                        fx=scaling,
        #                        fy=scaling,
        #                        interpolation=cv2.INTER_LINEAR)


        if mask_on == True:
            # create a mask and apply on video
            ret, mask = create_mask(mask_img)
            masked_vid = apply_mask(mask, input_vid)
            th_masked = thresh_video(masked_vid, blocksize_ini, offset_ini)

            contour_vid, cnt, pos_detection, pos_archive = detect_contours(input_vid,
                                                                           th_masked,
                                                                           cnt_min_th,
                                                                           cnt_max_th, )

            TrackingMethod.identify(pos_detection)
            TrackingMethod.visualize(contour_vid,obj_id,is_centroid=True,
                                     is_mark=True,is_trajectory=True)

            # # store tracking data when local tracking
            if is_timeStamp:
                tracking_data = TrackingDataLog.localDataFrame(video_elapse, frame_count, TrackingMethod.registration, obj_id)

            # display video properties on top of video
            display_video_prop(contour_vid, get_clock, frame_count, video_elapse, get_video_prop)


        else:
            th_masked = thresh_video(invert_vid, blocksize_ini, offset_ini)

            contour_vid, cnt, pos_detection, pos_archive = detect_contours(invert_vid,
                                                                           th_masked,
                                                                           cnt_min_th,
                                                                          cnt_max_th, )


        #############test kalman prediction##########################################
            ## Using Kalman.py
            ## test the predicted position and updated position
            ## using the randomball.mp4 video
            ## enable import Kalman as KF and specifiy the arguments
            # (x,y)=KF.predict()
            # print(x,y)
            # (x1,y1)=KF.update(pos_detection[0],1)
            # print(x1,y1)
            # print(pos_detection[0])
         #############################################################################

        #############test kalman prediction##########################################
            ## Using Kalman_branch.py
            ## test the predicted position and updated position
            ## using the randomball.mp4 video
            ## enable import Kalman as KF and specifiy the arguments

            # (x,y)=KF.predict()
            # print(x,y)
            # (x1,y1)=KF.correct(pos_detection[0])
            # print(x1,y1)
            # print(pos_detection[0])
         #############################################################################




        # display current date on video
            pass

            # # # # run tracking method
            # TrackingMethod.identify(pos_detection)
            # TrackingMethod.visualize(contour_vid,obj_id,is_centroid=True,
            #                          is_mark=True,is_trajectory=True)
            #
            # # # store tracking data when local tracking
            # if is_timeStamp:
            #     tracking_data = DataLog.localDataFrame(video_elapse, frame_count, TrackingMethod.registration, obj_id)

            # display video properties on top of video
            display_video_prop(contour_vid,get_clock,frame_count,video_elapse,get_video_prop)



        ## drawing block
        draw_object = DrawObjectWidget(contour_vid)
        draw_start, draw_end = draw_object.drawingPath(ini_start, ini_end)
        draw_object.displayDrawing(draw_start,draw_end,drawingMode)

        # # for condition, use a new function, take draw_start and draw_end as argument
        # # test for arduino position conditioning control
        # for i in range(len(TrackingMethod.registration)):
        #     # print(len(TrackingMethod.registration)) # examine number of registrated objects
        #     print(TrackingMethod.registration[i].pos_prediction[0])
        #     if (TrackingMethod.registration[i].pos_prediction[0] > draw_start[0] and draw_start[0]!= 0):
        #         arduino.write(b'1')
        #     else:
        #         arduino.write(b'0')


        # here or inside the module?
        # if drawingMode == 'Line':
        #     lineLen = ((draw_start[0]-draw_end[0])**2 + (draw_start[1]-draw_end[1])**2)**0.5
        #     print('Length of the line is : {}'.format(lineLen))

        cv2.imshow('Tracking', draw_object.show_image())
        toc = time.perf_counter()
        print(f'Time Elapsed Per Loop {toc - tic:.3f}')

        # wait 1ms if no input continue
        key = cv2.waitKey(1)

        # pause
        if key == ord('p'):
            cv2.waitKey(-1) # wait until any key is pressed

        # exit
        if key == ord('q'):
            cv2.destroyAllWindows()
            break

        # reset not working here, need find a solution

        elif key == ord('m') and drawingMode  == 'Line':
            draw_start, draw_end = ini_start,ini_end
            drawingMode  = 'Rectangle'
            print('Drawing mode : Rectangle')
            continue
        elif key == ord('m') and drawingMode  == 'Rectangle':
            resetDrawing = True
            drawingMode  = 'Circle'
            print('Drawing mode : Circle')
            continue
        elif key == ord('m') and drawingMode == 'Circle':
            resetDrawing = True
            drawingMode = 'Line'
            print('Drawing mode : Line')
            continue
        elif key == ord('c'):
            resetDrawing = True
            continue

    video.release()
    cv2.destroyAllWindows()
    # toc = time.perf_counter()
    # print(f'Time Elapsed Per Loop {toc - tic:.3f}')
    print(f'Memory consumption (after): {memory_profiler.memory_usage()}Mb')

    return tracking_data



if __name__ == '__main__':
    # scale_coordinates, metric, is_metric = CalibrateScale.run()
    # print(f'scale coordinates is {scale_coordinates}, metric is {metric}')
    # pixel_per_metric = CalibrateScale.convertScale(scale_coordinates, metric)
    # print(f'ppm is {pixel_per_metric}')
    #
    # print(is_metric)
    blocksize,offset,cnt_min,cnt_max = Threshold.run()
    # main()
    # is_metric = True
    # is_start = input('start tracking? Y/N')
    # if is_metric and is_start == 'Y':
    #     data = main()
    #     TrackingDataLog.exportData(data, data_save_path)
    #     TrackingDataLog.dataConvert(data_save_path, obj_num, pixel_per_metric)
    #     print('Finished')
    # elif is_start == 'N':
    #     exit()
