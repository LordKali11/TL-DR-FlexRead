    /* 8. ToastContainer */
    function ToastContainer({ toasts, onDismiss }) {
      if (!toasts || toasts.length === 0) return null;

      return (
        <div className="toast-container" aria-live="assertive" aria-atomic="true">
          {toasts.map((toast) => (
            <div
              key={toast.id}
              className={`toast ${toast.type === 'success' ? 'toast-success' : ''}`}
              onClick={() => onDismiss(toast.id)}
              title="Click to dismiss"
              style={{ cursor: 'pointer' }}
            >
              <div className="toast-body">
                <strong>{toast.title}</strong>
                <p>{toast.message}</p>
              </div>
            </div>
          ))}
        </div>
      );
    }


window.ToastContainer = ToastContainer;
