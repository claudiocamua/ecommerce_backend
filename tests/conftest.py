import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Cliente de teste para fazer requisições"""
    return TestClient(app)

@pytest.fixture
def test_user_data():
    """Dados de usuário para testes"""
    return {
        "email": "test@example.com",
        "password": "Test123!",
        "password_confirm": "Test123!",
        "full_name": "Test User",
        "phone": "11999999999"
    }

@pytest.fixture
def auth_headers(client, test_user_data):
    """Headers com token de autenticação"""
    # Registra um usuário de teste
    response = client.post("/auth/register", json=test_user_data)
    if response.status_code == 201:
        token = response.json()["access_token"]
    else:
        # Se já existe, faz login
        response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}