/* NzzTransitionOverlay.js
   Neue Zürcher Zeitung (NZZ) - Centered "Little Newspaper" Transition Animation
   Appears in the dead center of the screen as a miniature Swiss broadsheet edition
*/

function NzzTransitionOverlay({ isTransitioning, transitionMeta }) {
  if (!isTransitioning || !transitionMeta) return null;

  const {
    fromName = 'Executive Briefing',
    toName = 'Analytical Depth',
    fromTime = 3,
    toTime = 7,
    deltaText = 'Recalibrating reading depth'
  } = transitionMeta;

  return (
    <aside
      className="nzz-transition-overlay"
      role="status"
      aria-live="polite"
      aria-label={`Typesetting ${toName} edition`}
    >
      <div className="nzz-mini-newspaper-stage">
        <div className="nzz-mini-newspaper">
          {/* Central Crease */}
          <div className="newspaper-crease" aria-hidden="true" />

          {/* Newspaper Masthead */}
          <div className="mini-paper-header">
            <div className="mini-paper-top-meta">
              <span>ZÜRICH</span>
              <span>SEIT 1780</span>
              <span>SONDERAUSGABE</span>
            </div>
            <div className="mini-paper-masthead">
              <span className="mini-masthead-title">Neue Zürcher Zeitung</span>
              <div className="mini-masthead-subline">Intelligente Tiefen-Kalibrierung</div>
            </div>
          </div>

          {/* Main Headline & Transition Route */}
          <div className="mini-paper-content">
            <div className="mini-paper-kicker">
              <span className="mini-kicker-dot" aria-hidden="true" />
              <span>REKOMPOSITION · {toName.toUpperCase()}</span>
            </div>

            <div className="mini-paper-headline">
              <span className="mini-from-tier">{fromTime}m {fromName}</span>
              <span className="mini-arrow" aria-hidden="true">➔</span>
              <span className="mini-to-tier">{toTime}m {toName}</span>
            </div>

            <p className="mini-paper-deck">{deltaText}</p>

            {/* Miniature Print Columns with Ink Animation */}
            <div className="mini-paper-columns" aria-hidden="true">
              <div className="mini-col">
                <div className="mini-line w-100 ink-sweep-1" />
                <div className="mini-line w-85 ink-sweep-2" />
                <div className="mini-line w-95 ink-sweep-3" />
              </div>
              <div className="mini-col">
                <div className="mini-line w-90 ink-sweep-2" />
                <div className="mini-line w-100 ink-sweep-3" />
                <div className="mini-line w-75 ink-sweep-4" />
              </div>
              <div className="mini-col">
                <div className="mini-line w-100 ink-sweep-1" />
                <div className="mini-line w-95 ink-sweep-2" />
                <div className="mini-line w-80 ink-sweep-3" />
              </div>
            </div>
          </div>

          {/* 3D Page Turn Leaf */}
          <div className="mini-paper-leaf" aria-hidden="true" />

          {/* Progress / Typesetting Status */}
          <div className="mini-paper-footer">
            <span className="mini-print-status">NZZ Redaktion · Setzt neue Textstufe...</span>
            <div className="mini-progress-track" aria-hidden="true">
              <div className="mini-progress-fill" />
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}

window.NzzTransitionOverlay = NzzTransitionOverlay;
