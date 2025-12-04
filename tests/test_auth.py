import pytest
from fastapi import status

def test_health_check(client):
    """Testa o health check da API"""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "healthy"

def test_register_new_user(client):
    """Testa o registro de novo usuário"""
    import time
    unique_email = f"newuser{int(time.time())}@example.com"
    response = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "Password123!",
            "password_confirm": "Password123!",
            "full_name": "New User",
            "phone": "11999999999"
        }
    )
    print(f"\nResponse status: {response.status_code}")
    print(f"Response body: {response.json()}")
    assert response.status_code == status.HTTP_201_CREATED
    assert "access_token" in response.json()

def test_register_duplicate_email(client):
    """Testa registro com email duplicado"""
    import time
    user_data = {
        "email": f"duplicate{int(time.time())}@example.com",
        "password": "Password123!",
        "password_confirm": "Password123!",
        "full_name": "Duplicate User",
        "phone": "11999999999"
    }
    
    # Primeiro registro
    response1 = client.post("/auth/register", json=user_data)
    print(f"\nFirst register: {response1.status_code}")
    
    # Tentativa de registro duplicado
    response2 = client.post("/auth/register", json=user_data)
    print(f"Duplicate register: {response2.status_code}")
    print(f"Response: {response2.json()}")
    assert response2.status_code == status.HTTP_400_BAD_REQUEST

def test_register_password_mismatch(client):
    """Testa registro com senhas diferentes"""
    import time
    response = client.post(
        "/auth/register",
        json={
            "email": f"mismatch{int(time.time())}@example.com",
            "password": "Password123!",
            "password_confirm": "DifferentPass123!",
            "full_name": "Test User",
            "phone": "11999999999"
        }
    )
    print(f"\nPassword mismatch: {response.status_code}")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_login_success(client):
    """Testa login com credenciais corretas"""
    import time
    user_data = {
        "email": f"loginuser{int(time.time())}@example.com",
        "password": "Password123!",
        "password_confirm": "Password123!",
        "full_name": "Login User",
        "phone": "11999999999"
    }
    
    # Registra o usuário
    reg_response = client.post("/auth/register", json=user_data)
    print(f"\nRegister response: {reg_response.status_code}")
    
    # Faz login
    response = client.post(
        "/auth/login",
        data={
            "username": user_data["email"],
            "password": user_data["password"]
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Login response: {response.status_code}")
    print(f"Response body: {response.json()}")
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()

def test_login_invalid_credentials(client):
    """Testa login com credenciais inválidas"""
    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"\nInvalid login response: {response.status_code}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_current_user(client):
    """Testa obtenção de dados do usuário autenticado"""
    import time
    user_data = {
        "email": f"currentuser{int(time.time())}@example.com",
        "password": "Password123!",
        "password_confirm": "Password123!",
        "full_name": "Current User",
        "phone": "11999999999"
    }
    
    # Registra e obtém token
    reg_response = client.post("/auth/register", json=user_data)
    token = reg_response.json()["access_token"]
    
    # Busca dados do usuário
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"\nGet user response: {response.status_code}")
    print(f"Response body: {response.json()}")
    assert response.status_code == status.HTTP_200_OK
    assert "email" in response.json()
