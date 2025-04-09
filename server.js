// Import required modules
const express = require('express');
const path = require('path');
const { exec } = require('child_process');

const app = express();
const PORT = 3000;

// Middleware to parse JSON body
app.use(express.json());

// Function to run the equity calculator using Node child process
function calculateEquity(player1Hand, player2Hand, board = '') {
  return new Promise((resolve, reject) => {
    // Create a temporary script that will run the calculation
    const scriptPath = path.join(__dirname, 'temp-calc.js');
    const fs = require('fs');
    
    const tempScript = `
      const { CardGroup, OddsCalculator } = require('poker-odds-calculator');
      
      function calculatePlayerEquity(player1Hand, player2Hand, boardStr) {
        try {
          const player1Cards = CardGroup.fromString('${player1Hand}');
          const player2Cards = CardGroup.fromString('${player2Hand}');
          const board = CardGroup.fromString('${board}');
          
          const result = OddsCalculator.calculate([player1Cards, player2Cards], board);
          
          // Convert returned equities (in percentages) to decimals
          const rawEquity1 = result.equities[0].getEquity() / 100;
          const rawEquity2 = result.equities[1].getEquity() / 100;
          
          let adjustedEquity1 = rawEquity1;
          let adjustedEquity2 = rawEquity2;
          const totalEquity = rawEquity1 + rawEquity2;
          
          if (totalEquity < 1) {
            const tieShare = (1 - totalEquity) / 2;
            adjustedEquity1 += tieShare;
            adjustedEquity2 += tieShare;
          }
          
          console.log(JSON.stringify({ 
            player1Equity: adjustedEquity1, 
            player2Equity: adjustedEquity2 
          }));
        } catch (error) {
          console.error(JSON.stringify({ error: error.message }));
          process.exit(1);
        }
      }
      
      calculatePlayerEquity('${player1Hand}', '${player2Hand}', '${board}');
    `;
    
    fs.writeFileSync(scriptPath, tempScript);
    
    // Execute the script
    exec(`node ${scriptPath}`, (error, stdout, stderr) => {
      // Clean up the temporary script
      try {
        fs.unlinkSync(scriptPath);
      } catch (e) {
        console.error('Error removing temp file:', e);
      }
      
      if (error) {
        console.error(`Execution error: ${error.message}`);
        return reject(error);
      }
      
      if (stderr) {
        console.error(`stderr: ${stderr}`);
        return reject(new Error(stderr));
      }
      
      try {
        const result = JSON.parse(stdout);
        resolve(result);
      } catch (e) {
        console.error('Error parsing result:', e, stdout);
        reject(e);
      }
    });
  });
}

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

    // Calculate equity
    const equity = await calculateEquity(player1Hand, player2Hand, board);
    
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