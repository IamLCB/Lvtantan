from decimal import Decimal
from typing import get_args, get_type_hints

from sqlalchemy import UniqueConstraint, create_engine
from sqlalchemy.orm import configure_mappers

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


def test_model_mappers_configure_successfully():
    configure_mappers()


def test_expense_amount_uses_fixed_precision_numeric():
    amount_type = models.Expense.__table__.columns["amount"].type
    amount_annotation = get_type_hints(models.Expense)["amount"]

    assert amount_type.python_type is Decimal
    assert amount_type.precision == 12
    assert amount_type.scale == 2
    assert get_args(amount_annotation) == (Decimal,)


def test_expense_member_relationships_use_explicit_foreign_keys():
    created_relationship = models.Expense.__mapper__.relationships["created_by_member"]
    paid_relationship = models.Expense.__mapper__.relationships["paid_by_member"]

    assert created_relationship.mapper.class_ is models.Member
    assert paid_relationship.mapper.class_ is models.Member
    assert {
        column.name for column in created_relationship.local_columns
    } == {"created_by_member_id"}
    assert {column.name for column in paid_relationship.local_columns} == {"paid_by_member_id"}
    assert "created_expenses" in models.Member.__mapper__.relationships
    assert "paid_expenses" in models.Member.__mapper__.relationships


def test_members_declares_expected_unique_constraints():
    constraints = {
        tuple(constraint.columns.keys())
        for constraint in models.Member.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("trip_id", "name") in constraints
    assert ("trip_id", "user_id") in constraints


def test_metadata_can_create_and_drop_in_memory_sqlite_schema():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Base.metadata.drop_all(bind=engine)
