import hashlib
import hmac
import base64
import json
import time
import secrets
from typing import Dict, Any, Optional

SECRET_KEY = "pepr_pide_secret_jwt_key_2026_secure"
ALGORITHM = "HS256"
TOKEN_EXPIRE_SECONDS = 86400 * 7 # 7 days
RESET_CODE_EXPIRE_SECONDS = 900  # 15 minutes

def hash_password(password: str) -> str:
    """Hashes a password with salt using SHA-256."""
    salt = "pide_pepr_salt_"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against hashed password."""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
    """Creates a simple, secure HMAC-signed JWT token string."""
    payload = data.copy()
    now = int(time.time())
    expire = now + (expires_delta or TOKEN_EXPIRE_SECONDS)
    payload.update({"iat": now, "exp": expire})
    
    header = {"alg": "HS256", "typ": "JWT"}
    
    encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    signature_input = f"{encoded_header}.{encoded_payload}".encode()
    signature = hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates HMAC-signed JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
            
        encoded_header, encoded_payload, encoded_signature = parts
        
        # Verify signature
        signature_input = f"{encoded_header}.{encoded_payload}".encode()
        expected_sig = hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest()
        encoded_expected_sig = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
        
        if not hmac.compare_digest(encoded_signature, encoded_expected_sig):
            return None
            
        # Decode payload
        rem = len(encoded_payload) % 4
        padded_payload = encoded_payload + ("=" * (4 - rem) if rem else "")
        payload_bytes = base64.urlsafe_b64decode(padded_payload)
        payload = json.loads(payload_bytes.decode())
        
        # Check expiration
        if payload.get("exp") and time.time() > payload["exp"]:
            return None
            
        return payload
    except Exception:
        return None

def generate_reset_token(email: str) -> str:
    """Generates a password reset JWT token for an email address (used internally)."""
    return create_access_token({"sub": email, "type": "reset"}, expires_delta=RESET_CODE_EXPIRE_SECONDS)

def verify_reset_token(token: str) -> Optional[str]:
    """Verifies a password reset token and returns the email."""
    payload = decode_access_token(token)
    if payload and payload.get("type") == "reset":
        return payload.get("sub")
    return None

# ── 6-digit numeric reset code (emailed to researcher) ────────────────────────

def generate_reset_code(email: str) -> tuple[str, str]:
    """
    Generates a 6-digit numeric verification code AND a signed JWT token.
    Returns (code, token) — code is emailed; token is stored/returned for the
    reset-password endpoint to validate.
    """
    # Derive a deterministic 6-digit code from HMAC(email + timestamp bucket)
    # Bucket = 15-min window so the same call within 15 min yields same code
    bucket = int(time.time() // RESET_CODE_EXPIRE_SECONDS)
    raw = hmac.new(
        SECRET_KEY.encode(),
        f"{email}:{bucket}".encode(),
        hashlib.sha256
    ).digest()
    # Take last 3 bytes as int, mod 1_000_000, zero-pad to 6 digits
    code = str(int.from_bytes(raw[-3:], 'big') % 1_000_000).zfill(6)
    token = create_access_token({"sub": email, "type": "reset", "code": code}, expires_delta=RESET_CODE_EXPIRE_SECONDS)
    return code, token

def verify_reset_code(token: str, code: str) -> Optional[str]:
    """
    Verifies a reset token AND the 6-digit code the user typed.
    Returns the email on success, None on failure.
    """
    payload = decode_access_token(token)
    if not payload or payload.get("type") != "reset":
        return None
    if payload.get("code") != code.strip():
        return None
    return payload.get("sub")
