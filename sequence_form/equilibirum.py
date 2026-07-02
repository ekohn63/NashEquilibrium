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
    for index, sequence in enumerate(sequencelist):
        print(sequence, end = "     ")
        #index = sequencelist.index(sequence)
        if sequence == ((),): 
            continue
        infoset = sequence[-1][0]
        if len(sequence) > 2:
            parent_sequence = sequence[:-1]
        elif len(sequence) == 2:
            parent_sequence = sequence[:-1]
        else:
            parent_sequence = ((),)
        parent_index = sequencelist.index(parent_sequence)
        F[infoset, index] = 1.0
        F[infoset, parent_index] = -1.0

    return F

# batter matrix E
def batter_constraint_matrix(root, sequencelist:list): 
    num_infosets = get_num_infosets(root, "Batter")
    print(num_infosets)
    print(len(sequencelist))
    E = np.zeros((1+num_infosets, len(sequencelist)), dtype = np.float64)
    E[0, 0] = 1

    for sequence in sequencelist: 
        index = sequencelist.index(sequence)
        if sequence == ((),): 
            continue
        infoset = sequence[-1][0]
        if len(sequence) > 2:
            parent_sequence = sequence[:-1]
        elif len(sequence) == 2: 
            parent_sequence = sequence[:-1]
        else:
            parent_sequence = ((),)
        #print(f"p_seq: {parent_sequence}")
        parent_index = sequencelist.index(parent_sequence)
        E[infoset,index] = 1
        E[infoset,parent_index] = -1
        
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



def pyomo_primal(A,E,F): 
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
        return sum(-F[i, j] * model.y[j] for j in model.M) == -f[i]
    model.eq_constraints = Constraint(model.Q, rule=eq_constraint)

    solver = SolverFactory('highs')
    solver.solve(model, tee=False)

    y_val = [value(model.y[j]) for j in model.M]   # ← guaranteed correct
    p_val = [value(model.p[i]) for i in model.K]
    #print("y =", y_val)
    val = (value(model.obj))
    #print(val)
    assert np.allclose(F @ y_val, f, atol=1e-8)

    return y_val, p_val, val


    """
    filename = ''.join([str(Path(__file__).parent),"\pyomo_model.lp"])
    model.write(filename)

    h = highspy.Highs()
    
    status = h.readModel(filename)
    h.run()
    info = h.getInfo()
    solution = h.getSolution()
    print('Optimal objective = ', info.objective_function_value)
    print(f"primal var_values: {solution.col_value}")
    print(f"dual values: {solution.row_dual}")

    
    names = h.get()          # list of column names in HiGHS order
    vals  = h.getSolution().col_value  # corresponding values

    y_val = [0.0]*len(model.M)
    for idx, name in enumerate(names):
        if name.startswith("y["):
            j = int(name[2:-1])        # extract the index
            y_val[j] = vals[idx]

    print("y =", y_val)
    """

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

    model.dual = Suffix(direction=Suffix.IMPORT)

    solver = SolverFactory('highs')
    solver.solve(model, tee=False)

    x_val = [value(model.x[j]) for j in model.N]   # ← guaranteed correct
    q_val = [value(model.q[i]) for i in model.T]

    y_from_dual = np.array([model.dual[model.ineq_constraints[j]] for j in model.M], dtype=float)
    p_from_dual = np.array([model.dual[model.equality[r]]        for r in model.K], dtype=float)

    val = (value(model.objective))

    print(e)
    assert np.allclose(E @ x_val, e, atol=1e-8)
    assert np.allclose(x_val @ A @ y_from_dual, val, atol=1e-8)

    return x_val, q_val, val, y_from_dual, p_from_dual

    """
    filename = ''.join([str(Path(__file__).parent),"\pyomo_dual.lp"])
    model.write(filename)

    h = highspy.Highs()
    
    status = h.readModel(filename)
    h.run()
    info = h.getInfo()
    solution = h.getSolution()
    col_values = solution.col_value
    print('Optimal objective = ', info.objective_function_value)
    print(f"dual values: {solution.col_value}")
    print(f"primal values: {solution.row_dual}")
    return col_values, solution.row_dual
    """
