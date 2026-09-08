import React, { useState, useEffect, useRef } from 'react';
import { Article, ReadingTier, ArgumentFocusTopic, SemanticParagraph, ProgressiveExpander } from '../types';
import { ReadMoreDecisionHub } from './ReadMoreDecisionHub';
import { FloatingDepthBubble } from './FloatingDepthBubble';
import { NzzTransitionOverlay, TransitionMeta } from './NzzTransitionOverlay';

interface FlexReaderViewProps {
  article: Article;
  articles: Article[];
  initialTier?: ReadingTier;
  onBack: () => void;
  onUpdateStats: (mins: number) => void;
  onSelectArticle: (article: Article, budgetTier?: string) => void;
}

export const FlexReaderView: React.FC<FlexReaderViewProps> = ({
  article,
  articles,
  initialTier = 'briefing',
  onBack,
  onUpdateStats,
  onSelectArticle
}) => {
  const [tier, setTier] = useState<ReadingTier>(initialTier);
  const [selectedArgumentId, setSelectedArgumentId] = useState<string>('all');
  const [showLayerFilters, setShowLayerFilters] = useState(false);
  const [activeLayers, setActiveLayers] = useState<Record<string, boolean>>({
    thesis: true,
    evidence: true,
    counterpoint: true,
    context: true,
    data: true
  });
  const [expandedIds, setExpandedIds] = useState<Record<string, boolean>>({});
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [readCompleted, setReadCompleted] = useState(false);

  // NZZ Broadsheet Transition Animation State
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionMeta, setTransitionMeta] = useState<TransitionMeta | null>(null);
  const [isReflowing, setIsReflowing] = useState(false);
  const transitionTimerRef = useRef<NodeJS.Timeout | null>(null);

  const TIERS_META = {
    briefing: { name: 'Executive Briefing', time: article.readingTimes.briefing },
    analytical: { name: 'Analytical Depth', time: article.readingTimes.analytical },
    full: { name: 'Full Narrative', time: article.readingTimes.full }
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

  const changeReadingTier = (targetTier: 'briefing' | 'analytical' | 'full') => {
    if (targetTier === tier) return;

    const fromMeta = TIERS_META[tier] || TIERS_META.briefing;
    const toMeta = TIERS_META[targetTier] || TIERS_META.analytical;
    const diff = toMeta.time - fromMeta.time;

    let deltaText = 'Recalibrating reading depth';
    if (tier === 'briefing' && targetTier === 'analytical') {
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

  const toggleLayer = (l: string) => {
    setActiveLayers(prev => ({ ...prev, [l]: !prev[l] }));
  };

  const toggleExpander = (id: string) => {
    setExpandedIds(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleMarkComplete = () => {
    const saved = article.readingTimes.full - article.readingTimes[tier];
    onUpdateStats(Math.max(2, saved));
    setReadCompleted(true);
  };

  const tierRanking = { briefing: 1, analytical: 2, full: 3 };
  const currentTierRank = tierRanking[tier];

  const visibleParagraphs = article.paragraphs.filter(p => {
    const pRank = tierRanking[p.minTier];
    if (pRank > currentTierRank) return false;
    return activeLayers[p.layer];
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
              {tier === 'briefing' ? `${article.readingTimes.briefing}m Briefing` : tier === 'analytical' ? `${article.readingTimes.analytical}m Analytical` : `${article.readingTimes.full}m Full`}
              {' '}(~{estMins > 0 ? `${estMins}m ` : ''}{estSecs}s at 220 wpm)
            </span>
          </div>

          <div className="reader-bar-right">
            <button
              onClick={() => setAudioPlaying(!audioPlaying)}
              className={`btn-audio-toggle ${audioPlaying ? 'playing' : ''}`}
              title="Listen to synthesized NZZ editorial briefing"
            >
              <span>{audioPlaying ? 'Pause Briefing' : 'Audio Briefing'}</span>
            </button>

            <div className="reader-voice-badge" title="NZZ Editorial Voice Preserved">
              <span>NZZ Voice Preserved</span>
            </div>
          </div>
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
                <span className="byline-date">{article.date || (article as any).publishedAt}</span>
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
                    <span className="depth-pill-title">Executive Briefing</span>
                  </button>

                  <button
                    role="tab"
                    aria-selected={tier === 'analytical'}
                    className={`depth-pill-btn ${tier === 'analytical' ? 'active' : ''}`}
                    onClick={() => changeReadingTier('analytical')}
                  >
                    <span className="depth-pill-time">{article.readingTimes.analytical}m</span>
                    <span className="depth-pill-title">Analytical Depth</span>
                  </button>

                  <button
                    role="tab"
                    aria-selected={tier === 'full'}
                    className={`depth-pill-btn ${tier === 'full' ? 'active' : ''}`}
                    onClick={() => changeReadingTier('full')}
                  >
                    <span className="depth-pill-time">{article.readingTimes.full}m</span>
                    <span className="depth-pill-title">Full Narrative</span>
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
          {((article.summaryBullets && article.summaryBullets.length > 0) || ((article as any).takeaways && (article as any).takeaways.length > 0)) && tier !== 'full' && (
            <div className="executive-takeaways-card">
              <div className="takeaways-header">
                <span>Key Strategic Takeaways</span>
                <span className="takeaways-tier-tag">{tier.toUpperCase()}</span>
              </div>
              <ul className="takeaways-list">
                {(article.summaryBullets || (article as any).takeaways || []).slice(0, tier === 'briefing' ? 2 : 3).map((item: string, idx: number) => (
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

          {/* Pure Editorial Prose Flow */}
          <div className="paragraphs-flow">
            {visibleParagraphs.map((p, idx) => {
              const layerClassMap: Record<string, string> = {
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
              const statValue = p.statsMetric ? p.statsMetric.value : (p as any).statValue;
              const statLabel = p.statsMetric ? p.statsMetric.label : (p as any).statLabel;

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

                  <p className="paragraph-text">{p.text}</p>
                </div>
              );
            })}
          </div>

          {/* Progressive Disclosure Expanders */}
          {(() => {
            const dossiers: ProgressiveExpander[] = ((article.progressiveExpanders || article.expanders || []) as ProgressiveExpander[]);
            if (dossiers.length === 0) return null;

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
                  {dossiers.map((exp: ProgressiveExpander) => {
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
                              {proseParagraphs.map((pText: string, pIdx: number) => (
                                <p key={pIdx} className="dossier-prose-paragraph">{pText}</p>
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
};

export default FlexReaderView;
