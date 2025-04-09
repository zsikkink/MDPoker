# MDPoker JavaScript Equity Calculator Integration Guide

This guide explains how to integrate the JavaScript-based equity calculator with your Python MDPoker project to enhance the accuracy of your Markov Decision Process (MDP) model.

## Background

Your MDPoker project models poker as an MDP with a reward function that uses equity calculations. The JavaScript equity calculator provides more accurate equity calculations than what might be achievable with pure Python implementations, especially for preflop scenarios.

## Architecture

The integration uses a client-server architecture:

1. **Node.js Server**: A persistent Express server that exposes the JavaScript equity calculator as an API endpoint
2. **Python Client**: A lightweight client that communicates with the server via HTTP requests
3. **Integration Layer**: Python code that bridges the MDPoker project with the equity calculator client

## Setting Up the Integration

### 1. Install the Required Files

Place these files in your MDPoker project directory:

- `server.js`: The Express server that exposes the equity calculator API
- `equity_client.py`: The Python client for the equity calculator service 
- `setup.sh`: Script to install dependencies
- `mdpoker_integration.py`: Example of how to integrate with MDPoker

### 2. Install Dependencies

Run the setup script to install all required dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

### 3. Start the Node.js Service

Start the equity calculator service:

```bash
node server.js
```

Keep this service running in the background while you use your MDPoker project.

## Integrating with Your MDP Model

### 1. Update Your Reward Function

The reward function in your MDP model can now use the JavaScript equity calculator for more accurate equity calculations. Here's how to modify your code:

1. Import the HybridEquityEstimator:

```python
from mdpoker_integration import HybridEquityEstimator
```

2. Initialize the estimator:

```python
equity_estimator = HybridEquityEstimator()
```

3. Update your reward function to use the estimator:

```python
def calculate_reward(self, state, action, next_state):
    # For transitions to terminal states (when someone folds)
    if next_state.is_terminal():
        if next_state.winner == self.player_id:
            return next_state.pot_size
        else:
            return -next_state.pot_size
    
    # For transitions to the flop (both players continue)
    elif next_state.betting_round == 'flop':
        # Get hole cards for both players
        player_hole_cards = state.hole_cards[self.player_id]
        opponent_hole_cards = state.hole_cards[self.opponent_id]
        
        # Calculate equity using the JavaScript service
        player_equity, opponent_equity = equity_estimator.calculate_preflop_equity(
            player_hole_cards, opponent_hole_cards
        )
        
        # Apply the reward formula: R_i = (2*e_i - 1) * P
        return (2 * player_equity - 1) * next_state.pot_size
    
    # For other transitions (e.g., raising but still in preflop)
    else:
        return 0  # No immediate reward
```

### 2. Updating Your State Definition

If your state definition includes equity calculations, you can update those as well:

```python
def update_state_features(self, state):
    # Calculate current equity and add it to the state features
    if hasattr(state, 'opponent_hole_cards') and state.opponent_hole_cards:
        # If opponent cards are known (e.g., in training with perfect information)
        player_equity, _ = self.equity_estimator.calculate_preflop_equity(
            state.hole_cards, state.opponent_hole_cards
        )
    else:
        # If opponent cards are unknown, use average equity against a range
        player_equity = self.calculate_equity_vs_range(state.hole_cards, state.opponent_range)
    
    # Add equity to state features
    state.features['equity'] = player_equity
    
    return state
```

### 3. Creating a Custom MDP Environment

You can create a custom MDP environment that uses the JavaScript equity calculator:

```python
class EquityEnhancedMDP:
    def __init__(self):
        self.equity_estimator = HybridEquityEstimator()
        # Other initialization code
    
    def step(self, state, action):
        # Determine the next state based on the current state and action
        next_state = self.transition(state, action)
        
        # Calculate reward using equity
        reward = self.calculate_reward(state, action, next_state)
        
        # Check if the next state is terminal
        done = next_state.is_terminal()
        
        return next_state, reward, done
    
    # Implement other MDP methods...
```

## Performance Considerations

- **Service Startup**: Start the Node.js service before running your Python code to avoid connection errors
- **Connection Pooling**: The Python client maintains a persistent connection to the Node.js service
- **Error Handling**: The client includes fallback mechanisms if the service is unavailable

## Additional Use Cases

The integration can be extended for:

1. **Training Data Generation**: Generate training data with accurate equity calculations
2. **Strategy Evaluation**: Evaluate different strategies against each other
3. **Monte Carlo Simulations**: Run Monte Carlo simulations with accurate equity estimation

## Troubleshooting

If you encounter issues:

1. Ensure the Node.js service is running
2. Check for error messages in both the Node.js console and Python output
3. Verify that the server and client are configured to use the same port
4. Check that all dependencies are installed correctly

## Example Integration

See `mdpoker_integration.py` for a complete example of how to integrate the JavaScript equity calculator with your MDPoker project.