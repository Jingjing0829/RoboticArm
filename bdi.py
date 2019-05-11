from world_model import WorldModel
from hierarchical_task_network_planner import HierarchicalTaskNetworkPlanner
from collections import deque
from perception import Perception
from monitoring import Monitoring


def print_answers(what, why, how_well, what_else):
    print("What is the robot doing? {}\nWhy is it doing it? {}\nHow well is it doing it? {}\n"
          "What else could it have been doing instead?{}".format(what, why, how_well, what_else))

def filter_intentions(current_beliefs, current_desires, current_intentions):
    for current_intention in current_intentions:
        if current_intention == ('transfer_target_object_to_container', 'arm', 'target_object', 'table', 'container') \
                and current_beliefs.current_world_model.location["target_object"] == "container":
            current_intentions = ""  # if goal(s) achieved, empty I
    return current_intentions


def deliberate(current_beliefs, current_intentions):

    current_desires = current_intentions  # 1. Option Generation: The agent generates a set of possible alternatives.

    # 2. Filtering: Agent chooses between competing alternatives and commits to achieving them.
    current_intentions = filter_intentions(current_beliefs, current_desires, current_intentions)

    return current_intentions


if __name__ == '__main__':

    # max_ticks = 20  # TODO: set it in the property graph
    terminate = False
    SUCCESS = False
    htn_planner = HierarchicalTaskNetworkPlanner()

    goal = [('transfer_target_object_to_container', 'arm', 'target_object', 'table', 'container')]
    intentions = goal  # I = I0 Initial Intentions
    beliefs = WorldModel()  # B = B0 Initial Beliefs
    perception = Perception()
    perception.write_video = True
    monitoring = Monitoring()
    # Disable all 3 monitoring switches for testing
    monitoring.control.send_requests = True
    monitoring.control.center_init = False
    monitoring.control.detect_last_position = True

    what, why, how_well, what_else = "", "", "", ""

    while not SUCCESS and not terminate and beliefs.update_tick() < beliefs.current_world_model.max_ticks:

        percept = {"xyz": {'target_object': perception.get_percept()}}  # get next percept ρ OBSERVE the world
        beliefs = beliefs.belief_revision(percept)

        intentions = deliberate(beliefs, intentions)  # DELIBERATE about what INTENTION to achieve next
        if intentions == "":
            SUCCESS = True

        plans = htn_planner.get_plans(beliefs.current_world_model, intentions)  # π = plan(B, I) MEANS_END REASONING
        if plans != False:
            if len(plans) > 0:
                plans.sort(key=len)  # TODO: check why sorting doesn't work on "deeper" levels
                print("{}: Plan: {}".format(beliefs.current_world_model.tick, plans[0]))
                selected_plan = deque(plans[0])  # TODO: Use a "cost function" to evaluate the best plan, not shortest

                # while len(selected_plan) > 0 and beliefs.update_tick() < max_ticks:
                while len(selected_plan) > 0 and beliefs.update_tick() < beliefs.current_world_model.max_ticks:
                    action, selected_plan = selected_plan.popleft(), selected_plan  # action = hd(π); π = tail(π);

                    print("{}: Action: {}".format(beliefs.current_world_model.tick, action))
                    monitoring.execute_action(action, beliefs.current_world_model)

                    what = action
                    why = intentions
                    how_well = ""
                    what_else = plans[1] if len(plans) > 1 else plans[0]
                    print_answers(what, why, how_well, what_else)

                    # get next percept ρ OBSERVE the world
                    percept = {"xyz": {'target_object': perception.get_percept()}}
                    beliefs = beliefs.belief_revision(percept)

                    if action == ('initialize', 'arm'):  # TODO: for testing only
                        percept = {"initialized": {'arm': True}}  # TODO: post conditions
                        beliefs = beliefs.belief_revision(percept)  # TODO: post conditions
                    elif action == ('grab', 'arm', 'target_object', 'table'):
                        percept = {"grabbed": {'target_object': True}, "initialized": {'arm': False}}
                        beliefs = beliefs.belief_revision(percept)
                    elif action == ('put', 'arm', 'target_object', 'container'):
                        percept = {"location": {"target_object": "container"}, "grabbed": {'target_object': False}}
                        beliefs = beliefs.belief_revision(percept)

                    # if not sound(π, I, B) then
                    #   π = plan(B, I)
        else:
            print("Plan failure_reason: {}".format(htn_planner.failure_reason))

    print("Done.")
    perception.destroy()

    show_history = True
    print("Final World model:")
    print("-- Ticks: {}".format(beliefs.current_world_model.tick))
    print("-- initialized: {}".format(beliefs.current_world_model.initialized))
    print("-- location: {}".format(beliefs.current_world_model.location))
    print("-- grabbed: {}".format(beliefs.current_world_model.grabbed))
    if show_history:
        print()
        print("World model History:")
        for tick in range(len(beliefs.world_model_history)):
            print("Tick {}:".format(tick))
            print("-- initialized: {}".format(beliefs.world_model_history[tick].initialized))
            print("-- location: {}".format(beliefs.world_model_history[tick].location))
            print("-- grabbed: {}".format(beliefs.world_model_history[tick].grabbed))

    print()
    print("{}!".format("SUCCESS" if SUCCESS else "FAIL"))
