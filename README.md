# 🛡️ VIGILANT - Getting Started Guide

VIGILANT is now ready. Follow these steps to run the complete system.

## 1. Start the Backend API
The backend handles the AI inference and de-obfuscation logic.
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Wait for the log: `[✓] VIGILANT is ready for threat detection`*

## 2. Launch the Dashboard
The dashboard provides live analysis and security analytics.
```bash
cd frontend
npm run dev
```
*Open http://localhost:5173 to access the dashboard.*

## 3. Load the Chrome Extension
To protect your browser in real-time:
1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer Mode** (toggle in the top right).
3. Click **Load unpacked**.
4. Select the `extension/` folder in this project directory.
5. **Note:** Navigate to a test page (e.g., `http://paypa1-update.tk`) to see the AI auto-block it.

## 4. Testing the System
- **URL Scanning:** Paste `http://paypa1-secure-login.bit.ly/update` in the Dashboard Scanner.
- **Email Analysis:** Paste: *"Urgent: Your account is suspended. Click here to verify your password immediately or your access will be permanently lost."*
- **SMS Analysis:** Paste: *"Amazon: Unusual activity detected. Tap here to confirm your delivery address: http://amzon-track.tk"*

## System Architecture
- **Layer 1-2:** Ingestion & Normalization (De-obfuscates Punycode, Homoglyphs, Short URLs)
- **Layer 3:** Feature Extraction (25-dimension vector replaces static blacklists)
- **Layer 4:** Ensemble ML (XGBoost + Random Forest weighted scoring)
- **Layer 5:** Explainability (Reason mapping for security teams)
- **Layer 6:** Real-time Blocking (Chrome Extension integration)
