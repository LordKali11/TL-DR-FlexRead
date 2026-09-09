(function() {
  const ProfileModal = ({ isOpen, user, onClose, onSignOut, returnLabel, returnContext }) => {
    if (!isOpen) return null;

    React.useEffect(() => {
      const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
          onClose();
        }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onClose]);

    const handleBackdropClick = (e) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    };

    const backButtonText = returnLabel || (returnContext === 'reader' ? '← Back to Article' : '← Back to Articles');

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
                {user.age !== undefined ? user.age : 38} <span className="metric-unit">yrs</span>
              </div>
              <div className="metric-subtext">Demographic Baseline</div>
            </div>

            <div className="profile-metric-card">
              <div className="metric-header">
                <span className="metric-label">Daily Average</span>
              </div>
              <div className="metric-value">
                {user.dailyAverageReadingMinutes !== undefined ? user.dailyAverageReadingMinutes : 18} <span className="metric-unit">min/day</span>
              </div>
              <div className="metric-subtext">Current Reading Habit</div>
            </div>

            <div className="profile-metric-card">
              <div className="metric-header">
                <span className="metric-label">Monthly Volume</span>
              </div>
              <div className="metric-value">
                {user.monthlyAverageReadingMinutes !== undefined ? user.monthlyAverageReadingMinutes : ((user.dailyAverageReadingMinutes || 18) * 30)} <span className="metric-unit">min</span>
              </div>
              <div className="metric-subtext">
                ~{(((user.monthlyAverageReadingMinutes !== undefined ? user.monthlyAverageReadingMinutes : ((user.dailyAverageReadingMinutes || 18) * 30))) / 60).toFixed(1)} hrs / month
              </div>
            </div>

            <div className="profile-metric-card profile-metric-highlight">
              <div className="metric-header">
                <span className="metric-label">Modal Reading Time</span>
              </div>
              <div className="metric-value">
                {user.modalReadingTierMinutes !== undefined ? user.modalReadingTierMinutes : 7} <span className="metric-unit">min</span>
              </div>
              <div className="metric-subtext">
                {user.modalReadingTierName || 'Analytical Depth (7 min)'}
              </div>
            </div>
          </div>

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

          <div className="modal-actions profile-modal-actions">
            <button
              type="button"
              className="btn-secondary btn-modal-escape"
              onClick={onClose}
            >
              {backButtonText}
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

  window.ProfileModal = ProfileModal;
})();
