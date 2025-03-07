use crate::deck::Deck;
use crate::models::{Card, CompletedTrick, Trick};
use crate::player::Player;
use crate::strategy::Strategy;
use serde::{Deserialize, Serialize};

pub struct HeartsGame {
    players: Vec<Player>,
    current_leader: usize,
    tricks: Vec<CompletedTrick>,
    current_trick: Trick,
    hearts_broken: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlayerInfo {
    pub name: String,
    pub initial_hand: Vec<Card>,
    pub score: u8,
    pub strategy: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameResult {
    pub players: Vec<PlayerInfo>,
    pub tricks: Vec<CompletedTrick>,
    pub winner: usize,
}

impl HeartsGame {
    pub fn new(player_configs: &[(&str, Strategy)]) -> Self {
        let mut deck = Deck::new();
        let hands = deck.deal(4);
        let players: Vec<Player> = player_configs
            .iter()
            .zip(hands.into_iter())
            .map(|((name, strategy), hand)| Player::new(name, hand, strategy.clone()))
            .collect();

        let current_leader = Self::find_starting_player(&players);
        Self {
            players,
            hearts_broken: false,
            current_leader,
            tricks: Vec::new(),
            current_trick: Trick::new(),
        }
    }

    fn find_starting_player(players: &[Player]) -> usize {
        for (i, player) in players.iter().enumerate() {
            if player.hand.iter().any(|c| c.is_two_of_clubs()) {
                return i;
            }
        }
        0
    }

    fn must_follow_suit(hand: &[Card], lead_suit: char) -> Vec<Card> {
        hand.iter()
            .filter(|c| c.suit == lead_suit)
            .cloned()
            .collect()
    }

    fn avoid_hearts(hand: &[Card]) -> Vec<Card> {
        let non_hearts: Vec<Card> = hand.iter().filter(|c| !c.is_hearts()).cloned().collect();

        if non_hearts.is_empty() {
            hand.to_vec()
        } else {
            non_hearts
        }
    }

    fn avoid_penalties(hand: &[Card]) -> Vec<Card> {
        let safe_cards: Vec<Card> = hand.iter().filter(|c| !c.is_penalty()).cloned().collect();

        if safe_cards.is_empty() {
            hand.to_vec()
        } else {
            safe_cards
        }
    }

    fn get_two_of_clubs(hand: &[Card]) -> Vec<Card> {
        hand.iter()
            .filter(|c| c.is_two_of_clubs())
            .cloned()
            .collect()
    }

    fn get_valid_moves(&self, player_index: usize) -> Vec<Card> {
        let hand = &self.players[player_index].hand;
        if self.current_trick.is_first_card() && self.tricks.is_empty() {
            let two_clubs = Self::get_two_of_clubs(hand);
            if !two_clubs.is_empty() {
                return two_clubs;
            }
        }

        // If a suit was led, must follow suit if possible
        let lead_suit = self.current_trick.lead_suit();
        if let Some(lead_suit) = lead_suit {
            let same_suit = Self::must_follow_suit(hand, lead_suit);
            if !same_suit.is_empty() {
                return same_suit;
            }
        }

        // On first trick, can't play hearts or queen of spades
        if self.tricks.is_empty() {
            return Self::avoid_penalties(hand);
        }

        // If hearts not broken, avoid hearts if possible
        if !self.hearts_broken {
            let non_hearts = Self::avoid_hearts(hand);
            if !non_hearts.is_empty() {
                return non_hearts;
            }
        }

        hand.to_vec()
    }

    fn determine_trick_winner(cards: &Vec<Card>, first_player: usize) -> usize {
        let lead_suit = cards[first_player].suit;
        cards
            .iter()
            .enumerate()
            .filter(|(_, card)| card.suit == lead_suit)
            .max_by_key(|(_, card)| card.rank)
            .map(|(player_idx, _)| player_idx)
            .unwrap_or(0)
    }

    fn play_trick(&mut self) -> CompletedTrick {
        // Store the first player (leader) of this trick
        let first_player = self.current_leader;

        // Play the trick in turn order
        let mut current_trick: Trick = Trick::new();
        current_trick.first_player = first_player;
        let mut current_player = first_player;

        for i in 0..4 {
            let valid_moves = self.get_valid_moves(i);

            let played_card = self.players[i].play_card(&valid_moves);
            if played_card.suit == 'H' {
                self.hearts_broken = true;
            }

            // Store the card with player information
            current_trick.add_card(played_card, i);

            current_player = (current_player + 1) % 4;
        }

        let trick_cards = current_trick
            .cards
            .iter()
            .map(|c| c.unwrap().clone())
            .collect();

        let winner = Self::determine_trick_winner(&trick_cards, first_player);
        self.current_leader = winner;

        // Calculate points for the trick
        let points = trick_cards.iter().map(|card| card.score()).sum();

        CompletedTrick {
            cards: trick_cards,
            winner,
            points,
            first_player,
        }
    }

    pub fn play_game(&mut self) -> GameResult {
        let mut scores = vec![0u8; 4];
        let mut tricks = Vec::new();

        // Play all 13 tricks
        for _ in 0..13 {
            let trick = self.play_trick();
            let trick_score = trick.points;
            scores[trick.winner] += trick_score;
            tricks.push(trick);
        }

        // Create final scores with player names
        let players: Vec<PlayerInfo> = self
            .players
            .iter()
            .enumerate()
            .map(|(idx, player)| PlayerInfo {
                name: player.name.clone(),
                initial_hand: player.initial_hand.clone(),
                score: scores[idx],
                strategy: player.strategy_name().to_string(),
            })
            .collect();

        // Find winner (player with lowest score)
        let winner_idx = scores
            .iter()
            .enumerate()
            .min_by_key(|(_, score)| *score)
            .map(|(idx, _)| idx)
            .unwrap();

        GameResult {
            players,
            tricks,
            winner: winner_idx,
        }
    }
}
