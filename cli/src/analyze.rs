use hearts_game::GameResult;
use serde_json;
use std::fs;

use crate::stats::display_statistics;

pub fn analyze_results(input_file: &str) {
    let file_content = fs::read_to_string(input_file).expect("Failed to read file");
    let results: Vec<GameResult> = serde_json::from_str(&file_content).expect("Failed to parse JSON");

    display_statistics(&results);
}
