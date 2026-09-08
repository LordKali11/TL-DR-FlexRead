/**
 * Type definitions for NZZ Authentication & Profile Creation Application
 */

export type Salutation = 'Mr.' | 'Ms.' | 'Prefer not to say';

export type AuthTab = 'login' | 'register';

export type ToastType = 'info' | 'success' | 'error';

export interface ToastItem {
  id: string;
  title: string;
  message: string;
  type: ToastType;
}

export interface RegistrationData {
  salutation: Salutation;
  firstName: string;
  lastName: string;
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
  newsletter: boolean;
}

export interface RegistrationErrors {
  firstName?: string;
  lastName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  terms?: string;
}

export interface LoginErrors {
  identifier?: string;
  password?: string;
}

export interface PasswordStrengthEvaluation {
  fillClass: string;
  label: string;
}

// ==========================================
// NZZ Flex Read Dynamic Reading System Types
// ==========================================

export type ReadingTier = 'briefing' | 'analytical' | 'full';

export type ArgumentLayer = 'thesis' | 'evidence' | 'counterpoint' | 'context' | 'data';

export interface ArgumentFocusTopic {
  id: string;
  label: string;
  tag: string;
  summary: string;
  paragraphIds: string[];
}

export interface SemanticParagraph {
  id: string;
  layer: ArgumentLayer;
  minTier: ReadingTier;
  text: string;
  argumentId?: string;
  keyTakeaway?: string;
  statsMetric?: {
    value: string;
    label: string;
  };
}

export interface ProgressiveExpander {
  id: string;
  title: string;
  category: string;
  badge?: string;
  readTime?: string;
  previewSnippet: string;
  keyTakeaway?: string;
  fullContent: string;
  dataCallout?: {
    value: string;
    label: string;
  };
  source?: string;
}

export interface ArticleSummary {
  id: string;
  slug: string;
  kicker: string;
  title: string;
  subtitle: string;
  author: string;
  authorRole: string;
  date: string;
  publishedAt?: string;
  topic: string;
  heroImage: string;
  readingTimes: {
    briefing: number;
    analytical: number;
    full: number;
  };
  summaryBullets: string[];
  takeaways?: string[];
  argumentCount?: number;
  dossierCount?: number;
  paragraphsCount?: number;
}

export interface Article extends ArticleSummary {
  takeaways: string[];
  argumentFocusTopics: ArgumentFocusTopic[];
  paragraphs: SemanticParagraph[];
  expanders?: ProgressiveExpander[];
  progressiveExpanders?: ProgressiveExpander[];
}

export interface UserProfile {
  name: string;
  email: string;
  membership: string;
  memberSince: string;
  minutesReadToday: number;
  minutesSavedToday: number;
  syncDevice: string;
  avatarInitials: string;
}

