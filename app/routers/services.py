from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from typing import Optional
from ..core.database import get_db
from ..core.dependencies import get_current_active_user, require_role
from ..core.templates import templates
from ..models.user import User
from ..models.service import Service
from ..schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse

router = APIRouter(prefix="/services", tags=["services"])

@router.get("/", response_class=HTMLResponse)
async def services_page(request: Request):
    return templates.TemplateResponse(request, "services.html")

@router.get("/all")
async def get_all_services_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get all services - admin only"""
    services = db.query(Service).all()
    result = []
    for service in services:
        result.append({
            "id": service.id,
            "name": service.name,
            "description": service.description,
            "category": service.category,
            "price": service.price,
            "duration_minutes": service.duration_minutes,
            "image_url": service.image_url,
            "provider_id": service.provider_id,
            "provider_name": service.provider.full_name if service.provider else None,
            "is_active": service.is_active,
            "created_at": service.created_at
        })
    return result

@router.get("/search")
async def search_services(
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None),
    provider_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Service).join(
        User, Service.provider_id == User.id
    ).filter(
        and_(
            Service.is_active == True,
            User.is_active == True
        )
    )    

    
    if q:
        query = query.filter(
            or_(
                Service.name.ilike(f"%{q}%"),
                Service.description.ilike(f"%{q}%")
            )
        )
    
    if category:
        query = query.filter(Service.category == category)
    
    if provider_id:
        query = query.filter(Service.provider_id == provider_id)
    
    if min_price:
        query = query.filter(Service.price >= min_price)
    
    if max_price:
        query = query.filter(Service.price <= max_price)
    
    services = query.all()
    
    # Calculate average rating for each service
    result = []
    for service in services:
        
        result.append({
            "id": service.id,
            "name": service.name,
            "description": service.description,
            "category": service.category,
            "price": service.price,
            "duration_minutes": service.duration_minutes,
            "image_url": service.image_url,
            "provider_id": service.provider_id,
            "provider_name": service.provider.full_name if service.provider else None
        })
    
    return result

@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Service.category).distinct().all()
    return [cat[0] for cat in categories if cat[0]]

@router.post("/", response_model=ServiceResponse)
async def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("provider"))
):
    db_service = Service(
        **service.dict(),
        provider_id=current_user.id
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.get("/my-services")
async def get_my_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("provider"))
):
    services = db.query(Service).filter(Service.provider_id == current_user.id).all()
    return services

@router.put("/{service_id}")
async def update_service(
    service_id: int,
    service_update: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check permission
    if current_user.role != "admin" and db_service.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    for key, value in service_update.dict(exclude_unset=True).items():
        setattr(db_service, key, value)
    
    db.commit()
    db.refresh(db_service)
    return db_service

@router.delete("/{service_id}")
async def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_service = db.query(Service).filter(Service.id == service_id).first()
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    if current_user.role != "admin" and db_service.provider_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(db_service)
    db.commit()
    return {"message": "Service deleted successfully"}

@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: int,
    db: Session = Depends(get_db)
):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service