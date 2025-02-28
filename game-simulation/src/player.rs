use crate::card::Card;
use rand::seq::SliceRandom;
use rand::thread_rng;

pub struct Player {
    pub name: String,
    pub hand: Vec<Card>,
    pub score: u8,
}

impl Player {
    pub fn new(name: &str, hand: Vec<Card>) -> Self {
        Self {
            name: name.to_string(),
            hand,
            score: 0,
        }
    }

    pub fn play_card(&mut self, valid_moves: Vec<Card>) -> Card {
        let chosen_card = if valid_moves.is_empty() {
            // If no valid moves (shouldn't happen), pick a random card from hand
            self.hand.choose(&mut thread_rng()).copied().unwrap_or(self.hand[0])
        } else {
            // Pick a random card from valid moves
            valid_moves.choose(&mut thread_rng()).copied().unwrap_or(valid_moves[0])
        };
        
        self.hand.retain(|c| *c != chosen_card);
        chosen_card
    }
}
