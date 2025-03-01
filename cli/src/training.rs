use hearts_game::{AggressiveStrategy, AvoidPointsStrategy, Card, HeartsGame, RandomStrategy, Strategy};
use serde::Serialize;
use serde_json;
use std::collections::HashSet;
use std::fs::{self, File};
use std::io::BufWriter;
use std::path::PathBuf;
use std::time::Instant;
use chrono::Utc;

#[derive(Serialize)]
struct TrainingDataItem {
    game_id: usize,
    trick_number: usize,
    previous_tricks: Vec<TrainingTrick>,
    current_trick_cards: Vec<(Card, usize)>,
    current_player_index: usize,
    played_card: Card,
}

#[derive(Serialize, Clone)]
struct TrainingTrick {
    cards: Vec<(Card, usize)>,
    winner: usize,
}

pub fn generate_training_data(num_games: usize, save_games: bool) {
    let start = Instant::now();
    let mut training_data = Vec::new();
    let mut excluded_moves = 0;
    let mut total_moves = 0;

    let player_configs = [
        ("Alice", Strategy::Random(RandomStrategy)),
        ("Bob", Strategy::Random(RandomStrategy)),
        ("Charlie", Strategy::AvoidPoints(AvoidPointsStrategy)),
        ("David", Strategy::Aggressive(AggressiveStrategy)),
    ];

    let mut all_game_results = Vec::with_capacity(num_games);

    for game_id in 0..num_games {
        // Play a full game and record its result
        let mut game = HeartsGame::new_with_strategies(&player_configs, game_id);
        let game_result = game.play_game();
        
        // Get players with more than 3 points in final score
        let bad_players: HashSet<_> = game_result.final_scores
            .iter()
            .filter(|(_, score)| *score > 3)
            .map(|(name, _)| {
                player_configs
                    .iter()
                    .position(|(n, _)| n == name)
                    .expect("Player name not found")
            })
            .collect();

        // Process each trick to create training data
        let mut previous_tricks = Vec::new();
        
        for (trick_number, trick) in game_result.tricks.iter().enumerate() {
            let mut current_trick_cards = Vec::new();
            let mut trick_points = vec![0; 4]; // Track points in current trick
            
            // For each card played in the trick
            for (_i, (card, player_idx)) in trick.cards.iter().enumerate() {
                total_moves += 1;
                
                // Skip if player had bad final score
                if bad_players.contains(player_idx) {
                    excluded_moves += 1;
                    current_trick_cards.push((*card, *player_idx));
                    continue;
                }

                // Calculate points this card would add to the trick
                let card_points = card.score();
                trick_points[*player_idx] += card_points;

                // Skip if this move causes player to score more than 1 point
                if trick_points[*player_idx] > 1 {
                    excluded_moves += 1;
                    current_trick_cards.push((*card, *player_idx));
                    continue;
                }

                // Create a training example for this play
                let training_item = TrainingDataItem {
                    game_id,
                    trick_number,
                    previous_tricks: previous_tricks.clone(),
                    current_trick_cards: current_trick_cards.clone(),
                    current_player_index: *player_idx,
                    played_card: *card,
                };
                training_data.push(training_item);
                
                // Update current trick for next card
                current_trick_cards.push((*card, *player_idx));
            }
            
            // After processing all cards in the trick, add it to previous tricks
            previous_tricks.push(TrainingTrick {
                cards: trick.cards.clone(),
                winner: trick.winner,
            });
        }

        if save_games {
            all_game_results.push(game_result);
        }
    }

    // Create data directory if it doesn't exist
    fs::create_dir_all("data").expect("Failed to create data directory");

    // Generate timestamped filename and save training data
    let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
    let filename = format!("training_data_{}_{}_games.json", timestamp, num_games);
    let filepath = PathBuf::from("data").join(filename);

    let file = File::create(&filepath).expect("Failed to create file");
    let writer = BufWriter::new(file);
    serde_json::to_writer_pretty(writer, &training_data).expect("Failed to write JSON");

    // Save game results if requested
    if save_games {
        let filename = format!("game_results_{}_{}_games.json", timestamp, num_games);
        let filepath = PathBuf::from("data").join(filename);
        
        let file = File::create(&filepath).expect("Failed to create file");
        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, &all_game_results).expect("Failed to write JSON");
        println!("Game results saved to: {}", filepath.display());
    }

    let duration = start.elapsed();
    println!("Time to generate and save training data for {} games: {:?}", num_games, duration);
    println!("Average time per game: {:?}", duration / num_games as u32);
    println!("Total moves: {}", total_moves);
    println!("Excluded moves: {} ({:.1}%)", excluded_moves, (excluded_moves as f64 / total_moves as f64) * 100.0);
    println!("Training examples generated: {}", training_data.len());
    println!("Training data saved to: {}", filepath.display());
}
