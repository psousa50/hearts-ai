use hearts_game::{CompletedHeartsGame, CompletedTrick};
pub struct GameMovesFilter {
    good_players: Vec<usize>,
}

impl GameMovesFilter {
    pub fn new(completed_game: &CompletedHeartsGame) -> Self {
        let percentile25 = 1.25;
        let mut ordered_scores: Vec<u8> = completed_game.players.iter().map(|p| p.score).collect();
        ordered_scores.sort();
        let threshold = ordered_scores[0] as f32
            + (ordered_scores[1] as f32 - ordered_scores[0] as f32) * percentile25;

        let good_players: Vec<usize> = completed_game
            .players
            .iter()
            .enumerate()
            .filter(|(_, p)| (p.score as f32) <= threshold)
            .map(|(i, _)| i)
            .collect();
        Self { good_players }
    }

    pub fn filter(&self, player_index: usize, trick: &CompletedTrick) -> bool {
        self.good_players.contains(&player_index)
            && (trick.points <= 1 || trick.winner != player_index)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hearts_game::{CompletedHeartsGame, PlayerInfo};

    fn create_players(scores: Vec<u8>) -> Vec<PlayerInfo> {
        scores
            .into_iter()
            .enumerate()
            .map(|(i, score)| PlayerInfo {
                score,
                name: format!("Player {}", i + 1),
                initial_hand: vec![],
                strategy: "Random".to_string(),
            })
            .collect()
    }

    fn create_test_game(scores: Vec<u8>) -> CompletedHeartsGame {
        let players = create_players(scores);

        CompletedHeartsGame {
            players,
            previous_tricks: vec![],
            hearts_broken: true,
            winner_index: 0,
        }
    }

    #[test]
    fn test_good_players_identification() {
        let game = create_test_game(vec![0, 6, 7, 13]);
        let filter = GameMovesFilter::new(&game);

        assert!(filter.good_players == vec![0, 1, 2]);
    }
    #[test]
    fn test_good_players_with_zeros() {
        let game = create_test_game(vec![0, 0, 9, 17]);
        let filter = GameMovesFilter::new(&game);

        assert!(filter.good_players == vec![0, 1]);
    }

    #[test]
    fn test_good_players_identification_unsorted() {
        let game = create_test_game(vec![18, 0, 6, 2]);
        let filter = GameMovesFilter::new(&game);

        assert!(filter.good_players == vec![1, 3]);
    }
}
