import math
import pickle
from scipy.optimize import linprog
import numpy as np
from model.action_set import BATTER_ACTIONS, PITCHER_ACTIONS
from model.batter_strategies import num_infosets
from model.helpers import idx_to_strat
from pyomo.environ import *

def maximin(U: np.ndarray):
    nB, nP = U.shape
    model = ConcreteModel()
    model.P = RangeSet(0, nP - 1)     
    model.B = RangeSet(0, nB - 1)    
    
    model.U = Param(model.P, model.B, initialize=lambda m,i,j: float(U[i, j]))

    model.alpha = Var(domain=Reals)                    # α free
    model.x   = Var(model.B, domain=NonNegativeReals)    # π_B ≥ 0

    model.obj = Objective(expr=model.alpha, sense=maximize)

    def maximum_constraint(model, i):
        return model.alpha - sum(model.U[j, i] * model.x[j] for j in model.B) <= 0
    
    model.payoff_ub = Constraint(model.P, rule=maximum_constraint)

    model.simplex = Constraint(expr=sum(model.x[j] for j in model.B) == 1)

    return model


def minimax(U: np.ndarray):
    nB, nP = U.shape
    model = ConcreteModel()
    model.P = RangeSet(0, nP - 1)
    model.B = RangeSet(0, nB - 1)
    model.U = Param(model.P, model.B, initialize=lambda m,i,j: float(U[i, j]))

    model.beta = Var(domain=Reals)                      # β free
    model.y  = Var(model.P, domain=NonNegativeReals)      # π_P ≥ 0

    model.obj = Objective(expr=model.beta, sense=minimize)

    def minimum_constraint(m, i):
        return m.beta - sum(model.U[i, j] * model.y[j] for j in model.P) >= 0
    model.payoff_lb = Constraint(model.B, rule = minimum_constraint)

    model.simplex = Constraint(expr=sum(model.y[i] for i in model.P) == 1)

    return model


#----------- Old Version for completemss using scipy.optimize lin prog solver
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

    file_path = "C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\data\\batter_optimal.pkl"
    with open(file_path, mode = 'wb') as file:
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

    file_path = "C:\\Users\\elidk\\PycharmProjects\\NashEquilibirum\\data\\batter_optimal.pkl"
    with open(file = file_path, mode = 'wb') as f:
        pickle.dump(q, f)

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

def find_saddle_points(U): 
    v = pure_strat_col_player_second(U)
    w = pure_strat_row_player_second(U)

    saddle_points = []
    if math.isclose(v, w, rel_tol = 1e-8): 
        saddle_points.append(v)

    return saddle_points

def pure_strategies(piB, piP, PINFOSETS): 
    pitcher_pure_strat = []
    for idx, val in enumerate(piP):
        if val > 0: 
            strat = idx_to_strat(idx, len(PITCHER_ACTIONS), PINFOSETS, PITCHER_ACTIONS)
            pitcher_pure_strat.append(strat)

    batter_pure_strat = []
    for idx, val in enumerate(piB):
        if val > 0: 
            strat = idx_to_strat(idx, len(BATTER_ACTIONS), num_infosets(), BATTER_ACTIONS)
            batter_pure_strat.append(strat)

    return pitcher_pure_strat, batter_pure_strat