from app.bootstrap import warn_about_deployment_config
from app.config import Settings


def settings(**kw):
    return Settings(_env_file=None, **kw)


def test_production_sqlite_is_flagged():
    problems = warn_about_deployment_config(settings(environment="production", database_url="sqlite:///./x.db", gemini_api_key="k"))
    assert any("SQLite" in p for p in problems)


def test_production_localhost_cors_is_flagged():
    problems = warn_about_deployment_config(settings(
        environment="production", database_url="postgresql://u:p@h/d", gemini_api_key="k",
        cors_origins="http://localhost:3000",
    ))
    assert any("CORS" in p for p in problems)


def test_missing_gemini_key_is_flagged_everywhere():
    assert any("GEMINI_API_KEY" in p for p in warn_about_deployment_config(settings(environment="development", gemini_api_key="")))


def test_clean_production_config_has_no_warnings():
    assert warn_about_deployment_config(settings(
        environment="production", database_url="postgresql://u:p@h/d", gemini_api_key="k",
        cors_origins="https://app.example.com",
    )) == []


def test_render_database_urls_are_normalised_for_psycopg3():
    from app.db.session import normalize_database_url
    assert normalize_database_url("postgres://u:p@h/d").startswith("postgresql+psycopg://")
    assert normalize_database_url("postgresql://u:p@h/d").startswith("postgresql+psycopg://")
