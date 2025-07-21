from sys import path
import os.path
import math

path.append(os.path.dirname(path[0]))
print(os.path.dirname(path[0]))
print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.optimization import build_matrix
from model.induced_tree import build_tree, Node
from model.expected_value import *
from model.pitcher_strategies import pitcher_strategy
from model.batter_strategies import batter_strat

node = Node(data = "Pitcher")
root = build_tree(node)

def test(): 
    ps = pitcher_strategy(5)
    bs = batter_strat[2^4-1]
    assert node is root
    print(bs, ps)
    print("EV =", expected_value(root, ps, bs))

test()

print("check")

def fill_matrix():
    ev = expected_value(root, pitcher_strategy(0), batter_strat[0], START_STATE)
    print(ev)
    U = build_matrix(root)
    print(U)
    print(U[0,0])
    print(ev)
    assert math.isclose(U[0,0], ev, rel_tol=1e-2)
    return U

fill_matrix()

print(batter_strat[2])