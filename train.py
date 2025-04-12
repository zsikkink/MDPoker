import os
import pickle
import csv
import numpy as np
import matplotlib.pyplot as plt
import time

from environment import PreflopHeadsUpEnv
from utils import get_state, get_state_vector_for_deep_rl, classify_hand
from q_learning_agent import QLearningAgent  # Your Q-learning agent implementation
from mdp_components import PokerAction

# ----- Configuration Parameters -----
NUM_EPISODES = 5000       # Increase number of episodes for convergence.
LOG_INTERVAL = 1000       # Log progress every this many episodes.
EVAL_EPISODES = 50        # Number of evaluation episodes for performance measurement.
PLOT_RESULTS = True       # Generate a plot at the end.
QTABLE_SAVE_PATH = "q_tables.pkl"
TRAINING_LOG_CSV = "training_log.csv"
HAND_ACTION_STATS_SAVE_PATH = "hand_action_stats.pkl"
HAND_REWARD_STATS_SAVE_PATH = "hand_reward_stats.pkl"

# ----- Initialize Environment and Agents -----
env = PreflopHeadsUpEnv()

# Create an agent for each position.
btn_agent = QLearningAgent(alpha=0.1, gamma=0.95, epsilon=1.0, num_bins=10)
bb_agent  = QLearningAgent(alpha=0.1, gamma=0.95, epsilon=1.0, num_bins=10)

# Metrics for monitoring performance.
episode_rewards = []  # List storing (BTN_reward, BB_reward) per episode.
btn_rewards = []      # Per-episode cumulative reward for BTN.
bb_rewards = []       # Per-episode cumulative reward for BB.
eval_rewards = []     # Evaluation-phase rewards (to track greedy performance).

# ----- Set Up Logging for Hand Action Statistics and Hand Reward Statistics -----
# Separate dictionaries keyed by starting hand classification for each player.
hand_action_stats = {"BTN": {}, "BB": {}}
# For rewards, we will store cumulative reward and count per hand.
hand_reward_stats = {"BTN": {}, "BB": {}}

def update_hand_stats(player, hand, action: PokerAction):
    """
    Update action counts for a given starting hand.
    - player: "BTN" or "BB"
    - hand: Raw 4-character hand string (e.g., "AsAh").
    - action: The selected PokerAction.
    """
    classified, _, _, _, _ = classify_hand(hand)
    if classified not in hand_action_stats[player]:
        hand_action_stats[player][classified] = {"fold": 0, "call": 0, "check": 0, "raise": 0}
    hand_action_stats[player][classified][action.action_type.value] += 1

def update_hand_reward_stats(player, hand, reward_val):
    """
    Update reward statistics for a given starting hand.
    - player: "BTN" or "BB"
    - hand: Raw 4-character hand string.
    - reward_val: Final reward earned in that episode.
    """
    classified, _, _, _, _ = classify_hand(hand)
    if classified not in hand_reward_stats[player]:
        hand_reward_stats[player][classified] = {"total_reward": 0.0, "count": 0}
    hand_reward_stats[player][classified]["total_reward"] += reward_val
    hand_reward_stats[player][classified]["count"] += 1

