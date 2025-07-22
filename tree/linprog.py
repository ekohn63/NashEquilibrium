import math
import pickle
from scipy.optimize import linprog
import numpy as np
# let row player be the pitcher, colplayer be the batter

from .test import fill_matrix

# ---------- LP for the batter (row player, maximiser) ----------
# Variables: p_1..p_m  (probabilities) and v (game value)
def row_max_min(U):
    (n, m) = U.shape
    c = np.zeros(n + 1)
    c[-1] = -1      # maximise v  -> minimise -v

    A_ub = np.hstack([-U.T, np.ones((m, 1))])   #  -Aᵀ p + v ≤ 0  ⇔  pᵀA ≥ v
    b_ub = np.zeros(m)

    A_eq = np.ones((1, n + 1))                  #  ∑ p_i = 1
    A_eq[0, -1] = 0
    b_eq = np.array([1.0])

    bounds = [(0, 1)] * n + [(None, None)]      # 0 ≤ p_i ≤ 1 ,   v free

    res_row = linprog(c, A_ub, b_ub, A_eq, b_eq, bounds, method="highs")

    p = res_row.x[:n]
    v = -res_row.fun                            # remember: we minimized -v

    file_path = "C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\data\\pitcher_optimal.pkl"
    with open(file_path, mode = 'w') as file:
        pickle.dump(p, file)

    return (p, v)


# recall sci py format:
# min c @ x
#such that
#A_ub @ x <= b_ub
#A_eq @ x == b_eq
#lb <= x <= ub

# ---------- LP for the pitcher (column player, minimiser) ----------
# Variables: q_1..q_n  and w (same game value)
def col_min_max(U):
    (n, m) = U.shape 
    c2 = np.zeros(m+1)                                  # why a 1D array?, and not shape = (1, m+1)
    c2[-1] = 1                                          # minimise w

    A_ub2 = np.hstack([U, -np.ones(shape = (n, 1))])    # A q - w ≤ 0  ⇔  Aq ≤ w
    b_ub2 = np.zeros(n)                                 # why not shpae = (n, 1)

    A_eq2 = np.ones(shape = (1,m+1))                    # ∑ q_j = 1
    A_eq2[0, -1] = 0    
    b_eq2 = np.array([1.0])

    bounds2 = [(0,1)] * m + [(None, None)]

    col_res = linprog(c2, A_ub2, b_ub2, A_eq2, b_eq2, bounds2, method="highs")

    q = col_res.x[:m]
    w = col_res.fun
    return (q, w)

#this is assuming pure strategy nash equilibirum!
def pure_strat_col_player_second(U):
    (row, col) = U.shape

    #max _ min (col player chooses after row player)
    min = []
    for (i,rows) in enumerate(U): 
        row_min = float('inf')
        for (j, col) in enumerate(rows):
            if U[i, j] < row_min:
                row_min = U[i,j]
        min.append(row_min)
    
    row_guarantee = float('-inf')
    for row_min in min:
        if row_min > row_guarantee:
            row_guarantee = row_min

    return row_guarantee

def pure_strat_row_player_second(U):
    columns = [U[:,i] for i in range(U.shape[1])]
    max = []
    for (j, column) in enumerate(columns): 
        col_max = float('-inf')
        for (i, row) in enumerate(column):
            if U[i, j] > col_max:
                col_max = U[i,j]
        max.append(col_max)
        
    col_guarantee = float('inf')
    for row_max in max: 
        if row_max < col_guarantee: 
            col_guarantee = row_max

    return col_guarantee

def display(U, p,v, q, w):
    print("Optimal batter strategy (p):", p)
    print("Optimal pitcher strategy (q): non-zero probabilities at indices where q>0")
    print(np.where(q > 1e-8)[0], "with probs", q[q > 1e-8])
    print("Game value (expected runs for batter):", v)
    print("Min Max value:", w)
    print(U[2, 14])
    assert math.isclose(v,w, rel_tol = 1e-8)


def find_saddle_points(U): 
    v = pure_strat_col_player_second(U)
    w = pure_strat_row_player_second(U)

    saddle_points = []
    if math.isclose(v, w, rel_tol = 1e-8): 
        saddle_points.append(v)

    return saddle_points

if __name__ == "__main__":
    U = fill_matrix()
    U = U.transpose()
    #print(U)
    p,v = row_max_min(U)
    q,w = col_min_max(U)
    print(find_saddle_points(U))
    display(U, p, v, q, w)
