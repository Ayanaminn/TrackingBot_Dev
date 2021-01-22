
# try:
#     import numpy as np
# except Exception as e:
#     print(e, "\nPlease Install the package")

import cv2
import numpy as np
import pandas as pd
import time
import memory_profiler
# from Kalman import KalmanFilter
#from Kalman_branch import KalmanFilter
from KF_Track import TrackingMethod
from Interactive import DrawObjectWidget
from datetime import datetime
# import serial
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from sklearn.cluster import MiniBatchKMeans

Video_load = 'zebrafish_video.mp4'
# Video_load = 'randomball.mp4'

Mask_file_load = 'mask1.png'

debug = 0

mask_on = False

obj_num = 1 #is this still useful?
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

mark_on = 0



## define constant for color threshold
## blocksize_ini: the initial value of block size used for adaptive thresholding
## blocksize_max: the max value of block size track bar
## offset_ini: the initial value of offset used for adaptive thresholding
blocksize_ini = 13
offset_ini = 11

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
    # vid = cv2.blur(vid, (5, 5))
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


def nothing(x):
    """
    call back function for trackbar
    """
    pass


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


def data_log():
    now = datetime.now()
    output_filepath = now.strftime('%Y%m%d%H%M')+'_tracked.csv'

df=[]

# tic = time.time()
# print('Memory consumption (before): {}Mb'.format(memory_profiler.memory_usage()))

def main():

    video = cv2.VideoCapture(Video_load)

    cv2.namedWindow('Test', cv2.WINDOW_NORMAL)


    frame_count = 0

    drawingMode = 'Line'
    resetDrawing = False

    #default drawing start coordinates
    ini_start = (0, 0)
    ini_end = (0, 0)

    tic = time.time()
    print('Memory consumption (before): {}Mb'.format(memory_profiler.memory_usage()))

    # # test , so direct connect
    # arduino = serial.Serial('COM9', 9600)
    # time.sleep(1)

    while True:
        ret, input_vid = video.read()
        frame_count += 1

        mask_img = cv2.imread(Mask_file_load, 1)
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

            for i in range(len(TrackingMethod.registration)):
                print(len(TrackingMethod.registration))
                cv2.circle(contour_vid,
                           tuple([int(x) for x in TrackingMethod.registration[i].pos_prediction]),
                           5, (255, 0, 0), -1, cv2.LINE_AA)
                cv2.putText(contour_vid,
                            obj_id[i % len(TrackingMethod.registration)],
                            tuple([int(x) for x in TrackingMethod.registration[i].pos_prediction]),
                            1, 2, (0, 0, 0), 2)

                ## display the trajectory
                if (len(TrackingMethod.registration[i].trajectory) > 1):
                    for j in range(len(TrackingMethod.registration[i].trajectory)):
                        x = int(TrackingMethod.registration[i].trajectory[j][0][0])
                        y = int(TrackingMethod.registration[i].trajectory[j][1][0])
                        cv2.circle(contour_vid, (x, y), 1, (0,255,0), -1)

        else:
            th_masked = thresh_video(input_vid, blocksize_ini, offset_ini)

            contour_vid, cnt, pos_detection, pos_archive = detect_contours(input_vid,
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

            # run tracking method
            TrackingMethod.identify(pos_detection)

            # ## mark indentity of each objects
            for i in range(len(TrackingMethod.registration)):
                # print(len(TrackingMethod.registration)) # examine number of registrated objects
                # print(TrackingMethod.registration[i].pos_prediction[0])
                # display centroid
                cv2.circle(contour_vid,
                           tuple([int(x) for x in TrackingMethod.registration[i].pos_prediction]),
                           1, (255, 0, 0), -1, cv2.LINE_AA)
                # display indentity number
                cv2.putText(contour_vid,
                            obj_id[i % len(TrackingMethod.registration)],
                            tuple([int(x) for x in TrackingMethod.registration[i].pos_prediction]),
                            1, 2, (0, 0, 255), 2)

                # test create output dataframe
                df.append([TrackingMethod.registration[i].pos_prediction[0],
                          TrackingMethod.registration[i].pos_prediction[1],obj_id[i]])


                ## display the trajectory (circle)
                # if (len(TrackingMethod.registration[i].trajectory) > 1):
                #     for j in range(len(TrackingMethod.registration[i].trajectory)):
                #         x = int(TrackingMethod.registration[i].trajectory[j][0][0])
                #         y = int(TrackingMethod.registration[i].trajectory[j][1][0])
                #         cv2.circle(contour_vid, (x, y), 1, (0,255,0), -1)

                # display the trajectory (line)
                if (len(TrackingMethod.registration[i].trajectory) > 1):
                    for j in range(len(TrackingMethod.registration[i].trajectory)-1):
                        x = int(TrackingMethod.registration[i].trajectory[j][0][0])
                        y = int(TrackingMethod.registration[i].trajectory[j][1][0])
                        x1 = int(TrackingMethod.registration[i].trajectory[j+1][0][0])
                        y1 = int(TrackingMethod.registration[i].trajectory[j+1][1][0])
                        cv2.line(contour_vid, (x,y), (x1,y1),
                                 (0,255,0), 1)

        # print(df)

        # display current frame on video
        cv2.putText(contour_vid,
                    '{}'.format(frame_count),(150,50),
                    1, 2, (0, 0, 0), 2)

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

        cv2.imshow('Test', draw_object.show_image())

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

    data = pd.DataFrame(np.array(df), columns=['pos_x', 'pos_y', 'id'])
    data.to_csv('test_datalog.csv', sep=',')

    video.release()
    cv2.destroyAllWindows()
    toc = time.time()
    print("Time Elapsed Per Loop {:.3f}".format((tic - toc)/50))
    print('Memory consumption (after): {}Mb'.format(memory_profiler.memory_usage()))



if __name__ == '__main__':
    main()