# ----- Prepare Training Log CSV Header -----
if not os.path.exists(TRAINING_LOG_CSV):
    with open(TRAINING_LOG_CSV, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Episode", "BTN Reward", "BB Reward", "Eval BTN Reward", "Eval BB Reward", "Epsilon_BTN", "Epsilon_BB"])

# ----- Training Loop -----
start_time = time.time()
for episode in range(1, NUM_EPISODES + 1):
    env.reset()
    done = False
    episode_btn_reward = 0.0
    episode_bb_reward = 0.0

    # The dealt hands remain fixed for the episode.
    btn_hand = env.hands[0]
    bb_hand = env.hands[1]

    # Run the episode.
    while not done:
        current_player = env.current_turn  # "BTN" or "BB"
        if current_player == "BTN":
            agent = btn_agent
            player_hand = btn_hand
        else:
            agent = bb_agent
            player_hand = bb_hand

        # Obtain the current state vector.
        state = get_state(
            current_player,
            player_hand,
            {p: env.players[p]["stack"] for p in env.players},
            env.contributions,
            env.betting_history,
            is_first_action=(len(env.betting_history) == 0)
        )
        state_vector = get_state_vector_for_deep_rl(state)

        # Retrieve legal actions.
        legal_actions = env.get_current_legal_actions()

        # Choose an action using the epsilon-greedy policy.
        action = agent.choose_action(state_vector, legal_actions)

        # Update hand-action statistics.
        update_hand_stats(current_player, player_hand, action)

        # Execute the action.
        (reward_BTN, reward_BB), info, done = env.step(action)
        reward = reward_BTN if current_player == "BTN" else reward_BB

        # Accumulate episode reward for the acting player.
        if current_player == "BTN":
            episode_btn_reward += reward
        else:
            episode_bb_reward += reward

        # Get next state info if the episode is not finished.
        if not done:
            next_player = env.current_turn
            next_hand = btn_hand if next_player == "BTN" else bb_hand
            next_state = get_state(
                next_player,
                next_hand,
                {p: env.players[p]["stack"] for p in env.players},
                env.contributions,
                env.betting_history,
                is_first_action=(len(env.betting_history) == 0)
            )
            next_state_vector = get_state_vector_for_deep_rl(next_state)
            legal_actions_next = env.get_current_legal_actions()
        else:
            next_state_vector = None
            legal_actions_next = []

        # Update Q-table.
        agent.update(state_vector, action, reward, next_state_vector, done, legal_actions_next)

    # End of episode: record the final rewards.
    episode_rewards.append((episode_btn_reward, episode_bb_reward))
    btn_rewards.append(episode_btn_reward)
    bb_rewards.append(episode_bb_reward)

    # Update hand reward statistics per player (each hand is dealt once per episode).
    update_hand_reward_stats("BTN", btn_hand, episode_btn_reward)
    update_hand_reward_stats("BB", bb_hand, episode_bb_reward)

    # Decay exploration rates.
    btn_agent.decay_epsilon()
    bb_agent.decay_epsilon()

    # Log progress every LOG_INTERVAL episodes.
    if episode % LOG_INTERVAL == 0:
        avg_btn = np.mean(btn_rewards[-LOG_INTERVAL:])
        avg_bb = np.mean(bb_rewards[-LOG_INTERVAL:])
        elapsed = time.time() - start_time
        print(f"Episode {episode}: Avg BTN Reward = {avg_btn:.2f}, Avg BB Reward = {avg_bb:.2f}, Time Elapsed = {elapsed:.1f}s, Epsilon = {btn_agent.epsilon:.3f}")
        
        # Evaluation phase (with ε=0, no exploration).
        eval_btn_rewards = []
        eval_bb_rewards = []
        original_btn_epsilon = btn_agent.epsilon
        original_bb_epsilon = bb_agent.epsilon
        btn_agent.epsilon = 0.0
        bb_agent.epsilon = 0.0
        for _ in range(EVAL_EPISODES):
            env.reset()
            done_eval = False
            eval_reward_BTN = 0.0
            eval_reward_BB = 0.0
            while not done_eval:
                current_player = env.current_turn
                if current_player == "BTN":
                    eval_agent = btn_agent
                    eval_hand = env.hands[0]
                else:
                    eval_agent = bb_agent
                    eval_hand = env.hands[1]
                eval_state = get_state(
                    current_player,
                    eval_hand,
                    {p: env.players[p]["stack"] for p in env.players},
                    env.contributions,
                    env.betting_history,
                    is_first_action=(len(env.betting_history) == 0)
                )
                eval_state_vector = get_state_vector_for_deep_rl(eval_state)
                eval_legal_actions = env.get_current_legal_actions()
                eval_action = eval_agent.choose_action(eval_state_vector, eval_legal_actions)
                (eval_r_BTN, eval_r_BB), _, done_eval = env.step(eval_action)
                if current_player == "BTN":
                    eval_reward_BTN += eval_r_BTN
                else:
                    eval_reward_BB += eval_r_BB
            eval_btn_rewards.append(eval_reward_BTN)
            eval_bb_rewards.append(eval_reward_BB)
        avg_eval_btn = np.mean(eval_btn_rewards)
        avg_eval_bb = np.mean(eval_bb_rewards)
        print(f"Evaluation: Avg BTN Reward = {avg_eval_btn:.2f}, Avg BB Reward = {avg_eval_bb:.2f}")
        with open(TRAINING_LOG_CSV, mode='a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([episode, avg_btn, avg_bb, avg_eval_btn, avg_eval_bb, btn_agent.epsilon, bb_agent.epsilon])
        # Restore exploration rates.
        btn_agent.epsilon = original_btn_epsilon
        bb_agent.epsilon = original_bb_epsilon

# ----- Save Final Q-Tables, Hand-Action Stats, and Hand-Reward Stats -----
q_tables = {"BTN": btn_agent.Q, "BB": bb_agent.Q}
with open(QTABLE_SAVE_PATH, "wb") as f:
    pickle.dump(q_tables, f)
print("\nQ-tables saved to", QTABLE_SAVE_PATH)

with open(HAND_ACTION_STATS_SAVE_PATH, "wb") as f:
    pickle.dump(hand_action_stats, f)
print("Hand action stats saved to", HAND_ACTION_STATS_SAVE_PATH)

with open(HAND_REWARD_STATS_SAVE_PATH, "wb") as f:
    pickle.dump(hand_reward_stats, f)
print("Hand reward stats saved to", HAND_REWARD_STATS_SAVE_PATH)

# ----- Print Final Training Statistics to Console -----
print("\n========= Final Training Statistics =========")
print(f"Total Episodes: {NUM_EPISODES}")
print(f"Final BTN Epsilon: {btn_agent.epsilon:.4f}")
print(f"Final BB Epsilon: {bb_agent.epsilon:.4f}")
print(f"Overall Average BTN Reward: {np.mean(btn_rewards):.2f}")
print(f"Overall Average BB Reward: {np.mean(bb_rewards):.2f}")

# ----- Print Q-Table Summaries -----
def print_q_table_summary(q_table, player_name, sample_count=5):
    print(f"\n--- {player_name} Q-Table Summary ---")
    print(f"Total state-action pairs: {len(q_table)}")
    print("Sample entries:")
    count = 0
    for key, q_value in q_table.items():
        print(f"State: {key[0]}, Action: {key[1]}, Q-value: {q_value:.3f}")
        count += 1
        if count >= sample_count:
            break

print_q_table_summary(btn_agent.Q, "BTN")
print_q_table_summary(bb_agent.Q, "BB")

# ----- Print Hand Action Statistics -----
def print_hand_action_stats(stats, player_name, max_entries=10):
    print(f"\n--- {player_name} Hand Action Statistics ---")
    sorted_hands = sorted(stats.items(), key=lambda x: sum(x[1].values()), reverse=True)
    for i, (hand, actions) in enumerate(sorted_hands):
        total_actions = sum(actions.values())
        print(f"Hand: {hand}, Total Actions: {total_actions}, Details: {actions}")
        if i + 1 >= max_entries:
            break

print_hand_action_stats(hand_action_stats["BTN"], "BTN")
print_hand_action_stats(hand_action_stats["BB"], "BB")

# ----- Print Average Reward per Starting Hand -----
def print_hand_reward_stats(stats, player_name):
    print(f"\n--- {player_name} Average Reward by Starting Hand ---")
    # Sort by highest average reward.
    for hand, data in sorted(stats.items(), key=lambda x: x[1]["total_reward"] / x[1]["count"], reverse=True):
        avg_reward = data["total_reward"] / data["count"]
        print(f"Hand: {hand}, Average Reward = {avg_reward:.2f} (Count = {data['count']})")

print_hand_reward_stats(hand_reward_stats["BTN"], "BTN")
print_hand_reward_stats(hand_reward_stats["BB"], "BB")

# ----- Optionally Plot Training Performance -----
if PLOT_RESULTS:
    episodes = np.arange(LOG_INTERVAL, NUM_EPISODES + 1, LOG_INTERVAL)
    avg_btn_rewards = [np.mean([r[0] for r in episode_rewards[max(0, i - LOG_INTERVAL):i]]) for i in episodes]
    avg_bb_rewards = [np.mean([r[1] for r in episode_rewards[max(0, i - LOG_INTERVAL):i]]) for i in episodes]
    plt.figure()
    plt.plot(episodes, avg_btn_rewards, label="BTN Avg Reward")
    plt.plot(episodes, avg_bb_rewards, label="BB Avg Reward")
    plt.xlabel("Episode")
    plt.ylabel("Average Reward")
    plt.title("Training Performance")
    plt.legend()
    plt.show()

print("\nTraining completed.")