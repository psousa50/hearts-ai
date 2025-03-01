use std::collections::HashMap;
use hearts_game::GameResult;

pub fn display_statistics(games: &[&GameResult]) {
    let mut total_scores = HashMap::new();
    let mut total_wins = HashMap::new();

    // Collect statistics
    for game in games {
        // Update total scores
        for player in &game.players {
            let entry = total_scores.entry((&player.name, &player.strategy)).or_insert(0);
            *entry += player.score;
        }

        // Update win counts
        let winner = &game.players[game.winner];
        let entry = total_wins.entry((&winner.name, &winner.strategy)).or_insert(0);
        *entry += 1;
    }

    // Calculate and display statistics
    println!("\nPlayer Statistics:");
    println!("Player (Strategy)         |  Win Rate | Avg Score | Total Wins");
    println!("--------------------------------------------------------------");

    for ((name, strategy), total_score) in total_scores.iter() {
        let wins = total_wins.get(&(name, strategy)).unwrap_or(&0);
        let win_rate = (*wins as f64 / games.len() as f64) * 100.0;
        let avg_score = *total_score as f64 / games.len() as f64;

        println!(
            "{:<20} |    {:>5.1}% |     {:>5.1} |         {:>2}",
            format!("{} ({})", name, strategy),
            win_rate,
            avg_score,
            wins
        );
    }
}
