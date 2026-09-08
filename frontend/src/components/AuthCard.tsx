import React from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import { AuthTab, RegistrationData, ToastType } from '../types';

interface AuthCardProps {
  activeTab: AuthTab;
  setActiveTab: (tab: AuthTab) => void;
  onOpenForgotPassword: (currentEmailOrUsername: string) => void;
  onLoginSuccess: (identifier: string) => void;
  onRegisterSuccess: (data: RegistrationData) => void;
  onShowToast: (title: string, message: string, type?: ToastType) => void;
  loginIdentifier: string;
  setLoginIdentifier: (val: string) => void;
  loginPassword: string;
  setLoginPassword: (val: string) => void;
  regData: RegistrationData;
  setRegData: React.Dispatch<React.SetStateAction<RegistrationData>>;
  onFillDemo: () => void;
}

export default function AuthCard({
activeTab,
setActiveTab,
onOpenForgotPassword,
onLoginSuccess,
onRegisterSuccess,
onShowToast,
loginIdentifier,
setLoginIdentifier,
loginPassword,
setLoginPassword,
regData,
setRegData,
onFillDemo
}: AuthCardProps): React.ReactElement {
  return (
    <section className="auth-panel" aria-label="Sign In and Registration">
      <div className="auth-card">
        {/* Brand Logo Header */}
        <div className="brand-header">
          <a href="https://www.nzz.ch/" title="Neue Zürcher Zeitung" className="logo-link">
            <img src="/assets/nzz-logo.svg" alt="Neue Zürcher Zeitung Logo" className="nzz-logo" />
          </a>
          <p className="brand-subline">My NZZ Account</p>
        </div>

        {/* Auth Tab Switcher */}
        <div className="tab-group" role="tablist" aria-label="Account Actions">
          <button
            type="button"
            className={`tab-btn ${activeTab === 'login' ? 'active' : ''}`}
            id="tab-login"
            role="tab"
            aria-selected={activeTab === 'login'}
            aria-controls="panel-login"
            onClick={() => setActiveTab('login')}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`tab-btn ${activeTab === 'register' ? 'active' : ''}`}
            id="tab-register"
            role="tab"
            aria-selected={activeTab === 'register'}
            aria-controls="panel-register"
            onClick={() => setActiveTab('register')}
          >
            Create Profile
          </button>
        </div>

        {/* Demo Mode Quick Bar */}
        <div className="demo-bar">
          <span>Demo Profile:</span>
          <button
            type="button"
            className="btn-demo"
            onClick={onFillDemo}
            title="Populate sample subscriber credentials"
          >
            Fill Sample Account
          </button>
        </div>

        {/* Form Panels */}
        {activeTab === 'login' ? (
          <div id="panel-login" role="tabpanel" aria-labelledby="tab-login">
            <LoginForm
              onLoginSuccess={onLoginSuccess}
              onOpenForgotPassword={onOpenForgotPassword}
              onSwitchToRegister={() => setActiveTab('register')}
              onShowToast={onShowToast}
              identifierValue={loginIdentifier}
              setIdentifierValue={setLoginIdentifier}
              passwordValue={loginPassword}
              setPasswordValue={setLoginPassword}
            />
          </div>
        ) : (
          <div id="panel-register" role="tabpanel" aria-labelledby="tab-register">
            <RegisterForm
              onRegisterSuccess={onRegisterSuccess}
              onSwitchToLogin={() => setActiveTab('login')}
              regData={regData}
              setRegData={setRegData}
            />
          </div>
        )}

        {/* Seamless Navigation Link to Flex Read Dashboard */}
        {onNavigateToDashboard && (
          <div className="auth-dashboard-bridge">
            <span>Direct Access:</span>
            <button
              type="button"
              onClick={onNavigateToDashboard}
              className="btn-bridge-link"
            >
              Explore NZZ Flex Read Articles &rarr;
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
