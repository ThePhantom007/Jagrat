from app.config import Settings


def test_cors_origins_string_parses_without_json_decoding():
    settings = Settings(_env_file=None, cors_origins="http://localhost:3000,http://localhost:5173")
    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]
