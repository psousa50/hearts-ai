use chrono::Utc;
use hearts_game::{
    AggressiveStrategy, AvoidPointsStrategy, Card, GameResult, HeartsGame, RandomStrategy,
    Strategy, Trick,
};
use rmp_serde;
use std::collections::HashSet;
use std::fs::{self, File};
use std::io::BufWriter;
use std::path::PathBuf;
use std::time::Instant;

use crate::models::CompactTrainingData;

pub fn generate_training_data(num_games: usize, save_games: bool, save_as_json: bool) {
    let start = Instant::now();
    let mut training_data = Vec::new();
    let mut all_game_results = Vec::with_capacity(num_games);

    let player_configs = [
        ("Alice", Strategy::Random(RandomStrategy)),
        ("Bob", Strategy::Random(RandomStrategy)),
        ("Charlie", Strategy::AvoidPoints(AvoidPointsStrategy)),
        ("David", Strategy::Aggressive(AggressiveStrategy)),
    ];

    for _ in 0..num_games {
        let mut game = HeartsGame::new(&player_configs);
        let result = game.play_game();
        training_data.extend(extract_training_data(&result));
        all_game_results.push(result);
    }

    let total_moves = all_game_results.len() * 13 * 4;
    let total_training_moves = training_data.len();
    let excluded_moves = total_moves - total_training_moves;

    // Create data directory if it doesn't exist
    fs::create_dir_all("data").expect("Failed to create data directory");

    // Generate timestamped filename and save training data
    let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
    let filename = format!("training_data_{}_{}_games.msgpack", timestamp, num_games);
    let filepath = PathBuf::from("data").join(filename);

    if save_as_json {
        let filename = format!("training_data_{}_{}_games.json", timestamp, num_games);
        let filepath = PathBuf::from("data").join(filename);

        let file = File::create(&filepath).expect("Failed to create file");
        let mut writer = BufWriter::new(file);
        serde_json::to_writer_pretty(&mut writer, &training_data).expect("Failed to write JSON");
        println!("Training data saved to: {}", filepath.display());
    } else {
        let file = File::create(&filepath).expect("Failed to create file");
        let mut writer = BufWriter::new(file);
        rmp_serde::encode::write(&mut writer, &training_data).expect("Failed to write MessagePack");
    }

    // Save game results if requested
    if save_games {
        if save_as_json {
            let filename = format!("game_results_{}_{}_games.json", timestamp, num_games);
            let filepath = PathBuf::from("data").join(filename);
            let file = File::create(&filepath).expect("Failed to create file");
            let mut writer = BufWriter::new(file);
            serde_json::to_writer_pretty(&mut writer, &all_game_results)
                .expect("Failed to write JSON");
            println!("Game results saved to: {}", filepath.display());
        } else {
            let filename = format!("game_results_{}_{}_games.msgpack", timestamp, num_games);
            let filepath = PathBuf::from("data").join(filename);

            let file = File::create(&filepath).expect("Failed to create file");
            let mut writer = BufWriter::new(file);
            rmp_serde::encode::write(&mut writer, &all_game_results)
                .expect("Failed to write MessagePack");
            println!("Game results saved to: {}", filepath.display());
        }
    }

    let duration = start.elapsed();
    println!(
        "\nTime to generate and save training data for {} games: {:?}",
        num_games, duration
    );
    println!("Average time per game: {:?}", duration / num_games as u32);
    println!("Total moves: {}", total_moves);
    println!(
        "Excluded moves: {} ({:.1}%)",
        excluded_moves,
        (excluded_moves as f64 / total_moves as f64) * 100.0
    );
    println!("Training examples generated: {}", training_data.len());
    println!("Training data saved to: {}", filepath.display());
}

fn extract_training_data(game_result: &GameResult) -> Vec<CompactTrainingData> {
    let mut training_data = Vec::new();
    // Get players with more than 3 points in final score
    let bad_players: HashSet<_> = game_result
        .players
        .iter()
        .enumerate()
        .filter(|(_, p)| p.score > 3)
        .map(|(i, _)| i)
        .collect();

    // Process each trick to create training data
    let mut previous_tricks = Vec::new();

    let mut hands: Vec<Vec<Card>> = game_result
        .players
        .iter()
        .map(|p| p.initial_hand.clone())
        .collect();
    for trick in game_result.tricks.iter() {
        let mut current_trick = Trick::new();
        current_trick.first_player = trick.first_player;

        // For each card played in the trick
        for (player_index, trick_card) in trick.cards.iter().enumerate() {
            let card_idx = hands[player_index]
                .iter()
                .position(|c| c == trick_card)
                .unwrap();
            hands[player_index].remove(card_idx);

            if true || include_move(&bad_players, player_index, trick_card) {
                let training_item = CompactTrainingData {
                    previous_tricks: previous_tricks.clone(),
                    current_trick: current_trick.clone(),
                    current_player_index: player_index,
                    player_hand: hands[player_index].clone(),
                    played_card: trick_card.clone(),
                };
                training_data.push(training_item);
            }

            // Update current trick for next card
            current_trick.add_card(trick_card.clone(), player_index);
        }

        // After processing all cards in the trick, add it to previous tricks
        previous_tricks.push(trick.clone());
    }
    training_data
}

fn include_move(bad_players: &HashSet<usize>, player_index: usize, trick_card: &Card) -> bool {
    // Skip if player had bad final score or this move causes player to score more than 1 point
    !bad_players.contains(&player_index) && trick_card.score() <= 1
}
