# MDPoker Equity Calculator Integration

This integration provides a lightweight solution to use the JavaScript-based equity calculator from your Python MDPoker project, allowing accurate poker equity calculations to be used in your MDP simulation environment.

## How It Works

1. A persistent Node.js Express server directly imports and uses the `calculatePlayerEquity` function from `src/simulation/equity_calculator.mjs` as a REST API endpoint.
2. The Python `PreflopEnv` class uses the `equity_client.py` module to communicate with this service for equity calculations.
3. This provides accurate equity calculations for the reward function and winner determination.

## Benefits

- **Efficiency**: The Express server remains running, eliminating Node.js startup time for each calculation
- **Accuracy**: Uses the powerful JavaScript poker-odds-calculator library for precise equity calculations
- **Modularity**: Clean separation between JavaScript calculation engine and Python simulation
- **Graceful Fallback**: Falls back to simpler equity estimations if the service is unavailable

## Setup Instructions

### Prerequisites

- Node.js (v16+) and npm installed
- Python 3.x with pip
- Your conda environment "Poker" activated

### Installation

1. Run the setup script to install all dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

Alternatively, install the dependencies manually:

```bash
# Node.js dependencies
npm install

# Python dependencies
pip install requests
```

### Starting the Service

Start the Node.js service:

```bash
npm start
```

This will run the server.mjs file, which now directly imports the equity_calculator.mjs module. You should see output indicating the service is running on http://localhost:3000.

### Testing the Integration

The preflop_env.py file includes testing code in its `__main__` section:

```bash
python -m src.simulation.preflop_env
```

This will perform sample equity calculations and display the results of simulated hands.

## Integration with Your MDP Model

The `PreflopEnv` class now automatically uses the equity service if it's available. There are two ways to configure it:

1. Use with Express service (default):
```python
env = PreflopEnv(use_express_service=True)  # Uses Express equity calculator service
```

2. Use with fallback calculator only:
```python
env = PreflopEnv(use_express_service=False, equity_calculator=my_simple_calculator)
```

## API Endpoints

- `GET /health`: Health check endpoint
- `POST /calculate-equity`: Calculate equity between two hands
  - Request body:
    ```json
    {
      "player1Hand": "AcKh",
      "player2Hand": "QsJd",
      "board": "Th9d2c"  // optional
    }
    ```

## Troubleshooting

- If the Express service is not available, the PreflopEnv will automatically fall back to a provided equity calculator or simple estimations.
- Check the Node.js console for any errors if calculations seem incorrect.
- Verify that port 3000 is available for the service to use.

## Project Structure

- `server.mjs`: The Express server that exposes the equity calculation API
- `src/simulation/equity_calculator.mjs`: The core equity calculation function
- `src/simulation/equity_client.py`: Python client that communicates with the Express service
- `src/simulation/preflop_env.py`: The pre-flop MDP environment that uses equity calculations
- `src/simulation/game_rules.py`: Enforces the rules of Texas Hold'em poker

## Configuration

You can modify the service port or host in both `server.mjs` and `src/simulation/equity_client.py` if needed.