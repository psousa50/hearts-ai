use crate::card::Card;
use crate::strategy::{Strategy, PlayingStrategy};

pub struct Player {
    pub name: String,
    pub hand: Vec<Card>,
    pub score: u8,
    strategy: Strategy,
}

impl Player {
    pub fn with_strategy(name: &str, hand: Vec<Card>, strategy: Strategy) -> Self {
        Self {
            name: name.to_string(),
            hand,
            score: 0,
            strategy,
        }
    }

    pub fn play_card(&mut self, valid_moves: Vec<Card>, trick_cards: &[(Card, usize)]) -> Card {
        let chosen_card = self.strategy.choose_card(&self.hand, &valid_moves, trick_cards);
        self.hand.retain(|c| *c != chosen_card);
        chosen_card
    }
}
