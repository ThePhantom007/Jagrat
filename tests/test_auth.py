from datetime import datetime, timezone

from app.api.auth import claim_anonymous_profile, login, me, signup
from app.api.deps import get_profile_id
from app.api.profile import create_profile
from app.models import Account, AuthSession, JournalEntry, Profile
from app.schemas import ClaimProfileRequest, LoginRequest, ProfileCreateRequest, SignupRequest
from app.services.auth import find_active_session


def test_signup_creates_account_profile_and_session(db_session):
    result = signup(SignupRequest(email="Alice@Example.com", password="strongpass123", display_name="Alice"), db_session)
    assert result.access_token
    assert result.profile.email == "alice@example.com"
    profile = db_session.get(Profile, result.profile.id)
    account = db_session.query(Account).filter(Account.profile_id == profile.id).first()
    session = db_session.query(AuthSession).filter(AuthSession.account_id == account.id).first()
    assert profile is not None
    assert account is not None
    assert account.password_hash != "strongpass123"
    assert session is not None


def test_login_and_me_report_persisted_profile_storage(db_session):
    created = signup(SignupRequest(email="a@example.com", password="strongpass123", display_name="A"), db_session)
    profile = db_session.get(Profile, created.profile.id)
    db_session.add(JournalEntry(profile_id=profile.id, text="A saved diary entry"))
    db_session.commit()

    logged_in = login(LoginRequest(email="A@EXAMPLE.COM", password="strongpass123"), db_session)
    assert logged_in.account_id == created.account_id
    assert find_active_session(db_session, logged_in.access_token) is not None
    me_result = me(authorization=f"Bearer {logged_in.access_token}", x_profile_token=None, db=db_session)
    assert me_result.profile.id == profile.id
    assert me_result.storage["journal_entries"] == 1


def test_anonymous_profile_can_be_claimed_without_losing_diary(db_session):
    anonymous = create_profile(ProfileCreateRequest(display_name="Anonymous"), db_session)
    profile = db_session.get(Profile, anonymous.id)
    db_session.add(JournalEntry(profile_id=profile.id, text="Keep this diary"))
    db_session.commit()

    token_hash_key = get_profile_id(x_profile_token=anonymous.access_token, authorization=None, x_profile_id=None)
    assert token_hash_key.startswith("token:")
    result = claim_anonymous_profile(
        ClaimProfileRequest(email="claimed@example.com", password="strongpass123"),
        db_session,
        profile,
    )
    assert result.profile.id == profile.id
    assert db_session.query(JournalEntry).filter(JournalEntry.profile_id == profile.id).count() == 1
    assert db_session.query(Account).filter(Account.profile_id == profile.id).count() == 1
    assert profile.access_token_hash is None


def test_session_expires_and_cannot_be_used(db_session):
    result = signup(SignupRequest(email="expiry@example.com", password="strongpass123", display_name="Expiry"), db_session)
    session = db_session.query(AuthSession).filter(AuthSession.account_id == result.account_id).first()
    session.expires_at = datetime.now(timezone.utc).replace(year=2020)
    db_session.commit()
    assert find_active_session(db_session, result.access_token) is None


def test_two_profiles_are_isolated(db_session):
    first = signup(SignupRequest(email="one@example.com", password="strongpass123", display_name="One"), db_session)
    second = signup(SignupRequest(email="two@example.com", password="strongpass123", display_name="Two"), db_session)
    p1 = db_session.get(Profile, first.profile.id)
    p2 = db_session.get(Profile, second.profile.id)
    db_session.add(JournalEntry(profile_id=p1.id, text="Only for one"))
    db_session.add(JournalEntry(profile_id=p2.id, text="Only for two"))
    db_session.commit()
    assert db_session.query(JournalEntry).filter(JournalEntry.profile_id == p1.id).count() == 1
    assert db_session.query(JournalEntry).filter(JournalEntry.profile_id == p2.id).count() == 1
    assert find_active_session(db_session, first.access_token).profile_id == p1.id
    assert find_active_session(db_session, second.access_token).profile_id == p2.id


def test_logout_revokes_session(db_session):
    from app.api.auth import logout
    result = signup(SignupRequest(email="logout@example.com", password="strongpass123", display_name="Logout"), db_session)
    assert find_active_session(db_session, result.access_token) is not None
    response = logout(authorization=f"Bearer {result.access_token}", x_profile_token=None, db=db_session)
    assert response.logged_out is True
    assert find_active_session(db_session, result.access_token) is None


def test_profile_storage_isolated_even_when_history_contains_similar_content(db_session):
    from app.models import Conversation, VivekanandaComparison, WeeklyCheckIn
    first = signup(SignupRequest(email="first@example.com", password="strongpass123", display_name="First"), db_session)
    second = signup(SignupRequest(email="second@example.com", password="strongpass123", display_name="Second"), db_session)
    db_session.add_all([
        JournalEntry(profile_id=first.profile.id, text="same topic"),
        JournalEntry(profile_id=second.profile.id, text="same topic"),
        Conversation(profile_id=first.profile.id, current_problem="same topic"),
        VivekanandaComparison(profile_id=second.profile.id, user_view="same topic", result_json={}),
        WeeklyCheckIn(profile_id=first.profile.id, week_start=datetime.now(timezone.utc), self_belief=5, fear=5, discipline=5, clarity=5, resilience=5, note="first"),
    ])
    db_session.commit()

    first_journals = db_session.query(JournalEntry).filter(JournalEntry.profile_id == first.profile.id).all()
    second_journals = db_session.query(JournalEntry).filter(JournalEntry.profile_id == second.profile.id).all()
    assert [x.text for x in first_journals] == ["same topic"]
    assert [x.text for x in second_journals] == ["same topic"]
    assert db_session.query(Conversation).filter(Conversation.profile_id == first.profile.id).count() == 1
    assert db_session.query(VivekanandaComparison).filter(VivekanandaComparison.profile_id == first.profile.id).count() == 0
