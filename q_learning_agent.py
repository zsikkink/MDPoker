import numpy as np
from mdp_components import PokerAction, ActionType

class QLearningAgent:
    def __init__(self, alpha=0.1, gamma=0.95, epsilon=1.0, num_bins=10):
        self.alpha = alpha          # Learning rate
        self.gamma = gamma          # Discount factor
        self.epsilon = epsilon      # Exploration rate
        self.num_bins = num_bins    # Number of bins per feature for discretization
        self.Q = {}                 # The Q-table. Keys will be tuples of (state, action)

    def discretize_state(self, state_vector):
        """
        Discretizes a continuous state vector by quantizing each element.
        For example, if each feature is normalized between 0 and 1,
        multiplying by num_bins and converting to int gives discrete bins.
        """
        discrete_state = tuple(int(min(max(v, 0), 1) * self.num_bins) for v in state_vector)
        return discrete_state

    def action_to_key(self, action: PokerAction):
        """
        Converts a PokerAction to a hashable key.
        If the action is a raise, include the raise amount in the key.
        """
        if action.action_type == ActionType.RAISE:
            return (action.action_type.value, action.raise_amount)
        else:
            return (action.action_type.value,)

    def choose_action(self, state_vector, legal_actions):
        """
        Uses an epsilon-greedy policy to choose between exploring a random action
        or exploiting the current Q-table.
        """
        state = self.discretize_state(state_vector)
        if np.random.rand() < self.epsilon:
            # Explore: select a random legal action.
            action = np.random.choice(legal_actions)
        else:
            # Exploit: select the action with highest Q-value.
            best_action = None
            best_q = -float("inf")
            for action in legal_actions:
                key = (state, self.action_to_key(action))
                q_value = self.Q.get(key, 0.0)
                if q_value > best_q:
                    best_q = q_value
                    best_action = action
            # Fall back to random if no action has been seen yet.
            if best_action is None:
                best_action = np.random.choice(legal_actions)
            action = best_action
        return action

    def update(self, state_vector, action, reward, next_state_vector, done, legal_actions_next):
        """
        Update Q-values using the standard Q-learning update rule:
          Q(s,a) <- Q(s,a) + alpha * (reward + gamma * max_a' Q(s', a') - Q(s,a))
        """
        state = self.discretize_state(state_vector)
        action_key = self.action_to_key(action)
        current_q = self.Q.get((state, action_key), 0.0)
        
        # Determine the target value.
        if done or next_state_vector is None:
            target = reward
        else:
            next_state = self.discretize_state(next_state_vector)
            max_q_next = 0.0
            for next_action in legal_actions_next:
                next_action_key = self.action_to_key(next_action)
                max_q_next = max(max_q_next, self.Q.get((next_state, next_action_key), 0.0))
            target = reward + self.gamma * max_q_next
        
        # Q-learning update.
        new_q = current_q + self.alpha * (target - current_q)
        self.Q[(state, action_key)] = new_q

    def decay_epsilon(self, decay_rate=0.99, min_epsilon=0.01):
        """Decays the exploration rate (epsilon) over episodes."""
        self.epsilon = max(min_epsilon, self.epsilon * decay_rate)