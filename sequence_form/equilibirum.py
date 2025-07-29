from pathlib import Path
import numpy as np
from scipy.sparse import csc_matrix
from model.induced_tree import get_num_infosets

import highspy, math
from pyomo.environ import *

#constructing pitcher constraint matrix F, and batter constraint matrix E

# pitcher matrix F
def pitcher_constraint_matrix(root, sequencelist: list):
    num_infoset = get_num_infosets(root, "Pitcher")
    F = np.zeros(shape = ((1+num_infoset),len(sequencelist)), dtype = np.float64)
    F[0,0] = 1.0
    for sequence in sequencelist:
        index = sequencelist.index(sequence)
        if sequence == ((),): 
            continue
        infoset = sequence[-1][0]
        if len(sequence) > 2:
            parent_sequence = sequence[:-2]
        elif len(sequence) == 2:
            parent_sequence = (sequence[:-2],)
        else:
            parent_sequence = ((),)
        parent_index = sequencelist.index(parent_sequence)
        F[infoset, index] = 1.0
        F[infoset, parent_index] = -1.0
    
    # constructin glittle f:
    f = np.zeros(shape = ((1+num_infoset),1), dtype = np.float64)
    f[0,0] = 1.0

    return F

# batter matrix E
def batter_constraint_matrix(root, sequencelist:list): 
    num_infosets = get_num_infosets(root, "Batter")
    print(num_infosets)
    E = np.zeros((1+num_infosets, len(sequencelist)), dtype = np.float64)
    E[0, 0] = 1

    for sequence in sequencelist: 
        #print(f"\033[91m {sequence} \033[0m")
        index = sequencelist.index(sequence)
        if sequence == ((),): 
            continue
        infoset = sequence[-1][0]
        if len(sequence) > 2:
            parent_sequence = sequence[:-2]
        elif len(sequence) == 2: 
            parent_sequence = (sequence[:-2],)
        else:
            parent_sequence = ((),)
        print(f"p_seq: {parent_sequence}")
        parent_index = sequencelist.index(parent_sequence)
        E[infoset,index] = 1
        E[infoset,parent_index] = -1

    # little e:
    e = np.zeros(((1+num_infosets),1), dtype = np.float64)
    e[0,0] = 1.

    return E


# primal LP to minimizat eTp

def build_primal_MPS(root, batterlist, pitcherlist, A):
    print(A)
    E = batter_constraint_matrix(root, batterlist)
    F = pitcher_constraint_matrix(root, pitcherlist)
    f = np.zeros(shape = F.shape[0], dtype = np.float64)
    f[0] = 1

    m_ineq, n_y = A.shape
    n_p = E.shape[0]            # |1 + U_B|
    m_eq = F.shape[0]           # |1 + U_P|

    h = highspy.Highs()
    inf = highspy.kHighsInf

    #--------------------add rows (constraints)----------------------
    empty_i = np.empty(0, dtype=np.int32)
    empty_v = np.empty(0, dtype=np.float64)

    for i in range(m_ineq):
        h.addRow(0.0,inf,0,empty_i,empty_v)
        
    for i in range(m_eq):
        h.addRow(-f[i],-f[i],0, empty_i, empty_v)#upper

    #------------------add y variables (columns)------------------
    for j in range(n_y):
        indices = []  #indices = [0 … m_in‑1, m_in … m_in+m_eq‑1]
        values = []   #[‑A_{0j}, … , ‑A_{m_in‑1,j}, ‑F_{0j}, … , ‑F_{m_eq‑1,j}]
        for i in range(m_ineq):
            indices.append(i)
            values.append(-A[i,j])
        
        for k in range(m_eq):
            indices.append(k + m_ineq)
            values.append(-F[k,j])

        arr = np.array(indices, dtype=np.int32)
        vals = np.array(values, dtype = np.float64)

        assert arr.ndim == 1
        assert vals.ndim == 1
        assert arr.shape[0] == vals.shape[0]
        assert not np.any(np.isnan(vals))
        assert not np.any(np.isnan(arr))
        status = h.addCol(
            0.0, #cost
            0.0,  #lower
            inf,  #upper
            m_ineq + m_eq, #len
            arr, #indices
            vals)
    
    #-------------------add p variables (columns)-------------------
    for k in range(n_p):
        indices = []
        values = []
        for i in range(m_ineq):
            indices.append(i)
            values.append(E[k,i])
        if k == 0:
            h.addCol(
                1., #csot
                -inf, #lower
                inf, #upper
                m_ineq, #num elements
                indices, 
                values
            )
        else:
            h.addCol(
                0., #csot
                -inf, #lower
                inf, #upper
                m_ineq, #num elements
                indices, 
                values
            )

    h.writeModel(f"{Path(__file__).parent}\zero_sum.mps")
    h.writeModel(f"{Path(__file__).parent}\zero_sum.lp")
    #print("MPS file written with", h.getNumCols(), "vars and", h.getNumRows(), "rows.")
    h.run()
    solution = h.getSolution()
    basis = h.getBasis()
    info = h.getInfo()
    model_status = h.getModelStatus()
    print('Model status = ', h.modelStatusToString(model_status))
    print('Optimal objective = ', info.objective_function_value)
    return h


