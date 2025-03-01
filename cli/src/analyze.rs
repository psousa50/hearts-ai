use hearts_game::GameResult;
use serde_json;
use std::fs::File;

use crate::stats::display_statistics;

pub fn analyze_results(input: &str) {
    let file = File::open(input).expect("Failed to open file");
    let results: Vec<GameResult> = serde_json::from_reader(file).expect("Failed to parse JSON");
    
    println!("\nAnalyzing results from: {}", input);
    println!("Total games analyzed: {}", results.len());
    
    display_statistics(&results);
}
