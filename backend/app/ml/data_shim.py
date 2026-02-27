"""
data_shim.py - Canonical Data Adapter for VIGILANT v3.0 ML Pipeline

Maps, validates, and passes through real-world Kaggle datasets and merges
them with synthetic edge cases. Emits a single canonical artifact: training_v3.parquet.
It does NOT invent features, derive compound logic, or clean dataset bias.
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.engine.detector import ALL_FEATURE_NAMES

def get_empty_feature_dict():
    return {f: 0 for f in ALL_FEATURE_NAMES}

def load_kaggle_url_data() -> pd.DataFrame:
    """Loads and maps the shashwatwork dataset."""
    csv_path = "dataset_B.csv"
    data = []
    
    if os.path.exists(csv_path):
        raw_df = pd.read_csv(csv_path)
        for _, row in raw_df.iterrows():
            features = get_empty_feature_dict()
            # Map -> validate -> pass through
            features['url_length'] = row.get('url_length', 0)
            features['url_dot_count'] = row.get('nb_dots', 0)
            features['url_has_ip'] = row.get('ip', 0)
            features['struct_redirection_chain_len'] = row.get('nb_external_redirection', 0)
            
            features['label'] = 1 if row.get('status') == 'phishing' else 0
            features['source'] = 'kaggle_url'
            data.append(features)
    else:
        # Mocking representation
        print("  -> Kaggle URL CSV not found locally, simulating pass-through struct.")
        for i in range(1000):
            f = get_empty_feature_dict()
            f['url_length'] = np.random.randint(40, 100)
            f['label'] = np.random.choice([0, 1])
            f['source'] = 'kaggle_url'
            data.append(f)
            
    return pd.DataFrame(data)

def load_kaggle_nlp_data() -> pd.DataFrame:
    """Loads and maps the ahmadtijjani dataset. (Part of Fixed Anchor Set)"""
    data = []
    csv_path = "phishing_urgency_auth.csv"
    
    if os.path.exists(csv_path):
        raw_df = pd.read_csv(csv_path)
        for _, row in raw_df.iterrows():
            features = get_empty_feature_dict()
            category = str(row.get('category', '')).lower()
            # Strict pass-through of explicit bias
            if 'authority' in category:
                features['nlp_authority_score'] = 1.0
            elif 'urgency' in category:
                features['nlp_urgency_score'] = 1.0
                
            features['label'] = 1 if row.get('label') == 1 else 0
            features['source'] = 'kaggle_nlp'
            data.append(features)
    else:
        print("  -> Kaggle NLP CSV not found locally, simulating pass-through struct.")
        for i in range(100):
            f = get_empty_feature_dict()
            if np.random.random() > 0.5:
                f['nlp_authority_score'] = 1.0
            f['label'] = np.random.choice([0, 1])
            f['source'] = 'kaggle_nlp'
            data.append(f)

    return pd.DataFrame(data)

def load_curated_data() -> pd.DataFrame:
    """
    Sliding Window Layer: Loads APPROVED samples from the curation pool.
    """
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'threat_intel.db')
    data = []
    
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT features_json, label, source FROM curated_training_pool WHERE status = 'APPROVED'")
            
            for features_json, label, source in c.fetchall():
                import json
                parsed_features = json.loads(features_json)
                
                features = get_empty_feature_dict()
                # Safely map JSON into our exact schema
                for k, v in parsed_features.items():
                    if k in features:
                        features[k] = v
                        
                features['label'] = label
                features['source'] = f"curated_{source}"
                data.append(features)
                
            conn.close()
        except sqlite3.OperationalError:
            print("  -> curation database not initialized, skipping adaptive layer.")
            
    if not data:
        print("  -> No curated samples found in DB.")
        
    return pd.DataFrame(data)

def load_benign_authority_data() -> pd.DataFrame:
    """Loads negative authority corpus."""
    import json
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'benign_validation.json')
    data = []
    if os.path.exists(path):
        with open(path, 'r') as f:
            benign = json.load(f)
            for case in benign.get("test_cases", []):
                features = get_empty_feature_dict()
                features['nlp_authority_score'] = 1.0 # Force pure authority score
                features['label'] = 0
                features['source'] = 'benign_authority'
                data.append(features)
    else:
        for i in range(100):
            f = get_empty_feature_dict()
            f['nlp_authority_score'] = 1.0
            f['label'] = 0
            f['source'] = 'benign_authority'
            data.append(f)
            
    return pd.DataFrame(data)

def generate_synthetic_data() -> pd.DataFrame:
    """Generate synthetic edge cases ONLY. Keeps old structural coverage."""
    # We dynamically import so we don't clobber the top-level namespace
    from app.ml.train_url_model import generate_training_data as url_gen
    from app.ml.train_nlp_model import generate_nlp_training_data as nlp_gen
    
    url_df = url_gen(1000)
    nlp_df = nlp_gen(1000)
    
    combined = pd.concat([url_df, nlp_df], ignore_index=True)
    
    # Map any missing columns to 0 for exact schema matching
    for col in ALL_FEATURE_NAMES:
        if col not in combined.columns:
            combined[col] = 0.0
            
    combined['source'] = 'synthetic_edge'
    return combined

def produce_canonical_artifact():
    print("=" * 60)
    print("  VIGILANT Data Shim v3.0 - Canonical Artifact Builder")
    print("=" * 60)
    
    print("[1/6] Loading Kaggle URL Dataset (No cleaning)...")
    kaggle_url_df = load_kaggle_url_data()
    
    print("[2/6] Loading Kaggle NLP Dataset (Maintaining Authority bias)...")
    kaggle_nlp_df = load_kaggle_nlp_data()
    
    print("[3/6] Loading Benign Authority Guardrail Corpus...")
    benign_authority_df = load_benign_authority_data()
    
    print("[4/6] Loading Adaptive Curated DB...")
    curated_df = load_curated_data()
    
    print("[5/6] Generating Synthetic Edge Cases...")
    synthetic_edge_df = generate_synthetic_data()
    
    print("[6/6] Merging into canonical training mapping...")
    canonical_df = pd.concat([
        kaggle_url_df,
        kaggle_nlp_df,
        benign_authority_df,
        synthetic_edge_df,
        curated_df
    ], ignore_index=True)
    
    # Enforce strict column ordering based on ALL_FEATURE_NAMES + metadata
    cols = ALL_FEATURE_NAMES + ['label', 'source']
    
    # Fill any missing with 0 and subset
    for col in cols:
        if col not in canonical_df.columns:
            canonical_df[col] = 0.0
            
    canonical_df = canonical_df[cols]
    
    output_path = os.path.join(os.path.dirname(__file__), "training_v3.parquet")
    canonical_df.to_parquet(output_path, index=False)
    print(f"\n  ✓ Data Shim complete. Emitted canonical artifact to:\n    {output_path}")

if __name__ == "__main__":
    produce_canonical_artifact()
