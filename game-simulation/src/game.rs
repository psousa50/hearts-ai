use crate::card::Card;
use crate::deck::Deck;
use crate::player::Player;
use crate::strategy::Strategy;
use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct Trick {
    pub cards: Vec<(Card, usize)>,
    pub winner: usize,
}

#[derive(Debug, Clone, Serialize)]
pub struct GameResult {
    pub tricks: Vec<Trick>,
    pub final_scores: Vec<(String, u8)>,
    pub winner: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct GameStats {
    pub game_id: usize,
    pub winner: String,
    pub scores: Vec<(String, u8)>,
    pub tricks: Vec<Trick>,
    pub total_points: u8,
}

pub struct HeartsGame {
    players: Vec<Player>,
    hearts_broken: bool,
    current_leader: usize,
    tricks: Vec<Trick>,
}

impl HeartsGame {
    pub fn new_with_strategies(player_configs: &[(&str, Strategy)]) -> Self {
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

        // Must follow suit if possible
        if let Some(suit) = lead_suit {
            let suit_cards = Self::must_follow_suit(hand, suit);
            if !suit_cards.is_empty() {
                return suit_cards;
            }
        }

        // Leading a trick
        if is_first_card {
            // Can't lead hearts until broken
            if !self.hearts_broken {
                return Self::avoid_hearts(hand);
            }
            return hand.to_vec();
        }

        // Can't play penalties on first trick
        if self.tricks.is_empty() {
            return Self::avoid_penalties(hand);
        }

        // Any card is valid
        hand.to_vec()
    }

    fn determine_trick_winner(trick_cards: &[(Card, usize)], lead_suit: char) -> usize {
        trick_cards
            .iter()
            .filter(|(card, _)| card.suit == lead_suit)
            .max_by_key(|(card, _)| card.rank)
            .map(|(_, player)| *player)
            .unwrap()
    }

    fn calculate_trick_score(trick_cards: &[(Card, usize)]) -> u8 {
        trick_cards.iter().map(|(card, _)| card.score()).sum()
    }

    pub fn play_trick(&mut self) -> Trick {
        let mut trick_cards: Vec<(Card, usize)> = Vec::new();
        let mut current_player = self.current_leader;
        let mut lead_suit = None;

        for _ in 0..4 {
            let hand = &self.players[current_player].hand;
            let valid_moves = self.get_valid_moves(hand, lead_suit, trick_cards.is_empty());

            let played_card = self.players[current_player].play_card(valid_moves, &trick_cards);

            if trick_cards.is_empty() {
                lead_suit = Some(played_card.suit);
                if played_card.suit == 'H' {
                    self.hearts_broken = true;
                }
            }

            trick_cards.push((played_card, current_player));
            current_player = (current_player + 1) % 4;
        }

        let lead_suit = trick_cards[0].0.suit;
        let winner = Self::determine_trick_winner(&trick_cards, lead_suit);
        let score = Self::calculate_trick_score(&trick_cards);

        self.current_leader = winner;
        self.players[winner].score += score;

        Trick {
            cards: trick_cards,
            winner,
        }
    }

    pub fn play_game(&mut self) -> GameResult {
        // Play all 13 tricks
        for _ in 0..13 {
            let trick = self.play_trick();
            self.tricks.push(trick);
        }

        // Calculate final scores
        let final_scores: Vec<(String, u8)> = self
            .players
            .iter()
            .map(|p| (p.name.clone(), p.score))
            .collect();

        // Find winner (player with lowest score)
        let winner = final_scores
            .iter()
            .min_by_key(|(_, score)| score)
            .map(|(name, _)| name.clone())
            .unwrap_or_else(|| "Unknown".to_string());

        GameResult {
            tricks: self.tricks.clone(),
            final_scores,
            winner,
        }
    }
}
