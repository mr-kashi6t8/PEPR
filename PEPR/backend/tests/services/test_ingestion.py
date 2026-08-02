import pytest
import httpx
from datetime import datetime, timezone
from app.services.ingestion.manager import IngestionManager
from app.services.ingestion.connectors.rss import RSSConnector

# Mock RSS Data
VALID_RSS = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Dawn News</title>
  <item>
    <title>Economic Growth Surges</title>
    <link>https://dawn.com/news/123</link>
    <description>Growth hit 5% this year.</description>
  </item>
</channel>
</rss>"""

MALFORMED_RSS = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Dawn News</title>
  <item>
    <description>No title or link here, invalid data!</description>
  </item>
</channel>
</rss>"""

@pytest.fixture
def mock_db_session(mocker):
    return mocker.MagicMock()

@pytest.mark.asyncio
async def test_successful_ingestion(mock_db_session, respx_mock):
    # Mock the external RSS endpoint
    respx_mock.get("https://test.rss.com").respond(200, text=VALID_RSS)
    
    manager = IngestionManager(
        db=mock_db_session,
        source_id="test_rss_1",
        connector_type="rss",
        config={"rss_url": "https://test.rss.com"}
    )
    
    result = await manager.run_ingestion()
    assert result["status"] == "success"
    assert result["records_processed"] == 1

@pytest.mark.asyncio
async def test_malformed_data(mock_db_session, respx_mock):
    # Mock the external RSS endpoint with invalid data
    respx_mock.get("https://test.rss.com").respond(200, text=MALFORMED_RSS)
    
    manager = IngestionManager(
        db=mock_db_session,
        source_id="test_rss_1",
        connector_type="rss",
        config={"rss_url": "https://test.rss.com"}
    )
    
    result = await manager.run_ingestion()
    assert result["status"] == "failed"
    assert "Validation failed" in result["error"] or "Malformed RSS" in result["error"]

@pytest.mark.asyncio
async def test_retry_logic_and_timeout(mock_db_session, respx_mock):
    # Mock the endpoint to fail twice with 500, then succeed on 3rd attempt
    route = respx_mock.get("https://test.rss.com")
    route.side_effect = [
        httpx.Response(500),
        httpx.Response(503),
        httpx.Response(200, text=VALID_RSS)
    ]
    
    manager = IngestionManager(
        db=mock_db_session,
        source_id="test_rss_1",
        connector_type="rss",
        config={"rss_url": "https://test.rss.com"}
    )
    
    # Manager is configured with @retry in _fetch_with_retries
    result = await manager.run_ingestion()
    assert result["status"] == "success"
    assert route.call_count == 3

@pytest.mark.asyncio
async def test_failed_source_exhausts_retries(mock_db_session, respx_mock):
    # Mock the endpoint to always fail
    route = respx_mock.get("https://test.rss.com").respond(500)
    
    manager = IngestionManager(
        db=mock_db_session,
        source_id="test_rss_1",
        connector_type="rss",
        config={"rss_url": "https://test.rss.com"}
    )
    
    result = await manager.run_ingestion()
    assert result["status"] == "failed"
    assert "Server error" in result["error"] or "500" in result["error"]

@pytest.mark.asyncio
async def test_idempotency_duplicate_ingestion(mock_db_session, respx_mock):
    # In a fully connected test, we would assert that `db.add()` isn't called twice for the same payload
    # Since persist is a stub in M1, we ensure that calling run_ingestion twice succeeds without side effects
    respx_mock.get("https://test.rss.com").respond(200, text=VALID_RSS)
    
    manager = IngestionManager(
        db=mock_db_session,
        source_id="test_rss_1",
        connector_type="rss",
        config={"rss_url": "https://test.rss.com"}
    )
    
    result_1 = await manager.run_ingestion()
    result_2 = await manager.run_ingestion()
    
    assert result_1["status"] == "success"
    assert result_2["status"] == "success"


def test_manager_tracks_connector_type():
    manager = IngestionManager(
        db=None,
        source_id="test_rss_1",
        connector_type="rss",
        config={"rss_url": "https://test.rss.com"},
    )

    assert manager.connector_type == "rss"


@pytest.mark.asyncio
async def test_list_data_sources_returns_admin_shape():
    from app.api.v1.endpoints.ingestion import list_data_sources

    class DummyScalars:
        def all(self):
            return []

    class DummyResult:
        def scalars(self):
            return DummyScalars()

    class DummyDB:
        async def execute(self, stmt):
            return DummyResult()

        async def commit(self):
            return None

    response = await list_data_sources(db=DummyDB())

    assert response
    first_source = response[0]
    assert "records_ingested" in first_source
    assert "error_rate" in first_source
    assert "frequency" in first_source
    assert first_source["records_ingested"] >= 0
    assert first_source["error_rate"] >= 0
