from dataclasses import dataclass

@dataclass(frozen = True)
class State:
    balls: int
    strikes: int
    outs: int
    on_first: bool
    on_second: bool
    on_third: bool
    
START_STATE = State(0, 0, 0, False, False, True)