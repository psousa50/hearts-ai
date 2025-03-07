use serde::Serialize;

#[derive(Serialize, Clone)]
pub struct Card {
    pub suit: char,
    pub rank: u8,
}

#[derive(Serialize, Clone)]
pub struct CompletedTrick {
    pub cards: Vec<Card>,
    pub first_player: usize,
    pub score: u8,
    pub winner: usize,
}

#[derive(Serialize, Clone)]
pub struct Trick {
    pub cards: Vec<Card>,
    pub first_player: usize,
    pub winner: usize,
    pub points: u8,
}

impl Trick {
    pub fn new() -> Self {
        Self {
            cards: Vec::new(),
            first_player: 0,
            winner: 0,
            points: 0,
        }
    }

    pub fn push(&mut self, card: Card) {
        self.cards.push(card);
    }
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
    pub game_id: usize,
    pub trick_number: usize,
    pub previous_tricks: Vec<CompletedTrick>,
    pub current_trick_cards: Vec<Card>,
    pub current_player_index: usize,
    pub player_hand: Vec<Card>,
    pub played_card: Card,
}
