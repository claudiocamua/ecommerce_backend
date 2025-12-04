import pytest
from fastapi import status
import time

def test_list_products(client):
    """Testa a listagem de produtos"""
    response = client.get("/products")
    print(f"\nList products: {response.status_code}")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)

def test_create_product_unauthorized(client):
    """Testa criação de produto sem autenticação"""
    response = client.post(
        "/products",
        json={
            "nome": "Produto Teste",
            "descricao": "Descrição",
            "preco": 99.99,
            "estoque": 10,
            "categoria": "Eletrônicos"
        }
    )
    print(f"\nUnauthorized create: {response.status_code}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_product_authorized(client):
    """Testa criação de produto com autenticação"""
    # Registra usuário e obtém token
    user_data = {
        "email": f"seller{int(time.time())}@example.com",
        "password": "Password123!",
        "password_confirm": "Password123!",
        "full_name": "Seller User",
        "phone": "11999999999"
    }
    reg_response = client.post("/auth/register", json=user_data)
    token = reg_response.json()["access_token"]
    
    # Cria produto
    response = client.post(
        "/products",
        json={
            "name": "Produto Teste",
            "description": "Descrição do produto",
            "price": 99.99,
            "stock": 10,
            "category": "Eletrônicos",
            "images": []
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"\nCreate product: {response.status_code}")
    if response.status_code != 201:
        print(f"Response: {response.json()}")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "Produto Teste"

def test_get_product_by_id(client):
    """Testa obtenção de produto por ID"""
    # Cria usuário
    user_data = {
        "email": f"buyer{int(time.time())}@example.com",
        "password": "Password123!",
        "password_confirm": "Password123!",
        "full_name": "Buyer User",
        "phone": "11999999999"
    }
    reg_response = client.post("/auth/register", json=user_data)
    token = reg_response.json()["access_token"]
    
    # Cria produto
    create_response = client.post(
        "/products",
        json={
            "name": "Produto para Buscar",
            "description": "Teste",
            "price": 50.0,
            "stock": 5,
            "category": "Teste",
            "images": []
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if create_response.status_code == 201:
        product_id = create_response.json()["_id"]
        
        # Busca produto
        response = client.get(f"/products/{product_id}")
        print(f"\nGet product: {response.status_code}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Produto para Buscar"
    else:
        pytest.skip(f"Failed to create product: {create_response.json()}")

def test_search_products(client):
    """Testa busca de produtos"""
    response = client.get("/products?search=teste")
    print(f"\nSearch products: {response.status_code}")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)