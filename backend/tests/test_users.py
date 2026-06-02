def test_create_user_returns_user_id(test_client):
    response = test_client.post("/users", json={"username": "小李"})

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "小李"
    assert isinstance(body["id"], str)


def test_create_user_rejects_whitespace_only_username(test_client):
    response = test_client.post("/users", json={"username": "   "})

    assert response.status_code == 422


def test_create_user_trims_username(test_client):
    response = test_client.post("/users", json={"username": "  小李  "})

    assert response.status_code == 201
    assert response.json()["username"] == "小李"
