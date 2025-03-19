use crate::models::Card;
use rand::seq::SliceRandom;
use rand::{SeedableRng, rngs::StdRng};

#[derive(Clone)]
pub struct Deck {
    cards: Vec<Card>,
}

impl Deck {
    pub fn new(seed: Option<u64>) -> Self {
        let cards: Vec<Card> = ['S', 'H', 'D', 'C']
            .iter()
            .flat_map(|&suit| (2..=14).map(move |rank| Card::new(suit, rank)))
            .collect();

        let mut deck = Self { cards };

        deck.shuffle(seed);

        deck
    }

    pub fn shuffle(&mut self, seed: Option<u64>) {
        match seed {
            Some(seed_value) => self.cards.shuffle(&mut StdRng::seed_from_u64(seed_value)),
            None => self.cards.shuffle(&mut rand::thread_rng()),
        }
    }

    pub fn deal(&mut self, num_players: usize) -> Vec<Vec<Card>> {
        let mut hands: Vec<Vec<Card>> = vec![Vec::new(); num_players];

        for (i, card) in self.cards.drain(..).enumerate() {
            hands[i % num_players].push(card);
        }

        hands.iter_mut().for_each(|hand| hand.sort());
        hands
    }

    pub fn rotate(&self, rotation: usize) -> Deck {
        let mut new_cards = self.cards.clone();
        new_cards.rotate_left(rotation);
        Deck { cards: new_cards }
    }
}
