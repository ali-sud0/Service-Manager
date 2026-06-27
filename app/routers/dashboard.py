from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from ..core.database import SessionLocal, get_db
from ..core.dependencies import get_current_active_user
from ..core.templates import templates
from ..models.user import User
from ..services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_user_from_token(request: Request):
    """Get user from Authorization header without raising exception"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user and hasattr(user.role, 'value'):
            user.role = user.role.value
        return user
    finally:
        db.close()



@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard page - no auth required for the HTML page itself"""
    token = request.cookies.get("access_token")
    user = None
    if token:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")
            db = SessionLocal()
            user = db.query(User).filter(User.id == int(user_id)).first()
            db.close()

    print(user)
    return templates.TemplateResponse({"request": request, "user": user}, "admin/dashboard.html")

@router.get("/provider", response_class=HTMLResponse)
async def provider_dashboard(request: Request):
    """Provider dashboard page - no auth required for the HTML page itself"""
    return templates.TemplateResponse({"request": request}, "provider/dashboard.html")

@router.get("/customer", response_class=HTMLResponse)
async def my_bookings_page(request: Request):
    """Page for user to view their bookings and make payments"""
    return templates.TemplateResponse({"request": request}, "customer/my_bookings.html")

@router.get("/admin-stats")
async def get_admin_stats_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin" and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return DashboardService.get_admin_stats(db)

@router.get("/provider-stats")
async def get_provider_stats_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "provider":
        raise HTTPException(status_code=403, detail="Provider access required")
    return DashboardService.get_provider_stats(db, current_user.id)

@router.get("/check-role")
async def check_role(
    current_user: User = Depends(get_current_active_user),
):
    """Check current user role - requires auth"""
    return {
        "username": current_user.username,
        "role": current_user.role if isinstance(current_user.role, str) else current_user.role.value,
        "is_admin": current_user.role == "admin" or (hasattr(current_user.role, 'value') and current_user.role.value == "admin")
    }