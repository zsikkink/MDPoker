import { CardGroup, OddsCalculator } from 'poker-odds-calculator';

const player1Cards = CardGroup.fromString('JhJs');
const player2Cards = CardGroup.fromString('JdQd');
const board = CardGroup.fromString('7d9dTs');

const result = OddsCalculator.calculate([player1Cards, player2Cards], board);

// Convert returned equities (given in percentages) to decimals.
const rawEquity1 = result.equities[0].getEquity() / 100;
const rawEquity2 = result.equities[1].getEquity() / 100;

// If there is a tie portion, then the sum of rawEquity1 and rawEquity2 will be less than 1.
// Calculate the remainder and split it evenly between both players.
let adjustedEquity1 = rawEquity1;
let adjustedEquity2 = rawEquity2;
const totalEquity = rawEquity1 + rawEquity2;

if (totalEquity < 1) {
  const tieShare = (1 - totalEquity) / 2;
  adjustedEquity1 += tieShare;
  adjustedEquity2 += tieShare;
}

console.log(`Player #1 - ${player1Cards} - ${adjustedEquity1}`);
console.log(`Player #2 - ${player2Cards} - ${adjustedEquity2}`);