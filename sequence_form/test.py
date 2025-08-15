from model.induced_tree import build_tree, Node, COUNTER, get_num_infosets
from model.pitcher_strategies import pitcher_pure_strats
from sequence_form.sequence import set_sequences, compute_payoff_matrix
from sequence_form.equilibirum import batter_constraint_matrix, build_primal_MPS, pitcher_constraint_matrix, pyomo_dual, pyomo_batter_br, pyomo_mps, pyomo_pitcher_br
from sequence_form.conversion import realization_to_behavioural, behavioural_to_mixed
import numpy as np

node = Node(data = "Pitcher", info_set = 1)
root = build_tree(node)
#print(f"\033[91m {COUNTER} \033[0m")
battersequences = set_sequences(root, "Batter")
pitchersequences = set_sequences(root, "Pitcher")
print(f"\033[91m pitcher_sequences = \033[0m {pitchersequences}")
print(f"\033[91m batter_sequences = \033[0m {battersequences}")
#print(f"\033[91m {len(battersequences)} \033[0m")
#for i in (battersequences):
#    print(i)

#print(get_num_infosets(root, "Batter"))

A = compute_payoff_matrix(root)
E = batter_constraint_matrix(root, battersequences)
F = pitcher_constraint_matrix(root, pitchersequences)

def test_nature_realization():
    pitcher_strat = set_sequences(root, "Pitcher")
    batter_strat = set_sequences(root, "Batter")
    #print(pitcher_strat)
    print(f"batter_strat: {batter_strat}")
    print(A)
    print(np.count_nonzero(A))

#test_nature_realization()

def test_constraint_matrix(): 
    E = batter_constraint_matrix(root, battersequences)
    F = batter_constraint_matrix(root, pitchersequences)
    print(F)

#test_constraint_matrix()

def test_mps_file():
    #build_primal_MPS(root, battersequences, pitchersequences, A)
    print(f"E: {E}")
    primal = pyomo_mps(A,E,F)
    #dual2, primal2 = pyomo_dual(A,E,F)
    return primal
    #pitcher_realization = primal[F.shape[0]:]
    #print(f"pitcher_realization: {primal}")
    #assert primal == reversed(primal2)
    #assert dual == reversed(dual2)

    #behavioural = realization_to_behavioural(primal, "Pitcher")

def test_conversion(primal):
    E = batter_constraint_matrix(root, battersequences)
    F = pitcher_constraint_matrix(root, pitchersequences)    
    behavioural = realization_to_behavioural(primal, pitchersequences, F)
    print(behavioural)
    mixed_strat = behavioural_to_mixed(behavioural, "Pitcher")
    print(f"\033[94m {mixed_strat} \033[0m")
    indices = np.where(mixed_strat > 1e-8)[0]
    strats = []
    pure_strategies = pitcher_pure_strats()
    print(len(pure_strategies))
    for idx, strat in enumerate(pure_strategies):
        if idx in indices:
            strats.append(strat)
    print(f"idx: {np.where(mixed_strat > 1e-8)[0]}, strats: {strats}, len: {len(strats)}")

def test_dfs():
    B = -A
    x_val, val = pyomo_dual(A, E, F)
    y_val, br_val = pyomo_pitcher_br(F, B, x_val) 

    print(y_val)


#primal = test_mps_file()
#test_conversion(primal)

test_dfs()