use crate::models::Card;
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};

pub trait PlayingStrategy {
    fn choose_card(&self, hand: &[Card], valid_moves: &[Card]) -> Card;
}

#[derive(Clone)]
pub struct AIStrategy {
    client: Client,
    endpoint: String,
}

#[derive(Serialize)]
struct GameState {
    hand: Vec<(char, u8)>,
    valid_moves: Vec<(char, u8)>,
}

#[derive(Deserialize)]
struct PredictResponse {
    suit: char,
    rank: u8,
}

#[derive(Clone)]
pub struct RandomStrategy;

impl PlayingStrategy for RandomStrategy {
    fn choose_card(&self, _hand: &[Card], valid_moves: &[Card]) -> Card {
        use rand::seq::SliceRandom;
        let mut rng = rand::thread_rng();
        valid_moves
            .choose(&mut rng)
            .copied()
            .unwrap_or(valid_moves[0])
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

impl AIStrategy {
    pub fn new(endpoint: String) -> Self {
        AIStrategy {
            client: Client::new(),
            endpoint,
        }
    }
}

impl PlayingStrategy for AIStrategy {
    fn choose_card(&self, hand: &[Card], valid_moves: &[Card]) -> Card {
        // Convert cards to the format expected by the Python service
        let state = GameState {
            hand: hand.iter().map(|c| (c.suit, c.rank)).collect(),
            valid_moves: valid_moves.iter().map(|c| (c.suit, c.rank)).collect(),
        };

        // Make request to Python service
        match self.client.post(&self.endpoint).json(&state).send() {
            Ok(response) => {
                if let Ok(prediction) = response.json::<PredictResponse>() {
                    // Find the card in valid_moves that matches the prediction
                    valid_moves
                        .iter()
                        .find(|c| c.suit == prediction.suit && c.rank == prediction.rank)
                        .copied()
                        .unwrap_or(valid_moves[0])
                } else {
                    // Fallback to first valid move if can't parse response
                    valid_moves[0]
                }
            }
            Err(_) => {
                // Fallback to first valid move if request fails
                valid_moves[0]
            }
        }
    }
}

#[derive(Clone)]
pub enum Strategy {
    Random(RandomStrategy),
    AvoidPoints(AvoidPointsStrategy),
    Aggressive(AggressiveStrategy),
    AI(AIStrategy),
}

impl Strategy {
    pub fn choose_card(&self, hand: &[Card], valid_moves: &[Card]) -> Card {
        match self {
            Strategy::Random(s) => s.choose_card(hand, valid_moves),
            Strategy::AvoidPoints(s) => s.choose_card(hand, valid_moves),
            Strategy::Aggressive(s) => s.choose_card(hand, valid_moves),
            Strategy::AI(s) => s.choose_card(hand, valid_moves),
        }
    }
}
