import { useState, useEffect, useCallback, type ReactElement } from 'react';
import TopBar from './components/TopBar';
import EditorialPanel from './components/EditorialPanel';
import AuthCard from './components/AuthCard';
import ForgotPasswordModal from './components/ForgotPasswordModal';
import ToastContainer from './components/Toast';
import Footer from './components/Footer';
import { DashboardTopBar } from './components/DashboardTopBar';
import { ArticleGrid } from './components/ArticleGrid';
import { FlexReaderView } from './components/FlexReaderView';
import { ProfileModal } from './components/ProfileModal';
import {
  AuthTab,
  RegistrationData,
  ToastItem,
  ToastType,
  Article,
  UserProfile,
  ReadingTier
} from './types';
import {
  fetchArticles,
  fetchArticleById,
  recordReadingTime,
  MOCK_ARTICLES,
  generateRandomizedProfileStats,
  getRecommendedReadingTier
} from './services/articleApi';

// Helper to determine active client device dynamically
function detectClientDevice(): string {
  if (typeof navigator === 'undefined') return 'Device Synced';
  const ua = navigator.userAgent;
  if (/iPhone/i.test(ua)) return 'iPhone Synced';
  if (/iPad/i.test(ua)) return 'iPad Synced';
  if (/Android/i.test(ua)) return 'Android Device Synced';
  if (/Macintosh/i.test(ua)) return 'Mac Synced';
  return 'Desktop Synced';
}

// Fallback guest user for type safety with randomized metrics
const DEFAULT_GUEST_USER: UserProfile = {
  name: 'NZZ Subscriber',
  email: 'reader@nzz.ch',
  membership: 'NZZ Standard Digital Subscriber',
  memberSince: 'Member',
  minutesReadToday: 0,
  minutesSavedToday: 0,
  syncDevice: 'Device Synced',
  avatarInitials: 'NZ',
  age: 38,
  dailyAverageReadingMinutes: 18,
  monthlyAverageReadingMinutes: 540,
  modalReadingTierMinutes: 7,
  modalReadingTierName: 'Analytical Depth (7 min)',
  readingHistory: [
    {
      articleId: 'trump-tariff-deal-eu',
      articleTitle: "Three takes on Trump's tariff deal with the EU",
      tierChosen: 'analytical',
      minutesRead: 7,
      readAt: 'Yesterday'
    },
    {
      articleId: 'swiss-us-investment-paradox',
      articleTitle: 'Swiss companies are world leaders in US investment',
      tierChosen: 'briefing',
      minutesRead: 2,
      readAt: '2 days ago'
    }
  ]
};

