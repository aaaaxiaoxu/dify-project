import os
import sys
import unittest


BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from routes.ai import analyze_emotion
from utils.sentiment import analyze_emotion_rules, evaluate_sentiment_samples


class SentimentRuleTest(unittest.TestCase):
    def test_negation_flips_positive_word(self):
        label, _analysis, score = analyze_emotion("今天并不开心，服务也让人失望。")

        self.assertEqual(label, "消极")
        self.assertLess(score, -0.2)

    def test_degree_adverb_amplifies_weight(self):
        mild = analyze_emotion_rules("这里有点开心。")
        strong = analyze_emotion_rules("这里非常开心。")

        self.assertGreater(strong["evidence"][0]["weight"], mild["evidence"][0]["weight"])

    def test_eval_dataset_reaches_expected_metrics(self):
        metrics = evaluate_sentiment_samples()

        self.assertGreaterEqual(metrics["accuracy"], 0.8)
        self.assertGreaterEqual(metrics["macro_f1"], 0.8)


if __name__ == "__main__":
    unittest.main()
