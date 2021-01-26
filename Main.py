import time as time
import cv2
import Detection as det
from Tracking import TrackingMethod

video_source = 'zebrafish_video.mp4'

Mask_file_load = 'mask1.png'
mask_on = False

## number of objects to be detected in video
obj_num = 11
obj_id = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'
                                                                           'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W',
          'X', 'Y', 'Z']
colours = [(0, 0, 255), (0, 255, 255), (255, 0, 255), (255, 255, 255), (255, 255, 0),
           (255, 0, 0),
           (0, 255, 0),
           (0, 0, 0),
           (54, 0, 7),
           (0, 72, 0),
           (8, 77, 134),
           (130, 56, 99),
           (255, 0, 0)]

# if true,show centroid and object id,otherwise not
mark_on = 0

## define constant for color threshold
## blocksize_ini: the initial value of block size used for adaptive thresholding
## blocksize_max: the max value of block size track bar
## offset_ini: the initial value of offset used for adaptive thresholding
blocksize_ini = 13
blocksize_max = 255
offset_ini = 9

## define constant for contour threshold
## cnt_min_th: minimum contour area for threshold
## cnt_max_th: maximum contour area for threshold
cnt_min_th = 100
cnt_max_th = 1000

## offset trackbar disabled
# offset_max = 100

scaling = 1.0

# dist_thresh, max_undetected_frames, max_trajectory_len
TrackingMethod = TrackingMethod(50, 60, 100)


def main():
    video = cv2.VideoCapture(video_source)

    cv2.namedWindow('Test', cv2.WINDOW_NORMAL)

    ## create trackbar for blocksize adjust
    cv2.createTrackbar('Block size', 'Test', blocksize_ini, blocksize_max, det.nothing)
    ## disable off set trackbar
    # cv2.createTrackbar('offset', 'Test', offset_ini, offset_max, nothing)

    while True:
        ret, input_vid = video.read()
        mask_img = cv2.imread(Mask_file_load, 1)
        input_vid = cv2.resize(input_vid,
                               None,
                               fx=scaling,
                               fy=scaling,
                               interpolation=cv2.INTER_LINEAR)

        ## set parameter for thresholding
        ## read track bar position
        set_blocksize = cv2.getTrackbarPos('Block size', 'Test')

        # block_size must be odd value
        if set_blocksize % 2 == 0:
            set_blocksize += 1
        if set_blocksize < 3:
            set_blocksize = 3

        ## offset trackbar disabled
        # offs = cv2.getTrackbarPos('Offset', 'Test')

        # set_blocksize =blocksize_ini
        # set_offset = offset_ini

        tic = time.time()
        if mask_on == True:
            ## create a mask and apply on video
            ret, mask = det.create_mask(mask_img)
            masked_vid = det.apply_mask(mask, input_vid)
            ## if disable trackbar, set 2nd arg to blocksize_ini
            th_masked = det.thresh_video(masked_vid, set_blocksize, offset_ini)
            contour_vid, cnt, pos_detection, pos_archive = det.detect_contours(input_vid,
                                                                               th_masked,
                                                                               cnt_min_th,
                                                                               cnt_max_th, )
            TrackingMethod.identify(pos_detection)

            TrackingMethod.visualize(contour_vid, obj_id, is_centroid=True,
                                     is_mark=True, is_trajectory=True)

        else:
            ## if disable trackbar, set 2nd arg to blocksize_ini
            th_masked = det.thresh_video(input_vid, set_blocksize, offset_ini)

            contour_vid, cnt, pos_detection, pos_archive = det.detect_contours(input_vid,
                                                                               th_masked,
                                                                               cnt_min_th,
                                                                               cnt_max_th, )

            TrackingMethod.identify(pos_detection)

            ## mark indentity of each objects
            TrackingMethod.visualize(contour_vid, obj_id, is_centroid=True,
                                     is_mark=True, is_trajectory=True)

        toc = time.time()

        # cv2.imshow('Test', final_vid)
        cv2.imshow('Test', contour_vid)

        print("Time Elapsed Per Loop {:.3f}".format((tic - toc) / 50))


        if cv2.waitKey(1) & 0xFF == ord('q'):
            video.release()
            cv2.destroyAllWindows()
            break

if __name__ == '__main__':
	main()