from app.database import get_db
from app.main import app
from app.models import Member


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


def deactivate_trip_member(trip_id, user_id):
    db_generator = app.dependency_overrides[get_db]()
    db = next(db_generator)
    try:
        member = db.query(Member).filter(
            Member.trip_id == trip_id,
            Member.user_id == user_id,
        ).one()
        member.status = "inactive"
        member_id = member.id
        db.commit()
        return member_id
    finally:
        db.close()
        db_generator.close()


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


def test_create_expense_trims_category_name(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)

    response = test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "128.50",
        "expression_text": "100+28.5",
        "category_name": " 餐饮 ",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "第一天晚饭",
    })

    assert response.status_code == 201
    assert response.json()["category_name"] == "餐饮"


def test_create_expense_rejects_whitespace_only_category_name(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)

    response = test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": creator["id"],
        "amount": "128.50",
        "expression_text": "100+28.5",
        "category_name": "   ",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "第一天晚饭",
    })

    assert response.status_code == 422


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


def test_get_settlement_includes_historical_inactive_payer(test_client):
    creator, friend, trip = create_trip_with_two_members(test_client)
    test_client.post(f"/trips/{trip['id']}/expenses", json={
        "user_id": friend["id"],
        "amount": "100.00",
        "expression_text": "100",
        "category_name": "餐饮",
        "spent_at": "2026-06-02T12:00:00Z",
        "note": "晚饭",
    })
    inactive_payer_id = deactivate_trip_member(trip["id"], friend["id"])

    response = test_client.get(f"/trips/{trip['id']}/settlement")

    assert response.status_code == 200
    body = response.json()
    balances = {member["name"]: member["balance"] for member in body["members"]}
    assert balances == {"小李": "-50.00", "小王": "50.00"}
    assert body["members"][1]["member_id"] == inactive_payer_id
    assert body["transfers"] == [{
        "from_member_id": body["members"][0]["member_id"],
        "from_member_name": "小李",
        "to_member_id": inactive_payer_id,
        "to_member_name": "小王",
        "amount": "50.00",
    }]


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
