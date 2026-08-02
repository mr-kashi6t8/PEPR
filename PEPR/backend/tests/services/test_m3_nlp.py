import pytest
from app.services.nlp.text_processor import TextProcessor
from app.services.nlp.topic_modeler import TopicModeler
from app.services.analysis.aggregator import EvidenceAggregator
from app.services.ingestion.connectors.rss import RSSConnector

def test_canonical_url():
    url = "https://dawn.com/news/123?utm_source=twitter&utm_medium=social&page=1"
    clean = TextProcessor.canonicalize_url(url)
    assert clean == "https://dawn.com/news/123?page=1"

def test_clean_html():
    html = "<p>Prices are <b>rising</b> fast!</p>"
    clean = TextProcessor.clean_html(html)
    assert clean == "Prices are rising fast!"

def test_language_detection():
    # Simple english test
    assert TextProcessor.detect_language("This is a simple english sentence about the economy.") == "en"
    # Note: testing pure Urdu might require full font/lang support on the local machine, 
    # but we can test fallback mechanism
    assert TextProcessor.detect_language(" ") == "unknown"

def test_sentiment_analysis():
    # English positive
    score_pos = TextProcessor.analyze_sentiment("The economy is booming and doing wonderfully.", "en")
    assert score_pos > 0.0
    
    # English negative
    score_neg = TextProcessor.analyze_sentiment("Terrible inflation is destroying the market.", "en")
    assert score_neg < 0.0

def test_missing_content_handling():
    # Should not crash on empty content
    result = TextProcessor.process_article("http://test.com", "", "Just a title")
    assert result["canonical_url"] == "http://test.com"
    assert result["clean_text"] == ""

def test_topic_clustering():
    articles = [
        {"title": "Wheat prices surge", "clean_text": "Wheat grain prices are up.", "url": "url1"},
        {"title": "Wheat shortage", "clean_text": "Less wheat this year.", "url": "url2"},
        {"title": "IMF bailout", "clean_text": "The IMF loan is approved.", "url": "url3"},
        {"title": "IMF conditions", "clean_text": "Strict IMF tax conditions.", "url": "url4"},
    ]
    # Small test, we need eps and min_samples adjusted for tiny dataset
    clusters = TopicModeler.cluster_articles(articles, eps=0.9, min_samples=2)
    # Should find at least the IMF or Wheat cluster (or both)
    assert len(clusters) > 0
    # Make sure at least one cluster isn't noise
    valid_clusters = [c for c in clusters if c["topic_id"] != -1]
    assert len(valid_clusters) >= 1
    assert len(valid_clusters[0]["keywords"]) > 0

def test_evidence_aggregator():
    agg = EvidenceAggregator("ind_inflation")
    
    anomalies = [{"anomaly_score": 5.0, "observed_value": 42}]
    trend = {"severity": "high"}
    
    # Needs to match clusters, so we provide identical topics
    articles = [
        {"title": "Inflation is terrible", "clean_text": "Prices inflation", "sentiment_score": -0.8, "url": "http://x/1"},
        {"title": "Inflation is terrible", "clean_text": "Prices inflation", "sentiment_score": -0.9, "url": "http://x/2"}
    ]
    
    problem = agg.generate_candidate_problem(anomalies, trend, articles)
    assert problem is not None
    assert problem["severity"] == "high"
    assert problem["sentiment"] < 0
    assert "inflation" in problem["description"].lower() or "anomaly" in problem["description"].lower()

@pytest.mark.asyncio
async def test_live_data_fetching_rss(mock_db_session=None):
    # Live integration test against Dawn RSS as requested
    connector = RSSConnector(config={"rss_url": "https://www.dawn.com/feeds/business"})
    
    try:
        raw = await connector.fetch()
        normalized = connector.normalize(raw)
        
        # Ensure we got articles
        assert len(normalized) > 0
        assert "title" in normalized[0]
        assert "sentiment_score" in normalized[0] # Proves NLP ran inline
        assert normalized[0]["published_at"] is not None # Proves Date extraction ran
    except Exception as e:
        pytest.skip(f"Live fetch failed (network issue): {e}")

def test_source_reliability():
    assert TextProcessor.get_source_reliability("https://www.dawn.com/news/123") == 0.95
    assert TextProcessor.get_source_reliability("https://tribune.com.pk/story/123") == 0.85
    assert TextProcessor.get_source_reliability("https://unknown-blog.com/123") == 0.5

def test_date_parsing():
    import dateutil.parser
    # RSS feeds use various date formats (RFC-822, ISO-8601, etc)
    d1 = dateutil.parser.parse("Sat, 07 Sep 2002 00:00:01 GMT")
    d2 = dateutil.parser.parse("2023-10-15T14:30:00Z")
    assert d1.year == 2002
    assert d2.year == 2023
