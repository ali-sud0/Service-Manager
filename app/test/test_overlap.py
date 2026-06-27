import pytest
from datetime import datetime, timedelta
from app.models.booking import BookingStatus

class TestOverlap:
    
    def test_prevent_double_booking_same_schedule(self, client, customer_headers, db, test_booking):
        """Test preventing booking of already booked schedule"""
        
        schedule_id = test_booking.schedule_id
        
        response = client.post("/bookings/", json={
            "service_id": test_booking.service_id,
            "schedule_id": schedule_id
        }, headers=customer_headers)
        
        
        assert response.status_code == 404


    def test_prevent_booking_confirmed_schedule(self, client, customer_headers, db, test_booking):
        """Test preventing booking of already confirmed schedule"""
        test_booking.status = BookingStatus.CONFIRMED
        db.commit()
        
        schedule_id = test_booking.schedule_id
        
        response = client.post("/bookings/", json={
            "service_id": test_booking.service_id,
            "schedule_id": schedule_id
        }, headers=customer_headers)
        
        assert response.status_code == 404
    

    def test_allow_booking_after_cancellation(self, client, customer_headers, db, test_booking):
        """Test allowing booking after previous booking was cancelled"""
        test_booking.status = BookingStatus.CANCELLED
        if test_booking.schedule:
            test_booking.schedule.is_available = True
        db.commit()
        
        response = client.post("/bookings/", json={
            "service_id": test_booking.service_id,
            "schedule_id": test_booking.schedule_id
        }, headers=customer_headers)
        
        assert response.status_code == 200
    
    def test_prevent_booking_overlapping_schedules(self, client, provider_headers, test_service):
        """Test preventing booking of overlapping time slots"""
        start_time1 = datetime.now() + timedelta(days=1)
        end_time1 = start_time1 + timedelta(minutes=60)
        
        start_time2 = start_time1 + timedelta(minutes=30)
        end_time2 = start_time2 + timedelta(minutes=60)
        
        # Create first schedule
        response1 = client.post("/schedules/", json={
            "service_id": test_service.id,
            "start_time": start_time1.isoformat(),
            "end_time": end_time1.isoformat()
        }, headers=provider_headers)
        
        assert response1.status_code == 200
        
        # Create overlapping schedule (should fail)
        response2 = client.post("/schedules/", json={
            "service_id": test_service.id,
            "start_time": start_time2.isoformat(),
            "end_time": end_time2.isoformat()
        }, headers=provider_headers)
        
        assert response2.status_code == 400
        assert "overlaps" in response2.json()["detail"].lower()
    
    def test_allow_non_overlapping_bookings(self, client, customer_headers, provider_headers, test_service):
        """Test allowing bookings for different time slots"""
        start_time1 = datetime.now() + timedelta(days=2)
        end_time1 = start_time1 + timedelta(minutes=60)
        
        start_time2 = start_time1 + timedelta(hours=2)
        end_time2 = start_time2 + timedelta(minutes=60)
        
        # Create schedules
        response1 = client.post("/schedules/", json={
            "service_id": test_service.id,
            "start_time": start_time1.isoformat(),
            "end_time": end_time1.isoformat()
        }, headers=provider_headers)
        schedule1_id = response1.json()["id"]
        
        response2 = client.post("/schedules/", json={
            "service_id": test_service.id,
            "start_time": start_time2.isoformat(),
            "end_time": end_time2.isoformat()
        }, headers=provider_headers)
        schedule2_id = response2.json()["id"]
        
        # Book first schedule
        booking1 = client.post("/bookings/", json={
            "service_id": test_service.id,
            "schedule_id": schedule1_id
        }, headers=customer_headers)
        assert booking1.status_code == 200
        
        # Book second schedule (should be allowed)
        booking2 = client.post("/bookings/", json={
            "service_id": test_service.id,
            "schedule_id": schedule2_id
        }, headers=customer_headers)
        assert booking2.status_code == 200