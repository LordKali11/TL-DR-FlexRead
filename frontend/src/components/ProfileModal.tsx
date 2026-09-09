import React from 'react';
import { UserProfile } from '../types';

interface ProfileModalProps {
  isOpen: boolean;
  user: UserProfile;
  onClose: () => void;
  onSignOut: () => void;
}

export const ProfileModal: React.FC<ProfileModalProps> = ({
  isOpen,
  user,
  onClose,
  onSignOut
}) => {
  if (!isOpen) return null;

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
      aria-labelledby="profile-modal-title"
    >
      <div className="modal-content profile-modal-content">
        <div className="modal-header">
          <div>
            <div className="profile-editorial-badge">NZZ MITGLIEDSCHAFT · SUBSCRIBER PROFILE</div>
            <h3 className="modal-title" id="profile-modal-title">Subscriber Profile</h3>
          </div>
          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close profile"
          >
            &times;
          </button>
        </div>

        {/* Profile Card Header */}
        <div className="profile-identity-card">
          <div className="profile-avatar-large" aria-hidden="true">
            {user.avatarInitials || 'NZ'}
          </div>
          <div className="profile-identity-text">
            <h4 className="profile-identity-name">{user.name}</h4>
            <div className="profile-identity-email">{user.email}</div>
            <div className="profile-status-chip">
              <span className="profile-status-dot"></span>
              {user.membership || 'NZZ Standard Digital Subscriber'}
            </div>
          </div>
        </div>

        {/* Profile Details List */}
        <div className="profile-details-grid">
          <div className="profile-detail-item">
            <span className="profile-detail-label">Subscription Tier</span>
            <span className="profile-detail-value">{user.membership || 'Standard Digital'}</span>
          </div>
          <div className="profile-detail-item">
            <span className="profile-detail-label">Membership Status</span>
            <span className="profile-detail-value status-active">
              <span className="dot-active"></span> Active (Annual Access)
            </span>
          </div>
          <div className="profile-detail-item">
            <span className="profile-detail-label">Member Since</span>
            <span className="profile-detail-value">{user.memberSince || '2026'}</span>
          </div>
          <div className="profile-detail-item">
            <span className="profile-detail-label">Connected Device</span>
            <span className="profile-detail-value">{user.syncDevice || 'Desktop Browser'}</span>
          </div>
          <div className="profile-detail-item">
            <span className="profile-detail-label">Reading Mode</span>
            <span className="profile-detail-value">Flex Read · Adaptive Briefing</span>
          </div>
          <div className="profile-detail-item">
            <span className="profile-detail-label">Security & Auth</span>
            <span className="profile-detail-value">2-Factor Authentication Protected</span>
          </div>
        </div>

        {/* Modal Actions */}
        <div className="modal-actions profile-modal-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={onClose}
          >
            Back to Dashboard
          </button>
          <button
            type="button"
            className="btn-primary btn-profile-signout"
            onClick={() => {
              onClose();
              onSignOut();
            }}
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfileModal;
