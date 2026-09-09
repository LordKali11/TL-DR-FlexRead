const { useMemo } = React;

    /* DashboardTopBar */
    function DashboardTopBar({ user, onOpenProfile, onSignOut }) {
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
              <div
                className="user-profile-badge"
                onClick={onOpenProfile}
                role="button"
                tabIndex={0}
                title="Click to view your subscriber profile"
                style={{ cursor: 'pointer' }}
              >
                <div className="user-avatar" aria-hidden="true">{user.avatarInitials}</div>
                <div className="user-info">
                  <span className="user-name">{user.name}</span>
                  <span className="user-tier">{user.membership}</span>
                </div>
              </div>

              <div className="header-actions">
                <button
                  onClick={onOpenProfile}
                  className="btn-header-secondary"
                  title="View and manage your subscriber profile"
                >
                  Profile
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
