from control import Control


class Coordination:
    """
    Executes actions (discrete), by invoking control commands (continuous).
    """

    def __init__(self):
        self.control = Control()
        self.verbose = False

    def execute_action(self, action, world_model):
        """
        Executes actions by using information from the world model and invoking control commands.
        :param action: Tuple of "actor", "actee" (and "from", "to" in some cases).
        :param world_model: The current world state, to extract information from.
        :return: True if action command was executed successful.
        """
        action_successful = False

        if action == ('initialize', 'arm'):
            object_side_length = world_model.size["object_side_length"]
            # action_successful = self.control.initialize_arm()
            action_successful = self.control.open_hand(object_side_length)
        elif action == ('grab', 'arm', 'target_object', 'table'):
            # pass
            xyz = world_model.xyz["target_object"]
            last_servo_values = world_model.location["servo_values"]
            object_side_length = world_model.size["object_side_length"]
            action_successful = self.control.move_arm_above_xyz(xyz, last_servo_values, object_side_length * 2.0)
            action_successful = self.control.move_arm_above_xyz(xyz, last_servo_values, object_side_length * 0.5)
            action_successful = self.control.close_hand(object_side_length)
            action_successful = self.control.move_arm_above_xyz(xyz, last_servo_values, object_side_length * 2.0)
        elif action == ('put', 'arm', 'target_object', 'container'):
            container_xyz = world_model.xyz["container"]
            last_servo_values = world_model.location["servo_values"]
            object_side_length = world_model.size["object_side_length"]
            action_successful = self.control.move_arm_above_xyz(container_xyz, last_servo_values, 14)
            action_successful = self.control.open_hand(object_side_length)

        return action_successful


if __name__ == '__main__':

    # Sequence for testing
    from world_model import WorldModel
    current_world_model = WorldModel()
    coordination = Coordination()
    coordination.control.send_requests = False
    coordination.control.center_init = False
    coordination.control.detect_last_position = False
    coordination.execute_action(('initialize', 'arm'), current_world_model.current_world_model)
    coordination.execute_action(('grab', 'arm', 'target_object', 'table'), current_world_model.current_world_model)
    coordination.execute_action(('put', 'arm', 'target_object', 'container'), current_world_model.current_world_model)
    import numpy as np
    # target_position = np.array([12.5, -12.5, 2.0]) * coordination.control.scale
    target_position = np.array([20, -20.0, 20]) * coordination.control.scale
    # target_position = np.array([12.5, -12.5, 25]) * coordination.control.scale
    # target_position = np.array([-16, 0.0, 10]) * coordination.control.scale
    # target_position = np.array([-20, -20, 25]) * coordination.control.scale
    # target_position = np.array([0, 0, 0]) * coordination.control.scale
    # target_position = np.array([-13.12, 0.27, 1.5]) * coordination.control.scale
    last_servo_values = current_world_model.current_world_model.location["servo_values"]
    action_successful_test = coordination.control.move_arm(np.array(target_position), last_servo_values)
