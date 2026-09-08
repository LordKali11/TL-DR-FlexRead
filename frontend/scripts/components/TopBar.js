const { useMemo } = React;

    /* 1. TopBar */
    function TopBar(props) {
      const formattedDate = useMemo(() => {
        const now = new Date();
        try {
          return new Intl.DateTimeFormat('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
            year: 'numeric'
          }).format(now);
        } catch {
          return now.toLocaleDateString();
        }
      }, []);

      return (
        <header className="nzz-topbar">
          <div className="topbar-container">
            <div className="topbar-meta">
              <span className="meta-date">{formattedDate}</span>
              <span className="meta-divider">|</span>
              <span className="meta-location">Zurich</span>
            </div>
            <div className="topbar-actions">
              
              <a
                href="https://www.nzz.ch/"
                target="_blank"
                rel="noopener noreferrer"
                className="back-link"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <line x1="19" y1="12" x2="5" y2="12"></line>
                  <polyline points="12 19 5 12 12 5"></polyline>
                </svg>
                Back to nzz.ch
              </a>
            </div>
          </div>
        </header>
      );
    }


window.TopBar = TopBar;
