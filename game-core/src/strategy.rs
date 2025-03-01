use crate::card::Card;

pub trait PlayingStrategy {
    fn choose_card(&self, hand: &[Card], valid_moves: &[Card], trick_cards: &[(Card, usize)]) -> Card;
}

#[derive(Clone)]
pub struct RandomStrategy;

impl PlayingStrategy for RandomStrategy {
    fn choose_card(&self, _hand: &[Card], valid_moves: &[Card], _trick_cards: &[(Card, usize)]) -> Card {
        use rand::seq::SliceRandom;
        let mut rng = rand::thread_rng();
        valid_moves.choose(&mut rng).copied().unwrap_or(valid_moves[0])
    }
}

#[derive(Clone)]
pub struct AvoidPointsStrategy;

impl PlayingStrategy for AvoidPointsStrategy {
    fn choose_card(&self, _hand: &[Card], valid_moves: &[Card], trick_cards: &[(Card, usize)]) -> Card {
        // If we're not leading, try to play highest card that won't win
        if !trick_cards.is_empty() {
            let lead_suit = trick_cards[0].0.suit;
            let highest_played = trick_cards
                .iter()
                .filter(|(card, _)| card.suit == lead_suit)
                .map(|(card, _)| card.rank)
                .max()
                .unwrap_or(0);

            // Try to play highest card that won't win
            if let Some(safe_card) = valid_moves
                .iter()
                .filter(|card| card.suit == lead_suit && card.rank < highest_played)
                .max_by_key(|card| card.rank)
            {
                return *safe_card;
            }
        }

        // If leading or can't play safe, play lowest value card
        *valid_moves
            .iter()
            .min_by_key(|card| {
                // Prioritize low hearts and queen of spades
                if card.suit == 'H' || (card.suit == 'S' && card.rank == 12) {
                    card.rank + 13 // Make hearts and queen of spades less desirable
                } else {
                    card.rank
                }
            })
            .unwrap_or(&valid_moves[0])
    }
}

#[derive(Clone)]
pub struct AggressiveStrategy;

impl PlayingStrategy for AggressiveStrategy {
    fn choose_card(&self, _hand: &[Card], valid_moves: &[Card], trick_cards: &[(Card, usize)]) -> Card {
        if trick_cards.is_empty() {
            // If leading, play highest non-penalty card if possible
            if let Some(safe_card) = valid_moves
                .iter()
                .filter(|card| card.suit != 'H' && !(card.suit == 'S' && card.rank == 12))
                .max_by_key(|card| card.rank)
            {
                return *safe_card;
            }
        } else {
            // Try to win the trick if no points are involved
            let has_points = trick_cards.iter().any(|(card, _)| 
                card.suit == 'H' || (card.suit == 'S' && card.rank == 12)
            );
            
            if !has_points {
                if let Some(winning_card) = valid_moves
                    .iter()
                    .filter(|card| card.suit == trick_cards[0].0.suit)
                    .max_by_key(|card| card.rank)
                {
                    return *winning_card;
                }
            }
        }

        // Default to lowest card if no better option
        *valid_moves.iter().min_by_key(|card| card.rank).unwrap_or(&valid_moves[0])
    }
}

#[derive(Clone)]
pub enum Strategy {
    Random(RandomStrategy),
    AvoidPoints(AvoidPointsStrategy),
    Aggressive(AggressiveStrategy),
}

impl PlayingStrategy for Strategy {
    fn choose_card(&self, hand: &[Card], valid_moves: &[Card], trick_cards: &[(Card, usize)]) -> Card {
        match self {
            Strategy::Random(s) => s.choose_card(hand, valid_moves, trick_cards),
            Strategy::AvoidPoints(s) => s.choose_card(hand, valid_moves, trick_cards),
            Strategy::Aggressive(s) => s.choose_card(hand, valid_moves, trick_cards),
        }
    }
}
