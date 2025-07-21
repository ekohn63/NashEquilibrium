import numpy as np
from scipy.optimize import linprog

from .induced_tree import Node
from .state import START_STATE
from .expected_value import expected_value
from .pitcher_strategies import list_all_strats, P_TOTAL, pitcher_strategy
from .batter_strategies import batter_strat, B_TOTAL

pitcher_strats = list_all_strats()

def build_matrix(root: Node, max_p: int = None):
    n = P_TOTAL if max_p is None else max_p

    print(n)
    m = B_TOTAL

    U = np.zeros((n,m), dtype = np.float32)

    for i in range(n):
        ps = pitcher_strategy(i)
        for j, bs in enumerate(batter_strat): 
            #print(ps, bs)
            U[i,j] = expected_value(root, ps, bs, START_STATE)    
    return U


if __name__ == "__main__": 
    U = build_matrix(10)
    print(U)

    assert U[0,0] == expected_value(pitcher_strategy(0), batter_strat[0], START_STATE)

    print("worked!")