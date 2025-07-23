# pitcher_strats.py
from pathlib import Path
from .action_set import PITCHER_ACTIONS, BATTER_ACTIONS, NONTERMINAL_NATURE
from .helpers import idx_to_strat
from itertools import islice
import csv
from model.induced_tree import STRIKEOUT, WALK

P_BASE   = len(PITCHER_ACTIONS)          # alphabet size
P_LEN    = STRIKEOUT + WALK - 1         # walk at 3 balls, strikeout at 2 strikes!

def num_infosets():
    p_infosets = 0
    for i in range(P_LEN):
        if i == (P_LEN - 1): 
            p_infosets += (len(PITCHER_ACTIONS)*len(BATTER_ACTIONS)*(len(NONTERMINAL_NATURE) - 1)) ** i
        else: 
            p_infosets += (len(PITCHER_ACTIONS)*len(BATTER_ACTIONS)*len(NONTERMINAL_NATURE)) ** i
    return p_infosets

P_TOTAL  = P_BASE ** num_infosets() 

def pitcher_strategy(idx: int):
    if not 0 <= idx < P_TOTAL:
        raise IndexError("strategy id out of range")
    return idx_to_strat(idx, P_BASE, num_infosets(), PITCHER_ACTIONS)

def pitcher_strategies(start: int = 0):
    """Lazy forward iterator from `start` to P_TOTAL-1."""
    for i in range(start, P_TOTAL):
        yield pitcher_strategy(i)


def dump_to_csv(path:str, limit:int):
    print(path)
    with open(path, mode = "w") as file:
        writer = csv.writer(file, delimiter=',')
        for idx, strat in enumerate(pitcher_strategies()): 
            content = map(PITCHER_ACTIONS.index, strat)
            print(content)
            writer.writerow([a] for a in content)
            if idx + 1 >= limit:
                break

def list_all_strats():
    all_strats = []
    for i in pitcher_strategies(): 
        all_strats.append(i)
    return all_strats

if __name__ == "__main__":
    print(f"num_infosets: {num_infosets()}")
    print(pitcher_strategy(5))
    print(PITCHER_ACTIONS[0], PITCHER_ACTIONS[1])
    all_strats = list_all_strats()
    print(len(all_strats))

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