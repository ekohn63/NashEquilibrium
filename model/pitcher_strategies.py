# pitcher_strats.py
from pathlib import Path
from .action_set import PITCHER_ACTIONS as PA, BATTER_ACTIONS as BA, NONTERMINAL_NATURE as NA
from .helpers import idx_to_strat
from itertools import islice
import csv
from model.induced_tree import STRIKEOUT, WALK

P_BASE   = len(PA)          # alphabet size
P_LEN    = STRIKEOUT + WALK - 1         # walk at 3 balls, strikeout at 2 strikes!

def num_infosets():
    p_infosets = 0
    for i in range(P_LEN):
        if i == (P_LEN - 1): 
            p_infosets += (len(PA)*len(BA)*(len(NA) - 1)) ** i
        else: 
            p_infosets += (len(PA)*len(BA)*len(NA)) ** i
    return p_infosets

# clean this funciton up!
def num_infosets2():
    p_infosets = 0
    #def dfs(prev, active):
    #    prev = len(PA)*len(BA)*active
    #    p_infoset += prev
    #    dfs(, )
    for i in range(4):
        if i == 0: 
            p_infosets += (len(PA)*len(BA)*len(NA)) ** i
        if i == 1:
            p_infosets += len(PA)*len(BA)*len(NA) ** i
        if i == 2:
            p_infosets +=  len(PA)*len(BA)*len(NA)*(4) + len(PA)*len(BA)*1*4
        if i == 3: 
            p_infosets += 4*48

    return p_infosets
"""
depth 2: (1 + 8) = 9
S S
depth 3: 
S B S
B S S
B B B
depth 4: 
----- finish with strike: 3nCr2
BBSS
BSBS
SBBS
----- finish with ball: 3 nCr 2
B B S B
B S B B
S B B B
"""

if P_LEN == 2:
    P_TOTAL  = P_BASE ** num_infosets() 
if P_LEN == 4: 
    P_TOTAL = P_BASE ** num_infosets2()

def pitcher_strategy(idx: int):
    if not 0 <= idx < P_TOTAL:
        raise IndexError("strategy id out of range")
    return idx_to_strat(idx, P_BASE, num_infosets(), PA)

def pitcher_strategies(start: int = 0):
    """Lazy forward iterator from `start` to P_TOTAL-1."""
    for i in range(start, P_TOTAL):
        yield pitcher_strategy(i)


def dump_to_csv(path:str, limit:int):
    print(path)
    with open(path, mode = "w") as file:
        writer = csv.writer(file, delimiter=',')
        for idx, strat in enumerate(pitcher_strategies()): 
            content = map(PA.index, strat)
            print(content)
            writer.writerow([a] for a in content)
            if idx + 1 >= limit:
                break

def pitcher_pure_strats():
    all_strats = []
    for i in pitcher_strategies(): 
        all_strats.append(i)
    return all_strats


def pure_strategies(root):
    return


if __name__ == "__main__":
    print(f"num_infosets: {num_infosets()}")
    print(pitcher_strategy(5))
    print(PA[0], PA[1])
    all_strats = list_all_strats()
    #print(len(all_strats))
    print(num_infosets2())
    #print("Total pitcher strategies =", P_TOTAL)
    #for s in islice(pitcher_strategies(), 20):
    #    print(s, "\n")
    """
    print(PITCHER_ACTIONS.index)
    strat = pitcher_strategy(50)
    print(strat)

    for i in strat: 
        print(i)
        print(PITCHER_ACTIONS.index(i))
    for i in map(PITCHER_ACTIONS.index,strat):
        print(i)
    """
    #path = Path(__file__).parent.parent/"data/pitcher_strategies.csv"
    #dump_to_csv(path, 10000000)