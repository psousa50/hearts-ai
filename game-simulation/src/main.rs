mod card;
mod deck;
mod game;
mod player;
mod strategy;

use game::{GameResult, GameStats, HeartsGame};
use serde_json;
use std::fs::File;
use std::io::BufWriter;
use std::time::Instant;
use strategy::{AggressiveStrategy, AvoidPointsStrategy, RandomStrategy, Strategy};

fn create_game_stats(game_id: usize, result: &GameResult) -> GameStats {
    let total_points: u8 = result.final_scores.iter().map(|(_, score)| score).sum();

    GameStats {
        game_id,
        winner: result.winner.clone(),
        scores: result.final_scores.clone(),
        tricks: result.tricks.clone(),
        total_points,
    }
}

#[allow(dead_code)]
fn display_card(card: &card::Card) -> String {
    let rank_symbol = match card.rank {
        14 => "A".to_string(),
        13 => "K".to_string(),
        12 => "Q".to_string(),
        11 => "J".to_string(),
        n => n.to_string(),
    };
    format!("{}{}", rank_symbol, card.suit)
}

#[allow(dead_code)]
fn display_game_result(stats: &GameStats) {
    println!("\nGame #{}", stats.game_id);
    println!("Winner: {}", stats.winner);
    println!("\nFinal Scores:");
    for (player, score) in &stats.scores {
        println!("{}: {} points", player, score);
    }
    println!("\nTotal points in game: {}", stats.total_points);

    println!("\nTricks played:");
    for (trick_num, trick) in stats.tricks.iter().enumerate() {
        let cards: Vec<String> = trick
            .cards
            .iter()
            .map(|(card, player_idx)| format!("{}:{}", player_idx, display_card(card)))
            .collect();
        println!("Trick {}: {}", trick_num + 1, cards.join(" | "));
    }
}

fn main() {
    let num_games = 1;
    let start = Instant::now();

    // Pre-allocate vector to avoid reallocations
    let mut stats = Vec::with_capacity(num_games);
    let player_configs = vec![
        ("Alice", Strategy::Random(RandomStrategy)),
        ("Bob", Strategy::Random(RandomStrategy)),
        ("Charlie", Strategy::AvoidPoints(AvoidPointsStrategy)),
        ("David", Strategy::Aggressive(AggressiveStrategy)),
    ];

    // Run games
    for game_id in 0..num_games {
        let mut game = HeartsGame::new_with_strategies(&player_configs);
        let result = game.play_game();
        stats.push(create_game_stats(game_id, &result));
    }

    // Write results efficiently using a buffered writer
    let file = File::create("game_results.json").expect("Failed to create file");
    let writer = BufWriter::new(file);
    serde_json::to_writer(writer, &stats).expect("Failed to write JSON");

    let duration = start.elapsed();
    println!("Time to play and save {} games: {:?}", num_games, duration);
    println!("Average time per game: {:?}", duration / num_games as u32);

    // Display summary statistics
    let total_games = stats.len();
    let wins_per_player: std::collections::HashMap<_, _> = stats.iter().map(|s| &s.winner).fold(
        std::collections::HashMap::new(),
        |mut acc, winner| {
            *acc.entry(winner.to_string()).or_insert(0) += 1;
            acc
        },
    );

    // Calculate average scores per player
    let mut total_scores: std::collections::HashMap<String, (u32, u32)> =
        std::collections::HashMap::new();
    for game in &stats {
        for (name, score) in &game.scores {
            let entry = total_scores.entry(name.clone()).or_insert((0, 0));
            entry.0 += *score as u32;
            entry.1 += 1;
        }
    }

    println!("\nPlayer Statistics:");
    println!(
        "{:<25} | {:>9} | {:>9} | {:>10}",
        "Player (Strategy)", "Win Rate", "Avg Score", "Total Wins"
    );
    println!("--------------------------------------------------------------");
    for (name, strategy) in [
        ("Alice", "Random"),
        ("Bob", "Random"),
        ("Charlie", "Avoid Points"),
        ("David", "Aggressive"),
    ] {
        let wins = wins_per_player.get(name).copied().unwrap_or(0);
        let win_rate = (wins as f64 / total_games as f64) * 100.0;
        let (total_score, games_played) = total_scores.get(name).unwrap_or(&(0, 0));
        let avg_score = if *games_played > 0 {
            *total_score as f64 / *games_played as f64
        } else {
            0.0
        };
        println!(
            "{:<25} | {:>8.1}% | {:>9.1} | {:>10}",
            format!("{} ({})", name, strategy),
            win_rate,
            avg_score,
            wins
        );
    }

    // for game in stats {
    //     display_game_result(&game);
    // }
}
