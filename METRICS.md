# 📈 SENTINEL Evaluation & Metrics Methodology

In **Razorpay Buildathon Track 02: AI Risk Manager**, the criteria explicitly demand:
> *"Measured precision and recall on a held-out test set. Honest metrics including false-positive cost."*

This document outlines exactly how SENTINEL calculates its metrics, proves its economic value, and stress-tests itself against high-difficulty adversarial evasion.

---

## 1. The Dataset (`n=10,000`)

SENTINEL's training and evaluation are built on a synthetic 10,000-row dataset modeling Indian BFSI transaction patterns (UPI, Rupay, NetBanking, Intl Cards).

**Total Split:**
* **Legitimate Transactions (0)**: 5,000
* **Fraudulent Transactions (1)**: 5,000

**Fraud Topology:**
* `fraud_card_testing`: 1,200
* `fraud_velocity_spike`: 1,100
* `fraud_abuse_ring`: 1,000
* `fraud_chargeback_abuser`: 900 *(Chargeback label = 1)*
* `fraud_billing_mismatch`: 800 *(Chargeback label = 1)*

**Legitimate Topology:**
* `legit_regular_customer`: 1,700
* `legit_low_value_routine`: 1,400
* `legit_verified_repeat`: 1,300
* `legit_high_value_train`: 500 *(High ticket, high trust)*
* `legit_high_value` (Kill-Switch Holdout): 100

---

## 2. Train / Test Isolation (Data Leakage Prevention)

To ensure **Honest Metrics**, SENTINEL strictly adheres to test-set isolation:
1. `train_test_split` is applied with a 20% test size, yielding exactly **1,980** transactions for the evaluation holdout.
2. We utilize `cross_val_score(cv=5)` strictly on `X_train` and `y_train` during model compilation.
3. The model is then evaluated against `X_test` (the 1,980 unseen transactions).

---

## 3. The "Kill-Switch" Guardrail

A common trap in Fraud ML is blocking high-value legitimate customers because "high amount = anomaly." 

SENTINEL enforces an **Out-of-Sample Kill Switch**:
1. We carved out 100 `legit_high_value` transactions (amounts up to ₹5,00,000).
2. We **permanently deleted** these 100 rows from the training data pool (`df_trainable = df[df['source'] != 'legit_high_value']`).
3. After the model finishes training on the 1,980 test set, it is forced to evaluate the 100 Kill-Switch transactions.
4. **The Guardrail**: If the model blocks > 1.0% of these transactions, the training script throws an `Exception` and refuses to save the model. 

*Result: SENTINEL achieves a **0.00% False Positive Rate** on the Kill-Switch corpus.*

---

## 4. False-Positive Cost Calculation (Economic Impact)

Razorpay requires "Honest metrics including false-positive cost". We calculate this live via the `/api/metrics` endpoint.

**The Math:**
1. **Average Ticket Size**: We baseline the average Indian merchant transaction at **₹4,500**.
2. **False Positives (FP)**: The number of legitimate transactions in the held-out set that the model incorrectly classified as FRAUD.
3. **FP Cost (INR)** = `FP_Count * Average_Ticket_Size`

Because SENTINEL achieved **100% Precision (0 False Positives)** on the held-out test set, the resulting merchant capital lost to false declines is **₹0.00**.

---

## 5. Dual Model Targets

To fulfill the "Chargebacks & Returns" criteria, SENTINEL does not just predict generic fraud.
* **XGBoost (Target: `label`)**: Predicts outright binary fraud (Velocity, Rings, Testing).
* **Random Forest (Target: `chargeback_label`)**: Predicts the likelihood of a transaction resulting in a friendly fraud chargeback dispute, allowing merchants to selectively demand 3DS or OTP for risky customers without blocking them entirely.

---

## 6. ⚔️ The Brutal Adversarial & Real-World Stress Benchmark

While canonical held-out datasets test distribution matching, **real-world production fraud detection requires adversarial stress testing**. In reality, 100% accuracy claims are often artifacts of clean distributions. 

To prove genuine engineering depth, SENTINEL includes an autonomous **Brutal Adversarial Benchmark Suite** (`backend/tests/test_brutal_real_world.py`) testing **15 complex edge cases** across 4 high-difficulty categories.

