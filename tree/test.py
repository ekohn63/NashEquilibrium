from sys import path
import os.path
import math

from tree.linprog import col_min_max, display, find_saddle_points, row_max_min

path.append(os.path.dirname(path[0]))
print(os.path.dirname(path[0]))
print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.optimization import build_matrix
from model.induced_tree import build_tree, Node
from model.expected_value import *
from model.pitcher_strategies import pitcher_strategy
from model.batter_strategies import batter_strat

def test(root): 
    ps = pitcher_strategy(5)
    bs = batter_strat[2^4-1]
    assert node is root
    print(bs, ps)
    print("EV =", expected_value(root, ps, bs))

def fill_matrix():
    ev = expected_value(root, pitcher_strategy(0), batter_strat[0], START_STATE)
    print(ev)
    U = build_matrix(root)
    print(U)
    print(f"U[0,0]: {U[0,0]}, ev: {ev}")
    assert math.isclose(U[0,0], ev, rel_tol=1e-2)
    return U

if __name__== "__main__":
    node = Node(data = "Pitcher", info_set = 1)
    root = build_tree(node)
    test(root)
    print("check")
    
    U = fill_matrix()
    U = U.transpose()
    #print(U)
    p,v = row_max_min(U)
    q,w = col_min_max(U)
    print(find_saddle_points(U))
    display(U, p, v, q, w)
