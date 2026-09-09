const { useState, useEffect, useRef } = React;
const ReadMoreDecisionHub = window.ReadMoreDecisionHub;
const FloatingDepthBubble = window.FloatingDepthBubble;
const NzzTransitionOverlay = window.NzzTransitionOverlay;

function FlexReaderView({ article, articles, user, initialTier = 'briefing', onBack, onUpdateStats, onSelectArticle }) {
  const rec = (window.getRecommendedReadingTier && window.getRecommendedReadingTier(article, user)) || {
    tier: 'analytical',
    minutes: (article.readingTimes && article.readingTimes.analytical) || 7,
    label: `${(article.readingTimes && article.readingTimes.analytical) || 7}m Rec`,
    reason: 'Recommended for standard analytical focus'
  };
  const effectiveInitialTier = initialTier === 'recommended' ? rec.tier : initialTier;
  const [tier, setTier] = useState(effectiveInitialTier);
  const [selectedArgumentId, setSelectedArgumentId] = useState('all');
  const [showLayerFilters, setShowLayerFilters] = useState(false);
  const [activeLayers, setActiveLayers] = useState({
    thesis: true,
    evidence: true,
    counterpoint: true,
    context: true,
    data: true
  });
  const [expandedIds, setExpandedIds] = useState({});
  const [readCompleted, setReadCompleted] = useState(false);

  // NZZ Broadsheet Transition Animation State
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionMeta, setTransitionMeta] = useState(null);
  const [isReflowing, setIsReflowing] = useState(false);
  const transitionTimerRef = useRef(null);

  const TIERS_META = {
    briefing: { name: 'Executive Briefing', time: article.readingTimes.briefing },
    analytical: { name: 'Analytical Depth', time: article.readingTimes.analytical },
    full: { name: 'Full Narrative', time: article.readingTimes.full },
    recommended: { name: `Recommended (${rec.minutes}m)`, time: rec.minutes },
    bullets: { name: 'Bullet Mode (Summary)', time: 2 }
  };

  useEffect(() => {
    if (initialTier) {
      setTier(initialTier);
    }
    setSelectedArgumentId('all');
    setReadCompleted(false);
    setExpandedIds({});
    setIsTransitioning(false);
    setTransitionMeta(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [article.id, initialTier]);

  const changeReadingTier = (targetTier) => {
    if (targetTier === tier) return;

    const fromMeta = TIERS_META[tier] || TIERS_META.briefing;
    const toMeta = TIERS_META[targetTier] || TIERS_META.analytical;
    const diff = toMeta.time - fromMeta.time;

    let deltaText = 'Recalibrating reading depth';
    if (targetTier === 'bullets') {
      deltaText = 'Distilling core arguments & executive bullet points';
    } else if (tier === 'bullets') {
      deltaText = `Expanding from Bullet Mode into ${toMeta.name}`;
    } else if (tier === 'briefing' && targetTier === 'analytical') {
      deltaText = '+4 min deeper · Expanding institutional context & counter-arguments';
    } else if (tier === 'analytical' && targetTier === 'full') {
      deltaText = '+11 min deeper · Unlocking full broadsheet prose & historical documentation';
    } else if (tier === 'briefing' && targetTier === 'full') {
      deltaText = '+15 min deeper · Unlocking complete unabridged broadsheet reporting';
    } else if (diff < 0) {
      deltaText = `${Math.abs(diff)} min faster · Distilling executive briefing & core data`;
    } else {
      deltaText = `+${diff} min deeper · Recalibrating editorial density`;
    }

    setTransitionMeta({
      fromTier: tier,
      toTier: targetTier,
      fromName: fromMeta.name,
      toName: toMeta.name,
      fromTime: fromMeta.time,
      toTime: toMeta.time,
      deltaText
    });

    setIsTransitioning(true);
    setIsReflowing(true);
    setTier(targetTier);

    setActiveLayers({
      thesis: true,
      evidence: true,
      counterpoint: true,
      context: true,
      data: true
    });

    if (transitionTimerRef.current) {
      clearTimeout(transitionTimerRef.current);
    }

    transitionTimerRef.current = setTimeout(() => {
      setIsTransitioning(false);
      setTimeout(() => {
        setIsReflowing(false);
        setTransitionMeta(null);
      }, 250);
    }, 950);
  };

  const otherArticles = (articles || []).filter(a => a.id !== article.id);

  const toggleLayer = (l) => {
    setActiveLayers(prev => ({ ...prev, [l]: !prev[l] }));
  };

  const toggleExpander = (id) => {
    setExpandedIds(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleMarkComplete = () => {
    const tierTime = tier === 'bullets' ? 2 : (article.readingTimes[tier] || 3);
    const saved = article.readingTimes.full - tierTime;
    onUpdateStats(Math.max(2, saved));
    setReadCompleted(true);
  };

  const tierRanking = { briefing: 1, analytical: 2, full: 3, bullets: 3, recommended: 2 };
  const currentTierRank = tierRanking[tier] || 1;

  const visibleParagraphs = (article.paragraphs || []).filter(p => {
    const tierLevel = p.minTier || p.tier || 'briefing';
    const pRank = tierRanking[tierLevel] || 1;
    if (pRank > currentTierRank) return false;
    if (p.layer && activeLayers && activeLayers[p.layer] === false) return false;
    return true;
  });

  const argumentTopics = article.argumentFocusTopics || [];
  const activeArgumentTopic = argumentTopics.find(t => t.id === selectedArgumentId);

  const wordsCount = visibleParagraphs.reduce((acc, p) => acc + p.text.split(' ').length, 0);
  const estimatedSeconds = Math.round((wordsCount / 220) * 60);
  const estMins = Math.floor(estimatedSeconds / 60);
  const estSecs = estimatedSeconds % 60;

  return (
    <div className="flex-reader-page">
      {/* NZZ Miniature Broadsheet Newspaper Centered Transition Animation */}
      <NzzTransitionOverlay
        isTransitioning={isTransitioning}
        transitionMeta={transitionMeta}
      />

      {/* Reader Sticky Top Bar */}
      <header className="reader-sticky-bar">
        <div className="reader-bar-inner">
          <button onClick={onBack} className="btn-back-grid" title="Back to Articles">
            <span aria-hidden="true">←</span> All Articles
          </button>

          <div className="reader-center-meta">
            <span className="reader-article-kicker">{article.kicker}</span>
            <span className="reader-dot">·</span>
            <span className="reader-time-readout">
              {tier === 'briefing' ? `${article.readingTimes.briefing}m Briefing` :
               tier === 'analytical' ? `${article.readingTimes.analytical}m Analytical` :
               tier === 'bullets' ? '2m Bullet Mode' : `${article.readingTimes.full}m Full`}
              {' '}(~{estMins > 0 ? `${estMins}m ` : ''}{estSecs}s at 220 wpm)
            </span>
          </div>

          <div className="reader-bar-right" aria-hidden="true"></div>
        </div>
      </header>

      {/* Main Reading Canvas */}
      <main className="reader-layout-container">
        <article className={`reader-article-content ${isReflowing ? 'tier-transition-reflow' : ''}`}>
          
          {/* Authentic Broadsheet Header: Headline, Kicker, Subtitle, Byline */}
          <header className="article-headline-block">
            <div className="article-kicker-tag">{article.kicker}</div>
            <h1 className="article-title">{article.title}</h1>
            <p className="article-subtitle">{article.subtitle}</p>

            <div className="article-byline-bar">
              <div className="byline-meta">
                <span className="byline-author">{article.author}</span>
                <span className="byline-sep">/</span>
                <span className="byline-date">{article.date || article.publishedAt}</span>
                <span className="byline-sep">/</span>
                <span className="byline-location">Zurich</span>
              </div>
              <div className="byline-sync-info">
                <span>Swiss Broadsheet Edition</span>
              </div>
            </div>

            {/* Sleek Broadsheet Reading Depth Toolbar */}
            <div className="nzz-reading-depth-bar">
              <div className="depth-bar-left">
                <span className="depth-bar-label">READING DEPTH:</span>
                <div className="depth-bar-pills" role="tablist">
                  <button
                    role="tab"
                    aria-selected={tier === 'briefing'}
                    className={`depth-pill-btn ${tier === 'briefing' ? 'active' : ''}`}
                    onClick={() => changeReadingTier('briefing')}
                  >
                    <span className="depth-pill-time">{article.readingTimes.briefing}m</span>
                    <span className="depth-pill-title">Briefing</span>
                  </button>

                  <button
                    role="tab"
                    aria-selected={tier === 'analytical'}
                    className={`depth-pill-btn ${tier === 'analytical' ? 'active' : ''}`}
                    onClick={() => changeReadingTier('analytical')}
                  >
                    <span className="depth-pill-time">{article.readingTimes.analytical}m</span>
                    <span className="depth-pill-title">Analytical</span>
                  </button>

                  <button
                    role="tab"
                    aria-selected={tier === 'full'}
                    className={`depth-pill-btn ${tier === 'full' ? 'active' : ''}`}
                    onClick={() => changeReadingTier('full')}
                  >
                    <span className="depth-pill-time">{article.readingTimes.full}m</span>
                    <span className="depth-pill-title">Full</span>
                  </button>

                  <button
                    role="tab"
                    aria-selected={tier === rec.tier}
                    className={`depth-pill-btn depth-pill-rec ${tier === rec.tier ? 'active' : ''}`}
                    onClick={() => changeReadingTier(rec.tier)}
                    title={`${rec.reason} (${rec.minutes}m)`}
                  >
                    <span className="depth-pill-time">★ {rec.minutes}m</span>
                    <span className="depth-pill-title">Rec</span>
                  </button>

                  <button
                    role="tab"
                    aria-selected={tier === 'bullets'}
                    className={`depth-pill-btn depth-pill-bullets ${tier === 'bullets' ? 'active' : ''}`}
                    onClick={() => changeReadingTier('bullets')}
                    title="View key points and main arguments in Bullet Mode"
                  >
                    <span className="depth-pill-time">●</span>
                    <span className="depth-pill-title">Bullet Mode</span>
                  </button>
                </div>
              </div>

              <div className="depth-bar-right">
                <button
                  type="button"
                  className={`btn-filter-layers-toggle ${showLayerFilters || selectedArgumentId !== 'all' ? 'active' : ''}`}
                  onClick={() => setShowLayerFilters(!showLayerFilters)}
                  title="Toggle article-specific argument focus"
                >
                  <span>Argument Focus</span>
                  {selectedArgumentId !== 'all' && (
                    <span className="argument-pill-tag" style={{ marginLeft: '4px' }}>Active</span>
                  )}
                  <span className="filter-layers-chevron">{showLayerFilters ? '▲' : '▼'}</span>
                </button>
              </div>
            </div>

            {/* Dynamic Article-Specific Argument Focus Drawer */}
            {showLayerFilters && (
              <div className="layer-pills-drawer">
                <div className="drawer-header-row">
                  <span className="drawer-label">Article Arguments ({argumentTopics.length} Core Dimensions)</span>
                  <span className="drawer-caption">Select an argument to highlight its evidence across reading depth</span>
                </div>
                <div className="argument-pills-list">
                  <button
                    type="button"
                    className={`argument-focus-pill ${selectedArgumentId === 'all' ? 'active' : ''}`}
                    onClick={() => setSelectedArgumentId('all')}
                  >
                    <span>All Arguments</span>
                    <span className="argument-pill-count">({visibleParagraphs.length})</span>
                  </button>

                  {argumentTopics.map(topic => {
                    const matchCount = visibleParagraphs.filter(p =>
                      (p.argumentId && p.argumentId === topic.id) ||
                      (topic.paragraphIds && topic.paragraphIds.includes(p.id))
                    ).length;

                    return (
                      <button
                        key={topic.id}
                        type="button"
                        className={`argument-focus-pill ${selectedArgumentId === topic.id ? 'active' : ''}`}
                        onClick={() => setSelectedArgumentId(selectedArgumentId === topic.id ? 'all' : topic.id)}
                        title={topic.summary}
                      >
                        <span className="argument-pill-tag">{topic.tag}</span>
                        <span>{topic.label}</span>
                        <span className="argument-pill-count">({matchCount})</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </header>

          {/* Key Strategic Takeaways (shown in Briefing & Analytical) */}
          {((article.summaryBullets && article.summaryBullets.length > 0) || (article.takeaways && article.takeaways.length > 0)) && tier !== 'full' && tier !== 'bullets' && (
            <div className="executive-takeaways-card">
              <div className="takeaways-header">
                <span>Key Strategic Takeaways</span>
                <span className="takeaways-tier-tag">{tier.toUpperCase()}</span>
              </div>
              <ul className="takeaways-list">
                {(article.summaryBullets || article.takeaways || []).slice(0, tier === 'briefing' ? 2 : 3).map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Contextual Active Argument Banner */}
          {activeArgumentTopic && (
            <div className="active-argument-banner">
              <div className="argument-banner-top">
                <span className="argument-banner-kicker">ARGUMENT FOCUS: {activeArgumentTopic.tag}</span>
                <button
                  type="button"
                  className="argument-banner-reset"
                  onClick={() => setSelectedArgumentId('all')}
                  title="Show all arguments"
                >
                  Show Full Narrative ✕
                </button>
              </div>
              <h3 className="argument-banner-title">{activeArgumentTopic.label}</h3>
              <p className="argument-banner-summary">{activeArgumentTopic.summary}</p>
            </div>
          )}

          {/* Main Article Content: Bullet Mode OR Paragraph Flow */}
          {tier === 'bullets' ? (
            <div className="bullet-mode-container">
              <div className="bullet-mode-intro-banner">
                <div className="bullet-mode-kicker">NZZ FLEX READ · BULLET MODE</div>
                <h2 className="bullet-mode-headline">Core Points & Strategic Takeaways</h2>
                <p className="bullet-mode-description">
                  Essential bullet breakdown of the core thesis, causal evidence, institutional positions, and geopolitical takeaways.
                </p>
              </div>

              {/* Section 1: Core Editorial Takeaways */}
              <div className="bullet-mode-section">
                <h3 className="bullet-section-title">Key Executive Points</h3>
                <ul className="bullet-mode-list">
                  {(article.takeaways || article.summaryBullets || []).map((point, idx) => (
                    <li key={idx} className="bullet-mode-item">
                      <span className="bullet-mode-marker" aria-hidden="true">■</span>
                      <div className="bullet-mode-text">
                        {(window.EditorialMarkdown || (typeof EditorialMarkdown !== 'undefined' ? EditorialMarkdown : null)) ? (
                          React.createElement(window.EditorialMarkdown || EditorialMarkdown, { text: point })
                        ) : (
                          <span>{point}</span>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Section 2: Core Argument Pillars */}
              {article.argumentFocusTopics && article.argumentFocusTopics.length > 0 && (
                <div className="bullet-mode-section">
                  <h3 className="bullet-section-title">Argument Structure & Core Pillars</h3>
                  <div className="bullet-pillars-grid">
                    {article.argumentFocusTopics.map((topic) => (
                      <div key={topic.id} className="bullet-pillar-card">
                        <div className="bullet-pillar-header">
                          <span className="pillar-tag">{topic.tag}</span>
                          <span className="pillar-title">{topic.label}</span>
                        </div>
                        <p className="pillar-summary">{topic.summary}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Section 3: Empirical Evidence & Key Quotes in Bullet Form */}
              {visibleParagraphs.some(p => p.statsMetric || p.quote) && (
                <div className="bullet-mode-section">
                  <h3 className="bullet-section-title">Empirical Evidence & Key Quotes</h3>
                  <ul className="bullet-mode-list">
                    {visibleParagraphs
                      .filter(p => p.statsMetric || p.quote)
                      .map((p, idx) => (
                        <li key={p.id || idx} className="bullet-mode-item bullet-item-evidence">
                          <span className="bullet-mode-marker" aria-hidden="true">◆</span>
                          <div className="bullet-mode-text">
                            {p.statsMetric && (
                              <strong className="bullet-metric-highlight">[{p.statsMetric.value}] {p.statsMetric.label}: </strong>
                            )}
                            {p.quote && (
                              <em className="bullet-quote-highlight">"{ p.quote }" &mdash; </em>
                            )}
                            {(window.EditorialMarkdown || (typeof EditorialMarkdown !== 'undefined' ? EditorialMarkdown : null)) ? (
                              React.createElement(window.EditorialMarkdown || EditorialMarkdown, {
                                text: p.keyTakeaway || p.text.split('.')[0] + '.'
                              })
                            ) : (
                              <span>{p.keyTakeaway || p.text.split('.')[0] + '.'}</span>
                            )}
                          </div>
                        </li>
                      ))}
                  </ul>
                </div>
              )}

              {/* Bottom Quick-Switch */}
              <div className="bullet-mode-footer-switch">
                <span className="footer-switch-label">Ready to explore full investigative prose?</span>
                <div className="footer-switch-buttons">
                  <button
                    type="button"
                    className="btn-switch-tier"
                    onClick={() => changeReadingTier('analytical')}
                  >
                    Switch to Analytical Depth ({article.readingTimes.analytical}m)
                  </button>
                  <button
                    type="button"
                    className="btn-switch-tier"
                    onClick={() => changeReadingTier('full')}
                  >
                    Read Full Broadsheet ({article.readingTimes.full}m)
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="paragraphs-flow">
              {visibleParagraphs.map((p, idx) => {
                const layerClassMap = {
                  thesis: 'layer-type-thesis',
                  evidence: 'layer-type-evidence',
                  counterpoint: 'layer-type-counterpoint',
                  data: 'layer-type-data',
                  context: 'layer-type-context'
                };

                const isMatch = selectedArgumentId === 'all' ||
                  (p.argumentId && p.argumentId === selectedArgumentId) ||
                  (activeArgumentTopic && activeArgumentTopic.paragraphIds && activeArgumentTopic.paragraphIds.includes(p.id));

                const isDimmed = selectedArgumentId !== 'all' && !isMatch;
                const statValue = p.statsMetric ? p.statsMetric.value : p.statValue;
                const statLabel = p.statsMetric ? p.statsMetric.label : p.statLabel;

                return (
                  <div
                    key={p.id || idx}
                    className={`semantic-paragraph-block ${layerClassMap[p.layer]} ${statValue ? 'stat-callout-block' : ''} ${isMatch && selectedArgumentId !== 'all' ? 'paragraph-argument-focused' : ''} ${isDimmed ? 'paragraph-argument-dimmed' : ''}`}
                  >
                    {isMatch && selectedArgumentId !== 'all' && activeArgumentTopic && (
                      <div className="argument-match-chip">
                        <span>Argument: {activeArgumentTopic.tag}</span>
                      </div>
                    )}

                    {statValue && (
                      <div className="stat-callout-card">
                        <span className="stat-value">{statValue}</span>
                        <span className="stat-desc">{statLabel}</span>
                      </div>
                    )}

                    {p.quote && (
                      <figure className="editorial-pull-quote-figure">
                        <blockquote className="editorial-pull-quote">
                          <span className="quote-mark-icon" aria-hidden="true">“</span>
                          <p className="quote-body-text">{p.quote}</p>
                        </blockquote>
                        <figcaption className="quote-attribution">
                          <span className="quote-tag">REDAKTIONELLER SCHLÜSSELSATZ</span>
                          <span className="quote-author-name">{article.author || 'NZZ Redaktion'}</span>
                        </figcaption>
                      </figure>
                    )}

                    {(window.EditorialMarkdown || (typeof EditorialMarkdown !== 'undefined' ? EditorialMarkdown : null)) ? (
                      React.createElement(window.EditorialMarkdown || EditorialMarkdown, {
                        text: p.text,
                        className: 'paragraph-text'
                      })
                    ) : (
                      <p className="paragraph-text">{p.text}</p>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Progressive Disclosure Expanders */}
          {(() => {
            const dossiers = (article.progressiveExpanders || article.expanders || []);
            if (!dossiers || dossiers.length === 0) return null;

            return (
              <section className="progressive-expanders-section" aria-label="Investigative Dossiers and Primary Sources">
                <div className="expanders-section-header">
                  <div className="expanders-header-titles">
                    <span className="expanders-kicker">INVESTIGATIVE DOSSIERS · PROGRESSIVE DRILL-DOWNS</span>
                    <h3 className="expanders-section-title">Primary Source Archives & Background Dossiers</h3>
                    <p className="expanders-section-subtext">
                      Deep analytical drill-downs, statutory frameworks, and primary source records curated by the NZZ editorial board.
                    </p>
                  </div>
                  <div className="expanders-count-badge">
                    <span className="count-number">{dossiers.length}</span>
                    <span className="count-label">DOSSIERS</span>
                  </div>
                </div>

                <div className="expanders-list">
                  {dossiers.map(exp => {
                    const isExpanded = !!expandedIds[exp.id];
                    const badgeText = exp.badge || exp.category || 'IN-DEPTH DOSSIER';
                    const readTimeText = exp.readTime || '~2 min deep dive';
                    const proseParagraphs = (exp.fullContent || '').split('\n\n').filter(Boolean);

                    return (
                      <article
                        key={exp.id}
                        id={`dossier-${exp.id}`}
                        className={`expander-card ${isExpanded ? 'open' : ''}`}
                      >
                        <button
                          type="button"
                          className="expander-card-trigger"
                          onClick={() => toggleExpander(exp.id)}
                          aria-expanded={isExpanded}
                          aria-controls={`dossier-body-${exp.id}`}
                        >
                          <div className="expander-header-main">
                            <div className="expander-meta-bar">
                              <span className="expander-tag-pill">{badgeText}</span>
                              <span className="expander-readtime-pill">{readTimeText}</span>
                            </div>
                            <h4 className="expander-card-title">{exp.title}</h4>
                            {exp.previewSnippet && (
                              <p className="expander-teaser-snippet">{exp.previewSnippet}</p>
                            )}
                          </div>
                          <div className="expander-action-btn" aria-hidden="true">
                            <span className="expander-action-icon">{isExpanded ? '−' : '+'}</span>
                            <span className="expander-action-label">{isExpanded ? 'Collapse' : 'Explore'}</span>
                          </div>
                        </button>

                        {isExpanded && (
                          <div id={`dossier-body-${exp.id}`} className="expander-body-pane">
                            {/* Editorial Key Takeaway */}
                            {exp.keyTakeaway && (
                              <div className="dossier-takeaway-box">
                                <div className="takeaway-label">
                                  <span className="takeaway-dot"></span>
                                  EDITORIAL SYNTHESIS
                                </div>
                                <p className="takeaway-text">{exp.keyTakeaway}</p>
                              </div>
                            )}

                            {/* Data Metric Callout */}
                            {exp.dataCallout && (
                              <div className="dossier-metric-callout">
                                <span className="dossier-metric-val">{exp.dataCallout.value}</span>
                                <span className="dossier-metric-lbl">{exp.dataCallout.label}</span>
                              </div>
                            )}

                            {/* Full Investigative Narrative */}
                            <div className="dossier-prose-stream">
                              {proseParagraphs.map((pText, pIdx) => (
                                (window.EditorialMarkdown || (typeof EditorialMarkdown !== 'undefined' ? EditorialMarkdown : null)) ? (
                                  React.createElement(window.EditorialMarkdown || EditorialMarkdown, {
                                    key: pIdx,
                                    text: pText,
                                    className: 'dossier-prose-paragraph'
                                  })
                                ) : (
                                  <p key={pIdx} className="dossier-prose-paragraph">{pText}</p>
                                )
                              ))}
                            </div>

                            {/* Archival Reference */}
                            {exp.source && (
                              <div className="dossier-source-footnote">
                                <span className="source-label">Primary Archival Reference:</span>
                                <cite className="source-citation">{exp.source}</cite>
                              </div>
                            )}

                            <div className="dossier-card-footer">
                              <button
                                type="button"
                                className="dossier-close-button"
                                onClick={() => toggleExpander(exp.id)}
                              >
                                <span>Collapse Dossier</span>
                                <span className="close-symbol">▲</span>
                              </button>
                            </div>
                          </div>
                        )}
                      </article>
                    );
                  })}
                </div>
              </section>
            );
          })()}

          {/* Bottom Hub: Recommended Articles Only */}
          <ReadMoreDecisionHub
            currentTier={tier}
            article={article}
            nextArticles={otherArticles}
            onSelectNextStory={(nextArticle, budget) => onSelectArticle(nextArticle, budget)}
            onMarkComplete={handleMarkComplete}
            isCompleted={readCompleted}
            onBackToDashboard={onBack}
          />
        </article>
      </main>

      {/* Floating Reading Depth Bubble */}
      <FloatingDepthBubble
        currentTier={tier}
        article={article}
        nextArticles={otherArticles}
        otherArticles={otherArticles}
        onChangeTier={changeReadingTier}
        onSelectTier={changeReadingTier}
        onSelectNextStory={(nextArticle, budget) => onSelectArticle(nextArticle, budget)}
        onSelectArticle={(nextArticle, budget) => onSelectArticle(nextArticle, budget)}
      />
    </div>
  );
}

window.FlexReaderView = FlexReaderView;
