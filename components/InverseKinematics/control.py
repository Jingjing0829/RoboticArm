from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink
import matplotlib.pyplot
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from ikpy import geometry_utils
import requests
import time


class Control:

    def __init__(self):

        # send_requests = True
        self.send_requests = False
        self.scale = 0.04  # For the plotting
        # self.scale = 1.0
        self.servo_count = 6
        self.command_delay = 0.05  # seconds
        self.center_init = True
        # self.center_init = False
        self.angle_degree_limit = 75  # degrees
        self.trajectory_steps = 10
        self.current_servo_monotony = [-1.0, -1.0, 1.0, -1.0, -1.0, -1.0]
        self.active_links_mask = [True, True, True, True, False, True]  # Enabled/disabled links
        self.min_steps = 1
        self.max_steps = 5000
        self.rotating_gripper_servo = 2
        self.horizontal_gripper_position = 600
        self.init_position = np.array([0, 0, 1]) * self.scale
        self.init_servo_values = [1500, 1500, 1500, 1500, 1500, 1500]  # TODO: temp

        # Link lengths in centimeters
        self.link6 = np.array([0, 0, 7.0])
        self.link5 = np.array([0, 0, 3.0])
        self.link4 = np.array([0, 0, 10.5])
        self.link3 = np.array([0, 0, 9.0])
        self.link2 = np.array([0, 0, 7.0])
        self.link1 = np.array([0, 0, 10.0])

        # Joint rotation axis
        self.rotation6 = np.array([0, 0, 1])
        self.rotation5 = np.array([0, 1, 0])
        self.rotation4 = np.array([0, 1, 0])
        self.rotation3 = np.array([0, 1, 0])
        self.rotation2 = np.array([0, 0, 1])
        self.rotation1 = np.array([0, 0, 1])

        # Link bounds (degrees)  # TODO: per servo bounds
        self.bounds6 = np.radians(np.array([-self.angle_degree_limit, self.angle_degree_limit]))
        self.bounds5 = np.radians(np.array([-self.angle_degree_limit, self.angle_degree_limit]))
        self.bounds4 = np.radians(np.array([-self.angle_degree_limit, self.angle_degree_limit]))
        self.bounds3 = np.radians(np.array([-self.angle_degree_limit, self.angle_degree_limit]))
        self.bounds2 = np.radians(np.array([-self.angle_degree_limit, self.angle_degree_limit]))
        self.bounds1 = np.radians(np.array([-self.angle_degree_limit, self.angle_degree_limit]))

        self.le_arm_chain = Chain(name='le_arm', active_links_mask=self.active_links_mask, links=[
            URDFLink(
                name="link6",
                translation_vector=self.link6 * self.scale,
                orientation=[0, 0, 0],
                rotation=self.rotation6,
                bounds=self.bounds6
            ),
            URDFLink(
                name="link5",
                translation_vector=self.link5 * self.scale,
                orientation=[0, 0, 0],
                rotation=self.rotation5,
                bounds=self.bounds5
            ),
            URDFLink(
                name="link4",
                translation_vector=self.link4 * self.scale,
                orientation=[0, 0, 0],
                rotation=self.rotation4,
                bounds=self.bounds4
            ),
            URDFLink(
                name="link3",
                translation_vector=self.link3 * self.scale,
                orientation=[0, 0, 0],
                rotation=self.rotation3,
                bounds=self.bounds3
            ),
            URDFLink(
                name="link2",
                translation_vector=self.link2 * self.scale,
                orientation=[0, 0, 0],
                rotation=self.rotation2,
                bounds=self.bounds2
            ),
            URDFLink(
                name="link1",
                translation_vector=self.link1 * self.scale,
                orientation=[0, 0, 0],
                rotation=self.rotation1,
                bounds=self.bounds1
            )
        ])

    def xyz_to_servo_range(self, xyz, current_servo_monotony):
        k = self.le_arm_chain.inverse_kinematics(geometry_utils.to_transformation_matrix(xyz, np.eye(3)))
        k = np.multiply(k, np.negative(current_servo_monotony))
        return self.radians_to_servo_range(k)

    def servo_range_to_xyz(self, servo_range, current_servo_monotony):
        return geometry_utils.from_transformation_matrix(
            self.le_arm_chain.forward_kinematics(
                np.multiply(self.servo_range_to_radians(servo_range), np.negative(current_servo_monotony)),
            ))[0][:3]

    @staticmethod
    def servo_range_to_radians(x, x_min=500.0, x_max=2500.0, scaled_min=(-np.pi / 2.0), scaled_max=(np.pi / 2.0)):
        x_std = (np.array(x) - x_min) / (x_max - x_min)
        return x_std * (scaled_max - scaled_min) + scaled_min

    @staticmethod
    def radians_to_servo_range(x, x_min=(-np.pi / 2.0), x_max=(np.pi / 2.0), scaled_min=500.0, scaled_max=2500.0):
        x_std = (np.array(x) - x_min) / (x_max - x_min)
        return (np.round(x_std * (scaled_max - scaled_min) + scaled_min, 0)).astype(int)

    def get_kinematic_angle_trajectory(self, from_angle_radians_in, to_angle_radians_in, servo_monotony, steps=10):
        assert self.min_steps < steps < self.max_steps

        from_angle_radians = np.multiply(from_angle_radians_in, servo_monotony)
        to_angle_radians = np.multiply(to_angle_radians_in, servo_monotony)

        step_angle_radians = []
        for index in range(len(target_angle_radians)):
            step_angle_radians.append((from_angle_radians[index] - to_angle_radians[index]) / float(steps))

        angle_trajectory = []
        step_angle_radians = np.array(step_angle_radians)
        current_angles = np.array(from_angle_radians)
        # angle_trajectory.append(current_angles)

        for _ in range(steps):
            current_angles = np.add(current_angles, step_angle_radians)
            angle_trajectory.append(current_angles)

        return angle_trajectory


