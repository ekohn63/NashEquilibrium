"""
equilibrium_fast.py — sparse replacement for the solve path in equilibirum.py.

One LP solve returns BOTH players' equilibrium realization plans:

    y  (pitcher plan)   = primal variables of  min e^T p
                          s.t.  A y - E^T p <= 0,   F y = f,   y >= 0
    x  (batter plan)    = the duals of the inequality block
    v* (game value)     = e^T p at the optimum  (batter's expected run value,
                          identical to your primal/dual_val)

so pyomo_primal + pyomo_dual collapse into a single call.  Everything is
scipy.sparse + linprog(method="highs"); no Pyomo expression trees are built,
which is what makes 4B/3S feasible (Pyomo's dense constraint construction is
~5e10 expression nodes there).

Also included:
  * sparse constraint-matrix builders (same row/column conventions as yours:
    row index == infoset id, row 0 is the root constraint);
  * realization_to_behavioural_fast: O(#sequences) via a parent dict, with
    the numerical hardening (tolerance + renormalisation) discussed.

Typical usage:

    from model.induced_tree import build_tree, Node
    from sequence_form.sequence_fast import set_sequences_fast, \
                                            compute_payoff_matrix_sparse
    from sequence_form.equilibrium_fast import (constraint_matrix_sparse,
                                                solve_equilibrium,
                                                realization_to_behavioural_fast)

    root = build_tree(Node(data="Pitcher", info_set=1))
    pitcherseqs, p_idx = set_sequences_fast(root, "Pitcher")
    batterseqs,  b_idx = set_sequences_fast(root, "Batter")
    A = compute_payoff_matrix_sparse(root, b_idx, p_idx)
    E = constraint_matrix_sparse(batterseqs)
    F = constraint_matrix_sparse(pitcherseqs)

    y, x, v, p, q = solve_equilibrium(A, E, F)

    behav_p = realization_to_behavioural_fast(y, pitcherseqs)
    behav_b = realization_to_behavioural_fast(x, batterseqs)
"""

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix, hstack
from scipy.optimize import linprog

ROOT = ((),)
TOL = 1e-10


# ----------------------------------------------------------------------
# sparse constraint matrix (works for either player)
# ----------------------------------------------------------------------
def constraint_matrix_sparse(sequencelist):
    """Row 0: root mass = 1.  Row i (=infoset id i): sum of the infoset's
    action-sequences minus its parent sequence = 0.  Same conventions as
    your batter_/pitcher_constraint_matrix, but sparse and O(n)."""
    idx = {s: j for j, s in enumerate(sequencelist)}
    max_iset = max(s[-1][0] for s in sequencelist if s != ROOT)
    rows, cols, vals = [0], [0], [1.0]
    seen_parent = set()          # add each row's -1 exactly once
    for j, seq in enumerate(sequencelist):
        if seq == ROOT:
            continue
        iset = seq[-1][0]
        parent = seq[:-1] if len(seq) > 1 else ROOT
        rows.append(iset); cols.append(j); vals.append(1.0)
        if iset not in seen_parent:
            rows.append(iset); cols.append(idx[parent]); vals.append(-1.0)
            seen_parent.add(iset)
    M = coo_matrix((vals, (rows, cols)),
                   shape=(1 + max_iset, len(sequencelist)),
                   dtype=np.float64).tocsr()
    return M


# ----------------------------------------------------------------------
# one-shot equilibrium solve
# ----------------------------------------------------------------------
def solve_equilibrium(A, E, F):
    """Returns (y, x, v, p, q):
       y pitcher realization plan, x batter realization plan,
       v game value (= your primal = your dual_val),
       p, q the sequence-form dual vectors (batter/pitcher side)."""
    A = csr_matrix(A); E = csr_matrix(E); F = csr_matrix(F)
    n, m = A.shape                       # n batter seqs, m pitcher seqs
    k, t = E.shape[0], F.shape[0]

    e = np.zeros(k); e[0] = 1.0
    f = np.zeros(t); f[0] = 1.0

    # variables z = [y (m) ; p (k)]
    c = np.concatenate([np.zeros(m), e])                 # min e^T p
    A_ub = hstack([A, -E.T], format="csr")               # A y - E^T p <= 0
    b_ub = np.zeros(n)
    A_eq = hstack([F, csr_matrix((t, k))], format="csr") # F y = f
    b_eq = f
    bounds = [(0, None)] * m + [(None, None)] * k

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")
    if not res.success:
        raise RuntimeError(f"HiGHS failed: {res.message}")

    y = res.x[:m]
    p = res.x[m:]
    v = float(res.fun)

    # batter plan = duals of the inequality block.  scipy's sign convention
    # for <= rows in a min problem gives non-positive marginals, so negate;
    # guard against convention drift across scipy versions.
    x = -np.asarray(res.ineqlin.marginals, dtype=float)
    if not np.allclose(E @ x, e, atol=1e-6):
        x = -x
    q = np.asarray(res.eqlin.marginals, dtype=float)

    # self-checks (cheap; drop if you like)
    assert np.allclose(F @ y, f, atol=1e-7), "pitcher flow violated"
    assert np.allclose(E @ x, e, atol=1e-6), "batter flow violated"
    x_clip = np.clip(x, 0.0, None)
    assert abs(x_clip @ (A @ y) - v) < 1e-5, "x'Ay != value"
    return y, x_clip, v, p, q


# ----------------------------------------------------------------------
# fast, hardened realization -> behavioural
# ----------------------------------------------------------------------
def realization_to_behavioural_fast(realization, sequencelist, tol=TOL):
    """O(#sequences).  Same output format as your converter:
    {infoset: {action: prob}}.  Zero-mass infosets get the uniform fill;
    positive-mass infosets are renormalised over their children so each
    mix sums to exactly 1 regardless of LP round-off."""
    idx = {s: j for j, s in enumerate(sequencelist)}
    children = {}                                # infoset -> [(action, j)]
    parent_of = {}                               # infoset -> parent seq index
    for j, seq in enumerate(sequencelist):
        if seq == ROOT:
            continue
        iset, action = seq[-1]
        children.setdefault(iset, []).append((action, j))
        parent_of[iset] = idx[seq[:-1] if len(seq) > 1 else ROOT]

    behavioural = {}
    for iset, acts in children.items():
        behavioural[iset] = {}
        parent_mass = realization[parent_of[iset]]
        if parent_mass <= tol:
            for action, _ in acts:
                behavioural[iset][action] = 1.0 / len(acts)
        else:
            raw = {a: max(float(realization[j]), 0.0) for a, j in acts}
            total = sum(raw.values())
            for a, v in raw.items():
                behavioural[iset][a] = (v / total) if total > tol \
                                       else 1.0 / len(acts)
    return behavioural