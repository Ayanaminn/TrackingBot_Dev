import numpy as np
import cv2
from sklearn.cluster import KMeans

## video thresholding
def thresh_video(vid, block_size, offset):
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
    # return vid_th


def create_mask(mask_file):
    """
    this function is to create a mask image for analyzed frame
    Parameters
    ----------
    mask_file : the colored image used as mask, must have same shape with the frame
    """
    mask_gray = cv2.cvtColor(mask_file, cv2.COLOR_BGR2GRAY)
    mask_th = cv2.threshold(mask_gray, 10, 255, cv2.THRESH_BINARY_INV)
    return mask_th


def apply_mask(raw_mask, raw_vid):
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


def detect_contours(vid, masked_th, min_th, max_th):
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
                ## continue to next contour
                i += 1
        ## when a number is divided by a zero
        except ZeroDivisionError:
            pass
    return vid_draw, contours, pos_detection, pos_archive


def nothing(x):
    """
    call back function for track bar
    """
    pass

## Apply kmeans to seperate contour make performance speed much lower
## Could not use in real-time process

# def apply_k_means(contours, obj_n, pos_now_update):
#     del pos_now_update[:]
#
#     cnt_array = np.vstack(contours)
#     cnt_array = cnt_array.reshape(cnt_array.shape[0], cnt_array.shape[2])
#
#     kmeans = KMeans(n_clusters=obj_n, random_state=42, n_init=5, max_iter=50).fit(cnt_array)
#     l = len(kmeans.cluster_centers_)
#     runs = kmeans.n_iter_
#     for i in range(l):
#         x = int(tuple(kmeans.cluster_centers_[i])[0])
#         y = int(tuple(kmeans.cluster_centers_[i])[1])
#         pos_now_update.append([x, y])
#     return contours, pos_now_update,runs

# def apply_mini_k_means(contours, obj_n, pos_now_update):
#     del pos_now_update[:]
#
#     cnt_array = np.vstack(contours)
#     cnt_array = cnt_array.reshape(cnt_array.shape[0], cnt_array.shape[2])
#
#     kmeans = MiniBatchKMeans(n_clusters=obj_n, random_state=42, batch_size=5).fit(cnt_array)
#     l = len(kmeans.cluster_centers_)
#     runs = kmeans.n_iter_
#     for i in range(l):
#         x = int(tuple(kmeans.cluster_centers_[i])[0])
#         y = int(tuple(kmeans.cluster_centers_[i])[1])
#         pos_now_update.append([x, y])
#     return contours, pos_now_update,runs