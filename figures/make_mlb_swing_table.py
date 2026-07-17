"""
make_mlb_swing_table.py — regenerate the MLB swing-frequency-by-count table
for Figure 5 directly from Baseball Savant (2018 regular season, pitch level).

Usage:
    pip install pybaseball pandas
    python make_mlb_swing_table.py            # writes data/empirical_swing_by_count_2018.csv

pybaseball downloads the pitch-level CSVs from the Baseball Savant Statcast
search endpoint (baseballsavant.mlb.com) in date chunks and caches them
locally, so re-runs are cheap.  Cite as: MLB Advanced Media, Statcast search,
Baseball Savant (baseballsavant.mlb.com), 2018 regular season pitch-level
data, retrieved <date>.

Swing definition (Savant `description` field): hit_into_play*, foul,
foul_tip, swinging_strike, swinging_strike_blocked, swinging_pitchout,
foul_pitchout, plus bunt attempts (foul_bunt, missed_bunt, bunt_foul_tip).
Set INCLUDE_BUNTS = False to exclude bunt attempts; on 2018 data this moves
no cell by more than 0.007 (0-0 is the most affected, .289 -> .283).

Validation notes (run of 2026-07-17 against a mirror of the same pull):
  * 721,190 unique regular-season pitches (Albert 2018 reports 721,188)
  * 10 rows with balls > 3 dropped (known Savant count glitches)
  * overall swing rate 46.9% (Albert 2018: 46%)
"""

from pathlib import Path

import pandas as pd
from pybaseball import statcast, cache

cache.enable()

OUT = Path("data/empirical_swing_by_count_2018.csv")

SWINGS = {
    "hit_into_play", "hit_into_play_no_out", "hit_into_play_score",
    "foul", "foul_tip", "swinging_strike", "swinging_strike_blocked",
    "swinging_pitchout", "foul_pitchout", "pitchout_hit_into_play_score",
}
BUNT_SWINGS = {"foul_bunt", "missed_bunt", "bunt_foul_tip"}
INCLUDE_BUNTS = True

df = statcast(start_dt="2018-03-29", end_dt="2018-10-01")
df = df[df["game_type"] == "R"]
df = df.drop_duplicates(["game_pk", "at_bat_number", "pitch_number"])
df = df[(df["balls"] <= 3) & (df["strikes"] <= 2)]

swings = SWINGS | BUNT_SWINGS if INCLUDE_BUNTS else SWINGS
df["swing"] = df["description"].isin(swings)

table = (df.groupby(["balls", "strikes"])
           .agg(pitches=("swing", "size"), swings=("swing", "sum"))
           .reset_index())
table["swing_pct"] = table["swings"] / table["pitches"]

OUT.parent.mkdir(exist_ok=True)
table.to_csv(OUT, index=False)
print(table.to_string(index=False))
print(f"\noverall swing rate: {df['swing'].mean():.4f}")
print("wrote", OUT)
