import numpy as np


class KalmanFilter(object):
    def __init__(self, dt, u_x, u_y, std_acc, x_std_meas, y_std_meas):
        """
        :param dt: sampling time (time for 1 cycle)
        :param u_x: acceleration in x-direction
        :param u_y: acceleration in y-direction
        :param std_acc: process noise magnitude
        :param x_std_meas: standard deviation of the measurement in x-direction
        :param y_std_meas: standard deviation of the measurement in y-direction
        """
        # Define sampling time/delta time/time for one loop(step)
        self.dt = dt

        # Intial State
        # Current state estimate (xk)
        # We’ll call our best estimate xk (the mean, elsewhere named μ ),
        # and its covariance matrix Pk.
        # Dimensionality of the state = 4
        # position take 2, velocity take 2
        # (4,1) array
        self.state = np.array([[0], [0], [0], [0]])

        # Define the State Transition Matrix F(4,4)
        # It takes every point original estimate
        # and moves it to a new predicted location,
        # give a new distribution
        self.F = np.array([[1, 0, self.dt, 0],
                            [0, 1, 0, self.dt],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]])

        # Initial Covariance Matrix(4,4)
        # current probability estimate
        # Return a matrix with 1 on the diagonal
        # number of rows = number of rows of the Transition matrix A
        # The identity array is a square array with ones on the main diagonal.
        # the main difference is that with eye the diagonal can may be offset,
        # whereas identity only fills the main diagonal.
        self.P = np.identity(self.F.shape[0])

        # Define the Control Input Matrix B (1,4)
        self.B = np.array([[(self.dt ** 2) / 2, 0],
                            [0, (self.dt ** 2) / 2],
                            [self.dt, 0],
                            [0, self.dt]])

        # Define the  control input
        # changes that not related to the state itself
        #
        self.u = np.array([[u_x], [u_y]])

        # Initial Process Noise Covariance
        # process noise matrix
        # treating the untracked influences as noise with covariance Qk.
        # (4,4) array
        self.Q = np.array([[(self.dt ** 4) / 4, 0, (self.dt ** 3) / 2, 0],
                            [0, (self.dt ** 4) / 4, 0, (self.dt ** 3) / 2],
                            [(self.dt ** 3) / 2, 0, self.dt ** 2, 0],
                            [0, (self.dt ** 3) / 2, 0, self.dt ** 2]]) * std_acc ** 2

        # Define Measurement Mapping Matrix
        # State-Measurement matrix
        # Dimensionality of the measurement = 2 (only acceleration
        # (2,4) array
        self.H = np.array([[1, 0, 0, 0],[0, 1, 0, 0]])

        # Initial Measurement Noise Covariance
        # (2,2) array
        self.R = np.array([[x_std_meas ** 2, 0],
                            [0, y_std_meas ** 2]])

        # Initial last result to hold previous prediction
        self.previousState = np.array([[0], [255]])

    def predict(self):
        '''
        Predict state vector u and variance of uncertainty P (covariance).
        :return:vector of predicted state estimate
        '''

        # Predict state
        # the new best estimate is a prediction made from previous best estimate,
        # plus a correction for known external influences.
        # x_k =F* x(k-1) + B* u(k-1)
        self.state = np.dot(self.F, self.state) + np.dot(self.B, self.u)
        # self.x = self.x.astype(int)
        # Calculate error covariance prediction
        # the new uncertainty is predicted from the old uncertainty,
        # with some additional uncertainty from the environment(noise Q).
        # P= F*P*F' + Q
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q

        self.previousState = self.state  # same last predicted result

        return self.state[0:2]

    def update(self, z, flag):
        '''
        Correct or update state vector x and variance of uncertainty P (covariance)
        :param z: vector of observation/measurements
        :param flag:if "true" , update prediction
        :return: predicted state vector x
        '''
        if not flag:  # update using previous prediction
            self.z = self.previousState
        else:  # update using new detection
            self.z = z
        # Measurement residual
        # The difference between the true measurement z_k
        # and the previous estimated measurement Hx_k
        self.residual = self.z - np.dot(self.H, self.state)

        # Measurement prediction covariance
        # S = H*P*H'+R
        self.S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R

        # Calculate the Kalman Gain
        # K = P * H'* inv(H*P*H'+R)
        self.K = np.dot(self.P,np.dot(self.H.T, np.linalg.inv(self.S)))

        # Update the predicted state
        self.state = self.state + np.dot(self.K, self.residual)
        # self.state = self.state.astype(int)

        # Update error covariance matrix

        # where I is an identify matrix
        # I = np.eye(self.H.shape[1])
        # self.P = (I - (K * self.H)) * self.P

        # self.P = self.P-np.dot(K,np.dot(S,K.T))

        self.P = np.dot(np.identity(self.P.shape[0]) -
                              np.dot(self.K, self.H), self.P)

        return self.state[0:2]
