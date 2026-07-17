from collections import defaultdict
import numpy as np
from model.induced_tree import get_num_infosets, num_infosets
from model.pitcher_strategies import pitcher_pure_strats
from model.batter_strategies import batter_pure_strats

TOL = 1e-10

# tuple in the sme order as A which is in the same order as sequence_list
def realization_to_behavioural(realization, sequencelist, constraint_matrix):
    behavioural = {i: {} for i in range(constraint_matrix.shape[0])}
 
    for i, row in enumerate(constraint_matrix):
        if i == 0:                       # row 0 is the root-mass constraint
            continue
 
        successors = []
        parent = None
        for j in range(len(row)):
            if row[j] == -1:
                parent = j
            elif row[j] == 1:
                successors.append(j)
        if parent is None or not successors:
            continue                     # empty row (unused infoset id)
 
        parent_mass = realization[parent]
 
        if parent_mass <= TOL:
            # zero-mass infoset: any distribution is equilibrium-consistent
            # (von Stengel); use uniform.
            for idx in successors:
                choice = sequencelist[idx][-1][-1]
                behavioural[i][choice] = 1.0 / len(successors)
        else:
            raw = {}
            for idx in successors:
                choice = sequencelist[idx][-1][-1]
                raw[choice] = max(float(realization[idx]), 0.0)   # clamp -0.0
            total = sum(raw.values())                             # ~ parent_mass
            if total > TOL:
                for choice, v in raw.items():
                    behavioural[i][choice] = v / total            # renormalise
            else:
                for choice in raw:
                    behavioural[i][choice] = 1.0 / len(raw)
 
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


# assumign the behavioural strategy is a pure strategy
def behavioural_to_realization(behav: dict, pitchersequences):
    num_sequences = len(pitchersequences)
    y = [None] * num_sequences

    for idx, sequence in enumerate(pitchersequences):
        prob = 1
        # root gets probability 1
        if idx == 0:
            y[idx] = prob
            continue
        for infoset, action in sequence:
            if action == behav[infoset]:
                prob = prob
            else: 
                prob = 0
        y[idx] = prob

    return y