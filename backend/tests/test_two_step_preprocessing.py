import json
from unittest.mock import MagicMock
import pytest
from backend.app.models.article import Article, ArticlePreprocessing, FlexReadVariant, ReadingMode, ToneCategory, LengthTier
from backend.app.services.prompt_engine import prompt_engine
from backend.app.services.gemini_client import GeminiClientService

SAMPLE_ARTICLE_DICT = {
    "id": "ld_twostep_001",
    "headline": "European Central Bank Outlines Macroprudential Framework",
    "lead": "Governing Council emphasizes systemic risk mitigation and monetary policy alignment.",
    "section": "Economics",
    "raw_content": (
        "The European Central Bank convened in Frankfurt today to deliberate on macroeconomic resilience. "
        "President Christine Lagarde underscored that structural financial safeguards remain critical as credit conditions tighten. "
        "Eurozone member states have experienced divergent growth trajectories, prompting renewed focus on capital buffers. "
        "Commercial banking sectors have maintained robust tier-one capital ratios, though cross-border commercial real estate "
        "portfolios continue to face heightened refinancing friction. The ECB's forward posture remains strictly focused "
        "on inflation moderation while safeguarding banking sector solvency across the currency union."
    )
}

@pytest.fixture
def sample_article():
    return Article(
        id=SAMPLE_ARTICLE_DICT["id"],
        headline=SAMPLE_ARTICLE_DICT["headline"],
        lead=SAMPLE_ARTICLE_DICT["lead"],
        section=SAMPLE_ARTICLE_DICT["section"],
        raw_content=SAMPLE_ARTICLE_DICT["raw_content"]
    )

def test_prompt_engine_create_preprocessing_prompt():
    """Verify Step 1 preprocessing prompt embeds article JSON and target schema."""
    prompt = prompt_engine.create_preprocessing_prompt(SAMPLE_ARTICLE_DICT)
    
    assert "STEP 1: ARTICLE ANALYSIS & CONTEXT EXTRACTION" in prompt
    assert "European Central Bank Outlines Macroprudential Framework" in prompt
    assert '"main_points"' in prompt
    assert '"keywords"' in prompt
    assert '"tone"' in prompt
    assert '"article_length"' in prompt
    assert '"reading_time"' in prompt
    assert '"word_count"' in prompt
    assert "analytical" in prompt

def test_prompt_engine_create_two_step_synthesis_prompt():
    """Verify Step 2 synthesis prompt contains both raw article and populated contextual JSON."""
    context_dict = {
        "main_points": ["ECB outlines macroprudential framework", "Capital buffers remain resilient"],
        "keywords": ["ECB", "Frankfurt", "Christine Lagarde", "macroprudential"],
        "tone": "analytical",
        "article_length": "short",
        "reading_time": 60,
        "reading_time_minutes": 1.0,
        "word_count": 80
    }
    prompt = prompt_engine.create_two_step_synthesis_prompt(
        article_dict=SAMPLE_ARTICLE_DICT,
        context_dict=context_dict,
        mode=ReadingMode.SIXTY_SECONDS
    )

    assert "STEP 2: TWO-STEP SYNTHESIS WITH CONTEXTUAL INSIGHTS" in prompt
    assert "RAW ARTICLE JSON:" in prompt
    assert "POPULATED CONTEXTUAL JSON (METADATA & EDITORIAL INSIGHTS):" in prompt
    assert "European Central Bank Outlines Macroprudential Framework" in prompt
    assert "ECB outlines macroprudential framework" in prompt
    assert 'TARGET READING MODE: "60s"' in prompt
    assert "**The Essentials:**" in prompt

def test_extract_context_offline(sample_article):
    """Verify extract_context works deterministically and returns ArticlePreprocessing."""
    client_service = GeminiClientService()
    client_service._client = None  # Force offline fallback

    # 1. From Article domain object
    context = client_service.extract_context(sample_article)
    assert isinstance(context, ArticlePreprocessing)
    assert len(context.main_points) >= 1
    assert len(context.keywords) >= 1
    assert isinstance(context.tone, ToneCategory)
    assert isinstance(context.article_length, LengthTier)
    assert context.word_count > 40
    assert context.reading_time > 0

    # 2. From raw dictionary
    context_dict_input = client_service.extract_context(SAMPLE_ARTICLE_DICT)
    assert isinstance(context_dict_input, ArticlePreprocessing)
    assert context_dict_input.word_count > 40

