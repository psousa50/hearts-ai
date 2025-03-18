use crate::models::{Card, GameState};
use crate::strategy::Strategy;
use serde::{Deserialize, Serialize};

#[derive(Clone, Serialize, Deserialize)]
pub struct PlayerInfo {
    pub name: String,
    pub initial_hand: Vec<Card>,
    pub score: u8,
    pub strategy: String,
}

#[derive(Clone)]
pub struct Player {
    pub name: String,
    pub initial_hand: Vec<Card>,
    pub hand: Vec<Card>,
    pub score: u8,
    pub strategy: Strategy,
}

impl Player {
    pub fn new(name: &str, hand: Vec<Card>, strategy: Strategy) -> Self {
        Self {
            name: name.to_string(),
            initial_hand: hand.clone(),
            hand,
            score: 0,
            strategy,
        }
    }

    pub fn play_card(&mut self, valid_moves: &[Card], game_state: Option<GameState>) -> Card {
        let chosen_card = self.strategy.choose_card(valid_moves, game_state);
        self.hand.retain(|c| *c != chosen_card);
        chosen_card
    }

    pub fn strategy_name(&self) -> &'static str {
        match self.strategy {
            Strategy::Random(_) => "Random",
            Strategy::AvoidPoints(_) => "Avoid Points",
            Strategy::Aggressive(_) => "Aggressive",
            Strategy::AI(_) => "AI",
            Strategy::My(_) => "My Strategy",
        }
    }
}
