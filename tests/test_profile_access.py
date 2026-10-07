import hashlib

from app.api.profile import create_profile
from app.api.deps import get_profile_id
from app.models import Profile
from app.schemas import ProfileCreateRequest


def test_created_profile_returns_opaque_access_token(db_session):
    result = create_profile(ProfileCreateRequest(display_name="Alice"), db_session)
    assert result.access_token
    profile = db_session.get(Profile, result.id)
    assert profile is not None
    assert profile.access_token_hash == hashlib.sha256(result.access_token.encode()).hexdigest()
    assert result.access_token != profile.access_token_hash
    assert get_profile_id(x_profile_token=result.access_token, authorization=None, x_profile_id=None).startswith("token:")


def test_bearer_token_is_accepted_and_profile_id_header_is_not_accepted_when_legacy_mode_is_disabled():
    from unittest.mock import patch
    with patch("app.api.deps.get_settings") as get_settings:
        get_settings.return_value.demo_mode = False
        get_settings.return_value.allow_legacy_profile_id = False
        try:
            get_profile_id(x_profile_token=None, authorization=None, x_profile_id="someone")
        except Exception as exc:
            assert getattr(exc, "status_code", None) == 401
        else:
            raise AssertionError("legacy profile id must not be accepted")


def test_bearer_token_is_normalized():
    with __import__('unittest').mock.patch("app.api.deps.get_settings") as get_settings:
        get_settings.return_value.demo_mode = False
        get_settings.return_value.allow_legacy_profile_id = False
        value = get_profile_id(x_profile_token=None, authorization="Bearer abc123", x_profile_id=None)
        assert value.startswith("token:")
