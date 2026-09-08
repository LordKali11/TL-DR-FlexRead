const LoginForm = window.LoginForm;
const RegisterForm = window.RegisterForm;
const { useState } = React;

    /* 7. AuthCard */
    function AuthCard({
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
      onFillDemo,
      onNavigateToDashboard
    }) {
      return (
        <section className="auth-panel" aria-label="Sign In and Registration">
          <div className="auth-card">
            <div className="brand-header">
              <a href="https://www.nzz.ch/" title="Neue Zürcher Zeitung" className="logo-link">
                <img src="assets/nzz-logo.svg" alt="Neue Zürcher Zeitung Logo" className="nzz-logo" />
              </a>
              <p className="brand-subline">My NZZ Account</p>
            </div>

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
                Create Account
              </button>
            </div>

            <div className="demo-bar">
              <span>Demo Mode:</span>
              <button
                type="button"
                className="btn-demo"
                onClick={onFillDemo}
                title="Populate test sample credentials"
              >
                Fill Sample Account
              </button>
            </div>

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

            
          </div>
        </section>
      );
    }


window.AuthCard = AuthCard;
