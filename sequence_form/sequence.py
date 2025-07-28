from model.state import START_STATE
import numpy as np

from model.dynamics import state_dynamics
from model.induced_tree import Node
from behavioural.si_star import path_to_node
from model.payoff import terminal_utility
from model.nature import behave_strat
from behavioural.strategy import terminal_nodes
""" Pseudocode:
dfs -> visit each info set of the tree belonging to player_id
path to infoset
construct sequence from the path to node (each (info_set, act) tuple along the path)
add that sequence to the list of sequences
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
                print(counter)
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

# bfs might work, might build the tfds
def set_sequences(root: Node, player_id):
    my_set = set()
    infosets_visited = set()
    def dfs(node: Node, sequence): 
        if node.parent is None: 
            my_set.add(())
        if node.children is not None:
            for choice, child in node.children.items():
                if node.data == player_id:
                    if node.info_set not in infosets_visited:
                        new_sequence = sequence + ((node.info_set, choice))
                        my_set.add(new_sequence)
                    dfs(child, new_sequence) 
                else: 
                    dfs(child, sequence)
    dfs(root, ())
    return my_set

def construct_node_sequence(path: tuple[Node], player_id):
    sequence: list = []
    for node,nxt in zip(path, path[1:]):
        if node.data == player_id:
            choice = next(choice for choice in node.children if node.children[choice] is nxt)
            entry = (node.info_set, choice)
            sequence.append(entry)
    return tuple(sequence)

def get_sequence_tuple(terminal) -> tuple[tuple]: 
    path = path_to_node(terminal)
    nature = construct_node_sequence(path, "Nature")
    node = terminal.parent
    batter_path = path_to_node(node)
    batter = construct_node_sequence(batter_path, "Batter")
    node = node.parent
    pitcher_path = path_to_node()
    pitcher = construct_node_sequence(pitcher_path, "Pitcher")

    return nature, batter, pitcher

def get_terminal_node_payoff(terminal: Node, start_state): 
    result = next(choice for choice in terminal.parent.children if terminal.parent.children[choice] == terminal)
    new_state, runs = state_dynamics(start_state, result)
    utility = terminal_utility(start_state, new_state, runs)
    return utility

# r_0(s_0)

def get_terminal_prob(root, sequence: tuple):
    realization_strat = 1
    nature_b_strat = behave_strat(root)
    for info_set, choice in sequence:
        realization_strat = realization_strat * nature_b_strat[info_set][choice]
    return realization_strat


# uses that the sequence to a node for player i is unique 
def compute_payoff_matrix(root: Node):
    terminal_nodes = terminal_nodes(root)
    pitcher_sequences = set_sequences(root, "Pitcher")
    batter_sequences = set_sequences(root, "Batter")
    A = make_matrix(len(batter_sequences), len(pitcher_sequences))
    for terminal in terminal_nodes:
        nature, batter, pitcher = get_sequence_tuple(terminal)
        prob = get_terminal_prob(root, nature)
        payoff = get_terminal_node_payoff(terminal, START_STATE)
        row = batter_sequences.index(batter)
        column = pitcher_sequences.index(pitcher)
        A[row,column] += prob*payoff
    
    return A

def make_matrix(rows, columns):
    A = np.zeros((rows,columns), dtype = np.float64)

def num_sequences(player_id):
    return