import pytest

class TestAuth:
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post("/auth/signup", json={
            "email": "newuser@test.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "password123",
            "phone": "1234567890",
            "role": "customer"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
    
    def test_register_duplicate_email(self, client, test_customer):
        """Test registration with existing email"""
        response = client.post("/auth/signup", json={
            "email": test_customer.email,
            "username": "anotheruser",
            "full_name": "Another User",
            "password": "password123",
            "phone": "1234567890",
            "role": "customer"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_duplicate_username(self, client, test_customer):
        """Test registration with existing username"""
        response = client.post("/auth/signup", json={
            "email": "unique@test.com",
            "username": test_customer.username,
            "full_name": "Another User",
            "password": "password123",
            "phone": "1234567890",
            "role": "customer"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_success(self, client, test_customer):
        """Test successful login with username"""
        response = client.post("/auth/login", json={
            "username": test_customer.username,
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["role"] == "customer"
    
    def test_login_with_email(self, client, test_customer):
        """Test successful login with email"""
        response = client.post("/auth/login", json={
            "username": test_customer.email,
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_wrong_password(self, client, test_customer):
        """Test login with wrong password"""
        response = client.post("/auth/login", json={
            "username": test_customer.username,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })
        assert response.status_code == 401
    
    def test_login_inactive_user(self, client, db, test_customer):
        """Test login with inactive user"""
        test_customer.is_active = False
        db.commit()
        
        response = client.post("/auth/login", json={
            "username": test_customer.username,
            "password": "password123"
        })
        assert response.status_code == 401
        assert "disabled" in response.json()["detail"].lower()