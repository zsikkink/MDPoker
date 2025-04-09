# Poker Equity Calculator Integration

This integration provides a lightweight solution to use the JavaScript-based equity calculator from your Python MDPoker project without the overhead of starting a new Node.js process for each calculation.

## How It Works

1. A persistent Node.js Express server exposes the `calculatePlayerEquity` function from `equity_calculator.mjs` as a REST API endpoint.
2. A Python client sends HTTP requests to this service when equity calculations are needed.
3. The Node.js service performs the calculations using the JavaScript library and returns the results.

## Benefits

- **Efficiency**: Eliminates Node.js startup time for each calculation by keeping the service running
- **Simplicity**: Clean separation between JavaScript and Python code
- **Performance**: Local HTTP requests have minimal overhead compared to process spawning

## Setup Instructions

### Prerequisites

- Node.js (v14+) and npm installed
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
npm install express poker-odds-calculator

# Python dependencies
pip install requests
```

2. Make sure your `package.json` includes `"type": "module"` to enable ES modules.

### Starting the Service

Start the Node.js service:

```bash
node server.js
```

You should see output indicating the service is running on http://localhost:3000.

### Testing the Integration

Run the Python client test script:

```bash
python equity_client.py
```

This will perform sample equity calculations and display the results.

## Integration with Your Python Code

To use the equity calculator in your existing Python code:

1. Import the client:

```python
from equity_client import EquityCalculator
```

2. Create an instance of the calculator:

```python
calculator = EquityCalculator()
```

3. Calculate equity:

```python
# Preflop equity (no board)
equity = calculator.calculate_equity("AcKh", "QsJd")

# Equity with community cards
equity = calculator.calculate_equity("AcKh", "QsJd", "Th9d2c")
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

- If you encounter connection errors, make sure the Node.js service is running.
- Check for errors in the Node.js service console output.
- Verify that the port (default: 3000) is not being used by another application.

## Advanced Configuration

You can modify the service port or host in both the Node.js server (`server.js`) and the Python client (`equity_client.py`).