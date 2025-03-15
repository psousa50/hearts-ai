mod game_moves_filter;
mod generate;
mod models;
mod stats;
mod training;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate and run games with specified parameters
    GenerateGames {
        /// Number of games to simulate
        #[arg(short, long, default_value_t = 1)]
        num_games: usize,
    },

    /// Generate AI training data from simulated games
    GenerateAiTrainingData {
        /// Number of games to simulate
        #[arg(short, long, default_value_t = 1)]
        num_games: usize,

        /// Also save game results to a separate file
        #[arg(short, long)]
        save_games: bool,

        /// Also save training data to a separate file
        #[arg(short = 'j', long)]
        save_as_json: bool,
    },
}

fn main() {
    let cli = Cli::parse();

    match &cli.command {
        Commands::GenerateGames { num_games } => {
            generate::generate_games(*num_games);
        }
        Commands::GenerateAiTrainingData {
            num_games,
            save_games,
            save_as_json,
        } => {
            training::generate_training_data(*num_games, *save_games, *save_as_json);
        }
    }
}
