import pytest
from backend.app.db.mongodb import MongoDBService

def test_mongodb_articles_crud():
    db = MongoDBService(uri="mongodb://localhost:27017", db_name="test_flexread_mongo")
    
    # 1. Create / Upsert
    article_doc = {
        "id": "ld_test_mongo_doc_1",
        "headline": "European Central Bank Rate Decision",
        "lead": "Governing Council weighs rate trajectory amidst disinflation.",
        "section": "Economy",
        "raw_content": "The Governing Council met in Frankfurt to deliberate on benchmark rates.",
        "word_count": 120,
        "preprocessing": {
            "main_points": ["Rates unchanged", "Inflation decelerating"],
            "keywords": ["ECB", "Frankfurt", "Rates"]
        }
    }
    saved_id = db.save_article(article_doc)
    assert saved_id == "ld_test_mongo_doc_1"

    # 2. Read
    fetched = db.get_article("ld_test_mongo_doc_1")
    assert fetched is not None
    assert fetched["headline"] == "European Central Bank Rate Decision"
    assert fetched["preprocessing"]["keywords"] == ["ECB", "Frankfurt", "Rates"]

    # 3. Update Preprocessing
    new_prep = {
        "main_points": ["Updated key takeaway"],
        "keywords": ["ECB", "Monetary Policy"],
        "tone": "analytical",
        "article_length": "short",
        "reading_time": 35,
        "word_count": 120
    }
    updated = db.update_article_preprocessing("ld_test_mongo_doc_1", new_prep)
    assert updated is True

    fetched_updated = db.get_article("ld_test_mongo_doc_1")
    assert fetched_updated["preprocessing"]["main_points"] == ["Updated key takeaway"]

    # 4. List and Count
    articles = db.list_articles(section="Economy")
    assert len(articles) >= 1
    assert db.count_articles(section="Economy") >= 1

def test_mongodb_users_crud():
    db = MongoDBService(uri="mongodb://localhost:27017", db_name="test_flexread_mongo")

    user_doc = {
        "user_id": "user_test_mongo_001",
        "username": "Alex Zurich",
        "email": "alex@zurich.ch",
        "created_at": "2026-08-25T08:00:00+00:00",
        "preferences": {
            "reading_speed_wpm": 260,
            "preferred_mode": "60s",
            "topic_interests": ["Business", "Technology"],
            "commute_time_budget_minutes": 4
        },
        "reading_history": [],
        "bookmarked_articles": []
    }
    db.save_user(user_doc)

    user = db.get_user("user_test_mongo_001")
    assert user is not None
    assert user["username"] == "Alex Zurich"
    assert user["preferences"]["reading_speed_wpm"] == 260
