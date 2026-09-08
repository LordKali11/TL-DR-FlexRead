import React from 'react';

export default function EditorialPanel(): React.ReactElement {
  return (
    <section className="editorial-panel" aria-label="NZZ Benefits and Journalism">
      <div className="panel-inner">
        <div className="edition-badge">
          <span className="badge-dot"></span>
          <span>NZZ User Account</span>
        </div>

        <h1 className="editorial-headline">
          Independent journalism from a Swiss perspective.
        </h1>

        <p className="editorial-lead">
          With your NZZ account, enjoy unlimited access to in-depth investigations, sharp analyses, and cosmopolitan debates since 1780.
        </p>

        <div className="benefits-card">
          <h2 className="benefits-title">Your Benefits at a Glance</h2>
          <ul className="benefits-list">
            <li>
              <div className="benefit-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <div className="benefit-text">
                <strong>Unlimited Reading Access</strong>
                <span>Every article, deep-dive report, and analysis on nzz.ch and inside the NZZ app.</span>
              </div>
            </li>
            <li>
              <div className="benefit-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
              <div className="benefit-text">
                <strong>Personal Reading List</strong>
                <span>Save essential articles synchronized across all your devices for offline reading.</span>
              </div>
            </li>
            <li>
              <div className="benefit-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                  <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
              </div>
              <div className="benefit-text">
                <strong>Curated Newsletters</strong>
                <span>Exclusive briefings from our correspondents delivered straight to your inbox.</span>
              </div>
            </li>
            <li>
              <div className="benefit-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                  <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                </svg>
              </div>
              <div className="benefit-text">
                <strong>NZZ am Sonntag & E-Paper</strong>
                <span>Digital 1:1 replica newspaper edition available each morning from 5:00 AM.</span>
              </div>
            </li>
          </ul>
        </div>

        <blockquote className="editorial-quote">
          <p>«Freedom of expression and the principle of individual responsibility form the cornerstone of our work.»</p>
          <cite>— Editorial Mission Statement of Neue Zürcher Zeitung</cite>
        </blockquote>
      </div>
    </section>
  );
}
