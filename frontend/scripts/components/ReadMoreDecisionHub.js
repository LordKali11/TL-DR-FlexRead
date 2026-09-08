/* ReadMoreDecisionHub.js
   Neue Zürcher Zeitung (NZZ) - End-of-Article Recommended Articles
   Updated: Removed 3m/7m/18m depth switching (now handled exclusively via the floating bubble & top toolbar)
   Now purely displays Recommended Articles to Read based on available time.
*/

function ReadMoreDecisionHub(props) {
  const {
    article,
    tier,
    currentTier,
    otherArticles,
    nextArticles,
    onSelectArticle,
    onSelectNextStory,
    onBack,
    onBackToDashboard,
    handleMarkComplete,
    onMarkComplete,
    readCompleted,
    isCompleted
  } = props;

  const activeTier = tier || currentTier || 'briefing';
  const stories = otherArticles || nextArticles || [];
  const handleSelect = onSelectArticle || onSelectNextStory;
  const handleBack = onBack || onBackToDashboard;
  const handleComplete = handleMarkComplete || onMarkComplete;
  const completed = readCompleted || isCompleted;

  const tierNames = {
    briefing: 'Executive Briefing',
    analytical: 'Analytical Depth',
    full: 'Full Narrative'
  };

  const currentTierName = tierNames[activeTier] || 'Executive Briefing';
  const currentTierTime = (article && article.readingTimes && article.readingTimes[activeTier]) || 3;
  const timeSaved = Math.max(2, ((article && article.readingTimes && article.readingTimes.full) || 18) - currentTierTime);

  return (
    <section className="read-more-options-section" id="read-more-options-hub" aria-label="Recommended Articles">
      <div className="read-more-header">
        <span className="read-more-kicker">NZZ REDAKTION · RECOMMENDATIONS</span>
        <h3 className="read-more-title">
          Recommended Articles to Read
        </h3>
        <p className="read-more-subtitle">
          Completed reading in <strong>{currentTierName} ({currentTierTime} min)</strong>. Continue your session with curated Swiss journalism matched to your available time.
        </p>
      </div>

      {/* Recommended Articles Grid */}
      {stories.length > 0 && (
        <div className="read-more-block">
          <div className="read-more-block-title">
            <span>Next Stories Curated for You</span>
            <span className="read-more-block-hint">Select a story and launch directly in your chosen reading window</span>
          </div>

          <div className="next-articles-grid">
            {stories.map((other) => (
              <div key={other.id} className="next-article-card">
                <div className="next-article-info">
                  <span className="next-article-kicker">{other.kicker}</span>
                  <h4 className="next-article-title">{other.title}</h4>
                  <p className="next-article-author">{other.author} · {other.topic}</p>
                </div>

                <div className="next-article-time-buttons">
                  <span className="next-time-prompt">Read more in:</span>
                  <button
                    type="button"
                    className="btn-next-tier btn-tier-briefing"
                    onClick={() => handleSelect && handleSelect(other, 'briefing')}
                    title={`Read in ${other.readingTimes.briefing} min`}
                  >
                    <strong>{other.readingTimes.briefing}m</strong> Briefing
                  </button>
                  <button
                    type="button"
                    className="btn-next-tier btn-tier-analytical"
                    onClick={() => handleSelect && handleSelect(other, 'analytical')}
                    title={`Read in ${other.readingTimes.analytical} min`}
                  >
                    <strong>{other.readingTimes.analytical}m</strong> Analytical
                  </button>
                  <button
                    type="button"
                    className="btn-next-tier btn-tier-full"
                    onClick={() => handleSelect && handleSelect(other, 'full')}
                    title={`Read full narrative in ${other.readingTimes.full} min`}
                  >
                    <strong>{other.readingTimes.full}m</strong> Full
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Session Logging & Return to Grid */}
      <div className="read-more-footer-actions">
        <div className="completion-status-info">
          <div>
            <strong>Session Status:</strong>
            <p>
              {completed
                ? 'Recorded! Your reading state is synchronized across all your devices.'
                : `You saved ~${timeSaved}m using ${currentTierName}.`
              }
            </p>
          </div>
        </div>

        <div className="footer-button-group">
          {!completed && (
            <button
              type="button"
              className="btn-hub-primary"
              onClick={handleComplete}
            >
              Mark as Read ({timeSaved}m Saved)
            </button>
          )}

          <button
            type="button"
            className="btn-hub-secondary"
            onClick={handleBack}
          >
            Return to Dashboard Grid →
          </button>
        </div>
      </div>
    </section>
  );
}

window.ReadMoreDecisionHub = ReadMoreDecisionHub;
