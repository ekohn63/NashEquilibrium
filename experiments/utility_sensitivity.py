"""
Utility perturbation sensitivity experiment for the baseball sequence-form game.

Run from the project root, e.g.

    python experiments/equilibrium_utility_sensitivity.py --eps 0 0.01 0.05 0.10 --trials 20

Outputs CSV files under results/utility_sensitivity/:
  - sensitivity_summary.csv
  - behavioural_probabilities.csv
  - same_action_differences.csv

The script does not edit model/payoff.py.  Instead, it rebuilds the sequence-form
payoff matrix from terminal nodes and perturbs terminal utilities before solving
the minimax LP again.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import math
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.optimize import linprog

# Make imports work when this file is executed from experiments/ or project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from model.state import START_STATE
from model.dynamics import state_dynamics
from model.payoff import terminal_utility
import model.induced_tree as induced_tree
from model.induced_tree import Node, build_tree
from model.nature import behave_strat


def terminal_nodes(root: Node) -> list[Node]:
    leaves = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.children is None:
            leaves.append(node)
        else:
            stack.extend(node.children.values())
    return leaves


def path_to_node(root: Node, target: Node) -> list[Node]:
    path = []
    node = target
    while node is not None:
        path.append(node)
        if node is root:
            return list(reversed(path))
        node = node.parent
    raise ValueError("target is not in this tree")


def set_sequences2(root: Node, player_id: str) -> list[tuple]:
    seqs = []
    seen = {((),)}

    def dfs(node: Node, sequence: tuple) -> None:
        if node.parent is None:
            seqs.append(((),))
        if node.children is None:
            return
        for choice, child in node.children.items():
            if node.data == player_id:
                new_seq = sequence + ((node.info_set, choice),)
                if new_seq not in seen:
                    seqs.append(new_seq)
                    seen.add(new_seq)
                dfs(child, new_seq)
            else:
                dfs(child, sequence)

    dfs(root, ())
    return seqs


def construct_node_sequence(path: list[Node], player_id: str) -> tuple:
    sequence = []
    for node, nxt in zip(path, path[1:]):
        if node.data == player_id:
            choice = next(choice for choice, child in node.children.items() if child is nxt)
            sequence.append((node.info_set, choice))
    return tuple(sequence)


def sequence_of(node: Node, player_id: str) -> tuple:
    entries = []
    while node.parent is not None:
        parent = node.parent
        if parent.data == player_id:
            choice = next(choice for choice, child in parent.children.items() if child is node)
            entries.append((parent.info_set, choice))
        node = parent
    entries.reverse()
    return tuple(entries)


def get_terminal_prob(root: Node, sequence: tuple, nature_b_strat: dict) -> float:
    prob = 1.0
    for info_set, choice in sequence:
        prob *= float(nature_b_strat[info_set][choice])
    return prob


def get_num_infosets_local(root: Node, player_id: str) -> int:
    ids = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if node.data == player_id:
            ids.add(node.info_set)
        if node.children is not None:
            stack.extend(node.children.values())
    return len(ids)


def player_constraint_matrix(root: Node, sequencelist: list, player_id: str) -> np.ndarray:
    # Same construction as sequence_form/equilibirum.py, but without importing Pyomo.
    num_infosets = get_num_infosets_local(root, player_id)
    M = np.zeros((1 + num_infosets, len(sequencelist)), dtype=float)
    M[0, 0] = 1.0
    for index, sequence in enumerate(sequencelist):
        if sequence == ((),):
            continue
        infoset = sequence[-1][0]
        parent_sequence = sequence[:-1] if len(sequence) >= 2 else ((),)
        parent_index = sequencelist.index(parent_sequence)
        M[infoset, index] = 1.0
        M[infoset, parent_index] = -1.0
    return M


def realization_to_behavioural(realization: np.ndarray, sequencelist: list, constraint_matrix: np.ndarray) -> dict:
    behavioural: dict[int, dict] = {i: {} for i in range(constraint_matrix.shape[0])}
    for i, row in enumerate(constraint_matrix):
        if i == 0:
            continue
        successors = []
        parent = None
        for j, value in enumerate(row):
            if value == -1:
                parent = j
            elif value == 1:
                successors.append(j)
        if parent is None:
            continue
        for idx in successors:
            child_seq = sequencelist[idx]
            info_set = child_seq[-1][0]
            choice = child_seq[-1][1]
            if abs(realization[parent]) <= 1e-12:
                behavioural[info_set][choice] = 1.0 / len(successors)
            else:
                behavioural[info_set][choice] = float(realization[idx] / realization[parent])
    return behavioural


@dataclass(frozen=True)
class TerminalRecord:
    terminal_index: int
    batter_sequence_index: int
    pitcher_sequence_index: int
    nature_probability: float
    base_utility: float
    terminal_outcome: str


def enum_name(x: Any) -> str:
    """Readable name for Enum actions and ordinary labels."""
    return getattr(x, "name", str(x))


def silence_stdout():
    """Some project functions print large debugging output; silence that here."""
    return contextlib.redirect_stdout(io.StringIO())


def reset_tree_counters() -> None:
    """Reset module-level counters so repeated script runs build the same infosets."""
    from collections import defaultdict
    from itertools import count

    induced_tree.pitcher_next_at_depth = defaultdict(int)
    induced_tree._next_iset = count(start=1)
    induced_tree.batter_counter = count(start=1)
    induced_tree._nature_counter = count(start=1)
    induced_tree.COUNTER = 0


def build_game():
    reset_tree_counters()
    root = Node(data="Pitcher", info_set=1)
    return build_tree(root)


def terminal_outcome(terminal: Node) -> Any:
    parent = terminal.parent
    return next(action for action, child in parent.children.items() if child is terminal)


def collect_terminal_records(root: Node, batter_sequences: list, pitcher_sequences: list) -> list[TerminalRecord]:
    records: list[TerminalRecord] = []
    nature_strategy = behave_strat(root)

    for idx, terminal in enumerate(terminal_nodes(root)):
        path = path_to_node(root, terminal)
        nature_seq = construct_node_sequence(path, "Nature")
        batter_seq = sequence_of(terminal, "Batter")
        pitcher_seq = sequence_of(terminal, "Pitcher")

        outcome = terminal_outcome(terminal)
        new_state, runs = state_dynamics(START_STATE, outcome)
        utility = float(terminal_utility(START_STATE, new_state, runs))
        prob = float(get_terminal_prob(root, nature_seq, nature_strategy))

        records.append(
            TerminalRecord(
                terminal_index=idx,
                batter_sequence_index=batter_sequences.index(batter_seq),
                pitcher_sequence_index=pitcher_sequences.index(pitcher_seq),
                nature_probability=prob,
                base_utility=utility,
                terminal_outcome=enum_name(outcome),
            )
        )
    return records


def payoff_matrix_from_records(
    records: Iterable[TerminalRecord],
    n_batter_sequences: int,
    n_pitcher_sequences: int,
    perturbed_utilities: np.ndarray | None = None,
) -> np.ndarray:
    A = np.zeros((n_batter_sequences, n_pitcher_sequences), dtype=float)
    for rec in records:
        u = rec.base_utility if perturbed_utilities is None else float(perturbed_utilities[rec.terminal_index])
        A[rec.batter_sequence_index, rec.pitcher_sequence_index] += rec.nature_probability * u
    return A


def solve_sequence_form(A: np.ndarray, E: np.ndarray, F: np.ndarray):
    """Solve both sequence-form LPs with scipy.linprog.

    Returns batter realization x, pitcher realization y, game value, and solver statuses.
    A is the batter payoff matrix, so the pitcher minimizes and batter maximizes.
    """
    n_batter, n_pitcher = A.shape
    n_batter_rows = E.shape[0]
    n_pitcher_rows = F.shape[0]

    e = np.zeros(n_batter_rows)
    e[0] = 1.0
    f = np.zeros(n_pitcher_rows)
    f[0] = 1.0

    # Pitcher/minimizer primal: min e^T p s.t. A y - E^T p <= 0, F y = f, y >= 0.
    c_primal = np.r_[np.zeros(n_pitcher), e]
    A_ub_primal = np.hstack([A, -E.T])
    b_ub_primal = np.zeros(n_batter)
    A_eq_primal = np.hstack([F, np.zeros((n_pitcher_rows, n_batter_rows))])
    b_eq_primal = f
    bounds_primal = [(0.0, None)] * n_pitcher + [(None, None)] * n_batter_rows

    primal = linprog(
        c_primal,
        A_ub=A_ub_primal,
        b_ub=b_ub_primal,
        A_eq=A_eq_primal,
        b_eq=b_eq_primal,
        bounds=bounds_primal,
        method="highs",
    )
    if not primal.success:
        raise RuntimeError(f"Pitcher LP failed: {primal.message}")
    y = primal.x[:n_pitcher]
    value = float(primal.fun)

    # Batter/maximizer dual: max -q_0 s.t. (-A)^T x - F^T q <= 0, E x = e, x >= 0.
    # Equivalent minimization: min q_0.
    c_dual = np.r_[np.zeros(n_batter), np.array([1.0] + [0.0] * (n_pitcher_rows - 1))]
    A_ub_dual = np.hstack([-A.T, -F.T])
    b_ub_dual = np.zeros(n_pitcher)
    A_eq_dual = np.hstack([E, np.zeros((n_batter_rows, n_pitcher_rows))])
    b_eq_dual = e
    bounds_dual = [(0.0, None)] * n_batter + [(None, None)] * n_pitcher_rows

    dual = linprog(
        c_dual,
        A_ub=A_ub_dual,
        b_ub=b_ub_dual,
        A_eq=A_eq_dual,
        b_eq=b_eq_dual,
        bounds=bounds_dual,
        method="highs",
    )
    if not dual.success:
        raise RuntimeError(f"Batter LP failed: {dual.message}")
    x = dual.x[:n_batter]
    dual_value = -float(dual.fun)

    if not np.allclose(E @ x, e, atol=1e-7):
        raise RuntimeError("Batter realization plan violates E x = e.")
    if not np.allclose(F @ y, f, atol=1e-7):
        raise RuntimeError("Pitcher realization plan violates F y = f.")
    if abs(value - dual_value) > 1e-6:
        raise RuntimeError(f"Primal/dual value mismatch: primal={value}, dual={dual_value}")

    return x, y, value, primal.message, dual.message


def perturb_utilities(
    base_utilities: np.ndarray,
    rng: np.random.Generator,
    epsilon: float,
    mode: str,
) -> np.ndarray:
    if epsilon == 0:
        return base_utilities.copy()
    noise = rng.normal(loc=0.0, scale=1.0, size=base_utilities.shape)
    if mode == "additive":
        return base_utilities + epsilon * noise
    if mode == "relative":
        return base_utilities * (1.0 + epsilon * noise)
    if mode == "range_scaled":
        scale = float(np.max(base_utilities) - np.min(base_utilities))
        return base_utilities + epsilon * scale * noise
    raise ValueError(f"Unknown perturbation mode: {mode}")


def behavioural_long_table(behavioural: dict, player: str, scenario: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for info_set, probs in sorted(behavioural.items(), key=lambda kv: kv[0]):
        for action, prob in probs.items():
            rows.append(
                {
                    **scenario,
                    "player": player,
                    "info_set": info_set,
                    "action": enum_name(action),
                    "probability": float(prob),
                }
            )
    return rows


def same_action_pairwise_table(prob_rows: list[dict[str, Any]], tolerance: float) -> list[dict[str, Any]]:
    df = pd.DataFrame(prob_rows)
    if df.empty:
        return []
    pair_rows = []
    group_cols = ["scenario_id", "epsilon", "trial", "mode", "player", "action"]
    for keys, group in df.groupby(group_cols, dropna=False):
        group = group.sort_values("info_set")
        for (_, r1), (_, r2) in combinations(group.iterrows(), 2):
            diff = abs(float(r1["probability"]) - float(r2["probability"]))
            pair_rows.append(
                {
                    "scenario_id": keys[0],
                    "epsilon": keys[1],
                    "trial": keys[2],
                    "mode": keys[3],
                    "player": keys[4],
                    "action": keys[5],
                    "info_set_a": int(r1["info_set"]),
                    "info_set_b": int(r2["info_set"]),
                    "probability_a": float(r1["probability"]),
                    "probability_b": float(r2["probability"]),
                    "abs_difference": diff,
                    "different": bool(diff > tolerance),
                }
            )
    return pair_rows


def max_abs_delta(a: dict, b: dict) -> float:
    max_delta = 0.0
    for I in a.keys() | b.keys():
        actions = set(a.get(I, {}).keys()) | set(b.get(I, {}).keys())
        for act in actions:
            max_delta = max(max_delta, abs(float(a.get(I, {}).get(act, 0.0)) - float(b.get(I, {}).get(act, 0.0))))
    return max_delta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eps", nargs="+", type=float, default=[0.0, 0.01, 0.05, 0.10])
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--mode", choices=["additive", "relative", "range_scaled"], default="range_scaled")
    parser.add_argument("--seed", type=int, default=20260521)
    parser.add_argument("--difference-tolerance", type=float, default=1e-6)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "results" / "utility_sensitivity")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    root = build_game()
    batter_sequences = set_sequences2(root, "Batter")
    pitcher_sequences = set_sequences2(root, "Pitcher")

    # The constraint builders print debug info; suppress it so the experiment output is readable.
    with silence_stdout():
        E = player_constraint_matrix(root, batter_sequences, "Batter")
        F = player_constraint_matrix(root, pitcher_sequences, "Pitcher")

    records = collect_terminal_records(root, batter_sequences, pitcher_sequences)
    base_utilities = np.array([r.base_utility for r in records], dtype=float)
    base_A = payoff_matrix_from_records(records, len(batter_sequences), len(pitcher_sequences))
    base_x, base_y, base_value, _, _ = solve_sequence_form(base_A, E, F)
    base_batter_behav = realization_to_behavioural(base_x, batter_sequences, E)
    base_pitcher_behav = realization_to_behavioural(base_y, pitcher_sequences, F)

    summary_rows = []
    prob_rows = []

    scenario_id = 0
    for epsilon in args.eps:
        n_trials = 1 if epsilon == 0 else args.trials
        for trial in range(n_trials):
            scenario_id += 1
            utilities = perturb_utilities(base_utilities, rng, epsilon, args.mode)
            A = payoff_matrix_from_records(records, len(batter_sequences), len(pitcher_sequences), utilities)
            x, y, value, primal_msg, dual_msg = solve_sequence_form(A, E, F)
            batter_behav = realization_to_behavioural(x, batter_sequences, E)
            pitcher_behav = realization_to_behavioural(y, pitcher_sequences, F)

            scenario = {
                "scenario_id": scenario_id,
                "epsilon": epsilon,
                "trial": trial,
                "mode": args.mode,
            }
            prob_rows.extend(behavioural_long_table(batter_behav, "Batter", scenario))
            prob_rows.extend(behavioural_long_table(pitcher_behav, "Pitcher", scenario))

            summary_rows.append(
                {
                    **scenario,
                    "game_value": value,
                    "value_delta_from_baseline": value - base_value,
                    "utility_l2_delta": float(np.linalg.norm(utilities - base_utilities)),
                    "payoff_matrix_l2_delta": float(np.linalg.norm(A - base_A)),
                    "batter_max_behavioural_delta_from_baseline": max_abs_delta(base_batter_behav, batter_behav),
                    "pitcher_max_behavioural_delta_from_baseline": max_abs_delta(base_pitcher_behav, pitcher_behav),
                    "primal_solver_message": primal_msg,
                    "dual_solver_message": dual_msg,
                }
            )

    pair_rows = same_action_pairwise_table(prob_rows, args.difference_tolerance)

    summary_df = pd.DataFrame(summary_rows)
    probs_df = pd.DataFrame(prob_rows)
    pairs_df = pd.DataFrame(pair_rows)

    summary_path = args.output_dir / "sensitivity_summary.csv"
    probs_path = args.output_dir / "behavioural_probabilities.csv"
    pairs_path = args.output_dir / "same_action_differences.csv"

    summary_df.to_csv(summary_path, index=False)
    probs_df.to_csv(probs_path, index=False)
    pairs_df.to_csv(pairs_path, index=False)

    print("Wrote:")
    print(f"  {summary_path}")
    print(f"  {probs_path}")
    print(f"  {pairs_path}")
    print()
    print("Baseline value:", base_value)
    print("Most sensitive perturbation rows:")
    print(
        summary_df.sort_values(
            ["batter_max_behavioural_delta_from_baseline", "pitcher_max_behavioural_delta_from_baseline"],
            ascending=False,
        ).head(10).to_string(index=False)
    )
    print()
    if not pairs_df.empty:
        print("Largest same-action differences across information sets:")
        print(
            pairs_df.sort_values("abs_difference", ascending=False)
            .head(20)
            .to_string(index=False)
        )


if __name__ == "__main__":
    main()