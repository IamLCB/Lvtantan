from app.database import Base
from app import models


def test_expected_tables_are_declared():
    table_names = set(Base.metadata.tables.keys())
    assert {
        "users",
        "trips",
        "members",
        "categories",
        "expenses",
        "realtime_events",
    }.issubset(table_names)
