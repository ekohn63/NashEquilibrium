from double_oracle.brs import best_response_pitcher
from model.induced_tree import build_tree, Node, COUNTER, get_num_infosets
from model.nature import behave_strat
from model.pitcher_strategies import pitcher_pure_strats
from sequence_form.sequence import set_sequences, set_sequences2, compute_payoff_matrix
from sequence_form.equilibirum import batter_constraint_matrix, build_primal_MPS, pitcher_constraint_matrix, pyomo_dual, pyomo_batter_br, pyomo_primal, pyomo_pitcher_br, pyomo_primal
from sequence_form.conversion import realization_to_behavioural, behavioural_to_mixed, behavioural_to_realization
from double_oracle.interpretation import bellman_eq, interpret_realization, organize_value_cache
import numpy as np

node = Node(data = "Pitcher", info_set = 1)
root = build_tree(node)
BEHAVE_STRAT = behave_strat(root)

battersequences = set_sequences2(root, "Batter")
pitchersequences = set_sequences2(root, "Pitcher")

print(f"\033[91m pitcher_sequences = \033[0m")
for idx, sequence in enumerate(pitchersequences):
    print(f"\033[91m {idx} \033[0m, {sequence}")

for idx, sequence in enumerate(battersequences):
    print(f"\033[91m {idx} \033[0m, {sequence}")

A = compute_payoff_matrix(root)
E = batter_constraint_matrix(root, battersequences)
F = pitcher_constraint_matrix(root, pitchersequences)

print(F)

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
    primal = pyomo_primal(A,E,F)
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

def test_linprogs():
    B = -A

    y_val, p_val, primal = pyomo_primal(A, E, F)
    x_val, q_val, dual_val, y_from_dual, p_from_dual = pyomo_dual(A, E, F)
    
    bry_val, q_from_dual, br_val = pyomo_pitcher_br(F, B, x_val) 

    print(f"primal: {primal}, dual: {dual_val}")
    print(f"q_val: {q_val}")
    print(f"p_val :{p_val}, p_from_dual: {p_from_dual}")

    print(f" y_val {y_val}, y_from_dual {y_from_dual}")


    assert np.isclose(dual_val, x_val @ A @ y_val, 1e-9)
    assert np.isclose(br_val, -(x_val @ A @ bry_val), 1e-9)

    #assert np.allclose(p_val, p_from_dual, atol= 1e-8) #<-- not good, why are they different!

    #assert np.allclose(y_val, y_from_dual, atol= 1e-8) #<-- this cuases an error for some reason!!

    assert np.isclose(primal, dual_val, atol= 1e-8)

    print(f"equilib x: {x_val}, equilib y: {y_val}")

    print(f"val = {dual_val}, br_val = {br_val}")

    print(f"\033[91m lp br_y_val = \033[0m {(bry_val)}")

def test_dp(): 
    B = -A
    y_val, p_val, primal = pyomo_primal(A, E, F)
    x_val, q_val, dual_val, y_from_dual, p_from_dual = pyomo_dual(A, E, F)
    y_br, q_br, val = pyomo_pitcher_br(F, B, x_val)

    print(f"val: {primal}, dual: {dual_val}")
    print(f"x_val: {x_val}, y_val: {y_val}")
    print(f"q_val: {q_val}, q_br: {q_br}")
    print(f"y_br: {y_br}")

    br, policy, value_cache, succ_prob = best_response_pitcher(root, x_val, battersequences, BEHAVE_STRAT)
    print(f" br: {br}, \033[91m policy: \033[0m {policy}")

    behave = realization_to_behavioural(y_br, pitchersequences, F)

    sequence_support = interpret_realization(y_br, pitchersequences)

    print(f"sequence_support: {sequence_support}")

    q_bellman = organize_value_cache(value_cache)

    print(f"q_bellman: {q_bellman}")
    print(f"br_q: {q_br}")

    bellman_eq(succ_prob, q_bellman, q_br)

   # behave2 = realization_to_behavioural(y_from_dual, pitchersequences, F)

    #print(f"behave: {behave}")
#    print(f"behave2: {behave2}")

    #assert policy == behave
    
    #converted = behavioural_to_realization(policy, pitchersequences)
    #print(f"converted: {converted}, y_val: {y_val}")
    #test_same(converted, y_val)

def test_dual(): 
    x_val, q_val, dual_val, y_from_dual, p_from_dual = pyomo_dual(A, E, F)
    print(x_val)
    print(E)

def test_same(converted, y_val):
    assert len(converted) == len(y_val)
    for idx in range(len(y_val)):
        assert converted[idx] == y_val[idx]

def test_pitcher_dp():
    return


def test_q_val(): 
    B = -A
    y_val, p_val, primal = pyomo_primal(A, E, F)
    x_val, q_val, dual_val, y_from_dual, p_from_dual = pyomo_dual(A, E, F)
    y_br, q_from_dual, val = pyomo_pitcher_br(F, B, x_val)

    Atx = -A.T @ x_val                      # c_j for pitcher BR

    r_dual = Atx - F.T @ q_val
    r_br   = Atx - F.T @ q_from_dual

    # whichever y you pair with, indices with y_j>1e-8 must have ~0 reduced cost
    supp_from_primal = [j for j,v in enumerate(y_val) if abs(v)>1e-9]       # from pyomo_primal
    supp_from_br     = [j for j,v in enumerate(y_br)   if abs(v)>1e-9]       # from pitcher BR
    print("r_dual on primal support:", r_dual[supp_from_primal])
    print("r_br   on BR     support:", r_br[supp_from_br])


#primal = test_mps_file()
#test_conversion(primal)

#test_linprogs()

test_dp()
#test_dual()