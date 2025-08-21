from .action_set import BATTER_ACTIONS, PITCHER_ACTIONS, NONTERMINAL_NATURE
from .helpers import idx_to_strat, strat_to_idx
from itertools import product
from model.induced_tree import STRIKEOUT, WALK, batter_counter

B_BASE = len(BATTER_ACTIONS)
B_LEN = STRIKEOUT + WALK - 1 

def num_infosets():
    infosets = 0
    for i in range(B_LEN):
        if i == (B_LEN - 1):
            infosets += (len(BATTER_ACTIONS) * len(PITCHER_ACTIONS) * (len(NONTERMINAL_NATURE)-1)) ** i
        else:
            infosets += (len(BATTER_ACTIONS) * len(PITCHER_ACTIONS) * len(NONTERMINAL_NATURE)) ** i 
    return infosets 

#B_NUM_INFOSETS = next(batter_counter) - 1
B_TOTAL = B_BASE ** num_infosets()

print(B_BASE, num_infosets())
def batter_pure_strats():
    batter_strat = []
    for i in range(B_TOTAL): 
        strat = idx_to_strat(i, B_BASE, num_infosets(), BATTER_ACTIONS)
        batter_strat.append(strat)
    return batter_strat

if __name__ == "__main__": 
    print(B_TOTAL, num_infosets())
    strat = batter_strat[15]
    print(batter_strat[8])
    print(strat_to_idx(strat, B_BASE, BATTER_ACTIONS))
    print(len(batter_strat), batter_strat)