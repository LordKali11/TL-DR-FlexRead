import React, { useState, useMemo } from 'react';
import { Article, UserProfile, ReadingTier } from '../types';
import { ArticleCard } from './ArticleCard';

interface ArticleGridProps {
  articles: Article[];
  user: UserProfile;
  onOpenReader: (article: Article, initialTier?: ReadingTier) => void;
  onLoadMore?: () => void;
  hasMore?: boolean;
  isLoadingMore?: boolean;
  totalArticles?: number;
}

export const ArticleGrid: React.FC<ArticleGridProps> = ({
  articles,
  user,
  onOpenReader,
  onLoadMore,
  hasMore = false,
  isLoadingMore = false,
  totalArticles
}) => {
  const [selectedTopic, setSelectedTopic] = useState<string>('All');

  // Dynamically derive topics from articles
  const topics = useMemo(() => {
    const set = new Set<string>();
    articles.forEach(a => {
      if (a.topic) set.add(a.topic);
    });
    return ['All', ...Array.from(set)];
  }, [articles]);

  const filteredArticles = selectedTopic === 'All'
    ? articles
    : articles.filter(a => a.topic === selectedTopic);

  return (
    <main className="dashboard-content" role="main">
      {/* Hero Welcome & Value Proposition */}
      <section className="dashboard-hero-section">
        <div className="hero-editorial-badge">
          <span>NZZ FLEX READ · INTELLIGENT DYNAMIC JOURNALISM</span>
        </div>

        <div className="hero-headline-row">
          <h1 className="hero-title">
            Independent journalism, calibrated to your cognitive density.
          </h1>
          <p className="hero-lead">
            NZZ Flex Read decomposes complex investigative narratives into semantic argument layers:
            core thesis, causal evidence, historical context, counter-arguments, and quantitative data.
            Select your reading budget on demand without compromising editorial nuance or authoritative voice.
          </p>
        </div>

        {/* Live Metrics Row (Austere Swiss typography, generous spacing) */}
        <div className="dashboard-metrics-bar">
          <div className="metric-cell">
            <span className="metric-num">
              <span className="num-accent">{totalArticles && totalArticles > 0 ? totalArticles : articles.length}</span>
            </span>
            <span className="metric-desc">Curated Articles</span>
          </div>
          <div className="metric-cell">
            <span className="metric-num">
              <span className="num-accent">{user.minutesSavedToday}</span>
              <span className="num-unit">m</span>
            </span>
            <span className="metric-desc">Time Saved Today</span>
          </div>
          <div className="metric-cell">
            <span className="metric-num">
              <span className="num-accent">100</span>
              <span className="num-unit">%</span>
            </span>
            <span className="metric-desc">Voice & Cadence Preserved</span>
          </div>
          <div className="metric-cell">
            <span className="metric-num">
              <span style={{ display: 'inline-block', width: '9px', height: '9px', backgroundColor: '#22c55e', borderRadius: '50%', marginRight: '6px', transform: 'translateY(-2px)', boxShadow: '0 0 0 3px rgba(34, 197, 94, 0.25)' }}></span>
              Live
            </span>
            <span className="metric-desc">Cross-Device Synchronized</span>
          </div>
        </div>
      </section>

      {/* Topic Filter Tabs */}
      <nav className="topic-filter-nav" aria-label="Topic filters">
        <div className="filter-pill-list">
          {topics.map(topic => (
            <button
              key={topic}
              onClick={() => setSelectedTopic(topic)}
              className={`filter-pill ${selectedTopic === topic ? 'active' : ''}`}
            >
              {topic} {topic === 'All' ? `(${articles.length})` : ''}
            </button>
          ))}
        </div>
      </nav>

      {/* Dynamic Articles Grid */}
      <section className="articles-section" aria-label="Curated articles">
        <div className="article-grid">
          {filteredArticles.map(article => (
            <ArticleCard
              key={article.id}
              article={article}
              onOpenReader={onOpenReader}
            />
          ))}
        </div>

        {hasMore && onLoadMore && (
          <div className="load-more-container" style={{ textAlign: 'center', marginTop: '3rem', marginBottom: '2.5rem' }}>
            <button
              onClick={onLoadMore}
              disabled={isLoadingMore}
              className="btn-load-more"
              style={{
                fontFamily: 'var(--font-sans, "Inter", -apple-system, sans-serif)',
                fontSize: '0.85rem',
                fontWeight: 600,
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                padding: '0.9rem 2.5rem',
                border: '1.5px solid #111',
                backgroundColor: isLoadingMore ? '#f3f4f6' : '#fff',
                color: '#111',
                cursor: isLoadingMore ? 'wait' : 'pointer',
                transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
                borderRadius: '2px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.04)'
              }}
              onMouseEnter={(e) => {
                if (!isLoadingMore) {
                  e.currentTarget.style.backgroundColor = '#111';
                  e.currentTarget.style.color = '#fff';
                }
              }}
              onMouseLeave={(e) => {
                if (!isLoadingMore) {
                  e.currentTarget.style.backgroundColor = '#fff';
                  e.currentTarget.style.color = '#111';
                }
              }}
            >
              {isLoadingMore ? 'Loading Articles…' : `Load More Curated Articles (${articles.length} of ${totalArticles || '167'})`}
            </button>
          </div>
        )}
      </section>
    </main>
  );
};
