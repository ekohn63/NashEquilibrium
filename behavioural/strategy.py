import pickle
from .si_star import Si_star
from tree.linprog import row_max_min
from model.helpers import strat_to_idx

def list_strategies(target, player_id, root):
    si =  Si_star(target, player_id, root)
    list_strats = []
    for strat in si:
        list_strats.append(strat)
    return list_strats

def load_mixed_strat():
    with open("C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\data\\pitcher_optimal.pkl", 'rb') as file:
        pitcher_strat = pickle.load(file)

    with open("C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\data\\batter_optimal.pkl", 'rb') as file:
        batter_strat = pickle.load(file)
    
    print(f"ps: {pitcher_strat}, bs: {batter_strat}")
    
    return pitcher_strat, batter_strat

def sum_of_strat(root, target, player_id):
    pitcher_strat, batter_strat = load_mixed_strat()
    list_strats = list_strategies(target, player_id, root)
    if player_id == "Pitcher":
        mixed_strat = pitcher_strat
    else: 
        mixed_strat = batter_strat
    prob = 0
    for strat in list_strats: 
        idx = strat_to_idx(mixed_strat)
        prob += mixed_strat[idx]

    return prob

if __name__ == "__main__":
    load_mixed_strat()
