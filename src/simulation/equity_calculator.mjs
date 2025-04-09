import { CardGroup, OddsCalculator } from 'poker-odds-calculator';

export function calculatePlayerEquity(player1Hand, player2Hand, boardStr) {
const player1Cards = CardGroup.fromString(player1Hand);
const player2Cards = CardGroup.fromString(player2Hand);
const board = CardGroup.fromString(boardStr);

const result = OddsCalculator.calculate([player1Cards, player2Cards], board);

// Convert returned equities (in percentages) to decimals.
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

return { player1Equity: adjustedEquity1, player2Equity: adjustedEquity2 };
}