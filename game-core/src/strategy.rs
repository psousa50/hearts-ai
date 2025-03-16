use crate::models::{Card, GameState};
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct PredictRequest {
    state: GameState,
    valid_moves: Vec<Card>,
}

pub trait PlayingStrategy {
    fn choose_card(&self, valid_moves: &[Card], game_state: Option<GameState>) -> Card;
}

#[derive(Clone)]
pub struct AIStrategy {
    client: Client,
    endpoint: String,
}

#[derive(Deserialize)]
struct PredictResponse {
    suit: char,
    rank: u8,
}

#[derive(Clone)]
pub struct RandomStrategy;

impl PlayingStrategy for RandomStrategy {
    fn choose_card(&self, valid_moves: &[Card], _game_state: Option<GameState>) -> Card {
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
    fn choose_card(&self, valid_moves: &[Card], _game_state: Option<GameState>) -> Card {
        // Play lowest value card
        *valid_moves
            .iter()
            .min_by_key(|card| {
                // Prioritize low hearts and queen of spades
                if card.is_penalty() {
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
    fn choose_card(&self, valid_moves: &[Card], _game_state: Option<GameState>) -> Card {
        // Play highest value card
        *valid_moves
            .iter()
            .max_by_key(|card| {
                // Prioritize hearts and queen of spades
                if card.is_penalty() {
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
    fn choose_card(&self, valid_moves: &[Card], game_state: Option<GameState>) -> Card {
        let game_state = game_state.unwrap();
        let request = PredictRequest {
            state: game_state,
            valid_moves: valid_moves.to_vec(),
        };

        // Make request to Python service
        match self.client.post(&self.endpoint).json(&request).send() {
            Ok(response) => {
                if let Ok(prediction) = response.json::<PredictResponse>() {
                    // Find the card in valid_moves that matches the prediction
                    valid_moves
                        .iter()
                        .find(|c| c.suit == prediction.suit && c.rank == prediction.rank)
                        .copied()
                        .unwrap_or(valid_moves[0])
                } else {
                    println!("Failed to parse response from AI service");
                    // Fallback to first valid move if can't parse response
                    valid_moves[0]
                }
            }
            Err(e) => {
                println!("Failed to make request to AI service: {}", e);
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
    pub fn choose_card(&self, valid_moves: &[Card], game_state: Option<GameState>) -> Card {
        match self {
            Strategy::Random(s) => s.choose_card(valid_moves, game_state),
            Strategy::AvoidPoints(s) => s.choose_card(valid_moves, game_state),
            Strategy::Aggressive(s) => s.choose_card(valid_moves, game_state),
            Strategy::AI(s) => s.choose_card(valid_moves, game_state),
        }
    }

    pub fn needs_game_state(&self) -> bool {
        match self {
            Strategy::Random(_) => false,
            Strategy::AvoidPoints(_) => false,
            Strategy::Aggressive(_) => false,
            Strategy::AI(_) => true,
        }
    }
}
