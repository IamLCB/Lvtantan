def test_create_user_returns_user_id(test_client):
    response = test_client.post("/users", json={"username": "小李"})

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "小李"
    assert isinstance(body["id"], str)
