/**
 * Neue Zürcher Zeitung (NZZ) - Login & Registration Script (English Version)
 * Handles tab transitions, password visibility, password strength calculation,
 * accessible form validation, demo auto-fill, and modal dialogs.
 */

document.addEventListener('DOMContentLoaded', () => {
  initCurrentDate();
  initTabNavigation();
  initPasswordToggles();
  initPasswordStrengthMeter();
  initForms();
  initForgotPasswordModal();
  initDemoHelper();
  initAlternativeLogins();
});

/* --------------------------------------------------------------------------
   1. Date Display (English Locale)
   -------------------------------------------------------------------------- */
function initCurrentDate() {
  const dateEl = document.getElementById('current-date');
  if (!dateEl) return;

  const now = new Date();
  const options = { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' };
  try {
    const formatted = new Intl.DateTimeFormat('en-US', options).format(now);
    dateEl.textContent = formatted;
  } catch (e) {
    // Fallback if locale format fails
    dateEl.textContent = now.toLocaleDateString();
  }
}

/* --------------------------------------------------------------------------
   2. Accessible Tab Navigation (Sign In / Create Account)
   -------------------------------------------------------------------------- */
function initTabNavigation() {
  const tabLogin = document.getElementById('tab-login');
  const tabRegister = document.getElementById('tab-register');
  const panelLogin = document.getElementById('panel-login');
  const panelRegister = document.getElementById('panel-register');
  
  const linkGoRegister = document.getElementById('link-go-register');
  const linkGoLogin = document.getElementById('link-go-login');

  function switchTab(target) {
    if (target === 'register') {
      tabLogin.classList.remove('active');
      tabLogin.setAttribute('aria-selected', 'false');
      panelLogin.classList.remove('active');

      tabRegister.classList.add('active');
      tabRegister.setAttribute('aria-selected', 'true');
      panelRegister.classList.add('active');

      const firstInput = document.getElementById('reg-firstname');
      if (firstInput) firstInput.focus();
    } else {
      tabRegister.classList.remove('active');
      tabRegister.setAttribute('aria-selected', 'false');
      panelRegister.classList.remove('active');

      tabLogin.classList.add('active');
      tabLogin.setAttribute('aria-selected', 'true');
      panelLogin.classList.add('active');

      const firstInput = document.getElementById('login-identifier');
      if (firstInput) firstInput.focus();
    }
  }

  if (tabLogin && tabRegister) {
    tabLogin.addEventListener('click', () => switchTab('login'));
    tabRegister.addEventListener('click', () => switchTab('register'));

    // Keyboard support for tabs (ArrowLeft / ArrowRight)
    [tabLogin, tabRegister].forEach(tab => {
      tab.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
          e.preventDefault();
          const target = tab.id === 'tab-login' ? 'register' : 'login';
          switchTab(target);
        }
      });
    });
  }

  if (linkGoRegister) {
    linkGoRegister.addEventListener('click', () => switchTab('register'));
  }
  if (linkGoLogin) {
    linkGoLogin.addEventListener('click', () => switchTab('login'));
  }
}

/* --------------------------------------------------------------------------
   3. Password Visibility Toggles
   -------------------------------------------------------------------------- */
function initPasswordToggles() {
  const toggleButtons = document.querySelectorAll('.password-toggle-btn');

  toggleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (!input) return;

      const eyeIcon = btn.querySelector('.icon-eye');
      const eyeOffIcon = btn.querySelector('.icon-eye-off');
      const isPassword = input.type === 'password';

      input.type = isPassword ? 'text' : 'password';
      btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');

      if (eyeIcon && eyeOffIcon) {
        eyeIcon.classList.toggle('hidden', isPassword);
        eyeOffIcon.classList.toggle('hidden', !isPassword);
      }
    });
  });
}

/* --------------------------------------------------------------------------
   4. Real-time Password Strength Meter & Confirmation Check
   -------------------------------------------------------------------------- */
