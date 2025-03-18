use hearts_game::CompletedHeartsGame;
use std::collections::HashMap;

pub fn display_statistics(games: &[CompletedHeartsGame]) {
    let mut total_scores: HashMap<(&String, &String), u32> = HashMap::new();
    let mut total_wins = HashMap::new();

    // Collect statistics
    for game in games {
        // Update total scores
        for player in &game.players {
            let entry = total_scores
                .entry((&player.name, &player.strategy))
                .or_insert(0);
            *entry += player.score as u32;
        }

        // Update win counts
        let winner = &game.players[game.winner_index];
        let entry = total_wins
            .entry((&winner.name, &winner.strategy))
            .or_insert(0);
        *entry += 1;
    }

    // Prepare data for sorted display
    let mut player_stats: Vec<_> = total_scores
        .iter()
        .map(|((name, strategy), total_score)| {
            let wins = total_wins.get(&(name, strategy)).unwrap_or(&0);
            let win_rate = (*wins as f64 / games.len() as f64) * 100.0;
            let avg_score = *total_score as f64 / games.len() as f64;
            (name, strategy, win_rate, avg_score, wins)
        })
        .collect();

    // Sort by win rate (highest first)
    player_stats.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap());

    // Calculate and display statistics
    println!("\nPlayer Statistics:");
    println!("Player (Strategy)         |  Win Rate | Avg Score | Total Wins");
    println!("--------------------------------------------------------------");

    for (name, strategy, win_rate, avg_score, wins) in player_stats {
        println!(
            "{:<25} |    {:>5.1}% |     {:>5.1} |         {:>2}",
            format!("{} ({})", name, strategy),
            win_rate,
            avg_score,
            wins
        );
    }
}
