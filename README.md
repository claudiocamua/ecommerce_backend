# E-commerce Backend API

Backend de uma aplicação de e-commerce desenvolvido com **FastAPI** e **MongoDB**.

Este projeto fornece uma API REST para cadastro de usuários, autenticação, produtos, carrinho de compras e pedidos.

---

## Tecnologias

- Python 3.12
- FastAPI
- MongoDB (Atlas)
- Pydantic
- JWT (python-jose)
- Uvicorn
- Pytest

---

## Funcionalidades

- Autenticação (Login / Registro com JWT)
- CRUD de usuários
- CRUD de produtos
- Upload de imagens de produtos
- Carrinho de compras
- Criação de pedidos
- Pagamento simulado (PIX e Cartão)
- Modo **DEMO** para testes

---

## Como rodar o projeto localmente
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload

pytest -v



### 1. Clonar o repositório
```bash
git clone git@github.com:claudiocamua/ecommerce_backend.git
cd seu-repositorio
