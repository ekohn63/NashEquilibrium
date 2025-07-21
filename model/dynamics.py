from enum import auto
from typing import Tuple
from dataclasses import replace
from .action_set import Nature, BatterAction
from .state import State
from .payoff import terminal_utility

class Outcome: 
    Single = auto()
    Double = auto()
    Triple = auto()
    HR = auto()
    Out = auto()
    Ball = auto()
    Strike = auto()
    Strikeout = auto()
    Walk = auto()


TERMINAL_EVENTS = [Nature.Single, Nature.Double, Nature.Triple, Nature.HR, Nature.Out]
# could I use a bitmap to make the if tree a lot nicer?

# solution ideas for terminal outcome Walk: could make a new class Outcome, and include Walk as a state
# or write the event as a string - lets do the former.

#Note: I need to compare it with nature attributes since otherwise they wouldn't match, but can call advance_runner method
# withe an atribute of the Outcome class!
def state_dynamics(s: State, event:Nature) -> Tuple[State, int]:
    if event in TERMINAL_EVENTS:
        if event == Nature.Single:
            first, second, third, o, runs = advance_runner(s, Outcome.Single)
            return replace(s, on_first = first, on_second= second, on_third = third, outs = o), runs
        elif event == Nature.Double:
            first, second, third, o, runs = advance_runner(s, Outcome.Double)
            return replace(s, on_first = first, on_second= second, on_third = third, outs = o), runs
        elif event == Nature.Triple:
            first, second, third, o, runs = advance_runner(s, Outcome.Triple)
            return replace(s, on_first = first, on_second= second, on_third = third, outs = o), runs            
        elif event == Nature.HR:
            first, second, third, o, runs = advance_runner(s, Outcome.HR)
            return replace(s, on_first = first, on_second= second, on_third = third, outs = o), runs
        elif event == Nature.Out:
            first, second, third, o, runs = advance_runner(s, Outcome.Out)
            return replace(s, on_first = first, on_second= second, on_third = third, outs = o), runs
        
    if event == Nature.Ball: 
        if s.balls >=3:
            first, second, third, o, runs = advance_runner(s, Outcome.Walk)
            return replace(s, strikes = 0, balls = 0, on_first = first, on_second = second, on_third = third, outs = 0), runs
        else: 
            return replace(s, balls= s.balls + 1), 0
    elif event ==  Nature.Strike: 
        if s.strikes >= 2:
            first, second, third, o, runs = advance_runner(s, Outcome.Strikeout)
            #print(o)
            return replace(s, strikes = 0, balls = 0, on_first = first, on_second = second, on_third = third, outs = o), runs
        else: 
            return replace(s, strikes = s.strikes+1), 0
    else:
        raise ValueError(f"Unhandled event type: {event}")
    
# can extend by adding probabilitistic runner advancements
# and also can extend by adding more nuanced runner advancements like fielders choice, sac fly, double...
def advance_runner(s: State, event: Outcome) -> Tuple[bool, bool, bool, int, int]:
    first, second, third = s.on_first, s.on_second, s.on_third
    outs = s.outs
    runs = 0

    if event == Outcome.Walk: 
        if first: 
            if second: 
                if third:
                    runs += 1
                else:
                    third = True
            else: 
                second = True
        else: 
            first = True
    elif event == Outcome.Single:
        if first: 
            if second:
                if third: 
                    runs += 2
                    # runners on second, and third score, runner on first to 3rd
                    first, second, third = True, False, True
                else: 
                    runs += 1
                    # runner on first advance to third, runner on 2nd scores
                    first, second, third = True, False, True
            else: 
                if third: 
                    runs += 1
                    first, second, third = True, False, True
        else: 
            if second: 
                if third:
                    runs += 2
                    first, second, third = True, False, False
                else:
                    runs += 1
                    first, second, third = True, False, False
            else:
                if third: 
                    runs += 1
                    first, second, third = True, False, False
                else: 
                    first, second, third = True, False, False
    elif event == Outcome.Double: 
        if first:
            runs += second + third
            first, second, third = False, True, True
        else:
            runs += second + third
            first, second, third = False, True, True

    elif event == Outcome.Triple:
        runs += first + second + third
        first, second, third = False, False, True

    elif event == Outcome.HR:
        runs += first + second + third + 1
        first, second, third = False, False, False
    
    elif event == Outcome.Out or Outcome.Strikeout:
        outs += 1
    
    return (first, second, third, outs, runs)

def get_utility(start_state, end_state):
    delta_outs = start_state.outs - end_state.outs
    if delta_outs == 1: 
        # if the result was an out then runs scored is 0
        return terminal_utility(start_state, end_state, 0)
    elif delta_outs == 0: 
        scored = (start_state.on_first + start_state.on_second + start_state.on_third) - (end_state.on_first + end_state.on_second + end_state.on_third)
        return terminal_utility(start_state, end_state, scored)

if __name__ == "__main__": 
    s = State(3,2,0,0,0, 0)
    event = Nature.Out
    (new_state, runs) = state_dynamics(s, event)
    print(new_state)