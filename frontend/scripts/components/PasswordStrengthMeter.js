    /* 3. PasswordStrengthMeter */
    function PasswordStrengthMeter({ password = '' }) {
      const { fillClass, label } = useMemo(() => {
        if (!password) {
          return { fillClass: '', label: 'Not entered yet' };
        }

        let score = 0;
        if (password.length >= 8) score += 1;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
        if (/[0-9]/.test(password)) score += 1;
        if (/[^A-Za-z0-9]/.test(password)) score += 1;

        switch (score) {
          case 1:
            return { fillClass: 'strength-fill-weak', label: 'Weak' };
          case 2:
            return { fillClass: 'strength-fill-fair', label: 'Fair' };
          case 3:
            return { fillClass: 'strength-fill-good', label: 'Good' };
          case 4:
            return { fillClass: 'strength-fill-strong', label: 'Strong' };
          default:
            return { fillClass: 'strength-fill-weak', label: 'Too short (min. 8 characters)' };
        }
      }, [password]);

      return (
        <div className="strength-meter-wrapper" aria-live="polite">
          <div className="strength-bar-track">
            <div className={`strength-bar-fill ${fillClass}`} />
          </div>
          <div className="strength-status-row">
            <span className="strength-text">Password strength: {label}</span>
            <span className="strength-criteria-hint">At least 8 characters, upper/lowercase & number</span>
          </div>
        </div>
      );
    }


window.PasswordStrengthMeter = PasswordStrengthMeter;
