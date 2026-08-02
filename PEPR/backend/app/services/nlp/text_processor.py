import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException
from textblob import TextBlob
from typing import Dict, Any

try:
    from transformers import pipeline
    # Load a very lightweight multilingual sentiment model if available
    # fallback to TextBlob if loading fails for any reason
    _urdu_sentiment = pipeline("sentiment-analysis", model="lxyuan/distilbert-base-multilingual-cased-sentiments-student", return_all_scores=False)
    HAS_URDU_MODEL = True
except Exception:
    HAS_URDU_MODEL = False

class TextProcessor:
    @staticmethod
    def canonicalize_url(url: str) -> str:
        """Removes tracking parameters to prevent duplicates based on UTM tags."""
        if not url:
            return ""
        try:
            parsed = urlparse(url)
            query = parse_qs(parsed.query)
            # Remove all utm_ parameters
            clean_query = {k: v for k, v in query.items() if not k.startswith('utm_')}
            new_query = urlencode(clean_query, doseq=True)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        except Exception:
            return url

    @staticmethod
    def clean_html(html_content: str) -> str:
        """Strips HTML tags to extract raw text content."""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    @staticmethod
    def detect_language(text: str) -> str:
        """Robust language detection."""
        if not text or len(text.strip()) < 3:
            return "unknown"
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"

    @classmethod
    def analyze_sentiment(cls, text: str, lang: str) -> float:
        """
        Returns sentiment score between -1.0 (very negative) and 1.0 (very positive).
        Uses TextBlob for English, and Transformers for Urdu/Multilingual.
        """
        if not text:
            return 0.0
            
        if lang == 'en':
            return TextBlob(text).sentiment.polarity
            
        if lang == 'ur' and HAS_URDU_MODEL:
            try:
                # The lxyuan model returns labels: 'positive', 'neutral', 'negative'
                result = _urdu_sentiment(text[:512])[0] # Truncate to 512 chars
                label = result['label'].lower()
                score = result['score']
                
                if 'positive' in label:
                    return float(score)
                elif 'negative' in label:
                    return -float(score)
                else:
                    return 0.0
            except Exception:
                return 0.0
                
                # Fallback for unknown or unsupported languages
        return 0.0

    @staticmethod
    def get_source_reliability(url: str) -> float:
        """Assigns a reliability score based on known domain."""
        if not url:
            return 0.5
        domain = urlparse(url).netloc.lower()
        if 'dawn.com' in domain:
            return 0.95
        elif 'tribune.com.pk' in domain:
            return 0.85
        elif 'sbp.org.pk' in domain or 'pbs.gov.pk' in domain:
            return 1.0
        return 0.5

    @classmethod
    def process_article(cls, url: str, html_content: str, title: str) -> Dict[str, Any]:
        """Full pipeline for a single article."""
        clean_url = cls.canonicalize_url(url)
        clean_text = cls.clean_html(html_content)
        
        # Combine title and text for better language/sentiment detection
        full_text = f"{title}. {clean_text}"
        lang = cls.detect_language(full_text)
        sentiment = cls.analyze_sentiment(full_text, lang)
        reliability = cls.get_source_reliability(clean_url)
        
        return {
            "canonical_url": clean_url,
            "clean_text": clean_text,
            "language": lang,
            "sentiment_score": sentiment,
            "source_reliability": reliability
        }
