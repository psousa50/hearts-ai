use crate::card::Card;
use crate::strategy::Strategy;

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

    pub fn play_card(&mut self, valid_moves: &[Card]) -> Card {
        let chosen_card = self.strategy.choose_card(&self.hand, valid_moves);
        self.hand.retain(|c| *c != chosen_card);
        chosen_card
    }

    pub fn strategy_name(&self) -> &'static str {
        match self.strategy {
            Strategy::Random(_) => "Random",
            Strategy::AvoidPoints(_) => "Avoid Points",
            Strategy::Aggressive(_) => "Aggressive",
            Strategy::AI(_) => "AI",
        }
    }
}
