import argparse
import json
import os
import signal
import sys

from model_builder import HeartsModel, extract_game_states


def signal_handler(sig, frame):
    print("\nTraining interrupted. Progress has been saved.", flush=True)
    sys.exit(0)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Train Hearts AI model on game data")
    parser.add_argument("training_data_file", help="Path to the training data file")
    parser.add_argument(
        "--batch-size", type=int, help="Override automatic batch size calculation"
    )
    parser.add_argument(
        "--epochs", type=int, help="Override automatic epochs calculation"
    )
    parser.add_argument(
        "--validation-split", type=float, default=0.2, help="Validation split ratio"
    )
    args = parser.parse_args()

    print("Training parameters:")
    print(f"- Training data file: {args.training_data_file}", flush=True)
    print(f"- Batch size: {args.batch_size}", flush=True)
    print(f"- Epochs: {args.epochs}", flush=True)
    print(f"- Validation split: {args.validation_split}\n", flush=True)

    # Check if file exists
    if not os.path.exists(args.training_data_file):
        print(f"Error: File {args.training_data_file} not found!", flush=True)
        return

    import msgpack

    with open(args.training_data_file, "rb") as f:
        raw_data = msgpack.unpackb(f.read(), raw=False)

    print(f"Number of game states in raw data: {len(raw_data)}", flush=True)

    # Register signal handler for graceful interruption
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize model
    print("Initializing model...", flush=True)
    model = HeartsModel()
    model.build_model()
    print("Model initialized!\n", flush=True)

    # Load latest checkpoint if exists
    initial_epoch, _ = model.load_latest_checkpoint()

    # Train model
    try:
        print("Starting training...", flush=True)
        model.train(
            train_data_path=args.training_data_file,
            epochs=args.epochs,  # Will be None if not specified
            batch_size=args.batch_size,  # Will be None if not specified
            validation_split=args.validation_split,
            initial_epoch=initial_epoch,
        )

        print("Training completed!", flush=True)

    except KeyboardInterrupt:
        print("\nTraining interrupted. Progress has been saved.", flush=True)


if __name__ == "__main__":
    main()
