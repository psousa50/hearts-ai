use crate::card::Card;

pub trait PlayingStrategy {
    fn choose_card(&self, hand: &[Card], valid_moves: &[Card]) -> Card;
}

#[derive(Clone)]
pub struct RandomStrategy;

impl PlayingStrategy for RandomStrategy {
    fn choose_card(&self, _hand: &[Card], valid_moves: &[Card]) -> Card {
        use rand::seq::SliceRandom;
        let mut rng = rand::thread_rng();
        valid_moves.choose(&mut rng).copied().unwrap_or(valid_moves[0])
    }
}

#[derive(Clone)]
pub struct AvoidPointsStrategy;

impl PlayingStrategy for AvoidPointsStrategy {
    fn choose_card(&self, _hand: &[Card], valid_moves: &[Card]) -> Card {
        // Play lowest value card
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
            .unwrap()
    }
}

#[derive(Clone)]
pub struct AggressiveStrategy;

impl PlayingStrategy for AggressiveStrategy {
    fn choose_card(&self, _hand: &[Card], valid_moves: &[Card]) -> Card {
        // Play highest value card
        *valid_moves
            .iter()
            .max_by_key(|card| {
                // Prioritize hearts and queen of spades
                if card.suit == 'H' || (card.suit == 'S' && card.rank == 12) {
                    card.rank + 13 // Make hearts and queen of spades more desirable
                } else {
                    card.rank
                }
            })
            .unwrap()
    }
}

#[derive(Clone)]
pub enum Strategy {
    Random(RandomStrategy),
    AvoidPoints(AvoidPointsStrategy),
    Aggressive(AggressiveStrategy),
}

impl Strategy {
    pub fn choose_card(&self, hand: &[Card], valid_moves: &[Card]) -> Card {
        match self {
            Strategy::Random(s) => s.choose_card(hand, valid_moves),
            Strategy::AvoidPoints(s) => s.choose_card(hand, valid_moves),
            Strategy::Aggressive(s) => s.choose_card(hand, valid_moves),
        }
    }
}
