use hearts_game::GameResult;
use std::collections::HashMap;

pub fn display_statistics(results: &[GameResult]) {
    let total_games = results.len();
    let wins_per_player: HashMap<_, _> = results.iter().map(|s| &s.winner).fold(
        HashMap::new(),
        |mut acc, winner| {
            *acc.entry(winner.to_string()).or_insert(0) += 1;
            acc
        },
    );

    // Calculate average scores per player
    let mut total_scores: HashMap<String, (u32, u32)> = HashMap::new();
    for game in results {
        for (name, score) in &game.final_scores {
            let entry = total_scores.entry(name.clone()).or_insert((0, 0));
            entry.0 += *score as u32;
            entry.1 += 1;
        }
    }

    println!("\nPlayer Statistics:");
    println!("{:<25} | {:>9} | {:>9} | {:>10}", "Player (Strategy)", "Win Rate", "Avg Score", "Total Wins");
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
}
