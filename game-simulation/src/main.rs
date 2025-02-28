mod card;
mod deck;
mod game;
mod player;

use game::{GameResult, GameStats, HeartsGame};
use std::fs::File;
use std::io::BufWriter;
use std::time::Instant;

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
    let num_games = 2;
    let start = Instant::now();

    // Pre-allocate vector to avoid reallocations
    let mut stats = Vec::with_capacity(num_games);
    let player_names = vec!["Alice", "Bob", "Charlie", "David"];

    // Run games
    for game_id in 0..num_games {
        let mut game = HeartsGame::new(player_names.clone());
        let result = game.play_game();
        stats.push(create_game_stats(game_id, &result));
    }

    // Write results efficiently using a buffered writer
    let file = File::create("game_results.json").expect("Failed to create file");
    let writer = BufWriter::new(file);
    serde_json::to_writer(writer, &stats).expect("Failed to write JSON");

    // Display the result of the last game
    if let Some(last_game) = stats.last() {
        display_game_result(last_game);
    }

    let duration = start.elapsed();
    println!("Time to play and save {} games: {:?}", num_games, duration);
    println!("Average time per game: {:?}", duration / num_games as u32);

    // Display summary statistics
    let total_games = stats.len();
    let wins_per_player: std::collections::HashMap<_, _> = stats.iter().map(|s| &s.winner).fold(
        std::collections::HashMap::new(),
        |mut acc, winner| {
            *acc.entry(winner).or_insert(0) += 1;
            acc
        },
    );

    println!("\nWin Statistics:");
    for (player, wins) in wins_per_player {
        println!(
            "{}: {:.1}% ({} wins)",
            player,
            (wins as f64 / total_games as f64) * 100.0,
            wins
        );
    }

    for game in stats {
        display_game_result(&game);
    }
}
