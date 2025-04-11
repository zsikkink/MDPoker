import express from 'express';
import { CardGroup, OddsCalculator } from 'poker-odds-calculator';

const app = express();
const port = 3000;

// Middleware to parse JSON bodies
app.use(express.json());

// Define the route to calculate poker equity
app.post('/calculate-equity', (req, res) => {
  const { player1Hand, player2Hand } = req.body;
  
  // Validate that both hands are provided
  if (!player1Hand || !player2Hand) {
    return res.status(400).json({ error: 'Missing player1Hand or player2Hand in request body' });
  }

  try {
    // Create CardGroup objects from the provided hands
    const player1Cards = CardGroup.fromString(player1Hand);
    const player2Cards = CardGroup.fromString(player2Hand);

    // Calculate equities for both players
    const result = OddsCalculator.calculate([player1Cards, player2Cards]);

    // Extract the equity values.
    // Note: getEquity() is assumed to return a numeric value as a string.
    const player1Equity = parseFloat(result.equities[0].getEquity());
    const player2Equity = parseFloat(result.equities[1].getEquity());

    // Return the results as JSON
    return res.json({
      player1Equity,
      player2Equity
    });
  } catch (error) {
    console.error('Error calculating equity:', error);
    return res.status(500).json({ error: 'Error calculating equity' });
  }
});

// Start the server
app.listen(port, () => {
  console.log(`Equity calculator service listening on http://localhost:${port}`);
});