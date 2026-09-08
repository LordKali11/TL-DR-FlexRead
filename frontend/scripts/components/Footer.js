    /* 9. Footer */
    function Footer() {
      return (
        <footer className="nzz-footer">
          <div className="footer-container">
            <div className="footer-meta">
              <span className="copyright">© 2026 Neue Zürcher Zeitung AG. All rights reserved.</span>
            </div>
            <nav className="footer-nav" aria-label="Legal notices and help">
              <a href="https://www.nzz.ch/hilfe" target="_blank" rel="noopener noreferrer">Help & FAQ</a>
              <a href="https://www.nzz.ch/agb" target="_blank" rel="noopener noreferrer">Terms & Conditions</a>
              <a href="https://www.nzz.ch/datenschutz" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
              <a href="https://www.nzz.ch/impressum" target="_blank" rel="noopener noreferrer">Imprint</a>
              <a href="https://www.nzz.ch/kontakt" target="_blank" rel="noopener noreferrer">Contact</a>
            </nav>
          </div>
        </footer>
      );
    }


window.Footer = Footer;
