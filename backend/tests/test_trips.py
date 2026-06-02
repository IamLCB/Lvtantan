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
