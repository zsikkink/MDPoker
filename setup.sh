#!/bin/bash

# Make sure we're in the right directory
cd "$(dirname "$0")"

echo "Installing Node.js dependencies..."
npm install

echo "Installing Python requirements..."
pip install requests treys

echo "Testing Express service..."
node -e "const { CardGroup, OddsCalculator } = require('poker-odds-calculator'); console.log('Poker calculator ready!');"

echo "Setup completed!"
echo "To start the equity calculator service, run: npm start"
echo "To test the client, run: python -m src.simulation.preflop_env"