use serde::Serialize;

#[derive(Serialize, Clone)]
pub struct CompactCard(pub char, pub u8);

#[derive(Clone, Serialize)]
pub struct CompactTrick {
    pub cards: Vec<Option<CompactCard>>,
    pub first_player: usize,
}

#[derive(Clone, Serialize)]
pub struct CompactCompletedTrick {
    pub cards: Vec<CompactCard>,
    pub winner: usize,
    pub points: u8,
    pub first_player: usize,
}

#[derive(Clone, Serialize)]
pub struct CompactTrainingData {
    pub previous_tricks: Vec<CompactCompletedTrick>,
    pub current_trick: CompactTrick,
    pub current_player_index: usize,
    pub player_hand: Vec<CompactCard>,
    pub played_card: CompactCard,
}
