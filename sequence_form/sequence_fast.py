"""
sequence_fast.py — drop-in fast replacement for sequence_form/sequence.py.

Same traversal (hence same sequence ORDER) as your set_sequences2, but:
  * sequence -> index lookups are dicts (O(1)), never list.index();
  * the payoff matrix is assembled SPARSE in a single DFS that carries
    (pitcher sequence, batter sequence, nature probability) down the tree —
    no terminal_nodes(), no per-terminal path_to_node()/get_sequence_tuple();
  * returns scipy.sparse.csr_matrix; nnz ~ #terminals, versus n*m dense
    (~410 GB at 4 balls / 3 strikes).

Usage (mirrors test.py):

    from model.induced_tree import build_tree, Node
    from sequence_form.sequence_fast import (set_sequences_fast,
                                             compute_payoff_matrix_sparse)

    root = build_tree(Node(data="Pitcher", info_set=1))
    pitcherseqs, p_idx = set_sequences_fast(root, "Pitcher")
    batterseqs,  b_idx = set_sequences_fast(root, "Batter")
    A = compute_payoff_matrix_sparse(root, b_idx, p_idx)  # csr, batter x pitcher

Cross-check at small size:
    assert np.allclose(A.toarray(), compute_payoff_matrix(root))
"""

import numpy as np
from dataclasses import replace
from scipy.sparse import coo_matrix

from model.state import START_STATE
from model.dynamics import state_dynamics
from model.payoff import terminal_utility
from model.nature import behave_strat

ROOT = ((),)


def set_sequences_fast(root, player_id):
    """(sequence_list, {sequence: index}); order identical to set_sequences2:
    root sequence ((),) first, then first-encounter DFS order."""
    seqs = [ROOT]
    idx = {ROOT: 0}

    def dfs(node, sequence):
        if node.children is None:
            return
        for choice, child in node.children.items():
            if node.data == player_id:
                new_seq = sequence + ((node.info_set, choice),)
                if new_seq not in idx:
                    idx[new_seq] = len(seqs)
                    seqs.append(new_seq)
                dfs(child, new_seq)
            else:
                dfs(child, sequence)

    dfs(root, ())
    return seqs, idx


def compute_payoff_matrix_sparse(root, batter_index, pitcher_index,
                                 start_state=START_STATE):
    """A[batter_seq, pitcher_seq] += P_nature(path) * payoff(terminal).
    Identical semantics to compute_payoff_matrix, assembled in one pass."""
    nature = behave_strat(root)
    rows, cols, vals = [], [], []

    def is_terminal(child):
        return (child.children is None) or (isinstance(child.data, str)
                                            and child.data.startswith("Terminal"))

    def terminal_payoff(nature_node, outcome):
        # pre-pitch count = the Nature node's count (as in get_terminal_node_payoff)
        balls, strikes = nature_node.count
        pre_state = replace(start_state, balls=balls, strikes=strikes)
        new_state, runs = state_dynamics(pre_state, outcome)
        return terminal_utility(start_state, new_state, runs)

    def dfs(node, p_seq, b_seq, prob):
        if node.data == "Pitcher":
            for choice, child in node.children.items():
                dfs(child, p_seq + ((node.info_set, choice),), b_seq, prob)
        elif node.data == "Batter":
            for choice, child in node.children.items():
                dfs(child, p_seq, b_seq + ((node.info_set, choice),), prob)
        elif node.data == "Nature":
            probs = nature[node.info_set]
            for outcome, child in node.children.items():
                p = prob * float(probs[outcome])
                if p == 0.0:
                    continue                      # prunes e.g. Swing -> Ball
                if is_terminal(child):
                    rows.append(batter_index[b_seq if b_seq else ROOT])
                    cols.append(pitcher_index[p_seq if p_seq else ROOT])
                    vals.append(p * terminal_payoff(node, outcome))
                else:
                    dfs(child, p_seq, b_seq, p)

    dfs(root, (), (), 1.0)
    return coo_matrix((vals, (rows, cols)),
                      shape=(len(batter_index), len(pitcher_index)),
                      dtype=np.float64).tocsr()