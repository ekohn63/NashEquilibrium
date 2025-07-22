from behavioural.si_star import Si_star, path_to_node, player_info_sets, print_path, size_of_Si
from behavioural.strategy import enumerate_behavioural_strat
from model.helpers import strat_to_idx
from model.action_set import BATTER_ACTIONS as ba, PITCHER_ACTIONS as pa
from model.batter_strategies import batter_strat
from test_tree import build_tree


def test_helpers_fn():
    strat = {1:ba[0], 4: ba[1], 3: ba[0], 2: ba[0]}
    print(strat)
    idx = strat_to_idx(strat, len(ba), ba)
    print(idx)

def test_strategy():
    root = build_tree()
    behavioural = enumerate_behavioural_strat(root, "Batter")
    with open(file = "C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\behavioural\\behav_strat.txt", mode = "w") as f: 
        print(behavioural, file = f)

def test_si():
    root = build_tree()
    node = root.children["Fastball"].children["Swing"].children["Ball"].children["Fastball"]

    path = path_to_node(root, node)
    print(print_path(path), path)

    infoset = player_info_sets(root, "Pitcher")

    num_strategies = size_of_Si(root, node, player_id = "Pitcher")
    print(f"num_strategies: {num_strategies}")

    si_star = Si_star(node, "Pitcher", root)

    Si = []
    for strat in si_star:
        Si.append(strat)

    assert len(Si) == num_strategies
    assert root is infoset[1]

if __name__ == "__main__":
    test_strategy()