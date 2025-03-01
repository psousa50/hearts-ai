mod analyze;
mod generate;
mod stats;

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
        
        /// Output file for game results
        #[arg(short, long, default_value = "game_results.json")]
        output: String,
    },
    
    /// Analyze existing game results
    AnalyzeResults {
        /// Input file containing game results
        #[arg(short, long, default_value = "game_results.json")]
        input: String,
    },
}

fn main() {
    let cli = Cli::parse();

    match &cli.command {
        Commands::GenerateGames { num_games, output } => {
            generate::generate_games(*num_games, output);
        }
        Commands::AnalyzeResults { input } => {
            analyze::analyze_results(input);
        }
    }
}
