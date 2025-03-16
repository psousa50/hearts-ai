use crate::deck::Deck;
use crate::models::{Card, CompletedHeartsGame, CompletedTrick, GameState, Trick};
use crate::player::{Player, PlayerInfo};
use crate::strategy::Strategy;

pub struct HeartsGame {
    pub players: Vec<Player>,
    pub tricks: Vec<CompletedTrick>,
    pub current_trick: Trick,
    pub current_player_index: usize,
    pub hearts_broken: bool,
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

        let current_player = Self::find_starting_player(&players);
        Self {
            players,
            hearts_broken: false,
            current_player_index: current_player,
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

    pub fn get_valid_moves(&self, player_index: usize) -> Vec<Card> {
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
            // If can't follow suit, can play any card including hearts
            return hand.to_vec();
        }

        // Leading a trick (current_trick is empty or is first card)
        
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

    fn play_trick(&mut self) {
        if self.current_trick.is_first_card() {
            self.current_trick.first_player_index = self.current_player_index;
        }

        let valid_moves = self.get_valid_moves(self.current_player_index);

        let game_state = if self.players[self.current_player_index]
            .strategy
            .needs_game_state()
        {
            Some(self.fetch_game_state())
        } else {
            None
        };
        let played_card =
            self.players[self.current_player_index].play_card(&valid_moves, game_state);

        if played_card.is_hearts() {
            self.hearts_broken = true;
        }

        // Store the card with player information
        self.current_trick
            .add_card(played_card, self.current_player_index);

        if self.current_trick.is_completed() {
            self.complete_trick();
        } else {
            self.current_player_index = (self.current_player_index + 1) % 4;
        }
    }

    fn complete_trick(&mut self) {
        let first_player_index = self.current_trick.first_player_index;
        let trick_cards = self
            .current_trick
            .cards
            .iter()
            .map(|c| c.unwrap().clone())
            .collect();

        let winner = Self::determine_trick_winner(&trick_cards, first_player_index);
        self.current_player_index = winner;

        let points = trick_cards.iter().map(|card| card.score()).sum();

        let completed_trick = CompletedTrick {
            cards: trick_cards,
            winner_index: winner,
            score: points,
            first_player_index,
        };

        self.players[completed_trick.winner_index].score += completed_trick.score;

        self.tricks.push(completed_trick);
        self.current_trick = Trick::new();
    }

    pub fn fetch_game_state(&self) -> GameState {
        GameState {
            previous_tricks: self.tricks.clone(),
            current_trick: self.current_trick.clone(),
            player_hand: self.players[self.current_player_index].hand.clone(),
            current_player_index: self.current_player_index,
        }
    }

    pub fn completed_game(&self) -> CompletedHeartsGame {
        let players = self
            .players
            .iter()
            .map(|p| PlayerInfo {
                name: p.name.clone(),
                initial_hand: p.initial_hand.clone(),
                score: p.score,
                strategy: p.strategy_name().to_string(),
            })
            .collect();

        CompletedHeartsGame {
            previous_tricks: self.tricks.clone(),
            players,
            hearts_broken: self.hearts_broken,
            winner_index: self.current_player_index,
        }
    }

    pub fn play_game(&mut self) {
        while !self.game_is_over() && !self.current_trick.is_completed() {
            self.play_trick();
        }
    }

    fn game_is_over(&self) -> bool {
        self.tricks.len() == 13
    }
}
