from typing import Hashable, Sequence, Tuple
from model.induced_tree import Node

def idx_to_strat(idx:int, base:int, length: int, action_set: Sequence) -> Tuple: 
    out = [None]*length
    for pos in (range(length)):
        (idx, position) = divmod(idx, base)
        out[pos] = action_set[position]
    return tuple(out)

# first info set is most significat -> least significant
def strat_to_idx(strategy: dict[Hashable, Node], base, action_set):
    length = len(strategy)-1
    idx = 0
    for info_set, action_at_infoset in strategy.items():
        idx += action_at_infoset.value * (base**length)
        length -= 1
    return idx