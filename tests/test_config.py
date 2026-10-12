from ki_review.config import get_settings


def test_get_settings_uses_defaults(monkeypatch) -> None:
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    settings = get_settings()

    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.github_token is None


def test_get_settings_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "9001")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    settings = get_settings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 9001
    assert settings.github_token == "test-token"
