from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from ..models.api import PersonalizedFeedResponse, RecommendedArticle
from ..models.article import ArticleSummary
from ..services.user_service import user_service
from ..services.article_ingestion import article_ingestion_service
from ..services.preprocessor import preprocessor_service

router = APIRouter(prefix="/api/personalize", tags=["Personalization & Commute Context"])

@router.get("/{user_id}/feed", response_model=PersonalizedFeedResponse, summary="Get commute-adaptive personalized feed")
def get_personalized_feed(
    user_id: str,
    time_budget_minutes: Optional[int] = Query(None, description="Override available commute/reading time window in minutes"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Generates an adaptive reading feed for commuters and busy professionals:
    - Filters/ranks articles matching the user's topic interests
    - Dynamically chooses the optimal FlexRead length variant (60s, bullet_points, inline_simplified, full)
      fitting the user's commute time budget and personal WPM.
    """
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")

    budget_minutes = time_budget_minutes or user.preferences.commute_time_budget_minutes
    articles, _ = article_ingestion_service.list_articles(limit=100)

    # Filter by user topic interests if available
    interests = [t.lower() for t in user.preferences.topic_interests]
    relevant_articles = []
    other_articles = []

    for a in articles:
        if not a.preprocessing or not a.preprocessing.word_count:
            a.preprocessing = preprocessor_service.process(a)

        sec = (a.section or "").lower()
        if any(interest in sec for interest in interests):
            relevant_articles.append(a)
        else:
            other_articles.append(a)

    ranked_articles = (relevant_articles + other_articles)[:limit]

    recommended_list = []
    for a in ranked_articles:
        mode, est_minutes, reason = user_service.recommend_mode_for_article(
            user=user,
            article=a,
            override_time_budget_minutes=budget_minutes
        )

        summary = ArticleSummary(
            id=a.id,
            headline=a.headline,
            lead=a.lead,
            section=a.section,
            date=a.date,
            author=a.author,
            url=a.url,
            image_url=a.image_url,
            word_count=a.preprocessing.word_count,
            reading_time_seconds=a.preprocessing.reading_time,
            article_length=a.preprocessing.article_length,
            tone=a.preprocessing.tone
        )

        recommended_list.append(RecommendedArticle(
            article=summary,
            recommended_mode=mode,
            estimated_reading_time_minutes=est_minutes,
            relevance_reason=reason
        ))

    return PersonalizedFeedResponse(
        user_id=user.user_id,
        commute_time_budget_minutes=budget_minutes,
        reading_speed_wpm=user.preferences.reading_speed_wpm,
        recommended_articles=recommended_list
    )

@router.get("/{user_id}/article/{article_id}", response_model=RecommendedArticle, summary="Recommend mode for specific article")
def recommend_for_article(
    user_id: str,
    article_id: str,
    time_budget_minutes: Optional[int] = Query(None, description="Available time window in minutes")
):
    """Recommends optimal reading mode for a single article given user context."""
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")

    article = article_ingestion_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Article {article_id} not found")

    if not article.preprocessing:
        article.preprocessing = preprocessor_service.process(article)

    budget_minutes = time_budget_minutes or user.preferences.commute_time_budget_minutes
    mode, est_minutes, reason = user_service.recommend_mode_for_article(
        user=user,
        article=article,
        override_time_budget_minutes=budget_minutes
    )

    summary = ArticleSummary(
        id=article.id,
        headline=article.headline,
        lead=article.lead,
        section=article.section,
        date=article.date,
        author=article.author,
        url=article.url,
        image_url=article.image_url,
        word_count=article.preprocessing.word_count,
        reading_time_seconds=article.preprocessing.reading_time,
        article_length=article.preprocessing.article_length,
        tone=article.preprocessing.tone
    )

    return RecommendedArticle(
        article=summary,
        recommended_mode=mode,
        estimated_reading_time_minutes=est_minutes,
        relevance_reason=reason
    )
