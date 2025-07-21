from typing import Sequence, Tuple

def idx_to_strat(idx:int, base:int, length: int, strategy: Sequence) -> Tuple: 
    out = [None]*length
    for pos in (range(length)):
        (idx, position) = divmod(idx, base)
        out[pos] = strategy[position]
    return tuple(out)
