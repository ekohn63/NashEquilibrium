from itertools import product
from typing import Hashable
from model.induced_tree import Node
from collections import deque

from test_tree import build_tree
# Underlying thm: 
# the path from the root to any node in the game tree is unique
def path_to_node(root: Node, target: Node) -> list[Node]: 
    stack = deque([(root, [root])], None)

    while stack:
        node, prefix = stack.pop()
        #print(list(node.data for node in prefix))
        #if prefix[-1] is not root: 
        #    for action, node in prefix[-1].parent.children.items():
        #        if node == prefix[-1]:
        #            print(action)
        #            continue
        if node is target:
            return prefix
        if node.children is None: 
            continue
        for child in node.children.values(): 
            stack.append((child, prefix + [child]))
    
    raise ValueError("target not in the tree!")

def print_path(p:list):
    path = []
    for nxt in p[1:]:
        for action, n in nxt.parent.children.items():
            if n is nxt:
                path.append(action)
    return path

def path_to_node2(root: Node, target: Node):
    path = []
    while target is not root:
        path.append(target)
        target = target.parent
    
    path.append(root)
    path.reverse()
    return path

# as an exercise, try and write the equivalent pre-order traversal in dfs form!

#suppose for the purposes that I do indeed have info_set_id
# for of: player_id_#info_set
# returns a representative node of each info_set
def player_info_sets(root: Node, player_id)-> dict[Hashable,Node]:
    reps: dict[Hashable, Node] = {}

    stack = deque(iterable = [root])

    while stack: 
        node = stack.pop()
        if (node.data == player_id) and (node.info_set not in reps): 
            reps[node.info_set] = node
        if node.children is None: 
            continue
        for child in node.children.values(): #equivalently could write stack.extend(node.children.values())
            stack.append(child)
    return reps

# what is a hashable?
# returns all pure strategies for player i such that the target node is in the subtree formed by the pure strategy

# step one - path of 
def Si_star(target: Node, player_id, root: Node,): 
    path = path_to_node(root, target)
    # get info-sets on the path, and the corresponding action!
    # importantly, the last node on the path doesn't have an info set!
    # Note: this sets such that every vertex in info_set, U_i takes the same action
    required_strat = get_required_strat(root, target, player_id)
   
    all_infosets = player_info_sets(root, player_id)

    #print(f"required_strat: {required_strat}")
    # find all the "free" info sets:
    free_info_set = {}
    for infoset_id, node in all_infosets.items(): 
        if infoset_id not in required_strat:
            free_info_set[infoset_id] = node
    
    print(f"\033[91m len_req \033[0m = {len(required_strat)} \033, \033[91m len_free \033[0m = {len(free_info_set)}")

    #print(f"free_info_set: {free_info_set}")
    # get a list of the list of the actions available at the node in each info set

    action_lists = []
    for node in free_info_set.values(): 
        actions = list(node.children.keys())
        action_lists.append(actions)

    #print(f" \033[91m action_list: \033[0m action_lists")
    #print(f"prod_actions: {list(product(*action_lists))}, \033[91m len: \033[0m {len(list(product(*action_lists)))}")

    # cartesian product over all the actions available at the free info sets - yield each produced strategy
    for actions in product(*action_lists): 
        strategy = required_strat
        for i, infoset_id in enumerate(free_info_set):
            strategy[infoset_id] = actions[i]
        yield strategy

def get_required_strat(root:Node, target:Node, player_id):
    required_strat: dict[Hashable, Node] = {}
    path = path_to_node(root, target)
    for node, nxt in zip(path[:-1], path[1:]): 
        if node.data == player_id:
            for action, child in node.children.items():
                if child == nxt:
                    required_strat[node.info_set] = action
    
    return required_strat


def size_of_Si(root:Node, target:Node, player_id):
    total_infosets = player_info_sets(root, player_id)
    strat_required = (get_required_strat(root, target, player_id))

    free_infoset = {}
    for info_id, node in total_infosets.items():
        if info_id not in strat_required:
            free_infoset[info_id] = node
        
    # compressed version: free_infoset = [info_id for info_id in total_infosets if info_id not in strat_required]

    size_actions = []
    for node in free_infoset.values(): 
        size = len(node.children)
        size_actions.append(size)

    prod = 1
    for i in size_actions:
        prod = prod*i

    lenght = prod
    return lenght
    
if __name__ == "__main__":
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


"""
need to fix: 
the strategy should give a node, not the action!
"""
