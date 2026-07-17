from collections import defaultdict
from model.state import START_STATE
from dataclasses import replace
import numpy as np

from model.dynamics import state_dynamics
from model.induced_tree import Node
from behavioural.si_star import path_to_node
from model.payoff import terminal_utility
from model.nature import behave_strat
from behavioural.strategy import terminal_nodes
#from sequence_form.test import BEHAVE_STRAT

# bfs might work, might build the tfds
def set_sequences(root: Node, player_id):
    my_set = []
    infosets_visited = defaultdict(int)
    def dfs(node: Node, sequence): 
        if node.parent is None: 
            my_set.append(((),))
        if node.children is not None:
            for choice, child in node.children.items():
                if node.data == player_id:
                    if infosets_visited[node.info_set] <= len(node.children):
                        my_set.append((sequence)+((node.info_set,choice),))
                        infosets_visited[node.info_set] += 1
                    dfs(child, (sequence)+((node.info_set,choice),))
                else: 
                    dfs(child, sequence)
    dfs(root, ())
    return my_set


# bfs might work, might build the tfds
def set_sequences2(root: Node, player_id):
    my_set = []
    seen = {((),)}
    # need to add the seen logic else we will ahve duplicate sequences in our sequence list. 
    # Deatiled intuition: 
    def dfs(node: Node, sequence): 
        if node.parent is None: 
            my_set.append(((),))
        if node.children is not None:
            for choice, child in node.children.items():
                if node.data == player_id:
                    new_seq = (sequence) + ((node.info_set, choice),)
                    if new_seq not in seen:    
                        my_set.append((sequence)+((node.info_set,choice),))
                        seen.add(new_seq)
                    dfs(child, (sequence)+((node.info_set,choice),))
                else: 
                    dfs(child, sequence)
    dfs(root, ())
    return my_set

# fix this with the

def construct_node_sequence(path: tuple[Node], player_id):
    sequence: list = []
    for node,nxt in zip(path, path[1:]):
        if node.data == player_id:
            choice = next(choice for choice in node.children if node.children[choice] is nxt)
            entry = (node.info_set, choice)
            sequence.append(entry)
    return tuple(sequence)


#defining a not stupid way of constructing the seuqence defined by a node (the way I have been doing is stupid)
def sequence_of(node, player_id):
    my_list = []

    if node.parent is None: 
        my_list.append(())

    while (node.parent is not None): 
        parent = node.parent
        if parent.data == player_id: 
            choice = next(choice for choice in parent.children if parent.children[choice] == node)
            seq = (parent.info_set, choice)
            my_list.append(seq)
        node = parent

    my_list.reverse()
    return tuple(my_list)

def get_sequence_tuple(root: Node, terminal:Node) -> tuple[tuple]: 
    path = path_to_node(root, terminal)
    nature = construct_node_sequence(path, "Nature")
    node = terminal.parent
    batter_path = path_to_node(root, node)
    batter = construct_node_sequence(batter_path, "Batter")
    node = node.parent
    pitcher_path = path_to_node(root, node)
    pitcher = construct_node_sequence(pitcher_path, "Pitcher")

    return nature, batter, pitcher

def get_terminal_node_payoff(terminal: Node, start_state):
    result = next(choice for choice in terminal.parent.children
                  if terminal.parent.children[choice] == terminal)
    balls, strikes = terminal.parent.count      # count when this pitch was thrown
    pre_state = replace(start_state, balls=balls, strikes=strikes)
    new_state, runs = state_dynamics(pre_state, result)
    return terminal_utility(start_state, new_state, runs)

def get_terminal_prob(root, sequence: tuple, nature_b_strat):
    realization_strat = 1
    for info_set, choice in sequence:
        realization_strat = realization_strat * float(nature_b_strat[info_set][choice])
    return float(realization_strat)

# uses that the sequence to a node for player i is unique 
def compute_payoff_matrix(root: Node):
    leaf_nodes = terminal_nodes(root)
    print(f"\033[91m len: {len(leaf_nodes)} \033[0m")
    pitcher_sequences = set_sequences2(root, "Pitcher")
    batter_sequences = set_sequences2(root, "Batter")
    A = make_matrix(len(batter_sequences), len(pitcher_sequences))
    nature_b_strat = behave_strat(root)
    for terminal in leaf_nodes:
        nature, batter, pitcher = get_sequence_tuple(root, terminal)
        assert nature == sequence_of(terminal, "Nature")
        assert batter == sequence_of(terminal, "Batter")
        assert pitcher == sequence_of(terminal, "Pitcher")
        prob = get_terminal_prob(root, nature, nature_b_strat)
        #print(f"prob: {prob}")
        payoff = get_terminal_node_payoff(terminal, START_STATE)
        #print(f"payoff: {payoff}")
        row = batter_sequences.index(batter)
        column = pitcher_sequences.index(pitcher)
        A[row,column] += prob*payoff
    return A

def make_matrix(rows, columns):
    A = np.zeros((rows,columns), dtype = np.float64)
    return A

def test_perfect_recall(): 
    parent_seq_by_iset = {}

    def dfs(node, seq):
        if not getattr(node, "children", None):
            return
        for action, child in node.children.items():
            next_seq = seq
            if node.data == player_id:
                I = node.info_set
                # check parent sequence consistency
                if I not in parent_seq_by_iset:
                    parent_seq_by_iset[I] = seq
                elif parent_seq_by_iset[I] != seq:
                    print("Imperfect recall at infoset", I,
                        "parent1:", parent_seq_by_iset[I],
                        "parent2:", seq)
                next_seq = seq + ((I, action),)
            dfs(child, next_seq)

"""
---------------------------------------------------------------------------------
 Pseudocode:
dfs -> visit each info set of the tree belonging to player_id
path to infoset
construct sequence from the path to node (each (info_set, act) tuple along the path)
add that sequence to the list of sequences
"""
"""
# I think that above algo is better than building the TFDP for pitcher and player and 
# then traversing that tree. That might be an option to explore as an option and compare
# time
def set_sequences_playeri(root: Node, player_id): 
    my_set = set()
    infoset_visited = {}
    counter = 0
    info_set_c = 0
    def dfs(node: Node): 
        nonlocal counter, info_set_c
        if node.parent == None: 
            my_set.add(()) #add empyt set for the root for both pitcher and batter!
        else:
            if node.parent.data == player_id: 
                path = path_to_node(root, node)
                sequence = construct_node_sequence(path, player_id)
                my_set.add(sequence)
                counter += 1
                #infoset_visited[node.parent.info_set] = infoset_visited[node.parent.info_set] -1
            
        if node.children is not None:
            if node.data == player_id: 
                info_set_c += 1
                print(f"\033[94m {info_set_c} \033[0m")
            #if node.data == player_id: 
            #    if node.info_set not in infoset_visited:
            #        infoset_visited[node.info_set] = len(node.children)
            for choice, child in node.children.items():
                #if node.data == player_id: 
                #    sequence.append((node.info_set, choice))
                dfs(child)
        else:
            return
    dfs(root)
    return my_set
"""