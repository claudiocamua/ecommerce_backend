from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_demo_flow():
    res = client.post("/auth/register", json={
        "email": "demo@demo.com",
        "password": "Demo@1234",
        "password_confirm": "Demo@1234",
        "full_name": "Usuário Demo"
    })
    assert res.status_code in [200, 201, 400]  

    login = client.post("/auth/login", data={
        "username": "demo@demo.com",
        "password": "Demo@1234"
    })
    assert login.status_code == 200

    token = login.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    produtos = client.get("/products", headers=headers)
    assert produtos.status_code == 200

    cart = client.get("/cart", headers=headers)
    assert cart.status_code == 200
