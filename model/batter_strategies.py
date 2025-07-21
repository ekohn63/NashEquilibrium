from .action_set import BATTER_ACTIONS
from .helpers import idx_to_strat
from itertools import product

B_BASE = 2
B_LEN = 6
B_TOTAL = B_BASE ** B_LEN

batter_strat = []
for i in range(B_TOTAL): 
    strat = idx_to_strat(i, B_BASE, B_LEN, BATTER_ACTIONS)
    #batter_strat.append(tuple(reversed(strat)))
    batter_strat.append(strat)


if __name__ == "__main__": 
    #print(BATTER_ACTIONS)
    #print(BATTER_ACTIONS[0], BATTER_ACTIONS[1])
    #print(idx_to_strat(, B_BASE, B_LEN, BATTER_ACTIONS))
    #print(idx_to_strat(5, B_BASE, B_LEN, BATTER_ACTIONS))
    for i in range(10):
        print(batter_strat[i], "\n")