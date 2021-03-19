import time as time
import cv2
from Threshold import Threshold
import Detection as Detection
from Tracking import TrackingMethod
from collections import namedtuple
import memory_profiler
from Interactive import DrawObjectWidget
from datetime import datetime, timedelta
from Datalog import TrackingDataLog, CalibrateScale, TrackingVideoLog

video_source = 0

Mask_file_load = 'mask1.png'
mask_on = False

data_save_path = 'data_export_test' + '_tracked.csv'
recording_save_path = datetime.now().strftime('%Y-%m-%d %H%M') + '.mp4'  # living function
export_fps = 25

## number of objects to be detected in video
obj_num = 5
obj_id = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
          'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
colours = [(0, 0, 255), (0, 255, 255), (255, 0, 255), (255, 255, 255), (255, 255, 0), (255, 0, 0),
           (0, 255, 0), (0, 0, 0), (54, 0, 7), (0, 72, 0), (8, 77, 134), (130, 56, 99), (255, 0, 0)]


scaling = 1.0

# dist_thresh, max_undetected_frames, max_trajectory_len
TrackingMethod = TrackingMethod(50, 60, 100)

# initialize other functional class object
TrackingDataLog = TrackingDataLog()

CalibrateScale = CalibrateScale(video_source)

Threshold=Threshold(video_source)

def main(blocksize,offset,cnt_min, cnt_max):
    video = cv2.VideoCapture(video_source, cv2.CAP_DSHOW)
    mask_img = cv2.imread(Mask_file_load, 1)

    cv2.namedWindow('Tracking', cv2.WINDOW_NORMAL)

    get_video_prop = live_video_prop(video)

    frame_count = -1  # first frame start from 0
    start_delta = time.perf_counter()

    # default drawing start coordinates
    ini_start = (0, 0)
    ini_end = (0, 0)
    drawingMode = 'Line'


    tracking_data = []


    print('Memory consumption (before): {}Mb'.format(memory_profiler.memory_usage()))

    while True:
        ret, input_vid = video.read()
        # mask_img = cv2.imread(Mask_file_load, 1) # this will slow down the perf_counter
        # presumbaly take time to load img in each loop?

        tic = time.perf_counter()

        frame_count += 1

        # absolute time elapsed after start capturing
        end_delta = time.perf_counter()
        elapse_delta = timedelta(seconds=end_delta - start_delta).total_seconds()

        # frame rate of living camera source
        fps = round(frame_count/elapse_delta)

        # get current date and time
        get_clock = TrackingDataLog.updateClock()

        # get time stamp mark
        is_timeStamp, video_elapse = TrackingDataLog.liveTimeStamp(fps,
                                                                   elapse_delta,
                                                                   frame_count,
                                                                   interval=None)

        # VideoLog = TrackingVideoLog(input_vid)
        # VideoLog.exportVideo(recording_save_path,export_fps,get_video_prop)

        # input_vid = cv2.resize(input_vid, None, fx=scaling, fy=scaling,
        #                        interpolation=cv2.INTER_LINEAR)


        if mask_on == True:


            ## create a mask and apply on video
            ret, mask = Detection.create_mask(mask_img)
            masked_vid = Detection.apply_mask(mask, input_vid)
            ## if disable trackbar, set 2nd arg to blocksize_ini
            th_masked = Detection.thresh_video(masked_vid, blocksize, offset)
            contour_vid, cnt, pos_detection, pos_archive = Detection.detect_contours(input_vid,
                                                                                     th_masked,
                                                                                     cnt_min,
                                                                                     cnt_max, )
            TrackingMethod.identify(pos_detection)

            TrackingMethod.visualize(contour_vid, obj_id, is_centroid=True,
                                     is_mark=True, is_trajectory=True)

            # # store tracking data when local tracking
            if is_timeStamp:
                tracking_data = TrackingDataLog.liveDataFrame(get_clock, video_elapse,TrackingMethod.registration, obj_id)

            # display video properties on top of video
            display_video_prop(contour_vid, get_clock, fps, video_elapse, get_video_prop)

        else:
            ## if disable trackbar, set 2nd arg to blocksize_ini
            th_masked = Detection.thresh_video(input_vid, blocksize, offset)

            contour_vid, cnt, pos_detection, pos_archive = Detection.detect_contours(input_vid,
                                                                                     th_masked,
                                                                                     cnt_min,
                                                                                     cnt_max, )

            TrackingMethod.identify(pos_detection)

            ## mark indentity of each objects
            TrackingMethod.visualize(contour_vid, obj_id, is_centroid=True,
                                     is_mark=True, is_trajectory=True)

            # # store tracking data when live tracking
            if is_timeStamp:
                tracking_data = TrackingDataLog.liveDataFrame(get_clock, video_elapse,TrackingMethod.registration, obj_id)

            # display video properties on top of video
            display_video_prop(contour_vid, get_clock, fps, video_elapse, get_video_prop)

        ## drawing block
        draw_object = DrawObjectWidget(contour_vid)
        draw_start, draw_end = draw_object.drawingPath(ini_start, ini_end)
        draw_object.displayDrawing(draw_start, draw_end, drawingMode)

        cv2.imshow('Tracking', draw_object.show_image())
        toc = time.perf_counter()
        print(f'Time Elapsed Per Loop {toc - tic:.3f}')

        # wait 1ms if no input continue
        key = cv2.waitKey(1)

        # pause
        if key == ord('p'):
            cv2.waitKey(-1)  # wait until any key is pressed

        # exit
        if key == ord('q'):
            cv2.destroyAllWindows()
            break

        # reset not working here, need find a solution

        elif key == ord('m') and drawingMode == 'Line':
            draw_start, draw_end = ini_start, ini_end
            drawingMode = 'Rectangle'
            print('Drawing mode : Rectangle')
            continue
        elif key == ord('m') and drawingMode == 'Rectangle':
            resetDrawing = True
            drawingMode = 'Circle'
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

        if cv2.waitKey(1) & 0xFF == ord('q'):
            video.release()
            cv2.destroyAllWindows()
            break

    video.release()
    cv2.destroyAllWindows()
    print(f'Memory consumption (after): {memory_profiler.memory_usage()}Mb')

    return tracking_data


