from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentService:
    POSITIVE_THRESHOLD = 0.05
    NEGATIVE_THRESHOLD = -0.05

    def __init__(self) -> None:
        self.analyzer = SentimentIntensityAnalyzer()

    def score_text(self, text: str) -> dict[str, float | str]:
        if not text.strip():
            return {
                "neg_score": 0.0,
                "neu_score": 1.0,
                "pos_score": 0.0,
                "compound_score": 0.0,
                "sentiment_label": "neutral",
            }

        polarity = self.analyzer.polarity_scores(text)
        compound = float(polarity["compound"])
        if compound > self.POSITIVE_THRESHOLD:
            label = "positive"
        elif compound < self.NEGATIVE_THRESHOLD:
            label = "negative"
        else:
            label = "neutral"

        return {
            "neg_score": float(polarity["neg"]),
            "neu_score": float(polarity["neu"]),
            "pos_score": float(polarity["pos"]),
            "compound_score": compound,
            "sentiment_label": label,
        }
