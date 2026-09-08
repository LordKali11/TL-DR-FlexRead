import React, { useState, useEffect, useRef } from 'react';
import { Article, ReadingTier } from '../types';

export interface FloatingDepthBubbleProps {
  article: Article;
  currentTier: ReadingTier;
  onSelectTier?: (targetTier: ReadingTier) => void;
  onChangeTier?: (targetTier: ReadingTier) => void;
  otherArticles?: Article[];
  nextArticles?: Article[];
  onSelectArticle?: (article: Article, tier: ReadingTier) => void;
  onSelectNextStory?: (article: Article, tier: ReadingTier) => void;
}

export const FloatingDepthBubble: React.FC<FloatingDepthBubbleProps> = ({
  article,
  currentTier,
  onSelectTier,
  onChangeTier,
  otherArticles,
  nextArticles,
  onSelectArticle,
  onSelectNextStory
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const popoverRef = useRef<HTMLElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);

  const tierChangeHandler = onSelectTier || onChangeTier;
  const nextStoryList = otherArticles && otherArticles.length > 0 ? otherArticles : (nextArticles || []);
  const nextStoryHandler = onSelectArticle || onSelectNextStory;

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        isOpen &&
        popoverRef.current &&
        !popoverRef.current.contains(event.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const TIERS_META = [
    {
      id: 'briefing' as ReadingTier,
      name: 'Executive Briefing',
      time: article.readingTimes.briefing,
      desc: 'Core thesis assertions and verified quantitative data metrics.',
      badgeText: 'Executive Brief'
    },
    {
      id: 'analytical' as ReadingTier,
      name: 'Analytical Depth',
      time: article.readingTimes.analytical,
      desc: 'Causal evidence, institutional tensions, and counter-arguments.',
      badgeText: 'Analytical Layer'
    },
    {
      id: 'full' as ReadingTier,
      name: 'Full Narrative',
      time: article.readingTimes.full,
      desc: 'Uncompromising Swiss broadsheet prose with full historical context.',
      badgeText: 'Full Broadsheet'
    }
  ];

  // User directive: "if im reading the three minute one then it shouldnt be an option as im readin it only the 7 and 18 should show etc"
  const alternativeTiers = TIERS_META.filter(t => t.id !== currentTier);
  const currentMeta = TIERS_META.find(t => t.id === currentTier) || TIERS_META[0];

  const handleTierSwitch = (targetTier: ReadingTier) => {
    if (tierChangeHandler) {
      tierChangeHandler(targetTier);
    }
    setIsOpen(false);
  };

  const handleStorySelect = (story: Article, budget: ReadingTier) => {
    if (nextStoryHandler) {
      nextStoryHandler(story, budget);
    }
    setIsOpen(false);
  };

  const getDeltaLabel = (targetMeta: typeof TIERS_META[0]) => {
    const diff = targetMeta.time - currentMeta.time;
    if (diff > 0) {
      return `+${diff} min deeper`;
    } else if (diff < 0) {
      return `${Math.abs(diff)} min faster`;
    }
    return 'Alternate depth';
  };

  return (
    <div className="floating-depth-bubble-wrapper">
      {isOpen && (
        <aside
          ref={popoverRef}
          className="depth-bubble-popover"
          role="dialog"
          aria-label="Reading Depth & Further Options"
        >
          <div className="bubble-popover-header">
            <div className="bubble-header-title-wrap">
              <span className="bubble-kicker">NZZ FLEX READ · READING CONTROLS</span>
              <h4 className="bubble-title">Further Reading Options</h4>
            </div>
            <button
              type="button"
              className="btn-bubble-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close reading options"
            >
              ✕
            </button>
          </div>

          <div className="bubble-current-tier-banner">
            <span className="current-tier-dot" aria-hidden="true">●</span>
            <div className="current-tier-text">
              <span className="current-tier-label">Currently reading:</span>
              <strong className="current-tier-name">
                {currentMeta.name} ({currentMeta.time} min)
              </strong>
            </div>
            <span className="current-tier-badge">Active</span>
          </div>

          <div className="bubble-options-section">
            <div className="bubble-section-label">
              <span>Change Reading Depth for this Story:</span>
              <span className="bubble-section-note">
                (Alternative depths available)
              </span>
            </div>

            <div className="bubble-tier-options-list">
              {alternativeTiers.map((alt) => {
                const delta = getDeltaLabel(alt);
                return (
                  <button
                    key={alt.id}
                    type="button"
                    className="bubble-alt-tier-card"
                    onClick={() => handleTierSwitch(alt.id)}
                  >
                    <div className="alt-tier-left">
                      <div className="alt-tier-time-pill">{alt.time} min</div>
                      <div className="alt-tier-info">
                        <div className="alt-tier-name-row">
                          <span className="alt-tier-name">{alt.name}</span>
                          <span className="alt-tier-delta">{delta}</span>
                        </div>
                        <p className="alt-tier-desc">{alt.desc}</p>
                      </div>
                    </div>
                    <span className="alt-tier-arrow">Switch →</span>
                  </button>
                );
              })}
            </div>
          </div>

          {nextStoryList.length > 0 && (
            <div className="bubble-next-stories-section">
              <div className="bubble-section-label">
                <span>Or Choose Next Story by Available Time:</span>
              </div>
              <div className="bubble-next-stories-list">
                {nextStoryList.slice(0, 2).map((other) => (
                  <div key={other.id} className="bubble-next-story-item">
                    <div className="bubble-next-story-title">{other.title}</div>
                    <div className="bubble-next-story-actions">
                      <button
                        type="button"
                        className="btn-bubble-quick-tier"
                        onClick={() => handleStorySelect(other, 'briefing')}
                      >
                        <strong>{other.readingTimes.briefing}m</strong> Briefing
                      </button>
                      <button
                        type="button"
                        className="btn-bubble-quick-tier"
                        onClick={() => handleStorySelect(other, 'analytical')}
                      >
                        <strong>{other.readingTimes.analytical}m</strong> Analytical
                      </button>
                      <button
                        type="button"
                        className="btn-bubble-quick-tier"
                        onClick={() => handleStorySelect(other, 'full')}
                      >
                        <strong>{other.readingTimes.full}m</strong> Full
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>
      )}

      <button
        ref={triggerRef}
        type="button"
        className={`floating-depth-bubble-button ${isOpen ? 'is-active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        title="Further Reading & Depth Options (3 min, 7 min, 18 min)"
      >
        <span className="bubble-btn-icon" aria-hidden="true">⏱</span>
        <span className="bubble-btn-time">{currentMeta.time} min</span>
        <span className="bubble-btn-divider">|</span>
        <span className="bubble-btn-label">
          {isOpen ? 'Close Options' : 'Further Reading'}
        </span>
        <span className="bubble-btn-arrow" aria-hidden="true">
          {isOpen ? '▾' : '▴'}
        </span>
      </button>
    </div>
  );
};
