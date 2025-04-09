#!/bin/bash

# Make sure we're in the right directory
cd "$(dirname "$0")"

echo "Installing Node.js dependencies..."
npm install express
npm install poker-odds-calculator

echo "Installing Python requirements..."
pip install requests

echo "Testing poker-odds-calculator package..."
node test-equity.js

echo "Setup completed!"
echo "To start the equity calculator service, run: npm start"
echo "To test the client, run: python equity_client.py"