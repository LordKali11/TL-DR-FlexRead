import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.article import ReadingMode, FlexReadVariant
from backend.app.services.gemini_client import gemini_client_service
from backend.app.services.prompt_engine import prompt_engine

client = TestClient(app)

SAMPLE_RAW_TEXT = """# Federal Reserve Signals Deliberate Approach on Benchmark Interest Rates

The Federal Reserve signaled a deliberate, data-dependent stance regarding upcoming policy adjustments. Central bankers emphasized that inflation metrics remain closely tethered to underlying labor market dynamics and energy volatility.

Recent quarterly prints show a cooling across broad service sectors, while manufactured goods reflect stabilized supply chains. Market observers from major financial institutions in Zurich, Frankfurt, and London noted that persistent wage resilience has kept nominal yields bounded within predictable corridors.

Federal Reserve officials reiterated that restrictive policy rates have performed their intended stabilization role. However, systemic risks, including geopolitical supply chain friction and commercial real estate refinancing cycles, demand careful monitoring rather than abrupt policy shifts.

Academic researchers and institutional treasurers broadly concur that forward guidance must balance price stability objectives against avoidable growth deceleration. As upcoming economic indices are released, financial market participants will scrutinize every phrasing nuance to gauge the terminal velocity of this monetary tightening phase.
"""

def test_reading_mode_aliases():
    """Verify '15 minutes' and 'full' enum parsing and aliases."""
    assert ReadingMode("15 minutes") == ReadingMode.FIFTEEN_MINUTES
    assert ReadingMode("15-minutes") == ReadingMode.FIFTEEN_MINUTES
    assert ReadingMode("15min") == ReadingMode.FIFTEEN_MINUTES
    assert ReadingMode("15") == ReadingMode.FIFTEEN_MINUTES
    assert ReadingMode("fifteen minutes") == ReadingMode.FIFTEEN_MINUTES

    assert ReadingMode("full") == ReadingMode.FULL
    assert ReadingMode("full article") == ReadingMode.FULL
    assert ReadingMode("original") == ReadingMode.FULL

    assert ReadingMode("5 minutes") == ReadingMode.FIVE_MINUTES
    assert ReadingMode("5min") == ReadingMode.FIVE_MINUTES
    assert ReadingMode("10 minutes") == ReadingMode.TEN_MINUTES
    assert ReadingMode("10min") == ReadingMode.TEN_MINUTES

def test_flexread_variant_full_reading_time():
    """Verify FlexReadVariant calculates full reading time at 200 WPM."""
    variant = FlexReadVariant(
        mode=ReadingMode.FULL,
        title="Sample Headline",
        summary="Sample Lead",
        actual_content="One two three four five",
        word_count=1000
    )
    # 1000 words / 200 wpm = 5 minutes
    assert variant.estimated_reading_time_minutes == 5

    variant_large = FlexReadVariant(
        mode=ReadingMode.FULL,
        title="Sample Headline",
        summary="Sample Lead",
        actual_content="One two three four five",
        word_count=3000
    )
    # 3000 words / 200 wpm = 15 minutes
    assert variant_large.estimated_reading_time_minutes == 15

def test_transform_raw_text_full_mode():
    """Verify 'full' mode returns verbatim raw_text and 200 WPM calculation."""
    res = client.post(
        "/api/articles/transform",
        json={
            "raw_text": SAMPLE_RAW_TEXT,
            "target_time_minutes": "full"
        }
    )
    assert res.status_code == 200
    data = res.json()

    assert "title" in data
    assert "summary" in data
    assert "actual_content" in data
    assert "estimated_reading_time_minutes" in data
    assert "word_count" in data

    # Verbatim content preservation in full mode
    assert data["actual_content"] == SAMPLE_RAW_TEXT
    expected_word_count = len(SAMPLE_RAW_TEXT.strip().split())
    assert data["word_count"] == expected_word_count
    assert data["estimated_reading_time_minutes"] == max(1, round(expected_word_count / 200))

def test_transform_raw_text_15_minutes():
    """Verify '15 minutes' mode returns structured output for 15 min."""
    res = client.post(
        "/api/articles/transform",
        json={
            "raw_text": SAMPLE_RAW_TEXT,
            "target_time_minutes": "15 minutes"
        }
    )
    assert res.status_code == 200
    data = res.json()

    assert data["estimated_reading_time_minutes"] == 15
    assert len(data["title"]) > 0
    assert len(data["summary"]) > 0
    assert len(data["actual_content"]) > 0
    assert data["word_count"] > 0

def test_transform_raw_text_5_and_10_minutes():
    """Verify 5 minutes and 10 minutes modes."""
    # 5 minutes
    res_5 = client.post(
        "/api/articles/transform",
        json={
            "raw_text": SAMPLE_RAW_TEXT,
            "target_time_minutes": 5
        }
    )
    assert res_5.status_code == 200
    data_5 = res_5.json()
    assert data_5["estimated_reading_time_minutes"] == 5

    # 10 minutes
    res_10 = client.post(
        "/api/articles/transform",
        json={
            "raw_text": SAMPLE_RAW_TEXT,
            "target_time_minutes": "10 minutes"
        }
    )
    assert res_10.status_code == 200
    data_10 = res_10.json()
    assert data_10["estimated_reading_time_minutes"] == 10

def test_prompt_engine_raw_text_prompt():
    """Verify prompt creation contains required guidelines."""
    prompt = prompt_engine.create_raw_text_prompt(SAMPLE_RAW_TEXT, "15 minutes")
    assert "15-Minute Mode" in prompt
    assert "Full Mode / Full Article" in prompt
    assert "target_time_minutes: 15 minutes" in prompt
    assert "actual_content" in prompt
