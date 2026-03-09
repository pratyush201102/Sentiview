from backend.app.services.sentiment import SentimentService


def test_sentiment_service_labels_positive():
    service = SentimentService()
    result = service.score_text("I absolutely love this product")
    assert result["sentiment_label"] == "positive"


def test_sentiment_service_labels_negative():
    service = SentimentService()
    result = service.score_text("This is the worst experience ever")
    assert result["sentiment_label"] == "negative"


def test_sentiment_service_labels_neutral():
    service = SentimentService()
    result = service.score_text("This is a table")
    assert result["sentiment_label"] == "neutral"


def test_sentiment_service_empty_text_returns_neutral_scores():
    service = SentimentService()
    result = service.score_text("   ")
    assert result == {
        "neg_score": 0.0,
        "neu_score": 1.0,
        "pos_score": 0.0,
        "compound_score": 0.0,
        "sentiment_label": "neutral",
    }
