import os
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class AllKeysExhaustedException(Exception):
    """Raised when all API keys are exhausted"""
    pass

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
DB_PATH = os.path.join(CACHE_DIR, "gs_data.db")
KEYS_FILE = os.path.join(BASE_DIR, "credentials.json")

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

def loadApiKeys():
    """Load API keys from credentials.json"""
    if not os.path.exists(KEYS_FILE):
        return []
    try:
        with open(KEYS_FILE, 'r') as f:
            keysData = json.load(f)
            return keysData if isinstance(keysData, list) else []
    except Exception as e:
        print(f"Warning: Could not load API keys: {e}")
        return []

def saveApiKeys(keysData):
    """Save API keys back to credentials.json"""
    try:
        with open(KEYS_FILE, 'w') as f:
            json.dump(keysData, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save API keys: {e}")

def getLeastRecentlyUsedKey(keysData):
    """Get the key that was used least recently (or never used)"""
    if not keysData:
        return None
    
    def getLastUsed(keyEntry):
        lastUsed = keyEntry.get('last_used')
        if lastUsed is None:
            return datetime.min
        try:
            return datetime.fromisoformat(lastUsed)
        except:
            return datetime.min
    
    sortedKeys = sorted(keysData, key=getLastUsed)
    return sortedKeys[0] if sortedKeys else None

def updateKeyLastUsed(keysData, keyValue):
    """Update the last_used timestamp for a key"""
    now = datetime.now().isoformat()
    for keyEntry in keysData:
        if keyEntry.get('key') == keyValue:
            keyEntry['last_used'] = now
            return True
    return False

class KeyManager:
    def __init__(self):
        self.keysData = loadApiKeys()
        self.apiKeys = [entry.get('key') for entry in self.keysData if entry.get('key')]
        self.rateLimitedKeys = {}
        self.currentKeyIndex = 0
        self.cooldownMinutes = 2
        self.keysFileLock = False
        self.lastSavedKey = None
        self.saveCounter = 0
        
    def _saveKeysIfNeeded(self, keyValue):
        """Save keys to file, but not on every single usage to reduce I/O"""
        self.lastSavedKey = keyValue
        self.saveCounter += 1
        
        if self.saveCounter >= 10:
            if not self.keysFileLock:
                self.keysFileLock = True
                try:
                    saveApiKeys(self.keysData)
                    self.saveCounter = 0
                finally:
                    self.keysFileLock = False
        
    def saveKeys(self):
        """Force save keys to file"""
        if not self.keysFileLock:
            self.keysFileLock = True
            try:
                saveApiKeys(self.keysData)
                self.saveCounter = 0
            finally:
                self.keysFileLock = False
        
    def getAvailableKey(self):
        if not self.apiKeys:
            raise AllKeysExhaustedException("No API keys available")
        
        keyEntry = getLeastRecentlyUsedKey(self.keysData)
        if not keyEntry:
            raise AllKeysExhaustedException("No API keys available")
        
        keyValue = keyEntry.get('key')
        
        if self._isKeyAvailable(keyValue):
            updateKeyLastUsed(self.keysData, keyValue)
            self._saveKeysIfNeeded(keyValue)
            return keyValue
        
        for keyEntry in self.keysData:
            keyValue = keyEntry.get('key')
            if self._isKeyAvailable(keyValue):
                updateKeyLastUsed(self.keysData, keyValue)
                self._saveKeysIfNeeded(keyValue)
                return keyValue
        
        if len(self.rateLimitedKeys) >= len(self.apiKeys):
            self.saveKeys()
            raise AllKeysExhaustedException("All API keys exhausted. Please wait for cooldown period or add more keys.")
        
        return None
    
    def _isKeyAvailable(self, key):
        if key not in self.rateLimitedKeys:
            return True
        cooldownUntil = self.rateLimitedKeys[key]
        if datetime.now() >= cooldownUntil:
            self.rateLimitedKeys.pop(key, None)
            return True
        return False
    
    def markRateLimited(self, key):
        """Mark a key as rate-limited and update its timestamp"""
        cooldownUntil = datetime.now() + timedelta(minutes=self.cooldownMinutes)
        self.rateLimitedKeys[key] = cooldownUntil
        updateKeyLastUsed(self.keysData, key)
        self._saveKeysIfNeeded(key)
    
    def getAvailableCount(self):
        return sum(1 for key in self.apiKeys if self._isKeyAvailable(key))
