from sqlalchemy.engine import make_url

from core.config import Settings


def test_database_url_is_built_from_postgres_variables() -> None:
    settings = Settings(
        _env_file=None,
        postgres_host="db.internal",
        postgres_port=6543,
        postgres_db="catalog",
        postgres_user="router",
        postgres_password="p@ss:word/1",
    )

    url = make_url(settings.sqlalchemy_database_url)

    assert url.drivername == "postgresql+asyncpg"
    assert (url.host, url.port, url.database) == ("db.internal", 6543, "catalog")
    assert (url.username, url.password) == ("router", "p@ss:word/1")


def test_database_url_takes_precedence() -> None:
    settings = Settings(
        _env_file=None, database_url="sqlite+aiosqlite:///tmp.db", postgres_host="ignored"
    )

    assert settings.sqlalchemy_database_url == "sqlite+aiosqlite:///tmp.db"