"""
def pyomo_batter_br(A, E):
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
"""
def pyomo_batter_br(A, E, y, write_lp=False):
    """
    Batter best response in sequence form.

    Solves:

        max_x x^T A y
        s.t.  E x = e
              x >= 0

    where:
        A is the batter payoff matrix, shape (# batter sequences, # pitcher sequences)
        E is the batter flow-constraint matrix, shape (# batter infoset constraints, # batter sequences)
        y is the pitcher's realization plan, shape (# pitcher sequences,)
    """

    A = np.asarray(A, dtype=float)
    E = np.asarray(E, dtype=float)
    y = np.asarray(y, dtype=float)

    n, m = A.shape          # n batter sequences, m pitcher sequences
    k, n_E = E.shape        # k batter flow constraints

    assert n_E == n, f"E has {n_E} columns, but A has {n} batter sequences"
    assert y.shape == (m,), f"y should have shape ({m},), got {y.shape}"

    # Payoff vector c = A y, so objective is c^T x
    Ay = A @ y

    # Batter sequence-form RHS
    e = np.zeros(k)
    e[0] = 1.0

    model = ConcreteModel()

    # x indices: batter sequences
    model.N = RangeSet(0, n - 1)

    # flow-constraint indices
    model.K = RangeSet(0, k - 1)

    # Batter realization plan x >= 0
    model.x = Var(model.N, domain=NonNegativeReals)

    # max_x x^T A y
    def obj_rule(model):
        return sum(Ay[i] * model.x[i] for i in model.N)

    model.obj = Objective(rule=obj_rule, sense=maximize)

    # E x = e
    def eq_constraint(model, j):
        return sum(E[j, i] * model.x[i] for i in model.N) == e[j]

    model.constraints = Constraint(model.K, rule=eq_constraint)

    # Import duals, useful if you want the dual variables p
    model.dual = Suffix(direction=Suffix.IMPORT)

    if write_lp:
        lp_path = Path.cwd() / "pyomo_batter_br.lp"
        model.write(str(lp_path))

    solver = SolverFactory("highs")
    results = solver.solve(model, tee=False)

    x_val = np.array([value(model.x[i]) for i in model.N])
    p_from_dual = np.array([model.dual[model.constraints[j]] for j in model.K])
    val = value(model.obj)

    assert np.allclose(E @ x_val, e, atol=1e-8), "Batter realization plan violates E x = e"

    return x_val, p_from_dual, val

def pyomo_pitcher_br(F, B, x): 
    model = ConcreteModel()
    
    n, m = B.shape
    p = F.shape[0]

    model.M = RangeSet(0, m-1)
    model.N = RangeSet(0, n-1)
    model.P = RangeSet(0, p-1) # number of pitcher infosets

    f = np.zeros(p)
    f[0] = 1

    model.y = Var(model.M, domain=NonNegativeReals)

    # max (x^T B)y
    def obj_rule(model):
        return sum( sum(x[i] * B[i, j] for i in model.N) * model.y[j] for j in model.M)
    model.obj = Objective(rule=obj_rule, sense=maximize)

    def eq_constraint(model, j):
        return sum(F[j, i] * model.y[i] for i in model.M) == f[j]
    model.constraints = Constraint(model.P, rule=eq_constraint)
    
    model.dual = Suffix(direction=Suffix.IMPORT)

    solver = SolverFactory('highs')
    solver.solve(model, tee=False)

    y_val = [value(model.y[j]) for j in model.M]   
    q_from_dual = [value(model.dual[model.constraints[j]]) for j in model.P]

    val = (value(model.obj))

    assert np.allclose(F @ y_val, f, atol=1e-8)

    return y_val, q_from_dual, val