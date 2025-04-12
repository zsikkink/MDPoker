import pickle
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# ----- Configuration -----
filename = "hand_action_stats.pkl"  # Make sure this path is correct.
PLAYER = "BTN"                       # Change to "BTN" if desired.
ACTION_TO_SHOW = "call"            # Which action frequency to display.

# Define ranks in the standard order.
ranks = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]

def get_hand_label(i, j):
    """
    Returns the standard starting hand notation:
      - If i == j: pocket pair (e.g., "AA")
      - If i < j: suited (e.g., "AKs")
      - If i > j: offsuit (e.g., "AKo")
    """
    if i == j:
        return ranks[i] + ranks[j]
    elif i < j:
        return ranks[i] + ranks[j] + "s"
    else:
        return ranks[j] + ranks[i] + "o"

def get_action_frequency(hand_stats, hand_key, action_key):
    """
    For a given hand (by its key) in hand_stats, return the fraction of times
    the chosen action was taken.
    """
    if hand_key not in hand_stats:
        return np.nan
    total = sum(hand_stats[hand_key].values())
    if total == 0:
        return np.nan
    return hand_stats[hand_key].get(action_key, 0) / total

# ----- Load Data -----
with open(filename, "rb") as f:
    all_hand_action_stats = pickle.load(f)

if PLAYER not in all_hand_action_stats:
    raise ValueError(f"Player '{PLAYER}' not found in the file.")

hand_stats = all_hand_action_stats[PLAYER]

# ----- Create a 13x13 Matrix of Action Frequencies (then reverse them) -----
size = 13
freq_matrix = np.full((size, size), np.nan)

for i in range(size):
    for j in range(size):
        hand_label = get_hand_label(i, j)
        freq = get_action_frequency(hand_stats, hand_label, ACTION_TO_SHOW)
        # Reverse the value: if the agent raised 0% of the time, we show 100% (1.0),
        # and if it raised 100% of the time, we show 0%.
        if np.isnan(freq):
            freq_matrix[i, j] = np.nan
        else:
            freq_matrix[i, j] = 1 - freq

# ----- Plot the Reversed Heatmap -----
plt.figure(figsize=(9, 7))
ax = sns.heatmap(
    freq_matrix,
    annot=True,         # Annotate each cell with the numeric value.
    fmt=".2f",          # Format to two decimal places.
    cmap="YlOrRd",      # You can change this palette as needed.
    xticklabels=ranks,
    yticklabels=ranks,
    linewidths=0.5,
    linecolor="gray",
    vmin=0.0,
    vmax=1.0
)

ax.set_title(f"{PLAYER} {ACTION_TO_SHOW.capitalize()} Frequency by Starting Hand")
# Optionally invert the y-axis if you prefer.
# ax.invert_yaxis()

plt.tight_layout()
plt.show()