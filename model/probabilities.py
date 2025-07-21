from collections import defaultdict
from pathlib import Path
import pandas as pd

from .action_set import Nature
# baseline_probs.py  (values from 2024 MLB league averages)
#   Source: Baseball-Reference “League Year-by-Year Batting Averages” table  :contentReference[oaicite:0]{index=0}

csv_path = Path(__file__).with_suffix('').parent.parent/"data/pitch_outcome_probabilities.csv"

df = pd.read_csv(csv_path, names= ["Location", "Type", "BatterAction", "Outcome", "Probability"])

df.drop(index=df.index[0], axis=0, inplace=True)

prob_dict = defaultdict(lambda: defaultdict(dict))

for _, row in df.iterrows():
    loc = row["Location"]
    typ = row["Type"]
    action = row["BatterAction"]
    outcome = row["Outcome"]
    prob = row["Probability"]
    prob_dict[(loc, typ)][action][outcome] = prob

# Convert defaultdict to regular dict for export
final_dict = {k: dict(v) for k, v in prob_dict.items()}

converted_dict = {}

for pitcher_action, batter_actions in final_dict.items():
    converted_batter_actions = {}
    for batter_action, outcomes in batter_actions.items():
        converted_outcomes = {Nature[outcome]: prob for outcome, prob in outcomes.items()}
        converted_batter_actions[batter_action] = converted_outcomes
    converted_dict[pitcher_action] = converted_batter_actions

# Show a small sample
sample = dict(list(converted_dict.items())[:2])

"""
PROBS = dict(
    SWING={
        Nature.Single: 0.08,
        Nature.Double: 0.025,
        Nature.Triple: 0.003,
        Nature.HR   : 0.03,
        Nature.Out  : 0.25,
        Nature.Strike: 0.25,
        Nature.Ball : 0.362
    },
    TAKE={
        Nature.Single: 0.0,
        Nature.Double: 0.0,
        Nature.Triple: 0.0,
        Nature.HR   : 0.0,
        Nature.Out  : 0.0,
        Nature.Strike: 0.40,
        Nature.Ball : 0.60
    }
)

if __name__ == "__main__":
    for (event, prob) in PROBS["SWING"].items():
        print(event,prob)

"""
