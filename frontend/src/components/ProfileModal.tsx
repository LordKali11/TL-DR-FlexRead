import React from 'react';
import { UserProfile } from '../types';

interface ProfileModalProps {
  isOpen: boolean;
  user: UserProfile;
  onClose: () => void;
  onSignOut: () => void;
}

export const ProfileModal: React.FC<ProfileModalProps> = ({
  isOpen,
  user,
  onClose,
  onSignOut
}) => {
  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="nzz-modal-backdrop"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="profile-modal-title"
    >
      <div className="modal-content profile-modal-content">
        <div className="modal-header">
          <div>
            <div className="profile-editorial-badge">NZZ MITGLIEDSCHAFT · SUBSCRIBER PROFILE</div>
            <h3 className="modal-title" id="profile-modal-title">Subscriber Profile</h3>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close profile"
          >
            &times;
          </button>
        </div>

        {/* Profile Card Header */}
        <div className="profile-identity-card">
          <div className="profile-avatar-large" aria-hidden="true">
            {user.avatarInitials || 'NZ'}
          </div>
          <div className="profile-identity-text">
            <h4 className="profile-identity-name">{user.name}</h4>
            <div className="profile-identity-email">{user.email}</div>
            <div className="profile-status-chip">
              <span className="profile-status-dot"></span>
              {user.membership || 'NZZ Standard Digital Subscriber'}
            </div>
          </div>
        </div>

        {/* Cognitive Reading Metrics & Demographics Showcase */}
        <div className="profile-metrics-showcase">
          <div className="profile-metric-card">
            <div className="metric-header">
              <span className="metric-label">Subscriber Age</span>
            </div>
            <div className="metric-value">
              {user.age ?? 38} <span className="metric-unit">yrs</span>
            </div>
            <div className="metric-subtext">Demographic Baseline</div>
          </div>

          <div className="profile-metric-card">
            <div className="metric-header">
              <span className="metric-label">Daily Average</span>
            </div>
            <div className="metric-value">
              {user.dailyAverageReadingMinutes ?? 18} <span className="metric-unit">min/day</span>
            </div>
            <div className="metric-subtext">Current Reading Habit</div>
          </div>

          <div className="profile-metric-card">
            <div className="metric-header">
              <span className="metric-label">Monthly Volume</span>
            </div>
            <div className="metric-value">
              {user.monthlyAverageReadingMinutes ?? ((user.dailyAverageReadingMinutes ?? 18) * 30)} <span className="metric-unit">min</span>
            </div>
            <div className="metric-subtext">
              ~{(((user.monthlyAverageReadingMinutes ?? ((user.dailyAverageReadingMinutes ?? 18) * 30))) / 60).toFixed(1)} hrs / month
            </div>
          </div>

          <div className="profile-metric-card profile-metric-highlight">
            <div className="metric-header">
              <span className="metric-label">Modal Reading Time</span>
            </div>
            <div className="metric-value">
              {user.modalReadingTierMinutes ?? 7} <span className="metric-unit">min</span>
            </div>
            <div className="metric-subtext">
              {user.modalReadingTierName || 'Analytical Depth (7 min)'}
            </div>
          </div>
        </div>

        {/* Reading History & Personalization Ledger */}
        <div className="profile-history-section">
          <div className="history-section-header">
            <span className="history-title">Reading History & Recommendation Basis</span>
            <span className="history-badge">Calibrating 4th Button (★ Rec)</span>
          </div>

          <div className="history-list">
            {(user.readingHistory && user.readingHistory.length > 0) ? (
              user.readingHistory.slice(0, 4).map((entry, idx) => (
                <div key={idx} className="history-item-row">
                  <div className="history-item-left">
                    <span className={`history-tier-pill tier-${entry.tierChosen}`}>
                      {entry.tierChosen === 'briefing' ? 'Briefing (3m)' :
                       entry.tierChosen === 'analytical' ? 'Analytical (7m)' :
                       entry.tierChosen === 'full' ? 'Full Narrative (16m)' :
                       entry.tierChosen === 'bullets' ? 'Bullet Mode' : 'Recommended'}
                    </span>
                    <span className="history-item-title" title={entry.articleTitle}>{entry.articleTitle}</span>
                  </div>
                  <div className="history-item-meta">
                    <span className="history-item-mins">{entry.minutesRead} min read</span>
                    <span className="history-item-date">{entry.readAt}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="history-empty-state">
                No past reading sessions logged today. Select an article to begin building your personalized profile.
              </div>
            )}
          </div>
        </div>

        {/* Profile Details List */}
        <div className="profile-details-grid">
          <div className="profile-detail-item">
            <span className="profile-detail-label">Subscription Tier</span>
            <span className="profile-detail-value">{user.membership || 'Standard Digital'}</span>
          </div>
          <div className="profile-detail-item">
            <span className="profile-detail-label">Membership Status</span>
            <span className="profile-detail-value status-active">
              <span className="dot-active"></span> Active (Annual Access)
            </span>
          </div>
          <div className="profile-detail-item">
            <span className="profile-detail-label">Member Since</span>
            <span className="profile-detail-value">{user.memberSince || '2026'}</span>
          </div>
          <div className="profile-detail-item">
            <span className="profile-detail-label">Connected Device</span>
            <span className="profile-detail-value">{user.syncDevice || 'Desktop Browser'}</span>
          </div>
          <div className="profile-detail-item">
            <span className="profile-detail-label">Reading Mode</span>
            <span className="profile-detail-value">Flex Read · Adaptive Briefing</span>
          </div>
          <div className="profile-detail-item">
            <span className="profile-detail-label">Minutes Saved Today</span>
            <span className="profile-detail-value">{user.minutesSavedToday || 0} min saved</span>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="modal-actions profile-modal-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={onClose}
          >
            Back to Dashboard
          </button>
          <button
            type="button"
            className="btn-primary btn-profile-signout"
            onClick={() => {
              onClose();
              onSignOut();
            }}
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfileModal;