def test_extract_context_with_gemini_mock(sample_article):
    """Verify extract_context parses Gemini LLM response into ArticlePreprocessing."""
    client_service = GeminiClientService()
    mock_genai_client = MagicMock()
    
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "main_points": [
            "ECB establishes stringent macroprudential guardrails",
            "Eurozone banking capital buffers prove resilient against commercial real estate stress"
        ],
        "keywords": ["ECB", "Frankfurt", "Lagarde", "Macroprudential"],
        "tone": "sober_briefing",
        "article_length": "short",
        "reading_time": 45,
        "reading_time_minutes": 0.8,
        "word_count": 75
    })
    mock_genai_client.models.generate_content.return_value = mock_response
    client_service._client = mock_genai_client

    context = client_service.extract_context(sample_article)
    assert isinstance(context, ArticlePreprocessing)
    assert context.tone == ToneCategory.SOBER_BRIEFING
    assert context.article_length == LengthTier.SHORT
    assert len(context.main_points) == 2
    assert "ECB establishes stringent macroprudential guardrails" in context.main_points[0]
    assert context.word_count == 75

def test_generate_summary_with_context_full_mode(sample_article):
    """Verify generate_summary_with_context preserves verbatim raw_content for full mode."""
    client_service = GeminiClientService()
    context = ArticlePreprocessing(
        main_points=["Key takeaway"],
        keywords=["Banking", "ECB"],
        tone=ToneCategory.ANALYTICAL,
        article_length=LengthTier.SHORT,
        reading_time=60,
        word_count=80
    )

    variant = client_service.generate_summary_with_context(
        article=sample_article,
        context=context,
        mode=ReadingMode.FULL
    )

    assert isinstance(variant, FlexReadVariant)
    assert variant.mode == ReadingMode.FULL
    assert variant.actual_content == sample_article.raw_content
    assert variant.word_count == len(sample_article.raw_content.split())
    # 200 WPM estimation
    assert variant.estimated_reading_time_minutes == max(1, round(variant.word_count / 200))

def test_generate_summary_with_context_gemini_mock(sample_article):
    """Verify generate_summary_with_context parses LLM response into FlexReadVariant."""
    client_service = GeminiClientService()
    mock_genai_client = MagicMock()

    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "title": "ECB Reinforces Financial Stability Guardrails",
        "summary": "Governing Council bolsters capital buffers amid commercial real estate strains.",
        "actual_content": "**The Essentials:** Strict macroprudential buffers.\n\n**The Crux:** Divergent Eurozone growth.\n\n**What Matters Now:** Solvency safeguards.",
        "estimated_reading_time_minutes": 1,
        "word_count": 60
    })
    mock_genai_client.models.generate_content.return_value = mock_response
    client_service._client = mock_genai_client

    context = ArticlePreprocessing(
        main_points=["ECB guardrails"],
        keywords=["ECB", "Frankfurt"],
        tone=ToneCategory.ANALYTICAL,
        article_length=LengthTier.SHORT,
        reading_time=60,
        word_count=80
    )

    variant = client_service.generate_summary_with_context(
        article=sample_article,
        context=context,
        mode=ReadingMode.SIXTY_SECONDS
    )

    assert isinstance(variant, FlexReadVariant)
    assert variant.title == "ECB Reinforces Financial Stability Guardrails"
    assert "**The Essentials:**" in variant.actual_content
    assert variant.estimated_reading_time_minutes == 1

def test_generate_two_step_variant_coordination(sample_article):
    """Verify generate_two_step_variant coordinates both steps and updates article preprocessing."""
    client_service = GeminiClientService()
    client_service._client = None  # Offline mode

    assert len(sample_article.preprocessing.main_points) == 0

    variant = client_service.generate_two_step_variant(sample_article, ReadingMode.BULLET_POINTS)

    # 1. Verify variant is synthesized
    assert isinstance(variant, FlexReadVariant)
    assert variant.mode == ReadingMode.BULLET_POINTS
    assert variant.word_count > 0

    # 2. Verify article preprocessing metadata was updated
    assert sample_article.preprocessing is not None
    assert isinstance(sample_article.preprocessing, ArticlePreprocessing)
    assert len(sample_article.preprocessing.main_points) >= 1
    assert len(sample_article.summary_bullets_en) >= 1
    assert sample_article.word_count > 0
    assert sample_article.reading_time_seconds > 0
