from pathlib import Path
from backend.app.services.article_ingestion import ArticleIngestionService
from backend.app.config import settings

def test_ingestion_service_finds_articles():
    service = ArticleIngestionService(input_dir=settings.INPUT_DIR)
    found, indexed, errors = service.ingest_all(force_reload=True)
    
    assert found > 0, "Should discover articles in input directory"
    assert indexed > 0, "Should index at least one article"
    assert len(errors) == 0, f"Encountered unexpected parsing errors: {errors}"

def test_get_article_by_id():
    service = ArticleIngestionService(input_dir=settings.INPUT_DIR)
    service.ingest_all()
    
    articles, total = service.list_articles(limit=5)
    assert total > 0
    first_article = articles[0]
    
    fetched = service.get_article(first_article.id)
    assert fetched is not None
    assert fetched.id == first_article.id
    assert len(fetched.headline) > 0
    assert len(fetched.raw_content) > 0

def test_id_normalization():
    service = ArticleIngestionService()
    assert service.extract_id_from_path(Path("2026-08-25_wirtschaft_nvidia_ld10020939.json")) == "ld10020939"
    assert service.extract_id_from_path(Path("article_ld1846968.md")) == "ld1846968"
