import pickle
from typing import Hashable
from .si_star import Si_star, player_info_sets
from tree.linprog import row_max_min
from model.helpers import strat_to_idx
from model.induced_tree import Node
from model.action_set import PITCHER_ACTIONS, BATTER_ACTIONS

def list_strategies(target, player_id, root):
    si =  Si_star(target, player_id, root)
    list_strats = []
    for strat in si:
        list_strats.append(strat)
    return list_strats

def load_mixed_strat():
    with open("C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\data\\pitcher_optimal.pkl", 'rb') as file:
        pitcher_strat = pickle.load(file)

    with open("C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\data\\batter_optimal.pkl", 'rb') as file:
        batter_strat = pickle.load(file)
    
    print(f"ps: {pitcher_strat}, bs: {batter_strat}")
    
    return pitcher_strat, batter_strat

def sum_of_strat(root, target, player_id):
    pitcher_strat, batter_strat = load_mixed_strat()
    list_strats = list_strategies(target, player_id, root)
    if player_id == "Pitcher":
        mixed_strat = pitcher_strat
        action_set = PITCHER_ACTIONS
    else: 
        mixed_strat = batter_strat
        action_set = BATTER_ACTIONS
    prob = 0

    for strat in list_strats: 
        print(strat)
        idx = strat_to_idx(strat, len(action_set), action_set)
        prob += mixed_strat[idx]
    return prob

def behavioural_strat(rep: Node, root, player_id):
    strat = {}
    for i in rep.children:
        strat[i] = None
    
    denominator = sum_of_strat(root, rep, player_id)
    for action, node in rep.children.items():
        numerator = sum_of_strat(root, node, player_id)
        strat[action] = numerator/denominator
    
    return strat

def sanity_check(strat): 
    sum = 0
    for i in strat.values():
        sum += i
    assert sum == 1 

def enumerate_behavioural_strat(root, player_id):
    behavioural: dict[Hashable, dict] = {}
    all_info_sets = player_info_sets(root, player_id)
    for info_set, rep in all_info_sets.items(): 
        strat = behavioural_strat(rep, root, player_id)
        behavioural[info_set] = strat