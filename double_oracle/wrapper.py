"""
initial restricted sequences S_P, S_B   # tiny sets (e.g. empty, or first‐pitch actions only)
repeat
    σ_P, σ_B ← solve restricted game via sequence-form LP
    BR_B ← exact best-response sequences for Batter to σ_P      # DP over full tree
    BR_P ← exact best-response sequences for Pitcher to σ_B
    if BR_B ⊆ S_B and BR_P ⊆ S_P:
         break              # convergence
    else:
         S_B ← S_B ∪ BR_B   # enlarge restricted games
         S_P ← S_P ∪ BR_P
until convergence
return (σ_P, σ_B)           # equilibrium of the full game
"""