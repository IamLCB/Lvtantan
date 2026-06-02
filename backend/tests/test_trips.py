def create_user(test_client, username="小李"):
    return test_client.post("/users", json={"username": username}).json()


def test_create_trip_generates_invite_code_and_membership(test_client):
    user = create_user(test_client)
    response = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": user["id"],
    })

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "青岛周末旅行"
    assert len(body["invite_code"]) == 6
    assert body["currency_code"] == "CNY"
    assert body["members"][0]["name"] == "小李"


def test_create_trip_rejects_whitespace_only_name(test_client):
    user = create_user(test_client)

    response = test_client.post("/trips", json={
        "name": "   ",
        "created_by_user_id": user["id"],
    })

    assert response.status_code == 422


def test_create_trip_trims_name(test_client):
    user = create_user(test_client)

    response = test_client.post("/trips", json={
        "name": "  青岛周末旅行  ",
        "created_by_user_id": user["id"],
    })

    assert response.status_code == 201
    assert response.json()["name"] == "青岛周末旅行"


def test_create_trip_retries_invite_code_collision(test_client, monkeypatch):
    first_user = create_user(test_client, "小李")
    second_user = create_user(test_client, "小王")
    codes = iter(["ABC123", "ABC123", "XYZ789"])
    monkeypatch.setattr("app.routers.trips.generate_invite_code", lambda: next(codes))

    first_response = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": first_user["id"],
    })
    second_response = test_client.post("/trips", json={
        "name": "威海周末旅行",
        "created_by_user_id": second_user["id"],
    })

    assert first_response.status_code == 201
    assert first_response.json()["invite_code"] == "ABC123"
    assert second_response.status_code == 201
    assert second_response.json()["invite_code"] == "XYZ789"


def test_join_trip_rejects_duplicate_member_name(test_client):
    creator = create_user(test_client, "小李")
    trip = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": creator["id"],
    }).json()
    duplicate = create_user(test_client, "小李")

    response = test_client.post("/trips/join", json={
        "invite_code": trip["invite_code"],
        "user_id": duplicate["id"],
    })

    assert response.status_code == 409
    assert response.json()["detail"] == "username already exists in this trip"


def test_join_trip_same_user_is_idempotent(test_client):
    creator = create_user(test_client, "小李")
    trip = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": creator["id"],
    }).json()

    response = test_client.post("/trips/join", json={
        "invite_code": trip["invite_code"],
        "user_id": creator["id"],
    })

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == trip["version"]
    assert [member["name"] for member in body["members"]] == ["小李"]


def test_join_trip_adds_member(test_client):
    creator = create_user(test_client, "小李")
    trip = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": creator["id"],
    }).json()
    friend = create_user(test_client, "小王")

    response = test_client.post("/trips/join", json={
        "invite_code": trip["invite_code"],
        "user_id": friend["id"],
    })

    assert response.status_code == 200
    member_names = [member["name"] for member in response.json()["members"]]
    assert member_names == ["小李", "小王"]


def test_join_trip_accepts_lowercase_invite_code(test_client):
    creator = create_user(test_client, "小李")
    trip = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": creator["id"],
    }).json()
    friend = create_user(test_client, "小王")

    response = test_client.post("/trips/join", json={
        "invite_code": trip["invite_code"].lower(),
        "user_id": friend["id"],
    })

    assert response.status_code == 200
    member_names = [member["name"] for member in response.json()["members"]]
    assert member_names == ["小李", "小王"]


def test_join_trip_increments_version(test_client):
    creator = create_user(test_client, "小李")
    trip = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": creator["id"],
    }).json()
    friend = create_user(test_client, "小王")

    response = test_client.post("/trips/join", json={
        "invite_code": trip["invite_code"],
        "user_id": friend["id"],
    })

    assert response.status_code == 200
    assert response.json()["version"] == trip["version"] + 1


def test_create_trip_missing_user_returns_404(test_client):
    response = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": "missing-user",
    })

    assert response.status_code == 404
    assert response.json()["detail"] == "user not found"


def test_join_trip_missing_user_returns_404(test_client):
    creator = create_user(test_client, "小李")
    trip = test_client.post("/trips", json={
        "name": "青岛周末旅行",
        "created_by_user_id": creator["id"],
    }).json()

    response = test_client.post("/trips/join", json={
        "invite_code": trip["invite_code"],
        "user_id": "missing-user",
    })

    assert response.status_code == 404
    assert response.json()["detail"] == "user not found"


def test_join_trip_missing_invite_returns_404(test_client):
    friend = create_user(test_client, "小王")

    response = test_client.post("/trips/join", json={
        "invite_code": "ABC123",
        "user_id": friend["id"],
    })

    assert response.status_code == 404
    assert response.json()["detail"] == "invite code not found"
