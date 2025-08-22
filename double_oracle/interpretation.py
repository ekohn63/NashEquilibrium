import numpy as np

def interpret_realization(y, pitchersequences):
    sequence_support = []
    for idx, val in enumerate(y):
        if val == 1:
            sequence_support.append(pitchersequences[idx])
        if val > 0 and val !=1: 
            print("check")
    return sequence_support

def organize_value_cache(value_cache):
    q_bellman = [0.0]*(len(value_cache)+1)

    for info_set, value in value_cache.items(): 
        q_bellman[info_set] = float(value)
    
    q_bellman[0] = q_bellman[1]

    return q_bellman

def bellman_eq(stoch_prob, bellman_val, q_val):
    scaled_bellman = [0]*len(bellman_val)

    for info_set, val in stoch_prob.items():
        scaled_bellman[info_set] = bellman_val[info_set]*val

    scaled_bellman[0] = -q_val[0]
    scaled_bellman[1] = -q_val[1]*1

    print(scaled_bellman)
    for idx, val in enumerate(scaled_bellman): 
        assert np.isclose(-val, q_val[idx], atol=1e-9)