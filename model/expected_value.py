from dataclasses import replace
from typing import Tuple, Dict
from .action_set import Nature, BatterAction, PitcherAction
from .induced_tree import Node, build_tree
from .probabilities import converted_dict
from .dynamics import state_dynamics
from .state import START_STATE, State
from .payoff import terminal_utility
from .dynamics import get_utility
import pdb
import traceback
from concurrent.futures import ProcessPoolExecutor


TERMINAL_OUTCOME = [Nature.Single, Nature.Double, Nature.Triple, Nature.HR, Nature.Out]
RED = "\033[91m"
RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def outcome_prob(pitcher_act: PitcherAction, batter_act: BatterAction) -> Dict[str, float]: 
    if batter_act == BatterAction.Swing: 
        b_key = "Swing"
    else: 
        b_key = "Take"
    #if pitcher_act == PitcherAction.Fastball_Bottom:
    #    p_key = ("Bottom", "Fastball")
    if pitcher_act == PitcherAction.Fastball_Middle:
        p_key = ("Middle", "Fastball")
    #elif pitcher_act == PitcherAction.Fastball_Top:
    #    p_key = ("Top", "Fastball")
    #elif pitcher_act == PitcherAction.Fastball_Chase:
    #    p_key = ("Chase", "Fastball")
    #elif pitcher_act == PitcherAction.Offspeed_Bottom:
    #    p_key = ("Bottom", "Offspeed")
    elif pitcher_act == PitcherAction.Offspeed_Middle:
        p_key = ("Middle", "Offspeed")
    #elif pitcher_act == PitcherAction.Offspeed_Top:
    #    p_key = ("Top", "Offspeed")
    #elif pitcher_act == PitcherAction.Offspeed_Chase:
    #    p_key = ("Chase", "Offspeed")
    return converted_dict[p_key][b_key]

def follow_strat(node:Node, ps:list, bs: list):
    explore_nodes = []
    new_ps = ps
    new_bs = bs
    if node.data == "Pitcher":
        #print(f"ps = {ps}")
        decision = ps[node.info_set]
        explore_nodes.append(node.children[decision])
        #ps.pop(node.info_set)
        #new_ps = ps[1:]
    elif node.data == "Batter":
        #print(f"bs = {bs}")
        decision = bs[node.info_set]
        explore_nodes.append(node.children[decision])
        #bs.pop(node.info_set)
        #new_bs = bs[1:]
    elif node.data == "Nature":
        for decision, child in node.children.items():
            explore_nodes.append(child)

    return explore_nodes, ps, bs

def expected_value(root: Node, ps: Tuple, bs: Tuple, start_state: State = START_STATE):
    """
    ps_list = []
    bs_list = []

    for i in ps: 
        ps_list.append(i)
    for j in bs:
        bs_list.append(j)
    """
    ev = dfs(root, ps, bs, start_state, start_state)
    return ev

def get_prev_strat(node: Node):
    prev_strat = []
    for decision, child in node.parent.children.items():
        if child == node: 
            prev_strat.append(decision)
    
    grandparent = node.parent.parent
    for decision, child in grandparent.children.items(): 
        if child == node.parent:
            prev_strat.append(decision)
    
    great_grandparent = grandparent.parent
    for decision, child in great_grandparent.children.items():
        if child == grandparent:
            prev_strat.append(decision)
    return prev_strat

def track_path(path: list) -> list: 
    return    

def dfs_worker_child(args):
    child, new_ps, new_bs, start_state, cur_state, unfolding_path_p = args
    try:
        prob = 1
        prev_strat = None
        local_state = cur_state
        if child.data == "Nature":
            prev_strat = get_prev_strat(child)
            prob = float(outcome_prob(prev_strat[2], prev_strat[1])[prev_strat[0]])
            if prev_strat[0] == Nature.Ball:
                local_state = replace(cur_state, balls = cur_state.balls + 1)
            elif prev_strat[0] == Nature.Strike:
                local_state = replace(cur_state, strikes = cur_state.strikes + 1)        
        ev = dfs(child, new_ps, new_bs, start_state, local_state, unfolding_path_p*prob)
        
        return (child,ev)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e  # re-raise so the pool can still crash loudly
  

def dfs(node:Node, ps: dict, bs: dict, start_state: State, cur_state: State, unfolding_path_p: float = 1) -> int:
    if node.children is None:
        #print(f"count: ({cur_state.balls}, {cur_state.strikes})")
        prev_strat = get_prev_strat(node)
        new_state, runs = state_dynamics(cur_state, prev_strat[0])
        utility = terminal_utility(start_state, new_state, runs)
        #print(f"{CYAN}utility: {utility}{RESET}, unfolding_path_p: {unfolding_path_p}")
        term_ev = unfolding_path_p*utility
        #print(f"{GREEN}terminal_ev: {term_ev}{RESET}")
        return term_ev
    
    #print(f"{node.data}, {node}")
    ev = 0
    # recurse on the child given by the strategy
    # follow the strategy for the subtree - so if it is a decision node only one child, but if it is a
    # nature node, it is all the children
    explore_nodes, new_ps, new_bs = follow_strat(node, ps, bs)

    #spawn worker processes
    #if node.parent == None: # only split the children of the root into new processes 
    #    print(f"\033[94m {node.data}, {[node for node in explore_nodes]} len: {len(explore_nodes)} \033[0m")
    #    for child in explore_nodes:
    #        task_args = [(child, new_ps, new_bs, start_state, cur_state, unfolding_path_p) for child in explore_nodes]
    #        with ProcessPoolExecutor() as executor:
    #            for child, result in executor.map(dfs_worker_child, task_args):
    #                print(f"\033[91m [depth 1] child={child}  EV={result:.6f} \033[0m")
    #                ev += result
    #    return ev
    
    # -------- Serial branch (depth > 0 or only 1 child) -------
    for child in explore_nodes:
        prob = 1
        prev_strat = None
        if node.data == "Nature":
            prev_strat = get_prev_strat(child)
            prob = float(outcome_prob(prev_strat[2], prev_strat[1])[prev_strat[0]])

        if node.data == "Nature" and prev_strat[0] == Nature.Ball:
            cur_state = replace(cur_state, balls = cur_state.balls + 1)
            ev += dfs(child, new_ps, new_bs, start_state, cur_state, unfolding_path_p*prob)

        elif node.data == "Nature" and prev_strat[0] == Nature.Strike:
            cur_state = replace(cur_state, strikes = cur_state.strikes + 1)
            ev += dfs(child, new_ps, new_bs, start_state, cur_state, unfolding_path_p*prob)
        else:
            ev += dfs(child, new_ps, new_bs, start_state, cur_state, unfolding_path_p*prob)

    return ev

if __name__ == "__main__": 
    # demo_dfs.py
    from pitcher_strategies import pitcher_strategy
    from batter_strategies  import batter_strat

    ps = pitcher_strategy(5)   # always first composite pitch
    bs = batter_strat[1000]       # always SWING

    print(f"batter strategy: {bs},\n pitcher strategy: {ps}")
    node = Node(data = "Pitcher")
    root = build_tree(node)
    assert node is root
    print("EV =", expected_value(root, ps, bs))