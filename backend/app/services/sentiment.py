from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentService:
    def __init__(self) -> None:
        self.analyzer = SentimentIntensityAnalyzer()

    def score_text(self, text: str) -> dict[str, float | str]:
        polarity = self.analyzer.polarity_scores(text)
        compound = float(polarity["compound"])
        if compound > 0.05:
            label = "positive"
        elif compound < -0.05:
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
