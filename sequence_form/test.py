from model.induced_tree import build_tree, Node, COUNTER
from sequence_form.sequence import set_sequences, set_sequences_playeri

node = Node(data = "Pitcher", info_set = 1)
root = build_tree(node)
print(f"\033[91m {COUNTER} \033[0m")
set = set_sequences(root, "Pitcher")
print(f"\033[91m {len(set)} \033[0m")
for i in (set):
    print(i)

