"""
fig_path_comparison.py — Figure 4: equilibrium mixing along a realized plate
appearance, compared across base-out records.

The fixed path (see caption): 0-0 --[OS chase, Take -> Ball]--> 1-0
--[OS chase, Take -> Ball]--> 2-0 --[FB bottom, Take -> Strike]--> 2-1.
Information-set ids below are for the tree export shipped in DATA_DIR; if the
tree is regenerated, re-derive them by walking that path in induced_tree.txt.

Output: record_comparison_path.{png,pdf}
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

from figures_common import parse_strat, PITCHER_ACTIONS, BATTER_ACTIONS

# ----------------------------------------------------------------- config
DATA_DIR = Path("data")
OUT_DIR = Path("figures")

RECORDS = [  # (label, pitcher export, batter export, hatch, alpha)
    ("runner on 3rd, 0 out",
     "pitcher_behavioural_(0 outs, runner on third).txt",
     "batter_behavioural_(0 outs, runner on third).txt", None, 1.00),
    ("bases loaded, 1 out",
     "pitcher_behavioural_(1 out, bases loaded).txt",
     "batter_behavioural_(1 out, bases loaded).txt", "//", 0.75),
    ("bases empty, 1 out",
     "pitcher_behavioural_(1 out, bases clear).txt",
     "batter_behavioural_(1 out, bases clear.txt", "..", 0.50),
]

# on-path information sets (pitcher, batter) at each count of the fixed path
PITCHER_ISETS = [(1, "count 0\u20130"), (642, "count 1\u20130"),
                 (714, "count 2\u20130"), (717, "count 2\u20131")]
BATTER_ISETS = [1, 642, 713, 715]
TRANSITIONS = ["OS chase, take\n$\\downarrow$\nball",
               "OS chase, take\n$\\downarrow$\nball",
               "FB bottom, take\n$\\downarrow$\nstrike"]

ACTION_COLOR = {"Fastball_Bottom": "#1f77b4", "Offspeed_Bottom": "#2ca02c",
                "Offspeed_Chase": "#d62728", "Swing": "#ff7f0e",
                "Take": "#7f7f7f"}
PITCHER_LABELS = ["FB\nbottom", "OS\nbottom", "OS\nchase"]
BATTER_LABELS = ["Swing", "Take"]
# -------------------------------------------------------------------------

data = [(label,
         parse_strat(DATA_DIR / pf),
         parse_strat(DATA_DIR / bf),
         hatch, alpha)
        for label, pf, bf, hatch, alpha in RECORDS]
n_rec = len(data)
bar_w = 0.72 / n_rec

mpl.rcParams.update({"font.family": "serif", "font.size": 12,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "hatch.linewidth": 0.7})
fig, axes = plt.subplots(2, 4, figsize=(19.5, 7.6),
                         gridspec_kw={"wspace": 0.62, "hspace": 0.38})


def draw_panel(ax, actions, mixes, xticklabels, label_size):
    for j, (mix, hatch, alpha) in enumerate(mixes):
        for i, action in enumerate(actions):
            v = max(mix.get(action, 0.0), 0.0)
            x = i - 0.40 + (0.80 / n_rec) * (j + 0.5)
            ax.bar([x], [v], width=bar_w, color=ACTION_COLOR[action],
                   alpha=alpha, hatch=hatch, edgecolor="white", lw=0.6)
            if v > 0.005:
                ax.text(x, v + 0.03, f"{v:.2f}".lstrip("0"),
                        ha="center", fontsize=9)
    ax.set_xticks(range(len(actions)))
    ax.set_xticklabels(xticklabels, fontsize=label_size)
    ax.set_ylim(0, 1.16)
    ax.set_yticks([0, 0.5, 1.0])


for col, ((p_iset, title), b_iset) in enumerate(zip(PITCHER_ISETS,
                                                    BATTER_ISETS)):
    ax_p, ax_b = axes[0][col], axes[1][col]
    draw_panel(ax_p, PITCHER_ACTIONS,
               [(pit[p_iset], h, a) for _, pit, _, h, a in data],
               PITCHER_LABELS, 12)
    draw_panel(ax_b, BATTER_ACTIONS,
               [(bat[b_iset], h, a) for _, _, bat, h, a in data],
               BATTER_LABELS, 13)
    ax_p.set_title(title, fontsize=14, pad=10)
    if col > 0:
        ax_p.set_yticklabels([])
        ax_b.set_yticklabels([])

axes[0][0].set_ylabel("pitcher behavioural\nprobability", fontsize=12)
axes[1][0].set_ylabel("batter behavioural\nprobability", fontsize=12)

# transition annotations centered in the gaps between top-row panels
fig.canvas.draw()
for col, text in enumerate(TRANSITIONS):
    right = axes[0][col].get_position()
    left = axes[0][col + 1].get_position()
    x_mid = (right.x1 + left.x0) / 2
    y_mid = (right.y0 + right.y1) / 2
    fig.text(x_mid, y_mid + 0.03, text, ha="center", va="center",
             fontsize=10.5, color="0.3")
    fig.text(x_mid, y_mid - 0.10, r"$\longrightarrow$", ha="center",
             fontsize=15, color="0.3")

handles = [mpl.patches.Patch(facecolor="0.45", alpha=a, hatch=h,
                             edgecolor="white", label=lab)
           for lab, _, _, h, a in data]
fig.legend(handles=handles, loc="upper center", ncol=n_rec, frameon=False,
           fontsize=13, bbox_to_anchor=(0.5, 1.0))
fig.suptitle("Equilibrium mixing along a realized plate appearance, "
             "compared across base\u2013out records", y=1.075, fontsize=15)

OUT_DIR.mkdir(exist_ok=True)
fig.savefig(OUT_DIR / "record_comparison_path.png", dpi=300,
            bbox_inches="tight")
fig.savefig(OUT_DIR / "record_comparison_path.pdf", bbox_inches="tight")
print("wrote", OUT_DIR / "record_comparison_path.{png,pdf}")
