use crate::player::PlayerInfo;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Card {
    pub suit: char,
    pub rank: u8,
}

impl Card {
    pub fn new(suit: char, rank: u8) -> Self {
        Self { suit, rank }
    }

    pub fn is_penalty(&self) -> bool {
        self.is_hearts() || self.is_queen_of_spades()
    }

    pub fn score(&self) -> u8 {
        if self.is_hearts() {
            1
        } else if self.is_queen_of_spades() {
            13
        } else {
            0
        }
    }

    pub fn is_hearts(&self) -> bool {
        self.suit == 'H'
    }

    pub fn is_queen_of_spades(&self) -> bool {
        self.suit == 'S' && self.rank == 12
    }

    pub fn is_two_of_clubs(&self) -> bool {
        self.suit == 'C' && self.rank == 2
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompletedTrick {
    pub cards: Vec<Card>,
    pub winner: usize,
    pub points: u8,
    pub first_player_index: usize,
}

impl CompletedTrick {
    pub fn lead_suit(&self) -> char {
        self.first_card().suit
    }

    pub fn first_card(&self) -> Card {
        self.cards[self.first_player_index]
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trick {
    pub cards: Vec<Option<Card>>,
    pub first_player_index: usize,
}

impl Trick {
    pub fn new() -> Self {
        Self {
            cards: vec![None; 4],
            first_player_index: 0,
        }
    }

    pub fn add_card(&mut self, card: Card, player_index: usize) {
        self.cards[player_index] = Some(card);
    }

    pub fn first_card(&self) -> Option<Card> {
        self.cards.get(self.first_player_index).cloned().unwrap()
    }

    pub fn lead_suit(&self) -> Option<char> {
        self.first_card().map(|c| c.suit)
    }

    pub fn is_first_card(&self) -> bool {
        self.cards.iter().all(|c| c.is_none())
    }

    pub fn is_completed(&self) -> bool {
        self.cards.iter().all(|c| c.is_some())
    }
}

#[derive(Clone, Serialize, Deserialize)]
pub struct CompletedHeartsGame {
    pub players: Vec<PlayerInfo>,
    pub previous_tricks: Vec<CompletedTrick>,
    pub hearts_broken: bool,
    pub winner_index: usize,
}

#[derive(Clone, Serialize, Deserialize)]
pub struct GameState {
    pub tricks: Vec<CompletedTrick>,
    pub current_trick: Trick,
    pub current_player: usize,
    pub hearts_broken: bool,
}
