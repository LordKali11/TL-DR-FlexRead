# NZZ (Neue Zürcher Zeitung) — Login & Profile Creation

A modern, elegant, and fully responsive sign-in and registration portal for the **Neue Zürcher Zeitung (NZZ)**. The design honors NZZ's rich Swiss editorial tradition: authoritative serif typography, timeless Swiss grotesque controls, the official vector masthead, and a structured newspaper layout.

---

## 📁 Project Structure

```text
nzz-login/
├── assets/
│   └── nzz-logo.svg       # Official NZZ vector logo (SVG)
├── index.html             # Semantic HTML5 layout (Sign In & Registration)
├── styles.css             # Swiss editorial CSS with responsive breakpoints
├── script.js              # Interactive logic (tabs, validation, password meter, toasts)
└── README.md              # Project instructions for VS Code
```

---

## 🚀 Opening & Developing in Visual Studio Code

### Option 1: Open the Project Folder in VS Code
1. Open **VS Code**.
2. From the top menu, select: **File ➔ Open Folder...**.
3. Select this directory:
   ```text
   C:\Users\HP\.gemini\antigravity\scratch\nzz-login
   ```
   *(Or run `code "C:\Users\HP\.gemini\antigravity\scratch\nzz-login"` in your terminal)*

---

### Option 2: Live Preview in Your Browser

#### A. Using the VS Code "Live Server" Extension (Recommended):
1. Install the **"Live Server"** extension (by *Ritwick Dey*) in VS Code if you haven't already.
2. In the VS Code Explorer, right-click `index.html`.
3. Choose **"Open with Live Server"**.
4. The page will instantly open at `http://127.0.0.1:5500/index.html` and hot-reload whenever you edit files.

#### B. Using Python's Built-in Server:
Open the integrated terminal in VS Code (`Ctrl + ` `) and run:
```powershell
python -m http.server 3000
```
Then visit [http://localhost:3000](http://localhost:3000) in your web browser.

#### C. Direct Browser Double-Click (No server needed):
You can also double-click `index.html` directly in File Explorer to view it in Chrome, Edge, Firefox, or Safari.

---

## ✨ Features Included

- **Official NZZ Visual Identity**:
  - Original vector masthead logo (`assets/nzz-logo.svg`).
  - Swiss editorial typography (*Newsreader* serif for editorial depth, *Inter* grotesque for clear form UI).
  - Authentic NZZ color palette (deep black, paper off-white, and classic accent red `#a01a1e`).
- **Sign In ("Login")**:
  - Email address or username input with instant validation.
  - Password input with toggleable show/hide eye icon.
  - "Keep me signed in" checkbox.
  - "Forgot password?" modal dialog with simulated reset link request.
  - Alternative sign-in methods: One-time verification code via email, Apple ID, and Google.
- **Create Account ("Register")**:
  - Salutation selector (Mr., Ms., Prefer not to say).
  - First name & Last name in a clean 2-column grid.
  - Email address & optional desired username.
  - **Live Password Strength Meter**: Evaluates length, upper/lower case letters, digits, and special characters with a 4-stage color-coded bar (Weak, Fair, Good, Strong).
  - Password confirmation with instant mismatch detection.
  - Legal consent checkboxes for Terms & Conditions and Privacy Policy.
- **Convenient Testing**:
  - **"Fill Sample Account"** button at the top of the auth card fills realistic demo data into either form with one click.
- **Fully Responsive**:
  - **Desktop**: Elegant split-screen editorial view featuring NZZ values, subscriber benefits, and redaktionsleitbild quote.
  - **Tablet & Mobile**: Seamlessly collapses into a centered, touch-friendly card layout with comfortable 44px+ touch targets.
