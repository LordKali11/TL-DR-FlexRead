import re
from collections import Counter
from typing import List, Optional
from ..models.article import Article, ArticlePreprocessing, LengthTier, ToneCategory
from ..config import settings

# English-focused stopwords with German bilingual support
STOPWORDS = {
    # English primary
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from",
    "up", "about", "into", "over", "after", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "can", "could", "will", "would", "shall", "should",
    "may", "might", "must", "that", "which", "who", "whom", "this", "these", "those", "it", "its",
    "they", "their", "them", "he", "him", "his", "she", "her", "we", "us", "our", "not", "also",
    "more", "than", "most", "just", "now", "then", "there", "here", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "other", "some", "such", "no", "nor", "only", "own",
    "same", "so", "very", "can", "cannot", "could",
    # German fallback
    "der", "die", "das", "ein", "eine", "einer", "eines", "einem", "einen", "und", "oder", "aber",
    "dass", "da", "den", "dem", "des", "im", "in", "an", "auf", "aus", "bei", "mit", "nach", "von",
    "zu", "zum", "zur", "über", "unter", "vor", "zwischen", "ist", "sind", "war", "waren", "wird",
    "werden", "wurde", "wurden", "hat", "hatte", "haben", "hätte", "kann", "könnte", "muss", "müssen",
    "soll", "sollte", "nicht", "auch", "noch", "nur", "wie", "so", "als", "für", "um", "am", "es"
}

