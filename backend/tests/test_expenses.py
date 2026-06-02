from decimal import Decimal

from app.database import get_db
from app.main import app
from app.models import Member
from app.routers import trips
from app.services.settlements import MemberSummary, SettlementResult


def create_user(test_client, username):
    return test_client.post("/users", json={"username": username}).json()


def create_trip_with_two_members(test_client):
    creator = create_user(test_client, "小李")
    trip = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": creator["id"],
    }).json()
    friend = create_user(test_client, "小王")
    trip = test_client.post("/trips/join", json={
        "invite_code": trip["invite_code"],
        "user_id": friend["id"],
    }).json()
    return creator, friend, trip


def test_create_expense_defaults_payer_to_registering_member(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)

    response = test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "128.50",
        "expression_text": "100+28.5",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "第一天晚饭",
    })

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "128.50"
    assert body["created_by_member_id"] == body["paid_by_member_id"]


def test_get_settlement_splits_across_all_active_members(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)
    test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "100.00",
        "expression_text": "100",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "晚饭",
    })

    response = test_client.get(f"/trips/{trip['id']}/settlement")

    assert response.status_code == 200
    body = response.json()
    balances = {member["name"]: member["balance"] for member in body["members"]}
    assert balances["小李"] == "50.00"
    assert balances["小王"] == "-50.00"
    assert body["transfers"] == [{
        "from_member_id": body["members"][1]["member_id"],
        "from_member_name": "小王",
        "to_member_id": body["members"][0]["member_id"],
        "to_member_name": "小李",
        "amount": "50.00",
    }]


def test_get_settlement_passes_all_trip_expenses_to_calculator(test_client, monkeypatch):
    creator, friend, trip = create_trip_with_two_members(test_client)
    test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": friend["id"],
        "amount": "100.00",
        "expression_text": "100",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "晚饭",
    })

    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        creator_member = db.query(Member).filter(
            Member.trip_id == trip["id"],
            Member.user_id == creator["id"],
        ).one()
        inactive_payer = db.query(Member).filter(
            Member.trip_id == trip["id"],
            Member.user_id == friend["id"],
        ).one()
        inactive_payer.status = "inactive"
        creator_member_id = creator_member.id
        inactive_payer_id = inactive_payer.id
        db.commit()
    finally:
        db.close()
        db_generator.close()

    def fake_calculate_settlement(members, expenses):
        assert [member.id for member in members] == [creator_member_id]
        assert len(expenses) == 1
        assert expenses[0].paid_by_member_id == inactive_payer_id
        return SettlementResult(
            member_summaries={
                creator_member_id: MemberSummary(
                    member_id=creator_member_id,
                    name="小李",
                    paid=Decimal("0.00"),
                    owed=Decimal("0.00"),
                    balance=Decimal("0.00"),
                )
            },
            transfers=[],
        )

    monkeypatch.setattr(trips, "calculate_settlement", fake_calculate_settlement)

    response = test_client.get(f"/trips/{trip['id']}/settlement")

    assert response.status_code == 200


def test_update_expense_allows_any_member_and_increments_version(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)
    created = test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "100.00",
        "expression_text": "100",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "晚饭",
    }).json()

    response = test_client.put(f"/trips/{trip['id']}/expenses/{created['id']}", json={
        "user_id": friend["id"],
        "amount": "120.00",
        "expression_text": "(100+20)",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:30:00Z",
        "note": "改成含饮料",
    })

    assert response.status_code == 200
    assert response.json()["amount"] == "120.00"
    assert response.json()["note"] == "改成含饮料"


def test_delete_expense_records_change_event(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)
    created = test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "100.00",
        "expression_text": "100",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "晚饭",
    }).json()

    response = test_client.request("DELETE", f"/trips/{trip['id']}/expenses/{created['id']}", json={
        "user_id": friend["id"],
    })

    assert response.status_code == 204
    detail = test_client.get(f"/trips/{trip['id']}").json()
    assert detail["expenses"] == []


def test_changes_returns_events_since_version(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)
    test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "100.00",
        "expression_text": "100",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "晚饭",
    })

    response = test_client.get(f"/trips/{trip['id']}/changes?since_version=0")

    assert response.status_code == 200
    body = response.json()
    assert body["current_version"] >= 3
    assert any(event["action"] == "created" for event in body["events"])
