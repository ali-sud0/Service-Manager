import pytest

class TestLogin:
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully"""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert "login" in response.text.lower()
    
    def test_login_with_valid_credentials(self, client, test_customer):
        """Test login with valid credentials"""
        response = client.post("/auth/login", json={
            "username": test_customer.username,
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_with_email(self, client, test_customer):
        """Test login using email instead of username"""
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
            "username": "nonexistentuser",
            "password": "password123"
        })
        
        assert response.status_code == 401
    
    def test_login_empty_fields(self, client):
        """Test login with empty fields"""
        response = client.post("/auth/login", json={
            "username": "",
            "password": ""
        })
        
        assert response.status_code in [401, 422]
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post("/auth/login", json={
            "username": "testuser"
        })
        
        assert response.status_code == 422
    
    def test_login_inactive_user(self, client, db, test_customer):
        """Test login with inactive user account"""
        test_customer.is_active = False
        db.commit()
        
        response = client.post("/auth/login", json={
            "username": test_customer.username,
            "password": "password123"
        })
        
        assert response.status_code == 401
        assert "disabled" in response.json()["detail"].lower()
    
    def test_login_case_sensitivity(self, client, test_customer):
        """Test that username is case sensitive"""
        response = client.post("/auth/login", json={
            "username": test_customer.username.upper(),
            "password": "password123"
        })
        
        assert response.status_code == 401
    
    def test_login_remember_me_functionality(self, client, test_customer):
        """Test login with remember me functionality"""
        response = client.post("/auth/login", json={
            "username": test_customer.username,
            "password": "password123"
        })
        
        assert response.status_code == 200
        token = response.json().get("access_token")
        assert token is not None
    
    def test_login_response_contains_role(self, client, test_customer):
        """Test that login response contains user role"""
        response = client.post("/auth/login", json={
            "username": test_customer.username,
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "role" in data
        assert data["role"] == "customer"
    
    def test_login_provider_role(self, client, test_provider):
        """Test login for provider user"""
        response = client.post("/auth/login", json={
            "username": test_provider.username,
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "provider"
    
    def test_login_admin_role(self, client, test_admin):
        """Test login for admin user"""
        response = client.post("/auth/login", json={
            "username": test_admin.username,
            "password": "password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
    
    def test_login_with_special_characters(self, client):
        """Test login with special characters in username"""
        response = client.post("/auth/login", json={
            "username": "test@#$%",
            "password": "password123"
        })
        
        assert response.status_code == 401