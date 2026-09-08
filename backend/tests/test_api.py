from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.article import ReadingMode

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "gemini_model" in data
    assert data["primary_database"] == "mongodb"
    assert data["cache_layer"] == "redis"
    assert data["mongodb_status"]["connected"] is True
    assert data["redis_status"]["connected"] is True

def test_ingest_and_list_articles():
    # Ingest
    ingest_res = client.post("/api/articles/ingest?force_reload=true")
    assert ingest_res.status_code == 200
    ingest_data = ingest_res.json()
    assert ingest_data["articles_indexed"] > 0
    
    # List
    list_res = client.get("/api/articles?limit=5")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] > 0
    assert len(list_data["articles"]) > 0
    
    first = list_data["articles"][0]
    assert "headline" in first
    assert "word_count" in first
    assert "reading_time_seconds" in first
    assert "article_length" in first
    assert "tone" in first

def test_get_article_preprocessing():
    # Get list to pick an ID
    list_res = client.get("/api/articles?limit=1")
    article_id = list_res.json()["articles"][0]["id"]
    
    # Get detail
    res = client.get(f"/api/articles/{article_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == article_id
    
    # Verify preprocessing phase definitions:
    # "main points, keywords, tone, article_length reading time and word count"
    prep = data["preprocessing"]
    assert "main_points" in prep
    assert "keywords" in prep
    assert "tone" in prep
    assert "article_length" in prep
    assert "reading_time" in prep
    assert "word_count" in prep
    assert prep["word_count"] > 0

def test_read_modes_output_format_english():
    # Verify: "Output is a Title, summary and actual content" with English formatting
    list_res = client.get("/api/articles?limit=1")
    article_id = list_res.json()["articles"][0]["id"]
    
    modes = [ReadingMode.SIXTY_SECONDS, ReadingMode.BULLET_POINTS, ReadingMode.INLINE_SIMPLIFIED, ReadingMode.FULL]
    
    for mode in modes:
        res = client.get(f"/api/articles/{article_id}/read?mode={mode.value}")
        assert res.status_code == 200
        data = res.json()
        
        # Verify required outputs
        assert "title" in data, f"Missing title for {mode}"
        assert "summary" in data, f"Missing summary for {mode}"
        assert "actual_content" in data, f"Missing actual_content for {mode}"
        
        assert len(data["title"]) > 0
        assert len(data["summary"]) > 0
        assert len(data["actual_content"]) > 0

        # Check English structural markers when using fallback
        if mode == ReadingMode.SIXTY_SECONDS:
            assert "**The Essentials:**" in data["actual_content"]
            assert "**The Crux:**" in data["actual_content"]
            assert "**What Matters Now:**" in data["actual_content"]
        elif mode == ReadingMode.BULLET_POINTS:
            assert "**Core Development:**" in data["actual_content"] or "**Market Context:**" in data["actual_content"]
        elif mode == ReadingMode.INLINE_SIMPLIFIED:
            assert "### Why This Development Matters" in data["actual_content"]
        
        # Verify caching flag on second call
        res_cached = client.get(f"/api/articles/{article_id}/read?mode={mode.value}")
        assert res_cached.status_code == 200
        assert res_cached.json()["cached"] is True

def test_user_personalization_feed():
    res = client.get("/api/personalize/user_commuter_zurich/feed?time_budget_minutes=3")
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == "user_commuter_zurich"
    assert len(data["recommended_articles"]) > 0
    rec = data["recommended_articles"][0]
    assert "recommended_mode" in rec
    assert "estimated_reading_time_minutes" in rec
    assert "relevance_reason" in rec
    # Verify reason is in English
    assert any(word in rec["relevance_reason"] for word in ["Fits", "transit", "window", "Executive", "briefing", "Optimized", "preferences", "Sufficient", "reporting"])

def test_preprocessing_endpoints():
    # 1. First ensure we have at least one ingested article
    list_res = client.get("/api/articles?limit=1")
    assert list_res.status_code == 200
    articles = list_res.json()["articles"]
    assert len(articles) > 0
    article_id = articles[0]["id"]

    # 2. Trigger individual article preprocessing from MongoDB -> Redis
    prep_res = client.post(f"/api/articles/{article_id}/preprocess?warm_variants=true")
    assert prep_res.status_code == 200
    prep_data = prep_res.json()
    assert prep_data["article_id"] == article_id
    assert prep_data["redis_cache_populated"] is True
    assert "main_points" in prep_data["preprocessing"]
    assert "keywords" in prep_data["preprocessing"]
    assert "tone" in prep_data["preprocessing"]
    assert "article_length" in prep_data["preprocessing"]
    assert len(prep_data["warmed_modes"]) == 4

    # 3. Trigger batch preprocessing
    batch_res = client.post("/api/articles/preprocess/batch?limit=10&warm_variants=false")
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert "total_unprocessed_found" in batch_data
    assert "successfully_processed" in batch_data
    assert batch_data["redis_cache_populated"] is True

