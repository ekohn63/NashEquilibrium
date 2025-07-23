from model.induced_tree import Node, build_tree
from model.optimization import build_matrix
from tree.linprog import row_max_min, col_min_max, find_saddle_points, display
from behavioural.strategy import enumerate_behavioural_strat, check_equivalence

root = Node(data = "Pitcher", info_set = 1)
root = build_tree(root)

U = build_matrix(root)

U = U.transpose()
p,v = row_max_min(U)
q,w = col_min_max(U)
print(find_saddle_points(U))
display(U, p, v, q, w)

behavioural = enumerate_behavioural_strat(root, "Batter")
print(f"equivalence: {check_equivalence(behavioural, root, "Batter")}")

print(behavioural)