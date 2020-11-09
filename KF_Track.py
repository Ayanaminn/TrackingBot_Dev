import numpy as np
from Kalman import KalmanFilter
# from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment


class TrackList(object):
    """This class register every detected centroids(object)
       to be tracked as a unique object
    Attributes:
        None
    """

    def __init__(self, pos_prediction, object_id_count):
        """Initialize variables used by TrackList class
        Args:
            pos_prediction: predicted centroids(object) to be tracked
            object_id_count: count sequential number as unique identity
                             for each detected centroid(object)
        Return:
            None
        """
        # 1-on-1 correspond detected centroid and count sequential number
        self.object_id = object_id_count
        # Apply Kalman filter
        self.KF = KalmanFilter(1, 1, 1, 1, 0.1, 0.1)
        # Convert the input to an array.
        # predicted centroids (x,y)
        self.pos_prediction = np.asarray(pos_prediction)
        # number of frames a registered object undetected
        self.undetected_frames = 0
        # trace path
        self.trajectory = []


class TrackingMethod(object):
    """This class update detected centroids(objects) and make assignment
    Attributes:
        None
    """

    def __init__(self, dist_thresh, max_undetected_frames, max_trajectory_len):
        """Initialize variable used by Tracker class
        Args:
            dist_thresh: cost (distance) threshold
                         between prediction and detection coordinates
                         as condition to un_assign (delete) the object
                         and register a new object
            max_undetected_frames: maximum allowed frames for
                                   the track object being undetected
                                   as the threshold to un_assign (delete) the object
            max_trajectory_len: trace path history length
            object_id_count: count sequential number as unique identity
                             for each detected centroid(object)
        Return:
            None
        """
        # cost (distance) threshold
        # between prediction and detection coordinates
        # as condition to un_assign (delete) the registration
        self.dist_thresh = dist_thresh
        self.max_undetected_frames = max_undetected_frames
        self.max_trajectory_len = max_trajectory_len
        # an array to hold registered centroids(objects)
        self.registration = []
        self.object_id_count = 0

    def identify(self, pos_detection):
        '''
        Create registration array if no centroids(object) found
        Apply hungarian algorithm to differentiate tracked centroids
        from new detected centroids.
        Cost function is the euclidean distances between centroids
        detected and predicted
        :param pos_detection: a list of (2,1) array
        :return:
        '''

        # If no object is registered
        if (len(self.registration) == 0):
            # for all elements in detected centroids
            for i in range(len(pos_detection)):
                # create an unique object for each of the detected centroids under TrackList class
                # which takes prediction and trackidcount as argument
                # trackidcount = self.trackidcount =trackidcount(in Tracker class)=100
                object = TrackList(pos_detection[i], self.object_id_count)
                self.object_id_count += 1
                # a list of objects(centroids) that detected
                self.registration.append(object)

        # Calculate cost using euclidean distance between
        # predicted and detected centroids
        N = len(self.registration)
        M = len(pos_detection)
        cost = np.zeros(shape=(N, M))  # Cost matrix
        for i in range(len(self.registration)):
            for j in range(len(pos_detection)):
                try:
                    # the ith registered centroids and jth detected centroids
                    diff = self.registration[i].pos_prediction - pos_detection[j]
                    dist = np.sqrt(diff[0][0] * diff[0][0] +
                                   diff[1][0] * diff[1][0])
                    cost[i][j] = dist
                except:
                    pass

        # average the squared ERROR
        cost = (0.5) * cost

        # ################################################
        # An alternative approach to calculate cost
        # result list(pos_detection[i]) index out of range error
        # reason is not understood yet
        #
        # # Calculate cost using euclidean distance between
        # # predicted and detected centroids
        #
        # # Reshape data as array format for cost calculation
        # pos_detection_array = []
        # for arrays in pos_detection:
        #     arrays = arrays.reshape([1, 2])
        #     for subarray in arrays:
        #         pos_detection_array.append(subarray)
        # pos_detection_array = np.array(pos_detection_array)
        #
        # registration_list = []
        # for i in range(len(self.registration)):
        #     pos_prediction = self.registration[i].pos_prediction
        #     registration_list.append(pos_prediction)
        #
        # registration_array =[]
        # for arrays in registration_list:
        #     arrays = arrays.reshape([1,2])
        #     for subarray in arrays:
        #         registration_array.append(subarray)
        # registration_array = np.array(registration_array)
        #
        # # if pos_detection_array.shape != registration_array.shape:
        # #     if pos_detection_array.shape[0] < registration_array.shape[0]:
        # #         while pos_detection_array.shape[0] != registration_array.shape[0]:
        # #             registration_array = np.delete(registration_array, registration_array.shape[0] - 1, 0)
        # #     else:
        # #         result = np.zeros(pos_detection_array.shape)
        # #         result[:registration_array.shape[0], :registration_array.shape[1]] = registration_array
        # #         registration_array = result
        #
        # # cdist: cdist(XA, XB, metric='euclidean', *args, **kwargs)
        # # XA: mA*n  array
        # # XB: mB*n  array
        # # return cost: mA*mB array
        # cost = cdist(pos_detection_array, registration_array)
        # ###########################################################


        # Using Hungarian Algorithm assign the correct detected measurements
        # to predicted tracks
        # define a list to hold assignment
        assignment = []
        # create a empty list ( all value -1) with length N
        # that equals to number of registered c  entroids(objects)
        N = len(self.registration)
        # print(N)
        for _ in range(N):
            assignment.append(-1)
        id_index, id_assign = linear_sum_assignment(cost)
        # fill the list arranged in order of assignment,
        # if id_assign[i]=-1, means ith centroid has no assignment
        # e.g:rw=[0,1,2,3,4],col=[0,3,2,4,1]
        #     assignment=[0,3,2,4,1]
        #  or assignment=[0,3,2,4,1,-1,-1]
        #     ...
        for i in range(len(id_index)):
            assignment[id_index[i]] = id_assign[i]


        ## examine all registered centroids(objects)
        invalid_assignment = []
        for i in range(len(assignment)):
            # if the ith centroid has been assigned
            if (assignment[i] != -1):
                # For all assigned centroids,check for cost distance threshold
                # between prediction and detection.
                # If cost is very high then clear the assignment(not remove object)
                if (cost[i][assignment[i]] > self.dist_thresh):
                    assignment[i] = -1
                    invalid_assignment.append(i)
                pass
            else:
                # if ith centroid has not been assigned
                # recorded how long it has not been assigned
                self.registration[i].undetected_frames += 1

        # If registered centroids(objects) are not assigned for long time,
        # remove them
        del_registration = []
        for i in range(len(self.registration)):
            if (self.registration[i].undetected_frames > self.max_undetected_frames):
                del_registration.append(i)
        # when objects wait for unregister are in the list
        if len(del_registration) > 0:
            for i in del_registration:
                del self.registration[i]
                del assignment[i]

        # If a centroid(object) is not assigned, register it
        for i in range(len(pos_detection)):
            if i not in assignment:
                object = TrackList(pos_detection[i], self.object_id_count)
                self.object_id_count += 1
                self.registration.append(object)

        # Update KalmanFilter state
        for i in range(len(assignment)):
            self.registration[i].KF.predict()
            # if assigned, update
            if (assignment[i] != -1):
                self.registration[i].undetected_frames = 0

                self.registration[i].pos_prediction = self.registration[i].KF.update(
                    pos_detection[assignment[i]], 1)

            # if not assigned (became invaild), keep last result and do not update
            else:
                pass
                # self.registration[i].pos_prediction = self.registration[i].KF.update(
                #     np.array([[0], [0]]), 0)

            # if recorded trajectory counts is over max setting
            if(len(self.registration[i].trajectory) > self.max_trajectory_len):
                # clear the counts
                for j in range(len(self.registration[i].trajectory) - self.max_trajectory_len):
                    del self.registration[i].trajectory[j]

            # record trajectory counts to display
            self.registration[i].trajectory.append(self.registration[i].pos_prediction)

            self.registration[i].KF.previousState = self.registration[i].pos_prediction


