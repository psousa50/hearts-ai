use hearts_game::{AggressiveStrategy, AvoidPointsStrategy, HeartsGame, RandomStrategy, Strategy};
use serde_json;
use std::fs::File;
use std::io::BufWriter;
use std::time::Instant;

use crate::stats::display_statistics;

pub fn generate_games(num_games: usize, output: &str) {
    let start = Instant::now();
    let mut results = Vec::with_capacity(num_games);

    let player_configs = [
        ("Alice", Strategy::Random(RandomStrategy)),
        ("Bob", Strategy::Random(RandomStrategy)),
        ("Charlie", Strategy::AvoidPoints(AvoidPointsStrategy)),
        ("David", Strategy::Aggressive(AggressiveStrategy)),
    ];

    for game_id in 0..num_games {
        let mut game = HeartsGame::new_with_strategies(&player_configs, game_id);
        let result = game.play_game();
        results.push(result);
    }

    // Save results to file
    let file = File::create(output).expect("Failed to create file");
    let writer = BufWriter::new(file);
    serde_json::to_writer(writer, &results).expect("Failed to write JSON");

    let duration = start.elapsed();
    println!("Time to play and save {} games: {:?}", num_games, duration);
    println!("Average time per game: {:?}", duration / num_games as u32);

    display_statistics(&results);
}
