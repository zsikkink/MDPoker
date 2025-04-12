import pickle
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# 1. Define the rank ordering (top-left corner is A, etc.).
ranks = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]

def get_hand_label(i, j, ranks):
    """
    Returns the standard hand notation:
      - Pocket pairs on the diagonal: e.g. "AA".
      - Suited combos for i < j: e.g. "AKs".
      - Offsuit combos for i > j: e.g. "AKo".
    """
    if i == j:
        return ranks[i] + ranks[j]         # e.g. 'AA'
    elif i < j:
        return ranks[i] + ranks[j] + "s"   # e.g. 'AKs'
    else:
        return ranks[j] + ranks[i] + "o"   # e.g. 'AKo'

# 2. Load the hand_reward_stats dictionary (created by your training script).
with open("hand_reward_stats.pkl", "rb") as f:
    hand_reward_stats = pickle.load(f)

# We’re focusing on the BB statistics here.
bb_stats = hand_reward_stats["BB"]

# 3. Create a 13×13 matrix for the average rewards of each hand.
size = 13
Z = np.full((size, size), np.nan)  # Start with NaN for cells with no data.

# Populate the matrix with average rewards for each starting hand.
for i in range(size):
    for j in range(size):
        hand = get_hand_label(i, j, ranks)
        if hand in bb_stats:
            total_reward = bb_stats[hand]["total_reward"]
            count = bb_stats[hand]["count"]
            if count > 0:
                avg_reward = total_reward / count
                Z[i, j] = avg_reward
            else:
                Z[i, j] = 0.0

# 4. Create a heatmap of the matrix.
plt.figure(figsize=(10, 8))

# annot=True => each cell shows its numeric value (formatted to 2 decimals).
# fmt=".2f" => 2 decimal places.  You can tweak the cmap (e.g., "coolwarm", "viridis", etc.).
ax = sns.heatmap(
    Z,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    xticklabels=ranks,
    yticklabels=ranks,
    linewidths=0.5,
    linecolor="gray"
)

ax.set_title("BB Average Reward Heatmap by Starting Hand")

# By default, row 0 is at the top and row 12 is at the bottom,
# so "AA" will appear in the top-left corner.
# If you'd rather invert the y-axis so "AA" is at the bottom-left,
# you can do: ax.invert_yaxis()

plt.tight_layout()
plt.show()