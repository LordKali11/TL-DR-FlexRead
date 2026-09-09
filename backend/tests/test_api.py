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

        # Check structural markers (either live Gemini response or fallback template)
        if mode == ReadingMode.SIXTY_SECONDS:
            assert len(data["actual_content"]) > 50
        elif mode == ReadingMode.BULLET_POINTS:
            assert any(m in data["actual_content"] for m in ["*", "-", "•", "**", "###"])
        elif mode == ReadingMode.INLINE_SIMPLIFIED:
            assert "###" in data["actual_content"] or "**" in data["actual_content"] or len(data["actual_content"]) > 100
        
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

def test_dynamic_reading_target_times():
    # Ensure articles exist
    list_res = client.get("/api/articles?limit=3")
    assert list_res.status_code == 200
    data = list_res.json()
    assert len(data["articles"]) > 0
    article = data["articles"][0]
    article_id = article["id"]

    # Verify frontend compatibility fields are populated on article summary
    assert "heroImage" in article or "teaser_image" in article
    assert "readingTimes" in article
    assert article["readingTimes"]["briefing"] == 5
    assert article["readingTimes"]["analytical"] == 10
    assert "kicker" in article
    assert "topic" in article

    # Test 5-minute target reading time
    res_5 = client.get(f"/api/articles/{article_id}/read?target_time_minutes=5")
    assert res_5.status_code == 200
    data_5 = res_5.json()
    assert data_5["estimated_reading_time_minutes"] == 5
    assert "title" in data_5 and len(data_5["title"]) > 0
    assert "summary" in data_5 and len(data_5["summary"]) > 0
    assert "actual_content" in data_5 and len(data_5["actual_content"]) > 0
    assert "word_count" in data_5 or "variant_word_count" in data_5

    # Test 10-minute target reading time
    res_10 = client.get(f"/api/articles/{article_id}/read?target_time_minutes=10")
    assert res_10.status_code == 200
    data_10 = res_10.json()
    assert data_10["estimated_reading_time_minutes"] == 10
    assert "title" in data_10 and len(data_10["title"]) > 0
    assert "summary" in data_10 and len(data_10["summary"]) > 0
    assert "actual_content" in data_10 and len(data_10["actual_content"]) > 0

    # Test 15-minute target reading time
    res_15 = client.get(f"/api/articles/{article_id}/read?target_time_minutes=15")
    assert res_15.status_code == 200
    data_15 = res_15.json()
    assert data_15["estimated_reading_time_minutes"] == 15
    assert "title" in data_15 and len(data_15["title"]) > 0
    assert "summary" in data_15 and len(data_15["summary"]) > 0
    assert "actual_content" in data_15 and len(data_15["actual_content"]) > 0

    # Test string alias mode ("briefing")
    res_briefing = client.get(f"/api/articles/{article_id}/read?mode=briefing")
    assert res_briefing.status_code == 200
    data_briefing = res_briefing.json()
    assert data_briefing["estimated_reading_time_minutes"] == 5

    # Test string alias mode ("analytical")
    res_analytical = client.get(f"/api/articles/{article_id}/read?mode=analytical")
    assert res_analytical.status_code == 200
    data_analytical = res_analytical.json()
    assert data_analytical["estimated_reading_time_minutes"] == 10

def test_article_detail_frontend_compatibility():
    list_res = client.get("/api/articles?limit=1")
    article_id = list_res.json()["articles"][0]["id"]

    res = client.get(f"/api/articles/{article_id}")
    assert res.status_code == 200
    detail = res.json()

    assert detail["title"] == detail["headline"]
    assert detail["subtitle"] == detail["lead"]
    assert detail["topic"] == detail["section"]
    assert "readingTimes" in detail
    assert "summaryBullets" in detail
    assert "takeaways" in detail

