import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Account, AuthSession, Profile

PASSWORD_SCHEME = "pbkdf2_sha256"
DEFAULT_PASSWORD_ITERATIONS = 600_000


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def validate_email(email: str) -> str:
    value = normalize_email(email)
    local, sep, domain = value.partition("@")
    if not sep or not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("Enter a valid email address.")
    return value


def hash_password(password: str, *, iterations: int | None = None) -> str:
    settings = get_settings()
    rounds = iterations or getattr(settings, "password_hash_iterations", DEFAULT_PASSWORD_ITERATIONS)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    enc = base64.urlsafe_b64encode
    return f"{PASSWORD_SCHEME}${rounds}${enc(salt).decode()}${enc(digest).decode()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, rounds_s, salt_s, digest_s = encoded.split("$", 3)
        if scheme != PASSWORD_SCHEME:
            return False
        rounds = int(rounds_s)
        salt = base64.urlsafe_b64decode(salt_s.encode())
        expected = base64.urlsafe_b64decode(digest_s.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_session(db: Session, account: Account, profile: Profile) -> str:
    settings = get_settings()
    token = secrets.token_urlsafe(48)
    now = utcnow()
    lifetime = max(1, int(getattr(settings, "auth_session_days", 30)))
    db.add(
        AuthSession(
            id=secrets.token_hex(16),
            account_id=account.id,
            profile_id=profile.id,
            token_hash=hash_session_token(token),
            created_at=now,
            last_seen_at=now,
            expires_at=now + timedelta(days=lifetime),
        )
    )
    return token


def find_account_by_email(db: Session, email: str) -> Account | None:
    return db.scalar(select(Account).where(Account.email == normalize_email(email)))


def find_active_session(db: Session, token: str) -> AuthSession | None:
    now = utcnow()
    session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == hash_session_token(token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
    )
    if session:
        session.last_seen_at = now
    return session
