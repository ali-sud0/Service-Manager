from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Query, Session
from ..core.database import get_db
from ..core.dependencies import get_current_active_user, require_role
from ..core.security import decode_access_token
from ..models.user import User
from ..schemas.user import UserResponse, UserUpdate
import shutil
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Get all users - admin only"""
    users = db.query(User).filter(User.id != current_user.id).offset(skip).limit(limit)
    return users

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    logger.info(f"User authenticated: {current_user.username}")
    return current_user


@router.put("/me")
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if user_update.full_name:
        current_user.full_name = user_update.full_name
    if user_update.phone:
        current_user.phone = user_update.phone
    if user_update.profile_image:
        current_user.profile_image = user_update.profile_image
    
    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully", "user": current_user}

@router.post("/me/upload-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    os.makedirs("static/uploads", exist_ok=True)
    file_path = f"static/uploads/{current_user.id}_{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    current_user.profile_image = file_path
    db.commit()
    
    return {"message": "Image uploaded successfully", "image_url": file_path}

@router.get("/providers")
async def get_all_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    providers = db.query(User).filter(User.role == "provider", User.is_active == True).all()
    return providers

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}")
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Update user - admin only (full update)"""
    from ..core.security import get_password_hash
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update username (if provided and not duplicate)
    if user_update.username is not None:
        # Check if username is taken by another user
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = user_update.username
    
    # Update email (if provided and not duplicate)
    if user_update.email is not None:
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = user_update.email
    
    # Update full name
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    
    # Update phone
    if user_update.phone is not None:
        user.phone = user_update.phone
    
    # Update role
    if user_update.role is not None:
        if user_update.role not in ["customer", "provider", "admin"]:
            raise HTTPException(status_code=400, detail="Invalid role")
        # Prevent admin from changing their own role
        if user_id == current_user.id and user_update.role != current_user.role:
            raise HTTPException(status_code=400, detail="Cannot change your own role")
        user.role = user_update.role
    
    # Update active status
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    # Update profile image
    if user_update.profile_image is not None:
        user.profile_image = user_update.profile_image
    
    # Update password (if provided)
    if user_update.password is not None and user_update.password.strip():
        user.hashed_password = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(user)
    
    return {
        "message": "User updated successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "phone": user.phone,
            "profile_image": user.profile_image,
            "role": user.role.value if hasattr(user.role, 'value') else user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete user - admin only"""
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.put("/{user_id}/role")
async def change_user_role(
    user_id: int,
    role_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Change user role - admin only"""
    new_role = role_data.get("role")
    if new_role not in ["customer", "provider", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from changing their own role
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    user.role = new_role
    db.commit()
    db.refresh(user)
    
    return {
        "message": "User role updated successfully",
        "user_id": user.id,
        "new_role": user.role
    }

