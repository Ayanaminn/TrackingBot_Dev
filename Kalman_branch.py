import numpy as np
#############################################
# This branch using different initialization matrix
# The predicted result have high deviation compare with Kalman main


class KalmanFilter(object):
    """docstring for KalmanFilter"""

    def __init__(self, dt,stateVariance=0.1,
                 measurementVariance=0.1):

        self.stateVariance = stateVariance
        self.measurementVariance = measurementVariance
        self.dt = dt


        # (4,1)
        self.state = np.array([[0], [1], [0], [1]])

        # State Transition Matrix F (4,4)
        self.F = np.array([[1, self.dt, 0, 0], [0, 1, 0, 0],
                           [0, 0, 1, self.dt], [0, 0, 0, 1]])

        # Initial Covariance Matrix (4,4)
        # The identity array is a square array with ones on the main diagonal.
        #  the main difference is that with eye the diagonal can may be offset,
        #  whereas identity only fills the main diagonal.
        self.P = np.array(self.stateVariance * np.identity(self.F.shape[0]))

        # Define the Control Input Matrix B (1,4)
        self.B = np.array([[self.dt ** 2 / 2], [self.dt],
                            [self.dt ** 2 / 2], [self.dt]])


        self.U = 1


        # process noise matrix (2,4)
        self.Q = np.array([[self.dt ** 4 / 4, self.dt ** 3 / 2, 0, 0],
                            [self.dt ** 3 / 2, self.dt ** 2, 0, 0],
                            [0, 0, self.dt ** 4 / 4, self.dt ** 3 / 2],
                            [0, 0, self.dt ** 3 / 2, self.dt ** 2]])

        # State-Measurement matrix (4,2)
        self.H = np.array([[1, 0, 0, 0], [0, 0, 1, 0]])

        # Measurement Noise Covariance (4,4)
        self.R = np.array(self.measurementVariance * np.identity(self.H.shape[0]))



        self.erroCov = self.P


    """Predict function which predicst next state based on previous state"""

    def predict(self):
        # (4,4)*(4,1)
        self.predictedState = np.dot(self.F,self.state) + np.dot(self.B,self.U)

        self.predictedErrorCov = np.dot(np.dot(self.F , self.erroCov), self.F.T) + self.Q

        temp = np.asarray(self.predictedState)

        return temp[0], temp[2]

    """Correct function which correct the states based on measurements"""

    def correct(self, z):

        self.z = z
        # Measurement residual
        # The difference between the true measurement z_k
        # and the previous estimated measurement Hx_k
        self.residual = self.z - np.dot(self.H, self.predictedState)

        # Measurement prediction covariance
        # S = H*P*H'+R
        self.S = np.dot(self.H, np.dot(self.predictedErrorCov, self.H.T)) + self.R

        # Calculate the Kalman Gain
        # K = P * H'* inv(H*P*H'+R)
        self.kalmanGain = np.dot(self.predictedErrorCov,np.dot(self.H.T,np.linalg.pinv(self.S)))

        # Update the predicted state
        self.state = self.predictedState + np.dot(self.kalmanGain,self.residual)

        # Update error covariance matrix
        # self.P = (I - (K * self.H)) * self.P
        self.erroCov = np.dot(np.identity(self.P.shape[0]) -
                        np.dot(self.kalmanGain,self.H),self.predictedErrorCov)

        temp = np.asarray(self.state)

        return temp[0], temp[2]