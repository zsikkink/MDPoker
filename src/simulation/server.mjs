import express from ‘express’;
import { calculatePlayerEquity } from ‘./equity_calculator.mjs’;

const app = express();
const port = 3000;

// Middleware to parse JSON bodies.
app.use(express.json());

// Endpoint to calculate equity
app.post(’/calculate’, (req, res) => {
const { player1Hand, player2Hand, board } = req.body;
if (!player1Hand || !player2Hand || !board) {
return res
.status(400)
.json({ error: ‘Missing required fields: player1Hand, player2Hand, board’ });
}

try {
const equities = calculatePlayerEquity(player1Hand, player2Hand, board);
res.json(equities);
} catch (error) {
res.status(500).json({ error: error.message });
}
});

// Start the server
app.listen(port, () => {
console.log(Equity Calculator service running on port ${port});
});