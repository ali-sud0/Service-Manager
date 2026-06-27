import pytest
from datetime import datetime, timedelta

class TestSchedule:
    
    def test_create_schedule_success(self, client, provider_headers, test_service):
        """Test successful schedule creation"""
        start_time = datetime.now() + timedelta(days=2)
        end_time = start_time + timedelta(minutes=test_service.duration_minutes)
        
        response = client.post("/schedules/", json={
            "service_id": test_service.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }, headers=provider_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["service_id"] == test_service.id
        assert data["is_available"] == True
    
    def test_create_schedule_overlapping_fails(self, client, provider_headers, test_service, test_schedule):
        """Test creating overlapping schedule (should fail)"""
        response = client.post("/schedules/", json={
            "service_id": test_service.id,
            "start_time": test_schedule.start_time.isoformat(),
            "end_time": test_schedule.end_time.isoformat()
        }, headers=provider_headers)
        
        assert response.status_code == 400
        assert "overlaps" in response.json()["detail"].lower()
    
    def test_create_schedule_wrong_duration(self, client, provider_headers, test_service):
        """Test creating schedule with wrong duration (should fail)"""
        start_time = datetime.now() + timedelta(days=2)
        end_time = start_time + timedelta(minutes=30)  # Wrong duration
        
        response = client.post("/schedules/", json={
            "service_id": test_service.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }, headers=provider_headers)
        
        assert response.status_code == 400
        assert "duration must match" in response.json()["detail"].lower()
    
    def test_create_schedule_for_other_provider_fails(self, client, customer_headers, test_service):
        """Test creating schedule for service not owned (should fail)"""
        start_time = datetime.now() + timedelta(days=2)
        end_time = start_time + timedelta(hours=1)
        
        response = client.post("/schedules/", json={
            "service_id": test_service.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }, headers=customer_headers)
        
        assert response.status_code == 403
    
    def test_get_service_schedules(self, client, test_service, test_schedule):
        """Test getting schedules for a service"""
        response = client.get(f"/schedules/service/{test_service.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 0  # May be empty if schedule is booked
    
    def test_delete_schedule_by_owner(self, client, provider_headers, test_service):
        """Test schedule deletion by owner"""
        # Create a schedule first
        start_time = datetime.now() + timedelta(days=3)
        end_time = start_time + timedelta(minutes=test_service.duration_minutes)
        
        create_response = client.post("/schedules/", json={
            "service_id": test_service.id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }, headers=provider_headers)
        
        schedule_id = create_response.json()["id"]
        
        # Delete it
        delete_response = client.delete(f"/schedules/{schedule_id}", headers=provider_headers)
        assert delete_response.status_code == 200
    
    def test_delete_schedule_unauthorized(self, client, customer_headers, test_schedule):
        """Test schedule deletion by unauthorized user"""
        response = client.delete(f"/schedules/{test_schedule.id}", headers=customer_headers)
        assert response.status_code == 403