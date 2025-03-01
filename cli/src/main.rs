mod analyze;
mod generate;
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
    
    /// Analyze existing game results
    AnalyzeResults {
        /// Input file containing game results
        #[arg(short, long, default_value = "game_results.json")]
        input: String,
    },

    /// Generate AI training data from simulated games
    GenerateAiTrainingData {
        /// Number of games to simulate
        #[arg(short, long, default_value_t = 1)]
        num_games: usize,

        /// Also save game results to a separate file
        #[arg(short, long)]
        save_games: bool,
    },
}

fn main() {
    let cli = Cli::parse();

    match &cli.command {
        Commands::GenerateGames { num_games } => {
            generate::generate_games(*num_games);
        }
        Commands::AnalyzeResults { input } => {
            analyze::analyze_results(input);
        }
        Commands::GenerateAiTrainingData { num_games, save_games } => {
            training::generate_training_data(*num_games, *save_games);
        }
    }
}
