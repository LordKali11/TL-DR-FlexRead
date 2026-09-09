import json
from typing import Any, Dict, Optional, Union
from ..models.article import Article, ReadingMode, ArticlePreprocessing

class PromptEngine:
    """
    Structured Prompt Engineering for NZZ FlexRead powered by Google AntiGravity & Gemini.
    Strictly tailored for English-language delivery, preserving NZZ's distinct editorial voice.
    Supports agile time-budget reading variants (60s, bullet_points, inline_simplified, 5min, 10min, 15min, full).
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

- "5min" (5-Minute Mode / 5 minutes, ~1,000 to 1,250 words):
  * Focus on essential takeaways, primary facts, key figures, and immediate implications.
  * Structure: Executive summary section, 3-5 structured bullet points highlighting key developments, and a brief concluding overview.
  * Tone: Direct, sober, concise, and focused on core facts.

- "10min" (10-Minute Mode / 10 minutes, ~2,000 to 2,500 words):
  * Provide a balanced, structured narrative that includes important background context, supporting data points, and secondary arguments.
  * Structure: Short lead-in, thematic section headers, simplified inline explanations for complex concepts, and bullet points for data/metrics.
  * Tone: Analytical, clear, and easy to skim.

- "15min" (15-Minute Mode / 15 minutes, ~3,000 to 3,750 words):
  * Deliver a deep-dive analysis. Preserve nuanced perspectives, historical context, stakeholder viewpoints, and expert quotes.
  * Structure: Full long-form narrative with structured sections, complete background, detailed inline explanations, and comprehensive summaries.
  * Tone: Deeply analytical, authoritative, and thorough.

- "full" (Full Mode / Full Article):
  * Return the complete raw_text in actual_content without removing, summarizing, or modifying any text.
  * Compute estimated_reading_time_minutes based on total word count at 200 words per minute.

OUTPUT FORMAT REQUIREMENTS:
Return strict RFC 8259 JSON matching this structure:
CRITICAL: Escape all double quotes and internal newlines within JSON string values (e.g. use \n for line breaks, \" for nested quotes) so that the JSON string literals parse cleanly.
{
  "title": "Adapted headline fitting the selected mode",
  "summary": "1-2 sentence executive briefing",
  "actual_content": "Markdown-formatted text body for the target mode or full text",
  "estimated_reading_time_minutes": 5,
  "word_count": 1000
}

EXECUTION INSTRUCTIONS:
Evaluate target_time_minutes:
If full is requested: Set actual_content directly to raw_text with zero structural edits.
If a numerical time (5, 10, or 15) is requested: Transform raw_text into the targeted length using an average reading speed of 200-250 words per minute:
- 5 minutes: ~1,000 to 1,250 words
- 10 minutes: ~2,000 to 2,500 words
- 15 minutes: ~3,000 to 3,750 words
Calculate and populate accurate word_count and estimated_reading_time_minutes values.
Do not output markdown code fences (```json ... ```) or any extraneous text. Return ONLY the JSON object.
"""

    @classmethod
    def create_generation_prompt(
        cls,
        article: Article,
        mode: ReadingMode,
        preprocessing: Optional[ArticlePreprocessing] = None,
        target_time_minutes: Optional[int] = None
    ) -> str:
        """
        Builds the user prompt combining article metadata, preprocessing insights, and mode instructions.
        Supports 60s, bullet_points, inline_simplified, 5min, 10min, 15min, and full modes.
        """
        prep = preprocessing or article.preprocessing
        
        main_points_str = "\n".join([f"- {p}" for p in (prep.main_points or [])]) if prep else "None"
        keywords_str = ", ".join(prep.keywords or []) if prep else "None"
        tone_str = prep.tone.value if prep else "analytical"
        length_tier_str = prep.article_length.value if prep else "medium"

        # Resolve target duration in minutes
        target_mins = target_time_minutes
        if not target_mins:
            if mode == ReadingMode.FIVE_MINUTES:
                target_mins = 5
            elif mode == ReadingMode.TEN_MINUTES:
                target_mins = 10
            elif mode == ReadingMode.FIFTEEN_MINUTES:
                target_mins = 15
            elif mode == ReadingMode.SIXTY_SECONDS:
                target_mins = 1
        
        target_time_desc = f"{target_mins} minutes" if target_mins else f"mode: {mode.value}"

        prompt = f"""INPUT DATA:

raw_text:
{article.raw_content[:25000]}

target_time_minutes: {target_mins if target_mins else mode.value}

ARTICLE CONTEXT:
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

TASK:
Generate the reading variant for mode: "{mode.value}" (target reading time: {target_time_desc}).
LANGUAGE: ENGLISH ONLY.

Compute the exact output target length assuming an average reading speed of 200-250 words per minute:
- 5 minutes: ~1,000 to 1,250 words
- 10 minutes: ~2,000 to 2,500 words
- 15 minutes: ~3,000 to 3,750 words

Produce the final content adhering strictly to the JSON contract without changing the core factual accuracy or editorial integrity of the input text:
CRITICAL JSON FORMATTING REQUIREMENT:
Escape all quotes and newlines inside the JSON string values (e.g. use \n for line breaks, \" for inner quotes) so that the entire output is strictly valid RFC 8259 JSON.
{{
  "title": "Adapted, clear headline fitting the duration",
  "summary": "1-2 sentence executive briefing",
  "actual_content": "Markdown-formatted text body tailored to the exact reading time",
  "estimated_reading_time_minutes": {target_mins if target_mins else 5},
  "word_count": <computed_word_count>
}}
Do not output markdown code fences or any extraneous text. Return ONLY the JSON object.
"""
        return prompt

    @classmethod
    def create_raw_text_prompt(
        cls,
        raw_text: str,
        target_time_minutes: Union[int, str]
    ) -> str:
        """
        Builds the raw text transformation prompt adhering strictly to the user specification.
        """
        mins_str = str(target_time_minutes).strip()
        return f"""INPUT DATA:

raw_text:
{raw_text}

target_time_minutes: {mins_str}

OUTPUT FORMAT REQUIREMENTS:
Return strict JSON matching this structure:

{{
  "title": "Adapted headline fitting the selected mode",
  "summary": "1-2 sentence executive briefing",
  "actual_content": "Markdown-formatted text body for the target mode or full text",
  "estimated_reading_time_minutes": 5,
  "word_count": 1000
}}

TRANSFORMATION GUIDELINES BY TARGET TIME:

5-Minute Mode (~1,000 to 1,250 words):
Focus on essential takeaways, primary facts, key figures, and immediate implications.
Structure: Executive summary section, 3-5 structured bullet points highlighting key developments, and a brief concluding overview.
Tone: Direct, sober, concise, and focused on core facts.

10-Minute Mode (~2,000 to 2,500 words):
Provide a balanced, structured narrative that includes important background context, supporting data points, and secondary arguments.
Structure: Short lead-in, thematic section headers, simplified inline explanations for complex concepts, and bullet points for data/metrics.
Tone: Analytical, clear, and easy to skim.

15-Minute Mode (~3,000 to 3,750 words):
Deliver a deep-dive analysis. Preserve nuanced perspectives, historical context, stakeholder viewpoints, and expert quotes.
Structure: Full long-form narrative with structured sections, complete background, detailed inline explanations, and comprehensive summaries.
Tone: Deeply analytical, authoritative, and thorough.

Full Mode / Full Article:
Return the complete raw_text in actual_content without removing, summarizing, or modifying any text.
Compute estimated_reading_time_minutes based on total word count at 200 words per minute.

EXECUTION INSTRUCTIONS:

Evaluate target_time_minutes:
If full is requested: Set actual_content directly to raw_text with zero structural edits.
If a numerical time (5, 10, or 15) is requested: Transform raw_text into the targeted length using an average reading speed of 200–250 words per minute:
5 minutes: ~1,000 to 1,250 words
10 minutes: ~2,000 to 2,500 words
15 minutes: ~3,000 to 3,750 words

Calculate and populate accurate word_count and estimated_reading_time_minutes values.

Return valid RFC 8259 JSON strictly adhering to the output format. Ensure all internal newlines and quotes inside strings are escaped properly (e.g. use \n and \").
"""

    @classmethod
    def create_preprocessing_prompt(cls, article_dict: Dict[str, Any]) -> str:
        """
        Creates the Step 1 prompt embedding the ArticlePreprocessing JSON template
        (main_points, keywords, tone, article_length, reading_time, word_count)
        and instructs Gemini to populate it based on the full article JSON context.
        """
        article_json_str = json.dumps(article_dict, indent=2, ensure_ascii=False, default=str)

        return f"""You are the NZZ Editorial Preprocessing Engine.
STEP 1: ARTICLE ANALYSIS & CONTEXT EXTRACTION

Analyze the following full article JSON context:
```json
{article_json_str}
```

TASK:
Extract the editorial and semantic metadata according to the strict ArticlePreprocessing specification:
1. main_points: A list of 3-6 bullet-proof, analytical takeaways highlighting the core development, underlying tensions, and key implications.
2. keywords: A list of 5-10 topical, semantic, and named entity keywords.
3. tone: Exactly one of: "analytical", "investigative", "opinion_commentary", "reportage", "sober_briefing".
4. article_length: Exactly one of: "short" (<500 words), "medium" (500-1000 words), "long" (1000-2500 words), "longform" (>2500 words).
5. word_count: Total word count of original article text.
6. reading_time: Reading time in seconds calculated at 220 words per minute (word_count / 220 * 60).
7. reading_time_minutes: Reading time in minutes rounded to 1 decimal place.

OUTPUT FORMAT REQUIREMENTS:
Return strictly valid JSON matching this template:
{{
  "main_points": [
    "Core takeaway 1",
    "Core takeaway 2",
    "Core takeaway 3"
  ],
  "keywords": [
    "keyword1",
    "keyword2",
    "keyword3"
  ],
  "tone": "analytical",
  "article_length": "medium",
  "reading_time": 180,
  "reading_time_minutes": 3.0,
  "word_count": 650
}}

Do not output markdown code fences (```json ... ```) or any conversational text. Return ONLY the JSON object.
"""

    @classmethod
    def create_two_step_synthesis_prompt(
        cls,
        article_dict: Dict[str, Any],
        context_dict: Dict[str, Any],
        mode: Union[ReadingMode, str]
    ) -> str:
        """
        Creates the Step 2 prompt feeding both the raw article JSON and the populated
        contextual JSON, instructing Gemini to synthesize the summary matching the requested reading mode.
        """
        mode_val = mode.value if isinstance(mode, ReadingMode) else str(mode)
        article_json_str = json.dumps(article_dict, indent=2, ensure_ascii=False, default=str)
        context_json_str = json.dumps(context_dict, indent=2, ensure_ascii=False, default=str)

        mode_instructions = {
            "60s": "Target length: 100-140 words (~60s). Structure: Crisp title, single powerful summary sentence, and exactly 3 bullets: **The Essentials:**, **The Crux:**, and **What Matters Now:**.",
            "bullet_points": "Target length: 200-300 words (~90-120s). Structure: Analytical title, 2-sentence summary, 4-6 thematic bullets with bold categorical tags (e.g. **Core Development:**, **Context & Background:**, **Economic Dimension:**, **Critical Assessment:**, **Outlook & Implications:**).",
            "inline_simplified": "Target length: 350-500 words (~2-2.5m). Structure: Engaging headline, 2-sentence lead, flowing narrative under 2-3 subheadings (###) breaking down dense academic/technical syntax.",
            "5min": "Target length: ~1,000 to 1,250 words (5 minutes). Structure: Executive summary section, 3-5 structured bullets highlighting key developments, and a brief concluding overview. Tone: Direct, sober, concise.",
            "10min": "Target length: ~2,000 to 2,500 words (10 minutes). Structure: Short lead-in, thematic section headers (###), simplified inline explanations, and data bullets. Tone: Analytical, clear, easy to skim.",
            "15min": "Target length: ~3,000 to 3,750 words (15 minutes). Structure: Full long-form deep-dive with structured sections, complete background context, stakeholder viewpoints, and expert quotes. Tone: Deeply analytical and authoritative.",
            "full": "Full Mode: Output complete raw text in actual_content with ZERO structural edits. Compute estimated reading time at 200 words per minute."
        }
        instruction_for_mode = mode_instructions.get(mode_val, f"Synthesize variant for mode: {mode_val}.")

        target_mins = 5
        if mode_val in ("60s", "1"):
            target_mins = 1
        elif mode_val in ("5min", "5", "5 minutes"):
            target_mins = 5
        elif mode_val in ("10min", "10", "10 minutes"):
            target_mins = 10
        elif mode_val in ("15min", "15", "15 minutes"):
            target_mins = 15

        return f"""You are the NZZ Editorial Synthesis Engine.
STEP 2: TWO-STEP SYNTHESIS WITH CONTEXTUAL INSIGHTS

You are provided with:
1. RAW ARTICLE JSON:
```json
{article_json_str}
```

2. POPULATED CONTEXTUAL JSON (METADATA & EDITORIAL INSIGHTS):
```json
{context_json_str}
```

TARGET READING MODE: "{mode_val}"
MODE GUIDELINES:
{instruction_for_mode}

TASK:
Using BOTH the raw article context and the extracted contextual insights (main points, keywords, tone, length tier), synthesize the reading variant for mode "{mode_val}".
Language: Sophisticated, authoritative English only.

OUTPUT FORMAT REQUIREMENTS:
Return strict JSON matching this structure:
{{
  "title": "Adapted headline fitting the selected mode",
  "summary": "1-2 sentence executive briefing",
  "actual_content": "Markdown-formatted text body tailored to the target mode",
  "estimated_reading_time_minutes": {target_mins},
  "word_count": <computed_word_count>
}}

Do not output markdown code fences (```json ... ```) or any conversational text. Return ONLY the JSON object.
"""

    @classmethod
    def get_system_instruction(cls) -> str:
        """Returns English system prompt for Gemini / Vertex AI."""
        return cls.SYSTEM_PROMPT.strip()

prompt_engine = PromptEngine()
