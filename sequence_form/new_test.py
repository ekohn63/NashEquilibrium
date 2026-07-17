"""
test_fast.py — your test.py rewritten on the sparse pipeline.

Build -> solve -> certify -> convert -> write results, in one pass.
One LP call replaces pyomo_primal + pyomo_dual; two more (optional)
best-response LPs certify the equilibrium by exploitability.

Run it exactly like test.py.  At the current tree size the whole file
executes in about a second; the same file runs unchanged at 4B/3S.
"""

import time
import numpy as np
from pathlib import Path
from scipy.optimize import linprog
from scipy.sparse import hstack  # noqa: F401  (imported by equilibrium_fast)

from model.induced_tree import build_tree, Node
from sequence_form.sequence_fast import (set_sequences_fast,
                                         compute_payoff_matrix_sparse)
from sequence_form.equilibrium_fast import (constraint_matrix_sparse,
                                            solve_equilibrium,
                                            realization_to_behavioural_fast)

# set True (small trees only!) to cross-check against the legacy pipeline
CROSS_CHECK_LEGACY = False


# ----------------------------------------------------------------------
# best responses (certification), each a single sparse LP
# ----------------------------------------------------------------------
def batter_best_response(A, E, y):
    """max_x x^T (A y)  s.t.  E x = e, x >= 0.   Returns (x_br, value)."""
    Ay = np.asarray(A @ y).ravel()
    k, n = E.shape
    e = np.zeros(k); e[0] = 1.0
    res = linprog(-Ay, A_eq=E, b_eq=e, bounds=[(0, None)] * n, method="highs")
    assert res.success, res.message
    return res.x, -res.fun


def pitcher_best_response(A, F, x):
    """min_y (x^T A) y  s.t.  F y = f, y >= 0.   Returns (y_br, value)."""
    xA = np.asarray(A.T @ x).ravel()
    t, m = F.shape
    f = np.zeros(t); f[0] = 1.0
    res = linprog(xA, A_eq=F, b_eq=f, bounds=[(0, None)] * m, method="highs")
    assert res.success, res.message
    return res.x, res.fun


# ----------------------------------------------------------------------
# build
# ----------------------------------------------------------------------
t0 = time.time()
root = build_tree(Node(data="Pitcher", info_set=1))

pitchersequences, p_idx = set_sequences_fast(root, "Pitcher")
battersequences,  b_idx = set_sequences_fast(root, "Batter")

A = compute_payoff_matrix_sparse(root, b_idx, p_idx)
E = constraint_matrix_sparse(battersequences)
F = constraint_matrix_sparse(pitchersequences)
t1 = time.time()
print(f"built: |S_P|={len(pitchersequences)}, |S_B|={len(battersequences)}, "
      f"A {A.shape} nnz={A.nnz}, E {E.shape}, F {F.shape}  ({t1-t0:.2f}s)")

if CROSS_CHECK_LEGACY:
    from sequence_form.sequence import set_sequences2, compute_payoff_matrix
    assert set_sequences2(root, "Pitcher") == pitchersequences
    assert set_sequences2(root, "Batter") == battersequences
    A_dense = compute_payoff_matrix(root)
    assert np.allclose(A.toarray(), A_dense, atol=1e-12)
    print("legacy cross-check passed (sequences identical, A identical)")

# ----------------------------------------------------------------------
# solve (one call: pitcher plan y from the primal, batter plan x from duals)
# ----------------------------------------------------------------------
y_val, x_val, dual_val, p_val, q_val = solve_equilibrium(A, E, F)
t2 = time.time()
print(f"solved: value = {dual_val:.10f}  ({t2-t1:.2f}s)")

# ----------------------------------------------------------------------
# certify: neither player can gain against the other's plan
# ----------------------------------------------------------------------
_, br_batter = batter_best_response(A, E, y_val)   # best the batter can do vs y
_, br_pitcher = pitcher_best_response(A, F, x_val) # best the pitcher can do vs x
gap = max(abs(br_batter - dual_val), abs(br_pitcher - dual_val))
print(f"exploitability: batter BR = {br_batter:.10f}, "
      f"pitcher BR = {br_pitcher:.10f}, gap = {gap:.2e}")
assert gap < 1e-6, "not an equilibrium — investigate"

# ----------------------------------------------------------------------
# convert and write results (same outputs as your results())
# ----------------------------------------------------------------------
behavioural_p = realization_to_behavioural_fast(y_val, pitchersequences)
behavioural_b = realization_to_behavioural_fast(x_val, battersequences)

print(f"dual_val: {dual_val}")

outdir = Path("results")
outdir.mkdir(exist_ok=True)
with open(outdir / "pitcher_behavioural.txt", "w") as f:
    f.write(str(behavioural_p))
with open(outdir / "batter_behavioural.txt", "w") as f:
    f.write(str(behavioural_b))
print(f"wrote results/  ({time.time()-t2:.2f}s)")

# optional: dump the tree exactly as test.py did
# with open("test_tree.txt", "w") as f:
#     root.print_tree(f)