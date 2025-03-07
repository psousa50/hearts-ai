use hearts_game::{Card, CompletedTrick, Trick};
use serde::Serialize;

#[derive(Serialize, Clone)]
pub struct CompactCard {
    pub suit: char,
    pub rank: u8,
}

#[derive(Serialize)]
pub struct GameState {
    pub previous_tricks: Vec<CompletedTrick>,
    pub current_trick: Trick,
    pub current_player_index: usize,
    pub player_hand: Vec<Card>,
    pub played_card: Card,
}

#[derive(Serialize)]
pub struct CompactTrainingData {
    pub previous_tricks: Vec<CompletedTrick>,
    pub current_trick: Trick,
    pub current_player_index: usize,
    pub player_hand: Vec<Card>,
    pub played_card: Card,
}
