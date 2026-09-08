const { useMemo } = React;

    /* DashboardTopBar */
    function DashboardTopBar({ user, onSwitchToAuth, onSignOut }) {
      const formattedDate = useMemo(() => {
        try {
          return new Intl.DateTimeFormat('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
            year: 'numeric'
          }).format(new Date());
        } catch {
          return new Date().toLocaleDateString();
        }
      }, []);

      return (
        <header className="dashboard-header" role="banner">
          <div className="dashboard-header-inner">
            <div className="header-left">
              <div className="nzz-logo-wrap" title="Neue Zürcher Zeitung">
                <img
                  src="assets/nzz-logo.svg"
                  alt="Neue Zürcher Zeitung"
                  className="nzz-brand-logo"
                />
              </div>
              <div className="header-divider" aria-hidden="true"></div>
              <div className="header-edition-info">
                <span className="edition-date">{formattedDate}</span>
              </div>
            </div>

            <div className="header-right">
              <div className="stats-pill" title="Time saved through semantic argument distillation">
                <span className="stats-text">
                  <strong>{user.minutesSavedToday}m</strong>
                  <span style={{ marginLeft: '5px' }}>saved today</span>
                </span>
              </div>

              <div className="sync-pill" title={user.syncDevice}>
                <span className="sync-dot"></span>
                <span className="sync-label">{user.syncDevice || 'Device Synced'}</span>
              </div>

              <div className="user-profile-badge">
                <div className="user-avatar" aria-hidden="true">{user.avatarInitials}</div>
                <div className="user-info">
                  <span className="user-name">{user.name}</span>
                  <span className="user-tier">{user.membership}</span>
                </div>
              </div>

              <div className="header-actions">
                <button
                  onClick={onSwitchToAuth}
                  className="btn-header-secondary"
                  title="Go to Sign In / Create Profile Screen"
                >
                  Sign In / Profile
                </button>
                <button
                  onClick={onSignOut}
                  className="btn-header-signout"
                  title="Sign out of current account"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </header>
      );
    }


window.DashboardTopBar = DashboardTopBar;
