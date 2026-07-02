from enum import Enum, auto

class PitcherAction(Enum):
    Fastball_Bottom = 0
    #Fastball_Middle = 1
    Fastball_Top = 2
    #Fastball_Chase = 3
    Offspeed_Bottom = 4
    #Offspeed_Middle = 5
    #Offspeed_Top = 6
    Offspeed_Chase = 7

class BatterAction(Enum):
    Swing = 0
    Take = 1

class Nature(Enum):
    Single = auto()
    Double = auto()
    Triple = auto()
    HR = auto()
    Out = auto()
    Ball = auto()
    Strike = auto()

PITCHER_ACTIONS = list(PitcherAction)
BATTER_ACTIONS = list(BatterAction)
NATURE_ACTIONS = list(Nature)

NONTERMINAL_NATURE = [Nature.Ball, Nature.Strike]