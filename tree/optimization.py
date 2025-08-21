import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

from model.induced_tree import Node
from model.state import START_STATE
from model.expected_value import expected_value
from model.pitcher_strategies import P_TOTAL, pitcher_strategy
from model.batter_strategies import batter_pure_strats, B_TOTAL

batter_strat = batter_pure_strats()

def _ev_prior(args):
    i, j, root, ps, bs = args
    ev = expected_value(root, ps, bs)
    return i, j, ev

def build_matrix(root: Node, max_p: int = None):
    n = P_TOTAL if max_p is None else max_p
    m = B_TOTAL

    U = np.zeros((n,m), dtype = np.float32)
    
    tasks = []
    for i in range(n):
        ps = pitcher_strategy(i)
        for j, bs in enumerate(batter_strat): 
            tasks.append((i,j,root,ps,bs))
            #U[i,j] = expected_value(root, ps, bs, START_STATE)   
            #print(f"\033[94m {U[i,j]} counter: {counter} \033[0m")
            #counter += 1

    with ProcessPoolExecutor(max_workers = 8) as executor:
        for i, j, ev in executor.map(_ev_prior, tasks, chunksize = 8):
            U[i,j] = ev
    return U


if __name__ == "__main__": 
    U = build_matrix(10)
    print(U)

    assert U[0,0] == expected_value(pitcher_strategy(0), batter_strat[0], START_STATE)

    print("worked!")