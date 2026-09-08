import json
import logging
import re
from typing import Any, Dict, Optional
from ..config import settings
from ..models.article import Article, ReadingMode, FlexReadVariant, ArticlePreprocessing
from .prompt_engine import prompt_engine
from .preprocessor import preprocessor_service

logger = logging.getLogger(__name__)

class GeminiClientService:
    """
    Client for Google Gemini / Vertex AI with structured JSON outputs.
    Fully ready for Google Cloud Platform (Cloud Run, Vertex AI, ADC, API Key).
    Includes an English offline heuristic generator for local development and test coverage.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.project = settings.GOOGLE_CLOUD_PROJECT
        self.location = settings.GOOGLE_CLOUD_LOCATION
        self.use_vertex = settings.USE_VERTEX_AI or bool(self.project and not self.api_key)
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        try:
            from google import genai
            
            # GCP Vertex AI integration (Cloud Run with Service Account or ADC)
            if self.use_vertex and self.project:
                logger.info(f"Initializing GCP Vertex AI Client (project={self.project}, location={self.location})")
                self._client = genai.Client(
                    vertexai=True,
                    project=self.project,
                    location=self.location
                )
                return
            
            # Google AI Studio API Key integration
            if self.api_key:
                logger.info(f"Initializing Gemini Client with API Key and model {self.model_name}")
                self._client = genai.Client(api_key=self.api_key)
                return
            
            logger.info("No GCP Vertex AI credentials or GEMINI_API_KEY detected; using offline English NZZ generator.")
        except Exception as e:
            logger.warning(f"Could not initialize google-genai client: {e}. Falling back to offline engine.")
            self._client = None

    def generate_variant(
        self,
        article: Article,
        mode: ReadingMode,
        wpm: int = 220
    ) -> FlexReadVariant:
        """
        Generates an English FlexRead variant (60s, bullet_points, inline_simplified, full).
        Calls Gemini / Vertex AI if configured, otherwise uses deterministic editorial heuristic.
        """
        # Ensure preprocessing is fresh
        if not article.preprocessing or not article.preprocessing.main_points:
            article.preprocessing = preprocessor_service.process(article, wpm=wpm)

        # Full mode returns the original text formatted
        if mode == ReadingMode.FULL:
            word_count = len(article.raw_content.split())
            reading_time = preprocessor_service.calculate_reading_time(word_count, wpm)
            return FlexReadVariant(
                mode=ReadingMode.FULL,
                title=article.headline,
                summary=article.lead,
                actual_content=article.raw_content,
                word_count=word_count,
                reading_time_seconds=reading_time,
                cached=False
            )

        # Attempt Gemini / Vertex AI Generation if client is available
        if self._client:
            try:
                variant = self._generate_with_gemini(article, mode, wpm)
                if variant:
                    return variant
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}. Using English editorial fallback generator.")

        # Editorial Heuristic Fallback (English)
        return self._generate_heuristic_variant(article, mode, wpm)

    def _generate_with_gemini(
        self,
        article: Article,
        mode: ReadingMode,
        wpm: int
    ) -> Optional[FlexReadVariant]:
        """Calls Gemini API on GCP Vertex AI or AI Studio with structured JSON output."""
        user_prompt = prompt_engine.create_generation_prompt(article, mode)
        system_instruction = prompt_engine.get_system_instruction()

        response = self._client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "temperature": 0.2,
            }
        )

        if not response or not response.text:
            return None

        raw_text = response.text.strip()
        # Clean any accidental markdown fences
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\n", "", raw_text)
            raw_text = re.sub(r"\n```$", "", raw_text)

        data = json.loads(raw_text)
        title = data.get("title", article.headline)
        summary = data.get("summary", article.lead)
        actual_content = data.get("actual_content", "")

        word_count = preprocessor_service.calculate_word_count(f"{title} {summary} {actual_content}")
        reading_time = preprocessor_service.calculate_reading_time(word_count, wpm)

        return FlexReadVariant(
            mode=mode,
            title=title,
            summary=summary,
            actual_content=actual_content,
            word_count=word_count,
            reading_time_seconds=reading_time,
            cached=False
        )

    def _generate_heuristic_variant(
        self,
        article: Article,
        mode: ReadingMode,
        wpm: int
    ) -> FlexReadVariant:
        """
        High-quality English algorithmic fallback preserving NZZ editorial style when offline.
        """
        prep = article.preprocessing or preprocessor_service.process(article, wpm=wpm)
        main_points = prep.main_points or [article.lead]

        if mode == ReadingMode.SIXTY_SECONDS:
            title = article.headline
            summary = article.lead if article.lead else (main_points[0] if main_points else "Executive overview.")
            
            p1 = main_points[0] if len(main_points) > 0 else article.lead
            p2 = main_points[1] if len(main_points) > 1 else "Market dynamics and political shifts are forcing leaders to re-evaluate their positions."
            p3 = main_points[2] if len(main_points) > 2 else "The future trajectory will depend on upcoming regulatory and financial decisions."

            actual_content = (
                f"- **The Essentials:** {p1}\n\n"
                f"- **The Crux:** {p2}\n\n"
                f"- **What Matters Now:** {p3}"
            )

        elif mode == ReadingMode.BULLET_POINTS:
            title = f"Briefing: {article.headline}"
            summary = article.lead
            bullets = []
            tags = [
                "Core Development",
                "Context & Background",
                "Economic & Strategic Impact",
                "Critical Assessment",
                "Outlook & Implications"
            ]
            
            for idx, pt in enumerate(main_points[:5]):
                tag = tags[idx] if idx < len(tags) else f"Key Factor {idx+1}"
                bullets.append(f"- **{tag}:** {pt}")
            
            if len(bullets) < 3:
                bullets.append("- **Market Context:** Fundamental indicators suggest heightened short-term sensitivity to quarterly announcements.")
                bullets.append("- **Strategic Outlook:** Stakeholders across the value chain are monitoring systemic risks.")

            actual_content = "\n\n".join(bullets)

        elif mode == ReadingMode.INLINE_SIMPLIFIED:
            title = article.headline
            summary = article.lead
            
            # Select key paragraphs from original content, format with accessible subheadings
            paragraphs = [p.strip() for p in article.raw_content.split("\n\n") if p.strip()]
            selected_body = []
            
            selected_body.append("### Why This Development Matters")
            if paragraphs:
                selected_body.append(paragraphs[0])
            
            selected_body.append("### Key Driving Factors & Analysis")
            for p in paragraphs[1:4]:
                if not p.startswith("#"):
                    selected_body.append(p)
            
            actual_content = "\n\n".join(selected_body)

        else:
            title = article.headline
            summary = article.lead
            actual_content = article.raw_content

        word_count = preprocessor_service.calculate_word_count(f"{title} {summary} {actual_content}")
        reading_time = preprocessor_service.calculate_reading_time(word_count, wpm)

        return FlexReadVariant(
            mode=mode,
            title=title,
            summary=summary,
            actual_content=actual_content,
            word_count=word_count,
            reading_time_seconds=reading_time,
            cached=False
        )

    def transform_article(self, article: Article, mode: ReadingMode, wpm: int = 220) -> FlexReadVariant:
        """Alias for generate_variant."""
        return self.generate_variant(article, mode, wpm=wpm)

gemini_client_service = GeminiClientService()
gemini_client = gemini_client_service
