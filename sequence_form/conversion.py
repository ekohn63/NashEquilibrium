from collections import defaultdict
import numpy as np
from model.induced_tree import get_num_infosets, num_infosets
from model.pitcher_strategies import pitcher_pure_strats
from model.batter_strategies import batter_pure_strats

# tuple in the sme order as A which is in the same order as sequence_list
def realization_to_behavioural(realization: tuple[float], sequencelist, constraint_matrix):
    behavioural = {}
    for i in range(constraint_matrix.shape[0]):
        behavioural[i] = {}
    for i, row in enumerate(constraint_matrix):
        if i == 0: # skip the first row 
            continue
        children = []
        parent = None
        for j in range(len(row)):
            if row[j] == -1:
                parent = j
            if row[j] == 1:
                children.append(j)
        parent_sequence = sequencelist[parent]
        pinfo_set = None
        print(f"\033[94m {parent} \033[0m", end = "     ")
        if parent_sequence == ((),):
            pinfo_set = 1
        else: 
            pinfo_set = sequencelist[parent][-1][0]
        print(pinfo_set)
        for idx in children:
            child_seq = sequencelist[idx]
            c_infoset = child_seq[-1][0]
            choice = child_seq[-1][-1]
            if realization[parent] == 0:            # von stengel gives tht we can assign any arbitrary prob distribution!
                behavioural[c_infoset][choice] = 1/len(children)    # assign the uniform distribution
            else: 
                behavioural[c_infoset][choice] = realization[idx]/realization[parent]
    return behavioural


def behavioural_to_mixed(behavioural, player_id):
    purestrategies = []
    if player_id == "Pitcher":
        purestrategies = pitcher_pure_strats()
    if player_id == "Batter":
        purestrategies = batter_pure_strats()
    mixed_strat = np.zeros((len(purestrategies)), dtype = np.float64)
    for idx, strat in enumerate(purestrategies):
        prob = 1
        for infoset, choice in strat.items():
            prob = prob * behavioural[infoset][choice]
            print(infoset, choice, prob)
        mixed_strat[idx] = prob
    return mixed_strat


def compare(trad_lp, sequence_form):
    return