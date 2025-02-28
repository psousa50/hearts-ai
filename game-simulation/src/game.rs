use serde::Serialize;
use crate::card::Card;
use crate::deck::Deck;
use crate::player::Player;

#[derive(Debug, Clone, Serialize)]
pub struct Trick {
    pub cards: Vec<(Card, usize)>,
    pub winner: usize,
    pub score: u8,
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
    pub fn new(player_names: Vec<&str>) -> Self {
        let mut deck = Deck::new();
        let hands = deck.deal(4);
        let players: Vec<Player> = player_names
            .into_iter()
            .zip(hands.into_iter())
            .map(|(name, hand)| Player::new(name, hand))
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
        let non_hearts: Vec<Card> = hand.iter()
            .filter(|c| c.suit != 'H')
            .cloned()
            .collect();
            
        if non_hearts.is_empty() {
            hand.to_vec()
        } else {
            non_hearts
        }
    }

    fn avoid_penalties(hand: &[Card]) -> Vec<Card> {
        let safe_cards: Vec<Card> = hand.iter()
            .filter(|c| !c.is_penalty())
            .cloned()
            .collect();
            
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

    fn get_valid_moves(&self, hand: &[Card], lead_suit: Option<char>, is_first_card: bool) -> Vec<Card> {
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

    fn play_trick(&mut self) {
        // First player's move
        let first_player_index = self.current_leader;
        let first_hand = &self.players[first_player_index].hand;
        let first_valid_moves = self.get_valid_moves(first_hand, None, true);
        let first_card = self.players[first_player_index].play_card(first_valid_moves);
        
        if first_card.suit == 'H' {
            self.hearts_broken = true;
        }
        
        let mut cards_and_players = vec![(first_card, first_player_index)];
        let lead_suit = first_card.suit;

        // Other players' moves
        for i in 1..4 {
            let player_index = (self.current_leader + i) % 4;
            let hand = &self.players[player_index].hand;
            let valid_moves = self.get_valid_moves(hand, Some(lead_suit), false);
            let chosen_card = self.players[player_index].play_card(valid_moves);
            
            if chosen_card.suit == 'H' {
                self.hearts_broken = true;
            }
            
            cards_and_players.push((chosen_card, player_index));
        }

        let winning_player = Self::determine_trick_winner(&cards_and_players, lead_suit);
        let trick_score = Self::calculate_trick_score(&cards_and_players);

        self.players[winning_player].score += trick_score;
        self.current_leader = winning_player;

        self.tricks.push(Trick {
            cards: cards_and_players,
            winner: winning_player,
            score: trick_score,
        });
    }

    pub fn play_game(&mut self) -> GameResult {
        // Play all 13 tricks
        (0..13).for_each(|_| self.play_trick());

        // Calculate final scores
        let final_scores: Vec<(String, u8)> = self.players
            .iter()
            .map(|p| (p.name.clone(), p.score))
            .collect();

        // Find winner (player with lowest score)
        let winner = final_scores
            .iter()
            .min_by_key(|(_, score)| score)
            .map(|(name, _)| name.clone())
            .unwrap();

        GameResult {
            tricks: self.tricks.clone(),
            final_scores,
            winner,
        }
    }
}
