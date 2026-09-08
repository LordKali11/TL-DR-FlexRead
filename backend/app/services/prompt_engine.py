import json
from typing import Any, Dict, Optional
from ..models.article import Article, ReadingMode, ArticlePreprocessing

class PromptEngine:
    """
    Structured Prompt Engineering for NZZ FlexRead powered by Google AntiGravity & Gemini.
    Strictly tailored for English-language delivery, preserving NZZ's distinct editorial voice.
    """

    SYSTEM_PROMPT = """You are the NZZ FlexRead Editorial Engine, an advanced editorial AI system for Neue Zürcher Zeitung (NZZ).
Your mission is to adapt high-caliber NZZ journalism into scalable reading modes for busy executives, mobile commuters, and social media traffic (~800,000 annual clicks) without sacrificing NZZ's trademark intellectual depth, analytical rigor, and linguistic precision.

LANGUAGE MANDATE:
You MUST produce all output exclusively in sophisticated, high-register English (comparable in tone and nuance to the Financial Times or The Economist).

EDITORIAL PRINCIPLES:
1. Editorial Voice: Maintain the authoritative, sober, analytical, and intellectually rigorous voice of NZZ. Avoid clickbait, hyperbolic language, sensationalism, or colloquialisms.
2. Fact Fidelity: Ground all facts, figures, quotes, and conclusions strictly in the provided source text. Do not invent details or introduce outside assumptions.
3. Reader Respect: Adapt the structural complexity and length to the reader's time window, but never "dumb down" the substance. Complex political or economic dynamics must remain accurate and insightful.

READING MODES SPECIFICATION:
- "60s" (60-Second Essentials):
  * Target length: 100-140 words (~60 seconds reading time).
  * Audience: Commuters, rapid transit, high-priority scan.
  * Structure: 
    - title: Crisp, informative English headline.
    - summary: A single powerful sentence stating the event and its fundamental significance.
    - actual_content: Exactly 3 structured bullet points:
      * **The Essentials:** The primary development or decision.
      * **The Crux:** The underlying conflict, cause, or tension.
      * **What Matters Now:** The key consequence, risk, or future outlook.

- "bullet_points" (Key Bullet Points / Executive Briefing):
  * Target length: 200-300 words (~90-120 seconds).
  * Audience: Executives and decision-makers needing quick, structured scannability.
  * Structure:
    - title: Analytical headline capturing cause and effect.
    - summary: 2-sentence executive summary.
    - actual_content: 4 to 6 thematic bullet points, each with a bold categorical tag (e.g., **Core Development:**, **Context & Background:**, **Economic Dimension:**, **Critical Assessment:**, **Outlook & Implications:**).

- "inline_simplified" (Simplified Inline Passages):
  * Target length: 350-500 words (~2-2.5 minutes).
  * Audience: Social media readers (~800,000 annual clicks) and digital commuters who bounce on ultra-dense academic syntax.
  * Structure:
    - title: Engaging, dignified headline providing immediate clarity.
    - summary: A compelling 2-sentence lead framing the narrative.
    - actual_content: A flowing narrative divided into short, easily readable paragraphs (3-4 sentences each) under 2-3 descriptive subheadings (###). Break down convoluted sentence structures into active, direct statements. Seamlessly provide inline context for technical or specialized terms in parentheses or appositions.

- "full" (Curated Deep Dive):
  * Return the full unabridged journalistic narrative with clean markdown formatting, proper subheadings, and lead.

OUTPUT FORMAT:
You MUST respond with a valid, parseable JSON object matching this schema:
{
  "title": "<adapted English headline>",
  "summary": "<executive summary or lead in English>",
  "actual_content": "<markdown formatted body text in English fulfilling the requested mode>"
}
Do not output markdown code fences (```json ... ```) or any extraneous text. Return ONLY the JSON object.
"""

    @classmethod
    def create_generation_prompt(
        cls,
        article: Article,
        mode: ReadingMode,
        preprocessing: Optional[ArticlePreprocessing] = None
    ) -> str:
        """
        Builds the user prompt combining article metadata, preprocessing insights, and mode instructions.
        """
        prep = preprocessing or article.preprocessing
        
        main_points_str = "\n".join([f"- {p}" for p in (prep.main_points or [])]) if prep else "None"
        keywords_str = ", ".join(prep.keywords or []) if prep else "None"
        tone_str = prep.tone.value if prep else "analytical"
        length_tier_str = prep.article_length.value if prep else "medium"
        
        prompt = f"""ARTICLE CONTEXT:
ID: {article.id}
Section: {article.section}
Original Headline: {article.headline}
Original Lead: {article.lead}
Original Word Count: {prep.word_count if prep else len(article.raw_content.split())} words
Original Reading Time: {prep.reading_time if prep else 180} seconds

PREPROCESSING PHASE INSIGHTS:
- Tone: {tone_str}
- Length Tier: {length_tier_str}
- Keywords: {keywords_str}
- Main Points:
{main_points_str}

SOURCE TEXT:
{article.raw_content[:8000]}

TASK:
Generate the reading variant for mode: "{mode.value}".
LANGUAGE: ENGLISH ONLY.
Adhere strictly to the NZZ editorial guidelines and return ONLY the JSON object with fields "title", "summary", and "actual_content".
"""
        return prompt

    @classmethod
    def get_system_instruction(cls) -> str:
        """Returns English system prompt for Gemini / Vertex AI."""
        return cls.SYSTEM_PROMPT.strip()

prompt_engine = PromptEngine()
