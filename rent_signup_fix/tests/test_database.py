from database.db import init_db, get_db


def test_database_has_tables(tmp_path, monkeypatch):
    # Basic smoke-test placeholder for future isolated DB testing.
    init_db()
    db = get_db()

    tables = {
        row["name"]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    assert "families" in tables
    assert "bills" in tables

    db.close()
