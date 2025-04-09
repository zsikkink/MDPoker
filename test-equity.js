// Test script for poker-odds-calculator
const { CardGroup, OddsCalculator } = require('poker-odds-calculator');

function testCalculator() {
  console.log("Testing poker-odds-calculator...");
  
  try {
    // Create card groups
    const player1Cards = CardGroup.fromString('AcKh');
    const player2Cards = CardGroup.fromString('QsJd');
    const board = CardGroup.fromString('');
    
    console.log("Successfully created card groups");
    
    // Calculate odds
    const result = OddsCalculator.calculate([player1Cards, player2Cards], board);
    
    console.log("Calculation successful!");
    console.log("Player 1 equity:", result.equities[0].getEquity() + "%");
    console.log("Player 2 equity:", result.equities[1].getEquity() + "%");
  } catch (error) {
    console.error("Error testing calculator:", error);
  }
}

testCalculator();