import glob
import json
import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.mongodb import MongoDBService
from backend.app.services.cache_service import CacheService
from backend.app.services.preprocessor import ArticlePreprocessor
from backend.app.services.preprocessing_service import PreprocessingService

client = TestClient(app)

REFERENCE_DIR = "/home/lord_kali/TL-DR-FlexRead/input/days/2026-08-25/articles"
REFERENCE_FILE = os.path.join(REFERENCE_DIR, "2026-08-25_der-andere-blick_german-reform-fatigue-narrative-federal-government_ld10020899.json")

def get_reference_keys():
    with open(REFERENCE_FILE, "r", encoding="utf-8") as f:
        ref_doc = json.load(f)
    return set(ref_doc.keys())

def test_reference_keys_exist_in_preprocessing_output():
    ref_keys = get_reference_keys()
    assert len(ref_keys) == 30

    # 1. Setup mock/in-memory Mongo and Cache
    db = MongoDBService(uri="mongodb://localhost:27017", db_name="test_schema_check")
    cache = CacheService()
    preprocessor = ArticlePreprocessor()
    service = PreprocessingService(db_service=db, preprocessor=preprocessor, cache=cache)

    # 2. Seed article with canonical NZZ structure
    with open(REFERENCE_FILE, "r", encoding="utf-8") as f:
        sample_doc = json.load(f)

    # Use unique ID for testing
    sample_doc["id"] = "ld10020899_test"
    sample_doc["nzz_id"] = "ld.10020899_test"
    db.save_article(sample_doc)

    # 3. Process article
    result = service.process_article_from_mongo("ld10020899_test", warm_variants=True)

    # 4. Assert ALL 30 reference keys exist in the output dictionary
    missing_keys = [k for k in ref_keys if k not in result]
    assert len(missing_keys) == 0, f"Missing required NZZ JSON keys in preprocessing output: {missing_keys}"

    # 5. Assert summary output is populated in summary_bullets_en
    assert "summary_bullets_en" in result
    assert isinstance(result["summary_bullets_en"], list)
    assert len(result["summary_bullets_en"]) >= 1
    for bullet in result["summary_bullets_en"]:
        assert isinstance(bullet, str)
        assert len(bullet) > 0

    # 6. Assert standard NZZ attributes have valid values and types matching reference
    assert isinstance(result["nzz_id"], str)
    assert isinstance(result["headline"], str) and len(result["headline"]) > 0
    assert isinstance(result["lead"], str)
    assert isinstance(result["reading_time_seconds"], int) and result["reading_time_seconds"] > 0
    assert isinstance(result["word_count"], int) and result["word_count"] > 0
    assert isinstance(result["body"], list)
    assert isinstance(result["tags"], list)
    assert isinstance(result["url"], str)
    assert isinstance(result["language"], str)

def test_api_preprocess_and_summary_endpoint_return_nzz_schema():
    ref_keys = get_reference_keys()

    # Get available article ID
    list_res = client.get("/api/articles?limit=1")
    assert list_res.status_code == 200
    articles = list_res.json()["articles"]
    assert len(articles) > 0
    article_id = articles[0]["id"]

    # 1. Test POST /api/articles/{article_id}/preprocess
    prep_res = client.post(f"/api/articles/{article_id}/preprocess?warm_variants=false")
    assert prep_res.status_code == 200
    prep_data = prep_res.json()

    for k in ref_keys:
        assert k in prep_data, f"Key '{k}' missing from POST /api/articles/{{id}}/preprocess output"

    assert isinstance(prep_data["summary_bullets_en"], list)
    assert len(prep_data["summary_bullets_en"]) >= 1

    # 2. Test GET /api/articles/{article_id}/summary
    sum_res = client.get(f"/api/articles/{article_id}/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()

    for k in ref_keys:
        assert k in sum_data, f"Key '{k}' missing from GET /api/articles/{{id}}/summary output"

    assert isinstance(sum_data["summary_bullets_en"], list)
    assert len(sum_data["summary_bullets_en"]) >= 1
    assert sum_data["headline"] == prep_data["headline"]
