use chrono::Utc;
use hearts_game::{AggressiveStrategy, AvoidPointsStrategy, HeartsGame, RandomStrategy, Strategy};
use rmp_serde;
use std::collections::HashSet;
use std::fs::{self, File};
use std::io::BufWriter;
use std::path::PathBuf;
use std::time::Instant;

use crate::models::{Card, CompactTrainingData, CompletedTrick, Trick};

pub fn generate_training_data(num_games: usize, save_games: bool) {
    let start = Instant::now();
    let mut training_data = Vec::new();
    let mut excluded_moves = 0;
    let mut total_moves = 0;

    let player_configs = [
        ("Alice", Strategy::Random(RandomStrategy)),
        ("Bob", Strategy::Random(RandomStrategy)),
        ("Charlie", Strategy::AvoidPoints(AvoidPointsStrategy)),
        ("David", Strategy::Aggressive(AggressiveStrategy)),
    ];

    let mut all_game_results = Vec::with_capacity(num_games);

    for game_id in 0..num_games {
        if game_id % 1000 == 0 {
            println!("\rGenerating game {} of {}", game_id + 1, num_games);
        }
        // Play a full game and record its result
        let mut game = HeartsGame::new(&player_configs, game_id);
        let game_result = game.play_game();

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

        for (trick_number, trick) in game_result.tricks.iter().enumerate() {
            let mut current_trick = Trick::new();
            current_trick.first_player = trick.first_player;
            current_trick.winner = trick.winner;
            current_trick.points = trick.points;
            let mut trick_points = vec![0; 4]; // Track points in current trick

            // For each card played in the trick
            for trick_card in trick.cards.iter() {
                total_moves += 1;

                // Skip if player had bad final score
                if bad_players.contains(&trick_card.player_index) {
                    excluded_moves += 1;
                    current_trick.push(Card {
                        suit: trick_card.card.suit,
                        rank: trick_card.card.rank,
                    });
                    continue;
                }

                // Calculate points this card would add to the trick
                let card_points = if trick_card.card.suit == 'H' {
                    1
                } else if trick_card.card.suit == 'S' && trick_card.card.rank == 12 {
                    13
                } else {
                    0
                };
                trick_points[trick_card.player_index] += card_points;

                // Skip if this move causes player to score more than 1 point
                if trick_points[trick_card.player_index] > 1 {
                    excluded_moves += 1;
                    current_trick.push(Card {
                        suit: trick_card.card.suit,
                        rank: trick_card.card.rank,
                    });
                    continue;
                }

                // Get player's hand at this point
                let mut player_hand = trick_card
                    .hand
                    .iter()
                    .map(|c| Card {
                        suit: c.suit,
                        rank: c.rank,
                    })
                    .collect::<Vec<_>>();
                player_hand.push(Card {
                    suit: trick_card.card.suit,
                    rank: trick_card.card.rank,
                }); // Add back the played card

                // Create a training example for this play
                let training_item = CompactTrainingData {
                    game_id,
                    trick_number,
                    previous_tricks: previous_tricks.clone(),
                    current_trick_cards: current_trick.cards.clone(),
                    current_player_index: trick_card.player_index,
                    player_hand,
                    played_card: Card {
                        suit: trick_card.card.suit,
                        rank: trick_card.card.rank,
                    },
                };
                training_data.push(training_item);

                // Update current trick for next card
                current_trick.push(Card {
                    suit: trick_card.card.suit,
                    rank: trick_card.card.rank,
                });
            }

            // After processing all cards in the trick, add it to previous tricks
            previous_tricks.push(CompletedTrick {
                cards: current_trick.cards.clone(),
                first_player: trick.first_player,
                score: trick.points,
                winner: trick.winner,
            });
        }

        if save_games {
            all_game_results.push(game_result);
        }
    }

    // Create data directory if it doesn't exist
    fs::create_dir_all("data").expect("Failed to create data directory");

    // Generate timestamped filename and save training data
    let timestamp = Utc::now().format("%Y%m%d_%H%M%S");
    let filename = format!("training_data_{}_{}_games.msgpack", timestamp, num_games);
    let filepath = PathBuf::from("data").join(filename);

    let file = File::create(&filepath).expect("Failed to create file");
    let mut writer = BufWriter::new(file);
    rmp_serde::encode::write(&mut writer, &training_data).expect("Failed to write MessagePack");

    // Save game results if requested
    if save_games {
        let filename = format!("game_results_{}_{}_games.msgpack", timestamp, num_games);
        let filepath = PathBuf::from("data").join(filename);

        let file = File::create(&filepath).expect("Failed to create file");
        let mut writer = BufWriter::new(file);
        rmp_serde::encode::write(&mut writer, &all_game_results)
            .expect("Failed to write MessagePack");
        println!("Game results saved to: {}", filepath.display());
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
