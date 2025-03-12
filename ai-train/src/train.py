import argparse
import os
import signal
import sys

import tensorflow as tf
from transformer_model import HeartsTransformerModel


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
    parser.add_argument(
        "--model-path",
        type=str,
        help="Path to a pre-trained model to continue training",
    )
    args = parser.parse_args()

    print("Training parameters:")
    print(f"- Training data file: {args.training_data_file}", flush=True)
    print(f"- Batch size: {args.batch_size}", flush=True)
    print(f"- Epochs: {args.epochs}", flush=True)
    print(f"- Validation split: {args.validation_split}", flush=True)
    print(
        f"- Pre-trained model: {args.model_path if args.model_path else 'None'}\n",
        flush=True,
    )

    # Check if file exists
    if not os.path.exists(args.training_data_file):
        print(f"Error: File {args.training_data_file} not found!", flush=True)
        return

    # Register signal handler for graceful interruption
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize model
    print("Initializing model...", flush=True)
    model = HeartsTransformerModel()

    if args.model_path:
        print(f"Loading pre-trained model from {args.model_path}", flush=True)
        model.load(args.model_path)
    else:
        print("New model initialized!", flush=True)
        model.build()

        # Load latest checkpoint if exists and no specific model was provided
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
