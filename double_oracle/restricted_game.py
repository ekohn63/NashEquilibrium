from collections import defaultdict

import numpy as np

from model.dynamics import state_dynamics
from model.nature import get_outcome_prob
from model.induced_tree import Node, is_terminal_node
from model.payoff import terminal_utility
from model.state import START_STATE
from sequence_form import *
from sequence_form.equilibirum import batter_constraint_matrix, pitcher_constraint_matrix, pyomo_dual, pyomo_mps


# default strategy
# define a pure strategy that deterministicaly specifies an action for every info set
# strat defined implicitly as explicitly writing it can take up too much memory!

# defining pi^DEF_i
def default_strategy(node: Node):
     #pick the frist action in the ordered set A(h)
    for choice in node.children.values(): 
          return choice

def br_pitcher_subgame(h: Node, sigma_B):
    def V(n: Node):
        if is_terminal_node(n):
            nature_outcome = next(choice for choice in n.parent.children if n.parent.children[choice] is n)
            new_state, runs = state_dynamics(START_STATE, nature_outcome)
            utility = terminal_utility(START_STATE, new_state, runs)
        if n.data is "Batter":
             strat = sigma_B[n.info_set] 
             return sum(strat * V(c) for c in n.children.values())
        elif n.data == "Nature":
            sum = 0
            batter_act = next(act for act in n.parent.children if n.parent.children[act] == n)
            pitcher_act = next(act for act in n.parent.parent.children if n.parent.parent.children[act] == n.parent)
            for choice in n.children.values():
                prob = get_outcome_prob(pitcher_act, batter_act)
                sum += V(n) * prob
            return sum
        else:
             c = n.children[default_strategy(n)]
             return V(c)

    return V(h)

def br_batter_subgame(node, sigma_P):
    return

def compute_temporary_utilities(root: Node, S_B, S_P, sigma_P, sigma_B):
    mapping = {}
    tmp = {}

    def dfs(node: Node, seq_B, seq_P, prob):
        if is_terminal_node(node):
            nature_outcome = next(choice for choice in node.parent.children if node.parent.children[choice] is node)
            new_state, runs = state_dynamics(START_STATE, nature_outcome)
            utility = terminal_utility(START_STATE, new_state, runs)
            mapping[(seq_B, seq_P)] = mapping.get((seq_B, seq_P), 0) + utility*prob

        if node.data == "Nature":
             batter_act = next(act for act in node.parent.children if node.parent.children[act] == node)
             pitcher_act = next(act for act in node.parent.parent.children if node.parent.parent.children[act] == node.parent)
             for child in node.children.values(): 
                 child_prob = get_outcome_prob(pitcher_act, batter_act)
                 dfs(child, seq_B, seq_P, prob*child_prob)

        elif node.data == "Pitcher":
            if seq_P not in S_P: 
                return
            next_act = seq_P[node.info_set]
            if next_act is None:
                utility = br_batter_subgame(node, sigma_P)
                mapping[(seq_B, seq_P)] = mapping.get((seq_B,seq_P),0) + utility*prob
            else:
                for choice, child in node.children.items(): 
                    dfs(child, seq_B, seq_P + ((node.infoset, choice),), prob)

        elif node.data == "Batter":
            if seq_B not in S_B:
                return
            next_act = seq_B[node.info_set]
            if next_act is None:
                utility = br_pitcher_subgame(node, sigma_B)
                mapping[(seq_B, seq_P)] = mapping.get((seq_B, seq_P), 0) + utility*prob
            else: 
                for choice, child in node.children.items(): 
                    dfs(child, seq_B + ((node.info_set, choice),), seq_B, prob)
    dfs(root, ((),), ((),), 1.0)
    return mapping, tmp

def payoff_matrix_restricted(root, S_P, S_B, sigma_P, sigma_B):
    mapping,_ = compute_temporary_utilities(root, S_B, S_P, sigma_P, sigma_B)
    
    A = np.zeros(shape = (len(S_B), len(S_B)), dtype = np.float64)
    
    for ((seq_P), (seq_B)), val in mapping.items():
        if (seq_P) in S_B and (seq_B) in S_P: 
            A[S_B.indexof(seq_B), S_P.indexof(seq_P)] = val


def build_seq_form_lp(root, S_B: list[tuple], S_P: list[tuple]):
    F = pitcher_constraint_matrix(root, S_P)
    E = batter_constraint_matrix(root, S_B)
    A = payoff_matrix_restricted(root, S_B, S_P, sigma_P, sigma_B)
    sigma_P, val = pyomo_mps(A, E, F)
    sigma_B, dual_val = pyomo_dual(A, E, F)
    assert np.isclose((val), dual_val, rtol = 10e-7)
    return sigma_P, sigma_B, val