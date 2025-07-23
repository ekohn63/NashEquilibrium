from behavioural.si_star import Si_star, path_to_node, player_info_sets, print_path, size_of_Si
from behavioural.strategy import check_equivalence, enumerate_behavioural_strat, list_strategies, prob_vertex_behav, sum_of_strat
from model.helpers import strat_to_idx
from model.action_set import BATTER_ACTIONS as ba, PITCHER_ACTIONS as pa, Nature
from model.batter_strategies import batter_strat
from model.induced_tree import Node, build_tree


def test_helpers_fn():
    strat = {1:ba[0], 4: ba[1], 3: ba[0], 2: ba[0]}
    print(strat)
    idx = strat_to_idx(strat, len(ba), ba)
    print(idx)

def test_strategy():
    root = Node(data = "Pitcher", info_set = 1)
    root = build_tree(root)
    behavioural = enumerate_behavioural_strat(root, "Batter")
    with open(file = "C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\behavioural\\behav_strat.txt", mode = "w") as f: 
        print(behavioural, file = f)

    vertex = root.children[pa[0]].children[ba[0]].children[Nature.Strike].children[pa[1]].children[ba[1]].children["Terminal"]
    prob = prob_vertex_behav(behavioural, vertex, root, "Batter")
    print(prob)

    #indices = []
    #for strat in list_strategies(vertex, "Batter",root): 
    #    print(strat)
    #    idx = (strat_to_idx(strat, 2, pa))
    #    print(idx)
    #    indices.append(idx)
    #print(indices)

    print(f"mixed_strat_prob = {sum_of_strat(root, vertex, "Batter")}")

    print(check_equivalence(behavioural, root, "Batter"))

def test_si():
    root = Node("Pitcher", info_set = 1)
    root = build_tree(root)
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
    print(pa[0])
    test_strategy()