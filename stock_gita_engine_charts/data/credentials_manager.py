import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading
import time


class CredentialsManager:
    """
    Manages Twelve Data API keys from credentials.json file.
    Implements key rotation to distribute load across multiple keys.
    """
    
    def __init__(self, credentials_file: str = None):
        """
        Initialize the credentials manager.
        
        Args:
            credentials_file: Path to credentials.json file. 
                             Defaults to credentials.json in the project root.
        """
        if credentials_file is None:
            # Look for credentials.json in multiple locations
            # 1. Project root (stock_gita_deploy)
            project_root = Path(__file__).resolve().parent.parent.parent
            credentials_file = project_root / "credentials.json"
            
            # 2. If not found, try /app/credentials.json (Docker container path)
            if not credentials_file.exists():
                docker_path = Path("/app/credentials.json")
                if docker_path.exists():
                    credentials_file = docker_path
            
            # 3. If still not found, try current working directory
            if not credentials_file.exists():
                cwd_file = Path.cwd() / "credentials.json"
                if cwd_file.exists():
                    credentials_file = cwd_file
        
        self.credentials_file = Path(credentials_file)
        self.credentials: List[Dict] = []
        self.current_index = 0
        self.lock = threading.Lock()
        # Exhaustion tracking
        self.exhausted_keys: Dict[str, datetime] = {}  # key -> exhaustion timestamp
        self.exhaustion_cooldown = timedelta(minutes=1)  # 1 minute cooldown
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from JSON file."""
        try:
            if not self.credentials_file.exists():
                print(f"Warning: credentials.json not found at {self.credentials_file}")
                self.credentials = []
                return
            
            with open(self.credentials_file, 'r') as f:
                self.credentials = json.load(f)
            
            # Validate structure
            if not isinstance(self.credentials, list):
                print("Error: credentials.json must contain a JSON array")
                self.credentials = []
                return
            
            # Validate each credential and initialize missing fields
            valid_credentials = []
            for cred in self.credentials:
                if isinstance(cred, dict) and "key" in cred:
                    # Initialize missing fields with null
                    if "last_used" not in cred:
                        cred["last_used"] = None
                    if "exhausted_at" not in cred:
                        cred["exhausted_at"] = None
                    valid_credentials.append(cred)
                else:
                    print(f"Warning: Invalid credential entry: {cred}")
            
            self.credentials = valid_credentials
            
            # Restore exhausted keys from credentials file
            self.exhausted_keys = {}
            now = datetime.utcnow()
            for cred in self.credentials:
                key = cred["key"]
                exhausted_at_str = cred.get("exhausted_at")
                
                # If exhausted_at is null or empty, key is not exhausted
                if not exhausted_at_str:
                    continue
                
                try:
                    exhausted_at = datetime.fromisoformat(exhausted_at_str.replace('Z', '+00:00'))
                    # Only restore if cooldown hasn't expired
                    if now - exhausted_at < self.exhaustion_cooldown:
                        self.exhausted_keys[key] = exhausted_at
                    else:
                        # Cooldown expired, clear exhaustion
                        cred["exhausted_at"] = None
                        if key in self.exhausted_keys:
                            del self.exhausted_keys[key]
                except Exception:
                    # Invalid format, clear it
                    cred["exhausted_at"] = None
            
            # Save updated credentials (with null values initialized)
            self._save_credentials()
            
            # Sort by last_used (oldest first) for better rotation
            # Treat None as oldest (never used)
            self.credentials.sort(key=lambda x: x.get("last_used") or "1970-01-01T00:00:00")
            
            if len(self.credentials) > 0:
                import sys
                print(f"[Credentials] ========================================")
                sys.stdout.flush()
                print(f"[Credentials] Loaded {len(self.credentials)} API key(s) from {self.credentials_file}")
                sys.stdout.flush()
                print(f"[Credentials] Key rotation enabled - will cycle through all keys")
                sys.stdout.flush()
                # Show key info (masked for security)
                for i, cred in enumerate(self.credentials, 1):
                    key_preview = cred["key"][:8] + "..." + cred["key"][-4:] if len(cred["key"]) > 12 else cred["key"][:8] + "..."
                    last_used = cred.get("last_used")
                    exhausted_at = cred.get("exhausted_at")
                    
                    if exhausted_at:
                        try:
                            exhausted_dt = datetime.fromisoformat(exhausted_at.replace('Z', '+00:00'))
                            now = datetime.utcnow()
                            remaining = self.exhaustion_cooldown - (now - exhausted_dt)
                            if remaining.total_seconds() > 0:
                                remaining_sec = int(remaining.total_seconds())
                                status = f"Exhausted (resets in {remaining_sec}s)"
                            else:
                                status = "Ready (exhaustion expired)"
                        except Exception:
                            status = "Ready"
                    elif last_used:
                        status = f"Last used: {last_used}"
                    else:
                        status = "Ready (never used)"
                    
                    print(f"[Credentials]   Key {i}/{len(self.credentials)}: {key_preview} - {status}")
                    sys.stdout.flush()
                print(f"[Credentials] ========================================")
                sys.stdout.flush()
            
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in credentials.json: {e}")
            self.credentials = []
        except Exception as e:
            print(f"Error loading credentials.json: {e}")
            self.credentials = []
    
    def get_next_key(self) -> Optional[str]:
        """
        Get the next API key using round-robin rotation.
        Updates the last_used timestamp.
        Now uses get_available_key() to skip exhausted keys.
        
        Returns:
            API key string or None if no keys available
        """
        return self.get_available_key()
    
    def get_key_count(self) -> int:
        """Get the number of available API keys."""
        return len(self.credentials)
    
    def mark_key_exhausted(self, key: str):
        """
        Mark a key as exhausted (rate limited).
        Stores exhaustion time in the JSON file.
        
        Args:
            key: The API key that was exhausted
        """
        with self.lock:
            exhausted_at = datetime.utcnow()
            self.exhausted_keys[key] = exhausted_at
            
            # Find the credential and mark it in JSON
            for cred in self.credentials:
                if cred["key"] == key:
                    cred["exhausted_at"] = exhausted_at.isoformat()
                    break
            
            # Save to JSON file immediately
            self._save_credentials()
    
    def is_key_exhausted(self, key: str, lock_held: bool = False) -> bool:
        """
        Check if a key is currently exhausted by reading from JSON file.
        
        Args:
            key: The API key to check
            lock_held: If True, assumes lock is already held (for internal use)
            
        Returns:
            True if key is exhausted and cooldown hasn't expired
        """
        def _check():
            cred = None
            for c in self.credentials:
                if c["key"] == key:
                    cred = c
                    break
            
            if not cred:
                return False
            
            exhausted_at_str = cred.get("exhausted_at")
            if not exhausted_at_str:
                if key in self.exhausted_keys:
                    del self.exhausted_keys[key]
                return False
            
            now = datetime.utcnow()
            try:
                exhausted_at = datetime.fromisoformat(exhausted_at_str.replace('Z', '+00:00'))
            except Exception:
                cred["exhausted_at"] = None
                if key in self.exhausted_keys:
                    del self.exhausted_keys[key]
                self._save_credentials()
                return False
            
            if now - exhausted_at >= self.exhaustion_cooldown:
                cred["exhausted_at"] = None
                if key in self.exhausted_keys:
                    del self.exhausted_keys[key]
                self._save_credentials()
                return False
            
            self.exhausted_keys[key] = exhausted_at
            return True
        
        if lock_held:
            return _check()
        with self.lock:
            return _check()
    
    def are_all_keys_exhausted(self, lock_held: bool = False) -> bool:
        """Check if all keys are currently exhausted."""
        def _check():
            if not self.credentials:
                return True
            
            now = datetime.utcnow()
            available_count = 0
            needs_save = False
            
            for cred in self.credentials:
                key = cred["key"]
                exhausted_at_str = cred.get("exhausted_at")
                if not exhausted_at_str:
                    available_count += 1
                    continue
                try:
                    exhausted_at = datetime.fromisoformat(exhausted_at_str.replace('Z', '+00:00'))
                    if now - exhausted_at >= self.exhaustion_cooldown:
                        cred["exhausted_at"] = None
                        if key in self.exhausted_keys:
                            del self.exhausted_keys[key]
                        available_count += 1
                        needs_save = True
                    else:
                        self.exhausted_keys[key] = exhausted_at
                except Exception:
                    cred["exhausted_at"] = None
                    if key in self.exhausted_keys:
                        del self.exhausted_keys[key]
                    available_count += 1
                    needs_save = True
            
            if needs_save:
                self._save_credentials()
            return available_count == 0
        
        if lock_held:
            return _check()
        with self.lock:
            return _check()
    
    def get_available_key(self) -> Optional[str]:
        """
        Get an available (non-exhausted) key using round-robin rotation.
        
        Returns:
            API key string or None if all keys are exhausted
        """
        with self.lock:
            if not self.credentials:
                return None
            if self.are_all_keys_exhausted(lock_held=True):
                return None
            
            attempts = 0
            while attempts < len(self.credentials):
                cred = self.credentials[self.current_index]
                key = cred["key"]
                if not self.is_key_exhausted(key, lock_held=True):
                    cred["last_used"] = datetime.utcnow().isoformat()
                    self.current_index = (self.current_index + 1) % len(self.credentials)
                    self._save_credentials()
                    return key
                self.current_index = (self.current_index + 1) % len(self.credentials)
                attempts += 1
            return None
    
    def _save_credentials(self):
        """Save credentials back to JSON file."""
        try:
            credentials_to_save = []
            for cred in self.credentials:
                cred_copy = cred.copy()
                if cred_copy.get("last_used") is None:
                    cred_copy["last_used"] = None
                if cred_copy.get("exhausted_at") is None:
                    cred_copy["exhausted_at"] = None
                credentials_to_save.append(cred_copy)
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials_to_save, f, indent=2)
        except Exception as e:
            print(f"[Credentials] Warning: Could not save credentials.json: {e}")
    
    def reload(self):
        """Reload credentials from file."""
        with self.lock:
            self._load_credentials()
            self.current_index = 0


_credentials_manager: Optional[CredentialsManager] = None


def get_credentials_manager() -> CredentialsManager:
    """Get or create the global credentials manager instance."""
    global _credentials_manager
    if _credentials_manager is None:
        _credentials_manager = CredentialsManager()
    return _credentials_manager