export default function App(): ReactElement {
  // FIRST PAGE MUST BE AUTH (Sign In or Create Profile)
  const [currentView, setCurrentView] = useState<'auth' | 'dashboard'>('auth');

  // Dynamic user profile: not hardcoded, derived upon sign-in or account creation
  const [user, setUser] = useState<UserProfile | null>(() => {
    try {
      const stored = sessionStorage.getItem('nzz_active_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [articles, setArticles] = useState<Article[]>(MOCK_ARTICLES);
  const [activeArticle, setActiveArticle] = useState<Article | null>(null);
  const [readerTier, setReaderTier] = useState<ReadingTier>('briefing');

  // Authentication & Form States
  const [activeTab, setActiveTab] = useState<AuthTab>('login');
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [isForgotModalOpen, setIsForgotModalOpen] = useState<boolean>(false);
  const [forgotInitialEmail, setForgotInitialEmail] = useState<string>('');
  const [isProfileOpen, setIsProfileOpen] = useState<boolean>(false);

  const [loginIdentifier, setLoginIdentifier] = useState<string>('');
  const [loginPassword, setLoginPassword] = useState<string>('');
  const [regData, setRegData] = useState<RegistrationData>({
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

  // Load articles from service / API dynamically
  useEffect(() => {
    fetchArticles().then((data) => {
      if (data && data.length > 0) {
        setArticles(data);
      }
    });
  }, []);

  const showToast = useCallback((title: string, message: string, type: ToastType = 'info') => {
    const id = Date.now().toString() + Math.random().toString(36).substring(2, 6);
    setToasts((prev) => [...prev, { id, title, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const handleOpenForgotPassword = (currentEmailOrUsername: string) => {
    setForgotInitialEmail(currentEmailOrUsername.includes('@') ? currentEmailOrUsername : '');
    setIsForgotModalOpen(true);
  };

  // DYNAMIC SIGN IN: parse human name and initials dynamically from whatever credentials user typed
  const handleLoginSuccess = (identifier: string) => {
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
    const randomStats = generateRandomizedProfileStats();

    const authenticatedUser: UserProfile = {
      name: displayName,
      email: cleanInput.includes('@') ? cleanInput : `${cleanInput}@nzz-reader.ch`,
      membership: 'NZZ Standard Digital Subscriber',
      memberSince: `Subscriber since ${currentDate}`,
      minutesReadToday: 0,
      minutesSavedToday: 0,
      syncDevice: currentDevice,
      avatarInitials: displayInitials,
      age: randomStats.age,
      dailyAverageReadingMinutes: randomStats.dailyAverageReadingMinutes,
      monthlyAverageReadingMinutes: randomStats.monthlyAverageReadingMinutes,
      modalReadingTierMinutes: randomStats.modalReadingTierMinutes,
      modalReadingTierName: randomStats.modalReadingTierName,
      readingHistory: randomStats.readingHistory
    };

    setUser(authenticatedUser);
    try {
      sessionStorage.setItem('nzz_active_user', JSON.stringify(authenticatedUser));
    } catch {}

    showToast('Signed in successfully', `Welcome back, ${displayName}! Accessing your dashboard.`, 'success');
    setCurrentView('dashboard');
  };

  // DYNAMIC PROFILE CREATION: construct user from actual submitted registration fields
  const handleRegisterSuccess = (data: RegistrationData) => {
    const salutationPrefix = (data.salutation && data.salutation !== 'Prefer not to say') ? `${data.salutation} ` : '';
    const fullName = `${salutationPrefix}${data.firstName.trim()} ${data.lastName.trim()}`.trim();
    const fInitial = data.firstName.trim().charAt(0) || 'N';
    const lInitial = data.lastName.trim().charAt(0) || 'Z';
    const initials = (fInitial + lInitial).toUpperCase();

    const currentDevice = detectClientDevice();
    const currentDate = new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(new Date());
    const randomStats = generateRandomizedProfileStats();

    const createdUser: UserProfile = {
      name: fullName,
      email: data.email.trim(),
      membership: 'NZZ Standard Digital Subscriber',
      memberSince: `Member since ${currentDate}`,
      minutesReadToday: 0,
      minutesSavedToday: 0,
      syncDevice: currentDevice,
      avatarInitials: initials,
      age: randomStats.age,
      dailyAverageReadingMinutes: randomStats.dailyAverageReadingMinutes,
      monthlyAverageReadingMinutes: randomStats.monthlyAverageReadingMinutes,
      modalReadingTierMinutes: randomStats.modalReadingTierMinutes,
      modalReadingTierName: randomStats.modalReadingTierName,
      readingHistory: randomStats.readingHistory
    };

    setUser(createdUser);
    try {
      sessionStorage.setItem('nzz_active_user', JSON.stringify(createdUser));
    } catch {}

    showToast('Profile created successfully', `Welcome to NZZ, ${data.firstName}! Your dashboard is ready.`, 'success');
    setCurrentView('dashboard');
  };

  const handleForgotSuccess = (email: string) => {
    showToast(
      'Reset instructions sent',
      `We have dispatched a password recovery link to ${email}.`,
      'success'
    );
  };

  const handleOpenReader = (article: Article, initialTier: ReadingTier | string = 'briefing'): void => {
    let resolvedTier: ReadingTier = 'briefing';
    if (initialTier === 'recommended') {
      const rec = getRecommendedReadingTier(article, activeUser);
      resolvedTier = rec.tier;
    } else if (initialTier === 'bullets') {
      resolvedTier = 'bullets';
    } else if (initialTier === 'analytical' || initialTier === 'full') {
      resolvedTier = initialTier;
    } else {
      resolvedTier = 'briefing';
    }

    if (!article.paragraphs || article.paragraphs.length === 0 || !article.progressiveExpanders || article.progressiveExpanders.length === 0) {
      fetchArticleById(article.id)
        .then((full) => {
          setActiveArticle(full || article);
          setReaderTier(resolvedTier);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        })
        .catch((e) => {
          console.warn('Error fetching full article detail:', e);
          setActiveArticle(article);
          setReaderTier(resolvedTier);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        });
      return;
    }
    setActiveArticle(article);
    setReaderTier(resolvedTier);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCloseReader = () => {
    setActiveArticle(null);
  };

  const handleUpdateStats = (savedMinutes: number) => {
    const minutesRead = Math.max(1, Math.round(savedMinutes * 0.4));
    setUser((prev) => {
      const current = prev || DEFAULT_GUEST_USER;
      const newHistoryEntry = {
        articleId: activeArticle?.id || 'reading-session',
        articleTitle: activeArticle?.title || 'Editorial Reading Session',
        tierChosen: readerTier,
        minutesRead,
        readAt: 'Just now'
      };
      const updated: UserProfile = {
        ...current,
        minutesSavedToday: current.minutesSavedToday + savedMinutes,
        minutesReadToday: current.minutesReadToday + minutesRead,
        readingHistory: [newHistoryEntry, ...(current.readingHistory || [])].slice(0, 10)
      };
      try {
        sessionStorage.setItem('nzz_active_user', JSON.stringify(updated));
      } catch {}
      return updated;
    });

    recordReadingTime(savedMinutes, minutesRead).catch(() => {});

    showToast('Reading session logged', `${savedMinutes} minutes saved via semantic argument distillation.`, 'success');
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

  // 1. Auth View: First access page (Sign in or Create Profile)
  if (currentView === 'auth') {
    return (
      <>
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
        <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      </>
    );
  }

  // 2. Reader View: Dynamic semantic reader canvas
  if (activeArticle) {
    return (
      <>
        <FlexReaderView
          article={activeArticle}
          user={activeUser}
          initialTier={readerTier}
          articles={articles}
          onBack={handleCloseReader}
          onUpdateStats={handleUpdateStats}
          onSelectArticle={handleOpenReader}
          onOpenProfile={() => setIsProfileOpen(true)}
        />
        <ProfileModal
          isOpen={isProfileOpen}
          user={activeUser}
          onClose={() => setIsProfileOpen(false)}
          onSignOut={handleSignOut}
          returnLabel="← Back to Article"
          returnContext="reader"
        />
        <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      </>
    );
  }

  // 3. Subscriber Dashboard View: Grid of Articles + Profile Modal
  return (
    <>
      <DashboardTopBar
        user={activeUser}
        onOpenProfile={() => setIsProfileOpen(true)}
        onSignOut={handleSignOut}
      />
      <ArticleGrid
        articles={articles}
        user={activeUser}
        onOpenReader={handleOpenReader}
      />
      <Footer />
      <ProfileModal
        isOpen={isProfileOpen}
        user={activeUser}
        onClose={() => setIsProfileOpen(false)}
        onSignOut={handleSignOut}
        returnLabel="← Back to Articles"
        returnContext="dashboard"
      />
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </>
  );
}
