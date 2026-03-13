import pytest

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


def test_sentiment_service_rejects_non_string_input():
    service = SentimentService()

    with pytest.raises(ValueError, match="must be a string"):
        service.score_text(None)  # type: ignore[arg-type]


def test_sentiment_service_accepts_custom_thresholds():
    service = SentimentService(positive_threshold=0.2, negative_threshold=-0.2)
    assert service.positive_threshold == 0.2
    assert service.negative_threshold == -0.2


def test_sentiment_service_rejects_invalid_threshold_order():
    with pytest.raises(ValueError, match="must be lower"):
        SentimentService(positive_threshold=0.0, negative_threshold=0.0)


def test_sentiment_service_rejects_out_of_range_thresholds():
    with pytest.raises(ValueError, match="between -1.0 and 1.0"):
        SentimentService(positive_threshold=1.2)

    with pytest.raises(ValueError, match="between -1.0 and 1.0"):
        SentimentService(negative_threshold=-1.2)
