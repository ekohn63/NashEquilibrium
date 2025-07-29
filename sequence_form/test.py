from model.induced_tree import build_tree, Node, COUNTER, get_num_infosets
from sequence_form.sequence import set_sequences, set_sequences_playeri, compute_payoff_matrix
from sequence_form.equilibirum import batter_constraint_matrix, build_primal_MPS, pyomo_dual, pyomo_lp, pyomo_mps
import numpy as np

node = Node(data = "Pitcher", info_set = 1)
root = build_tree(node)
#print(f"\033[91m {COUNTER} \033[0m")
battersequences = set_sequences(root, "Batter")
pitchersequences = set_sequences(root, "Pitcher")
print(pitchersequences)
#print(f"\033[91m {len(battersequences)} \033[0m")
#for i in (battersequences):
#    print(i)

#print(get_num_infosets(root, "Batter"))

A = compute_payoff_matrix(root)

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
    E = batter_constraint_matrix(root, battersequences)
    F = batter_constraint_matrix(root, pitchersequences)
    #pyomo_mps(A,E,F)
    pyomo_dual(A,E,F)
    
test_mps_file()