from .action_set import BATTER_ACTIONS
from .helpers import idx_to_strat, strat_to_idx
from itertools import product
from model.induced_tree import STRIKEOUT, WALK

B_BASE = len(BATTER_ACTIONS)
B_INFOSETS = STRIKEOUT + WALK - 1 
B_TOTAL = B_BASE ** B_INFOSETS

batter_strat = []
for i in range(B_TOTAL): 
    strat = idx_to_strat(i, B_BASE, B_INFOSETS, BATTER_ACTIONS)
    batter_strat.append(strat)

if __name__ == "__main__": 
    strat = batter_strat[15]
    print(batter_strat[8])
    print(strat_to_idx(strat, B_BASE, BATTER_ACTIONS))