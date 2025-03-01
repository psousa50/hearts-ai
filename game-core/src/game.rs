use crate::card::Card;
use crate::deck::Deck;
use crate::player::Player;
use crate::strategy::Strategy;
use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrickCard {
    pub card: Card,
    pub player_index: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trick {
    pub cards: Vec<TrickCard>,
    pub winner: usize,
    pub points: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlayerInfo {
    pub index: usize,
    pub name: String,
    pub strategy: String,
    pub score: u8,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GameResult {
    pub game_id: usize,
    pub players: Vec<PlayerInfo>,
    pub tricks: Vec<Trick>,
    pub winner: usize,
}

pub struct HeartsGame {
    players: Vec<Player>,
    hearts_broken: bool,
    current_leader: usize,
    tricks: Vec<Trick>,
    game_id: usize,
}

impl HeartsGame {
    pub fn new_with_strategies(player_configs: &[(&str, Strategy)], game_id: usize) -> Self {
        let mut deck = Deck::new();
        let hands = deck.deal(4);
        let players: Vec<Player> = player_configs
            .iter()
            .zip(hands.into_iter())
            .map(|((name, strategy), hand)| Player::with_strategy(name, hand, strategy.clone()))
            .collect();

        let current_leader = Self::find_starting_player(&players);
        Self {
            players,
            hearts_broken: false,
            current_leader,
            tricks: Vec::new(),
            game_id,
        }
    }

    fn find_starting_player(players: &[Player]) -> usize {
        for (i, player) in players.iter().enumerate() {
            if player.hand.iter().any(|c| c.suit == 'C' && c.rank == 2) {
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
        let non_hearts: Vec<Card> = hand.iter().filter(|c| c.suit != 'H').cloned().collect();

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
            .filter(|c| c.suit == 'C' && c.rank == 2)
            .cloned()
            .collect()
    }

    fn get_valid_moves(
        &self,
        hand: &[Card],
        lead_suit: Option<char>,
        is_first_card: bool,
    ) -> Vec<Card> {
        // First card of the first trick must be 2 of clubs
        if is_first_card && self.tricks.is_empty() {
            let two_clubs = Self::get_two_of_clubs(hand);
            if !two_clubs.is_empty() {
                return two_clubs;
            }
        }

        // If a suit was led, must follow suit if possible
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

    fn determine_trick_winner(trick_cards: &[(Card, usize)], lead_suit: char) -> usize {
        trick_cards
            .iter()
            .enumerate()
            .filter(|(_, (card, _))| card.suit == lead_suit)
            .max_by_key(|(_, (card, _))| card.rank)
            .map(|(_, (_, player_idx))| *player_idx)
            .unwrap()
    }

    fn play_trick(&mut self) -> Trick {
        let mut trick_cards = Vec::new();
        let mut current_player = self.current_leader;
        let mut lead_suit = None;

        for i in 0..4 {
            let is_first_card = i == 0 && trick_cards.is_empty();
            let valid_moves = self.get_valid_moves(
                &self.players[current_player].hand,
                lead_suit,
                is_first_card,
            );

            let played_card = self.players[current_player].play_card(&valid_moves);
            if played_card.suit == 'H' {
                self.hearts_broken = true;
            }

            // Set lead suit if this is the first card
            if lead_suit.is_none() {
                lead_suit = Some(played_card.suit);
            }

            trick_cards.push(TrickCard {
                card: played_card,
                player_index: current_player,
            });
            current_player = (current_player + 1) % 4;
        }

        let lead_suit = lead_suit.unwrap();
        let winner = Self::determine_trick_winner(
            &trick_cards.iter().map(|tc| (tc.card.clone(), tc.player_index)).collect::<Vec<_>>(),
            lead_suit,
        );
        self.current_leader = winner;

        // Calculate points for the trick
        let points = trick_cards.iter().map(|tc| {
            if tc.card.suit == 'H' {
                1
            } else if tc.card.suit == 'S' && tc.card.rank == 12 {
                13
            } else {
                0
            }
        }).sum();

        Trick {
            cards: trick_cards,
            winner,
            points,
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
        let final_scores: Vec<PlayerInfo> = self.players
            .iter()
            .enumerate()
            .map(|(idx, player)| PlayerInfo {
                index: idx,
                name: player.name.clone(),
                strategy: player.strategy_name().to_string(),
                score: scores[idx],
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
            game_id: self.game_id,
            players: final_scores,
            tricks,
            winner: winner_idx,
        }
    }
}
