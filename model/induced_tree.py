from collections import defaultdict, deque
from dataclasses import dataclass, field
from itertools import count
from pathlib import Path
from typing import Any, Dict, Tuple

from .action_set import PITCHER_ACTIONS, BATTER_ACTIONS, NATURE_ACTIONS, Nature
import csv
import sys

STRIKEOUT = 1
WALK = 2

pitcher_next_at_depth: dict[int, int] = defaultdict(int)
_next_iset = count(start = 1)
COUNTER = 0

# Note to self - make sure to review self, and what the python module, and PYTHONPATH business is
class Node:
    data: Any # labeling whic player owns the node!
    count: Tuple
    children: Dict[Any, "Node"]

    def __init__(self, children=None, data=None, count=None, info_set = None):
        self.children = None if children is None else children
        self.data = data
        self.parent = None
        self.count = (0,0) if count is None else count
        self.info_set = None if info_set is None else info_set

    def add_child(self, decision, child): 
        if child is None: 
            child = Node()
        if self.children is None:
            self.children = {}
        child.parent = self
        self.children[decision] = child

    def get_depth(self)->int:
        count = 0
        p = self.parent
        while p: 
            count += 1
            p = p.parent
        return count

    def print_tree(self, f:str):
        print('     .'*self.get_depth() + str(self.get_depth()) + f" info_set: {self.info_set} " + str((self.count)) + "|---", end = '', file = f)
        print(self.data, file = f)
        if self.children: 
            for child in self.children.values(): #need the values of the keyvalue else get a str
                child.print_tree(f)

def next_infoset(node: Node):
    global pitcher_next_at_depth, COUNTER
    depth = node.count[0] + node.count[1]
    iset = None
    if node.data == "Pitcher":
        if pitcher_next_at_depth[depth] == 0:
            pitcher_next_at_depth[depth] = next(_next_iset)
        iset = pitcher_next_at_depth[depth]
        pitcher_next_at_depth[depth] = next(_next_iset)
        COUNTER += 1
        print(f"counter= {COUNTER}")
    return iset

def next_player(cur_player:str):
    if cur_player == "Pitcher":
        return "Batter"
    elif cur_player == "Batter":
        return "Nature"
    elif cur_player == "Nature": 
        return "Pitcher"
    
def is_terminal_node(node:Node):
    decision = None

    if node.parent == None: #The node is the root
        return False
    for key,value in node.parent.children.items(): 
        if value == node:  # this here is the issue!
            decision = key
            break

    #print(f"decision={decision}, count={node.count}")
    #print(f"strikes = {node.count[1]}")

    if decision in [Nature.Single, Nature.Double, Nature.Triple, Nature.HR, Nature.Out]:
        return True
    elif decision == Nature.Ball and node.count[0] >= WALK: # this was the issue, count doesn't go up after this, so need to check at >=3, not >=2!
        return True
    elif decision == Nature.Strike and node.count[1] >= STRIKEOUT: #similar problem at this line!
        return True
    else:
        return False
    
def build_tree(node: Node):
    if node.parent == None: 
        next(_next_iset)
    actions = []
    count = node.count
    if node.data == "Pitcher":
        actions = PITCHER_ACTIONS
    elif node.data == "Batter":
        actions = BATTER_ACTIONS
    elif node.data == "Nature":
        actions = NATURE_ACTIONS

    if is_terminal_node(node):
        return node

    if node.data == "Pitcher" or node.data == "Batter":
        for act in actions:
            node.add_child(act, Node(data = next_player(node.data), count = count, info_set = node.info_set))

    elif node.data == "Nature":
        for act in actions:
            if act in {Nature.Single, Nature.Double, Nature.Triple, Nature.HR, Nature.Out}:
                node.add_child(act, child = Node(data = "Terminal", count = (0,0), info_set = node.info_set))
            elif act == Nature.Strike:
                if count[1]+1 >= STRIKEOUT:
                    label = "Terminal, Strikeout"
                else:
                    label = next_player(node.data)
                new_node = Node(data = label, count = (count[0], count[1]+1), info_set = None)
                new_node.info_set = next_infoset(new_node)
                node.add_child(Nature.Strike, child = new_node) # this should be terminal if the count is a terminal count
            else:
                if count[0]+1 >= WALK:
                    label = "Terminal, Walk"
                else:
                    label = next_player(node.data)
                new_node = Node(data = label, count = (count[0]+1, count[1]), info_set = None)
                new_node.info_set = next_infoset(new_node)
                node.add_child(Nature.Ball, new_node)
    for child in node.children.values():
        build_tree(child)

    return node


def num_infosets(root: Node): 
    my_set = []
    stack = deque([])
    stack.append(root)
    while stack: 
        node = stack.pop()
        if node.data == "Pitcher":
            my_set.append(node)
        if node.children is not None:
            for child in node.children.values():
                stack.append(child)
    
    ids = {n.info_set for n in my_set}
    print(f"pitcher nodes     : {len(my_set)}")
    print(f"pitcher infosets  : {len(ids)}")

if __name__ == "__main__":
    root = Node(data = "Pitcher", info_set = 1)
    tree_root = build_tree(root)
    print(f"\033[91m {id(root) == id(tree_root)} \033[0m")
    num_infosets(tree_root)

    path = Path(__file__).parent.parent/"data/induced_tree.txt"
    print(path)
    with open(path, "w") as file:
        root.print_tree(file)