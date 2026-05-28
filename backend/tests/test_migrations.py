from pathlib import Path

from app.db.session import DEFAULT_DATABASE_URL, resolve_database_url


ROOT = Path(__file__).resolve().parents[1]


def test_database_url_defaults_to_sqlite_and_can_use_environment(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert resolve_database_url() == DEFAULT_DATABASE_URL

    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://queue:secret@127.0.0.1:3306/queue_calling")
    assert resolve_database_url() == "mysql+pymysql://queue:secret@127.0.0.1:3306/queue_calling"


def test_alembic_initial_migration_covers_current_tables():
    alembic_ini = ROOT / "alembic.ini"
    env_py = ROOT / "migrations" / "env.py"
    versions = list((ROOT / "migrations" / "versions").glob("*.py"))

    assert alembic_ini.exists()
    assert env_py.exists()
    assert versions

    migration_text = "\n".join(path.read_text(encoding="utf-8") for path in versions)
    for table_name in [
        "meal_sessions",
        "line_items",
        "service_calls",
        "operation_logs",
        "stores",
        "dishes",
        "staff",
    ]:
        assert table_name in migration_text