function initPasswordStrengthMeter() {
  const regPassword = document.getElementById('reg-password');
  const regPasswordConfirm = document.getElementById('reg-password-confirm');
  const strengthFill = document.getElementById('strength-fill');
  const strengthText = document.getElementById('strength-text');

  if (!regPassword || !strengthFill || !strengthText) return;

  function calculateStrength(pwd) {
    if (!pwd) return { score: 0, text: 'Not entered yet', class: '' };
    
    let score = 0;
    if (pwd.length >= 8) score += 1;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score += 1;
    if (/[0-9]/.test(pwd)) score += 1;
    if (/[^A-Za-z0-9]/.test(pwd)) score += 1;

    switch (score) {
      case 1:
        return { score: 1, text: 'Weak', class: 'strength-fill-weak' };
      case 2:
        return { score: 2, text: 'Fair', class: 'strength-fill-fair' };
      case 3:
        return { score: 3, text: 'Good', class: 'strength-fill-good' };
      case 4:
        return { score: 4, text: 'Strong', class: 'strength-fill-strong' };
      default:
        return { score: 1, text: 'Too short (min. 8 characters)', class: 'strength-fill-weak' };
    }
  }

  regPassword.addEventListener('input', () => {
    const val = regPassword.value.trim();
    const result = calculateStrength(val);

    strengthFill.className = 'strength-bar-fill ' + result.class;
    strengthText.textContent = `Password strength: ${result.text}`;

    if (val.length >= 8) {
      clearFieldError(regPassword, 'reg-password-error');
    }

    // Check confirmation match if confirm field has text
    if (regPasswordConfirm && regPasswordConfirm.value.trim()) {
      checkPasswordMatch();
    }
  });

  if (regPasswordConfirm) {
    regPasswordConfirm.addEventListener('input', checkPasswordMatch);
  }

  function checkPasswordMatch() {
    const p1 = regPassword.value;
    const p2 = regPasswordConfirm.value;

    if (!p2) {
      clearFieldError(regPasswordConfirm, 'reg-password-confirm-error');
      return;
    }

    if (p1 !== p2) {
      showFieldError(regPasswordConfirm, 'reg-password-confirm-error', 'Passwords do not match.');
    } else {
      clearFieldError(regPasswordConfirm, 'reg-password-confirm-error');
    }
  }
}

/* --------------------------------------------------------------------------
   5. Form Validation & Submissions
   -------------------------------------------------------------------------- */
