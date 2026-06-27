import pytest
from app.models.booking import PaymentStatus, BookingStatus

class TestPayment:
    
    def test_process_payment_success(self, client, customer_headers, db, test_booking):
        """Test successful payment processing"""
        # First confirm the booking
        test_booking.status = BookingStatus.CONFIRMED
        db.commit()
        
        response = client.post(f"/payments/process/{test_booking.id}", json={
            "payment_method": "credit_card"
        }, headers=customer_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data
        assert "Payment successful" in data["message"]
    
    def test_process_payment_already_paid(self, client, customer_headers, db, test_booking):
        """Test processing payment for already paid booking"""
        test_booking.status = BookingStatus.CONFIRMED
        test_booking.payment_status = PaymentStatus.PAID
        db.commit()
        
        response = client.post(f"/payments/process/{test_booking.id}", json={
            "payment_method": "credit_card"
        }, headers=customer_headers)
        
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()
    
    def test_process_payment_not_confirmed(self, client, customer_headers, test_booking):
        """Test payment for non-confirmed booking (should fail)"""
        response = client.post(f"/payments/process/{test_booking.id}", json={
            "payment_method": "credit_card"
        }, headers=customer_headers)
        
        assert response.status_code == 400
        assert "confirmed" in response.json()["detail"].lower()
    
    def test_process_payment_unauthorized(self, client, provider_headers, test_booking):
        """Test payment by someone other than the customer"""
        response = client.post(f"/payments/process/{test_booking.id}", json={
            "payment_method": "credit_card"
        }, headers=provider_headers)
        
        assert response.status_code == 403
    
    def test_get_payment_status(self, client, customer_headers, test_booking):
        """Test getting payment status"""
        response = client.get(f"/payments/status/{test_booking.id}", headers=customer_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["booking_id"] == test_booking.id
        assert "payment_status" in data
    
    def test_payment_updates_booking_status(self, client, customer_headers, db, test_booking):
        """Test that payment updates booking payment status"""
        test_booking.status = BookingStatus.CONFIRMED
        db.commit()
        
        assert test_booking.payment_status == PaymentStatus.UNPAID
        
        response = client.post(f"/payments/process/{test_booking.id}", json={
            "payment_method": "credit_card"
        }, headers=customer_headers)
        
        assert response.status_code == 200
        
        db.refresh(test_booking)
        assert test_booking.payment_status == PaymentStatus.PAID
    
    def test_payment_creates_transaction_id(self, client, customer_headers, db, test_booking):
        """Test that payment creates a unique transaction ID"""
        test_booking.status = BookingStatus.CONFIRMED
        db.commit()
        
        response = client.post(f"/payments/process/{test_booking.id}", json={
            "payment_method": "credit_card"
        }, headers=customer_headers)
        
        assert response.status_code == 200
        transaction_id = response.json()["transaction_id"]
        
        assert transaction_id
        assert len(transaction_id) > 0
        assert "TXN_" in transaction_id