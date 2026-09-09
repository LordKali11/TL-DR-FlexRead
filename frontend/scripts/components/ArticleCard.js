    /* ArticleCard */
    function ArticleCard({ article, user, onOpenReader }) {
      const dossierCount = article.dossierCount || (article.progressiveExpanders || article.expanders || []).length;
      const rec = (window.getRecommendedReadingTier && window.getRecommendedReadingTier(article, user)) || {
        tier: 'analytical',
        minutes: (article.readingTimes && article.readingTimes.analytical) || 7,
        label: `${(article.readingTimes && article.readingTimes.analytical) || 7}m Rec`,
        reason: 'Recommended for standard analytical focus'
      };

      return (
        <article className="article-card" onClick={() => onOpenReader(article, rec.tier)}>
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
            <div className="card-kicker">{article.kicker}</div>
            <h2 className="card-title">{article.title}</h2>
            <p className="card-subtitle">{article.subtitle}</p>

            <div className="card-byline">
              <span className="author-name">{article.author}</span>
              <span className="author-role">{article.authorRole}</span>
            </div>

            <div className="card-footer">
              <div className="reading-depth-block">
                <div className="reading-depth-header">
                  <span className="depth-title">Reading Depth</span>
                  <span className="depth-hint">Select to jump</span>
                </div>
                <div className="reading-budget-strip">
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
                  <button
                    type="button"
                    className="budget-chip chip-recommended"
                    title={`${rec.reason} (${rec.minutes} min)`}
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenReader(article, rec.tier);
                    }}
                  >
                    ★ {rec.minutes}m Rec
                  </button>
                  <button
                    type="button"
                    className="budget-chip chip-bullets"
                    title="View core takeaways and argument points in Bullet Mode"
                    onClick={(e) => {
                      e.stopPropagation();
                      onOpenReader(article, 'bullets');
                    }}
                  >
                    ● Bullets
                  </button>
                </div>
              </div>

              <button
                type="button"
                className="btn-read-action"
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenReader(article, rec.tier);
                }}
              >
                <span>Read Article</span>
                <span className="btn-arrow" aria-hidden="true">&rarr;</span>
              </button>
            </div>
          </div>
        </article>
      );
    }


window.ArticleCard = ArticleCard;
