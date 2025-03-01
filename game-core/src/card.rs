use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
pub struct Card {
    pub suit: char,
    pub rank: u8,
}

impl Card {
    pub fn new(suit: char, rank: u8) -> Self {
        Self { suit, rank }
    }

    pub fn is_penalty(&self) -> bool {
        self.suit == 'H' || (self.suit == 'S' && self.rank == 12) // Queen of Spades
    }

    pub fn score(&self) -> u8 {
        if self.suit == 'H' {
            1
        } else if self.suit == 'S' && self.rank == 12 {
            13
        } else {
            0
        }
    }
}
