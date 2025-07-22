from typing import Hashable, Sequence, Tuple
from model.induced_tree import Node


# first infoset is least significant
def idx_to_strat(idx:int, base:int, info_sets: int, action_set: Sequence) -> Tuple: 
    out = {}
    for i in range(info_sets):
        out[i+1] = None  # i+1 since range starts at 0

    for pos in (range(info_sets)):
        pos = pos + 1  # i+1 since we want infoset to start at 1 
        (idx, position) = divmod(idx, base)
        out[pos] = action_set[position]
    return out

# first info set is least significat -> most significant
def strat_to_idx(strategy: dict[Hashable, Node], base, action_set):
    length = 0
    idx = 0
    for info_set, action_at_infoset in strategy.items():
        print(f"act_info: {action_at_infoset}")
        idx += action_at_infoset.value * (base**(info_set - 1))
        length += 1
    return idx