use crate::models::{Card, GameState};
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

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
                    // Fallback to first valid move if can't parse response
                    valid_moves[0]
                }
            }
            Err(_) => {
                panic!("Failed to make request to Python service");
            }
        }
    }
}

#[derive(Clone)]
pub struct MyStrategy;

impl MyStrategy {
    pub fn new() -> Self {
        MyStrategy {}
    }

    fn sorted_hand_from_suit(&self, hand: &[Card], suit: char) -> Vec<Card> {
        let mut cards_in_suit: Vec<Card> = hand
            .iter()
            .filter(|card| card.suit == suit)
            .copied()
            .collect();

        cards_in_suit.sort_by_key(|card| card.rank);
        cards_in_suit
    }
}

impl PlayingStrategy for MyStrategy {
    fn choose_card(&self, valid_moves: &[Card], game_state: Option<GameState>) -> Card {
        let game_state = match game_state {
            Some(state) => state,
            None => return valid_moves[0], // Fallback if no game state is provided
        };

        // If it's the first trick of the game and we have the two of clubs
        if game_state.current_trick.is_first_card() && game_state.previous_tricks.is_empty() {
            if let Some(two_of_clubs) = valid_moves.iter().find(|card| card.is_two_of_clubs()) {
                return *two_of_clubs;
            }
        }

        // Count cards out per suit
        let mut number_of_cards_out_per_suit: HashMap<char, u8> = HashMap::new();
        number_of_cards_out_per_suit.insert('C', 0);
        number_of_cards_out_per_suit.insert('D', 0);
        number_of_cards_out_per_suit.insert('H', 0);
        number_of_cards_out_per_suit.insert('S', 0);

        // Count cards in player's hand
        for card in &game_state.player_hand {
            *number_of_cards_out_per_suit.entry(card.suit).or_insert(0) += 1;
        }

        // Count cards in previous tricks
        for previous_trick in &game_state.previous_tricks {
            for card in &previous_trick.cards {
                *number_of_cards_out_per_suit.entry(card.suit).or_insert(0) += 1;
            }
        }

        // Count cards in current trick
        for card_option in &game_state.current_trick.cards {
            if let Some(card) = card_option {
                *number_of_cards_out_per_suit.entry(card.suit).or_insert(0) += 1;
            }
        }

        // Check if queen of spades is out
        let mut excluded_suits = vec!['H'];
        let mut queen_of_spades_is_out = false;

        for previous_trick in &game_state.previous_tricks {
            for card in &previous_trick.cards {
                if card.is_queen_of_spades() {
                    queen_of_spades_is_out = true;
                    break;
                }
            }
            if queen_of_spades_is_out {
                break;
            }
        }

        if !queen_of_spades_is_out {
            excluded_suits.push('S');
        }

        let chosen_card = if game_state.current_trick.is_first_card() {
            // Leading a trick
            // Find suit with fewest cards out but not zero, excluding hearts and spades (if queen is not out)
            let suit_with_less_cards = ['C', 'D', 'H', 'S']
                .iter()
                .filter(|&&suit| {
                    let count = *number_of_cards_out_per_suit.get(&suit).unwrap_or(&0);
                    count > 0 && !excluded_suits.contains(&suit)
                })
                .min_by_key(|&&suit| *number_of_cards_out_per_suit.get(&suit).unwrap_or(&u8::MAX))
                .copied()
                .unwrap_or('C'); // Default to clubs if no suitable suit found

            let sorted_hand =
                self.sorted_hand_from_suit(&game_state.player_hand, suit_with_less_cards);

            if *number_of_cards_out_per_suit
                .get(&suit_with_less_cards)
                .unwrap_or(&0)
                > 7
            {
                // If many cards of this suit are out, play lowest
                if !sorted_hand.is_empty() {
                    sorted_hand[0]
                } else {
                    game_state.player_hand[0]
                }
            } else {
                // Otherwise play highest
                if !sorted_hand.is_empty() {
                    *sorted_hand.last().unwrap()
                } else {
                    *game_state.player_hand.last().unwrap()
                }
            }
        } else {
            // Following a trick
            let lead_suit = game_state.current_trick.lead_suit().unwrap_or('C');

            // Get cards in the trick of the lead suit
            let trick_cards_in_suit: Vec<Card> = game_state
                .current_trick
                .cards
                .iter()
                .filter_map(|card_opt| *card_opt)
                .filter(|card| card.suit == lead_suit)
                .collect();

            if trick_cards_in_suit.is_empty() {
                // Fallback if no cards in lead suit (shouldn't happen)
                return valid_moves[0];
            }

            let highest_card_in_trick = trick_cards_in_suit
                .iter()
                .max_by_key(|card| card.rank)
                .unwrap();

            // Check if player can follow suit
            let can_follow_suit = game_state
                .player_hand
                .iter()
                .any(|card| card.suit == lead_suit);

            if can_follow_suit {
                let sorted_hand = self.sorted_hand_from_suit(&game_state.player_hand, lead_suit);

                // Calculate score of current trick
                let mut score = 0;
                for card_opt in &game_state.current_trick.cards {
                    if let Some(card) = card_opt {
                        score += card.score();
                    }
                }

                // Determine if we should try to take the trick
                let should_take_trick = score == 0
                    && *number_of_cards_out_per_suit.get(&lead_suit).unwrap_or(&0) < 7
                    && !excluded_suits.contains(&lead_suit);

                if should_take_trick {
                    // Play highest card to take the trick
                    *sorted_hand.last().unwrap()
                } else {
                    // Try to play a card lower than the highest card in the trick
                    let sorted_hand_lower_than_highest = sorted_hand
                        .iter()
                        .filter(|card| card.rank < highest_card_in_trick.rank)
                        .copied()
                        .collect::<Vec<Card>>();

                    if !sorted_hand_lower_than_highest.is_empty() {
                        *sorted_hand_lower_than_highest.last().unwrap()
                    } else {
                        *sorted_hand.last().unwrap()
                    }
                }
            } else {
                // Can't follow suit, try to dump high-value cards
                let has_queen_of_spades = game_state
                    .player_hand
                    .iter()
                    .any(|card| card.is_queen_of_spades());

                if has_queen_of_spades {
                    // Dump queen of spades if possible
                    game_state
                        .player_hand
                        .iter()
                        .find(|card| card.is_queen_of_spades())
                        .copied()
                        .unwrap()
                } else {
                    // Try to dump hearts
                    let sorted_hearts = self.sorted_hand_from_suit(&game_state.player_hand, 'H');

                    if !sorted_hearts.is_empty() {
                        *sorted_hearts.last().unwrap()
                    } else {
                        // Fallback to first valid move
                        valid_moves[0]
                    }
                }
            }
        };

        // Verify the chosen card is in valid_moves
        if valid_moves.contains(&chosen_card) {
            chosen_card
        } else {
            valid_moves[0]
        }
    }
}

#[derive(Clone)]
pub enum Strategy {
    Random(RandomStrategy),
    AvoidPoints(AvoidPointsStrategy),
    Aggressive(AggressiveStrategy),
    AI(AIStrategy),
    My(MyStrategy),
}

impl Strategy {
    pub fn choose_card(&self, valid_moves: &[Card], game_state: Option<GameState>) -> Card {
        match self {
            Strategy::Random(s) => s.choose_card(valid_moves, game_state),
            Strategy::AvoidPoints(s) => s.choose_card(valid_moves, game_state),
            Strategy::Aggressive(s) => s.choose_card(valid_moves, game_state),
            Strategy::AI(s) => s.choose_card(valid_moves, game_state),
            Strategy::My(s) => s.choose_card(valid_moves, game_state),
        }
    }

    pub fn needs_game_state(&self) -> bool {
        match self {
            Strategy::Random(_) => false,
            Strategy::AvoidPoints(_) => false,
            Strategy::Aggressive(_) => false,
            Strategy::AI(_) => true,
            Strategy::My(_) => true,
        }
    }
}
