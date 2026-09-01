# 🏗️ SENTINEL System Architecture

This document provides a technical deep-dive into the design, infrastructure, and flow of the SENTINEL AI Risk Manager.

## 1. High-Level System Design

SENTINEL is composed of two heavily decoupled components:
1. **Python / FastAPI Backend Engine**: A high-performance inference engine capable of sub-15ms risk evaluation, backed by SQLite for telemetry, XGBoost/Random Forest for ML, and Pydantic for strict schema validation.
2. **React / Vite Frontend**: A modern, responsive dashboard for merchants to visualize risk, view metrics, and simulate attacks.

## 2. The 6-Layer Inference Pipeline

The core of SENTINEL is its synchronous, 6-step pipeline (`app.engine.pipeline.score_transaction`). Every transaction must pass through these layers:

### Layer 1: Ingestion & Validation
* **Component**: `app/engine/ingestion.py`
* **Role**: Parses the incoming JSON payload via FastAPI + Pydantic.
* **Mechanics**: Computes a SHA-256 deduplication hash based on `merchant_id`, `amount`, `payment_method`, and `timestamp`. Standardizes all missing telemetry (IPs, device fingerprints) into safe defaults.

### Layer 2: Behavioral Enrichment
* **Component**: `app/engine/transaction_enricher.py`
* **Role**: Hydrates the raw transaction with contextual profile data.
* **Mechanics**: Simulates real-time feature stores by calculating velocity (e.g., how many transactions has this IP made in 1 hour?) and historical reputation (customer account age, merchant risk category). 

### Layer 3: Feature Extraction (The 30-Dim Vector)
* **Component**: `app/engine/features.py`
* **Role**: Translates enriched data into a normalized, strictly ordered 30-element float array `[1.0, 0.0, 0.45, ...]`.
* **Mechanics**: Implements a strict `schema_hash` (`b634231e7d0f`). If the training pipeline and the inference pipeline ever drift in feature count or order, the system hard-crashes to prevent silent ML degradation.

### Layer 4: Ensemble ML Core
* **Component**: `app/engine/detector.py`
* **Role**: Dual-model statistical risk assessment.
* **Mechanics**: 
  * **Fraud Model**: `XGBoost`. Extremely sensitive to non-linear relationships (e.g., High Amount + New Device + Late Night). Outputs `fraud_score` (0-100).
  * **Chargeback Model**: `Random Forest`. Trained strictly on `chargeback_label`. Identifies "Friendly Fraud" signatures (e.g., established accounts doing chronic disputes). Outputs `chargeback_score` (0-100).

### Layer 5: Deterministic Policy Floors
* **Component**: `app/engine/policy.py`
* **Role**: The "Safety Net". Machine Learning can be bypassed by novel adversarial inputs. Hardcoded rules cannot.
* **Mechanics**: If ML says a transaction is 5% risky, but the transaction violates `RULE_VELOCITY_SPIKE` (>5 txns/hr), the policy engine *overrides* the score to 82.0 and forces a BLOCK. 

### Layer 6: Explainer & Dossier Builder
* **Component**: `app/engine/explainer.py`
* **Role**: Explainability and Legal Auto-Response.
* **Mechanics**: Takes the triggering policy rules, the top SHAP-equivalent feature drivers, and the transaction context to compile a human-readable string: The **Chargeback Evidence Dossier**. This is immediately ready for bank representment.

## 3. Data Schema & Persistence

* **Database**: `SQLite3` (Synchronous, file-based).
* **Location**: `backend/vigilant.db` (Auto-generated).
* **Tables**:
  1. `assessments`: Stores the full transaction payload, risk scores, and the generated chargeback evidence.
  2. `outcomes`: Stores merchant feedback (e.g., "chargeback_lost", "fraud_confirmed"). This creates a closed-loop system for continuous retraining.
  3. `shadow_telemetry`: Stores divergence logs.

## 4. Shadow Mode (Canary ML Deployment)
* **Component**: `app/engine/shadow.py`
* **Role**: Zero-risk model updates.
* **Mechanics**: When a new model version is deployed, SENTINEL can run it in "Shadow Mode". The system compares the new model's output to the old model's output. If they diverge (e.g., Old says ALLOW, New says BLOCK), the delta is logged to the `shadow_telemetry` table without affecting the actual merchant decision.

## 5. Security Model (Strictly Defense-Only)
SENTINEL has zero offensive capabilities. It does not:
* Scan external IP addresses or ports.
* Send outbound webhooks or side-channel requests (except for basic UI telemetry).
* Mutate merchant databases.

It only accepts inbound JSON, performs local mathematical transformations, and returns a JSON recommendation. It is 100% compliant with Razorpay Track 02 constraints.