### Test Categories

| Category | Attack Vector / Real-Life Scenario | Expected |
| :--- | :--- | :--- |
| **Adversarial Evasion** | **ADV-01**: Micro-Testing at ₹149 (evading `<₹100` rule) & 4 txns/hr (evading `≥5` rule) | BLOCK |
| **Adversarial Evasion** | **ADV-02**: Prime-Time ATO (8:30 PM) on clean residential IP (evading late-night rule) | BLOCK |
| **Adversarial Evasion** | **ADV-03**: Strategic Chargebacker keeping dispute rate at 28% (evading `≥35%` rule) | BLOCK |
| **Adversarial Evasion** | **ADV-04**: Decentralized Botnet (1 txn/device/node, disposable domain) | BLOCK |
| **Adversarial Evasion** | **ADV-05**: Synthetic Business Persona with day-old account & corporate domain | REVIEW/BLOCK |
| **Legitimate Stress** | **LEGIT-01**: 3:15 AM Emergency Hospital ICU deposit (₹75,000 via UPI on daughter's phone) | ALLOW |
| **Legitimate Stress** | **LEGIT-02**: Diwali Midnight Flash Sale (₹79,900 iPhone purchase at 12:05 AM on new iPad) | ALLOW |
| **Legitimate Stress** | **LEGIT-03**: NRI Expat in US gifting ₹55,000 jewelry to parents in Bangalore | ALLOW |
| **Legitimate Stress** | **LEGIT-04**: Akshaya Tritiya Wedding Gold (₹3,50,000 UPI on 5-year trusted customer) | ALLOW |
| **Legitimate Stress** | **LEGIT-05**: College student exam night quick-commerce burst (3 Swiggy/Zepto orders/hr) | ALLOW |
| **Legitimate Stress** | **LEGIT-06**: Senior citizen first-time purchase (retiree buying insulin, unverified phone) | ALLOW |
| **Return & Chargeback** | **CB-01**: Serial Wardrobing returner on luxury fashion (high return history) | BLOCK |
| **Return & Chargeback** | **CB-02**: First-time "Package Empty" GPU fraud (₹68,000 on new gamer account) | BLOCK |
| **Data Chaos** | **CHAOS-01**: Zero-metadata webhook arrival (missing device, IP, and profile telemetry) | ALLOW |
| **Data Chaos** | **CHAOS-02**: ₹1.00 Penny Drop bank mandate verification | ALLOW |

### The Honest Failure Analysis & Trust Multipliers

When tested against uncalibrated binary rule floors, the system initially suffered **2 critical false declines** (dropping brutal precision to **77.78%**):
1. **The 3 AM Hospital ICU Deposit** was blocked because `RULE_ATO_PATTERN` blindly flagged any transaction where `new_device=1 + amount>50k + late_night=1`.
2. **The NRI Expat Gifting Parents** was blocked because `RULE_GEO_MISMATCH` blindly blocked `US billing + IN shipping + amount>50k`.

#### The Architectural Solution: Customer Trust Multipliers
To resolve this tension without weakening fraud defense, SENTINEL introduces **Dynamic Trust Calibration** in `detector.py`:
```python
is_high_trust = (
    features.get('customer_account_age_log', 0) >= 4.5 and  # Account age > 90 days
    features.get('customer_total_txns_log', 0) >= 2.3 and   # Clean txns > 10
    features.get('customer_dispute_rate', 0) <= 0.02 and    # Pristine dispute record
    features.get('phone_verified', 0) == 1.0 and           # Verified phone
    features.get('ip_risk_score', 1.0) <= 0.25             # Clean ISP connection
)
```
When `is_high_trust` is verified and network risk is clean (`ip_risk ≤ 0.30`):
- Emergency hospital payments and midnight flash sales by verified customers **bypass blind ATO blocking** while actual proxy-driven attackers (`ip_risk ≥ 0.70`) remain strictly blocked.
- Legitimate NRI expat family gifting **bypasses blind Geo-Mismatch blocking** while spoofed proxy carding remains strictly blocked.

### Benchmark Execution Command
```bash
cd backend
python tests/test_brutal_real_world.py
```
