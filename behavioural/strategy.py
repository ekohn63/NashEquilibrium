from collections import deque
import copy
import pickle
from typing import Hashable
from .si_star import Si_star, player_info_sets, path_to_node
from tree.linprog import row_max_min
from model.helpers import strat_to_idx
from model.induced_tree import Node
from model.action_set import PITCHER_ACTIONS, BATTER_ACTIONS

def list_strategies(target, player_id, root):
    si =  Si_star(target, player_id, root)
    list_strats = []
    for strat in si:
        list_strats.append(copy.deepcopy(strat))
    #for strat in list_strats:
    #    print(id(strat))
    return list_strats

def load_mixed_strat():
    with open("C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\data\\pitcher_optimal.pkl", 'rb') as file:
        pitcher_strat = pickle.load(file)

    with open("C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\data\\batter_optimal.pkl", 'rb') as file:
        batter_strat = pickle.load(file)
    
    #print(f"ps: {pitcher_strat}, bs: {batter_strat}")
    
    return pitcher_strat, batter_strat

def load_test_strat():
    pitcher_strat = [0]*(2**9)
    batter_strat = [0]*(2**9)
    for i in range(len(pitcher_strat)):
        pitcher_strat[i] = 1/(2**9)

    batter_strat[5] = 0.2
    batter_strat[31] = 0.2
    batter_strat[100] = 0.2
    batter_strat[421] = 0.2
    batter_strat[500] = 0.1
    batter_strat[506] = 0.05
    batter_strat[508] = 0.05

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
        idx = strat_to_idx(strat, len(action_set), action_set)
        prob += mixed_strat[idx]
    return prob

def behavioural_strat(rep: Node, root, player_id):
    strat = {}
    for i in rep.children:
        strat[i] = None
    
    denominator = sum_of_strat(root, rep, player_id)

    if denominator == 0: 
        for action, node in rep.children.items():
            strat[action] = 1/len(rep.children)     #uniform distribution
    else: 
        for action, node in rep.children.items():
            numerator = sum_of_strat(root, node, player_id)
            strat[action] = numerator/denominator
    
    return strat

def enumerate_behavioural_strat(root, player_id) -> dict:
    behavioural: dict[Hashable, dict] = {}
    all_info_sets = player_info_sets(root, player_id)
    for info_set, rep in all_info_sets.items(): 
        strat = behavioural_strat(rep, root, player_id)
        behavioural[info_set] = strat
        sanity_check(strat)
    return behavioural

#-----------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------
def sanity_check(strat): 
    sum = 0
    for i in strat.values():
        sum += i
    assert sum == 1

#a_l = a_i(x_i^l -> x)
# stack based postorder traversal to find action!
def action_on_path(path, node)->object:
    for vertex, nxt in zip(path, path[1:]):
        if node == vertex:
            action = [action for action, n in node.children.items() if n == nxt]
            return action[0]

def prob_vertex_behav(b_strat: dict[Hashable,dict], target: Node, root: Node, player_id): 
    path = path_to_node(root, target)
    decision_path = []
    for node in path:
        if node.data == player_id: 
            decision_path.append(node)

    prob = 1
    for node in decision_path: 
        info_set = node.info_set
        action = action_on_path(path,node)
        p_onpath = b_strat[info_set][action]
        prob = prob*p_onpath
    return prob

def terminal_nodes(root): 
    terminal = []
    stack = deque([root])
    while stack:
        node = stack.pop()
        if node.children == None:
            terminal.append(node)
        else:
            for child in node.children.values():
                stack.append(child)
    return terminal
# node prob_vertex_mixed is simply sum_of_strat

# p(x;bi,s_i) = p(x;si,s_i) for all x 
# suffices to show p(x;bi) = p(x;si)
# suffices to show p(x;bi) = p(x;si) for only leaf nodes, since probs propegate up!
def check_equivalence(b_strat:dict[Hashable, dict], root, player_id)-> bool: 
    terminal_vertices = terminal_nodes(root)
    for node in terminal_vertices:
        b_prob = prob_vertex_behav(b_strat, node, root, player_id)
        mixed_strat = sum_of_strat(root, node, player_id)
        #print(f"\033[91m prob: \033[0m {b_prob}, \033[91m m_prob: \033[0m {mixed_strat}")
        if b_prob != mixed_strat: 
            return False
    return True