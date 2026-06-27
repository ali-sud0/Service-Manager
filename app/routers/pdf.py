from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from io import BytesIO
from ..core.database import get_db
from ..core.dependencies import get_current_active_user, require_role
from ..models.user import User
from ..models.booking import Booking, PaymentStatus
from ..models.service import Service
from ..services.pdf_generator import PDFGenerator
from ..services.dashboard_service import DashboardService
from datetime import datetime

router = APIRouter(prefix="/pdf", tags=["pdf"])

@router.get("/invoice/{booking_id}")
async def generate_invoice(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate invoice for a paid booking"""
    
    booking = db.query(Booking).options(
        joinedload(Booking.customer),
        joinedload(Booking.provider),
        joinedload(Booking.service),
        joinedload(Booking.schedule)
    ).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check permission
    if booking.customer_id != current_user.id and booking.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Only paid bookings can generate invoice
    if booking.payment_status != PaymentStatus.PAID:
        raise HTTPException(status_code=400, detail="Invoice only available for paid bookings")
    
    pdf_buffer = PDFGenerator.generate_booking_invoice(booking)
    
    filename = f"invoice_{booking_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/customer-bookings/{customer_id}")
async def generate_customer_report(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate bookings report for a customer"""
    
    # Check permission
    if current_user.id != customer_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    customer = db.query(User).filter(User.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    bookings = db.query(Booking).options(
        joinedload(Booking.customer),
        joinedload(Booking.provider),
        joinedload(Booking.service),
        joinedload(Booking.schedule)
    ).filter(Booking.customer_id == customer_id).all()
    
    pdf_buffer = PDFGenerator.generate_customer_bookings_report(bookings, customer)
    
    filename = f"customer_{customer.username}_bookings_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/provider-bookings/{provider_id}")
async def generate_provider_report(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate bookings report for a provider"""
    
    # Check permission
    if current_user.id != provider_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    provider = db.query(User).filter(User.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    bookings = db.query(Booking).options(
        joinedload(Booking.customer),
        joinedload(Booking.provider),
        joinedload(Booking.service),
        joinedload(Booking.schedule)
    ).filter(Booking.provider_id == provider_id).all()
    
    pdf_buffer = PDFGenerator.generate_provider_bookings_report(bookings, provider)
    
    filename = f"provider_{provider.username}_bookings_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/admin-stats")
async def generate_admin_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Generate admin statistics report"""
    
    # Get statistics
    stats = DashboardService.get_admin_stats(db)
    
    # Get all bookings for reference
    bookings = db.query(Booking).all()
    users = db.query(User).all()
    services = db.query(Service).all()
    
    pdf_buffer = PDFGenerator.generate_admin_stats_report(stats, bookings, users, services)
    
    filename = f"admin_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )