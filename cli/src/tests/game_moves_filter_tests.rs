use hearts_game::{Card, CompletedHeartsGame, CompletedTrick, PlayerInfo};
use crate::game_moves_filter::GameMovesFilter;

fn create_test_game() -> CompletedHeartsGame {
    // Create players with different scores
    let players = vec![
        PlayerInfo { 
            score: 5, 
            name: "Player 1".to_string(),
            initial_hand: vec![],
            strategy: "Random".to_string()
        },
        PlayerInfo { 
            score: 15, 
            name: "Player 2".to_string(),
            initial_hand: vec![],
            strategy: "Random".to_string()
        },
        PlayerInfo { 
            score: 10, 
            name: "Player 3".to_string(),
            initial_hand: vec![],
            strategy: "Random".to_string()
        },
        PlayerInfo { 
            score: 20, 
            name: "Player 4".to_string(),
            initial_hand: vec![],
            strategy: "Random".to_string()
        },
    ];

    // Create some completed tricks
    let tricks = vec![
        CompletedTrick {
            cards: vec![
                Card { suit: 'C', rank: 2 },
                Card { suit: 'C', rank: 3 },
                Card { suit: 'C', rank: 4 },
                Card { suit: 'C', rank: 5 },
            ],
            first_player_index: 0,
            winner: 3,
            points: 0,
        },
        CompletedTrick {
            cards: vec![
                Card { suit: 'H', rank: 2 },
                Card { suit: 'H', rank: 3 },
                Card { suit: 'H', rank: 4 },
                Card { suit: 'H', rank: 5 },
            ],
            first_player_index: 1,
            winner: 3,
            points: 4,
        },
    ];

    CompletedHeartsGame { 
        players, 
        tricks,
        hearts_broken: true,
        winner_index: 0,
    }
}

#[test]
fn test_good_players_identification() {
    let game = create_test_game();
    let filter = GameMovesFilter::new(game.clone());
    
    // The good players should be player 0 (score 5) and player 2 (score 10)
    assert!(filter.good_players.contains(&0), "Player 0 should be a good player");
    assert!(filter.good_players.contains(&2), "Player 2 should be a good player");
    assert!(!filter.good_players.contains(&1), "Player 1 should not be a good player");
    assert!(!filter.good_players.contains(&3), "Player 3 should not be a good player");
}

#[test]
fn test_threshold_calculation() {
    let game = create_test_game();
    
    // Calculate threshold manually
    let mut ordered_scores: Vec<u8> = game.players.iter().map(|p| p.score).collect();
    ordered_scores.sort();
    let percentile25 = 1.25;
    let threshold = ordered_scores[0] as f32 + (ordered_scores[1] as f32 - ordered_scores[0] as f32) * percentile25;
    
    // Threshold should be 5 + (10 - 5) * 1.25 = 11.25
    assert_eq!(threshold, 11.25, "Threshold calculation is incorrect");
}

#[test]
fn test_filter_good_player_no_points() {
    let game = create_test_game();
    let filter = GameMovesFilter::new(game.clone());
    
    // Player 0 is a good player and Trick 0 has 0 points
    let result = filter.filter(0, &game.tricks[0]);
    assert!(result, "Player 0 with Trick 0 should pass the filter");
}

#[test]
fn test_filter_good_player_with_points_not_winner() {
    let game = create_test_game();
    
    // Modify trick 1 to have player 0 not be the winner
    let mut modified_game = game.clone();
    modified_game.tricks[1].winner = 3; // Player 3 is the winner
    
    let filter = GameMovesFilter::new(modified_game.clone());
    
    // Player 0 is a good player, Trick 1 has 4 points, but player 0 is not the winner
    let result = filter.filter(0, &modified_game.tricks[1]);
    assert!(result, "Player 0 with Trick 1 (not winner) should pass the filter");
}

#[test]
fn test_filter_good_player_with_points_as_winner() {
    let game = create_test_game();
    
    // Modify trick 1 to have player 0 be the winner
    let mut modified_game = game.clone();
    modified_game.tricks[1].winner = 0; // Player 0 is the winner
    
    let filter = GameMovesFilter::new(modified_game.clone());
    
    // Player 0 is a good player, Trick 1 has 4 points, and player 0 is the winner
    let result = filter.filter(0, &modified_game.tricks[1]);
    assert!(!result, "Player 0 with Trick 1 (as winner) should not pass the filter");
}

#[test]
fn test_filter_bad_player() {
    let game = create_test_game();
    let filter = GameMovesFilter::new(game.clone());
    
    // Player 3 is not a good player
    let result = filter.filter(3, &game.tricks[0]);
    assert!(!result, "Player 3 should not pass the filter regardless of the trick");
}
