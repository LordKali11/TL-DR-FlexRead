from backend.app.models.article import Article, ArticlePreprocessing, LengthTier, ToneCategory
from backend.app.services.preprocessor import ArticlePreprocessor

def test_preprocessing_computes_all_required_fields_english():
    preprocessor = ArticlePreprocessor()
    
    sample_article = Article(
        id="ld_test_001_en",
        source_path="/fake/path_en.json",
        headline="Nvidia Beats Earnings Expectations as AI Spending Surges",
        lead="The American semiconductor powerhouse delivered record revenue, but Wall Street demands proof that hyperscalers can monetize AI models.",
        section="Business & Finance",
        raw_content="""
        Demand for high-performance AI accelerators remains virtually insatiable across the globe. Nvidia doubled its quarterly revenue compared to the previous year.
        However, the crucial strategic question remains whether hyperscalers like Microsoft, Google, and Amazon can justify their capital expenditure.
        Consequently, stock volatility increased following the earnings release as institutional investors reassessed valuations.
        Analysts note that the technology sector is approaching an inflection point where generative AI must demonstrate tangible productivity gains.
        In the future, corporate balance sheets will come under closer scrutiny if enterprise software revenues fail to match infrastructure buildout costs.
        """,
        preprocessing=ArticlePreprocessing()
    )
    
    result = preprocessor.process(sample_article, wpm=220)
    
    # 1. Main points defined
    assert len(result.main_points) >= 1
    assert any("Nvidia" in p or "semiconductor" in p or "hyperscalers" in p for p in result.main_points)
    
    # 2. Keywords defined
    assert len(result.keywords) >= 2
    assert any("Nvidia" in k or "AI" in k or "revenue" in k or "Wall" in k for k in result.keywords)
    
    # 3. Tone defined
    assert result.tone in [ToneCategory.ANALYTICAL, ToneCategory.SOBER_BRIEFING, ToneCategory.INVESTIGATIVE, ToneCategory.OPINION_COMMENTARY]
    assert result.tone == ToneCategory.ANALYTICAL
    
    # 4. Article length tier defined
    assert result.article_length in [LengthTier.SHORT, LengthTier.MEDIUM, LengthTier.LONG, LengthTier.LONGFORM]
    assert result.article_length == LengthTier.SHORT  # Short test snippet
    
    # 5. Reading time defined
    assert result.reading_time > 0
    assert result.reading_time_minutes > 0.0
    
    # 6. Word count defined
    assert result.word_count > 50

def test_tone_detection_english_opinion():
    preprocessor = ArticlePreprocessor()
    sample = Article(
        id="ld_test_opinion_en",
        source_path="/fake/opinion_en.json",
        headline="Opinion: Why European Industrial Policy Is Destined to Stumble",
        lead="A case for competitive market incentives rather than an endless subsidy race.",
        section="Opinion",
        raw_content="I remain convinced that government subsidies distort capital allocation and discourage real innovation.",
        preprocessing=ArticlePreprocessing()
    )
    result = preprocessor.process(sample)
    assert result.tone == ToneCategory.OPINION_COMMENTARY

def test_tone_detection_english_investigative():
    preprocessor = ArticlePreprocessor()
    sample = Article(
        id="ld_test_investigative_en",
        source_path="/fake/investigative_en.json",
        headline="Investigation: Secret Documents Reveal Misconduct in Sovereign Wealth Fund",
        lead="Internal whistleblower files disclose unauthorized transfers.",
        section="International",
        raw_content="Documents show that top officials authorized confidential accounts without oversight.",
        preprocessing=ArticlePreprocessing()
    )
    result = preprocessor.process(sample)
    assert result.tone == ToneCategory.INVESTIGATIVE
