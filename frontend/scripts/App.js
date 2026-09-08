const TopBar = window.TopBar;
const EditorialPanel = window.EditorialPanel;
const AuthCard = window.AuthCard;
const ForgotPasswordModal = window.ForgotPasswordModal;
const ToastContainer = window.ToastContainer;
const DashboardTopBar = window.DashboardTopBar;
const ArticleGrid = window.ArticleGrid;
const FlexReaderView = window.FlexReaderView;
const Footer = window.Footer;
const MOCK_ARTICLES = window.MOCK_ARTICLES;
const CURRENT_USER = window.CURRENT_USER;

const { useState, useMemo, useCallback, useEffect } = React;

    /* 10. App Root */
    function detectClientDevice() {
      if (typeof navigator === 'undefined') return 'Device Synced';
      const ua = navigator.userAgent;
      if (/iPhone/i.test(ua)) return 'iPhone Synced';
      if (/iPad/i.test(ua)) return 'iPad Synced';
      if (/Android/i.test(ua)) return 'Android Device Synced';
      if (/Macintosh/i.test(ua)) return 'Mac Synced';
      return 'Desktop Synced';
    }

    const DEFAULT_GUEST_USER = {
      name: 'NZZ Subscriber',
      email: 'reader@nzz.ch',
      membership: 'NZZ Standard Digital Subscriber',
      memberSince: 'Member',
      minutesReadToday: 0,
      minutesSavedToday: 0,
      syncDevice: 'Device Synced',
      avatarInitials: 'NZ'
    };

    /* 10. App Root */
    function App() {
      // FIRST PAGE MUST BE AUTH (Sign in or Create Profile)
      const [currentView, setCurrentView] = useState('auth');

      // User state is dynamic, initialized from session if exists, otherwise null
      const [user, setUser] = useState(() => {
        try {
          const stored = sessionStorage.getItem('nzz_active_user');
          return stored ? JSON.parse(stored) : null;
        } catch {
          return null;
        }
      });

      const [articles, setArticles] = useState(MOCK_ARTICLES);
      const [activeArticle, setActiveArticle] = useState(null);
      const [readerTier, setReaderTier] = useState('briefing');

      const [activeTab, setActiveTab] = useState('login');
      const [toasts, setToasts] = useState([]);
      const [isForgotModalOpen, setIsForgotModalOpen] = useState(false);
      const [forgotInitialEmail, setForgotInitialEmail] = useState('');

      const [loginIdentifier, setLoginIdentifier] = useState('');
      const [loginPassword, setLoginPassword] = useState('');

      const [regData, setRegData] = useState({
        salutation: 'Mr.',
        firstName: '',
        lastName: '',
        email: '',
        username: '',
        password: '',
        confirmPassword: '',
        acceptTerms: false,
        newsletter: true
      });

      // Dynamic Article API loading with asynchronous REST client and local fallback
      useEffect(() => {
        if (window.NzzApiClient) {
          window.NzzApiClient.fetchArticles()
            .then(data => {
              if (Array.isArray(data) && data.length > 0) {
                setArticles(data);
              }
            })
            .catch(err => console.warn('Article API fetch failed:', err));
        }
      }, []);

      const showToast = useCallback((title, message, type = 'info') => {
        const id = Date.now().toString() + Math.random().toString(36).substring(2, 6);
        setToasts((prev) => [...prev, { id, title, message, type }]);

        setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 4500);
      }, []);

      const dismissToast = (id) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      };

      const handleOpenForgotPassword = (currentEmailOrUsername) => {
        setForgotInitialEmail(currentEmailOrUsername.includes('@') ? currentEmailOrUsername : '');
        setIsForgotModalOpen(true);
      };

      // DYNAMIC SIGN IN: extracts human name and initials dynamically from whatever user entered
      const handleLoginSuccess = (identifier) => {
        let displayName = '';
        let displayInitials = '';

        const cleanInput = identifier.trim();
        if (cleanInput.includes('@')) {
          const local = cleanInput.split('@')[0];
          const parts = local.split(/[._-]/).filter(Boolean);
          displayName = parts.map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase()).join(' ');
          displayInitials = parts.length > 1
            ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
            : local.substring(0, 2).toUpperCase();
        } else {
          const parts = cleanInput.split(/[._-]/).filter(Boolean);
          displayName = parts.map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase()).join(' ');
          displayInitials = parts.length > 1
            ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
            : cleanInput.substring(0, 2).toUpperCase();
        }

        if (!displayName) displayName = cleanInput;
        if (!displayInitials) displayInitials = displayName.substring(0, 2).toUpperCase();

        const currentDevice = detectClientDevice();
        const currentDate = new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(new Date());

        const authenticatedUser = {
          name: displayName,
          email: cleanInput.includes('@') ? cleanInput : `${cleanInput}@nzz-reader.ch`,
          membership: 'NZZ Standard Digital Subscriber',
          memberSince: `Subscriber since ${currentDate}`,
          minutesReadToday: 0,
          minutesSavedToday: 0,
          syncDevice: currentDevice,
          avatarInitials: displayInitials
        };

        setUser(authenticatedUser);
        try {
          sessionStorage.setItem('nzz_active_user', JSON.stringify(authenticatedUser));
        } catch {}

        showToast('Signed in successfully', `Welcome back, ${displayName}! Accessing your dashboard.`, 'success');
        setCurrentView('dashboard');
      };

      // DYNAMIC REGISTRATION: creates profile dynamically from user's actual entered data
      const handleRegisterSuccess = (data) => {
        const salutationPrefix = (data.salutation && data.salutation !== 'Prefer not to say') ? `${data.salutation} ` : '';
        const fullName = `${salutationPrefix}${data.firstName.trim()} ${data.lastName.trim()}`.trim();
        const fInitial = data.firstName.trim().charAt(0) || 'N';
        const lInitial = data.lastName.trim().charAt(0) || 'Z';
        const initials = (fInitial + lInitial).toUpperCase();

        const currentDevice = detectClientDevice();
        const currentDate = new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(new Date());

        const createdUser = {
          name: fullName,
          email: data.email.trim(),
          membership: 'NZZ Standard Digital Subscriber',
          memberSince: `Member since ${currentDate}`,
          minutesReadToday: 0,
          minutesSavedToday: 0,
          syncDevice: currentDevice,
          avatarInitials: initials
        };

        setUser(createdUser);
        try {
          sessionStorage.setItem('nzz_active_user', JSON.stringify(createdUser));
        } catch {}

        showToast('Profile created successfully', `Welcome to NZZ, ${data.firstName}! Your dashboard is ready.`, 'success');
        setCurrentView('dashboard');
      };

      const handleSignOut = () => {
        setUser(null);
        try {
          sessionStorage.removeItem('nzz_active_user');
        } catch {}
        showToast('Signed out', 'You have been signed out. Sign in or create a profile to continue.', 'info');
        setCurrentView('auth');
        setActiveArticle(null);
        setActiveTab('login');
      };

      const handleOpenReader = async (article, initialTier = 'briefing') => {
        // High-performance progressive fetch: load full paragraphs and deep dossiers on demand
        if (window.NzzApiClient && (!article.paragraphs || article.paragraphs.length === 0 || !article.progressiveExpanders || article.progressiveExpanders.length === 0)) {
          try {
            const fullArticle = await window.NzzApiClient.fetchArticleById(article.id);
            if (fullArticle) {
              setActiveArticle(fullArticle);
              setReaderTier(initialTier);
              window.scrollTo({ top: 0, behavior: 'smooth' });
              return;
            }
          } catch (e) {
            console.warn('[NZZ Client] Error fetching full article detail:', e);
          }
        }
        setActiveArticle(article);
        setReaderTier(initialTier);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      };

      const handleCloseReader = () => {
        setActiveArticle(null);
      };

      const handleUpdateStats = (savedMinutes) => {
        setUser((prev) => {
          const current = prev || DEFAULT_GUEST_USER;
          const updated = {
            ...current,
            minutesReadToday: current.minutesReadToday + 3,
            minutesSavedToday: current.minutesSavedToday + savedMinutes
          };
          try {
            sessionStorage.setItem('nzz_active_user', JSON.stringify(updated));
          } catch {}
          return updated;
        });

        if (window.NzzApiClient) {
          window.NzzApiClient.recordReadingTime(savedMinutes, 3).catch(() => {});
        }

        showToast(
          'Reading Progress Synced',
          `Saved ${savedMinutes} minutes with Flex Read! Cross-device sync updated.`,
          'success'
        );
      };

      const handleForgotSuccess = (submittedEmail) => {
        showToast(
          'Email sent',
          `If an account exists for ${submittedEmail}, we have sent a secure password reset link.`,
          'success'
        );
      };

      const handleFillDemo = () => {
        if (activeTab === 'login') {
          setLoginIdentifier('sophie.meier@nzz.ch');
          setLoginPassword('Zurich#2026!');
          showToast('Sample credentials loaded', 'Demo data for NZZ sign in has been populated.');
        } else {
          setRegData({
            salutation: 'Ms.',
            firstName: 'Sophie',
            lastName: 'Meier',
            email: 'sophie.meier@nzz-reader.ch',
            username: 'smeier',
            password: 'Switzerland#2026!',
            confirmPassword: 'Switzerland#2026!',
            acceptTerms: true,
            newsletter: true
          });
          showToast('Sample data loaded', 'Demo data for NZZ profile creation has been populated.');
        }
      };

      const activeUser = user || DEFAULT_GUEST_USER;

      return (
        <React.Fragment>
          {currentView === 'dashboard' ? (
            activeArticle ? (
              <FlexReaderView
                article={activeArticle}
                user={activeUser}
                initialTier={readerTier}
                articles={articles}
                onBack={handleCloseReader}
                onUpdateStats={handleUpdateStats}
                onSelectArticle={handleOpenReader}
              />
            ) : (
              <React.Fragment>
                <DashboardTopBar
                  user={activeUser}
                  onSwitchToAuth={() => setCurrentView('auth')}
                  onSignOut={handleSignOut}
                />
                <ArticleGrid
                  articles={articles}
                  user={activeUser}
                  onOpenReader={handleOpenReader}
                />
                <Footer />
              </React.Fragment>
            )
          ) : (
            <React.Fragment>
              {/* Clean BroadSheet TopBar: No Flex Read button */}
              <TopBar />

              <main className="page-wrapper">
                <div className="content-grid">
                  <EditorialPanel />
                  <AuthCard
                    activeTab={activeTab}
                    setActiveTab={setActiveTab}
                    onOpenForgotPassword={handleOpenForgotPassword}
                    onLoginSuccess={handleLoginSuccess}
                    onRegisterSuccess={handleRegisterSuccess}
                    onShowToast={showToast}
                    loginIdentifier={loginIdentifier}
                    setLoginIdentifier={setLoginIdentifier}
                    loginPassword={loginPassword}
                    setLoginPassword={setLoginPassword}
                    regData={regData}
                    setRegData={setRegData}
                    onFillDemo={handleFillDemo}
                  />
                </div>
              </main>

              <Footer />

              <ForgotPasswordModal
                isOpen={isForgotModalOpen}
                initialEmail={forgotInitialEmail}
                onClose={() => setIsForgotModalOpen(false)}
                onSubmitSuccess={handleForgotSuccess}
              />
            </React.Fragment>
          )}

          <ToastContainer toasts={toasts} onDismiss={dismissToast} />
        </React.Fragment>
      );
    }

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
