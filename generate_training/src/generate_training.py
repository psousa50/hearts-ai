def generate_training_data():
    parser = argparse.ArgumentParser(description="Generate training data for Hearts game")
    parser.add_argument("--num-games", type=int, default=1, help="Number of games to generate")

    args = parser.parse_args()

    print("Generating training data...")

    players = [
        Player("Random", RandomStrategy()),
        Player("My Strategy", MyStrategy()),
        Player("AvoidPointsStrategy", AvoidPointsStrategy()),
        Player("AggressiveStrategy", AggressiveStrategy()),
    ]

    game_statistics = []
    for player in players:
        game_statistics.append(
            PlayerStatistics(
                player_name=player.name,
                strategy=player.strategy.__class__.__name__,
                total_score=0,
                total_wins=0,
            )
        )

    completed_games = []
    start_time = time.time()
    for i in range(args.num_games):
        deck = Deck()
        game = HeartsGame(players, deck)
        completed_game = game.play_game()
        completed_games.append(completed_game)
        update_statistics(completed_game, game_statistics)

    end_time = time.time()
    print(f"Time taken: {end_time - start_time:.2f} seconds")

    display_statistics(args.num_games, game_statistics)

    save_completed_games(completed_games)

if __name__ == "__main__":
    generate_training_data()