if __name__ == '__main__':

    control = Control()

    # target_position = np.array([12.5, -12.5, 2.0]) * control.scale
    # target_position = np.array([20, -20.0, 20]) * control.scale
    # target_position = np.array([12.5, -12.5, 25]) * control.scale
    # target_position = np.array([-5, -5, 40]) * control.scale
    # target_position = np.array([-16, 0.0, 10]) * control.scale
    # target_position = np.array([-20, -20, 25]) * control.scale
    # target_position = np.array([0, 0, 0]) * control.scale
    target_position = np.array([-13.12, 0.27, 1.5]) * control.scale

    # TODO: init from request
    detect_last_position = False
    if detect_last_position:
        try:
            if control.send_requests:
                url = "http://ESP32/"
                r = requests.put(url, data="")
                # print("r.status_code: ", r.status_code)
                # print("r.text: ", r.text)
                # print("r.encoding: ", r.encoding)
                # print("r.json(): ", r.json())
                # print("r.headers['content-type']: ", r.headers['content-type'])
                # print("servo6: ", r.json()['variables']['servo6'])
                result = r.json()['variables']
                # print("servo6: ", result['servo6'], result['servo5'])
                if r.status_code == 200:
                    result = r.json()["variables"]
                    init_servo_values = np.array(
                        [result["servo6"], result["servo5"], result["servo4"], result["servo3"],
                         result["servo2"], result["servo1"]])

                    # init_servo_radians = np.multiply(servo_range_to_radians(init_servo_values), control.current_servo_monotony)
                    # print("init_servo_radians: ", init_servo_radians)
                    #
                    # print("init_servo_radians: ", np.multiply(servo_range_to_radians(init_servo_values),
                    #                                          control.current_servo_monotony[::-1]))
                    #
                    # init_position2 = le_arm_chain.forward_kinematics(init_servo_radians)
                    # init_position = np.round(servo_range_to_xyz2(init_servo_values, control.current_servo_monotony), 2)
                    # print("predicted_init_position: ", init_position)
                    # print("proper init_position: ", target_position)

        except Exception as e:
            print("Exception: {}".format(str(e)))

    if control.center_init:
        print("Top position (radians): ",
              control.le_arm_chain.inverse_kinematics(geometry_utils.to_transformation_matrix(
                  control.init_position,
                  np.eye(3))))
        ax = matplotlib.pyplot.figure().add_subplot(111, projection='3d')

        control.le_arm_chain.plot(control.le_arm_chain.inverse_kinematics(geometry_utils.to_transformation_matrix(
            control.init_position,
            np.eye(3))), ax, target=control.init_position)
        matplotlib.pyplot.show()

    print("Target angles (radians): ", control.le_arm_chain.inverse_kinematics(geometry_utils.to_transformation_matrix(
        target_position,
        np.eye(3))))
    ax = matplotlib.pyplot.figure().add_subplot(111, projection='3d')

    control.le_arm_chain.plot(control.le_arm_chain.inverse_kinematics(geometry_utils.to_transformation_matrix(
        target_position,
        np.eye(3))), ax,
        target=target_position)
    matplotlib.pyplot.show()

    target_angle_radians = control.le_arm_chain.inverse_kinematics(geometry_utils.to_transformation_matrix(
        target_position,
        np.eye(3)))

    # TODO: test 0
    # target_servo_range = radians_to_servo_range(np.multiply(target_angle_radians, control.current_servo_monotony))
    # kinematic_servo_range_trajectory = get_kinematic_servo_trajectory(init_servo_values, target_servo_range,
    #  trajectory_steps)
    # print("kinematic_servo_range_trajectory (steps: {}): {}".format(trajectory_steps, kinematic_servo_range_
    # trajectory))

    # TODO: test 1
    init_angle_radians = control.le_arm_chain.inverse_kinematics(geometry_utils.to_transformation_matrix(
        control.init_position,
        np.eye(3)))
    kinematic_angle_trajectory = control.get_kinematic_angle_trajectory(init_angle_radians, target_angle_radians,
                                                                        control.current_servo_monotony,
                                                                        control.trajectory_steps)
    print("kinematic_angle_trajectory (steps: {}): {}".format(control.trajectory_steps, kinematic_angle_trajectory))
    print("kinematic_angle_trajectory (steps: {}): {}".format(control.trajectory_steps,
                                                              np.rad2deg(kinematic_angle_trajectory)))
    kinematic_servo_range_trajectory = control.radians_to_servo_range(kinematic_angle_trajectory)
    print("kinematic_servo_range_trajectory (steps: {}): {}".format(control.trajectory_steps,
                                                                    kinematic_servo_range_trajectory))

    # TODO: from to, to-from with MONOTONY
    servo_range1 = control.xyz_to_servo_range(target_position, control.current_servo_monotony)
    target2 = np.round(control.servo_range_to_xyz(servo_range1, control.current_servo_monotony), 2)
    print("\n", target_position, " -> \n",
          servo_range1, " -> \n",
          target2, "\n")

    # TODO: https possible in ESP32? How slower?

    servo_mask = control.active_links_mask  # TODO: servo mask

    if control.send_requests:

        url = "http://ESP32/set_servo{}?value={}".format(control.rotating_gripper_servo,
                                                         control.horizontal_gripper_position)  # TODO: gripper horizontal orientation
        requests.put(url, data="")
        time.sleep(control.command_delay)

        for step in kinematic_servo_range_trajectory:
            for i in range(len(step)):
                if servo_mask[i]:
                    servo_value = step[i]
                    current_servo = control.servo_count - i
                    if current_servo == 1 and servo_value < 1500:  # Gripper MUST be >= 1500
                        servo_value = 1500
                    url = "http://ESP32/set_servo{}?value={}".format(current_servo, servo_value)
                    print(url)
                    try:
                        r = requests.put(url, data="")
                        if r.status_code != 200:
                            break  # TODO: abort
                    except Exception as e:
                        print("Exception: {}".format(str(e)))
                    time.sleep(control.command_delay)
            print("")