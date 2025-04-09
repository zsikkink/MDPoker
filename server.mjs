// Updated server.mjs with direct import of equity_calculator.mjs
import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { calculatePlayerEquity } from './src/simulation/equity_calculator.mjs';

// Get current directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;

// Middleware to parse JSON body
app.use(express.json());

// API endpoint to calculate equity
app.post('/calculate-equity', async (req, res) => {
  try {
    const { player1Hand, player2Hand, board = '' } = req.body;
    
    // Validate input
    if (!player1Hand || !player2Hand) {
      return res.status(400).json({ 
        error: 'Missing required parameters. Please provide player1Hand and player2Hand.' 
      });
    }

    // Calculate equity using imported function
    const equity = calculatePlayerEquity(player1Hand, player2Hand, board);
    
    // Return the result
    return res.json({
      player1Hand,
      player2Hand,
      board: board || 'None',
      player1Equity: equity.player1Equity,
      player2Equity: equity.player2Equity
    });
  } catch (error) {
    console.error('Error calculating equity:', error);
    return res.status(500).json({ 
      error: 'Error calculating equity', 
      message: error.message 
    });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', message: 'Equity calculator service is running' });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Equity calculator service running on http://localhost:${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Calculate equity endpoint: http://localhost:${PORT}/calculate-equity (POST)`);
});
