"""
fig_swing_heatmap.py — Figure 5: realization-weighted swing rate by count,
model equilibrium (three records) vs MLB Statcast at its native counts.

Model cells: S(b,s) = reach-weighted average of the batter's behavioural
swing probability over all information sets at count (b,s); see the paper's
Figure 5 caption for the formula.  Computed by figures_common.reach_rates
from the tree export, the behavioural-strategy exports, and the Nature CSV.

MLB panel: league-wide swing frequencies (swings / pitches at each count),
2018 Statcast pitch-level data.  TODO before submission: regenerate this
table directly from Baseball Savant (e.g. via pybaseball) and cite the pull.

Output: swing_rate_true_counts.{png,pdf}
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from figures_common import parse_tree, parse_strat, load_nature, reach_rates

# ----------------------------------------------------------------- config
DATA_DIR = Path("data")
OUT_DIR = Path("figures")

RECORDS = [
    ("runner on 3rd, 0 out",
     "pitcher_behavioural_(0 outs, runner on third).txt",
     "batter_behavioural_(0 outs, runner on third).txt"),
    ("bases loaded, 1 out",
     "pitcher_behavioural_(1 out, bases loaded).txt",
     "batter_behavioural_(1 out, bases loaded).txt"),
    ("bases empty, 1 out",
     "pitcher_behavioural_(1 out, bases clear).txt",
     "batter_behavioural_(1 out, bases clear.txt"),
]

MODEL_COUNTS = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)]

# MLB 2018 swing% by count (swings / pitches).  Provenance: computed from
# 2018 Statcast pitch-level data; see TODO in the module docstring.
MLB_SWING = {"0-0": .290, "0-1": .475, "0-2": .514,
             "1-0": .422, "1-1": .536, "1-2": .578,
             "2-0": .432, "2-1": .585, "2-2": .651,
             "3-0": .108, "3-1": .559, "3-2": .724}
# -------------------------------------------------------------------------

root = parse_tree(DATA_DIR / "induced_tree.txt")
nature = load_nature(DATA_DIR / "pitch_outcome_probabilities.csv")

panels = []
for label, pitcher_file, batter_file in RECORDS:
    rates = reach_rates(root,
                        parse_strat(DATA_DIR / pitcher_file),
                        parse_strat(DATA_DIR / batter_file),
                        nature)
    grid = np.zeros((2, 3))
    for b, s in MODEL_COUNTS:
        grid[s, b] = rates[(b, s)]["swing"]
    panels.append((label, grid, 3, 2))

mlb_grid = np.zeros((3, 4))
for b in range(4):
    for s in range(3):
        mlb_grid[s, b] = MLB_SWING[f"{b}-{s}"]
panels.append(("MLB 2018 (true counts)", mlb_grid, 4, 3))

mpl.rcParams.update({"font.family": "serif", "font.size": 11})
fig, axes = plt.subplots(1, 4, figsize=(15.5, 3.9),
                         gridspec_kw={"width_ratios": [3, 3, 3, 4]})
for ax, (label, grid, n_balls, n_strikes) in zip(axes, panels):
    image = ax.imshow(grid, cmap="Oranges", vmin=0, vmax=1, aspect="auto")
    for s in range(n_strikes):
        for b in range(n_balls):
            ax.text(b, s, f"{grid[s, b]:.2f}".lstrip("0"),
                    ha="center", va="center", fontsize=11.5,
                    color="black" if grid[s, b] < 0.6 else "white")
    ax.set_xticks(range(n_balls))
    ax.set_xticklabels([str(b) for b in range(n_balls)])
    ax.set_yticks(range(n_strikes))
    ax.set_yticklabels([str(s) for s in range(n_strikes)])
    ax.set_xlabel("balls")
    ax.set_title(label, fontsize=11, pad=8)
axes[0].set_ylabel("strikes")

fig.suptitle("Realization-weighted swing rate by count: equilibrium model "
             "(walk at 3 balls, K at 2 strikes) vs MLB Statcast at its "
             "native counts", fontsize=12.5, y=1.12)
cbar = fig.colorbar(image, ax=axes, shrink=0.85, pad=0.015)
cbar.set_label("swing probability")

OUT_DIR.mkdir(exist_ok=True)
fig.savefig(OUT_DIR / "swing_rate_true_counts.png", dpi=300,
            bbox_inches="tight")
fig.savefig(OUT_DIR / "swing_rate_true_counts.pdf", bbox_inches="tight")
print("wrote", OUT_DIR / "swing_rate_true_counts.{png,pdf}")
