import logging
from typing import Literal

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class SentimentService:
    """
    VADER-based sentiment analysis service for scoring text.
    
    Attributes:
        POSITIVE_THRESHOLD: Compound score threshold for positive sentiments (default: 0.05)
        NEGATIVE_THRESHOLD: Compound score threshold for negative sentiments (default: -0.05)
        analyzer: VADER SentimentIntensityAnalyzer instance
    """
    
    POSITIVE_THRESHOLD = 0.05
    NEGATIVE_THRESHOLD = -0.05

    def __init__(
        self,
        positive_threshold: float = POSITIVE_THRESHOLD,
        negative_threshold: float = NEGATIVE_THRESHOLD,
    ) -> None:
        """Initialize VADER sentiment analyzer and scoring thresholds."""
        self.positive_threshold = float(positive_threshold)
        self.negative_threshold = float(negative_threshold)

        if not -1.0 <= self.negative_threshold <= 1.0:
            raise ValueError("negative_threshold must be between -1.0 and 1.0")

        if not -1.0 <= self.positive_threshold <= 1.0:
            raise ValueError("positive_threshold must be between -1.0 and 1.0")

        if self.negative_threshold >= self.positive_threshold:
            raise ValueError("negative_threshold must be lower than positive_threshold")

        self.analyzer = SentimentIntensityAnalyzer()
        logger.debug(
            "SentimentService initialized with VADER analyzer "
            "(negative_threshold=%s, positive_threshold=%s)",
            self.negative_threshold,
            self.positive_threshold,
        )

    def score_text(self, text: str) -> dict[str, float | Literal["positive", "negative", "neutral"]]:
        """
        Analyze sentiment of given text using VADER algorithm.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing:
                - neg_score: Negative sentiment proportion (0-1)
                - neu_score: Neutral sentiment proportion (0-1)
                - pos_score: Positive sentiment proportion (0-1)
                - compound_score: Normalized compound sentiment score (-1 to 1)
                - sentiment_label: Classification as 'positive', 'negative', or 'neutral'
                
        Raises:
            ValueError: If text parameter is not a string
        """
        if not isinstance(text, str):
            logger.warning(f"Non-string input received: {type(text)}")
            raise ValueError("Text input must be a string")
            
        if not text.strip():
            logger.debug("Empty text provided, returning neutral scores")
            return {
                "neg_score": 0.0,
                "neu_score": 1.0,
                "pos_score": 0.0,
                "compound_score": 0.0,
                "sentiment_label": "neutral",
            }

        try:
            polarity = self.analyzer.polarity_scores(text)
            compound = float(polarity["compound"])
            
            if compound > self.positive_threshold:
                label = "positive"
            elif compound < self.negative_threshold:
                label = "negative"
            else:
                label = "neutral"

            result = {
                "neg_score": float(polarity["neg"]),
                "neu_score": float(polarity["neu"]),
                "pos_score": float(polarity["pos"]),
                "compound_score": compound,
                "sentiment_label": label,
            }
            
            logger.debug(f"Sentiment analyzed: {label} (compound={compound:.4f})")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}", exc_info=True)
            raise
