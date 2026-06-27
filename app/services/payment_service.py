from sqlalchemy.orm import Session
from ..models.payment import Payment
from ..models.booking import Booking, PaymentStatus
from datetime import datetime
import secrets

class PaymentService:
    
    @staticmethod
    def process_payment(db: Session, booking_id: int, payment_method: str = "credit_card"):
        """Process payment for a booking"""
        
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        
        if not booking:
            return None, "Booking not found"
        
        if booking.payment_status == PaymentStatus.PAID:
            return None, "Payment already processed"
        
        # Generate transaction ID
        transaction_id = f"TXN_{secrets.token_hex(8).upper()}"
        
        # Create payment record
        payment = Payment(
            booking_id=booking_id,
            amount=booking.total_price,
            transaction_id=transaction_id,
            payment_method=payment_method,
            paid_at=datetime.now()
        )
        
        # Update booking status
        booking.payment_status = PaymentStatus.PAID
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        return payment, "Payment successful"
    
    @staticmethod
    def get_payment_status(db: Session, booking_id: int):
        """Get payment status for a booking"""
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            return booking.payment_status
        return None