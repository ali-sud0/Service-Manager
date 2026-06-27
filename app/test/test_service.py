import pytest

class TestService:
    
    def test_create_service_success(self, client, provider_headers, test_provider):
        """Test successful service creation by provider"""
        response = client.post("/services/", json={
            "name": "Premium Cleaning Service",
            "description": "Professional cleaning service",
            "category": "Cleaning",
            "price": 150.00,
            "duration_minutes": 90
        }, headers=provider_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Premium Cleaning Service"
        assert data["price"] == 150.00
        assert data["provider_id"] == test_provider.id
        assert data["is_active"] == True
    
    def test_create_service_as_customer_fails(self, client, customer_headers):
        """Test service creation by customer (should fail)"""
        response = client.post("/services/", json={
            "name": "Test Service",
            "description": "Test description",
            "category": "Test",
            "price": 100.00,
            "duration_minutes": 60
        }, headers=customer_headers)
        
        assert response.status_code == 403
    
    def test_get_my_services(self, client, provider_headers, test_service):
        """Test getting services for a provider"""
        response = client.get("/services/my-services", headers=provider_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == test_service.name
    
    def test_update_service_by_owner(self, client, provider_headers, test_service):
        """Test service update by owner"""
        response = client.put(f"/services/{test_service.id}", json={
            "name": "Updated Service Name",
            "price": 200.00
        }, headers=provider_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Service Name"
        assert data["price"] == 200.00
    
    def test_update_service_by_admin(self, client, admin_headers, test_service):
        """Test service update by admin"""
        response = client.put(f"/services/{test_service.id}", json={
            "is_active": False
        }, headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False
    
    def test_update_service_unauthorized(self, client, customer_headers, test_service):
        """Test service update by unauthorized user"""
        response = client.put(f"/services/{test_service.id}", json={
            "name": "Hacked Name"
        }, headers=customer_headers)
        
        assert response.status_code == 403
    
    def test_delete_service_by_owner(self, client, provider_headers):
        """Test service deletion by owner"""
        # First create a service
        create_response = client.post("/services/", json={
            "name": "Service to Delete",
            "description": "Will be deleted",
            "category": "Test",
            "price": 50.00,
            "duration_minutes": 30
        }, headers=provider_headers)
        
        service_id = create_response.json()["id"]
        
        # Then delete it
        delete_response = client.delete(f"/services/{service_id}", headers=provider_headers)
        assert delete_response.status_code == 200
        assert "deleted" in delete_response.json()["message"].lower()
    
    def test_get_service_by_id(self, client, test_service):
        """Test getting service by ID"""
        response = client.get(f"/services/{test_service.id}")
        assert response.status_code == 200
        assert response.json()["id"] == test_service.id
    
    def test_search_services(self, client, test_service):
        """Test searching services"""
        response = client.get(f"/services/search?q={test_service.name}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_get_categories(self, client, test_service):
        """Test getting categories"""
        response = client.get("/services/categories")
        assert response.status_code == 200
        assert "Cleaning" in response.json()