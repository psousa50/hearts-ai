use chrono::Utc;
use hearts_game::{
    AIStrategy, AggressiveStrategy, Deck, HeartsGame, MyStrategy, RandomStrategy, Strategy,
};
use serde_json;
use std::fs::{self, File};
use std::io::BufWriter;
use std::path::PathBuf;
use std::time::Instant;

use crate::stats::display_statistics;

pub fn generate_games(num_games: usize, use_same_deck_for_all_players: bool) {
    println!(
        "Generating {} games using {}...",
        num_games,
        if use_same_deck_for_all_players {
            "same deck"
        } else {
            "random decks"
        }
    );
    let start = Instant::now();

    let ai_strategy = AIStrategy::new("http://localhost:8000/predict".to_string());
    let player_configs = [
        ("Alice", Strategy::Random(RandomStrategy)),
        ("Bob", Strategy::Random(RandomStrategy)),
        ("My", Strategy::My(MyStrategy)),
        ("David", Strategy::Aggressive(AggressiveStrategy)),
    ];

    let results = if use_same_deck_for_all_players {
        generate_with_same_deck(num_games, &player_configs)
    } else {
        generate_with_random_decks(num_games, &player_configs)
    };

    save_results(num_games, &results);

    let duration = start.elapsed();
    println!("Time to play and save {} games: {:?}", num_games, duration);
    println!("Average time per game: {:?}", duration / num_games as u32);

    display_statistics(&results);
}

fn generate_with_random_decks(
    num_games: usize,
    player_configs: &[(&str, Strategy)],
) -> Vec<hearts_game::CompletedHeartsGame> {
    let mut results = Vec::with_capacity(num_games);
    for _ in 0..num_games {
        let mut game = HeartsGame::new(&player_configs);
        game.play_game();
        results.push(game.completed_game());
    }
    results
}

fn generate_with_same_deck(
    num_games: usize,
    player_configs: &[(&str, Strategy)],
) -> Vec<hearts_game::CompletedHeartsGame> {
    let mut results = Vec::with_capacity(num_games);
    let mut game_index = 0;
    let mut current_deck = Deck::new(None);

    for _ in 0..num_games {
        let mut game = HeartsGame::new_with_deck(player_configs, Some(current_deck.clone()));
        game.play_game();
        results.push(game.completed_game());

        game_index += 1;
        if game_index % 4 == 0 {
            current_deck = Deck::new(None);
        } else {
            current_deck = current_deck.rotate(13);
        }
    }
    results
}

fn save_results(num_games: usize, results: &Vec<hearts_game::CompletedHeartsGame>) {
    // Create data directory if it doesn't exist
    fs::create_dir_all("data").expect("Failed to create data directory");

    // Generate timestamped filename
    let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
    let filename = format!("game_results_{}_{}_games.json", timestamp, num_games);
    let filepath = PathBuf::from("data").join(filename);

    // Save results to file
    let file = File::create(&filepath).expect("Failed to create file");
    let writer = BufWriter::new(file);
    serde_json::to_writer_pretty(writer, results).expect("Failed to write JSON");

    println!("Data saved to: {}", filepath.display());
}
