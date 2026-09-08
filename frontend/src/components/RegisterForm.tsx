import React, { useState } from 'react';
import PasswordStrengthMeter from './PasswordStrengthMeter';
import { RegistrationData, RegistrationErrors, Salutation } from '../types';

interface RegisterFormProps {
  onRegisterSuccess: (data: RegistrationData) => void;
  onSwitchToLogin: () => void;
  regData: RegistrationData;
  setRegData: React.Dispatch<React.SetStateAction<RegistrationData>>;
}

export default function RegisterForm({
  onRegisterSuccess,
  onSwitchToLogin,
  regData,
  setRegData
}: RegisterFormProps): React.ReactElement {
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState<boolean>(false);
  const [errors, setErrors] = useState<RegistrationErrors>({});
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleChange = <K extends keyof RegistrationData>(field: K, value: RegistrationData[K]) => {
    setRegData((prev) => ({ ...prev, [field]: value }));
    if (errors[field as keyof RegistrationErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const newErrors: RegistrationErrors = {};

    if (!regData.firstName.trim()) {
      newErrors.firstName = 'Please provide your first name.';
    }
    if (!regData.lastName.trim()) {
      newErrors.lastName = 'Please provide your last name.';
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!regData.email.trim() || !emailPattern.test(regData.email.trim())) {
      newErrors.email = 'Please enter a valid email address.';
    }

    if (regData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters long.';
    }

    if (regData.password !== regData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match.';
    }

    if (!regData.acceptTerms) {
      newErrors.terms = 'Please accept the Terms & Conditions and Privacy Policy.';
    }

    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;

    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      onRegisterSuccess(regData);
    }, 1100);
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      {/* Salutation */}
      <div className="form-group">
        <label className="form-label">Title / Salutation</label>
        <div className="radio-pill-group" role="radiogroup" aria-label="Select title">
          {(['Mr.', 'Ms.', 'Prefer not to say'] as Salutation[]).map((title) => (
            <label key={title} className="radio-pill">
              <input
                type="radio"
                name="salutation"
                value={title}
                checked={regData.salutation === title}
                onChange={(e) => handleChange('salutation', e.target.value as Salutation)}
              />
              <span>{title}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Name Grid */}
      <div className="name-grid">
        <div className="form-group">
          <label htmlFor="reg-firstname" className="form-label">
            First name <span className="required-mark">*</span>
          </label>
          <input
            type="text"
            id="reg-firstname"
            name="firstname"
            className={`form-input ${errors.firstName ? 'has-error' : ''}`}
            placeholder="Max"
            autoComplete="given-name"
            value={regData.firstName}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('firstName', e.target.value)}
            required
          />
          {errors.firstName && (
            <div className="error-feedback visible">{errors.firstName}</div>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="reg-lastname" className="form-label">
            Last name <span className="required-mark">*</span>
          </label>
          <input
            type="text"
            id="reg-lastname"
            name="lastname"
            className={`form-input ${errors.lastName ? 'has-error' : ''}`}
            placeholder="Muster"
            autoComplete="family-name"
            value={regData.lastName}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('lastName', e.target.value)}
            required
          />
          {errors.lastName && (
            <div className="error-feedback visible">{errors.lastName}</div>
          )}
        </div>
      </div>

      {/* Email */}
      <div className="form-group">
        <label htmlFor="reg-email" className="form-label">
          Email address <span className="required-mark">*</span>
        </label>
        <div className="input-wrapper">
          <input
            type="email"
            id="reg-email"
            name="email"
            className={`form-input ${errors.email ? 'has-error' : ''}`}
            placeholder="max.muster@example.ch"
            autoComplete="email"
            value={regData.email}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('email', e.target.value)}
            required
          />
          <span className="field-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
              <polyline points="22,6 12,13 2,6"></polyline>
            </svg>
          </span>
        </div>
        {errors.email && (
          <div className="error-feedback visible">{errors.email}</div>
        )}
      </div>

      {/* Optional Username */}
      <div className="form-group">
        <div className="label-row">
          <label htmlFor="reg-username" className="form-label">
            Desired username
          </label>
          <span className="field-hint">Optional</span>
        </div>
        <div className="input-wrapper">
          <input
            type="text"
            id="reg-username"
            name="username"
            className="form-input"
            placeholder="e.g. mmuster"
            autoComplete="username"
            value={regData.username}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('username', e.target.value)}
          />
          <span className="field-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="4"></circle>
              <path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.92 7.94"></path>
            </svg>
          </span>
        </div>
      </div>

      {/* Set Password & Strength Meter */}
      <div className="form-group">
        <label htmlFor="reg-password" className="form-label">
          Set password <span className="required-mark">*</span>
        </label>
        <div className="input-wrapper">
          <input
            type={showPassword ? 'text' : 'password'}
            id="reg-password"
            name="password"
            className={`form-input ${errors.password ? 'has-error' : ''}`}
            placeholder="At least 8 characters"
            autoComplete="new-password"
            value={regData.password}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('password', e.target.value)}
            required
          />
          <button
            type="button"
            className="password-toggle-btn"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            onClick={() => setShowPassword((prev) => !prev)}
          >
            {showPassword ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            )}
          </button>
        </div>
        
        <PasswordStrengthMeter password={regData.password} />
        
        {errors.password && (
          <div className="error-feedback visible">{errors.password}</div>
        )}
      </div>

      {/* Confirm Password */}
      <div className="form-group">
        <label htmlFor="reg-password-confirm" className="form-label">
          Confirm password <span className="required-mark">*</span>
        </label>
        <div className="input-wrapper">
          <input
            type={showConfirmPassword ? 'text' : 'password'}
            id="reg-password-confirm"
            name="password_confirm"
            className={`form-input ${errors.confirmPassword ? 'has-error' : ''}`}
            placeholder="Repeat password"
            autoComplete="new-password"
            value={regData.confirmPassword}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('confirmPassword', e.target.value)}
            required
          />
          <button
            type="button"
            className="password-toggle-btn"
            aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
            onClick={() => setShowConfirmPassword((prev) => !prev)}
          >
            {showConfirmPassword ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            )}
          </button>
        </div>
        {errors.confirmPassword && (
          <div className="error-feedback visible">{errors.confirmPassword}</div>
        )}
      </div>

      {/* Consents */}
      <div className="consent-block">
        <label className="custom-checkbox">
          <input
            type="checkbox"
            name="terms"
            checked={regData.acceptTerms}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('acceptTerms', e.target.checked)}
            required
          />
          <span className="checkbox-indicator"></span>
          <span className="checkbox-text">
            I accept the <a href="https://www.nzz.ch/agb" target="_blank" rel="noopener noreferrer">Terms & Conditions</a> and acknowledge the <a href="https://www.nzz.ch/datenschutz" target="_blank" rel="noopener noreferrer">Privacy Policy</a>. <span className="required-mark">*</span>
          </span>
        </label>
        {errors.terms && (
          <div className="error-feedback visible">{errors.terms}</div>
        )}

        <label className="custom-checkbox">
          <input
            type="checkbox"
            name="newsletter"
            checked={regData.newsletter}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleChange('newsletter', e.target.checked)}
          />
          <span className="checkbox-indicator"></span>
          <span className="checkbox-text">
            I would like to receive the free daily briefing from the NZZ editorial team via email. (Unsubscribe anytime)
          </span>
        </label>
      </div>

      <button type="submit" className="btn-primary" disabled={isLoading}>
        {isLoading && <span className="btn-spinner" aria-hidden="true"></span>}
        <span className="btn-label">{isLoading ? 'Creating Account...' : 'Create Account & Profile'}</span>
      </button>

      <div className="auth-switch-note">
        <span>Already have an account?</span>
        <button
          type="button"
          className="link-switch"
          onClick={onSwitchToLogin}
        >
          Sign in here
        </button>
      </div>
    </form>
  );
}
