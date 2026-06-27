from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from ..models.user import User, UserRole
from ..models.booking import Booking, BookingStatus, PaymentStatus
from ..models.service import Service
from ..models.payment import Payment

class DashboardService:
    
    @staticmethod
    def get_admin_stats(db: Session):
        """Get statistics for admin dashboard"""
        
        # User stats
        total_customers = db.query(User).filter(User.role == UserRole.CUSTOMER).count()
        total_providers = db.query(User).filter(User.role == UserRole.PROVIDER).count()
        total_users = total_customers + total_providers
        
        # Service stats
        total_services = db.query(Service).count()
        active_services = db.query(Service).filter(Service.is_active == True).count()
        inactive_services = total_services - active_services
        
        # Booking stats
        total_bookings = db.query(Booking).count()
        today = datetime.now().date()
        today_start = datetime(today.year, today.month, today.day)
        today_end = today_start + timedelta(days=1)
        
        today_bookings = db.query(Booking).filter(
            Booking.created_at >= today_start,
            Booking.created_at < today_end
        ).count()
        
        week_ago = datetime.now() - timedelta(days=7)
        weekly_bookings = db.query(Booking).filter(Booking.created_at >= week_ago).count()
        
        # Revenue stats (hypothetical)
        paid_bookings = db.query(Booking).filter(Booking.payment_status == PaymentStatus.PAID).all()
        total_revenue = sum(booking.total_price for booking in paid_bookings)
        total_revenue = total_revenue*0.2
        
        # Most booked services
        most_booked = db.query(
            Service.id, Service.name, func.count(Booking.id).label('booking_count')
        ).join(Booking, Booking.service_id == Service.id)\
         .group_by(Service.id)\
         .order_by(func.count(Booking.id).desc())\
         .limit(5).all()
        
        return {
            "users": {
                "total": total_users,
                "customers": total_customers,
                "providers": total_providers
            },
            "services": {
                "total": total_services,
                "active": active_services,
                "inactive": inactive_services
            },
            "bookings": {
                "total": total_bookings,
                "today": today_bookings,
                "weekly": weekly_bookings
            },
            "revenue": total_revenue,
            "most_booked_services": [
                {"name": s.name, "count": s.booking_count} for s in most_booked
            ]
        }
    
    @staticmethod
    def get_provider_stats(db: Session, provider_id: int):
        """Get statistics for provider dashboard"""
        
        # Services count
        services_count = db.query(Service).filter(Service.provider_id == provider_id).count()
        
        # Bookings received
        total_bookings = db.query(Booking).filter(Booking.provider_id == provider_id).count()
        
        # Bookings by status
        pending = db.query(Booking).filter(
            Booking.provider_id == provider_id,
            Booking.status == BookingStatus.PENDING
        ).count()
        
        confirmed = db.query(Booking).filter(
            Booking.provider_id == provider_id,
            Booking.status == BookingStatus.CONFIRMED
        ).count()
        
        completed = db.query(Booking).filter(
            Booking.provider_id == provider_id,
            Booking.status == BookingStatus.COMPLETED
        ).count()
        
        cancelled = db.query(Booking).filter(
            Booking.provider_id == provider_id,
            Booking.status == BookingStatus.CANCELLED
        ).count()
        
        # Revenue
        paid_bookings = db.query(Booking).filter(
            Booking.provider_id == provider_id,
            Booking.payment_status == PaymentStatus.PAID
        ).all()
        total_revenue = sum(booking.total_price for booking in paid_bookings)
        total_revenue = total_revenue*0.8

        return {
            "services_count": services_count,
            "bookings": {
                "total": total_bookings,
                "pending": pending,
                "confirmed": confirmed,
                "completed": completed,
                "cancelled": cancelled
            },
            "revenue": total_revenue
        }