import pytest
from datetime import datetime, timedelta
from app.models.booking import BookingStatus

class TestBooking:
    
    def test_create_booking_success(self, client, customer_headers, test_customer, test_service, test_schedule):
        """Test successful booking creation"""
        response = client.post("/bookings/", json={
            "service_id": test_service.id,
            "schedule_id": test_schedule.id
        }, headers=customer_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == test_customer.id
        assert data["service_id"] == test_service.id
        assert data["status"] == "pending"
        assert data["payment_status"] == "unpaid"
    
    def test_create_booking_without_auth(self, client, test_service, test_schedule):
        """Test booking without authentication"""
        response = client.post("/bookings/", json={
            "service_id": test_service.id,
            "schedule_id": test_schedule.id
        })
        assert response.status_code == 401
    
    def test_create_booking_nonexistent_schedule(self, client, customer_headers, test_service):
        """Test booking with non-existent schedule"""
        response = client.post("/bookings/", json={
            "service_id": test_service.id,
            "schedule_id": 99999
        }, headers=customer_headers)
        
        assert response.status_code == 404
    
    def test_get_my_bookings(self, client, customer_headers, db, test_booking):
        """Test getting customer's bookings"""
        db.refresh(test_booking)
        
        response = client.get("/bookings/my-bookings", headers=customer_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["id"] == test_booking.id
    
    def test_confirm_booking_as_provider(self, client, provider_headers, test_booking):
        """Test provider confirming a booking"""
        response = client.put(f"/bookings/{test_booking.id}/status", json={
            "status": "confirmed"
        }, headers=provider_headers)
        
        assert response.status_code == 200
        assert "confirmed" in response.json()["message"].lower()
    
    def test_reject_booking_as_provider(self, client, provider_headers, test_booking):
        """Test provider rejecting a booking"""
        response = client.put(f"/bookings/{test_booking.id}/status", json={
            "status": "rejected"
        }, headers=provider_headers)
        
        assert response.status_code == 200
        assert "rejected" in response.json()["message"].lower()
    
    def test_cancel_booking_as_customer(self, client, customer_headers, db, test_booking):
        """Test customer cancelling a booking"""
        test_booking.cancellation_deadline = datetime.now() + timedelta(hours=3)
        db.commit()
        
        response = client.post(f"/bookings/{test_booking.id}/cancel", headers=customer_headers)
        assert response.status_code == 200
        assert "cancelled" in response.json()["message"].lower()
    
    def test_cancel_booking_after_deadline_fails(self, client, customer_headers, db, test_booking, test_schedule):
        """Test cancellation after deadline (should fail)"""
        test_booking.status = BookingStatus.CONFIRMED
        test_schedule.start_time = datetime.now() - timedelta(hours=1)
        test_booking.cancellation_deadline = test_schedule.start_time - timedelta(hours=2)
        db.commit()
        
        response = client.post(f"/bookings/{test_booking.id}/cancel", headers=customer_headers)
        assert response.status_code == 400
        assert "deadline" in response.json()["detail"].lower()
    
    def test_cancel_already_cancelled_booking_fails(self, client, customer_headers, db, test_booking):
        """Test cancelling already cancelled booking"""
        test_booking.status = BookingStatus.CANCELLED
        db.commit()
        
        response = client.post(f"/bookings/{test_booking.id}/cancel", headers=customer_headers)
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower() or "deadline" in response.json()["detail"].lower()