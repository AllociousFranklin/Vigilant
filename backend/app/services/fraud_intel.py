"""SENTINEL - Fraud Intelligence Service

Maintains real-time BFSI threat intelligence feeds:
- Stolen / Test Card BIN blacklist
- Known Device Fingerprint fraud syndicates
- High-risk IP proxy ranges
"""
import re
from typing import Set

# Known card testing / compromised test BINs (Visa, Mastercard, Amex test ranges)
KNOWN_FRAUD_BINS: Set[str] = {
    '411111', '400000', '424242', '555555', '510510',
    '378282', '371449', '601100', '352800', '491277'
}

# Known syndicate device fingerprints (hashes of fraudulent Android emulators / spoofed user agents)
KNOWN_FRAUD_DEVICES: Set[str] = {
    'dev_syndicate_alpha_01', 'dev_emulator_nox_991', 'dev_spoof_android_v8',
    'dev_botnet_cluster_44b', 'dev_compromised_pos_31', 'abuse_ring_hash_77a'
}


def check_card_bin(card_bin: str) -> bool:
    """Check if first 6 digits of card match known compromised / test BINs."""
    if not card_bin:
        return False
    clean_bin = re.sub(r'\D', '', str(card_bin))[:6]
    return clean_bin in KNOWN_FRAUD_BINS


def check_device(device_fingerprint: str) -> bool:
    """Check if device hardware fingerprint matches known fraud rings."""
    if not device_fingerprint:
        return False
    dev_str = str(device_fingerprint).strip().lower()
    return dev_str in KNOWN_FRAUD_DEVICES or any(bad in dev_str for bad in ['syndicate', 'emulator_nox', 'botnet_cluster'])
