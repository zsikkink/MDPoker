# MDPoker JavaScript Equity Calculator Integration Guide

This guide explains how to integrate the JavaScript-based equity calculator with your Python MDPoker project to enhance the accuracy of your Markov Decision Process (MDP) model.

## Background

Your MDPoker project models poker as an MDP with a reward function that uses equity calculations. The JavaScript equity calculator provides more accurate equity calculations than what might be achievable with pure Python implementations, especially for preflop scenarios.

## Architecture

The integration uses a client-server architecture:

1. **Node.js Express Server**: A persistent server that directly imports the `equity_calculator.mjs` module to expose the JavaScript equity calculator as an API endpoint
2. **Python Equity Client**: A lightweight client that communicates with the server via HTTP requests
3. **PreflopEnv Integration**: The preflop environment directly uses the equity client for accurate calculations

## Setting Up the Integration

### 1. Install the Required Dependencies

Run the setup script to install all required dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

### 2. Start the Node.js Service

Start the equity calculator service:

```bash
npm start
```

Keep this service running in the background while you use your MDPoker project.

## Using the PreflopEnv Environment

The `PreflopEnv` class now has built-in support for using the equity calculator service:

```python
from src.simulation.preflop_env import PreflopEnv

# Create an environment with the equity service enabled (default)
env = PreflopEnv(use_express_service=True)

# Or use without the service
env = PreflopEnv(use_express_service=False, equity_calculator=my_custom_calculator)
```

The environment will automatically:

1. Try to connect to the equity calculation service
2. Use it for accurate equity calculations if available
3. Fall back to a provided calculator or simple estimation if the service is unavailable

## How the Integration Works

### 1. Equity Calculation Flow

When the `PreflopEnv` needs to calculate equity (for rewards or winner determination):

1. It sends the hole cards to the equity client
2. The client formats the request and sends it to the Express server
3. The server uses the imported `calculatePlayerEquity` function to calculate accurate equity
4. The result is returned to the Python environment

### 2. Fallback Mechanism

If the Express service is unavailable or encounters an error:

1. The equity client will log a warning
2. The client will attempt to use a provided custom equity calculator
3. If no custom calculator is available, it will use a simple estimation

## Testing the Integration

You can test the integration by running the preflop environment directly:

```bash
python -m src.simulation.preflop_env
```

This will test both modes (with and without the Express service).

## Customization

### Modifying the Equity Calculation

If you need to modify the equity calculation algorithm:

1. Update `src/simulation/equity_calculator.mjs` to implement your algorithm
2. The Express server automatically uses the updated implementation

### Using in Custom Environments

To use the equity calculator in your own custom environments:

```python
from src.simulation.equity_client import EquityClient

class MyCustomEnvironment:
    def __init__(self):
        self.equity_client = EquityClient()
        
    def calculate_hand_strength(self, hand1, hand2, board=None):
        equity1, equity2 = self.equity_client.calculate_equity(hand1, hand2, board)
        return equity1  # Return player 1's equity
```