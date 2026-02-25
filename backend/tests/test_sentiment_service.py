from backend.app.services.sentiment import SentimentService


def test_sentiment_service_labels_positive():
    service = SentimentService()
    result = service.score_text("I absolutely love this product")
    assert result["sentiment_label"] == "positive"


def test_sentiment_service_labels_negative():
    service = SentimentService()
    result = service.score_text("This is the worst experience ever")
    assert result["sentiment_label"] == "negative"