class ArticlePreprocessor:
    """
    Executes the preprocessing phase for an article in English:
    Defines:
    - main_points (core argumentative takeaways)
    - keywords (semantic entities & terms)
    - tone (analytical, opinion_commentary, investigative, etc.)
    - article_length (tier: short, medium, long, longform)
    - reading_time (in seconds and minutes)
    - word_count
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """Removes markdown tags, image captions, and extra whitespace."""
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)  # Images
        text = re.sub(r"\[.*?\]\(.*?\)", "", text)  # Links
        text = re.sub(r"^#+\s+.*$", "", text, flags=re.MULTILINE)  # Headings
        text = re.sub(r">\s+.*$", "", text, flags=re.MULTILINE)  # Blockquotes
        text = re.sub(r"[\*_`~]", "", text)  # Bold/Italics
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def calculate_word_count(cls, text: str) -> int:
        """Calculates accurate word count."""
        cleaned = cls.clean_text(text)
        words = re.findall(r"\b[\w\-']+\b", cleaned)
        return len(words)

    @classmethod
    def calculate_reading_time(cls, word_count: int, wpm: int = 220) -> int:
        """Returns reading time in seconds, minimum 15 seconds."""
        seconds = int((word_count / max(wpm, 60)) * 60)
        return max(15, seconds)

    @staticmethod
    def determine_length_tier(word_count: int) -> LengthTier:
        """Classifies length into tiers."""
        if word_count < 500:
            return LengthTier.SHORT
        elif word_count < 1000:
            return LengthTier.MEDIUM
        elif word_count < 2500:
            return LengthTier.LONG
        else:
            return LengthTier.LONGFORM

    @staticmethod
    def detect_tone(article: Article, full_text: str) -> ToneCategory:
        """Detects editorial tone with English and German journalistic markers."""
        section = (article.section or "").lower()
        headline = article.headline.lower()
        text_lower = full_text.lower()
        
        # Opinion & Commentary
        opinion_markers = [
            "opinion", "commentary", "editorial", "column", "perspective", "viewpoint",
            "essay", "meinung", "der andere blick", "kommentar", "kolumne", "debatte"
        ]
        if any(marker in section for marker in opinion_markers) \
           or any(marker in headline for marker in ["comment:", "opinion:", "column:", "editorial:", "plea:"]):
            return ToneCategory.OPINION_COMMENTARY
        
        # Culture & Arts Reportage
        reportage_markers = ["culture", "arts", "books", "feuilleton", "panorama", "society", "lifestyle"]
        if any(marker in section for marker in reportage_markers):
            return ToneCategory.REPORTAGE
        
        # Investigative
        investigative_markers = [
            "investigation", "reveals", "uncovered", "documents show", "allegations",
            "scandal", "exclusive probe", "confidential", "whistleblower", "leak",
            "recherche", "enthüllt", "aufgedeckt", "vorwürfe"
        ]
        if any(marker in text_lower[:2500] for marker in investigative_markers):
            return ToneCategory.INVESTIGATIVE
        
        # Short briefing
        if "briefing" in section or "ticker" in section or len(full_text.split()) < 80:
            return ToneCategory.SOBER_BRIEFING
        
        # Default NZZ editorial hallmark: Analytical
        return ToneCategory.ANALYTICAL

    @classmethod
    def extract_keywords(cls, headline: str, lead: str, body: str, max_keywords: int = 8) -> List[str]:
        """Extracts prominent English semantic keywords and named entities."""
        combined_text = f"{headline}. {lead}. {body}"
        raw_tokens = re.findall(r"\b[A-ZÄÖÜ][a-zäöüßA-Z0-9\-]{2,}\b", combined_text)
        
        filtered = [
            token for token in raw_tokens 
            if token.lower() not in STOPWORDS 
            and not token.isdigit()
            and len(token) > 2
        ]
        
        counts = Counter(filtered)
        # Extra weight to words appearing in headline and lead
        headline_lead_words = set(re.findall(r"\b[A-ZÄÖÜ][a-zäöüßA-Z0-9\-]{2,}\b", f"{headline} {lead}"))
        for word in headline_lead_words:
            if word in counts:
                counts[word] += 4
                
        keywords = [word for word, _ in counts.most_common(max_keywords)]
        return keywords

    @classmethod
    def extract_main_points(cls, headline: str, lead: str, body: str, existing_points: Optional[List[str]] = None) -> List[str]:
        """
        Synthesizes 3-5 main argumentative points in English.
        Prioritizes existing curated bullets when available.
        """
        if existing_points and len(existing_points) >= 2:
            return [pt.strip() for pt in existing_points if pt.strip()][:5]
        
        points = []
        # First point: The core news hook from lead
        if lead.strip():
            sentences = re.split(r"(?<=[.!?])\s+", lead.strip())
            if sentences:
                points.append(sentences[0])
        
        # Extract pivotal sentences from body paragraphs
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and not p.startswith("#")]
        
        argument_markers = [
            "crucial", "essential", "however", "consequently", "result", "signals",
            "indicates", "highlights", "key driver", "analysts note", "critics argue",
            "in the future", "significantly", "fundamental", "turning point",
            "entscheidend", "wichtig", "zeigt", "bedeutet"
        ]

        for p in paragraphs:
            if len(points) >= 4:
                break
            p_sentences = re.split(r"(?<=[.!?])\s+", p)
            for s in p_sentences:
                clean_s = s.strip()
                if 40 < len(clean_s) < 240:
                    if any(marker in clean_s.lower() for marker in argument_markers):
                        if clean_s not in points:
                            points.append(clean_s)
                            break
        
        # Fallback if too few points found
        if len(points) < 2 and paragraphs:
            for p in paragraphs[:3]:
                sentences = re.split(r"(?<=[.!?])\s+", p)
                if sentences and sentences[0] not in points and len(sentences[0]) > 30:
                    points.append(sentences[0])
                    if len(points) >= 3:
                        break

        return points

    def process(self, article: Article, wpm: int = 220) -> ArticlePreprocessing:
        """
        Runs the full preprocessing phase and returns ArticlePreprocessing metadata.
        """
        full_content = f"{article.headline}\n\n{article.lead}\n\n{article.raw_content}"
        word_count = self.calculate_word_count(full_content)
        reading_time = self.calculate_reading_time(word_count, wpm)
        length_tier = self.determine_length_tier(word_count)
        tone = self.detect_tone(article, full_content)
        keywords = self.extract_keywords(article.headline, article.lead, article.raw_content)
        
        existing_bullets = article.preprocessing.main_points if article.preprocessing else None
        main_points = self.extract_main_points(
            headline=article.headline,
            lead=article.lead,
            body=article.raw_content,
            existing_points=existing_bullets
        )
        
        return ArticlePreprocessing(
            main_points=main_points,
            keywords=keywords,
            tone=tone,
            article_length=length_tier,
            reading_time=reading_time,
            reading_time_minutes=round(reading_time / 60.0, 1),
            word_count=word_count
        )

preprocessor_service = ArticlePreprocessor()