def live_video_prop(video_source):
    """
    read parameters of live camera
    Parameters
    ----------
    video_source

    Returns
    -------
    get_video_prop: a named tuple of video parameter
    """

    video_prop = namedtuple('video_prop', ['width', 'height'])
    get_video_prop = video_prop(video_source.get(cv2.CAP_PROP_FRAME_WIDTH),
                                video_source.get(cv2.CAP_PROP_FRAME_HEIGHT))

    return get_video_prop


def display_video_prop(video_souce, clock, fps, elapse, video_prop):
    """
    Display video parameters while video playing
    Parameters
    ----------
    video_souce
    clock : current time
    fps : video fps
    elapse : absolute time elapsed when video is playing
    video_prop

    Returns
    -------

    """

    # display current time on video
    cv2.putText(video_souce,
                '{}'.format(clock), (10, int(video_prop.height - 10)),
                1, 1, (0, 0, 255), 2)

    # display current fps on video
    cv2.putText(video_souce,
                'FPS: {}'.format(fps), (250, int(video_prop.height - 10)),
                1, 1, (0, 0, 255), 2)

    # display elapsed video time
    cv2.putText(video_souce,
                f'elapsed time: {elapse}', (420, int(video_prop.height - 10)),
                1, 1, (0, 0, 255), 2)


if __name__ == '__main__':
    # scale_coordinates, metric, is_metric = CalibrateScale.run()
    # print(f'scale coordinates is {scale_coordinates}, metric is {metric}')
    # pixel_per_metric = CalibrateScale.convertScale(scale_coordinates, metric)
    # print(f'ppm is {pixel_per_metric}')
    blocksize, offset, cnt_min, cnt_max = Threshold.run()
    is_metric = True
    is_start = input('start tracking? Y/N')
    if is_metric and is_start == 'Y':
        data = main(blocksize, offset, cnt_min, cnt_max)
        TrackingDataLog.exportData(data, data_save_path)
        # TrackingDataLog.dataConvert(data_save_path, obj_num, pixel_per_metric)
        print('Finished')
    elif is_start == 'N':
        exit()



