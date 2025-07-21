import pandas as pd
from pathlib import Path
from .state import State
from .action_set import Nature

csv_path = Path(__file__).with_suffix('').parent.parent/"data/baseball_run_expectancy.csv"

df = pd.read_csv(csv_path)

zero_out = ["2010-2015 0 outs", "1993-2009 0 outs", "1969-1992 0 outs", "1950-1968 0 outs"]
one_out = ["2010-2015 1 out", "1993-2009 1 out", "1969-1992 1 out", "1950-1968 1 out"]
two_out = ["2010-2015 2 outs", "1993-2009 2 outs", "1969-1992 2 outs", "1950-1968 2 outs"]

df["Average 0 outs"] = df[zero_out].mean(axis=1)
df["Average 1 outs"] = df[one_out].mean(axis=1)
df["Average 2 outs"] = df[two_out].mean(axis=1)

df = df[["Base Runners", "Average 0 outs", "Average 1 outs", "Average 2 outs"]]

def run_expectancy(state: State) -> float: 
    row_index = (state.on_first) + 2*(state.on_second) + 3*(state.on_third)
    col_index = (state.outs+1)
    return df.iloc[row_index, col_index]


# RV = runs_score + RE(after) - RE(before)
def terminal_utility(start: State, end: State, runs_scored: int) -> float:
    return runs_scored + run_expectancy(end) - run_expectancy(start)

if __name__ == "__main__": 
    print(csv_path)
    print(df.iloc[:, [True, False, False, False]])

    print(df)
    s = State(0, 0, 0, 0, 0, 0)
    new_s = State(0, 0, 0, 1, 0, 0)
    print(type(run_expectancy(s)))
    s_prime = State(0, 0, 1, 0, 0, 0)
    out_utility = terminal_utility(s, new_s, 0)
    print(out_utility)


"""
s = State(0,0,0,True,True,False)

print(run_expectancy(s))

print(df.shape)
"""