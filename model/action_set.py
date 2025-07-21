from enum import Enum, auto

class Location(Enum):
    Bottom = auto()
    Middle = auto()
    Top = auto()
    Chase = auto()

class Type(Enum):
    Fastball = auto()
    Offspeed = auto()

class BatterAction(Enum):
    Swing = auto()
    Take = auto()

class Nature(Enum):
    Single = auto()
    Double = auto()
    Triple = auto()
    HR = auto()
    Out = auto()
    Ball = auto()
    Strike = auto()

PITCHER_ACTIONS = [(l, t) for l in Location for t in Type]
BATTER_ACTIONS = list(BatterAction)
NATURE_ACTIONS = list(Nature)