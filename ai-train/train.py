import os
import argparse
from model import HeartsModel
import signal
import sys

def signal_handler(sig, frame):
    print('\nTraining interrupted. Progress has been saved.')
    sys.exit(0)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Train Hearts AI model on game data')
    parser.add_argument('json_file', help='Path to the training data JSON file')
    parser.add_argument('--batch-size', type=int, help='Override automatic batch size calculation')
    parser.add_argument('--epochs', type=int, help='Override automatic epochs calculation')
    parser.add_argument('--validation-split', type=float, default=0.2, help='Validation split ratio')
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.json_file):
        print(f"Error: File {args.json_file} not found!")
        return
    
    # Register signal handler for graceful interruption
    signal.signal(signal.SIGINT, signal_handler)
    
    # Initialize model
    model = HeartsModel()
    model.build_model()
    
    # Load latest checkpoint if exists
    initial_epoch, _ = model.load_latest_checkpoint()
    
    # Train model
    try:
        print("Starting training...")
        model.train(
            train_data_path=args.json_file,
            epochs=args.epochs,  # Will be None if not specified
            batch_size=args.batch_size,  # Will be None if not specified
            validation_split=args.validation_split,
            initial_epoch=initial_epoch
        )
        
        print("Training completed!")
        
    except KeyboardInterrupt:
        print("\nTraining interrupted. Progress has been saved.")
    
if __name__ == "__main__":
    main()