def peek_matrix(h):
    col_ptr, row_ind, val = h.getMatrix()

def pyomo_mps(A,E,F): 
    n, m = A.shape # n = |S_B|, m= |S_P|
    k = E.shape[0] # |1 + U_B|
    q = F.shape[0] # |1 + U_P|

    e = np.zeros(k)
    e[0] = 1
    f = np.zeros(q)
    f[0] = 1

    # Pyomo model
    model = ConcreteModel()

    # Index sets
    model.M = RangeSet(0, m - 1)  # indices for y
    model.K = RangeSet(0, k - 1)  # indices for p
    model.N = RangeSet(0, n - 1)  # constraints from -Ay + ET p >= 0
    model.Q = RangeSet(0, q - 1)  # constraints from -F y = -f

    # Decision variables
    model.y = Var(model.M, domain=NonNegativeReals)
    model.p = Var(model.K)

    # Objective: minimize e^T p
    def obj_rule(model):
        return sum(e[j] * model.p[j] for j in model.K)
    model.obj = Objective(rule=obj_rule, sense=minimize)

    # Constraint 1: -A y + E^T p >= 0
    def ineq_constraint(model, i):  # for each row i in n constraints
        ay = sum(-A[i, j] * model.y[j] for j in model.M)
        etp = sum(E[j, i] * model.p[j] for j in model.K)  # column i of E^T
        return ay + etp >= 0
    model.ineq_constraints = Constraint(model.N, rule=ineq_constraint)

    # Constraint 2: -F y = -f  <==> F y = f
    def eq_constraint(model, i):
        return sum(F[i, j] * model.y[j] for j in model.M) == f[i]
    model.eq_constraints = Constraint(model.Q, rule=eq_constraint)


    filename = ''.join([str(Path(__file__).parent),"\pyomo_model.lp"])
    model.write(filename)

    h = highspy.Highs()
    
    status = h.readModel(filename)
    h.run()
    info = h.getInfo()
    print('Optimal objective = ', info.objective_function_value)

def pyomo_dual(A,E,F):
    n, m = A.shape
    k = E.shape[0]
    t = F.shape[0]

    f = np.zeros(t)
    f[0] = 1
    e = np.zeros(k)
    e[0] = 1

    model = ConcreteModel()

    model.N = RangeSet(0, n-1)
    model.M = RangeSet(0, m-1)
    model.K = RangeSet(0, k-1)
    model.T = RangeSet(0, t-1)

    model.x = Var(model.N, domain = NonNegativeReals)
    model.q = Var(model.T, domain = Reals)

    def objective_function(model):
        return sum(-f[i]*model.q[i] for i in model.T)   #fT @ q
    
    model.objective = Objective(rule=objective_function, sense=maximize)

    def inequality_constraint(model, j):
        xTA = sum(model.x[i] * -A[i,j] for i in model.N) 
        qTF = sum(model.q[i] * F[i,j] for i in model.T)
        return xTA-qTF <= 0
    model.ineq_constraints = Constraint(model.M, rule = inequality_constraint)

    def equality_constraint(model, j):
        return sum(model.x[i] * E[j,i] for i in model.N) == e[j]
    model.equality = Constraint(model.K, rule = equality_constraint)

    filename = ''.join([str(Path(__file__).parent),"\pyomo_dual.lp"])
    model.write(filename)

    h = highspy.Highs()
    
    status = h.readModel(filename)
    h.run()
    info = h.getInfo()
    print('Optimal objective = ', info.objective_function_value)

def pyomo_lp(A, E):
    model = ConcreteModel()

    n, m = A.shape
    k = E.shape[0]  # dimensions
    A = np.random.rand(n, m)
    y = np.random.rand(m)
    Ay = A @ y  # A * y
    e = np.zeros(k)
    e[0] = 1

    # Index sets
    model.N = RangeSet(0, n - 1)  # x indices
    model.K = RangeSet(0, k - 1)  # constraint indices

    # Decision variables: x ≥ 0
    model.x = Var(model.N, domain=NonNegativeReals)

    # Objective: maximize x^T (A y)
    def obj_rule(model):
        return sum(Ay[i] * model.x[i] for i in model.N)
    model.obj = Objective(rule=obj_rule, sense=maximize)

    # Constraint: x^T E^T = e^T  <==>  sum_i x[i] * E[j, i] = e[j]
    def eq_constraint(model, j):
        return sum(model.x[i] * E[j, i] for i in model.N) == e[j]
    model.constraints = Constraint(model.K, rule=eq_constraint)

    # Optional: export to LP format
    model.write(f"{Path(__file__).parent}\pyomo.lp")

