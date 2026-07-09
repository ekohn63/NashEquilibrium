from collections import defaultdict, deque
from .action_set import NATURE_ACTIONS, BatterAction, PitcherAction
from .induced_tree import Node, build_tree
from .probabilities import converted_dict


def get_outcome_prob(pitcher_act: PitcherAction, batter_act: BatterAction) -> dict[str, float]: 
    if batter_act == BatterAction.Swing: 
        b_key = "Swing"
    else: 
        b_key = "Take"
    if pitcher_act == PitcherAction.Fastball_Bottom:
        p_key = ("Bottom", "Fastball")
    #elif pitcher_act == PitcherAction.Fastball_Middle:
    #    p_key = ("Middle", "Fastball")
    #elif pitcher_act == PitcherAction.Fastball_Top:
    #    p_key = ("Top", "Fastball")
    #elif pitcher_act == PitcherAction.Fastball_Chase:
    #    p_key = ("Chase", "Fastball")
    elif pitcher_act == PitcherAction.Offspeed_Bottom:
        p_key = ("Bottom", "Offspeed")
    #elif pitcher_act == PitcherAction.Offspeed_Middle:
    #    p_key = ("Middle", "Offspeed")
    #elif pitcher_act == PitcherAction.Offspeed_Top:
    #    p_key = ("Top", "Offspeed")
    elif pitcher_act == PitcherAction.Offspeed_Chase:
        p_key = ("Chase", "Offspeed")

    return (converted_dict[p_key][b_key])

"""PSEUDOCODE:
DFS throught tree, at each nature info_set, add the 
"""
# now I also have to add nature info_sets!

def get_prev_action(node: Node):
    parent = node.parent
    batter_choice = next(choice for choice in parent.children if parent.children[choice] is node)

    grandparent = parent.parent
    pitcher_choice = next(choice for choice in grandparent.children if grandparent.children[choice] is parent)

    return (pitcher_choice, batter_choice)

def behave_strat(root:Node)-> dict[int, dict]:
    #behave_strat = defaultdict(dict) # initialize the entries of the dictionary
    behave_strat = {}
    stack = deque([])
    stack.append(root)
    while stack: 
        node = stack.pop()
        if node.data == "Nature":
            behave_strat[node.info_set] = {}
            for choice, child in node.children.items():
                (pitcher_choice, batter_choice) = get_prev_action(node)
                outcome_prob = get_outcome_prob(pitcher_choice, batter_choice)
                behave_strat[node.info_set][choice] = outcome_prob[choice]
        if node.children is not None: 
            for child in node.children.values(): 
                stack.append(child)

    return behave_strat

# node: this funciton would help the expected value function 
# insted of the get_outcome funny business, just call this!

#------------------------------------------------------------------------
# module testing!
if __name__ == "__main__":
    root = Node(data = "Pitcher", info_set = 1)
    root = build_tree(root)
    behavioural = behave_strat(root)
    print(behavioural)