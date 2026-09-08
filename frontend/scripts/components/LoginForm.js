const { useState } = React;

    /* 5. LoginForm */
    function LoginForm({
      onLoginSuccess,
      onOpenForgotPassword,
      onSwitchToRegister,
      onShowToast,
      identifierValue,
      setIdentifierValue,
      passwordValue,
      setPasswordValue
    }) {
      const [showPassword, setShowPassword] = useState(false);
      const [rememberMe, setRememberMe] = useState(true);
      const [errors, setErrors] = useState({});
      const [isLoading, setIsLoading] = useState(false);

      const handleSubmit = (e) => {
        e.preventDefault();
        const newErrors = {};

        if (!identifierValue.trim()) {
          newErrors.identifier = 'Please enter your email address or username.';
        }
        if (!passwordValue) {
          newErrors.password = 'Please enter your password.';
        }

        setErrors(newErrors);
        if (Object.keys(newErrors).length > 0) return;

        setIsLoading(true);
        setTimeout(() => {
          setIsLoading(false);
          onLoginSuccess(identifierValue.trim());
        }, 900);
      };

      const handleRequestCode = () => {
        if (identifierValue.includes('@')) {
          onShowToast(
            'One-time code requested',
            `A 6-digit verification code was sent to ${identifierValue.trim()}.`,
            'success'
          );
        } else {
          onShowToast(
            'Email address required',
            'Please enter your email address in the field above first.'
          );
          setErrors((prev) => ({
            ...prev,
            identifier: 'Please enter a valid email address to receive a code.'
          }));
        }
      };

      return (
        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="login-identifier" className="form-label">
              Email address or username
              <span className="required-mark" aria-hidden="true">*</span>
            </label>
            <div className="input-wrapper">
              <input
                type="text"
                id="login-identifier"
                name="identifier"
                className={`form-input ${errors.identifier ? 'has-error' : ''}`}
                placeholder="name@example.ch"
                autoComplete="username"
                value={identifierValue}
                onChange={(e) => {
                  setIdentifierValue(e.target.value);
                  if (errors.identifier) setErrors((prev) => ({ ...prev, identifier: '' }));
                }}
                required
              />
              <span className="field-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                  <circle cx="12" cy="7" r="4"></circle>
                </svg>
              </span>
            </div>
            {errors.identifier && (
              <div className="error-feedback visible">{errors.identifier}</div>
            )}
          </div>

          <div className="form-group">
            <div className="label-row">
              <label htmlFor="login-password" className="form-label">
                Password
                <span className="required-mark" aria-hidden="true">*</span>
              </label>
              <button
                type="button"
                className="inline-link"
                onClick={() => onOpenForgotPassword(identifierValue)}
              >
                Forgot password?
              </button>
            </div>
            <div className="input-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                id="login-password"
                name="password"
                className={`form-input ${errors.password ? 'has-error' : ''}`}
                placeholder="Your password"
                autoComplete="current-password"
                value={passwordValue}
                onChange={(e) => {
                  setPasswordValue(e.target.value);
                  if (errors.password) setErrors((prev) => ({ ...prev, password: '' }));
                }}
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
            {errors.password && (
              <div className="error-feedback visible">{errors.password}</div>
            )}
          </div>

          <div className="form-options">
            <label className="custom-checkbox">
              <input
                type="checkbox"
                name="remember"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span className="checkbox-indicator"></span>
              <span className="checkbox-text">Keep me signed in</span>
            </label>
          </div>

          <button type="submit" className="btn-primary" disabled={isLoading}>
            {isLoading && <span className="btn-spinner" aria-hidden="true"></span>}
            <span className="btn-label">{isLoading ? 'Signing In...' : 'Sign In'}</span>
          </button>

          <div className="divider-text">
            <span>or alternatively</span>
          </div>

          <div className="alternative-logins">
            <button
              type="button"
              className="btn-secondary"
              onClick={handleRequestCode}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="4" width="20" height="16" rx="2"></rect>
                <path d="M7 15h10M7 9h2M11 9h6"></path>
              </svg>
              <span>Sign in with one-time code via email</span>
            </button>

            <div className="social-button-grid">
              <button
                type="button"
                className="btn-social"
                onClick={() => onShowToast('Apple ID Authentication', 'Simulating connection to Apple Sign-In service...')}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.37c.61-.75 1.04-1.8 1.01-2.87-.96.04-2.09.65-2.73 1.4-.56.64-1.05 1.69-.97 2.73 1.05.08 2.08-.51 2.69-1.26z"/>
                </svg>
                <span>Apple</span>
              </button>
              <button
                type="button"
                className="btn-social"
                onClick={() => onShowToast('Google Authentication', 'Simulating connection to Google Sign-In service...')}
              >
                <svg width="16" height="16" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.67v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.16z"/>
                  <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.94H1.26v3.15C3.26 21.36 7.33 24 12 24z"/>
                  <path fill="#FBBC05" d="M5.28 14.26c-.25-.72-.38-1.49-.38-2.26s.13-1.54.38-2.26V6.59H1.26C.46 8.18 0 10.03 0 12c0 1.97.46 3.82 1.26 5.41l4.02-3.15z"/>
                  <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.26 6.59l4.02 3.15c.95-2.84 3.6-4.99 6.72-4.99z"/>
                </svg>
                <span>Google</span>
              </button>
            </div>
          </div>

          <div className="auth-switch-note">
            <span>Don't have an account yet?</span>
            <button
              type="button"
              className="link-switch"
              onClick={onSwitchToRegister}
            >
              Register here for free
            </button>
          </div>
        </form>
      );
    }


window.LoginForm = LoginForm;