function initForms() {
  const formLogin = document.getElementById('form-login');
  const formRegister = document.getElementById('form-register');

  // ---------- Login Form ----------
  if (formLogin) {
    const identifierInput = document.getElementById('login-identifier');
    const passwordInput = document.getElementById('login-password');
    const submitBtn = document.getElementById('btn-submit-login');

    [identifierInput, passwordInput].forEach(inp => {
      inp.addEventListener('input', () => {
        clearFieldError(inp, inp.id + '-error');
      });
    });

    formLogin.addEventListener('submit', (e) => {
      e.preventDefault();
      let isValid = true;

      const identifier = identifierInput.value.trim();
      const password = passwordInput.value;

      if (!identifier) {
        showFieldError(identifierInput, 'login-identifier-error', 'Please enter your email address or username.');
        isValid = false;
      } else {
        clearFieldError(identifierInput, 'login-identifier-error');
      }

      if (!password) {
        showFieldError(passwordInput, 'login-password-error', 'Please enter your password.');
        isValid = false;
      } else {
        clearFieldError(passwordInput, 'login-password-error');
      }

      if (!isValid) return;

      // Simulate Authentication Request
      setButtonLoading(submitBtn, true);

      setTimeout(() => {
        setButtonLoading(submitBtn, false);
        showToast('Signed in successfully', `Welcome back to NZZ, ${identifier.split('@')[0]}!`, 'success');
      }, 900);
    });
  }

  // ---------- Register Form ----------
  if (formRegister) {
    const firstName = document.getElementById('reg-firstname');
    const lastName = document.getElementById('reg-lastname');
    const email = document.getElementById('reg-email');
    const password = document.getElementById('reg-password');
    const passwordConfirm = document.getElementById('reg-password-confirm');
    const terms = document.getElementById('reg-terms');
    const submitBtn = document.getElementById('btn-submit-register');

    [firstName, lastName, email, password, passwordConfirm].forEach(inp => {
      inp.addEventListener('input', () => {
        clearFieldError(inp, inp.id + '-error');
      });
    });

    terms.addEventListener('change', () => {
      clearFieldError(terms, 'reg-terms-error');
    });

    formRegister.addEventListener('submit', (e) => {
      e.preventDefault();
      let isValid = true;

      if (!firstName.value.trim()) {
        showFieldError(firstName, 'reg-firstname-error', 'Please provide your first name.');
        isValid = false;
      }

      if (!lastName.value.trim()) {
        showFieldError(lastName, 'reg-lastname-error', 'Please provide your last name.');
        isValid = false;
      }

      const emailVal = email.value.trim();
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailVal || !emailPattern.test(emailVal)) {
        showFieldError(email, 'reg-email-error', 'Please enter a valid email address.');
        isValid = false;
      }

      if (password.value.length < 8) {
        showFieldError(password, 'reg-password-error', 'Password must be at least 8 characters long.');
        isValid = false;
      }

      if (password.value !== passwordConfirm.value) {
        showFieldError(passwordConfirm, 'reg-password-confirm-error', 'Passwords do not match.');
        isValid = false;
      }

      if (!terms.checked) {
        showFieldError(terms, 'reg-terms-error', 'Please accept the Terms & Conditions and Privacy Policy.');
        isValid = false;
      }

      if (!isValid) return;

      // Simulate Registration Request
      setButtonLoading(submitBtn, true);

      setTimeout(() => {
        setButtonLoading(submitBtn, false);
        showToast(
          'Account created successfully', 
          `Welcome to NZZ, ${firstName.value.trim()} ${lastName.value.trim()}! You can now sign in.`, 
          'success'
        );

        // Switch to login tab and prefill
        const tabLogin = document.getElementById('tab-login');
        if (tabLogin) tabLogin.click();
        const loginId = document.getElementById('login-identifier');
        if (loginId) loginId.value = emailVal;
      }, 1100);
    });
  }
}

/* --------------------------------------------------------------------------
   6. Forgot Password Modal Dialog
   -------------------------------------------------------------------------- */
function initForgotPasswordModal() {
  const modal = document.getElementById('modal-forgot-password');
  const openBtn = document.getElementById('btn-open-forgot');
  const closeBtn = document.getElementById('btn-close-modal');
  const cancelBtn = document.getElementById('btn-cancel-modal');
  const form = document.getElementById('form-forgot');
  const emailInput = document.getElementById('forgot-email');

  if (!modal || !openBtn) return;

  function openModal() {
    if (typeof modal.showModal === 'function') {
      modal.showModal();
    } else {
      modal.setAttribute('open', 'true');
    }
    if (emailInput) {
      // Pre-fill if user had entered email in login
      const loginIdentifier = document.getElementById('login-identifier');
      if (loginIdentifier && loginIdentifier.value.includes('@')) {
        emailInput.value = loginIdentifier.value.trim();
      }
      emailInput.focus();
    }
  }

  function closeModal() {
    if (typeof modal.close === 'function') {
      modal.close();
    } else {
      modal.removeAttribute('open');
    }
    clearFieldError(emailInput, 'forgot-email-error');
  }

  openBtn.addEventListener('click', openModal);
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

  // Close on backdrop click
  modal.addEventListener('click', (e) => {
    const rect = modal.getBoundingClientRect();
    const isInDialog = (
      rect.top <= e.clientY &&
      e.clientY <= rect.top + rect.height &&
      rect.left <= e.clientX &&
      e.clientX <= rect.left + rect.width
    );
    if (!isInDialog) {
      closeModal();
    }
  });

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const val = emailInput.value.trim();
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (!val || !emailPattern.test(val)) {
        showFieldError(emailInput, 'forgot-email-error', 'Please enter a valid email address.');
        return;
      }

      closeModal();
      showToast('Email sent', `If an account exists for ${val}, we have sent a reset link.`, 'success');
    });
  }
}

/* --------------------------------------------------------------------------
   7. Quick Test Demo Helper (Fill in Sample Data)
   -------------------------------------------------------------------------- */
