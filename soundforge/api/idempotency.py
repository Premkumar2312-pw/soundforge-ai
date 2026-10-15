"""
Idempotency Manager for SoundForge AI
Guarantees safe request deduplication based on client Idempotency-Key.
"""

import hashlib
import json
import threading
from typing import Dict, Any, Optional

class IdempotencyRecord:
    def __init__(self, key: str, payload_hash: str, response_payload: Dict[str, Any]):
        self.key = key
        self.payload_hash = payload_hash
        self.response_payload = response_payload

class IdempotencyManager:
    def __init__(self):
        self._store: Dict[str, IdempotencyRecord] = {}
        self._lock = threading.Lock()

    def compute_payload_hash(self, payload_dict: Dict[str, Any]) -> str:
        # Canonical JSON string serialization
        canonical_str = json.dumps(payload_dict, sort_keys=True, default=str)
        return hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

    def get(self, key: str) -> Optional[IdempotencyRecord]:
        with self._lock:
            return self._store.get(key)

    def register(self, key: str, payload_hash: str, response_payload: Dict[str, Any]):
        with self._lock:
            self._store[key] = IdempotencyRecord(key, payload_hash, response_payload)

idempotency_manager = IdempotencyManager()
