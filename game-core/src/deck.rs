use crate::models::Card;
use rand::seq::SliceRandom;

pub struct Deck {
    cards: Vec<Card>,
}

impl Deck {
    pub fn new() -> Self {
        let cards: Vec<Card> = ['S', 'H', 'D', 'C']
            .iter()
            .flat_map(|&suit| (2..=14).map(move |rank| Card::new(suit, rank)))
            .collect();

        let mut deck = Self { cards };
        deck.shuffle();
        deck
    }

    pub fn shuffle(&mut self) {
        self.cards.shuffle(&mut rand::thread_rng());
    }

    pub fn deal(&mut self, num_players: usize) -> Vec<Vec<Card>> {
        let mut hands: Vec<Vec<Card>> = vec![Vec::new(); num_players];

        for (i, card) in self.cards.drain(..).enumerate() {
            hands[i % num_players].push(card);
        }

        hands.iter_mut().for_each(|hand| hand.sort());
        hands
    }
}
