use chrono::Utc;
use hearts_game::{
    AIStrategy, AggressiveStrategy, HeartsGame, MyStrategy, RandomStrategy, Strategy,
};
use serde_json;
use std::fs::{self, File};
use std::io::BufWriter;
use std::path::PathBuf;
use std::time::Instant;

use crate::stats::display_statistics;

pub fn generate_games(num_games: usize) {
    let start = Instant::now();
    let mut results = Vec::with_capacity(num_games);

    let ai_strategy = AIStrategy::new("http://localhost:8000/predict".to_string());
    let player_configs = [
        ("Alice", Strategy::Random(RandomStrategy)),
        // ("Bob", Strategy::Random(RandomStrategy)),
        ("Bob", Strategy::AI(ai_strategy)),
        ("My", Strategy::My(MyStrategy)),
        ("David", Strategy::Aggressive(AggressiveStrategy)),
    ];

    for _ in 0..num_games {
        let mut game = HeartsGame::new(&player_configs);
        game.play_game();
        results.push(game.completed_game());
    }

    // Create data directory if it doesn't exist
    fs::create_dir_all("data").expect("Failed to create data directory");

    // Generate timestamped filename
    let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
    let filename = format!("game_results_{}_{}_games.json", timestamp, num_games);
    let filepath = PathBuf::from("data").join(filename);

    // Save results to file
    let file = File::create(&filepath).expect("Failed to create file");
    let writer = BufWriter::new(file);
    serde_json::to_writer_pretty(writer, &results).expect("Failed to write JSON");

    let duration = start.elapsed();
    println!("Time to play and save {} games: {:?}", num_games, duration);
    println!("Average time per game: {:?}", duration / num_games as u32);
    println!("Data saved to: {}", filepath.display());

    display_statistics(&results);
}
