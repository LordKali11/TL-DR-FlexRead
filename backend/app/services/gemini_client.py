import json
import logging
import re
from typing import Any, Dict, Optional, Union
from ..config import settings
from ..models.article import Article, ReadingMode, FlexReadVariant, ArticlePreprocessing, ToneCategory, LengthTier
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

    def extract_context(
        self,
        article: Union[Article, Dict[str, Any]],
        wpm: int = 220
    ) -> ArticlePreprocessing:
        """
        Executes Step 1 of the two-step preprocessing pipeline.
        Calls Gemini with the full article JSON context to extract and populate
        ArticlePreprocessing (main_points, keywords, tone, article_length, reading_time, word_count).
        Falls back to preprocessor_service if offline or on error.
        """
        if isinstance(article, Article):
            article_dict = article.to_nzz_json() if hasattr(article, "to_nzz_json") else article.model_dump()
            raw_content = article.raw_content
            article_obj = article
        elif isinstance(article, dict):
            article_dict = article
            raw_content = article.get("raw_content") or article.get("body_text") or ""
            if not raw_content and isinstance(article.get("body"), list):
                parts = [p.get("text", "") for p in article.get("body", []) if isinstance(p, dict) and p.get("text")]
                raw_content = "\n\n".join(parts)
            article_obj = Article(
                id=str(article.get("id") or article.get("nzz_id") or "raw_doc"),
                headline=article.get("headline") or "Untitled",
                lead=article.get("lead") or "",
                section=article.get("section") or "General",
                raw_content=raw_content
            )
        else:
            raise TypeError(f"Expected Article or dict, got {type(article)}")

        # Attempt Call 1 with Gemini if client available
        if self._client:
            try:
                system_instruction = prompt_engine.get_system_instruction()
                step1_prompt = prompt_engine.create_preprocessing_prompt(article_dict)
                from google.genai import types
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=step1_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )
                if response and response.text:
                    cleaned_text = response.text.strip()
                    if cleaned_text.startswith("```"):
                        cleaned_text = re.sub(r"^```(?:json)?\n", "", cleaned_text)
                        cleaned_text = re.sub(r"\n```$", "", cleaned_text)
                    data = json.loads(cleaned_text)

                    # Extract & validate fields
                    main_points = data.get("main_points") or []
                    if isinstance(main_points, str):
                        main_points = [main_points]
                    keywords = data.get("keywords") or []
                    if isinstance(keywords, str):
                        keywords = [k.strip() for k in keywords.split(",")]

                    tone_val = str(data.get("tone", "analytical")).lower().strip()
                    try:
                        tone = ToneCategory(tone_val)
                    except ValueError:
                        tone = ToneCategory.ANALYTICAL

                    length_val = str(data.get("article_length", "medium")).lower().strip()
                    try:
                        length_tier = LengthTier(length_val)
                    except ValueError:
                        length_tier = LengthTier.MEDIUM

                    wc = data.get("word_count") or preprocessor_service.calculate_word_count(raw_content)
                    rt = data.get("reading_time") or preprocessor_service.calculate_reading_time(wc, wpm)
                    rt_min = data.get("reading_time_minutes") or round(rt / 60.0, 1)

                    return ArticlePreprocessing(
                        main_points=main_points,
                        keywords=keywords,
                        tone=tone,
                        article_length=length_tier,
                        reading_time=rt,
                        reading_time_minutes=rt_min,
                        word_count=wc
                    )
            except Exception as e:
                logger.error(f"Gemini Call 1 (extract_context) failed: {e}. Falling back to preprocessor_service.")

        # Local deterministic fallback
        return preprocessor_service.process(article_obj, wpm=wpm)

    def generate_summary_with_context(
        self,
        article: Union[Article, Dict[str, Any]],
        context: Union[ArticlePreprocessing, Dict[str, Any]],
        mode: Union[ReadingMode, str],
        wpm: int = 220
    ) -> FlexReadVariant:
        """
        Executes Step 2 of the two-step synthesis pipeline.
        Feeds both the raw article JSON and the populated contextual JSON to Gemini,
        synthesizing the summary matching the requested reading mode variant (article.py:6-56).
        Returns a FlexReadVariant (article.py:110-130).
        """
        # Resolve mode
        if isinstance(mode, str):
            try:
                resolved_mode = ReadingMode(mode)
            except ValueError:
                resolved_mode = ReadingMode.SIXTY_SECONDS
        else:
            resolved_mode = mode

        # Prepare article dict and object
        if isinstance(article, Article):
            article_dict = article.to_nzz_json() if hasattr(article, "to_nzz_json") else article.model_dump()
            raw_content = article.raw_content
            article_obj = article
        elif isinstance(article, dict):
            article_dict = article
            raw_content = article.get("raw_content") or article.get("body_text") or ""
            if not raw_content and isinstance(article.get("body"), list):
                parts = [p.get("text", "") for p in article.get("body", []) if isinstance(p, dict) and p.get("text")]
                raw_content = "\n\n".join(parts)
            article_obj = Article(
                id=str(article.get("id") or article.get("nzz_id") or "raw_doc"),
                headline=article.get("headline") or "Untitled",
                lead=article.get("lead") or "",
                section=article.get("section") or "General",
                raw_content=raw_content
            )
        else:
            raise TypeError(f"Expected Article or dict, got {type(article)}")

        # Prepare context dict and object
        if isinstance(context, ArticlePreprocessing):
            context_dict = context.model_dump()
            context_obj = context
        elif isinstance(context, dict):
            context_dict = context
            context_obj = ArticlePreprocessing(**context)
        else:
            raise TypeError(f"Expected ArticlePreprocessing or dict, got {type(context)}")

        article_obj.preprocessing = context_obj

        # Full mode returns verbatim raw_content with zero structural edits
        if resolved_mode == ReadingMode.FULL:
            word_count = len(raw_content.split())
            reading_time = preprocessor_service.calculate_reading_time(word_count, wpm)
            est_minutes = max(1, round(word_count / 200))
            return FlexReadVariant(
                mode=ReadingMode.FULL,
                title=article_dict.get("headline", article_obj.headline),
                summary=article_dict.get("lead", article_obj.lead),
                actual_content=raw_content,
                word_count=word_count,
                reading_time_seconds=reading_time,
                estimated_reading_time_minutes=est_minutes,
                cached=False
            )

        # Attempt Call 2 with Gemini if client available
        if self._client:
            try:
                system_instruction = prompt_engine.get_system_instruction()
                step2_prompt = prompt_engine.create_two_step_synthesis_prompt(
                    article_dict=article_dict,
                    context_dict=context_dict,
                    mode=resolved_mode
                )
                from google.genai import types
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=step2_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                if response and response.text:
                    cleaned_text = response.text.strip()
                    if cleaned_text.startswith("```"):
                        cleaned_text = re.sub(r"^```(?:json)?\n", "", cleaned_text)
                        cleaned_text = re.sub(r"\n```$", "", cleaned_text)
                    data = json.loads(cleaned_text)

                    title = data.get("title", article_obj.headline)
                    summary = data.get("summary", article_obj.lead)
                    actual_content = data.get("actual_content", "")

                    computed_wc = preprocessor_service.calculate_word_count(f"{title} {summary} {actual_content}")
                    word_count = data.get("word_count") or computed_wc
                    reading_time = preprocessor_service.calculate_reading_time(word_count, wpm)

                    est_mins = data.get("estimated_reading_time_minutes")
                    if not est_mins:
                        if resolved_mode == ReadingMode.FIVE_MINUTES:
                            est_mins = 5
                        elif resolved_mode == ReadingMode.TEN_MINUTES:
                            est_mins = 10
                        elif resolved_mode == ReadingMode.FIFTEEN_MINUTES:
                            est_mins = 15
                        elif resolved_mode == ReadingMode.SIXTY_SECONDS:
                            est_mins = 1
                        else:
                            est_mins = max(1, round(reading_time / 60))

                    return FlexReadVariant(
                        mode=resolved_mode,
                        title=title,
                        summary=summary,
                        actual_content=actual_content,
                        estimated_reading_time_minutes=int(est_mins),
                        word_count=int(word_count),
                        reading_time_seconds=int(reading_time),
                        cached=False
                    )
            except Exception as e:
                logger.error(f"Gemini Call 2 (generate_summary_with_context) failed: {e}. Falling back to heuristic.")

        # Fallback to deterministic editorial heuristic
        return self._generate_heuristic_variant(article_obj, resolved_mode, wpm)

    def generate_two_step_variant(
        self,
        article: Article,
        mode: Union[ReadingMode, str],
        wpm: int = 220
    ) -> FlexReadVariant:
        """
        Coordinates the full two-step pipeline sequentially:
        1. Executes Call 1 (extract_context) to extract contextual JSON.
        2. Updates the article's preprocessing metadata.
        3. Executes Call 2 (generate_summary_with_context) with both raw article and populated context.
        """
        # Step 1: Extract contextual JSON
        context = self.extract_context(article, wpm=wpm)

        # Update article preprocessing metadata
        article.preprocessing = context
        article.word_count = context.word_count
        article.reading_time_seconds = context.reading_time
        article.reading_time_minutes = context.reading_time_minutes
        article.tone = context.tone
        article.article_length = context.article_length
        if context.main_points:
            article.summary_bullets_en = list(context.main_points)
        if context.keywords and not article.tags:
            article.tags = list(context.keywords)

        # Step 2: Synthesize summary with context
        return self.generate_summary_with_context(article, context, mode, wpm=wpm)

    def generate_variant(
        self,
        article: Article,
        mode: ReadingMode,
        wpm: int = 220
    ) -> FlexReadVariant:
        """
        Generates an English FlexRead variant (60s, bullet_points, inline_simplified, 5min, 10min, 15min, full).
        Coordinates the full two-step pipeline sequentially.
        """
        return self.generate_two_step_variant(article, mode, wpm=wpm)

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

        computed_wc = preprocessor_service.calculate_word_count(f"{title} {summary} {actual_content}")
        word_count = data.get("word_count") or computed_wc
        reading_time = preprocessor_service.calculate_reading_time(word_count, wpm)

        est_mins = data.get("estimated_reading_time_minutes")
        if not est_mins:
            if mode == ReadingMode.FIVE_MINUTES:
                est_mins = 5
            elif mode == ReadingMode.TEN_MINUTES:
                est_mins = 10
            elif mode == ReadingMode.FIFTEEN_MINUTES:
                est_mins = 15
            elif mode == ReadingMode.SIXTY_SECONDS:
                est_mins = 1
            else:
                est_mins = max(1, round(reading_time / 60))

        return FlexReadVariant(
            mode=mode,
            title=title,
            summary=summary,
            actual_content=actual_content,
            estimated_reading_time_minutes=est_mins,
            word_count=word_count,
            reading_time_seconds=reading_time,
            cached=False
        )

    def _build_5min_heuristic(self, article: Article, main_points: list[str]) -> tuple[str, str, str]:
        """Builds 5-minute variant: essential takeaways, facts, structured bullets, concluding overview."""
        title = f"Executive Briefing: {article.headline}"
        summary = article.lead if article.lead else (main_points[0] if main_points else "Essential executive briefing.")

        paragraphs = [p.strip() for p in article.raw_content.split("\n\n") if p.strip() and not p.startswith("#")]
        
        lead_p = paragraphs[0] if paragraphs else summary
        sec1 = f"### Executive Briefing\n\n{lead_p}\n\n"
        if len(paragraphs) > 1:
            sec1 += f"{paragraphs[1]}\n\n"

        sec2 = "### Key Developments & Immediate Implications\n\n"
        bullets = []
        tags = [
            "Primary Development",
            "Institutional & Regulatory Shift",
            "Key Metrics & Market Realities",
            "Operational Constraints",
            "Immediate Horizon"
        ]
        for idx, pt in enumerate(main_points[:5]):
            tag = tags[idx] if idx < len(tags) else f"Key Consideration {idx+1}"
            bullets.append(f"- **{tag}:** {pt}")
        if len(bullets) < 3:
            bullets.append("- **Strategic Assessment:** Fundamental variables indicate heightened scrutiny and near-term realignments.")
            bullets.append("- **Systemic Significance:** Cross-sector indicators illustrate broader economic reverberations.")
        sec2 += "\n\n".join(bullets) + "\n\n"

        sec3 = "### Detailed Background & Contextual Evidence\n\n"
        body_paras = paragraphs[2:] if len(paragraphs) > 2 else paragraphs
        sec3 += "\n\n".join(body_paras) if body_paras else f"{summary}\n\nStructural indicators reflect persistent real-world adjustments."

        sec4 = "\n\n### Concluding Overview & Strategic Outlook\n\n"
        sec4 += f"In conclusion, the situation surrounding {article.headline} marks a decisive inflection point. Decision-makers must navigate near-term policy choices and economic exposure with precision, as subsequent developments will determine broader stability."

        actual_content = f"{sec1}\n\n{sec2}\n\n{sec3}\n\n{sec4}".strip()
        return title, summary, actual_content

    def _build_10min_heuristic(self, article: Article, main_points: list[str]) -> tuple[str, str, str]:
        """Builds 10-minute variant: balanced structured narrative with background, explanations, and data bullets."""
        title = f"Strategic Analysis: {article.headline}"
        summary = article.lead if article.lead else (main_points[0] if main_points else "Balanced analytical assessment of driving factors.")

        paragraphs = [p.strip() for p in article.raw_content.split("\n\n") if p.strip() and not p.startswith("#")]
        lead_in = paragraphs[0] if paragraphs else summary

        sec_context = "### Context & Historical Precedent\n\n"
        if len(paragraphs) > 1:
            sec_context += f"{paragraphs[1]}\n\n"
        if len(paragraphs) > 2:
            sec_context += f"{paragraphs[2]}\n\n"
        else:
            sec_context += f"To understand current dynamics, one must examine the institutional and historical landscape underpinning {article.headline}. Previous market and policy shifts have established the framework within which current events unfold.\n\n"

        sec_dynamics = "### Structural Dynamics & Critical Arguments\n\n"
        sec_dynamics += (
            "The underlying mechanics involve both external pressures and internal institutional mandates "
            "(the regulatory and structural responsibilities governing stakeholder behavior). "
            "As decision-makers calibrate their responses, conflicting priorities between short-term stability "
            "and long-term structural viability become increasingly pronounced.\n\n"
        )
        if len(paragraphs) > 3:
            sec_dynamics += "\n\n".join(paragraphs[3:6]) + "\n\n"

        sec_metrics = "### Data & Key Empirical Metrics\n\n"
        metrics_bullets = []
        for idx, pt in enumerate(main_points):
            metrics_bullets.append(f"- **Pillar {idx+1}:** {pt}")
        if len(metrics_bullets) < 4:
            metrics_bullets.append("- **Market Exposure:** Measurable risk concentrations across primary sectors.")
            metrics_bullets.append("- **Comparative Benchmark:** Realignment tracking against broader historical indices.")
        sec_metrics += "\n\n".join(metrics_bullets) + "\n\n"

        sec_analysis = "### Analytical Assessment & Future Trajectory\n\n"
        remaining_paras = paragraphs[6:] if len(paragraphs) > 6 else paragraphs[:3]
        if remaining_paras:
            sec_analysis += "\n\n".join(remaining_paras) + "\n\n"
        sec_analysis += (
            "Looking forward, the strategic calculus will hinge on whether institutional actors can reconcile competing demands. "
            "The trajectory over the coming quarters will provide the decisive verdict on whether current mitigation strategies prove durable."
        )

        actual_content = f"{lead_in}\n\n{sec_context}\n\n{sec_dynamics}\n\n{sec_metrics}\n\n{sec_analysis}".strip()
        return title, summary, actual_content

    def _build_15min_heuristic(self, article: Article, main_points: list[str]) -> tuple[str, str, str]:
        """Builds 15-minute variant: full deep dive preserving nuanced perspectives, quotes, and comprehensive sections."""
        title = f"Comprehensive Deep Dive: {article.headline}"
        summary = article.lead if article.lead else (main_points[0] if main_points else "Comprehensive multi-dimensional deep-dive analysis.")

        paragraphs = [p.strip() for p in article.raw_content.split("\n\n") if p.strip() and not p.startswith("#")]
        lead_in = paragraphs[0] if paragraphs else summary

        sec_bg = "### Comprehensive Background & Historical Genesis\n\n"
        sec_bg += (
            f"The developments concerning {article.headline} cannot be evaluated in isolation. "
            "They reflect structural currents that have gathered momentum over years of policy and market evolution. "
            "Institutional stakeholders (ranging from governmental bodies to multinational market participants) "
            "find themselves confronting long-deferred systemic dilemmas.\n\n"
        )
        if len(paragraphs) > 1:
            sec_bg += f"{paragraphs[1]}\n\n"

        sec_tensions = "### Core Conflicts, Stakeholder Viewpoints & Expert Arguments\n\n"
        if len(paragraphs) > 2:
            sec_tensions += "\n\n".join(paragraphs[2:5]) + "\n\n"
        sec_tensions += (
            "Diverse stakeholders articulate contrasting priorities. Observers emphasizing orthodox fiscal or administrative prudence "
            "argue that concessions risk establishing perilous precedents. Conversely, reform proponents maintain that rigid adherence "
            "to legacy doctrines will exacerbate underlying vulnerabilities.\n\n"
        )

        sec_deep_dive = "### Multi-Sector Impact: Economic, Institutional & Geopolitical Dimensions\n\n"
        if len(paragraphs) > 5:
            sec_deep_dive += "\n\n".join(paragraphs[5:9]) + "\n\n"
        else:
            sec_deep_dive += (
                "On the economic frontier, cost structures and supply constraints continue to dictate commercial strategies. "
                "Simultaneously, the geopolitical dimension introduces non-trivial externalities that cannot easily be hedged.\n\n"
            )

        sec_evidence = "### Empirical Evidence & Synthesis of Key Pillars\n\n"
        pillars = []
        for idx, pt in enumerate(main_points):
            pillars.append(f"- **Strategic Pillar {idx+1}:** {pt} (Demonstrating systemic interconnectedness across the entire thematic ecosystem).")
        sec_evidence += "\n\n".join(pillars) + "\n\n"

        sec_conclusion = "### Thorough Synthesis & Long-Term Prognosis\n\n"
        if len(paragraphs) > 9:
            sec_conclusion += "\n\n".join(paragraphs[9:]) + "\n\n"
        sec_conclusion += (
            f"Ultimately, {article.headline} underscores the necessity of coherent, forward-looking stewardship. "
            "Whether through structural reforms, coordinated regulatory interventions, or renewed multilateral dialogue, "
            "the path chosen today will reverberate across international markets and policy circles for years to come."
        )

        actual_content = f"{lead_in}\n\n{sec_bg}\n\n{sec_tensions}\n\n{sec_deep_dive}\n\n{sec_evidence}\n\n{sec_conclusion}".strip()
        return title, summary, actual_content

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

        elif mode == ReadingMode.FIVE_MINUTES:
            title, summary, actual_content = self._build_5min_heuristic(article, main_points)

        elif mode == ReadingMode.TEN_MINUTES:
            title, summary, actual_content = self._build_10min_heuristic(article, main_points)

        elif mode == ReadingMode.FIFTEEN_MINUTES:
            title, summary, actual_content = self._build_15min_heuristic(article, main_points)

        else:
            title = article.headline
            summary = article.lead
            actual_content = article.raw_content

        word_count = preprocessor_service.calculate_word_count(f"{title} {summary} {actual_content}")
        reading_time = preprocessor_service.calculate_reading_time(word_count, wpm)

        if mode == ReadingMode.FIVE_MINUTES:
            est_mins = 5
        elif mode == ReadingMode.TEN_MINUTES:
            est_mins = 10
        elif mode == ReadingMode.FIFTEEN_MINUTES:
            est_mins = 15
        elif mode == ReadingMode.SIXTY_SECONDS:
            est_mins = 1
        else:
            est_mins = max(1, round(reading_time / 60))

        return FlexReadVariant(
            mode=mode,
            title=title,
            summary=summary,
            actual_content=actual_content,
            estimated_reading_time_minutes=est_mins,
            word_count=word_count,
            reading_time_seconds=reading_time,
            cached=False
        )

    def transform_article(self, article: Article, mode: ReadingMode, wpm: int = 220) -> FlexReadVariant:
        """Alias for generate_variant."""
        return self.generate_variant(article, mode, wpm=wpm)

    def transform_raw_text(
        self,
        raw_text: str,
        target_time_minutes: Union[int, str],
        wpm: int = 220
    ) -> Dict[str, Any]:
        """
        Transforms raw article text into the targeted reading mode (5, 10, 15 minutes, or full)
        strictly adhering to user specifications and output JSON format.
        """
        raw_clean = raw_text.strip()
        
        # 1. Parse target_time_minutes
        is_full = False
        target_mins: Optional[int] = None
        mode = ReadingMode.FULL

        if isinstance(target_time_minutes, str):
            clean_str = target_time_minutes.strip().lower()
            if clean_str in ("full", "full article", "full-article", "full_article", "original"):
                is_full = True
                mode = ReadingMode.FULL
            elif clean_str in ("15", "15min", "15m", "15 minutes", "15-minutes", "15_minutes", "fifteen", "fifteen minutes", "fifteen_minutes"):
                target_mins = 15
                mode = ReadingMode.FIFTEEN_MINUTES
            elif clean_str in ("10", "10min", "10m", "10 minutes", "10-minutes", "10_minutes", "ten", "ten minutes"):
                target_mins = 10
                mode = ReadingMode.TEN_MINUTES
            elif clean_str in ("5", "5min", "5m", "5 minutes", "5-minutes", "5_minutes", "five", "five minutes"):
                target_mins = 5
                mode = ReadingMode.FIVE_MINUTES
            else:
                try:
                    num = int(float(clean_str))
                    if num <= 5:
                        target_mins = 5
                        mode = ReadingMode.FIVE_MINUTES
                    elif num <= 10:
                        target_mins = 10
                        mode = ReadingMode.TEN_MINUTES
                    elif num <= 15:
                        target_mins = 15
                        mode = ReadingMode.FIFTEEN_MINUTES
                    else:
                        is_full = True
                        mode = ReadingMode.FULL
                except ValueError:
                    is_full = True
                    mode = ReadingMode.FULL
        elif isinstance(target_time_minutes, (int, float)):
            num = int(target_time_minutes)
            if num <= 5:
                target_mins = 5
                mode = ReadingMode.FIVE_MINUTES
            elif num <= 10:
                target_mins = 10
                mode = ReadingMode.TEN_MINUTES
            elif num <= 15:
                target_mins = 15
                mode = ReadingMode.FIFTEEN_MINUTES
            else:
                is_full = True
                mode = ReadingMode.FULL
        else:
            is_full = True
            mode = ReadingMode.FULL

        # Extract title and summary candidates from raw_text
        lines = [line.strip() for line in raw_clean.split("\n") if line.strip()]
        first_line = lines[0] if lines else "Adapted Article"
        if first_line.startswith("#"):
            first_line = first_line.lstrip("#").strip()
        headline = first_line if len(first_line) < 140 else first_line[:137] + "..."
        lead = lines[1] if len(lines) > 1 and not lines[1].startswith("#") else (raw_clean[:200] + "...")

        # 2. If full is requested: Set actual_content directly to raw_text with zero structural edits.
        # Compute estimated_reading_time_minutes based on total word count at 200 words per minute.
        if is_full or mode == ReadingMode.FULL:
            word_count = len(raw_clean.split())
            est_time = max(1, round(word_count / 200))
            return {
                "title": headline,
                "summary": lead,
                "actual_content": raw_text,
                "estimated_reading_time_minutes": est_time,
                "word_count": word_count
            }

        # 3. If Gemini client is active, attempt direct LLM generation
        if self._client:
            try:
                system_instruction = prompt_engine.get_system_instruction()
                user_prompt = prompt_engine.create_raw_text_prompt(raw_text, target_mins or mode.value)
                from google.genai import types
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                        response_mime_type="application/json"
                    )
                )
                if response and response.text:
                    cleaned_json = response.text.strip()
                    if cleaned_json.startswith("```"):
                        cleaned_json = re.sub(r"^```(?:json)?\n", "", cleaned_json)
                        cleaned_json = re.sub(r"\n```$", "", cleaned_json)
                    data = json.loads(cleaned_json)
                    if "title" in data and "actual_content" in data:
                        content = data["actual_content"]
                        wc = data.get("word_count") or len(content.split())
                        est_min = data.get("estimated_reading_time_minutes") or (target_mins if target_mins else max(1, round(wc / 200)))
                        return {
                            "title": data.get("title", headline),
                            "summary": data.get("summary", lead),
                            "actual_content": content,
                            "estimated_reading_time_minutes": int(est_min),
                            "word_count": int(wc)
                        }
            except Exception as e:
                logger.error(f"Gemini API call failed during transform_raw_text: {e}. Falling back to deterministic heuristic.")

        # 4. Fallback Heuristic Generator for 5, 10, 15 minutes
        temp_article = Article(
            id="raw_transform",
            headline=headline,
            lead=lead,
            section="Analysis",
            raw_content=raw_text
        )
        prep = preprocessor_service.process(temp_article, wpm=wpm)
        temp_article.preprocessing = prep
        main_points = prep.main_points or [lead]

        if mode == ReadingMode.FIVE_MINUTES:
            title, summary, actual_content = self._build_5min_heuristic(temp_article, main_points)
        elif mode == ReadingMode.TEN_MINUTES:
            title, summary, actual_content = self._build_10min_heuristic(temp_article, main_points)
        elif mode == ReadingMode.FIFTEEN_MINUTES:
            title, summary, actual_content = self._build_15min_heuristic(temp_article, main_points)
        else:
            title, summary, actual_content = headline, lead, raw_text

        wc = len(actual_content.split())
        est_min = target_mins if target_mins else max(1, round(wc / 200))
        return {
            "title": title,
            "summary": summary,
            "actual_content": actual_content,
            "estimated_reading_time_minutes": int(est_min),
            "word_count": int(wc)
        }

gemini_client_service = GeminiClientService()
gemini_client = gemini_client_service