function initDemoHelper() {
  const demoBtn = document.getElementById('btn-fill-demo');
  if (!demoBtn) return;

  demoBtn.addEventListener('click', () => {
    const isLoginActive = document.getElementById('panel-login').classList.contains('active');

    if (isLoginActive) {
      const idInput = document.getElementById('login-identifier');
      const pwdInput = document.getElementById('login-password');
      if (idInput) idInput.value = 'anna.meier@nzz-reader.ch';
      if (pwdInput) pwdInput.value = 'Switzerland#2026!';
      clearFieldError(idInput, 'login-identifier-error');
      clearFieldError(pwdInput, 'login-password-error');
      showToast('Sample credentials loaded', 'Demo data for NZZ sign in has been populated.');
    } else {
      const fn = document.getElementById('reg-firstname');
      const ln = document.getElementById('reg-lastname');
      const em = document.getElementById('reg-email');
      const un = document.getElementById('reg-username');
      const pw = document.getElementById('reg-password');
      const pwc = document.getElementById('reg-password-confirm');
      const tm = document.getElementById('reg-terms');

      if (fn) fn.value = 'Anna';
      if (ln) ln.value = 'Meier';
      if (em) em.value = 'anna.meier@example.ch';
      if (un) un.value = 'ameier';
      if (pw) {
        pw.value = 'Switzerland#2026!';
        pw.dispatchEvent(new Event('input'));
      }
      if (pwc) {
        pwc.value = 'Switzerland#2026!';
        pwc.dispatchEvent(new Event('input'));
      }
      if (tm) tm.checked = true;

      showToast('Sample data loaded', 'Demo data for NZZ profile creation has been populated.');
    }
  });
}

/* --------------------------------------------------------------------------
   8. Alternative Logins (Code, Apple, Google)
   -------------------------------------------------------------------------- */
function initAlternativeLogins() {
  const btnCode = document.getElementById('btn-login-code');
  const btnApple = document.getElementById('btn-login-apple');
  const btnGoogle = document.getElementById('btn-login-google');

  if (btnCode) {
    btnCode.addEventListener('click', () => {
      const emailField = document.getElementById('login-identifier');
      const emailVal = emailField ? emailField.value.trim() : '';
      if (emailVal.includes('@')) {
        showToast('One-time code requested', `A 6-digit verification code was sent to ${emailVal}.`, 'success');
      } else {
        showToast('Email address required', 'Please enter your email address in the field first.');
        if (emailField) emailField.focus();
      }
    });
  }

  if (btnApple) {
    btnApple.addEventListener('click', () => {
      showToast('Apple ID Authentication', 'Simulating connection to Apple Sign-In service...');
    });
  }

  if (btnGoogle) {
    btnGoogle.addEventListener('click', () => {
      showToast('Google Authentication', 'Simulating connection to Google Sign-In service...');
    });
  }
}

/* --------------------------------------------------------------------------
   9. Helper Utilities: Errors, Buttons, Toasts
   -------------------------------------------------------------------------- */
function showFieldError(inputEl, errorId, message) {
  if (inputEl) inputEl.classList.add('has-error');
  const errorEl = document.getElementById(errorId);
  if (errorEl) {
    if (message) errorEl.textContent = message;
    errorEl.classList.add('visible');
  }
}

function clearFieldError(inputEl, errorId) {
  if (inputEl) inputEl.classList.remove('has-error');
  const errorEl = document.getElementById(errorId);
  if (errorEl) {
    errorEl.classList.remove('visible');
  }
}

function setButtonLoading(buttonEl, isLoading) {
  if (!buttonEl) return;
  const spinner = buttonEl.querySelector('.btn-spinner');
  const label = buttonEl.querySelector('.btn-label');

  buttonEl.disabled = isLoading;
  if (spinner) spinner.classList.toggle('hidden', !isLoading);
  if (label) label.style.opacity = isLoading ? '0.6' : '1';
}

function showToast(title, message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type === 'success' ? 'toast-success' : ''}`;
  toast.innerHTML = `
    <div class="toast-body">
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(message)}</p>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4200);
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
