from sys import path
import os.path
import math

import numpy as np
from numpy import minimum

from tree.linprog import col_min_max, display, find_saddle_points, maximin, minimax, pure_strategies, row_max_min
from pyomo.environ import *

path.append(os.path.dirname(path[0]))
#print(os.path.dirname(path[0]))
#print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tree.optimization import build_matrix
from model.induced_tree import build_tree, Node, get_num_infosets
from model.expected_value import *
from model.pitcher_strategies import pitcher_strategy
from model.batter_strategies import batter_pure_strats

batter_strat = batter_pure_strats()

def fill_matrix():
    ev = expected_value(root, pitcher_strategy(0), batter_strat[0], START_STATE)
    print(ev)
    U = build_matrix(root)
    print(U)
    print(f"U[0,0]: {U[0,0]}, ev: {ev}")
    assert math.isclose(U[0,0], ev, rel_tol=1e-2)
    return U

def test_lin_prog():
    U = fill_matrix()
    U = U.transpose()
    #print(U)
    p,v = row_max_min(U)
    q,w = col_min_max(U)
    print(find_saddle_points(U))
    display(U, p, v, q, w)


def test_pyomo(root): 
    U = fill_matrix()
    U = U.transpose()

    primal = maximin(U)
    dual = minimax(U)

    solver = SolverFactory("highs")
    solver.solve(primal, tee=False)
    solver.solve(dual, tee=False)

    alpha = value(primal.alpha)
    piB   = np.array([value(primal.x[j]) for j in primal.B])

    beta  = value(dual.beta)
    piP   = np.array([value(dual.y[i]) for i in dual.P])

    print("alpha (primal obj) =", alpha)
    print("piB =", piB)
    print("beta  (dual   obj) =", beta)
    print("piP =", piP)
    
    p_infosets = get_num_infosets(root, "Pitcher")

    pitcher, batter = pure_strategies(piB, piP, p_infosets)

    print(f"\033[91m pitcher pure strategy: {pitcher} \033[0m , \033[94m batter pure strategy: {batter} \033[0m")
    return alpha, beta

if __name__== "__main__":
    node = Node(data = "Pitcher", info_set = 1)
    root = build_tree(node)
    
    U = fill_matrix()
    U = U.transpose()
    #print(U)
    p,v = row_max_min(U)
    q,w = col_min_max(U)
    print(find_saddle_points(U))
    
    alpha, beta = test_pyomo(root)

    assert alpha == v
    assert beta == w

