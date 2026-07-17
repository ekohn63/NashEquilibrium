"""
figures_common.py — shared utilities for the paper figures.

Inputs (paths configured at the top of each figure script):
  * induced_tree.txt          : print_tree() dump of the game tree, used to
                                map information-set ids to counts/histories
  * {pitcher,batter}_behavioural__<record>.txt
                              : str(dict) exports of equilibrium behavioural
                                strategies, {infoset: {Action: prob}}
  * pitch_outcome_probabilities.csv
                              : Nature kernel  (Location, Type, BatterAction)
                                -> outcome probabilities

Provides:
  parse_tree(path)            -> root node (data, iset, count, children)
  parse_strat(path)           -> {infoset: {action_name: prob}}
  reach_rates(root, pit, bat, nature)
                              -> per-count realization-weighted swing rate
                                 and pitcher action usage
"""

import ast
import csv
import re
from collections import defaultdict

PITCHER_ACTIONS = ["Fastball_Bottom", "Offspeed_Bottom", "Offspeed_Chase"]
BATTER_ACTIONS = ["Swing", "Take"]
NATURE_ORDER = ["Single", "Double", "Triple", "HR", "Out", "Ball", "Strike"]

# pitcher action -> (Location, Type) key of the Nature CSV
CSV_KEY = {"Fastball_Bottom": ("Bottom", "Fastball"),
           "Offspeed_Bottom": ("Bottom", "Offspeed"),
           "Offspeed_Chase": ("Chase", "Offspeed")}


class Node:
    __slots__ = ("data", "iset", "count", "children", "parent")

    def __init__(self, data, iset, count):
        self.data, self.iset, self.count = data, iset, count
        self.children = []          # list of (edge_label, child)
        self.parent = None


def parse_tree(path):
    """Rebuild the tree from a print_tree() dump.  Children of Nature nodes
    are labeled positionally by NATURE_ORDER (the insertion order used in
    build_tree)."""
    pat = re.compile(
        r"^(?:\s*\.)*\s*(\d+) info_set: (\S+) \((\d+), (\d+)\)\|---(.*)$")
    by_depth, root = {}, None
    with open(path) as fh:
        for line in fh:
            m = pat.match(line.rstrip("\n"))
            if not m:
                continue
            depth = int(m.group(1))
            iset = None if m.group(2) == "None" else int(m.group(2))
            count = (int(m.group(3)), int(m.group(4)))
            rest = m.group(5)
            if rest.startswith("Pitcher"):
                data, label = "Pitcher", None
            elif rest.startswith("Batter"):
                data = "Batter"
                label = rest.split("pitcher: PitcherAction.")[1].strip()
            elif rest.startswith("Nature"):
                data = "Nature"
                label = rest.split("batter: BatterAction.")[1].strip()
            else:
                data, label = "Terminal", None
            node = Node(data, iset, count)
            if depth == 0:
                root = node
            else:
                parent = by_depth[depth - 1]
                node.parent = parent
                parent.children.append([label, node])
            by_depth[depth] = node

    def relabel_nature(node):
        if node.data == "Nature":
            for i, child in enumerate(node.children):
                child[0] = NATURE_ORDER[i]
        for _, c in node.children:
            relabel_nature(c)

    relabel_nature(root)
    return root


def parse_strat(path):
    """Parse a behavioural-strategy export: enum reprs become plain names."""
    text = open(path).read()
    text = re.sub(r"<\w+Action\.(\w+): \d+>", r"'\1'", text)
    return ast.literal_eval(text)


def load_nature(csv_path):
    kernel = defaultdict(dict)
    with open(csv_path) as fh:
        for row in csv.DictReader(fh):
            key = (row["Location"], row["Type"], row["BatterAction"])
            kernel[key][row["Outcome"]] = float(row["Probability"])
    return kernel


def reach_rates(root, pitcher_strat, batter_strat, nature):
    """Realization-weighted per-count aggregates.

    Returns {count: {"mass": reach probability of the count,
                     "swing": batter swing rate,
                     "<pitcher action>": usage share}}.
    Reach probabilities multiply the pitcher's and batter's behavioural
    probabilities and the Nature kernel along each history; unreached
    histories therefore carry zero weight automatically.
    """
    def pitch_of(nature_node):
        b = nature_node.parent
        p = b.parent
        return next(l for l, c in p.children if c is b)

    def batter_action_of(nature_node):
        b = nature_node.parent
        return next(l for l, c in b.children if c is nature_node)

    mass = defaultdict(float)
    swing = defaultdict(float)
    usage = defaultdict(lambda: defaultdict(float))

    stack = [(root, 1.0)]
    while stack:
        node, prob = stack.pop()
        if prob <= 0.0:
            continue
        if node.data == "Pitcher":
            mass[node.count] += prob
            for a in PITCHER_ACTIONS:
                usage[node.count][a] += prob * max(pitcher_strat[node.iset][a], 0.0)
        elif node.data == "Batter":
            swing[node.count] += prob * max(batter_strat[node.iset]["Swing"], 0.0)
        for label, child in node.children:
            q = prob
            if node.data == "Pitcher":
                q = prob * max(pitcher_strat[node.iset][label], 0.0)
            elif node.data == "Batter":
                q = prob * max(batter_strat[node.iset][label], 0.0)
            elif node.data == "Nature":
                loc, typ = CSV_KEY[pitch_of(node)]
                q = prob * nature[(loc, typ, batter_action_of(node))].get(label, 0.0)
            stack.append((child, q))

    out = {}
    for count, m in mass.items():
        out[count] = {"mass": m, "swing": swing[count] / m}
        for a in PITCHER_ACTIONS:
            out[count][a] = usage[count][a] / m
    return out
