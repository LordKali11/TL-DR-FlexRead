import React from 'react';
import { Article, ReadingTier } from '../types';

interface ArticleCardProps {
  article: Article;
  onOpenReader: (article: Article, initialTier?: ReadingTier) => void;
}

export const ArticleCard: React.FC<ArticleCardProps> = ({ article, onOpenReader }) => {
  const dossierCount = article.dossierCount || (article.progressiveExpanders || article.expanders || []).length;

  return (
    <article className="article-card" onClick={() => onOpenReader(article, 'briefing')}>
      {/* Visual Header */}
      <div className="card-media-wrap">
        <img
          src={article.heroImage}
          alt={article.title}
          className="card-media-img"
          loading="lazy"
        />
        <span className="topic-badge">{article.topic}</span>
        {dossierCount > 0 && (
          <span className="card-dossier-badge">{dossierCount} Dossiers</span>
        )}
      </div>

      <div className="card-body">
        {/* Kicker */}
        <div className="card-kicker">{article.kicker}</div>

        {/* Headline */}
        <h2 className="card-title">{article.title}</h2>

        {/* Subtitle / Excerpt */}
        <p className="card-subtitle">{article.subtitle}</p>

        {/* Flex Read Reading Budget Matrix with 1-click depth launch */}
        <div className="reading-budget-strip">
          <span className="budget-label">Reading Budget:</span>
          <button
            type="button"
            className="budget-chip chip-briefing"
            title={`Read ${article.readingTimes.briefing} min Executive Briefing`}
            onClick={(e) => {
              e.stopPropagation();
              onOpenReader(article, 'briefing');
            }}
          >
            {article.readingTimes.briefing}m Brief
          </button>
          <button
            type="button"
            className="budget-chip chip-analytical"
            title={`Read ${article.readingTimes.analytical} min Analytical Depth`}
            onClick={(e) => {
              e.stopPropagation();
              onOpenReader(article, 'analytical');
            }}
          >
            {article.readingTimes.analytical}m Analysis
          </button>
          <button
            type="button"
            className="budget-chip chip-full"
            title={`Read ${article.readingTimes.full} min Full Narrative`}
            onClick={(e) => {
              e.stopPropagation();
              onOpenReader(article, 'full');
            }}
          >
            {article.readingTimes.full}m Full
          </button>
        </div>

        {/* Semantic Layers Available (Clean Swiss monochrome labels) */}
        <div className="argument-layers-preview">
          <span className="layer-dot dot-thesis" title="Core Thesis included">Thesis</span>
          <span className="layer-dot dot-evidence" title="Causal Evidence included">Evidence</span>
          <span className="layer-dot dot-counterpoint" title="Counter-arguments included">Balance</span>
          <span className="layer-dot dot-data" title="Quantitative Data included">Metrics</span>
        </div>

        {/* Author Byline & Action */}
        <div className="card-footer">
          <div className="author-meta">
            <span className="author-name">{article.author}</span>
            <span className="author-role">{article.authorRole}</span>
          </div>

          <button
            className="btn-read-action"
            onClick={(e) => {
              e.stopPropagation();
              onOpenReader(article, 'briefing');
            }}
          >
            Read Article &rarr;
          </button>
        </div>
      </div>
    </article>
  );
};
