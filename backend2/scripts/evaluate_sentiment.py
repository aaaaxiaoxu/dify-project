import argparse
import json
import os
import sys


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from utils.sentiment import evaluate_sentiment_samples, load_sentiment_eval_samples


def main():
    parser = argparse.ArgumentParser(description="Evaluate local rule-based sentiment analyzer.")
    parser.add_argument(
        "--sample-path",
        default=None,
        help="Path to a JSON sample file. Defaults to backend2/data/sentiment_eval_samples.json.",
    )
    args = parser.parse_args()

    samples = load_sentiment_eval_samples(args.sample_path) if args.sample_path else None
    metrics = evaluate_sentiment_samples(samples)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
