use crate::models::CompactCard;
use chrono::Utc;
use hearts_game::{
    AggressiveStrategy, AvoidPointsStrategy, Card, CompletedHeartsGame, HeartsGame, RandomStrategy,
    Strategy, Trick,
};
use rmp_serde;
use std::fs::{self, File};
use std::io::BufWriter;
use std::path::PathBuf;
use std::time::Instant;

use crate::game_moves_filter::GameMovesFilter;

use crate::models::{CompactCompletedTrick, CompactTrainingData, CompactTrick};

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
        game.play_game();
        let completed_game = game.completed_game();
        training_data.extend(extract_training_data(&completed_game));
        all_game_results.push(completed_game);
    }

    let total_moves = all_game_results.len() * 13 * 4;
    let total_training_moves = training_data.len();
    let excluded_moves = total_moves - total_training_moves;

    // Create data directory if it doesn't exist
    fs::create_dir_all("data").expect("Failed to create data directory");

    let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
    if save_as_json {
        let filename = format!("training_data_{}_{}_games.json", timestamp, num_games);
        let filepath = PathBuf::from("data").join(filename);

        let file = File::create(&filepath).expect("Failed to create file");
        let mut writer = BufWriter::new(file);
        serde_json::to_writer_pretty(&mut writer, &training_data).expect("Failed to write JSON");
        println!("Training data saved to: {}", filepath.display());
    }
    let filename = format!("training_data_{}_{}_games.msgpack", timestamp, num_games);
    let filepath = PathBuf::from("data").join(filename);
    let file = File::create(&filepath).expect("Failed to create file");
    let mut writer = BufWriter::new(file);
    rmp_serde::encode::write(&mut writer, &training_data).expect("Failed to write MessagePack");

    // Save game results if requested
    if save_games {
        if save_as_json {
            let filename = format!("game_results_{}_{}_games.json", timestamp, num_games);
            let filepath = PathBuf::from("data").join(filename);
            let file = File::create(&filepath).expect("Failed to create file");
            let mut writer = BufWriter::new(file);
            serde_json::to_writer_pretty(&mut writer, &all_game_results)
                .expect("Failed to write JSON");
            println!("Training data saved to: {}", filepath.display());
        } else {
            let filename = format!("game_results_{}_{}_games.msgpack", timestamp, num_games);
            let filepath = PathBuf::from("data").join(filename);

            let file = File::create(&filepath).expect("Failed to create file");
            let mut writer = BufWriter::new(file);
            rmp_serde::encode::write(&mut writer, &all_game_results)
                .expect("Failed to write MessagePack");
            println!("Training data saved to: {}", filepath.display());
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
}

fn extract_training_data(completed_game: &CompletedHeartsGame) -> Vec<CompactTrainingData> {
    let mut training_data = Vec::new();

    let game_moves_filter = GameMovesFilter::new(completed_game);

    let mut previous_tricks = Vec::new();

    let mut hands: Vec<Vec<Card>> = completed_game
        .players
        .iter()
        .map(|p| p.initial_hand.clone())
        .collect();

    for trick in completed_game.previous_tricks.iter() {
        let mut current_trick = Trick::new();
        current_trick.first_player_index = trick.first_player_index;

        for (p, trick_card) in trick.cards_starting_first_player().iter().enumerate() {
            let player_index = (trick.first_player_index + p) % 4;
            let card_idx = hands[player_index]
                .iter()
                .position(|c| c == trick_card)
                .unwrap();
            hands[player_index].remove(card_idx);
            current_trick.add_card(trick_card.clone(), player_index);

            if game_moves_filter.filter(player_index, trick) {
                let training_item = CompactTrainingData {
                    previous_tricks: previous_tricks.clone(),
                    current_trick: CompactTrick {
                        cards: current_trick
                            .cards
                            .iter()
                            .map(|c| c.map(|c| CompactCard(c.suit, c.rank)))
                            .collect(),
                        first_player_index: trick.first_player_index,
                    },
                    current_player_index: player_index,
                    player_hand: hands[player_index]
                        .iter()
                        .map(|c| CompactCard(c.suit, c.rank))
                        .collect(),
                    played_card: CompactCard(trick_card.suit, trick_card.rank),
                };
                training_data.push(training_item);
            }

            current_trick.add_card(trick_card.clone(), player_index);
        }

        previous_tricks.push(CompactCompletedTrick {
            cards: trick
                .cards
                .iter()
                .map(|c| CompactCard(c.suit, c.rank))
                .collect(),
            winner: trick.winner_index,
            points: trick.score,
            first_player_index: trick.first_player_index,
        });
    }
    training_data
}
