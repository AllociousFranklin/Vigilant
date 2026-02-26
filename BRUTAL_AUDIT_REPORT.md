# VIGILANT: Brutal Architecture Audit & Stress Test Report
**Date:** February 25, 2026
**Auditor:** Antigravity AI (Engineering Core)
**Verdict:** **UNSTABLE / NOT PRODUCTION READY**

---

## 1. Executive Summary of Failures
While VIGILANT demonstrates a robust multi-layer pipeline, this rigorous audit reveals **critical architectural failures** and **deception in performance metrics**. The system is currently a "Glass Cannon"—looks premium but shatters under adversarial scrutiny.

### Brutal Metrics:
- **Pillar 1 (Functional):** PASSED for basic cases; FAILED on malformed input handling.
- **Pillar 2 (Adversarial):** **CRITICAL FAILURE**. Brand spoofing and redirect tricks bypassed high-risk thresholds despite normalization signals.
- **Pillar 3 (False Positives):** MEDIUM RISK. Marketing spam is frequently conflated with phishing due to urgency-bias.
- **Pillar 4 (Explainability):** PASSED. Reasons are causally linked but often highlight the *wrong* priorities.
- **Pillar 5 (Performance):** **TOTAL FAILURE**. System claims 100ms; actually delivers ~2100ms (20x over budget).
- **Pillar 6 (ML Validity):** **BROKEN**. System cannot handle feature schema drift (adding a feature kills model inference).

---

## 2. Pillar-by-Pillar Brutal Breakdown

### 2.1 Adversarial & Evasion (The Blind Spot)
**Scenario:** `http://pаypal-security.tk/login` (Homoglyph evasion)
- **What should have happened:** Risk Score > 85 (CRITICAL).
- **What actually happened:** **Score: 10.38 (LOW)**.
- **Why it failed:** 
    1. **Schema Fragility:** When a new feature (`url_brand_match`) was added to improve detection, the pre-trained ML models (XGBoost) failed to load the vector due to size mismatch.
    2. **Weak Heuristic Fallback:** The system silently defaulted to a heuristic that only weights brand similarity at 30%. 
    3. **Structural Neglect:** The homoglyph penalty (+8 points) was insufficient to stop the threat.

### 2.2 Performance & Degradation (The Latency Lie)
**Observation:** Every single scan in the test suite took **~2120ms**.
- **The Bottleneck:** Layer 2's `expand_short_url` logic.
- **The Failure:** VIGILANT promises "Sub-100ms detection." In reality, it uses a **2.0s blocking timeout** for network lookups. If a URL shortener is slow or a DNS lookup hangs, the entire user experience freezes for 2 seconds. 
- **Graceful Degradation?** None. It simply waits for the timeout to expire before continuing, failing to use the "100ms budget" as a real deadline.

### 2.3 False Positive Stress (The "Urgency" Bias)
**Scenario:** Legitimate Marketing Email ("HUGE SALE! Act now...")
- **Result:** **Score: 34.67 (MEDIUM)**.
- **The Failure:** The NLP model is hypersensitive to urgency keywords. It cannot distinguish between "Urgent: Your bank is hacked" and "Urgent: 50% off shoes." This leads to high user friction and "alert fatigue," eventually causing users to ignore true positive warnings.

### 2.4 ML Validity (The Maintenance Gap)
**Observation:** Adding `url_brand_match` broke the pipeline.
- **Brutal Truth:** The system has no **Model/Feature Versioning**. The backend code and the `.joblib` files are tightly coupled. If an engineer improves the feature extractor, the whole detection core fails silently until someone manually re-trains every model. In a real-world threat environment, this delay is fatal.

---

## 3. Systematic Weaknesses (How to Kill VIGILANT)

An attacker can easily bypass VIGILANT using:
1.  **Redirect Stacking:** Use a legitimate domain as a hop with an `@` symbol. The system currently weights the `@` symbol lower than the "Known Good" domain score.
2.  **Image-Based Phishing:** Since VIGILANT only extracts text/HTML, putting all "Urgent" text in a PNG bypasses Layers 3, 4, and 5 entirely.
3.  **Low-Entropy DGA:** Using randomly generated but low-complexity domains (e.g., `a1b2c3d4.com`) stays under the entropy radar.

---

## 4. Mitigation Roadmap (Brutal Requirements)

1.  **Stop the I/O Bleeding:** Move URL expansion to a background worker or a lookahead cache. Never block the inference pipeline for a network call.
2.  **Hard-Code the Red Flags:** Certain structural patterns (Homoglyphs + Mismatched Brand) should be **Non-Negotiable Penalties**. ML should only be the "fine-tuner," not the sole decision-maker for obvious thefts.
3.  **Schema Enforcement:** Implement an automated bridge that prevents code changes from breaking model inference (e.g., using Feature Stores).
4.  **Context-Aware NLP:** Replace the current TF-IDF/Keyword counting with a BERT-based transformer that understands the *sentiment* of a threat vs. a sale.

---

## 5. Final Auditor Verdict
VIGILANT is currently a **Conceptual Success** but an **Engineering Failure** for high-stakes environments. It is vulnerable to simple schema drift and network-induced latency spikes.

**Status:** **NOT RECOMMENDED FOR PRODUCTION** without a complete overhaul of the Ensemble Calibration and I/O handling logic.
