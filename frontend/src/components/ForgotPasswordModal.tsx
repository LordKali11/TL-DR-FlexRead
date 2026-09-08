import React, { useState, useEffect } from 'react';

interface ForgotPasswordModalProps {
  isOpen: boolean;
  initialEmail?: string;
  onClose: () => void;
  onSubmitSuccess: (email: string) => void;
}

export default function ForgotPasswordModal({
  isOpen,
  initialEmail = '',
  onClose,
  onSubmitSuccess
}: ForgotPasswordModalProps): React.ReactElement | null {
  const [email, setEmail] = useState<string>('');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      setEmail(initialEmail);
      setError('');
    }
  }, [isOpen, initialEmail]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim() || !emailPattern.test(email.trim())) {
      setError('Please enter a valid email address.');
      return;
    }

    setError('');
    onSubmitSuccess(email.trim());
    onClose();
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="nzz-modal-backdrop"
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="modal-content">
        <div className="modal-header">
          <h3 className="modal-title" id="modal-title">Reset Password</h3>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            &times;
          </button>
        </div>
        <p className="modal-description">
          Enter the email address associated with your NZZ account. We will immediately send you a secure link to reset your password.
        </p>
        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="modal-forgot-email" className="form-label">Email address</label>
            <input
              type="email"
              id="modal-forgot-email"
              className={`form-input ${error ? 'has-error' : ''}`}
              placeholder="name@example.ch"
              value={email}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                setEmail(e.target.value);
                if (error) setError('');
              }}
              autoFocus
              required
            />
            {error && <div className="error-feedback visible">{error}</div>}
          </div>
          <div className="modal-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              <span className="btn-label">Request Link</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
